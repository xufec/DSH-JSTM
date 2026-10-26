"""AOI（Area of Interest，兴趣区域）—— 自研实现。

═══════════════════════════════════════════════════════════════════════════
★ 来源声明（任务书【原则 3】/【第十四节】要求）
───────────────────────────────────────────────────────────────────────────
设计思想参考（**只有思想，没有代码**）：
  · Survive `common/aoi.c`（均匀网格 + 每对象视野集合 + 新旧集合差 + 双向 see 回调）
    ⚠ **该文件头内嵌 GPLv3**，故**一行代码都不可复制**，本文件为**完全自研**
  · kongkongxiyou `aoi.md`（watcher/object 双注册 + 4 事件 + old/new watchers 双向差集）

JSTM 化改造（与两者都不同）：
  1. **纯 Python + 单进程**（参考项目是 C 模块 / Pomelo 插件）
  2. 坐标用 JSTM 的**瓦片坐标**（客户端 ×30 得世界像素）
  3. 事件不直接发网络 —— 只产出 `[(uid, event)]`，由调用方决定怎么推
     （对应空空西游 `getWatcherUids` 的"**AOI 绝不碰 socket**"原则）
  4. **不做隐藏**：JSTM 目前无需隐身/潜行，故不引入 visibleness 位
═══════════════════════════════════════════════════════════════════════════

设计要点（来自审计结论）：
  · **watcher**（有视野者，带 range）与 **object**（被看见者）**双注册**
  · 核心是 `update()` 求 **old_watchers vs new_watchers 双向差集**
    ⇒ 开销正比于**视野变化量**，而不是视野内实体数
  · 事件四种：`enter`（object 进入我的视野）/ `leave` / `update` / `update_watcher`
  · **移动时必须两个都调**：`update_watcher`（服务自己的视野）+ `update`（服务别人的视野）
    —— 这是空空西游 `move.js#update` 的做法，漏一个就会出现"别人看不到我移动"

⚠ 参考项目已知缺陷（本文件**已修正**，见各函数注释）：
  · 塔格硬编码 300（本实现 `tower_size` 可配）
  · **MOB 的 remove 分支被注释掉**（本实现 `remove_object` 正常派发 leave）
  · 零埋点（本实现提供 `stats()`）

★ 2026-09-18 自我审查修复（对照 `analysis/server_reference/survive/aoi_pathfind_review.md`）：
  · **A1** `remove()` 改为**双向对称清理**（否则重复 leave / 幽灵事件）
  · **A2** `_max_range()` 加缓存（否则 `_visible_watchers` 每次都 O(全部实体) 扫描）
  · **A3** `update_*` 只给一个坐标时**显式报错**（旧行为是静默忽略 x）
  · **A4** 新增 `move()`：**一次移动双向更新**（对应 Survive `aoi_moveto`），
        消除"必须成对调用、漏一个就单向失明"
  · **A8** 两向更新时**交叉维护对方集合**（`_diff` 同步 `_old_watchers`；
        `update_object` 同步 `seen`）——否则对方下次移动会产出**重复 enter/leave**
        （Survive 的 C 内核用 `enter_me(o,cur)` + `enter_me(cur,o)` 同时置两侧）
"""

from __future__ import annotations

import math


class Entity(object):
    """参与 AOI 的实体（玩家 / 怪物 / NPC / 掉落物）。"""

    __slots__ = ('uid', 'x', 'y', 'range', 'types', 'is_watcher', 'is_object',
                 '_old_watchers', 'seen')

    def __init__(self, uid, x, y, range_=0, types=0,
                 is_watcher=True, is_object=True):
        self.uid = uid
        self.x = x
        self.y = y
        self.range = range_          # 视野半径（瓦片）；watcher 才有意义
        self.types = types           # 位掩码，便于按类型过滤
        self.is_watcher = is_watcher
        self.is_object = is_object
        self._old_watchers = set()   # 上一次"看得见我的人"(对象视角)
        self.seen = set()            # 上一次"我看得见的人"(观察者视角)


