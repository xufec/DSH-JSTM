"""寻路模块 —— 自研实现（含 JSTM 特有的**安全校验**）。

═══════════════════════════════════════════════════════════════════════════
★ 来源声明（任务书【原则 3】要求）
───────────────────────────────────────────────────────────────────────────
设计思想参考（**只有思想，没有代码**）：
  · Survive `common/astar.h`/`astar.c`：A* + **Bresenham 直线裁剪 `lineto`（遇障碍即停）**
    ⚠ **该文件头内嵌 GPLv3** ⇒ **一行代码都不可复制**，本文件为**完全自研**
  · kongkongxiyou `pathfinding.md`：列压缩碰撞 → 权重图；**直线快路径优先**；两级路径压缩

★★ JSTM 特有的**安全红线**（R1 审计发现，参考项目均未做）
───────────────────────────────────────────────────────────────────────────
kongkongxiyou 的 `handler.move` **直接信任客户端上传的整条路径**，
`Map.verifyPath` 已定义但**全项目 0 处调用** ⇒ 可穿墙/瞬移/加速/拉怪。
Survive 战斗层也**零距离/角度/目标数校验**。

**本模块把校验内建为 API 的一部分**：
  · **L1 路径校验**：`verify_path()` —— 每段必须可走、且与起点连续
  · **L2 限流**：`check_speed()` —— 两次移动的时间/距离上限
  · 服务端**自己算路径**：`find_path()`，客户端只能"请求去某点"

即：**客户端永远不能提供路径，只能提供目标点。**
"""

from __future__ import annotations

import heapq
import time

# ── 8 邻域（含对角）────────────────────────────────────────────────────
NEIGHBORS8 = [(-1, -1, 1.4142), (0, -1, 1.0), (1, -1, 1.4142),
              (-1, 0, 1.0), (1, 0, 1.0),
              (-1, 1, 1.4142), (0, 1, 1.0), (1, 1, 1.4142)]
# 4 邻域（参考项目 forAllReachable 只给上下左右）
NEIGHBORS4 = [(0, -1, 1.0), (0, 1, 1.0), (-1, 0, 1.0), (1, 0, 1.0)]


class MapGrid(object):
    """地图通行数据。

    通行来源优先级：
      1. `blocked` 显式给出的阻挡集合（JSTM 目前从 `config_map` / 场景数据构造）
      2. 未给出 ⇒ **全部可走**（`allow_all=True`，便于在缺数据时先跑通链路）
    ⚠ JSTM 目前**没有**客户端那份 TMX 碰撞图层，故默认 `allow_all`；
      一旦拿到阻挡数据，直接塞 `blocked` 即可，**其余代码不用改**。
    """

    def __init__(self, width=256, height=256, blocked=None, allow_all=True):
        self.w = width
        self.h = height
        self.blocked = set(blocked or ())
        self.allow_all = allow_all

    def walkable(self, x, y):
        x, y = int(x), int(y)
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return False
        if self.allow_all and not self.blocked:
            return True
        return (x, y) not in self.blocked

    def set_blocked(self, pts):
        self.blocked = set((int(a), int(b)) for a, b in pts)
        self.allow_all = False
        return len(self.blocked)


def _heuristic(x1, y1, x2, y2):
    """八方向用 octile 距离（比曼哈顿更贴合对角移动）。"""
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    return (dx + dy) + (1.4142 - 2) * min(dx, dy)


def bresenham_points(grid, x1, y1, x2, y2, include_goal=True):
    """Bresenham 逐格点列 —— **撞到不可走格即停**，返回"已经走过的点"。

    ⇐ 这正是 Survive `lineto` 的**关键语义**（"遇障碍即停并返回已走的点"）：
      调用方拿到的是**能实际走到的最远位置**，而不只是"能不能直达"。
      用途：击退/位移（`Repel_Range`）、追踪站位（`AssignAtkPoint`）、
            方向技能落点、以及下面的 `forward_to` / `walk_until_blocked`。

    ★ 修复 P1（2026-09-18）：旧实现只有 `line_of_sight` 返回 bool
      ⇒ **无法回答"能走到哪"**，导致击退/位移/追踪站位全都做不了。
    """
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    x, y = x1, y1
    pts = []
    guard = 0
    while True:
        if not grid.walkable(x, y):
            return pts                     # ⚠ 障碍格本身不入列（停在它前面）
        if x == x2 and y == y2:
            if include_goal or not pts:
                pts.append((x, y))
            return pts
        pts.append((x, y))
        e2 = err * 2
        nx, ny = x, y
        if e2 > -dy:
            err -= dy
            nx += sx
        if e2 < dx:
            err += dx
            ny += sy
        # ★ 修复 P4b：**LOS 也必须禁贴角穿缝**（与 A* 主循环、verify_path 同一规则）。
        #   旧实现只在 A* 主循环里查，`line_of_sight` 不查 ⇒
        #   ① 快路径会返回"穿角"的 2 点路径（服务端自己生成的路**通不过自己的校验**）；
        #   ② 击退/位移也会滑过对角缝隙。
        if nx != x and ny != y:
            if not (grid.walkable(nx, y) and grid.walkable(x, ny)):
                return pts
        x, y = nx, ny
        guard += 1
        if guard > 8192:                   # 防御：异常输入不死循环
            return pts


