"""五层容器：AreaManager(R1) / Scene(R3) / Instance(R3) / InstancePool(R4)。

═══════════════════════════════════════════════════════════════════════════
层级归属规则（补齐参考实现没说清的部分）：
  R1 需要**跨场景/跨副本**视角的数据        → AreaManager
  R2 属于**一个世界实例**的数据             → Area（见 area.py）
  R3 只是**世界实例的包装/路由**            → Scene / Instance
  R4 **多个世界实例的生命周期管理**         → InstancePool

★ 一份 Player 对象、三套索引：
      AreaManager.players[player_id]  ─┐
                                       ├─ 同一个 Player 对象
      Area.players[player_id]=entity_id│
      Area.users[uid]=player_id       ─┘
  ⇒ 由此产生一个**必须显式处理的中间态**：Player 可能已在 AreaManager.players，
    但不在任何 Area.players 里（刚登录 / 换场景途中 / 已下线待缓存）。
    参考实现用 playerFilter 兜这个态（route 不以 enterScene 结尾就推 onChangeArea）。
    JSTM 把它建模成 `PlayerLocation.NONE`，并在守卫里显式判断（见 guards.py）。

★ 并发模型：既有服务器是**多线程**，故这里用 `threading.Lock`（每玩家一把），
  而不是 asyncio.Lock。参考实现用 `requestList` + 字符串 'waiting' 当致命错误，
  会让高并发首登偶发失败；这里改为**等待**。
"""

from __future__ import annotations

import threading
import time

from . import _deps
from .area import Area
from .consts import (Code, INSTANCE_GC_INTERVAL, INSTANCE_LIFE_TIME,
                     LocationKind, PLAYER_CACHE_TTL)
from .entities import PlayerLocation


# ══════════════════════════════════════════════════════════════════════════
# 小工具：真 TTL 缓存（参考实现的 playerCaches 是"边写边全清"，等于没缓存）
# ══════════════════════════════════════════════════════════════════════════
class TTLCache(object):
    def __init__(self, ttl=60.0, clock=time.time):
        self.ttl = float(ttl)
        self._clock = clock
        self._data = {}          # key -> (expire_at, value)
        self._stats = {'hit': 0, 'miss': 0, 'expired': 0, 'evicted': 0}

    def set(self, key, value):
        self._data[key] = (self._clock() + self.ttl, value)
        self._sweep()
        return value

    def get(self, key):
        item = self._data.get(key)
        if item is None:
            self._stats['miss'] += 1
            return None
        expire_at, value = item
        if self._clock() >= expire_at:
            self._data.pop(key, None)
            self._stats['expired'] += 1
            self._stats['miss'] += 1
            return None
        self._stats['hit'] += 1
        return value

    def pop(self, key):
        item = self._data.pop(key, None)
        return item[1] if item else None

    def find_by(self, pred):
        self._sweep()
        for _k, (_e, v) in list(self._data.items()):
            if pred(v):
                return v
        return None

    def _sweep(self):
        now = self._clock()
        dead = [k for k, (e, _v) in self._data.items() if now >= e]
        for k in dead:
            self._data.pop(k, None)
            self._stats['expired'] += 1
            self._stats['evicted'] += 1

    def __len__(self):
        self._sweep()
        return len(self._data)

    def stats(self):
        s = dict(self._stats)
        s['size'] = len(self)
        s['ttl'] = self.ttl
        return s


# ══════════════════════════════════════════════════════════════════════════
# R3：包装
# ══════════════════════════════════════════════════════════════════════════
class Scene(object):
    """常驻场景：只是 Area 的薄包装。"""

    def __init__(self, area):
        self.area = area
        self.id = area.area_id

    def get_player_in_area(self):
        return self.area

    def remove_player_by_uid(self, uid):
        return self.area.remove_player_by_uid(uid)

    def __repr__(self):
        return '<Scene %s>' % self.id


class Instance(object):
    """副本：Area + 生命周期。

    ★ `life_time` 从构造参数来（= 配置），**不再硬编码 300000**。
      参考实现把 `config/instance.json` 的 lifeTime=1800000 覆盖成 300000，
      配置成了死配置。
    """

    def __init__(self, area, life_time=INSTANCE_LIFE_TIME):
        self.area = area
        self.id = area.instance_id
        self.life_time = float(life_time)

    def start(self):
        return self.area.start()

    def close(self):
        self.area.close()

    def get_area(self):
        return self.area

    def is_alive(self, now=None):
        now = time.time() if now is None else now
        if not self.area.is_empty():
            return True
        et = self.area.empty_time
        if et is None:                 # 未记录空场时间 ⇒ 保守认为还活着
            return True
        # ★ 显式比较，不用 truthiness（empty_time 完全可能是 0.0 或很小的值）
        return not ((now - et) > self.life_time)

    def __repr__(self):
        return '<Instance %s players=%d>' % (self.id, self.area.player_num)


