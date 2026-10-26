"""Area —— 真正的世界实例（五层的第 4 层，R2 规则）。

═══════════════════════════════════════════════════════════════════════════
职责（只做"一个世界实例"内的事）：
  · 实体表三索引：entities{} / players{player_id→entity_id} / users{uid→player_id}
  · AOI（**复用 server/aoi.py**，每个 Area 一个实例）
  · 动作队列（actions）
  · 刷怪/刷物区（zones）
  · 场景频道（懒创建）
  · 三层 tick 的**实体侧**：tick / tick_1s / tick_3s

★ 与参考实现刻意的不同：
  1. **构造与启动分离**（参考实现 `new Area()` 内部就 `timer.run()` 起了世界）
  2. AOI 更新用 `aoi.move()` **一次双向**（见 aoi.py 的 A4 修复），
     而不是"必须成对调用 update_watcher + update_object，漏一个就单向失明"
  3. 用 `PlayerLocation` 显式状态，不靠"查不到就兜底改 areaId"
  4. 实体移除**双向对称清理**（aoi.remove 已实现），且清理顺序固定
"""

from __future__ import annotations

import time

from . import _deps
from .consts import (EntityType)
from .entities import Item, Mob, Player
from .move import ActionManager, MoveAction


class Zone(object):
    """刷怪/刷物区基类。"""

    def __init__(self, zone_id, x, y, width=0, height=0, area=None):
        self.zone_id = int(zone_id)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.area = area

    def update(self, now):
        raise NotImplementedError

    def remove(self, entity_id):
        pass


