"""移动：动作队列 + **客户端路径校验**。

═══════════════════════════════════════════════════════════════════════════
★★★ 本文件解决审计中最严重的一个安全 + 兼容问题 ★★★
───────────────────────────────────────────────────────────────────────────
【事实】kongkongxiyou 的 `handler.move` 里 `var path = msg;` —— **服务端完全信任
客户端上传的整条路径**，而 `Map.verifyPath` 定义了却**全项目 0 处调用**
（已脚本核验）⇒ 可穿墙/瞬移/加速/拉怪。

【Q2 决策】1.4.9 客户端**必须**上传整条路径 ⇒ 服务端主导路径（只收目标点）
不可行。因此只能走「**接受整条路径 + 严格校验**」。

⚠⚠ 注意 `pathfind.verify_path()` 的适用边界（**不要误用**）：
   它要求「每一步必须相邻」（`abs(b-a) > 1 → 拒绝`），那是为**服务端生成的稠密
   路径**设计的。
   而客户端上传的是**压缩后的航点（waypoint）列表** —— 相邻航点往往隔很远，
   用 `verify_path` 会把**所有合法移动全部拒掉**。
   ⇒ 客户端路径必须用本文件的 `validate_client_move()`：**逐段直线可达性**
     （Bresenham，`pathfind.line_of_sight`），既支持相邻也支持远距离航点。

【补充】本文件**不修改** `pathfind.py`（保持其既有 API 与测试不变），
只是在其之上补一个「航点路径」校验器。
"""

from __future__ import annotations

import math

from . import _deps
from .consts import ActionType

# ── 默认阈值（可通过构造参数覆盖；都是"参考值，需实测调整"）────────────────
DEFAULT_MAX_POINTS = 64          # 单次移动请求最多多少个航点
DEFAULT_MAX_SEGMENT = 64.0       # 单段最长（瓦片）—— 防"一段跨越全图"
DEFAULT_MAX_TOTAL = 96.0         # 单次移动总长（瓦片）
DEFAULT_START_TOLERANCE = 0.0    # 起点与服务器记录的容差（瓦片）；0 = 必须完全一致


# ══════════════════════════════════════════════════════════════════════════
# ★ 客户端路径校验（Q2 的落地）
# ══════════════════════════════════════════════════════════════════════════
class MoveReject(Exception):
    """移动被拒。调用方应把玩家位置**强制同步回服务端权威值**（推 onStand）。"""

    def __init__(self, reason, code=None):
        Exception.__init__(self, reason)
        self.reason = reason
        self.code = code


def _as_points(path):
    pts = []
    for p in path:
        if isinstance(p, dict):
            pts.append((int(p.get('x', 0)), int(p.get('y', 0))))
        else:
            pts.append((int(p[0]), int(p[1])))
    return pts


def normalize_client_path(path, server_pos, start_tolerance=DEFAULT_START_TOLERANCE):
    """把客户端路径的**起点强制改写为服务端权威位置**，返回新的点列表。

    参考实现在起点不符时是"跟着客户端走"（把客户端起点当权威）；
    这里反过来：**服务端位置是唯一权威**，客户端起点只作为一致性校验输入。
    """
    pts = _as_points(path)
    if not pts:
        return []
    sx, sy = int(server_pos[0]), int(server_pos[1])
    if start_tolerance <= 0:
        pts[0] = (sx, sy)
    else:
        # 容差 > 0 时，把接近的起点吸附到服务端位置
        dx, dy = pts[0][0] - sx, pts[0][1] - sy
        if dx * dx + dy * dy <= start_tolerance * start_tolerance:
            pts[0] = (sx, sy)
    return pts