class InstancePool(object):
    """R4：副本池。单进程下**本地回收**（参考实现要跨进程问 manager）。"""

    def __init__(self, manager):
        self._m = manager
        self.instances = {}
        self._last_gc = 0.0
        self._stats = {'created': 0, 'closed': 0, 'alive': 0}

    def create(self, area_id, instance_id, life_time=None):
        if instance_id in self.instances:
            return Code.INSTANCE_EXISTS
        cfg = self._m.area_config(area_id)
        area = self._m.build_area(area_id, instance_id=instance_id, cfg=cfg)
        inst = Instance(area, life_time or self._m.instance_life_time)
        self.instances[instance_id] = inst
        inst.start()
        self._stats['created'] += 1
        return Code.OK

    def get(self, instance_id):
        return self.instances.get(instance_id)

    def remove(self, instance_id):
        inst = self.instances.pop(instance_id, None)
        if inst is None:
            return False
        inst.close()
        self._stats['closed'] += 1
        return True

    def collect_garbage(self, now=None, force=False):
        now = time.time() if now is None else now
        if not force and (now - self._last_gc) < INSTANCE_GC_INTERVAL:
            return []
        self._last_gc = now
        dead = [iid for iid, inst in self.instances.items() if not inst.is_alive(now)]
        for iid in dead:
            self.remove(iid)
        return dead

    def all_instances(self):
        return [self.instances[k] for k in sorted(self.instances.keys())]

    def stats(self):
        s = dict(self._stats)
        s['alive'] = len(self.instances)
        s['ids'] = sorted(self.instances.keys())
        return s


