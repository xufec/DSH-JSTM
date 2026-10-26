"""★ P1 可运行骨架的演示入口 —— 一条命令验证整套骨架。

运行（二选一）：
    cd C:\\Users\\xu\\Desktop\\DSH\\server
    python -m world.demo
    python world\\demo.py

它会：
  1. 建一个**假时钟**世界（2 个场景 + 1 个刷怪区），全部 tick 走确定性步进
  2. 用 `@area_handler` 守卫把 2 名玩家送进场景（uid ≠ player_id，专门验证不混淆）
  3. 演示**移动校验**（Q2：客户端必传整条路径）
       · 合法稀疏航点      → 接受
       · 跨越阻挡的路径    → 拒绝
       · 起点与服务端不符  → 拒绝
       · 超速（限流）      → 拒绝
  4. 跑 6.5 秒 tick，打印分层统计 / AOI 差量 / 刷怪 / HP 恢复 / 消息计数
  5. 跑一段断言（失败即非零退出）
"""

from __future__ import annotations

import os
import sys

if __package__ in (None, ''):                     # 支持 python world/demo.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world import _deps                                    # noqa: E402
from world.consts import Code                  # noqa: E402
from world.containers import AreaManager                   # noqa: E402
from world.entities import Player, hpmp_recalibrate        # noqa: E402
from world.guards import HandlerCtx, Session, enter_scene, move   # noqa: E402
from world.message import ChannelService, MessageService   # noqa: E402
from world.ticker import TickScheduler                     # noqa: E402


