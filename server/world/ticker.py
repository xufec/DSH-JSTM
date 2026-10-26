"""分层 tick 调度器（P1 核心）。

═══════════════════════════════════════════════════════════════════════════
分层依据（来自 kongkongxiyou 审计，已核验到行）：
  100ms → 掉落物 / 动作（行走滑行、复活计时） / AI / 巡逻
  1.0s  → 刷怪刷物（zones）
  3.0s  → 玩家 update（HP/MP 恢复） + 心跳超时踢人 + 策略类扩展
           ★ 参考实现是 31 tick = 3.1s（`timeCount>30 → 归零`）；
             JSTM 按 **Q1 决策** 改为精确 3.0s。

与参考实现刻意的三点不同：
  1. **单一全局 ticker**（参考实现每个 Area 各起一个 setInterval ⇒ 顺序不确定）
  2. **绝对时间戳调度**（`next_1s += 1.0`）⇒ 无 31-tick 漂移
  3. **每 tick 预算 + 降级队列**（参考实现无预算，单进程一旦超时会雪崩）

★ 并发模型：本服务器既有代码是**多线程**（ThreadingHTTPServer / ThreadingTCPServer），
  不是 asyncio，因此这里提供两种驱动：
    · `step(now)` —— **纯同步、可注入时钟**，便于确定性单测（推荐单测只用它）
    · `start_thread()` —— 生产用的后台线程驱动
  世界状态被 tick 线程与连接线程共同访问 ⇒ 调用方需持有 `world.lock`（见 containers）。
"""

from __future__ import annotations

import threading
import time

from .consts import ONE_SECOND, THREE_SECONDS, TICK_MS


class TickScheduler(object):
    """单一全局 tick 循环。"""

    def __init__(self, world, clock=time.monotonic, tick_ms=TICK_MS,
                 one_s=ONE_SECOND, three_s=THREE_SECONDS, budget_ratio=0.5,
                 max_catchup=10, logger=None):
        self.world = world
        self.clock = clock
        self.tick_s = tick_ms / 1000.0
        self.one_s = float(one_s)
        self.three_s = float(three_s)
        self.budget_ratio = float(budget_ratio)
        self.max_catchup = int(max_catchup)
        self._log = logger

        self._running = False
        self._thread = None            # type: Optional[threading.Thread]
        self._stop_evt = threading.Event()

        self._tick_no = 0
        now = self.clock()
        self._next_1s = now + self.one_s
        self._next_3s = now + self.three_s
        self._deferred = []            # type: list[Callable[[], None]]
        self._stats = {
            'tick': 0, 'ticks_1s': 0, 'ticks_3s': 0,
            'over_budget': 0, 'max_ms': 0.0, 'total_ms': 0.0,
            'deferred': 0, 'deferred_dropped': 0, 'lag': 0,
        }

    # ── 纯同步步进（单测用）─────────────────────────────────────────────
    def step(self, now=None, dt_s=None):
        """推进一次。

        `now` 为注入时钟值（默认取 self.clock()）。若 `now` 越过 1s/3s 的截止时间，
        **会补跑**（`while` 循环），因此单测可以直接 `step(now=start+3.1)` 一次跑完三层。
        返回本次实际跑过的层名列表。
        """
        now = self.clock() if now is None else now
        dt_s = self.tick_s if dt_s is None else float(dt_s)
        ran = []
        t0 = time.perf_counter()

        self._tick_no += 1
        self._stats['tick'] += 1

        # ---- 100ms 层：永远执行 ----
        self.world.tick_all(dt_s)
        ran.append('tick')

        # ---- 1.0s 层 ----
        n = 0
        while now >= self._next_1s and n < self.max_catchup:
            self._next_1s += self.one_s
            self.world.tick_1s_all()
            self._stats['ticks_1s'] += 1
            ran.append('1s')
            n += 1

        # ---- 3.0s 层 ----
        n = 0
        while now >= self._next_3s and n < self.max_catchup:
            self._next_3s += self.three_s
            self.world.tick_3s_all()
            self._stats['ticks_3s'] += 1
            ran.append('3s')
            n += 1

        self._drain_deferred()

        used_ms = (time.perf_counter() - t0) * 1000.0
        self._stats['total_ms'] += used_ms
        if used_ms > self._stats['max_ms']:
            self._stats['max_ms'] = used_ms
        if used_ms > self.tick_s * 1000.0 * self.budget_ratio:
            self._stats['over_budget'] += 1
            if self._log is not None:
                self._log('!! tick over budget: %.1fms (>%.0f%% of %.0fms)'
                          % (used_ms, self.budget_ratio * 100, self.tick_s * 1000))
        return ran

    # ── 降级队列（把 A* 等重活推迟，避免阻塞主循环）─────────────────────
    def defer(self, fn, max_pending=2000):
        if len(self._deferred) >= max_pending:
            self._stats['deferred_dropped'] += 1
            return False
        self._deferred.append(fn)
        self._stats['deferred'] += 1
        return True

    def _drain_deferred(self, limit=32):
        for _ in range(min(len(self._deferred), limit)):
            fn = self._deferred.pop(0)
            try:
                fn()
            except Exception as e:            # 单个任务失败不应拖垮 tick
                if self._log is not None:
                    self._log('!! deferred task failed: %r' % (e,))

    @property
    def pending_deferred(self):
        return len(self._deferred)

    # ── 线程驱动（生产用）──────────────────────────────────────────────
    def start_thread(self, name='jstm-tick', daemon=True):
        if self._thread is not None and self._thread.is_alive():
            return self._thread
        self._stop_evt.clear()
        self._running = True
        self._thread = threading.Thread(target=self._loop, name=name, daemon=daemon)
        self._thread.start()
        return self._thread

    def _loop(self):
        deadline = self.clock()
        while not self._stop_evt.is_set():
            deadline += self.tick_s
            try:
                self.step()
            except Exception as e:             # tick 异常不应杀死调度线程
                if self._log is not None:
                    self._log('!! tick raised: %r' % (e,))
            delay = deadline - self.clock()
            if delay > 0:
                self._stop_evt.wait(delay)
            else:
                # 落后了：重置基准，避免"追赶风暴"
                deadline = self.clock()
                self._stats['lag'] += 1
        self._running = False

    def stop(self, timeout=2.0):
        self._stop_evt.set()
        t = self._thread
        if t is not None and t.is_alive():
            t.join(timeout)
        self._thread = None

    @property
    def running(self):
        return self._running

    # ── 观测 ────────────────────────────────────────────────────────────
    def stats(self):
        s = dict(self._stats)
        ticks = max(1, s['tick'])
        s['avg_ms'] = round(s['total_ms'] / ticks, 3)
        s['max_ms'] = round(s['max_ms'], 3)
        s['pending_deferred'] = len(self._deferred)
        s['tick_no'] = self._tick_no
        return s