# ══════════════════════════════════════════════════════════════════════════
# R1：进程级注册表
# ══════════════════════════════════════════════════════════════════════════
class AreaManager(object):
    """全世界（单进程）。"""

    def __init__(self, message_service=None, channel_service=None,
                 mapgrid=None, area_configs=None, loader=None,
                 ratelimiter=None, clock=None,
                 instance_life_time=INSTANCE_LIFE_TIME,
                 player_cache_ttl=PLAYER_CACHE_TTL, tower_size=8, logger=None):
        self._ms = message_service
        self._cs = channel_service
        self._mapgrid = mapgrid
        self._configs = dict(area_configs or {})
        self._loader = loader                 # player_id -> Player | None（查库）
        self._ratelimiter = ratelimiter       # pathfind.MoveRateLimiter（复用既有模块）
        self._clock = clock or time.time      # 可注入时钟
        self.instance_life_time = float(instance_life_time)
        self.tower_size = int(tower_size)
        self._log = logger

        self.scenes_by_id = {}                # area_id -> Scene
        self.players = {}                     # player_id -> Player（在线）
        self.player_cache = TTLCache(ttl=player_cache_ttl)
        self.instances = {}                   # instance_id -> Instance（便捷索引）
        self.player_to_instance = {}
        self.instance_pool = InstancePool(self)

        self._locks = {}                      # player_id -> threading.Lock
        self._locks_guard = threading.Lock()
        self.lock = threading.RLock()         # 世界级粗锁（P1：tick 与网络线程共用）
        self._stats = {'loaded': 0, 'cache_hit': 0, 'cache_promote': 0,
                       'force_cleanup': 0, 'area_changes': 0}

        if self._ms is not None:
            # ★ 唯一底层 send 的失败回调：连续失败才判定断线
            self._ms.on_unreachable = self.force_cleanup

    # ── 构建 ───────────────────────────────────────────────────────────
    def area_config(self, area_id):
        return self._configs.get(int(area_id))

    def get_ratelimiter(self):
        """移动限流器（复用 `server/pathfind.py` 的 MoveRateLimiter）。"""
        if self._ratelimiter is None:
            self._ratelimiter = _deps.new_ratelimiter()
        return self._ratelimiter

    def build_area(self, area_id, instance_id=None, cfg=None):
        cfg = cfg or self.area_config(area_id) or {}
        return Area(
            area_id, mapgrid=self._mapgrid, instance_id=instance_id,
            area_type=cfg.get('type', 1), area_kind=cfg.get('kind', 2),
            tower_size=cfg.get('tower_size', self.tower_size),
            message_service=self._ms, channel_service=self._cs,
            logger=self._log, name=cfg.get('name', ''), clock=self._clock,
        )

    def init_scenes(self, area_ids):
        """建场景（**不启动** —— 由调用方显式 start_all）。"""
        for aid in area_ids:
            cfg = self.area_config(aid)
            if cfg is None:
                if self._log:
                    self._log('!! area config missing area_id=%s' % aid)
                continue
            self.scenes_by_id[int(aid)] = Scene(self.build_area(aid, cfg=cfg))

    def start_all(self):
        """统一启动（参考实现是在构造器里逐个 start，无法批量控制）。"""
        n = 0
        for sc in self.scenes_by_id.values():
            if sc.area.start():
                n += 1
        return n

    # ── 确定性的遍历顺序（参考实现是每 Area 各起定时器，顺序不确定）──────
    def ordered_areas(self):
        out = [self.scenes_by_id[k].area for k in sorted(self.scenes_by_id.keys())]
        out.extend(inst.get_area() for inst in self.instance_pool.all_instances())
        return out

    # ── 三层 tick 入口（由 TickScheduler 调用）──────────────────────────
    def tick_all(self, dt):
        for a in self.ordered_areas():
            a.tick(dt)

    def tick_1s_all(self):
        n = 0
        for a in self.ordered_areas():
            n += a.tick_1s()
        return n

    def tick_3s_all(self):
        out = {'kicked': [], 'recovered': 0}
        for a in self.ordered_areas():
            r = a.tick_3s()
            out['kicked'].extend(r['kicked'])
            out['recovered'] += r['recovered']
        # 被踢/超时下线的玩家：交给上层收尾（存档/社交清理）
        for p in out['kicked']:
            self.cache_offline_player(p)
        self.instance_pool.collect_garbage()
        return out

    # ── 玩家：两级读取 + 每玩家锁（修正参考实现的 'waiting' bug）────────
    def _lock_for(self, player_id):
        with self._locks_guard:
            lk = self._locks.get(player_id)
            if lk is None:
                lk = self._locks[player_id] = threading.Lock()
            return lk

    def get_player(self, player_id):
        """内存 → 下线缓存 → None。命中缓存会**提升回在线**。"""
        pid = int(player_id)
        p = self.players.get(pid)
        if p is not None:
            return p
        p = self.player_cache.get(pid)
        if p is not None:
            self.player_cache.pop(pid)
            self.players[pid] = p
            self._stats['cache_promote'] += 1
        return p

    def get_or_load_player(self, player_id, timeout=5.0):
        """带**每玩家锁**的加载。并发同一玩家时会等待而不是报错。"""
        pid = int(player_id)
        p = self.get_player(pid)
        if p is not None:
            self._stats['cache_hit'] += 1
            return p
        lk = self._lock_for(pid)
        acquired = lk.acquire(timeout=timeout)
        if not acquired:
            return None
        try:
            p = self.get_player(pid)          # 双检
            if p is not None:
                return p
            if self._loader is None:
                return None
            p = self._loader(pid)
            if p is not None:
                self.players[pid] = p
                self._stats['loaded'] += 1
            return p
        finally:
            lk.release()

    def remove_player(self, player_id):
        self.players.pop(int(player_id), None)

    def cache_offline_player(self, player):
        """下线 → **先退出世界实例** → 再进 TTL 缓存。

        ★ 顺序很重要（对应参考实现 `playerRemote.playerLeave`：
          `area.exitArea(player)` 之后才 `areaManager.addPlayerCaches(player)`）：
          必须先从 Area 摘掉，否则：
            · 场景频道会残留成员（幽灵接收者）
            · AOI 里会留下死实体
            · Area.player_num 不准，导致空副本永远回收不掉
        """
        if player is None:
            return
        area = self.get_area_by_player(player)
        if area is not None and area.get_player(player.id) is not None:
            area.remove_player(player.id)
        self.remove_player(player.id)
        player.session_addr = None
        player.location = PlayerLocation.none()
        self.player_cache.set(player.id, player)
        if self._ms is not None:
            self._ms.clear_player(player.id)

    def force_cleanup(self, player_id):
        """推送连续失败的兜底清理（替代参考实现的空操作 errHandler）。"""
        self._stats['force_cleanup'] += 1
        pid = int(player_id)
        p = self.players.get(pid)
        if p is None:
            return False
        area = self.get_area_by_player(p)
        if area is not None:
            area.remove_player(pid)
        self.cache_offline_player(p)
        return True

    def find_by_uid(self, uid):
        """★ 参考实现缺失的 uid → Player 反查入口（正是 errHandler 坏掉的根因）。"""
        for p in self.players.values():
            if p.uid == int(uid):
                return p
        return self.player_cache.find_by(lambda p: p.uid == int(uid))

    # ── 定位 ───────────────────────────────────────────────────────────
    def get_area_by_player(self, player):
        if player is None:
            return None
        loc = player.location
        if loc.kind == LocationKind.SCENE:
            sc = self.scenes_by_id.get(loc.area_id)
            return sc.get_player_in_area() if sc is not None else None
        if loc.kind == LocationKind.INSTANCE:
            inst = self.instance_pool.get(loc.instance_id)
            return inst.get_area() if inst is not None else None
        return None

    def get_area(self, area_id, instance_id=None):
        if instance_id:
            inst = self.instance_pool.get(instance_id)
            if inst is not None:
                return inst.get_area()
        sc = self.scenes_by_id.get(int(area_id))
        return sc.get_player_in_area() if sc is not None else None

    def get_player_in_area(self, player_id, instance_id=None):
        p = self.get_player(player_id)
        if p is None:
            return None
        return self.get_area_by_player(p)

    # ── 换场景 / 进副本（单一分派点）──────────────────────────────────
    def change_area(self, player, target_id, arg_id=None, is_my_boss=False):
        cfg = self.area_config(target_id)
        if cfg is None:
            return Code.AREA_NOT_FOUND
        if cfg.get('type', 1) <= 1:            # SCENE
            return self._goto_scene(player, target_id, cfg)
        return self._goto_instance(player, target_id, cfg, arg_id, is_my_boss)

    def _goto_scene(self, player, target_id, cfg):
        if player.location.kind == LocationKind.SCENE and player.location.area_id == int(target_id):
            return Code.SAME_AREA
        cur = self.get_area_by_player(player)
        if cur is not None:
            cur.remove_player(player.id)
        pos = self.get_init_point(target_id, cur.area_id if cur else 0, cfg=cfg)
        player.x, player.y = pos
        player.location = PlayerLocation.scene(target_id)
        self._stats['area_changes'] += 1
        return Code.OK

    def _goto_instance(self, player, target_id, cfg, arg_id=None, is_my_boss=False):
        kind = cfg.get('kind', 2)
        if kind == 3:                          # FIGHT_AREA
            suffix = 'fight_%s' % (arg_id or '0')
        elif kind == 4:                        # MY_BOSS_AREA
            if not is_my_boss:
                return Code.FAIL
            suffix = 'my_%s%s' % (player.id, int(target_id) % 10)
        elif kind == 5:                        # WORLD_BOSS_AREA
            suffix = 'boss'
        else:
            suffix = 'sin_%s' % player.id      # ★ 命名即共享域
        instance_id = '%s_%s' % (target_id, suffix)

        cur = self.get_area_by_player(player)
        if cur is not None:
            cur.remove_player(player.id)
        code = self.instance_pool.create(target_id, instance_id, self.instance_life_time)
        if code not in (Code.OK, Code.INSTANCE_EXISTS):
            return code
        inst = self.instance_pool.get(instance_id)
        self.instances[instance_id] = inst
        self.player_to_instance[player.id] = instance_id
        pos = self.get_init_point(target_id, cur.area_id if cur else 0, cfg=cfg)
        player.x, player.y = pos
        player.location = PlayerLocation.instance(instance_id, target_id)
        self._stats['area_changes'] += 1
        return Code.OK

    def remove_instance(self, instance_id):
        self.instances.pop(instance_id, None)
        for pid, iid in list(self.player_to_instance.items()):
            if iid == instance_id:
                self.player_to_instance.pop(pid, None)
        return self.instance_pool.remove(instance_id)

    # ── 出生点 / 传送落点 ──────────────────────────────────────────────
    def get_born_point(self, area_id):
        cfg = self.area_config(area_id) or {}
        return (int(cfg.get('born_x', 0)), int(cfg.get('born_y', 0)))

    def get_init_point(self, target_id, cur_area_id, cfg=None):
        """传送落点：支持"来源反转"（参考实现 areaService.getInitPoint 的思想）：
        若目标地图的某个传送点指向来源场景，则落在该传送点附近，
        否则回出生点。**避免"从 B 回 A 时落在 A 的传送阵里"造成循环。**"""
        cfg = cfg or self.area_config(target_id) or {}
        for t in cfg.get('transports', ()):     # [{'target_area':..,'x':..,'y':..}]
            if int(t.get('target_area', -1)) == int(cur_area_id):
                return (int(t.get('x', 0)) + 2, int(t.get('y', 0)) - 1)
        return self.get_born_point(target_id)

    # ── 观测 ───────────────────────────────────────────────────────────
    def stats(self):
        with self.lock:
            return {
                'scenes': len(self.scenes_by_id),
                'players_online': len(self.players),
                'player_cache': self.player_cache.stats(),
                'instances': self.instance_pool.stats(),
                'locks': len(self._locks),
                'counters': dict(self._stats),
            }