class AOI(object):
    """均匀网格 AOI。

    用法：
        aoi = AOI(tower_size=8)
        aoi.add_watcher(uid=1001, x=40, y=37, range_=15)
        aoi.add_object(uid=2001, x=41, y=37)
        events = aoi.update_watcher(1001, x=41, y=37)   # 我移动了
        events += aoi.update_object(2001, x=42, y=37)   # 怪物移动了
        for uid, ev, other in events: ...
    """

    def __init__(self, tower_size=8):
        # ⚠ 参考项目硬编码 300（世界像素）；JSTM 用**瓦片坐标**，8 格一塔较合适且可配
        self.tower_size = max(1, int(tower_size))
        self._towers = {}        # (tx, ty) -> set(uid)
        self._ents = {}          # uid -> Entity
        self._stats = {'add': 0, 'remove': 0, 'update': 0, 'enter': 0, 'leave': 0}
        # ★ 修复 A2（2026-09-18）：缓存"全图最大视野"，避免 _visible_watchers 每次全表扫描
        self._maxr = 0
        self._maxr_dirty = False

    def __len__(self):
        return len(self._ents)

    # ── 网格 ────────────────────────────────────────────────────────────
    def _tower_of(self, x, y):
        # ★ 2026-10-17 修（ruff F821）：原作直接用 `t`，但这个函数里**从未定义** `t`
        #   （`t = self.tower_size` 被写在了隔壁 `_towers_in_range` 里，而那里根本用不到）
        #   ⇒ `_tower_of()` 一旦被调用就 NameError。这里补上定义。
        t = self.tower_size
        return (int(math.floor(x / t)), int(math.floor(y / t)))

    def _towers_in_range(self, x, y, r):
        """返回覆盖 (x,y) 半径 r 的所有塔坐标。"""
        x0, y0 = self._tower_of(x - r, y - r)
        x1, y1 = self._tower_of(x + r, y + r)
        for tx in range(x0, x1 + 1):
            for ty in range(y0, y1 + 1):
                yield (tx, ty)

    # ── 注册 / 注销 ─────────────────────────────────────────────────────
    def add_watcher(self, uid, x, y, range_):
        e = self._ents.get(uid)
        if e is None:
            # ★ 修复 A9：新实体默认 **is_object=True**（与 Entity 默认值、
            #   以及 `_visible_objects` 文档串"watcher 默认也是 object"一致）。
            #   旧实现显式传 is_object=False ⇒ **只注册 watcher 的玩家对任何人都不可见**
            #   （玩家之间永远互相看不到，是接线期最容易踩的坑）。
            e = Entity(uid, x, y, range_, is_watcher=True)
            self._ents[uid] = e
            self._towers.setdefault(self._tower_of(x, y), set()).add(uid)
            self._stats['add'] += 1
        else:
            e.is_watcher = True
            e.range = range_
            self._move_in_tower(e, x, y)
        if range_ > self._maxr:            # ★ A2：增量维护
            self._maxr = range_
        return e

    def add_player(self, uid, x, y, range_, types=0):
        """★ 修复 A9 的便利入口：玩家这类"**既看别人、也被别人看**"的实体一次注册。

        （怪物/NPC/掉落物只需 `add_object`；纯观察者只需 `add_watcher`。）
        """
        self.add_watcher(uid, x, y, range_)
        self.add_object(uid, x, y, types)
        return self._ents[uid]

    def add_object(self, uid, x, y, types=0):
        e = self._ents.get(uid)
        if e is None:
            e = Entity(uid, x, y, 0, types, is_watcher=False, is_object=True)
            self._ents[uid] = e
            self._towers.setdefault(self._tower_of(x, y), set()).add(uid)
            self._stats['add'] += 1
        else:
            e.is_object = True
            e.types = types
            self._move_in_tower(e, x, y)
        return e

    def remove(self, uid):
        """注销实体 —— ★ **必须正常派发 leave**（参考项目把 MOB 的 remove 分支注释掉了）。

        ★ 修复 A1（2026-09-18）：**双向对称清理**。
        只通知 `_old_watchers` 是不够的——已删 uid 仍会留在
          ① 其它 watcher 的 `seen` ⇒ 它们下次 update 产出**重复 leave**；
          ② 其它 object 的 `_old_watchers` ⇒ 下次产出**发给已删实体的幽灵事件**。
        """
        e = self._ents.get(uid)
        if e is None:
            return []
        events = []
        # ① 通知"看得见我的人"：我离开了，并从它们的 seen 里摘掉我（防重复 leave）
        for w_uid in e._old_watchers:
            events.append((w_uid, 'leave', uid))
            self._stats['leave'] += 1
            w = self._ents.get(w_uid)
            if w is not None:
                w.seen.discard(uid)
        # ② 通知"我看得见的人"：不必再记着我（防幽灵 enter/leave）
        for o_uid in e.seen:
            o = self._ents.get(o_uid)
            if o is not None:
                o._old_watchers.discard(uid)
        e._old_watchers.clear()
        e.seen.clear()
        tower = self._towers.get(self._tower_of(e.x, e.y))
        if tower:
            tower.discard(uid)
            if not tower:
                self._towers.pop(self._tower_of(e.x, e.y), None)
        del self._ents[uid]
        self._stats['remove'] += 1
        if e.is_watcher and e.range >= self._maxr:
            self._maxr_dirty = True        # ★ A2：删掉最大视野者 ⇒ 延迟重算
        return events

    def _move_in_tower(self, e, x, y):
        old = self._tower_of(e.x, e.y)
        new = self._tower_of(x, y)
        if old != new:
            s = self._towers.get(old)
            if s:
                s.discard(e.uid)
                if not s:
                    self._towers.pop(old, None)
            self._towers.setdefault(new, set()).add(e.uid)
        e.x, e.y = x, y

    # ── 视野计算 ────────────────────────────────────────────────────────
    def _in_range(self, a, b, r):
        """粗筛（塔）之后的**精确距离过滤** —— 参考项目内核读不到，此为自研。"""
        dx = a.x - b.x
        dy = a.y - b.y
        return dx * dx + dy * dy <= r * r

    def _visible_objects(self, e):
        """e 能看见的 object 集合（含其它 watcher，因为 watcher 默认也是 object）。"""
        if e.range <= 0:
            return set()
        out = set()
        for t in self._towers_in_range(e.x, e.y, e.range):
            for uid in self._towers.get(t, ()):  # noqa: B007
                if uid == e.uid:
                    continue
                o = self._ents.get(uid)
                if o is None or not o.is_object:
                    continue
                if self._in_range(e, o, e.range):
                    out.add(uid)
        return out

    def _visible_watchers(self, obj):
        """能看见 obj 的 watcher 集合。"""
        out = set()
        # 用 obj 附近一圈塔来找 watcher：watcher 的 range 各不相同，
        # 不能只查自己那一塔 ⇒ 以"最大 range 上界"扩圈。
        maxr = self._max_range()
        for t in self._towers_in_range(obj.x, obj.y, maxr):
            for uid in self._towers.get(t, ()):
                if uid == obj.uid:
                    continue
                w = self._ents.get(uid)
                if w is None or not w.is_watcher:
                    continue
                if self._in_range(w, obj, w.range):
                    out.add(uid)
        return out

    def _max_range(self):
        """★ 修复 A2：带缓存。旧实现每次调用都遍历全部实体（怪物移动是高频路径 ⇒ O(N²)）。"""
        if self._maxr_dirty:
            m = 0
            for e in self._ents.values():
                if e.is_watcher and e.range > m:
                    m = e.range
            self._maxr = m
            self._maxr_dirty = False
        return self._maxr

    # ── 更新（核心：双向差集）──────────────────────────────────────────
    def _resolve_xy(self, uid, x, y, who):
        """★ 修复 A3：消灭"只给一个坐标就静默不动"的陷阱。

        - (None, None) ⇒ 只重算视野，不移动（合法用法）
        - (x, y)       ⇒ 移动 + 重算
        - 只给一个坐标  ⇒ **抛 ValueError**（旧实现会静默忽略 x，最容易埋 bug）
        """
        if x is None and y is None:
            return False
        if x is None or y is None:
            raise ValueError(
                '%s(uid=%r): 必须同时给出 x 与 y（或都不给）；'
                '只给一个会被旧实现静默忽略，故改为显式报错' % (who, uid))
        return True

    def update_watcher(self, uid, x=None, y=None):
        """watcher 移动/换位 —— 服务**自己的视野**。

        返回 [(other_uid, 'enter'|'leave', ...)]，由调用方决定怎么推。
        ⚠ 单独调用它只解决"我看得见谁"；**要同时服务别人的视野，请用 `move()`**。
        """
        e = self._ents.get(uid)
        if e is None or not e.is_watcher:
            return []
        if self._resolve_xy(uid, x, y, 'update_watcher'):
            self._move_in_tower(e, x, y)
        new = self._visible_objects(e)
        old = getattr(e, 'seen', set())
        self._stats['update'] += 1
        return self._diff(e, old, new)

    def _diff(self, e, old, new):
        events = []
        for uid in new - old:
            events.append((uid, 'enter'))
            self._stats['enter'] += 1
            # ★ 修复 A8：同步维护"对方的 _old_watchers"
            #   否则 e 离开该对象时，对方会再发一次 leave（重复 LEAVESEE）
            o = self._ents.get(uid)
            if o is not None:
                o._old_watchers.add(e.uid)
        for uid in old - new:
            events.append((uid, 'leave'))
            self._stats['leave'] += 1
            o = self._ents.get(uid)
            if o is not None:
                o._old_watchers.discard(e.uid)
        e.seen = new
        return events

    def update_object(self, uid, x=None, y=None):
        """object 移动 —— 服务**别人的视野**（谁该被告知）。

        ⚠ 参考项目要求：移动时**两个都要调**（update_watcher + update_object），
          漏一个就会出现"别人看不到我移动" ⇒ **推荐直接用 `move()`**（本文件已提供）。
        """
        e = self._ents.get(uid)
        if e is None or not e.is_object:
            return []
        if self._resolve_xy(uid, x, y, 'update_object'):
            self._move_in_tower(e, x, y)
        new = self._visible_watchers(e)
        old = e._old_watchers
        events = []
        for w in new - old:
            events.append((w, 'enter', uid))
            self._stats['enter'] += 1
            # ★ 修复 A8：同步维护"对方的 seen"
            #   否则该 watcher 下次移动时会再产出一次 enter（重复 ENTERSEE）
            we = self._ents.get(w)
            if we is not None:
                we.seen.add(uid)
        for w in old - new:
            events.append((w, 'leave', uid))
            self._stats['leave'] += 1
            we = self._ents.get(w)
            if we is not None:
                we.seen.discard(uid)
        e._old_watchers = new
        self._stats['update'] += 1
        return events

    def move(self, uid, x=None, y=None):
        """★ 修复 A4：**一次移动，双向更新**（对应 Survive 的 `aoi_moveto`）。

        Survive 的 C 内核在一次 `aoi_moveto` 里同时处理"我进入谁的视野"和
        "谁进入我的视野"；本文件原本把两件事拆成两个必须成对调用的方法，
        调用方漏一个就会出现"单向失明"（正是 10204 最容易犯的错）。
        此方法把这条知识收回模块内部。

        返回 `(self_events, watch_events)`：
          · self_events  = [(other_uid, 'enter'|'leave')]      —— 我该增删的视野对象
          · watch_events = [(watcher_uid, 'enter'|'leave', uid)] —— 该被告知我动向的人
        """
        e = self._ents.get(uid)
        if e is None:
            return [], []
        self_events = []
        if e.is_watcher:
            self_events = self.update_watcher(uid, x, y)
        watch_events = []
        if e.is_object:
            watch_events = self.update_object(uid, x, y)
        return self_events, watch_events

    # ── 查询 ────────────────────────────────────────────────────────────
    def watchers_seeing(self, uid):
        """★ 新增（接线用）：**当前看得见 `uid` 的 watcher 集合**。

        等价于"我移动了该通知谁" —— 就是 `Entity._old_watchers` 的公开只读视图。
        广播时用它遍历接收者，而不必依赖 enter/leave 事件（事件只表达增量）。
        """
        e = self._ents.get(uid)
        if e is None:
            return set()
        return set(e._old_watchers)

    def watchers_of(self, px, py, r, types=None):
        """按坐标+半径取 watcher（对应空空西游 `getWatcherUids`）。

        ★ **返回 uid 列表，绝不返回 socket/连接** —— AOI 不碰网络。
        """
        out = []
        for t in self._towers_in_range(px, py, r):
            for uid in self._towers.get(t, ()):
                e = self._ents.get(uid)
                if e is None or not e.is_watcher:
                    continue
                if types is not None and not (e.types & types):
                    continue
                dx, dy = e.x - px, e.y - py
                if dx * dx + dy * dy <= r * r:
                    out.append(uid)
        return out

    def entities_near(self, px, py, r):
        out = []
        for t in self._towers_in_range(px, py, r):
            for uid in self._towers.get(t, ()):
                e = self._ents.get(uid)
                if e is None:
                    continue
                dx, dy = e.x - px, e.y - py
                if dx * dx + dy * dy <= r * r:
                    out.append(e)
        return out

    def stats(self):
        """★ 埋点（参考项目零埋点，不便诊断）。"""
        s = dict(self._stats)
        s['entities'] = len(self._ents)
        s['towers'] = len(self._towers)
        return s