# ══════════════════════════════════════════════════════════════════════════
# 测试替身
# ══════════════════════════════════════════════════════════════════════════
class FakeClock(object):
    def __init__(self, t=1000.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += float(dt)


class RecordingRouter(object):
    """替代 socket：记录所有出网消息。"""

    def __init__(self, failing_addrs=()):
        self.sent = []                       # [(addr, route, msg)]
        self.failing = set(failing_addrs)

    def __call__(self, addr, route, msg):
        if addr in self.failing:
            return False
        self.sent.append((addr, route, msg))
        return True

    def count(self, route=None):
        if route is None:
            return len(self.sent)
        return sum(1 for _a, r, _m in self.sent if r == route)

    def by_route(self):
        out = {}
        for _a, r, _m in self.sent:
            out[r] = out.get(r, 0) + 1
        return out

    def clear(self):
        self.sent = []


_AREA_CONFIGS = {
    1001: {'id': 1001, 'type': 1, 'kind': 2, 'name': '主城', 'born_x': 20, 'born_y': 20,
           'tower_size': 8},
    1002: {'id': 1002, 'type': 1, 'kind': 2, 'name': '野外', 'born_x': 40, 'born_y': 40,
           'transports': [{'target_area': 1001, 'x': 18, 'y': 18}]},
    # 一个单副本区域（验证 instanceId 命名即共享域）
    3001: {'id': 3001, 'type': 2, 'kind': 4, 'name': '个人BOSS', 'born_x': 10, 'born_y': 10},
}


def build_world(clock, router, blocked=()):
    """按五层容器装配一个可跑的世界。"""
    ms = MessageService(router=router, logger=None)
    cs = ChannelService(ms, resolve_player=lambda pid: world_holder['w'].get_player(pid))
    grid = _deps.new_mapgrid(128, 128, blocked=set(blocked), allow_all=True)
    if blocked:
        grid.set_blocked(blocked)
    world = AreaManager(
        message_service=ms, channel_service=cs, mapgrid=grid,
        area_configs=_AREA_CONFIGS, ratelimiter=_deps.new_ratelimiter(),
        clock=clock, instance_life_time=300.0, tower_size=8, logger=None,
    )
    world_holder['w'] = world
    world.init_scenes([1001, 1002, 3001])

    def loader(pid):
        # uid 与 player_id **刻意不同**（参考实现正因两者混用导致 errHandler 空操作）
        rec = hpmp_recalibrate(10.0, 10000, tick_seconds=3.0)
        return Player(pid, uid=900000 + pid, name='p%s' % pid,
                      x=20, y=20, max_hp=10000, max_mp=10000, range_=12,
                      walk_speed=12.0, hp_speed=rec['hp_speed'],
                      hp_capacity=rec['hp_capacity'])
    world._loader = loader
    world.start_all()
    return world


world_holder = {'w': None}


# ══════════════════════════════════════════════════════════════════════════
def main():
    print('=' * 74)
    print('JSTM 世界层 P1 骨架演示   modules=%s' % (_deps.modules_ready(),))
    print('=' * 74)

    clock = FakeClock(1000.0)
    router = RecordingRouter()
    # 在主城 x=25 竖一道墙（y=0..127），用于演示"跨墙路径被拒"
    blocked = set((25, y) for y in range(0, 129))
    world = build_world(clock, router, blocked=blocked)

    # 刷怪区：5s 一批（1s 层驱动 + interval 节流）
    main_area = world.get_area(1001)
    mz = main_area.add_mob_zone(kind_id=1001, x=30, y=30, width=10, height=10,
                                limit=3, gen_count=2, interval=5.0, max_hp=200,
                                is_active_attack=True)

    ticker = TickScheduler(world, clock=clock, logger=lambda m: print('   ' + m))

    fails = []

    def check(name, cond, extra=''):
        print(('  [OK]   ' if cond else '  [FAIL] ') + name + (('  ' + extra) if extra else ''))
        if not cond:
            fails.append(name)

    # ── ① 两名玩家进场景 ───────────────────────────────────────────────
    print('\n[1] 玩家进场景（uid ≠ player_id）')
    sessions = {}
    for pid in (101, 102):
        sess = Session(uid=900000 + pid, player_id=pid, addr=('fake', pid))
        ctx = HandlerCtx(world, sess)
        res = enter_scene(ctx, {'areaId': 1001})
        sessions[pid] = sess
        print('     player_id=%d uid=%d -> %s' % (pid, sess.uid, res.get('code')))
    check('两名玩家都进场成功', main_area.player_num == 2,
          'player_num=%d' % main_area.player_num)
    check('Area.users 反查表可用（uid→player_id）',
          main_area.get_player_by_account_uid(900101) is not None)
    check('AOI 里含 2 个 watcher',
          main_area.aoi.stats()['entities'] == 2, str(main_area.aoi.stats()))
    # ★ 验证"新实体进场会通知已有 watcher"（aoi.py 的 add_* 不派发事件，
    #   由 Area._announce_aoi_entry 主动重算一次视野来补上）
    saw = [m for a, r, m in router.sent
           if a == ('fake', 101) and r == 'onAddEntities'
           and any(e.get('entityId') == 102
                   for lst in m.values() if isinstance(lst, list) for e in lst)]
    check('已有玩家收到新进场玩家的 onAddEntities', len(saw) > 0,
          'msgs=%d' % len(saw))

    # ── ② 移动校验（Q2：客户端必传整条路径）────────────────────────────
    print('\n[2] 移动校验（客户端上传整条路径 + 严格校验）')
    p1 = world.get_player(101)
    p1.x, p1.y = 20, 20

    ctx1 = HandlerCtx(world, sessions[101])
    enter_scene(ctx1, {'areaId': 1001})
    p1 = world.get_player(101)
    p1.x, p1.y = 20, 20

    # (a) 合法：稀疏航点（相邻航点相隔 3 格 —— pathfind.verify_path 会误拒，本实现接受）
    r = move(ctx1, {'path': [[20, 20], [23, 20], [23, 23]]})
    check('合法稀疏航点被接受', r.get('code') == Code.OK, str(r.get('reason', '')))

    # (b) 非法：跨越 x=25 那道墙
    ctx1 = HandlerCtx(world, sessions[101])
    p1 = world.get_player(101)
    p1.x, p1.y = 20, 20
    r = move(ctx1, {'path': [[20, 20], [30, 20]]})
    check('跨墙路径被拒', r.get('code') == Code.ILLEGAL_MOVE, str(r.get('reason')))

    # (c) 非法：起点与服务端不符
    ctx1 = HandlerCtx(world, sessions[101])
    p1 = world.get_player(101)
    p1.x, p1.y = 20, 20
    r = move(ctx1, {'path': [[22, 20], [23, 20]]})
    check('起点不符被拒', r.get('code') == Code.ILLEGAL_MOVE, str(r.get('reason')))

    # (d) 非法：超速（连续大步，触发限流）—— 沿 x=20 向下走，避开 x=25 那道墙
    ctx1 = HandlerCtx(world, sessions[101])
    p1 = world.get_player(101)
    p1.x, p1.y = 20, 20
    world.get_ratelimiter().reset(101)
    long_line = [[20, 20 + i] for i in range(0, 41)]        # 40 段 × 1 格 = 40 格
    r = move(ctx1, {'path': long_line})
    check('超速被拒（限流，非因地形）',
          r.get('code') == Code.ILLEGAL_MOVE and 'rate' in str(r.get('reason', '')),
          str(r.get('reason')))

    # 复位：让玩家原地站好，供后续 tick 演示
    p1 = world.get_player(101)
    p1.x, p1.y = 20, 20
    p1.hp = p1.max_hp // 2
    p1.feed_hp(10000)                       # 投药：把恢复池填满
    world.get_ratelimiter().reset(101)

    # ── ③ 跑 6.5 秒 tick ──────────────────────────────────────────────
    print('\n[3] 确定性 tick（100ms / 1.0s / 3.0s 分层）')
    router.clear()
    layers = {'tick': 0, '1s': 0, '3s': 0}
    for _ in range(65):                     # 65 × 100ms = 6.5s
        clock.advance(0.1)
        for name in ticker.step():
            layers[name] = layers.get(name, 0) + 1
    print('     层执行次数: %s' % layers)
    # 6.5s ⇒ 100ms 层 65 次；1.0s 层 6 次；3.0s 层 2 次
    check('100ms 层 65 次', layers['tick'] == 65, str(layers['tick']))
    check('1.0s 层 6 次（精确 3.0s 决策下无漂移）', layers['1s'] == 6, str(layers['1s']))
    check('3.0s 层 2 次', layers['3s'] == 2, str(layers['3s']))

    check('刷怪区已刷出怪', mz.count > 0, 'mobs=%d' % mz.count)
    hp_now = world.get_player(101).hp
    check('HP 已按 3.0s 口径恢复（2 步 × hp_speed）',
          hp_now == (world.get_player(101).max_hp // 2) + 2 * world.get_player(101).hp_speed,
          'hp=%s hp_speed=%s' % (hp_now, world.get_player(101).hp_speed))

    print('     出网消息分布: %s' % router.by_route())

    # ── ④ 下线缓存 + force_cleanup ─────────────────────────────────────
    print('\n[4] 下线缓存 / 惰性断线清理')
    p2 = world.get_player(102)
    world.cache_offline_player(p2)
    check('下线后进缓存（内存已无）', world.players.get(102) is None
          and world.player_cache.get(102) is not None)
    promoted = world.get_player(102)
    check('再次读取会提升回在线', promoted is not None and world.players.get(102) is not None)

    # 模拟"推送连续失败" ⇒ force_cleanup（参考实现这里是空操作）
    p2 = world.get_player(102)
    # 注意：cache_offline_player 会清掉回包地址 ⇒ 先恢复地址，否则 send() 会走
    # "无地址丢弃"分支（不计入失败连击，这是正确行为）
    p2.session_addr = ('fake', 102)
    bad = RecordingRouter(failing_addrs={('fake', 102)})
    world._ms.router = bad
    world._ms.fail_streak_to_kick = 3
    for _ in range(3):
        world._ms.send(p2, 'onX', {})
    check('连续推送失败触发 force_cleanup', world.players.get(102) is None)
    ch = world._cs.get_channel('area_1001')
    check('下线后场景频道成员被摘掉（无幽灵接收者）',
          ch is not None and ch.get_user_amount() == 1 and 102 not in ch.members(),
          'members=%s' % (ch.members() if ch else None,))
    check('下线后 Area.player_num 已更新', main_area.player_num == 1,
          'player_num=%d' % main_area.player_num)

    # ── ⑤ 汇总 ────────────────────────────────────────────────────────
    print('\n[5] 统计')
    _dump('ticker', ticker.stats())
    _dump('area   ', main_area.stats())
    _dump('world  ', world.stats())
    _dump('message', world._ms.stats())
    _dump('channels', world._cs.stats())

    print('\n' + '=' * 74)
    if fails:
        print('结果：%d 项失败 -> %s' % (len(fails), fails))
        return 1
    print('结果：全部通过 ✅   （P1 骨架可运行）')
    print('=' * 74)
    return 0


def _dump(title, d):
    import json
    print('  %-9s %s' % (title, json.dumps(d, ensure_ascii=False, default=str)))


if __name__ == '__main__':
    sys.exit(main())
