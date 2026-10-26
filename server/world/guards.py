"""Handler 前置守卫（对应 kongkongxiyou `servers/area/filter/playerFilter.js`）。

═══════════════════════════════════════════════════════════════════════════
守卫做四件事（逐条保留参考实现的设计，并修掉它的问题）：
  ① 取玩家：内存 → 下线缓存 → 查库（**带每玩家锁**，参考实现用 'waiting' 字符串报错）
  ② 定位 Area：基于显式 `PlayerLocation`（参考实现是"先猜 scenes 再猜 instances"）
  ③ 校验"玩家确实在场"：不在则推 `onChangeArea` 让客户端自愈
     （参考实现靠 `route.search(/enterScene$/i)` 判断豁免 —— 又隐晦又慢，
       JSTM 改为**显式声明豁免**）
  ④ 注入 ctx.player / ctx.area（消除 13 个 handler 里的重复取玩家代码）

★ 本文件底部给出两个**示例 handler**：`enter_scene` 与 `move`。
  `move` 是 **Q2 决策**（客户端必须上传整条路径）的落地示范。
"""

from __future__ import annotations

from .consts import Code, FAILBACK_AREA_ID
from .move import DEFAULT_MAX_POINTS, MoveAction, validate_client_move


class Session(object):
    """最小会话对象（真实实现由 mock_server 的 TcpHandler 提供同名字段）。"""

    def __init__(self, uid=None, player_id=None, addr=None):
        self.uid = uid
        self.player_id = player_id
        self.addr = addr

    def __repr__(self):
        return '<Session uid=%r player_id=%r addr=%r>' % (self.uid, self.player_id, self.addr)


class HandlerCtx(object):
    """handler 上下文（守卫注入 player / area）。"""

    def __init__(self, world, session, msg=None, route=None):
        self.world = world
        self.session = session
        self.msg = msg or {}
        self.route = route
        self.player = None
        self.area = None

    @property
    def ms(self):
        return self.world._ms

    def reply(self, code=Code.OK, **kw):
        d = {'code': code}
        d.update(kw)
        return d


def area_handler(route, guard=True, allow_not_in_area=False):
    """Area handler 装饰器。

    用法：
        @area_handler('area.playerHandler.move')
        def move(ctx, msg): ...

        @area_handler('area.playerHandler.enterScene', guard=False)
        def enter_scene(ctx, msg): ...        # 唯一豁免守卫的路由
    """
    def deco(fn):
        def wrapper(ctx, msg=None):
            if msg is not None:
                ctx.msg = msg
            ctx.route = route
            if not guard:
                return fn(ctx, ctx.msg)

            world = ctx.world
            sess = ctx.session
            pid = getattr(sess, 'player_id', None)
            if not pid:
                return ctx.reply(Code.NOT_LOGGED_IN)

            # ① 取玩家（两级缓存 + 每玩家锁）
            player = world.get_or_load_player(pid)
            if player is None:
                return ctx.reply(Code.PLAYER_NOT_FOUND)

            # ② 定位 Area（显式状态，不猜）
            area = world.get_area_by_player(player)
            if area is None:
                # 兜底自愈：让客户端回主城重进（保留参考实现的能力）
                if ctx.ms is not None:
                    ctx.ms.send(player, 'onChangeArea', {'target': FAILBACK_AREA_ID})
                return ctx.reply(Code.AREA_NOT_FOUND)

            # ③ 校验"确实在场"
            if not allow_not_in_area and area.get_player(player.id) is None:
                if ctx.ms is not None:
                    ctx.ms.send(player, 'onChangeArea', {'target': area.area_id})
                return ctx.reply(Code.PLAYER_NOT_IN_AREA)

            # ④ 注入
            ctx.player, ctx.area = player, area
            return fn(ctx, ctx.msg)

        wrapper.__name__ = getattr(fn, '__name__', 'handler')
        wrapper.route = route
        return wrapper
    return deco