def line_of_sight(grid, x1, y1, x2, y2):
    """Bresenham 直线可达性（**bool 版**，语义与旧实现完全一致）。

    ⇒ 命中则 `find_path` **直接返回两点**，**零次 A***（参考项目正是靠这个省算力）。
    """
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    pts = bresenham_points(grid, x1, y1, x2, y2)
    return bool(pts) and pts[-1] == (x2, y2)


def walk_until_blocked(grid, x, y, dx, dy, max_tiles=64):
    """从 (x,y) 沿方向 (dx,dy) 走 **最多 max_tiles 格**，遇障碍即停。

    返回 `[(x,y), ..., 最远可达点]`；起点不可走时返回 `[]`。
    ⇐ 对应 Survive `Util.DirTo` 的用途（"按方向推进 N 像素，遇障碍停在障碍前"）。
    """
    dx = (dx > 0) - (dx < 0)               # 归一化为 -1/0/1（8 向之一）
    dy = (dy > 0) - (dy < 0)
    x, y = int(x), int(y)
    if dx == 0 and dy == 0:
        return [(x, y)] if grid.walkable(x, y) else []
    return bresenham_points(grid, x, y, x + dx * int(max_tiles), y + dy * int(max_tiles))


def forward_to(grid, frm, to, tiles):
    """从 `frm` 朝 `to` **前进 `tiles` 格**（遇障碍即停），返回最远可达点；不可走返回 None。

    ⇐ 对应 Survive `Util.ForwardTo`（**击退**、位移、追击站位都用它）。

    ★ 修复 P1b：按**主轴**缩放（`tiles / max(|dx|,|dy|)`），使 Bresenham 步数
      **恰好等于 `tiles`**。旧实现按欧氏距离缩放 ⇒ 45° 方向请求"前进 3 格"
      只会得到 (2,2)（因为 3/√2 ≈ 2.12），击退距离偏短。
    """
    fx, fy = int(frm[0]), int(frm[1])
    tx, ty = int(to[0]), int(to[1])
    dx, dy = tx - fx, ty - fy
    if dx == 0 and dy == 0:
        return None
    scale = float(tiles) / max(abs(dx), abs(dy))
    gx = fx + int(round(dx * scale))
    gy = fy + int(round(dy * scale))
    pts = bresenham_points(grid, fx, fy, gx, gy)
    if not pts:
        return None
    return pts[-1]


def find_path(grid, sx, sy, tx, ty, max_nodes=4096, compress=True, los_shortcut=True):
    """A*（8 邻域 + octile 启发）。

    **先试直线快路径**（`line_of_sight`）—— 多数同屏移动都是直线，可省掉整次 A*。
    返回 [(x,y), ...]（含起点与终点）；不可达返回 []。

    ★ 两个出口语义必须分清（修复 P2）：
      · **给客户端**：默认 `compress=True, los_shortcut=True`
        ⇒ 允许"2 点化 + 共线压缩"，省带宽；
      · **给服务端逐格走**：用 `path_for_walk()`
        ⇒ **必须逐格完整**。旧实现无条件压缩 + 无条件 2 点化，若服务端按该路径
          推进坐标就会**瞬移**（怪物追击/拾取/AOI 触发与客户端表现不符）。
    """
    sx, sy, tx, ty = int(sx), int(sy), int(tx), int(ty)
    if (sx, sy) == (tx, ty):
        return [(sx, sy)]
    if not grid.walkable(tx, ty):
        return []
    # ★ 直线快路径（零次 A*）
    if line_of_sight(grid, sx, sy, tx, ty):
        if compress and los_shortcut:
            return [(sx, sy), (tx, ty)]
        return bresenham_points(grid, sx, sy, tx, ty)   # 逐格完整（服务端自走用）

    openq = [(0.0, (sx, sy))]
    came = {}
    gscore = {(sx, sy): 0.0}
    closed = set()
    n = 0
    while openq:
        _, cur = heapq.heappop(openq)
        if cur in closed:
            continue
        closed.add(cur)
        n += 1
        if n > max_nodes:
            return []
        if cur == (tx, ty):
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            path.reverse()
            return _compress(path) if compress else path
        cx, cy = cur
        for dx, dy, cost in NEIGHBORS8:
            nx, ny = cx + dx, cy + dy
            if not grid.walkable(nx, ny):
                continue
            # 禁止"贴角穿缝"：对角移动要求两侧正交格都可走
            if dx and dy and not (grid.walkable(cx + dx, cy) and grid.walkable(cx, cy + dy)):
                continue
            ng = gscore[cur] + cost
            if ng < gscore.get((nx, ny), 1e18):
                gscore[(nx, ny)] = ng
                came[(nx, ny)] = cur
                heapq.heappush(openq, (ng + _heuristic(nx, ny, tx, ty), (nx, ny)))
    return []