class MobZone(Zone):
    """刷怪区。

    ★ 节奏（照搬参考实现 `domain/map/mobzone.js` 的语义）：
      · 由 **1.0s 层** 驱动（`updateZones`）
      · 内部再用 `next_gen_time` 以 `interval`（默认 5s）节流
      ⇒ **实际刷怪周期 ≈ max(1.0s, interval) = 5s**，每次刷 gen_count 只到 limit
    """

    def __init__(self, zone_id, kind_id, x, y, width=0, height=0, area=None,
                 limit=10, gen_count=3, interval=5.0, level=1,
                 max_hp=100, is_active_attack=False, next_entity_id=None):
        Zone.__init__(self, zone_id, x, y, width, height, area)
        self.kind_id = int(kind_id)
        self.limit = int(limit)
        self.gen_count = int(gen_count)
        self.interval = float(interval)
        self.level = int(level)
        self.max_hp = int(max_hp)
        self.is_active_attack = bool(is_active_attack)
        self.next_gen_time = 0.0
        self._mobs = set()
        self._next_entity_id = next_entity_id    # 由 Area 提供的 id 分配器
        self._stats = {'spawned': 0, 'skipped_throttle': 0, 'blocked': 0}

    @property
    def count(self):
        return len(self._mobs)

    def update(self, now):
        if now < self.next_gen_time:
            self._stats['skipped_throttle'] += 1
            return 0
        self.next_gen_time = now + self.interval
        if self.count >= self.limit:
            return 0
        made = 0
        for _ in range(self.gen_count):
            if self.count >= self.limit:
                break
            if self.spawn_one() is not None:
                made += 1
        return made

    def spawn_one(self):
        area = self.area
        if area is None or self._next_entity_id is None:
            return None
        # 在刷怪区内随机取点；不可走则重试（**用可达性判断，不用 find_path**，
        # 参考实现 checkPoint 里跑完整 findPath 是性能陷阱）
        pt = self._random_walkable(area)
        if pt is None:
            self._stats['blocked'] += 1
            return None
        eid = self._next_entity_id()
        mob = Mob(eid, kind_id=self.kind_id, x=pt[0], y=pt[1],
                  max_hp=self.max_hp, is_active_attack=self.is_active_attack)
        mob.zone_id = self.zone_id
        # 生成巡逻路径（闭环）—— 参考实现 map.genPatrolPath 的思想
        mob.path = self._gen_loop_path(pt, area)
        area.add_entity(mob)
        self._mobs.add(eid)
        self._stats['spawned'] += 1
        return mob

    def _random_walkable(self, area, tries=10):
        import random
        grid = area.map
        for _ in range(tries):
            if self.width <= 1 and self.height <= 1:
                x, y = self.x, self.y
            else:
                x = self.x + random.randint(-self.width // 2, self.width // 2)
                y = self.y + random.randint(-self.height // 2, self.height // 2)
            if grid is None or grid.walkable(x, y):
                return (int(x), int(y))
        return None

    def _gen_loop_path(self, start, area, steps=3):
        """随机游走 + **末点回填起点**（闭环）⇒ 配合巡逻 Loop 可无限巡逻。"""
        import random
        path = [start]
        x, y = start
        for _ in range(steps):
            nx = x + random.randint(-6, 6)
            ny = y + random.randint(-6, 6)
            if area.map is None or area.map.walkable(nx, ny):
                path.append((nx, ny))
                x, y = nx, ny
        path.append(start)
        return path

    def remove(self, entity_id):
        self._mobs.discard(entity_id)

    def stats(self):
        s = dict(self._stats)
        s['count'] = self.count
        s['limit'] = self.limit
        return s


class ItemZone(Zone):
    """刷物区（演示 100ms 层的超时消失）。"""

    def __init__(self, zone_id, kind_id, x, y, width=0, height=0, area=None,
                 limit=10, interval=10.0, life=60.0, next_entity_id=None):
        Zone.__init__(self, zone_id, x, y, width, height, area)
        self.kind_id = int(kind_id)
        self.limit = int(limit)
        self.interval = float(interval)
        self.life = float(life)
        self.next_gen_time = 0.0
        self._items = set()
        self._next_entity_id = next_entity_id
        self._stats = {'spawned': 0}

    @property
    def count(self):
        return len(self._items)

    def update(self, now):
        if now < self.next_gen_time:
            return 0
        self.next_gen_time = now + self.interval
        if self.count >= self.limit or self.area is None or self._next_entity_id is None:
            return 0
        grid = self.area.map
        import random
        for _ in range(10):
            x = self.x + random.randint(-max(1, self.width // 2), max(1, self.width // 2))
            y = self.y + random.randint(-max(1, self.height // 2), max(1, self.height // 2))
            if grid is None or grid.walkable(x, y):
                it = Item(self._next_entity_id(), self.kind_id, x, y, life=self.life, now=now)
                it.zone_id = self.zone_id
                self.area.add_entity(it)
                self._items.add(it.entity_id)
                self._stats['spawned'] += 1
                return 1
        return 0

    def remove(self, entity_id):
        self._items.discard(entity_id)

    def stats(self):
        s = dict(self._stats)
        s['count'] = self.count
        return s


class Area(object):
    """一个世界实例。"""

    def __init__(self, area_id, mapgrid=None, *, instance_id=None,
                 area_type=1, area_kind=2, tower_size=8,
                 message_service=None, channel_service=None, logger=None,
                 name='', aoi=None, clock=None):
        self.area_id = int(area_id)
        self.instance_id = instance_id
        self.area_type = int(area_type)
        self.area_kind = int(area_kind)
        self.name = name or ('area_%s' % area_id)
        self.map = mapgrid                      # ★ 全服共享的同一份 MapGrid
        self._ms = message_service
        self._cs = channel_service
        self._log = logger
        self._clock = clock or time.time        # 可注入时钟（单测/演示用假时钟）

        # ★ 每个 Area 一个 AOI 实例（副本之间视野隔离）
        self.aoi = aoi if aoi is not None else _deps.new_aoi(tower_size=tower_size)

        self.entities = {}       # entity_id -> Entity
        self.players = {}        # player_id -> entity_id
        self.users = {}          # ★ uid -> player_id（反查表，参考实现同样需要）
        self.items = {}          # entity_id -> entity_id
        self.npcs = {}           # kind_id -> NPC

        self.zones = {}          # zone_id -> Zone
        self.actions = ActionManager()
        self.channel = None
        self.player_num = 0
        # ★ 用"绝对时间戳或 None"表示空场时间，**绝不用 0.0 表示空**：
        #   0.0 是 falsy，会让 `while empty_time and ...` 之类的判断静默失效
        #   （Instance.is_alive 就踩过这个坑）。
        self.empty_time = self._clock()
        self._started = False
        self._next_id = 1
        self._stats = {'added': 0, 'removed': 0, 'expired_items': 0,
                       'aoi_enter': 0, 'aoi_leave': 0, 'kicked': 0}

    # ── 启动（★ 与构造分离）────────────────────────────────────────────
    def start(self):
        """显式启动。参考实现是在 Area 构造器里就 `areaLogic.startLogic()→area.start()`。"""
        if self._started:
            return False
        self._started = True
        self.empty_time = None if self.player_num else self._clock()
        return True

    @property
    def started(self):
        return self._started

    def close(self):
        """关闭。Python 只需解除引用；**不要**像参考实现那样手动 delete 所有字段。"""
        self._started = False
        self.entities.clear()
        self.players.clear()
        self.users.clear()
        self.items.clear()
        self.npcs.clear()
        self.zones.clear()
        self.aoi = None

    # ── id 分配 ────────────────────────────────────────────────────────
    def alloc_entity_id(self):
        eid = self._next_id
        self._next_id += 1
        return eid

    # ── 频道 ───────────────────────────────────────────────────────────
    def get_channel(self):
        if self.channel is None and self._cs is not None:
            name = ('area_%s' % self.instance_id) if self.instance_id else ('area_%s' % self.area_id)
            self.channel = self._cs.get_channel(name, create=True)
        return self.channel

    def channel_name(self):
        return ('area_%s' % self.instance_id) if self.instance_id else ('area_%s' % self.area_id)

    # ── 刷怪/刷物区 ────────────────────────────────────────────────────
    def add_mob_zone(self, kind_id, x, y, width=0, height=0, **kw):
        zid = len(self.zones) + 1
        z = MobZone(zid, kind_id, x, y, width, height, area=self,
                    next_entity_id=self.alloc_entity_id, **kw)
        self.zones[zid] = z
        return z

    def add_item_zone(self, kind_id, x, y, width=0, height=0, **kw):
        zid = len(self.zones) + 1
        z = ItemZone(zid, kind_id, x, y, width, height, area=self,
                     next_entity_id=self.alloc_entity_id, **kw)
        self.zones[zid] = z
        return z

    # ── 实体进出（★ AOI 双注册）────────────────────────────────────────
    def add_entity(self, e):
        """注册实体。

        AOI 双注册模型（审计结论核心）：
          · **watcher**（有视野者，带 range）：PLAYER / MOB
          · **object**（被看见者）：PLAYER / MOB / ITEM / EQUIPMENT
          · **NPC 完全不进 AOI**（进场时全量下发即可）
        """
        if e is None or getattr(e, 'entity_id', None) is None:
            return False
        eid = e.entity_id
        if eid in self.entities:
            if self._log:
                self._log('!! add_entity: duplicate entity_id=%s' % eid)
            return False
        e.area = self
        self.entities[eid] = e
        self._stats['added'] += 1

        if e.type == EntityType.PLAYER:
            if e.id in self.players:
                if self._log:
                    self._log('!! add_entity: player already in area player_id=%s' % e.id)
                del self.entities[eid]
                return False
            self.players[e.id] = eid
            self.users[e.uid] = e.id
            self.player_num += 1
            self.empty_time = None
            ch = self.get_channel()
            if ch is not None:
                ch.add(e.id)
            # 双注册（watcher + object）。
            # ★ 优先用 aoi.add_player（并发协作者新增的 A9 便利入口：
            #   "既看别人、也被别人看"一次注册）；旧版本没有此方法时回退到两步注册。
            add_player = getattr(self.aoi, 'add_player', None)
            if add_player is not None:
                add_player(eid, e.x, e.y, e.range, e.type)
            else:
                self.aoi.add_watcher(eid, e.x, e.y, e.range)
                self.aoi.add_object(eid, e.x, e.y, e.type)
        elif e.type == EntityType.MOB:
            self.aoi.add_watcher(eid, e.x, e.y, e.range)
            self.aoi.add_object(eid, e.x, e.y, e.type)
        elif e.type in (EntityType.ITEM, EntityType.EQUIPMENT):
            self.items[eid] = eid
            self.aoi.add_object(eid, e.x, e.y, e.type)
        elif e.type == EntityType.NPC:
            self.npcs[getattr(e, 'kind_id', eid)] = e
            # NPC 不进 AOI
        # ★ 关键：注册后**主动重算一次视野**，否则已有 watcher 永远不知道新实体进来了。
        #   （参考实现靠 AOI 的 `add` 事件达到同一效果；既有 aoi.py 的
        #     add_watcher/add_object 不派发事件，所以这里用 `move()` 不传坐标 → 只重算。）
        self._announce_aoi_entry(eid)
        return True

    def _announce_aoi_entry(self, entity_id):
        """新实体进场时：通知"能看见它的人"。

        ★ 只派发 **watch_events**（通知别人），**不派发 self_events**：
          新进场玩家自己的可见列表已由 `area_info_strip()` 快照给出，
          再推一次会重复。
          但 `aoi.move()` **必须调用**，因为它会初始化 `seen` / `_old_watchers`
          —— 否则该实体第一次移动时会产出大量重复 enter/leave。
        """
        if self.aoi is None or self._ms is None:
            return
        self_events, watch_events = self.aoi.move(entity_id)   # 不传坐标 = 只重算视野
        # self_events 丢弃（快照已覆盖），但其副作用（初始化 seen）已生效
        del self_events
        self._dispatch_watch_events(watch_events)

    def remove_entity(self, entity_id, now=None):
        """移除实体。清理顺序（照搬审计结论）：关系表 → AOI → 索引 → 对象。"""
        e = self.entities.get(entity_id)
        if e is None:
            return False
        now = self._clock() if now is None else now

        # ① AOI 注销（**双向对称清理**，由 aoi.remove 负责）→ 派发 leave
        events = self.aoi.remove(entity_id) if self.aoi is not None else []
        self._dispatch_watch_events(events)

        # ② 场景频道
        if e.type == EntityType.PLAYER:
            ch = self.channel
            if ch is not None:
                ch.leave(e.id)
            self.players.pop(e.id, None)
            self.users.pop(e.uid, None)
            self.player_num = max(0, self.player_num - 1)
            if self.player_num == 0:
                self.empty_time = now
        elif e.type == EntityType.MOB:
            z = self.zones.get(getattr(e, 'zone_id', 0))
            if z is not None:
                z.remove(entity_id)
        elif e.type in (EntityType.ITEM, EntityType.EQUIPMENT):
            z = self.zones.get(getattr(e, 'zone_id', 0))
            if z is not None:
                z.remove(entity_id)
            self.items.pop(entity_id, None)

        # ③ 动作队列
        self.actions.abort_all(entity_id)
        # ④ 索引与对象
        self.entities.pop(entity_id, None)
        self._stats['removed'] += 1
        return True

    def remove_player(self, player_id):
        eid = self.players.get(player_id)
        if eid is None:
            return False
        return self.remove_entity(eid)

    def remove_player_by_uid(self, uid):
        pid = self.users.get(int(uid))
        if pid is None:
            return False
        return self.remove_player(pid)

    # ── 查询 ───────────────────────────────────────────────────────────
    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    def get_player(self, player_id):
        eid = self.players.get(int(player_id))
        return self.entities.get(eid) if eid is not None else None

    def get_player_by_entity_id(self, entity_id):
        e = self.entities.get(entity_id)
        return e if isinstance(e, Player) else None

    def get_player_by_account_uid(self, uid):
        """按**账号 id** 反查 —— 这是参考实现缺失、导致 errHandler 空操作的入口。"""
        pid = self.users.get(int(uid))
        return self.get_player(pid) if pid is not None else None

    def get_all_players(self):
        return [self.entities[eid] for eid in list(self.players.values())
                if eid in self.entities]

    def is_empty(self):
        return self.player_num == 0

    # ── AOI 查询（绝不碰 socket，只返回 id/实体）───────────────────────
    def watchers_of(self, x, y, r, types=None):
        if self.aoi is None:
            return []
        return self.aoi.watchers_of(x, y, r, types)

    def entities_near(self, x, y, r):
        """按坐标+半径取**游戏实体**。

        ⚠ `aoi.entities_near()` 返回的是 aoi 自己的轻量 `Entity`（uid/x/y/range/types），
        **不是** world 的实体 ⇒ 必须用 uid（= entity_id）回查 `self.entities` 做映射。
        """
        if self.aoi is None:
            return []
        out = []
        for ae in self.aoi.entities_near(x, y, r):
            e = self.entities.get(ae.uid)
            if e is not None:
                out.append(e)
        return out

    def area_info_strip(self, x, y, r, include_npcs=True):
        """进入场景时的可见性快照。

        ★ 参考实现顺序：**先取快照，再 addEntity**（否则自己会出现在自己的列表里）。
        ★ NPC 不进 AOI，故在此全量并入（参考实现的 getAreaInfoStrip 同样如此）。
        """
        out = {}
        for e in self.entities_near(x, y, r):
            out.setdefault(e.type, []).append(e.strip())
        if include_npcs:
            for npc in self.npcs.values():
                out.setdefault(npc.type, []).append(npc.strip())
        return out

    def get_entities_by_pos(self, x, y, types, r):
        """按坐标+类型取实体（技能范围判定用）。"""
        out = {}
        for e in self.entities_near(x, y, r):
            if types and not (e.type & types):
                continue
            out.setdefault(e.type, []).append(e)
        return out

    # ── 三层 tick ──────────────────────────────────────────────────────
    def tick(self, dt):
        """100ms：掉落物超时 → 动作推进（含 AOI 更新）。"""
        now = self._clock()
        # ① 地面物超时消失
        for eid in list(self.items.keys()):
            it = self.entities.get(eid)
            if it is None:
                self.items.pop(eid, None)
                continue
            if isinstance(it, Item) and it.update(now):
                self._stats['expired_items'] += 1
                self._broadcast_remove([eid])
                self.remove_entity(eid, now=now)
        # ② 动作推进（顺序刻意在 AI 之前：AI 才能读到最新位置）
        for action, ret in self.actions.update(dt):
            if isinstance(action, MoveAction) and ret:
                old, new = ret
                self._on_entity_moved(action.entity, old, new)

    def tick_1s(self):
        """1.0s：刷怪刷物（zone 内部再以 interval 节流 ⇒ 实际约 5s 一批）。"""
        now = self._clock()
        made = 0
        for z in self.zones.values():
            made += z.update(now)
        return made

    def tick_3s(self):
        """3.0s：玩家 HP/MP 恢复 + 心跳超时踢人。

        ★★ 这是 **HP/MP 恢复的唯一驱动点**（Q1 决策 = 3.0s）。
        参考实现是 3.1s；若误挂到 100ms 层，回血会快 30 倍。
        """
        now = self._clock()
        kicked = []
        recovered = []
        for p in self.get_all_players():
            if p.kick_time and now > p.kick_time:
                kicked.append(p)
                continue
            hp_d, mp_d = p.update_recover()
            if hp_d or mp_d:
                recovered.append((p, hp_d, mp_d))
        # 先处理恢复推送（推给自己 + 广播回血数字给附近的人）
        for p, hp_d, mp_d in recovered:
            msg = {}
            if hp_d:
                msg['hp'] = p.hp
            if mp_d:
                msg['mp'] = p.mp
            if self._ms is not None and msg:
                self._ms.send(p, 'onHpMp', msg)
                if hp_d:
                    self._ms.send_by_aoi(self, 'onHp2All', {'entityId': p.entity_id,
                                                            'delta': hp_d},
                                         (p.x, p.y), ignore={p.id})
        # 再踢超时玩家（由 AreaManager 收尾：存档/清缓存/清社交）
        for p in kicked:
            self._stats['kicked'] += 1
            self.remove_entity(p.entity_id, now=now)
        return {'kicked': kicked, 'recovered': len(recovered)}

    # ── AOI 事件派发 ───────────────────────────────────────────────────
    def _on_entity_moved(self, entity, old, new):
        """实体移动 → AOI 一次双向更新 + 事件派发。

        ★ 用 `aoi.move()`（一次双向），而不是"必须成对调用、漏一个就单向失明"。
        """
        if self.aoi is None or self._ms is None:
            return
        self_events, watch_events = self.aoi.move(entity.entity_id, new[0], new[1])
        self._dispatch_self_events(entity, self_events)
        self._dispatch_watch_events(watch_events)

    def _dispatch_self_events(self, entity, events):
        """我该增删的视野对象（发给"我"）。"""
        adds, removes = {}, []
        for other_id, ev in events:
            other = self.entities.get(other_id)
            if other is None:
                continue
            if ev == 'enter':
                adds.setdefault(other.type, []).append(other.strip())
                self._stats['aoi_enter'] += 1
            else:
                removes.append(other_id)
                self._stats['aoi_leave'] += 1
        if adds:
            self._ms.send(entity, 'onAddEntities', adds)
        if removes:
            self._ms.send(entity, 'onRemoveEntities', {'entities': removes})

    def _dispatch_watch_events(self, events):
        """该被告知我动向的人（发给"别人"）。events: [(watcher_id, ev, obj_id)]"""
        by_target = {}
        for w_id, ev, obj_id in events:
            by_target.setdefault(w_id, []).append((ev, obj_id))
        for w_id, items in by_target.items():
            watcher = self.entities.get(w_id)
            if watcher is None:
                continue
            adds, removes = {}, []
            for ev, obj_id in items:
                obj = self.entities.get(obj_id)
                if ev == 'enter':
                    if obj is None:
                        continue
                    adds.setdefault(obj.type, []).append(obj.strip())
                    self._stats['aoi_enter'] += 1
                else:
                    removes.append(obj_id)
                    self._stats['aoi_leave'] += 1
            if adds:
                self._ms.send(watcher, 'onAddEntities', adds)
            if removes:
                self._ms.send(watcher, 'onRemoveEntities', {'entities': removes})

    def _broadcast_remove(self, entity_ids):
        ch = self.get_channel()
        if ch is not None:
            ch.push_message('onRemoveEntities', {'entities': list(entity_ids)})

    def broadcast(self, route, msg):
        ch = self.get_channel()
        if ch is None:
            return 0
        return ch.push_message(route, msg)

    # ── 观测 ───────────────────────────────────────────────────────────
    def stats(self):
        s = dict(self._stats)
        s.update({
            'areaId': self.area_id,
            'instanceId': self.instance_id,
            'entities': len(self.entities),
            'players': self.player_num,
            'items': len(self.items),
            'npcs': len(self.npcs),
            'zones': len(self.zones),
            'actions': len(self.actions),
            'aoi': (self.aoi.stats() if self.aoi is not None else None),
        })
        return s

    def __repr__(self):
        return '<Area %s%s players=%d entities=%d>' % (
            self.area_id, ('/' + str(self.instance_id)) if self.instance_id else '',
            self.player_num, len(self.entities))


def _now():
    import time
    return time.time()