def validate_client_move(grid, path, server_pos, *,
                         uid=None, limiter=None, now=None,
                         max_points=DEFAULT_MAX_POINTS,
                         max_segment=DEFAULT_MAX_SEGMENT,
                         max_total=DEFAULT_MAX_TOTAL,
                         start_tolerance=DEFAULT_START_TOLERANCE,
                         off_by_one=True):
    """校验客户端上传的移动路径。

    返回 `(ok: bool, reason: str, clean_path: list[(x,y)])`。
    校验项（每条都对应一类作弊）：
      1. 路径非空、格式可解析
      2. 航点数 ≤ max_points                      —— 防"一次上传超长路径造成 A*/AOI 风暴"
      3. **起点与服务器记录一致**（容差 start_tolerance）—— 防"从别处开始走"
      4. 每个航点可走                              —— 防"落到墙里"
      5. **每段直线可达**（Bresenham）              —— 防"穿墙"（这是核心一项）
      6. 单段长度 ≤ max_segment                    —— 防"一段跨越全图"
      7. 总长度 ≤ max_total                        —— 防"超长路径"
      8. 限流（`pathfind.MoveRateLimiter`）        —— 防"加速/瞬移"，按总距离扣 token
    """
    if grid is None:
        return False, 'no mapgrid', []
    if not path or not isinstance(path, (list, tuple)):
        return False, 'empty path', []
    try:
        pts = _as_points(path)
    except Exception:
        return False, 'bad point format', []
    if len(pts) < 1:
        return False, 'empty path', []
    if len(pts) > max_points:
        return False, 'too many points (%d > %d)' % (len(pts), max_points), []

    sx, sy = int(server_pos[0]), int(server_pos[1])
    p0 = pts[0]
    dx, dy = p0[0] - sx, p0[1] - sy
    if start_tolerance <= 0:
        if p0 != (sx, sy):
            return False, 'start mismatch (client %r, server %r)' % (p0, (sx, sy)), []
    elif dx * dx + dy * dy > start_tolerance * start_tolerance:
        return False, 'start too far (client %r, server %r)' % (p0, (sx, sy)), []

    # 起点强制为服务端权威值
    pts[0] = (sx, sy)

    # 单点路径：视为"原地"（允许，但强制为服务端位置）
    if len(pts) == 1:
        return True, '', pts

    # ★ 逐段直线可达性 —— 同时覆盖"相邻格"与"远距离航点"两种形态
    los = _deps.pathfind_mod.line_of_sight
    total = 0.0
    for i in range(1, len(pts)):
        ax, ay = pts[i - 1]
        bx, by = pts[i]
        if (ax, ay) == (bx, by):
            return False, 'duplicate/repeated point at %d' % i, []
        if not grid.walkable(bx, by):
            return False, 'blocked waypoint %r' % ((bx, by),), []
        if not los(grid, ax, ay, bx, by):
            return False, 'blocked segment %r->%r' % ((ax, ay), (bx, by)), []
        seg = math.hypot(bx - ax, by - ay)
        if seg > max_segment:
            return False, ('segment too long (%.1f > %.1f) %r->%r'
                           % (seg, max_segment, (ax, ay), (bx, by))), []
        total += seg
        if total > max_total:
            return False, 'path too long (%.1f > %.1f)' % (total, max_total), []

    # 限流：按整条路径长度扣 token
    if limiter is not None and uid is not None:
        ok, why = limiter.check(uid, total, now)
        if not ok:
            return False, why, []

    return True, '', pts


def plan_path(grid, src, dst, max_nodes=4096):
    """服务端自己算路径（给 AI / 巡逻 / "点击目标点" 用）。
    直接复用 `pathfind.find_path`（8 邻域 A* + 直线快路径）。"""
    if grid is None or _deps.pathfind_mod is None:
        return []
    return _deps.pathfind_mod.find_path(grid, src[0], src[1], dst[0], dst[1],
                                       max_nodes=max_nodes)


# ══════════════════════════════════════════════════════════════════════════
# ★ 单点逐步上报模型（**JSTM 1.4.9 的 10204 就是这个形态**）
# ══════════════════════════════════════════════════════════════════════════
def validate_step_move(grid, last_pos, x, y, *,
                       uid=None, limiter=None,
                       enforce_rate_limit=False,
                       max_step=None, now=None):
    """校验 **CS_10204{x,y}** 这类"客户端逐步上报单个坐标"的移动。

    ★ 与 `validate_client_move` 的分工（**不要混用**）：
        · `validate_step_move`   ← **10204**：客户端每次上报**一个点**
        · `validate_client_move` ← 尚未定位的"点击寻路"CMD：客户端上传**整条航点路径**
      依据：`analysis/jstm_1.4.9/movement_protocol.md` ——
        10204 = CS_10204{x:u16,y:u16} → SC_10204{rid,srv_id,x,y}（真机已验证通），
        而"点击自动寻路"的 CMD **仍待定位**。

    规则（**默认与 mock_server 现有实现保持等价**）：
      ① 目标格可走（`MapGrid` 无 blocked 时自动退化为越界检查）
      ② 限流（`enforce_rate_limit` **默认 False**）
      ③ 单步跨度上限（`max_step` **默认 None = 关闭**）

    ⚠️ **为什么默认全关**：`mock_server.py` 已有明确结论（见 aoi_pathfind_review.md P5）：
      "12 格/秒是拍的，**未按真机 10204 标定前打开会误杀正常玩家**"。
      ⇒ 任何"会拒人"的规则都必须**显式开启**，且开启前用真机日志标定。

    返回 `(ok, reason, corrected)`：
      · ok=True  → corrected = (x, y)
      · ok=False → **corrected = last_pos（服务端权威坐标）**，调用方应把它回给客户端
        让其自我纠正 —— 参考实现用"静默丢弃"，会导致两端坐标永久错位。
    """
    last = (int(last_pos[0]), int(last_pos[1])) if last_pos else (int(x), int(y))
    tx, ty = int(x), int(y)

    # ① 可走性
    if grid is not None and not grid.walkable(tx, ty):
        return False, 'blocked tile %r' % ((tx, ty),), last

    dist = math.hypot(tx - last[0], ty - last[1])

    # ③ 单步跨度（默认关）
    if max_step is not None and dist > float(max_step):
        return False, ('step too far (%.1f > %.1f)' % (dist, max_step)), last

    # ② 限流（默认关）
    if enforce_rate_limit and limiter is not None and uid is not None:
        ok, why = limiter.check(uid, dist, now)
        if not ok:
            return False, why, last

    return True, '', (tx, ty)


