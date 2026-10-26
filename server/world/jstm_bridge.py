"""★ JSTM 世界层 ←→ mock_server 的**桥接层**（dormant by default）。

═══════════════════════════════════════════════════════════════════════════
## 为什么需要这一层（先说清现状，避免"两套实现并存"）

审计 kongkongxiyou 时发现的最大维护陷阱就是**同一个功能有两套实现并存**
（`areaManager.changeArea` 与 `areaService.changeArea`，只有一套被调用）。

本服务器**已经有**一套 10204 的 AOI 接线（`mock_server.py`，标注"第二阶段"），
它写得克制且零回归：
  `_scene_enter / _scene_ensure / _scene_leave / _scene_validate_move / _scene_apply_move`
  `_scene_broadcast_10204`     ← ★ 这个**已经**接受 watcher 集合作为参数，天然解耦

所以本桥接层**不新增第二条 10204 通路**，而是作为一个**可切换的后端**：
把上面 5 个"判定类"函数换成由 `world/` 五层容器 + 分层 tick 驱动的实现，
**`_scene_broadcast_10204` 原样保留**（发包属于 mock_server 的职责）。

⇒ 边界划分（与 `aoi.md` 的"**AOI 绝不碰 socket**"同一原则）：
      · `world/` 负责 **谁应该看见我**（决策）
      · `mock_server` 负责 **怎么把包发出去**（I/O）

## 职责对照表（切过来时逐条等价）

| mock_server 现有函数 | 本桥接层方法 | world/ 里对应能力 |
|---|---|---|
| `_scene_enter(handler)` | `WorldBridge.scene_enter` | `AreaManager.get_or_load_player` + `Area.add_entity`（AOI **双注册**） |
| `_scene_ensure(handler)` | `WorldBridge.scene_ensure` | 幂等标志（同语义） |
| `_scene_leave(handler)` | `WorldBridge.scene_leave` | `AreaManager.cache_offline_player`（**先退出 Area 再进 TTL 缓存**） |
| `_scene_validate_move(h, rid, x, y, cmd)` | `WorldBridge.validate_move` | `move.validate_step_move`（**默认不拒人**，见下） |
| `_scene_apply_move(h, rid, x, y)` | `WorldBridge.apply_move` | `Area.move_player` → `aoi.watchers_seeing(rid)` |
| `_scene_broadcast_10204(...)` | **不替换** | （发包留给 mock_server） |
| `_LAST_POS[rid]` | `WorldBridge.last_pos` | `Player.x/y`（服务端权威坐标） |
| 全局单例 AOI（`get_aoi()`） | 每 Area 一个 AOI | 副本之间视野隔离 |

## ★ 三条**必须保留**的既有设计约定（否则会误杀正常玩家）

1. **校验失败时回复"服务端权威坐标"，而不是静默丢弃**
   —— 静默丢弃会让客户端与服务端**永久错位**。
2. **限流默认关闭**（`move_rate_limit=false`）。`mock_server` 的注释已写明：
   "12 格/秒是拍的，未按真机 10204 标定前打开会误杀正常玩家"（aoi_pathfind_review.md P5）。
   ⇒ 本桥接层的 `enforce_rate_limit` 同样**默认 False**。
3. **异常一律放行（fail-open）**。AOI/世界层出任何问题都不得影响移动与登录链路。

## 激活方式（dormant by default）

`config.json` 加一个开关即可（不加则**完全不生效**）：
```json
{ "world_bridge_enabled": true }
```
然后在 `mock_server.py` 里加 4 行（**可整段删除以回退**）：

```python
try:                                   # ← 世界层桥接（默认关闭，见 world/jstm_bridge.py）
    from world.jstm_bridge import attach as _attach_world_bridge
    _attach_world_bridge(globals())
except Exception as _e:
    print('!! world bridge attach failed: %r' % (_e,))
```

放在 `_scene_broadcast_10204` 定义**之后**、`class Handler` **之前**。
`attach()` 只在开关打开时才重绑那 5 个名字，并打印被替换的函数名。
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations


from . import _deps
from .consts import EntityType
from .containers import AreaManager
from .entities import Player, PlayerLocation
from .message import ChannelService, MessageService
from .move import validate_step_move

# 桥接层要接管的 5 个 mock_server 模块级函数名（`_scene_broadcast_10204` 故意不在其中）
TAKEOVER = (
    '_scene_enter',
    '_scene_ensure',
    '_scene_leave',
    '_scene_validate_move',
    '_scene_apply_move',
)

DEFAULT_AREA_ID = 10001          # 与 mock_server 的 `spawn.bid` 默认值一致
DEFAULT_VIEW_RANGE = 15          # 与 mock_server 的 aoi_view_range 默认值一致
DEFAULT_TOWER_SIZE = 8           # 与 aoi_tower_size 默认一致


class WorldBridge(object):
    """把 mock_server 的场景判定接到 world/ 上。

    所有公开方法都**不抛异常**（fail-open）—— 与 mock_server 既有约定一致。
    """

    def __init__(self, ns, enabled=None, logger=None):
        self.ns = ns
        self._log = logger or ns.get('log')
        cfg = ns.get('CFG') or {}
        self.cfg = cfg
        if enabled is None:
            enabled = bool(cfg.get('world_bridge_enabled', False))
        self.enabled = bool(enabled)

        self.area_id = int(cfg.get('spawn', {}).get('bid') or DEFAULT_AREA_ID) \
            if isinstance(cfg.get('spawn'), dict) else DEFAULT_AREA_ID
        self.view_range = int(cfg.get('aoi_view_range', DEFAULT_VIEW_RANGE))
        self.tower_size = int(cfg.get('aoi_tower_size', DEFAULT_TOWER_SIZE))
        # ★ 默认关：与 mock_server 的 move_rate_limit 默认值一致
        self.enforce_rate_limit = bool(cfg.get('move_rate_limit', False))

        self.world = None
        self._area = None
        self._replaced = []
        self._stats = {'enter': 0, 'leave': 0, 'validate_reject': 0,
                       'validate_pass': 0, 'apply': 0, 'errors': 0}

    # ── 装配 ───────────────────────────────────────────────────────────
    def build(self):
        """建世界。**只读 CFG，不碰 socket**，因此可离线构造（便于单测）。"""
        grid = None
        get_mapgrid = self.ns.get('get_mapgrid')
        if callable(get_mapgrid):
            grid = get_mapgrid()
        if grid is None:
            grid = _deps.new_mapgrid(256, 256, allow_all=True)

        ratelimiter = None
        get_rl = self.ns.get('get_ratelimit')
        if callable(get_rl):
            ratelimiter = get_rl()

        ms = MessageService(router=None, logger=None)          # 出网由 mock_server 负责
        cs = ChannelService(ms, resolve_player=lambda pid: self.world.get_player(pid))
        self.world = AreaManager(
            message_service=ms, channel_service=cs, mapgrid=grid,
            area_configs={self.area_id: {'id': self.area_id, 'type': 1, 'kind': 2,
                                        'born_x': 100, 'born_y': 100,
                                        'tower_size': self.tower_size}},
            ratelimiter=ratelimiter, clock=None, tower_size=self.tower_size,
        )
        self.world.init_scenes([self.area_id])
        self.world.start_all()
        self._area = self.world.get_area(self.area_id)
        return self.world

    def _ensure_built(self):
        if self.world is None:
            self.build()
        return self.world is not None

    def _rid(self, handler):
        f = self.ns.get('_scene_rid')
        if callable(f):
            return f(handler)
        try:
            return int(getattr(handler, '_aoi_rid', None) or 1001)
        except Exception:
            return None

    # ── 进入 / 离开 ────────────────────────────────────────────────────
    def scene_enter(self, handler):
        """登记进世界（**AOI 双注册**由 Area.add_entity 保证）。"""
        try:
            if not self._ensure_built():
                return
            rid = self._rid(handler)
            if rid is None:
                return
            role = self._role_with_pos(handler)
            x = int(role.get('x', 100)) if role else 100
            y = int(role.get('y', 100)) if role else 100
            p = self.world.get_player(rid)
            if p is None:
                p = Player(rid, uid=self._uid_of(handler, rid), name=str(role.get('name', '')) if role else '',
                           x=x, y=y, range_=self.view_range)
                self.world.players[rid] = p
            else:
                p.x, p.y = x, y
                p.range = self.view_range
            p.location = PlayerLocation.scene(self.area_id)
            if self._area.get_player(rid) is not None:
                self._area.remove_player(rid)
            self._area.add_entity(p)
            self._stats['enter'] += 1
        except Exception as e:
            self._fail('enter', e)

    def scene_ensure(self, handler):
        try:
            if getattr(handler, '_world_bridge_in', False):
                return
            self.scene_enter(handler)
            handler._world_bridge_in = True
        except Exception as e:
            self._fail('ensure', e)

    def scene_leave(self, handler):
        try:
            rid = getattr(handler, '_world_bridge_rid', None) or self._rid(handler)
            handler._world_bridge_in = False
            if rid is None or self.world is None:
                return
            p = self.world.get_player(rid)
            if p is not None:
                # ★ 先退出 Area（摘频道/AOI），再进 TTL 缓存
                self.world.cache_offline_player(p)
            self._stats['leave'] += 1
        except Exception as e:
            self._fail('leave', e)

    # ── 移动判定 ───────────────────────────────────────────────────────
    def validate_move(self, handler, rid, x, y, cmd):
        """返回 None=通过；返回 (ax, ay)=拒绝并给出**服务端权威坐标**。"""
        try:
            if not self._ensure_built():
                return None
            last = self.last_pos(handler, rid)
            ok, why, corrected = validate_step_move(
                self._area.map, last, x, y,
                uid=rid, limiter=self.world.get_ratelimiter(),
                enforce_rate_limit=self.enforce_rate_limit,
            )
            if ok:
                self._stats['validate_pass'] += 1
                return None
            self._stats['validate_reject'] += 1
            self._log_line('.. [world] cmd=%s rid=%s 移动被拒(%s) → 权威坐标 %r'
                           % (cmd, rid, why, corrected))
            return (int(corrected[0]), int(corrected[1]))
        except Exception as e:
            self._fail('validate', e)
            return None                      # ★ fail-open

    def apply_move(self, handler, rid, x, y):
        """接受移动：更新世界坐标 + AOI（双向）→ 返回"看得见我的 rid 集合"。"""
        try:
            if not self._ensure_built():
                return set()
            p = self.world.get_player(rid)
            if p is None:
                p = Player(rid, uid=self._uid_of(handler, rid), x=x, y=y,
                           range_=self.view_range)
                self.world.players[rid] = p
                p.location = PlayerLocation.scene(self.area_id)
                self._area.add_entity(p)
            p.x, p.y = int(x), int(y)
            if self._area.aoi is not None:
                self._area.aoi.move(p.entity_id, p.x, p.y)
            self._stats['apply'] += 1
            return self.watchers_seeing(p.entity_id)
        except Exception as e:
            self._fail('apply', e)
            return set()

    # ── 查询辅助 ───────────────────────────────────────────────────────
    def last_pos(self, handler, rid):
        """服务端权威坐标：优先内存（世界），其次 DB（与 mock_server 同序）。"""
        try:
            p = self.world.get_player(rid) if self.world else None
            if p is not None:
                return (p.x, p.y)
        except Exception:
            pass
        role = self._role_with_pos(handler)
        if role:
            return (int(role.get('x', 100)), int(role.get('y', 100)))
        return (100, 100)

    def watchers_seeing(self, entity_id):
        """"看得见我的人"（= Survive `watch_me` 语义）。"""
        try:
            if self._area is None or self._area.aoi is None:
                return set()
            f = getattr(self._area.aoi, 'watchers_seeing', None)
            if callable(f):
                return set(f(entity_id))
            # 回退：用坐标反查（旧版 aoi.py 没有 watchers_seeing）
            p = self._area.entities.get(entity_id)
            if p is None:
                return set()
            return set(self._area.watchers_of(p.x, p.y, self.view_range, EntityType.PLAYER))
        except Exception as e:
            self._fail('watchers_seeing', e)
            return set()

    # ── 内部 ───────────────────────────────────────────────────────────
    def _role_with_pos(self, handler):
        f = self.ns.get('role_with_saved_pos')
        if callable(f):
            try:
                return f(getattr(handler, 'cfg', None)) or {}
            except Exception:
                return {}
        return {}

    def _uid_of(self, handler, rid):
        """账号 uid：mock_server 的场景里只有 rid，故退化为 rid+偏移。

        ★ 只要**保证 uid ≠ rid** 即可 —— 参考项目的 errHandler 就是因为
          把 uid 当 playerId 用（两者混同）而静默失效（见 pomelo.md 4.2）。
        """
        try:
            st = self.ns.get('role_state')
            if callable(st):
                v = st(getattr(handler, 'cfg', None)) or {}
                uid = v.get('uid')
                if uid:
                    return int(uid)
        except Exception:
            pass
        return int(rid) + 900000

    def _log_line(self, s):
        if callable(self._log):
            try:
                self._log('tcp.log', s)
            except Exception:
                pass

    def _fail(self, where, e):
        self._stats['errors'] += 1
        self._log_line('!! [world] %s 失败（忽略，不影响链路）: %r' % (where, e))

    # ── attach ─────────────────────────────────────────────────────────
    def attach(self):
        """把 5 个判定函数重绑到本桥接层。返回被替换的名字列表。"""
        if not self.enabled:
            return []
        self._ensure_built()
        mapping = {
            '_scene_enter': self.scene_enter,
            '_scene_ensure': self.scene_ensure,
            '_scene_leave': self.scene_leave,
            '_scene_validate_move': self.validate_move,
            '_scene_apply_move': self.apply_move,
        }
        for name, fn in mapping.items():
            if name in self.ns:                 # 只在原本存在时替换（不凭空新建）
                self.ns[name] = fn
                self._replaced.append(name)
        self._log_line('.. [world] 桥接已启用，接管 %d 个函数: %s'
                       % (len(self._replaced), ', '.join(self._replaced)))
        return list(self._replaced)

    def stats(self):
        s = dict(self._stats)
        s['enabled'] = self.enabled
        s['replaced'] = list(self._replaced)
        s['area_id'] = self.area_id
        if self._area is not None:
            s['area'] = self._area.stats()
        return s


def attach(ns, enabled=None, logger=None):
    """给 mock_server 用的入口。返回值便于诊断；**任何异常都不外抛**。"""
    try:
        br = WorldBridge(ns, enabled=enabled, logger=logger)
        if not br.enabled:
            return {'enabled': False, 'replaced': []}
        replaced = br.attach()
        ns['__world_bridge__'] = br          # 供 HTTP 诊断接口读 stats
        return {'enabled': True, 'replaced': replaced, 'stats': br.stats()}
    except Exception as e:
        try:
            logf = ns.get('log')
            if callable(logf):
                logf('server.log', '!! world bridge attach 失败: %r' % (e,))
        except Exception:
            pass
        return {'enabled': False, 'error': repr(e)}