# ══════════════════════════════════════════════════════════════════════════
# 示例 handler ①：进场景
# ══════════════════════════════════════════════════════════════════════════
@area_handler('area.playerHandler.enterScene', guard=False)
def enter_scene(ctx, msg):
    """进场景。

    ★ 顺序关键（照搬参考实现 `playerHandler.enterScene`）：
        area.enter_area（清动作）
        → 坐标非法则回出生点
        → **先取 AOI 快照**
        → **再 add_entity**（此时才 aoi.add_watcher）
      顺序反了会把自己塞进自己的可见列表。
    """
    world, sess = ctx.world, ctx.session
    pid = getattr(sess, 'player_id', None)
    if not pid:
        return ctx.reply(Code.NOT_LOGGED_IN)
    player = world.get_or_load_player(pid)
    if player is None:
        return ctx.reply(Code.PLAYER_NOT_FOUND)

    target_id = msg.get('areaId') or player.location.area_id or FAILBACK_AREA_ID
    if player.location.kind == 0:
        code = world.change_area(player, target_id)
        if code != Code.OK:
            return ctx.reply(code)
    area = world.get_area_by_player(player)
    if area is None:
        return ctx.reply(Code.AREA_NOT_FOUND)

    # 已在场则先摘掉（参考实现同样处理）
    if area.get_player(pid) is not None:
        area.remove_player(pid)

    if getattr(sess, 'uid', None) != player.uid:
        return ctx.reply(Code.UID_MISMATCH)

    player.session_addr = getattr(sess, 'addr', None)
    player.kick_time = _now() + 30 * 60.0

    if area.map is not None and not area.map.walkable(player.x, player.y):
        player.x, player.y = world.get_born_point(area.area_id)

    # ① 先快照 ② 后注册
    entities = area.area_info_strip(player.x, player.y, player.range)
    area.actions.abort_all(player.entity_id)
    if not area.add_entity(player):
        return ctx.reply(Code.ADD_PLAYER_FAILED)

    return ctx.reply(Code.OK, areaId=area.area_id, entities=entities,
                     curPlayer=player.player_strip())


# ══════════════════════════════════════════════════════════════════════════
# 示例 handler ②：移动（★★ Q2 决策的落地：接受整条路径 + 严格校验 ★★）
# ══════════════════════════════════════════════════════════════════════════
@area_handler('area.playerHandler.move')
def move(ctx, msg):
    """移动。

    【Q2 事实】1.4.9 客户端**必须**上传整条路径 ⇒ 服务端主导路径不可行，
    只能「接受整条路径 + 严格校验」。

    校验与落地（`validate_client_move`）：
      · 航点数上限 / 起点一致 / 每点可走 / **每段直线可达** / 单段上限 / 总长上限 / 限流
    任一项不过 ⇒ **拒绝并强制同步回服务端权威位置**（推 onStand），
    而不是像参考实现那样"跟着客户端走"。
    """
    player, area = ctx.player, ctx.area
    if player is None or area is None:
        return ctx.reply(Code.PLAYER_NOT_FOUND)
    if player.died:
        return ctx.reply(Code.OK, ignored='died')

    # 兼容两种入参形态：{"path":[[x,y],...]}  或  直接就是 [[x,y],...]（参考实现是后者）
    if isinstance(msg, dict):
        raw = msg.get('path')
        if raw is None:
            raw = msg.get('points')
    elif isinstance(msg, (list, tuple)):
        raw = msg
    else:
        raw = None
    if not raw:
        return ctx.reply(Code.ILLEGAL_MOVE, reason='empty path')

    max_points = int(msg.get('_max_points', DEFAULT_MAX_POINTS)) if isinstance(msg, dict) \
        else DEFAULT_MAX_POINTS
    ok, reason, path = validate_client_move(
        area.map, raw, (player.x, player.y),
        uid=player.id, limiter=ctx.world.get_ratelimiter(),
        max_points=max_points,
    )
    if not ok:
        # ★ 拒绝 + 强制回位（推 onStand，客户端据此拉回）
        if ctx.ms is not None:
            ctx.ms.send(player, 'onStand',
                        {'entityId': player.entity_id, 'x': player.x, 'y': player.y})
        return ctx.reply(Code.ILLEGAL_MOVE, reason=reason)

    player.is_stop = False
    player.kick_time = _now() + 30 * 60.0
    action = MoveAction(player, path, speed=player.walk_speed)
    player.set_is_moving(True)
    if not area.actions.add(action):
        player.set_is_moving(False)
        return ctx.reply(Code.FAIL)

    start = path[0]
    # 起点若与服务器记录不符，先同步 AOI（此处 path[0] 已被强制为服务端位置）
    if ctx.ms is not None:
        ctx.ms.send_by_aoi(area, 'onMove',
                           {'entityId': player.entity_id, 'areaId': area.area_id,
                            'path': [[p[0], p[1]] for p in path]},
                           (start[0], start[1]))
    return ctx.reply(Code.OK, path=[[p[0], p[1]] for p in path])


def _now():
    import time
    return time.time()