# ══════════════════════════════════════════════════════════════════════════
# 动作队列（照搬参考实现 actionManager 的结构 + singleton 语义）
# ══════════════════════════════════════════════════════════════════════════
class Action(object):
    type = ActionType.DEFAULT

    def __init__(self, id_, singleton=False):
        self.id = id_
        self.singleton = bool(singleton)
        self.finished = False
        self.aborted = False

    def update(self, dt):
        raise NotImplementedError


class MoveAction(Action):
    """沿折线按 speed × dt 滑行；支持单 tick 跨多个航点。

    - 无状态插值（不依赖固定 tick 间隔），抗抖动 —— 照搬参考实现 `action/move.js` 的思想
    - `singleton=True`：一个实体同一时刻只有一个移动动作
    - `update()` 返回 `(old_xy, new_xy)` 或 None，由 Area 决定怎么更新 AOI
      （参考实现是在 move.js 里直接调 aoi；这里解耦，便于单测）
    """

    type = ActionType.MOVE

    def __init__(self, entity, path, speed=None):
        Action.__init__(self, entity.entity_id, singleton=True)
        self.entity = entity
        self.path = [(int(p[0]), int(p[1])) for p in path]
        self.speed = float(speed if speed is not None else getattr(entity, 'walk_speed', 12.0))
        self.index = 1 if len(self.path) > 1 else 0
        self.pos = self.path[0] if self.path else (entity.x, entity.y)
        self.ticks = 0

    def update(self, dt):
        if self.finished or self.aborted or not self.path:
            return None
        old = (self.entity.x, self.entity.y)
        travel = self.speed * float(dt)
        pos = self.pos
        while travel > 0.0:
            if self.index >= len(self.path):
                self.finished = True
                self.entity.set_is_moving(False)
                break
            dest = self.path[self.index]
            seg = math.hypot(dest[0] - pos[0], dest[1] - pos[1])
            if seg <= 0:
                self.index += 1
                continue
            if seg <= travel:
                travel -= seg
                pos = dest
                self.index += 1
                if self.index >= len(self.path):
                    self.finished = True
                    self.entity.set_is_moving(False)
                    break
            else:
                k = travel / seg
                pos = (pos[0] + (dest[0] - pos[0]) * k,
                       pos[1] + (dest[1] - pos[1]) * k)
                travel = 0.0
        self.pos = pos
        self.ticks += 1
        self.entity.x = int(round(pos[0]))
        self.entity.y = int(round(pos[1]))
        if old == (self.entity.x, self.entity.y) and not self.finished:
            return None
        return (old, (self.entity.x, self.entity.y))

    def stop_move(self):
        self.finished = True
        self.entity.set_is_moving(False)


class ActionManager(object):
    """动作队列：按 (type, id) 索引 + 插入顺序遍历（照搬参考实现）。"""

    def __init__(self):
        self._by_key = {}      # (type, id) -> action
        self._queue = []       # 保持顺序
        self._stats = {'added': 0, 'aborted': 0, 'finished': 0, 'updates': 0}

    def __len__(self):
        """**活跃**动作数（不含已 abort 的）。

        ⚠ 不能直接返回 `len(self._queue)`：abort 只是标记 + 从索引里删，
        队列里的条目要等下一次 update 才被跳过 —— 那样 `len()` 会虚高。
        """
        return len(self._by_key)

    def get(self, type_, id_):
        return self._by_key.get((type_, id_))

    def add(self, action):
        if action.singleton:
            self.abort(action.type, action.id)
        self._by_key[(action.type, action.id)] = action
        self._queue.append(action)
        self._stats['added'] += 1
        return True

    def abort(self, type_, id_):
        a = self._by_key.get((type_, id_))
        if a is None:
            return False
        if isinstance(a, MoveAction):
            a.stop_move()
        a.aborted = True
        self._by_key.pop((type_, id_), None)
        self._stats['aborted'] += 1
        return True

    def abort_all(self, id_):
        n = 0
        for (t, i) in list(self._by_key.keys()):
            if i == id_:
                self._by_key[(t, i)].aborted = True
                self._by_key.pop((t, i), None)
                n += 1
        self._stats['aborted'] += n
        return n

    def update(self, dt):
        """返回 [(action, retval)]，retval 是 action.update() 的返回值。"""
        results = []
        self._stats['updates'] += 1
        n = len(self._queue)
        for _ in range(n):
            if not self._queue:
                break
            a = self._queue.pop(0)
            if a is None or a.aborted:
                continue
            if a.finished:
                self._by_key.pop((a.type, a.id), None)
                continue
            ret = a.update(dt)
            results.append((a, ret))
            if a.finished:
                self._by_key.pop((a.type, a.id), None)
                self._stats['finished'] += 1
            else:
                self._queue.append(a)
        return results

    def stats(self):
        return dict(self._stats)