def _compress(path):
    """一级压缩：去掉共线的中间点（参考项目的 compressPath2 思想）。

    ⚠ **只用于"发给客户端的路径"**；服务端自走请用 `path_for_walk()`（不压缩）。
    """
    if len(path) <= 2:
        return path
    out = [path[0]]
    for i in range(1, len(path) - 1):
        ax, ay = out[-1]
        bx, by = path[i]
        cx, cy = path[i + 1]
        if (bx - ax) * (cy - by) != (by - ay) * (cx - bx):
            out.append(path[i])
    out.append(path[-1])
    return out


def path_for_walk(grid, sx, sy, tx, ty, **kw):
    """★ 修复 P2：**服务端自走用**的路径 —— 逐格完整，不做 2 点化 / 共线压缩。

    用途：怪物/NPC 按路径逐格推进坐标（配合 100ms 定时器 + 时间预算）；
    若用压缩路径推进，坐标会"瞬移"，与客户端表现不一致。
    """
    kw.pop('compress', None)
    kw.pop('los_shortcut', None)
    return find_path(grid, sx, sy, tx, ty, compress=False, los_shortcut=False, **kw)


# ══════════════════════════════════════════════════════════════════════════
# ★★ L1：路径校验（参考项目**全部缺失**）
# ══════════════════════════════════════════════════════════════════════════
def verify_path(grid, path, start=None):
    """校验一条路径是否合法。

    规则（每条都能挡住一类作弊）：
      1. 路径非空、格式正确
      2. **与起点连续**（防"跳段瞬移"）
      3. **每一步必须相邻**（防"瞬移"—— 参考项目完全不查）
      4. **每一步必须可走**（防"穿墙"）
    返回 (ok: bool, reason: str)
    """
    if not path or not isinstance(path, (list, tuple)):
        return False, 'empty path'
    try:
        pts = [(int(p[0]), int(p[1])) for p in path]
    except Exception:
        return False, 'bad point format'
    if start is not None and pts[0] != (int(start[0]), int(start[1])):
        return False, 'start mismatch (client claims %r, server has %r)' % (pts[0], start)
    for i in range(1, len(pts)):
        ax, ay = pts[i - 1]
        bx, by = pts[i]
        if abs(bx - ax) > 1 or abs(by - ay) > 1 or (ax == bx and ay == by):
            return False, 'non-adjacent step %r->%r' % (pts[i - 1], pts[i])
        if not grid.walkable(bx, by):
            return False, 'blocked tile %r' % ((bx, by),)
        # ★ 修复 P4：**与 find_path 用同一套"禁贴角穿缝"规则**。
        #   旧实现只查 abs<=1，允许"斜穿两个阻挡格的夹角" ⇒ 校验比路径生成更宽松
        #   ⇒ 客户端可提交穿角路径通过校验（穿墙）。
        if ax != bx and ay != by:
            if not (grid.walkable(ax + (bx - ax), ay) and grid.walkable(ax, ay + (by - ay))):
                return False, 'corner cut %r->%r (side tiles blocked)' % ((ax, ay), (bx, by))
    return True, ''


# ══════════════════════════════════════════════════════════════════════════
# ★★ L2：限流（参考项目**全部缺失**）
# ══════════════════════════════════════════════════════════════════════════
class MoveRateLimiter(object):
    """服务端权威的移动限流。

    ⚠ kongkongxiyou 的 `handler.move` **直接信任客户端整条路径且无限流**
      ⇒ 可加速/瞬移。本类把它补上。
    """

    def __init__(self, max_tiles_per_sec=12.0, burst=6):
        self.max_rate = float(max_tiles_per_sec)
        self.burst = int(burst)
        self._st = {}          # uid -> (last_ts, tokens)

    def check(self, uid, distance, now=None):
        """返回 (ok, reason)。distance 为本次移动的瓦片距离。"""
        now = now if now is not None else time.time()
        last, tokens = self._st.get(uid, (now, float(self.burst)))
        dt = max(0.0, now - last)
        tokens = min(float(self.burst), tokens + dt * self.max_rate)
        if distance > tokens:
            self._st[uid] = (now, tokens)
            return False, 'move rate exceeded (want %.1f, tokens %.1f)' % (distance, tokens)
        self._st[uid] = (now, tokens - distance)
        return True, ''

    def reset(self, uid):
        self._st.pop(uid, None)
