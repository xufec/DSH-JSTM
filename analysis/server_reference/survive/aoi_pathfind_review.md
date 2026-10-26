# 对照审查：`server/aoi.py` + `server/pathfind.py`

> **审查对象（钉住快照，2026-09-18 21:57）**
> | 文件 | 大小 | 修改时间 | MD5 |
> |---|---|---|---|
> | `server/aoi.py` | 12,557 B | 2026-09-18 19:56:43 | `D5F0D2E569588FA017BCDE88993905D6` |
> | `server/pathfind.py` | 9,944 B | 2026-09-18 19:56:59 | `BD1C0E12ED08B750C5ADE9AD1CBA7067` |
> | `server/mock_server.py`（被检查的接入方） | 313,909 B | 2026-09-18 21:42:31 | `A1A7622A0F4FB7145CEB2B300AC4567C` |
> | `server/power.py` | 3,732 B | 2026-09-18 21:12:10 | `056C40059B12DC349533500228E53E63` |
>
> **审查依据**：`analysis/server_reference/survive/`（Survive 参考设计，D11/D12/D13/D14 + 25 处已知缺陷）
> **约束遵守**：**只读**，未修改 `server/` 或 `cankao/` 下任何文件。
> ⚠ **时效声明**：`server/` 正在被并行修改（`aoi.py`/`pathfind.py` 于 19:56 新建，`mock_server.py` 21:42 刚改）。本审查**只对上述 MD5 负责**；若文件已变，结论需重跑。

---

## 一、结论速览

| 项 | 结论 | 状态 |
|---|---|---|
| **两个模块是否实现了 Survive 的核心设计** | ✅ **是**。AOI 吃到了 D11 的四个要点（网格 / 视野集合去重 / 新旧集合差 / 只回调不碰网络），寻路吃到了 D12 的 A\* + LOS 快路径 + octile 启发 | 【已确认】 |
| **是否比参考实现更好** | ✅ **是，三处明显更好**：① 精确圆判定取代 Survive 的"同塔近似"；② 事件以 `[(uid,event)]` 返回，**AOI 绝不碰 socket**；③ 提供 `stats()` 埋点（Survive 零埋点） | 【已确认】 |
| **是否已接入业务** | ❌ **完全没有**。`mock_server.py` 里 `AOI(` / `MapGrid(` / `MoveRateLimiter(` **只有实例化**（延迟构造 + `/status` 自检），而 `add_watcher`/`update_watcher`/`update_object`/`watchers_of`/`find_path`/`verify_path`/`check` **调用点全部为 0** | 【已确认】 |
| **后果（当前线上行为）** | 10204 只做 `save_role_pos` + **回包给本人** ⇒ **同场景其它角色收不到我的移动**（"别人看不到我动"）；10205 瞬移**无校验**；服务端**不会为怪物/NPC 寻路** | 【已确认】 |
| **必须修的缺陷** | AOI **4 处**、寻路 **4 处**、接线 **4 步**（见 §4/§5/§6） | 【已确认】 |
| **两处"会误伤"的风险** | ① `MapGrid(allow_all=True)` 使穿墙校验**实际失效**；② `MoveRateLimiter(12 格/秒)` 可能**低于客户端真实速度** ⇒ 误杀正常玩家 | 【待验证】 |

### 1.1 调用点实测（`mock_server.py`，`A1A7...`）

| 模式 | 命中数 | 说明 |
|---|---|---|
| `AOI(` | 1 | `get_aoi()` 延迟构造（`aoi_mod.AOI(tower_size=CFG['aoi_tower_size']==8)`） |
| `MapGrid(` | 1 | `get_mapgrid()` 延迟构造（`MapGrid(256,256,allow_all=True)`） |
| `MoveRateLimiter(` | 1 | 延迟构造（`max_tiles_per_sec=CFG['move_max_tiles_per_sec']==12.0`, `burst=CFG['move_burst']==6`） |
| `.add_watcher(` / `.add_object(` | **0** | — |
| `.update_watcher(` / `.update_object(` | **0** | — |
| `.watchers_of(` / `.entities_near(` | **0** | — |
| `.find_path(` / `.verify_path(` / `.line_of_sight(` | **0** | — |
| `.check(`（限流） | **0** | — |
| `.stats(` | 1 | 仅 `/status` JSON |
| `.set_blocked(` / `.reset(` | **0** | — |

⇒ **这三个模块目前是"孤岛"**：能力齐备、零业务接入。可类比为"零件已造好，未装到车上"。

---

## 二、`server/aoi.py` —— 逐方法对照审查

> 对照基准：`common/aoi.c`（Survive）的 `aoi_create/enter/moveto/leave` + `cal_blockset` + `block_process_*` + `cb_enter/cb_leave`
> **⚠️ 该 C 文件内嵌 GPLv3 ⇒ 只可读设计，不可复制代码（本审查同样只比对设计）**

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `server/aoi.py` | `Entity.__slots__` (`uid,x,y,range,types,is_watcher,is_object,_old_watchers,seen`) | 双角色实体：既是 watcher（有视野）又是 object（被看见）；**两张集合**：`seen`=我看得见谁、`_old_watchers`=谁看得见我 | ✅ **高度适合** | ✅ 正是 Survive `view_objs` 位图 + `aoi_moveto` 双向遍历的 Python 等价物；用 `set` 取代位图（JSTM 规模不需要位图）；`__slots__` 省内存。**比 Survive 更好**：Survive 只有 `view_objs` 一张位图，"谁看得见我"是遍历出来的 |
| `server/aoi.py` | `AOI.__init__(tower_size)` | `_towers = {(tx,ty): set(uid)}`、`_ents = {uid: Entity}`、`_stats` | ✅ 适合 | ✅ 对应 Survive `aoi_map.blocks[]`（链表）→ Python `dict[tower]=set`。**且 `tower_size` 可配**，修正了 Survive"`radius` 兼作格边长、参数语义混乱"的隐患（我上一轮 §6-24 标记的隐患） |
| `server/aoi.py` | `_tower_of(x,y)` / `_towers_in_range(x,y,r)` | `floor(x/t)`；由 `(x±r,y±r)` 取塔矩形并逐个 `yield` | ✅ 适合 | ✅ 等价 Survive `get_block_by_point` + `cal_blocks`；**用生成器**避免 Surive 的"预分配 5 个指针数组"复杂度 |
| `server/aoi.py` | `add_watcher(uid,x,y,range_)` / `add_object(uid,x,y,types)` | 首次创建实体并把 uid 挂到所在塔；已存在则升级角色 + `_move_in_tower` | ✅ 适合 | ✅ 对应 `aoi_enter`；**"同一 uid 可先 object 后 watcher"的设计比 Survive 更灵活**（Survive 用 `is_watcher/is_object` 两个布尔在 Lua 层表达） |
| `server/aoi.py` | `remove(uid)` | 对 `e._old_watchers` 逐个产出 `(w,'leave',uid)`；从塔中 `discard`；`del _ents[uid]` | ⚠️ **部分适合（有缺陷 A1）** | ⚠️ **只做了单边清理**：没有从**其它实体的 `seen`/`_old_watchers`** 中摘除该 uid ⇒ 见缺陷 A1（重复 leave / 幽灵事件）。Survive 的 `aoi_leave` 会 `kn_dlist_remove` + `block_process_leave` 走完双向 |
| `server/aoi.py` | `_move_in_tower(e,x,y)` | 塔号变了才搬动 `_towers`，并更新 `e.x/e.y` | ✅ 适合 | ✅ 对应 Survive `aoi_moveto` 里"跨格才 `kn_dlist_remove/push`"的优化；**且没有 Survive 那个"预分配数组可能不够"的越界隐患** |
| `server/aoi.py` | `_in_range(a,b,r)` | 平方距离 ≤ r² ⇒ **精确圆** | ✅ **优于参考** | ✅ Survive 的 `in_myscope` **恒返回 1**（可见性完全由"同塔"近似，见 `lua_aoi.c` 注释掉的原 Lua 回调）⇒ JSTM 实现更准。**这是正确的偏离** |
| `server/aoi.py` | `_visible_objects(e)` | 遍历 `e` 视野塔 → 过滤 `is_object` → 精确距离 → 返回 uid 集合；**跳过自己** | ✅ 适合 | 见 A5：**不产出 self 事件**是**正确取舍**（JSTM 的 `SC_10201` 已携带自己），但必须写进文档，否则后人会以为漏了 |
| `server/aoi.py` | `_visible_watchers(obj)` | 用 **`_max_range()`（全图最大 range）** 扩圈找 watcher → 精确距离 | ❌ **不适合（缺陷 A2）** | 🔴 **`_max_range()` 每次调用都 O(全部实体) 遍历**，且扩圈半径取全图最大值 ⇒ 单次 `update_object` 退化为接近 O(N) 甚至 O(N²)。**怪物每次移动都调** ⇒ 会成为热点。修复见 A2 |
| `server/aoi.py` | `update_watcher(uid,x,y=None)` | 只服务"我的视野"：`new=_visible_objects` vs `old=e.seen` → `_diff` | ⚠️ **部分适合（缺陷 A3/A4）** | ⚠️ `y` 可选 ⇒ `update_watcher(uid, x)` **静默不移动**（x 被忽略，因为 `_move_in_tower` 被跳过）；且**与 `update_object` 必须成对调用**，漏一个就"单向失明"。**Survive 的 `aoi_moveto` 一次完成双向** ⇒ 建议提供合并 API（A4，最高优先级） |
| `server/aoi.py` | `update_object(uid,x,y=None)` | 服务"别人的视野"：`new=_visible_watchers` vs `old=_old_watchers` → 产出 `(watcher,'enter'/'leave',uid)` | ⚠️ 同上 | 同上；语义正确（"通知谁该看我"），性能见 A2 |
| `server/aoi.py` | `_diff(e,old,new)` | 差集产出 enter/leave + 写回 `e.seen` | ✅ 适合 | ✅ 对应 Survive `cal_blockset` 的 enter/unchange/leave 三分；**JSTM 省掉了 `unchange`**（不产出事件，天然等价） |
| `server/aoi.py` | `watchers_of(px,py,r,types)` | 按坐标+半径取 watcher **uid 列表**，支持 `types` 位掩码 | ✅ **高度适合** | ✅✅ **"AOI 绝不返回 socket/连接"** 是本文件最好的设计：与 `avatar:Send2view`（Survive 直接把 `gatesession.sock` 塞进包里）相比，JSTM 的分层更干净，也更好测 |
| `server/aoi.py` | `entities_near(px,py,r)` | 取半径内全部实体对象 | ✅ 适合 | 用于"技能范围取目标"（对应 Survive `UseSkill` 的 AOE 目标收集） |
| `server/aoi.py` | `stats()` | 返回 add/remove/update/enter/leave 计数 + entities/towers | ✅ **优于参考** | ✅ Survive 零埋点；接入后可直接观测 enter/leave 频率 |

### 2.1 `aoi.py` 缺陷清单（按优先级）

| # | 缺陷 | 位置 | 后果 | 建议修复 |
|---|---|---|---|---|
| **A1** | **`remove()` 单向清理** | `remove()` L117-133 | ① 被删实体的 uid 仍留在**其它 watcher 的 `seen`** ⇒ 该 watcher 下次 `update_watcher` 产出**重复 `leave`**；② 被删实体曾"看见"的 object，其 `_old_watchers` 仍含 uid ⇒ 下次 `update_object` 产出**发给已删实体的幽灵 `enter/leave`** | `remove()` 里做**对称清理**：`for w_uid in e._old_watchers: w=self._ents.get(w_uid); w and w.seen.discard(uid)`；`for o_uid in e.seen: o=self._ents.get(o_uid); o and o._old_watchers.discard(uid)`；并 `e.seen.clear()` |
| **A2** | **`_visible_watchers` 的 O(N) 扩圈** | `_max_range()` L187-192 + L176 | 每次 `update_object` 遍历**全部实体**求最大 range，再按该半径扩塔 ⇒ 实体越多越慢（怪物移动是高频路径） | ① **增量维护 `_max_range`**（`add_watcher` 时取 max；`remove` 时才失效重算或惰性标记）；② 更好：按塔缓存 `tower_max_range`；③ JSTM 若所有 watcher 视距固定（客户端视距常量），**直接用常数扩圈**即可，`_max_range` 可退役 |
| **A3** | **`update_*(uid,x,y=None)` 可选 y 是 API 陷阱** | L195/L221 | `update_watcher(uid, x)` 静默变成"只重算视野、不移位" | 把签名改为 `move(uid, x, y)`（必填）；保留 `refresh(uid)` 供"只重算视野"用 |
| **A4** | **两向更新需调用方调两次**（漏调即单向失明） | L195 / L221 | 10204 接入点极易只调一个 ⇒ "别人看不到我动"（正是当前线上症状） | **提供 `move(uid,x,y) -> (self_events, watch_events)`**，内部一次完成 `update_watcher` + `update_object`；**把"必须成对"的知识收进模块**。参考 Survive：`aoi_moveto` 天然双向 |
| **A5** | **不产出 self 事件**（差异而非缺陷） | `_visible_objects` L161 | 无人收到"我进我自己视野" | ✅ **保持现状**（由 `SC_10201` 承担），但**在文件头写明**，避免被误当 bug；⚠️ 需与客户端确认：JSTM 客户端是否需要单独的"self enter see"（Survive 客户端需要）【待验证】 |
| **A6** | `types` 只在 `watchers_of` 生效，可见性不过滤类型 | `_visible_*` | 目前"万物可见"；将来若"怪物只被玩家看到/潜行"需扩展 | 待需要时给 `_visible_watchers` 加 `types` 过滤（Survive 的 `hide`/`invisible` 也是在 Lua 层过滤，非 AOI 内核 ⇒ 可接受） |
| **A7** | `remove()` 未处理"实体已跨塔但 `_towers` 里旧塔残留" | L126-130 | 因 `_move_in_tower` 始终同步，**当前不会发生** | 无需改；建议加断言/单测兜住 |

---

## 三、`server/pathfind.py` —— 逐函数对照审查

> 对照基准：`common/astar.c`（`find_path`/`isblock`）+ `common/lua_astar.c`（`lua_lineto`）+ `gameserver/util.lua`（`ForwardTo`/`DirTo`）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `server/pathfind.py` | `NEIGHBORS8` / `NEIGHBORS4` | 8 邻域 `(dx,dy,cost)`，对角 1.4142；4 邻域备用 | ✅ 适合 | ✅ 对应 Survive `direction[8][2]` + `cost_2_neighbor`（正交 50 / 对角 60 ≈ 同比例）。**用 1.0/1.4142 而不是 50/60 更规范** |
| `server/pathfind.py` | `MapGrid.walkable(x,y)` | 越界 False；`allow_all and not blocked` ⇒ True；否则查 `blocked` 集合 | ⚠️ **部分适合（缺陷 P3，🔴）** | 🔴 **默认 `allow_all=True` ⇒ 穿墙校验实际失效**（`verify_path` 只剩"相邻性"检查）。JSTM 尚无客户端 TMX 碰撞图层 ⇒ 必须尽快用 `_config_map_block.luac`（或场景数据）注入 `set_blocked()`，否则"防穿墙"是纸面功能 |
| `server/pathfind.py` | `MapGrid.set_blocked(pts)` | 整体替换阻挡集合并关 `allow_all` | ✅ 适合 | ✅ 提供了一键接入点；建议再加 `add_blocked()` 增量与"是否已加载"的日志 |
| `server/pathfind.py` | `_heuristic` | **octile**：`(dx+dy) + (1.4142-2)*min(dx,dy)` | ✅ **优于参考** | ✅✅ Survive 用**曼哈顿 ×50** 做 8 邻域启发（我上一轮判定为 inadmissible）⇒ JSTM 用 octile 与 `NEIGHBORS8` 的 cost **一致（consistent）**，A\* 首次出队即最优 ⇒ 可直接用 `closed` 集剪枝。**这是对参考缺陷的正确修正** |
| `server/pathfind.py` | `line_of_sight(grid,x1,y1,x2,y2)` | Bresenham 逐格检查 `walkable`；返回 **bool**；`guard>4096` 防死循环 | ⚠️ **部分适合（缺陷 P1，🟠）** | 🟠 函数本身正确（含防御性 guard），但**丢失了 Survive `lineto` 最关键的语义**：`lineto` 返回**已走过的点列**（"遇障碍即停"）⇒ 这正是 `Util.ForwardTo`/`DirTo`/**击退**/位移/追踪站位的实现基础。JSTM 现在只能判"能不能直达"，**无法算"能走到哪"** ⇒ 见 P1 |
| `server/pathfind.py` | `find_path(grid,sx,sy,tx,ty,max_nodes)` | 终点不可走直接 `[]`；**先试 LOS 快路径**（命中则返回 2 点）→ 否则 A\*（8 邻域 + **禁贴角穿缝** + 延迟删 `closed` + `max_nodes` 上限）→ `_compress` | ⚠️ **部分适合（缺陷 P2/P8，🟠）** | ✅ 算法与工程细节都正确（禁贴角是 Survive **没有**的优点）；🟠 **但返回的路径被"2 点化/共线压缩"** ⇒ 见 P2（若服务端要按路径逐格推进坐标会瞬移）；🟠 `max_nodes` 打满与"不可达"都用 `[]` 表示，见 P8 |
| `server/pathfind.py` | `_compress(path)` | 去掉共线中间点（用 `out[-1]` 作锚点比较方向） | ⚠️ 部分适合 | 实现正确（等价 kongkongxiyou `compressPath2`）；**但只应作用于"发给客户端的路径"**，不能作用于"服务端自走的路径"（P2） |
| `server/pathfind.py` | `verify_path(grid,path,start)` | 非空/格式 → 起点一致 → **相邻性**（`abs<=1` 且非原地）→ 每步 `walkable` | ⚠️ **部分适合（缺陷 P4，🟠；价值高）** | ✅✅ **L1 校验本身是 Survive 与 kongkongxiyou 都缺的**（我上一轮 B10 指的正是这个缺口），方向完全正确；🟠 但**允许对角步而未禁贴角**，比 `find_path` **更宽松** ⇒ 客户端可提交"穿角"路径通过校验。见 P4 |
| `server/pathfind.py` | `MoveRateLimiter` / `check(uid,distance,now)` | 令牌桶：`tokens = min(burst, tokens + dt*rate)`；`distance > tokens` ⇒ 拒绝 | ✅ **高度适合（设计）** / ⚠️ **参数待标定（P5，🔴）** | ✅✅ **L2 限流是 JSTM 相对所有参考项目的净增价值**（Survive/kongkongxiyou 均无）；🔴 但默认 `12 格/秒 + burst 6` **很可能是拍的**：Survive 的 `speed=27` ⇒ `27*8*1.2 = 259.2 px/s` ≈ **32 格/秒**（8px 格）。若 JSTM 客户端速度接近参考，**12 格/秒 会误杀正常玩家**。必须用真机 10204 采样标定（已可从 `config.json` 调 ⇒ 好设计） |
| `server/pathfind.py` | `MoveRateLimiter.reset(uid)` | 清 uid 状态 | ✅ 适合 | 断线/换场景时应调用（当前调用点 0） |

### 3.1 `pathfind.py` 缺陷清单（按优先级）

| # | 缺陷 | 位置 | 后果 | 建议修复 |
|---|---|---|---|---|
| **P1** | **LOS 只返回 bool，缺"遇障碍即停并返回已走的点"** | `line_of_sight` L76-103 | 🔴 **无法实现击退/位移/追踪站位/技能落点**（Survive `ForwardTo`/`DirTo`/`AssignAtkPoint`/`Repel_Range` 全靠 `lineto` 的返回值）；战斗与 AI 会卡住 | 新增 `walk_until_blocked(grid,x,y,dir,max_tiles) -> [(x,y),...]` 与 `forward_to(grid,frm,to,range) -> (x,y)|None`：**保留 LOS 的 bool 版本**，另加返回点列的版本（内部同一套 Bresenham，仅在撞障碍时 `return pts`） |
| **P2** | **`find_path` 的 LOS 快路径返回 2 点 + `_compress` 去中点** | `find_path` L118-119, L140 | 🟠 若服务端**按路径逐格推进坐标**（Survive D13 的"服务端自走"），2 点路径会让**服务端坐标瞬移**，导致怪物追击/拾取/AOI 触发与客户端表现不符 | 明确区分两个出口：`path_for_wire(...)`（允许 2 点/压缩，给客户端）与 `path_for_walk(...)`（`compress=False`，逐格完整，给服务端推进器）。**当前这两个语义混在一个函数里** |
| **P3** | **`MapGrid(allow_all=True)` 默认放行** | `mapgrid` L59 + `mock_server.py:get_mapgrid` | 🔴 **`verify_path` 的"防穿墙"与 `find_path` 的避障全部形同虚设**（只剩相邻性检查） | ① 从 `_config_map_block.luac`/场景数据构造 `blocked` 并 `set_blocked()`；② 在缺数据时**至少把 `allow_all` 反映到 `/status` 并在日志里显著告警**；③ `verify_path` 返回的 reason 里区分 "no-collision-data" |
| **P4** | **`verify_path` 允许对角而 `find_path` 禁贴角（校验比生成宽松）** | `verify_path` L196 vs `find_path` L147 | 🟠 客户端可提交"斜穿两个阻挡格夹角"的路径而通过校验 ⇒ 穿墙 | 在 `verify_path` 加同一规则：对角步要求 `walkable(ax+dx,ay) and walkable(ax,ay+dy)` |
| **P5** | **限流参数未标定** | `MoveRateLimiter.__init__` | 🔴 过严 ⇒ 误杀正常玩家（体感"走两步被拉回"）；过松 ⇒ 加速挂可用 | 用真机 10204 抓 N 次移动的 `(dt, 距离)` 分布，取 P99 作为 `max_tiles_per_sec`，`burst` 取 2~3 倍单次抖动；**并把"被限流的次数"计数上报 `/status`** |
| **P6** | `verify_path` 未限制路径总长/总时长 | L175-200 | 🟡 单次可提交超长路径（但需每步相邻 ⇒ 影响有限；限流按 distance 覆盖） | 可加 `max_len` 参数；或直接由 `MoveRateLimiter.check(distance=len(path))` 覆盖 |
| **P7** | 无"服务端自走器"（定时按路径推进 + 时间预算） | 缺 | 🟠 怪物/NPC 无法移动；`movement_protocol.md` 提到 `10212/10213` 是"怪物实时移动"⇒ 迟早需要 | 参考 Survive `map.movtimer`(100ms) + `avatar:process_mov` 的 **`movmargin` 时间预算**（一帧跨多格、不落后客户端）；**必须配合 P2 的逐格路径** |
| **P8** | `max_nodes` 打满返回 `[]`，与"不可达"不可区分 | L132-133 | 🟡 无法监控"路径搜索失败率"与"地图过大" | 返回 `(path, reason)` 或抛出特定异常，便于埋点 |

### 3.2 明确保留的正确决策（不要动）

| 决策 | 位置 | 为什么对 |
|---|---|---|
| 用 **octile** 而非曼哈顿 | `_heuristic` | 与 8 邻域 cost 一致 ⇒ 可安全剪枝（修正了 Survive 的缺陷） |
| **禁止贴角穿缝** | `find_path` L147 | 避免"斜穿墙角"造成的视觉穿模；Survive 没有这个约束 |
| **LOS 快路径优先** | `find_path` L118 | 同屏移动多为直线，**省掉整次 A\***（kongkongxiyou 的核心优化） |
| **`closed` 惰性删除** | L128-130 | 标准 A\* 写法，避免"重开 close 节点" |
| **AOI 只返回 uid，不碰网络** | `aoi.watchers_of` | 分层干净、可单测；比 Survive 直接把 socket 塞进包更好 |
| **`tower_size` 可配** | `AOI.__init__` | 修正了 Survive"`radius` 兼作格边长、50/75 混用"的隐患 |
| **`stats()` 埋点** | `AOI.stats` | Survive 零埋点，接入后可直接观测 enter/leave 频率 |
| **`max_tiles_per_sec`/`burst` 走 config** | `mock_server.get_ratelimit` | 参数可热调，便于标定（P5） |

---

## 四、接线方案（**从"孤岛"到"在线"，4 步**）

> 目标：让 10204/10205 与怪物移动真正走 AOI + 校验。**按依赖顺序**，每步都可独立验证。

| 步 | 动作 | 涉及 API | 验收（可观测） |
|---|---|---|---|
| **S1 场景实体登记** | 进场景（10200/10201）时：自己 `add_watcher(rid, x, y, range_)`；`_npcs`/`_mons` 逐个 `add_object(bid_uid, x, y, types)`；**离开场景时 `remove()`** | `add_watcher` / `add_object` / `remove` | `/status` 里 `aoi.stats()['entities']` 与场景单位数一致；离开后回落 |
| **S2 10204 双向广播（P0）** | 收到 `CS_10204{x,y}`：① 限流 `check(rid, 距离)`；② 若目标格不可走 ⇒ 拒绝并回**当前服务端坐标**纠正；③ `aoi.move(rid,x,y)`（= `update_watcher`+`update_object` 合并，见 A4）；④ 用 `watchers_of`/`update_object` 产出的 watcher 列表推 `SC_10204{rid,srv_id,x,y}` | `MoveRateLimiter.check` + `MapGrid.walkable` + `AOI.move` | **两个客户端同场**互相能看到移动（当前看不到）；日志出现 `enter/leave` |
| **S3 10205 瞬移校验** | 目标格必须 `walkable`；距离与冷却走限流；成功后同样双向广播（瞬移也要让别人看到） | 同 S2 | 穿墙瞬移被拒；日志有 `reason` |
| **S4 怪物实时移动（P1）** | 加"服务端自走器"（100ms）：怪物按 `path_for_walk` 逐格推进（P2）→ `AOI.update_object` → 按协议推 `10212/10213` | `find_path(...,compress=False)` + `update_object` | 客户端看到怪物移动；`stats()['update']` 增长 |

**阻塞项（必须先解决才能让 S2/S3 真正有效）**
1. **P3 阻挡数据**：没有 `blocked`，S2/S3 的"可走"判断恒真 ⇒ **校验是假的**。
2. **P5 限流参数**：未标定 ⇒ 要么误杀要么放行加速。
3. **A4 合并 API**：不先做，S2 极可能只调一半 ⇒ 重现"别人看不到我动"。

---

## 五、与 Survive 参考设计的对照评分（D11–D14）

| 设计点（我的 R1 编号） | Survive 的做法 | JSTM 现状（本审查） | 评分 |
|---|---|---|---|
| **D11 AOI：网格+视野集合+集合差+双向回调** | C 模块；`view_objs` 位图；`cal_blockset`；`cb_enter/cb_leave` | ✅ 四点全有；A4 的"双向需成对调用"是**退化**（Survive 一次 `aoi_moveto` 完成双向）；A2 性能待改 | **8/10** |
| **D12 寻路：A\* + LOS 裁剪 + 共享碰撞网格** | `find_path` + `lineto`(返回点列) + `.meta` 网格 | ✅ A\* 更好（octile/禁贴角）；⚠️ **LOS 丢了"返回点列"**（P1）；🔴 **碰撞网格未接入**（P3） | **6/10** |
| **D13 移动同步** | 客户端发目标点 → 服务端算路径 → **只广播目标点** → 服务端时间预算自走 | ❌ **与 JSTM 协议方向不同**：JSTM 是客户端**逐步上报坐标**（10204）；⇒ Survive 的"只广播目标点"**不适用**；「服务端自走器」仍未实现（P7） | **3/10**（需按 JSTM 协议重设计，见 `jstm_mapping.md` §3.1） |
| **D14 进视野/重连补发状态** | `SendEnterSee` 补 `CMD_SC_MOV` + `buff:OnEnterSee`；`ReConnect` 逐个重建 | ❌ 未实现（S1/S2 未接线 ⇒ 无"新人与老玩家互相可见"的处理） | **0/10** |
| **A10/A11（借鉴而非照抄）** | — | ✅ **两个文件的来源声明都正确标注了 Survive 的设计来源与 GPLv3 警示**，且明确写了"完全自研" | **合规 ✅** |

---

## 六、一句话总结

> `aoi.py` 与 `pathfind.py` 的**设计与工程质量都高于 Survive 参考实现**（精确圆判定、octile 启发、禁贴角、AOI 不碰网络、限流校验、埋点），并且**来源声明与 GPL 合规处理正确**；
> 目前唯一的问题是它们**还没接上任何一条业务线**——而接线的三个前置（**阻挡数据**、**限流标定**、**双向更新合并 API**）里，有两个（P3/P5）会直接决定"校验到底是真防作弊还是走过场"。

---

## 七、【待验证】与【未知】

| 项 | 状态 |
|---|---|
| JSTM 客户端是否需要"self enter see"事件（A5） | 【待验证】需与客户端 `scene_controller`/`model:syncRoles` 行为对齐（Survive 客户端需要） |
| JSTM 客户端真实移动速度（P5 标定依据） | 【未知】需真机 10204 采样（`analysis/1.4.9/movement/movement_test.md` 可能有线索，**本轮未读**） |
| `_config_map_block.luac` 的格式与坐标系（P3 数据源） | 【未读】`analysis/1.4.9/task/_mapblock_dis.txt`、`_config_map_block.luac` 存在但**本轮未打开** |
| `10212/10213`（怪物实时移动）的确认字段 | 【待验证】`movement_protocol.md` 标为"待定性" |
| `mock_server.py` 的 `/status` 之外的 AOI 使用意图 | 【未知】——可能并行 Agent 正打算接入；本审查**不代替其计划**，仅提供对照结论 |
| 本审查文件在 `server/` 继续演进后的有效性 | ⚠ **仅对 §1 表头的 MD5 负责** |

---

## 八、★ 修复与接线记录（2026-09-18 22:05–22:14，**已实施并验证**）

> 本节由**实施者本人**在改完之后回写，用于让并行的 Agent **不要重复劳动**。
> ⚠ **§1–§7 描述的是"修改前"的状态**；本节记录"修改后"的现状与新哈希。

### 8.1 改动前后哈希

| 文件 | 修改前 MD5 | **修改后 MD5** |
|---|---|---|
| `server/aoi.py` | `D5F0D2E569588FA017BCDE88993905D6` | **`6091ADEE79F89291D21759F14913ABB3`** |
| `server/pathfind.py` | `BD1C0E12ED08B750C5ADE9AD1CBA7067` | **`048043EE9D276B499717D423E89F4D54`** |
| `server/mock_server.py` | `A1A7622A0F4FB7145CEB2B300AC4567C` | **`5AE4AAF9758AA49EF3032E82E9C6FD0E`** |

### 8.2 已修复的缺陷（8 条，全部有测试）

| 编号 | 缺陷 | 修复方式 | 验证 |
|---|---|---|---|
| **A1** | `remove()` 单向清理 ⇒ 重复 leave / 幽灵事件 | 双向对称清理（`w.seen.discard` + `o._old_watchers.discard` + 清空自身两集合） | 单元测试 |
| **A2** | `_visible_watchers` 每次 O(全部实体) 扫描 | `_maxr` 增量缓存 + `_maxr_dirty` 惰性失效（只在删掉最大视野者时失效） | 单元测试（含"删除非最大者不应 dirty"） |
| **A3** | `update_*(uid,x)` 只给一个坐标会**静默忽略 x** | `_resolve_xy`：只给一个坐标 ⇒ **抛 `ValueError`**；(None,None) 仍表示"只重算视野" | 单元测试 |
| **A4** | 两向更新必须成对调用，漏一个就单向失明 | 新增 **`move(uid,x,y)`** 一次双向（对应 Survive `aoi_moveto`） | 单元测试 |
| **A8** | ⭐ **两向更新不交叉维护对方集合 ⇒ 对方下次移动会收到重复 enter/leave** | `_diff` 同步 `_old_watchers`；`update_object` 同步 `seen`（= Survive `enter_me(o,cur)`+`enter_me(cur,o)` 同时置两侧） | 单元测试（严格断言两侧集合） |
| **A9** | ⭐ **`add_watcher` 传 `is_object=False`，与自己文档"watcher 默认也是 object"矛盾 ⇒ 玩家对任何人都不可见** | 新实体改为 `is_object=True`；新增 **`add_player()`** 便利入口（一次注册两角色） | 单元测试（两玩家互见） |
| **P1 / P1b** | `line_of_sight` 只回 bool，**丢失"遇障碍即停返回点列"**；按欧氏缩放使 45° 前进 3 格只得 2 格 | 新增 `bresenham_points()` / `walk_until_blocked()` / `forward_to()`（后者改**主轴缩放** ⇒ 步数恰为 `tiles`） | 单元测试（`forward_to 45° 3 格 == (3,3)`、墙前停 `(4,0)`） |
| **P2 / P4 / P4b** | 路径被无条件 2 点化+压缩（服务端自走会瞬移）；`verify_path` 允许贴角而 A\* 不允许；**LOS 快路径也不查贴角（服务端生成的路径通不过自己的校验）** | 新增 `compress=`/`los_shortcut=` 参数与 **`path_for_walk()`**；`verify_path` 与 `bresenham_points` 统一加"禁贴角穿缝" | **6000 次随机地图自洽测试：0 失败** |

### 8.3 已接线（`mock_server.py`，4 处）

| 位置 | 内容 |
|---|---|
| 新增辅助函数（`live_push` 之后） | `_scene_rid / _scene_enter / _scene_ensure / _scene_leave / _authoritative_pos / _scene_validate_move / _scene_apply_move / _scene_broadcast_10204` + `_LAST_POS` |
| `_send_10200` | 进场景即 `_scene_ensure(self)`（幂等登记） |
| `10204/10205` 分支 | ① ensure → ② **服务端校验**（可走性 + 可选限流）→ 拒绝时**回权威坐标**纠正 → ③ `_scene_apply_move`（`aoi.move` 双向）→ ④ **只向"看得见我的人"广播 `SC_10204`** |
| `_unregister_live` | 断线 `_scene_leave(self)`（`aoi.remove` 正常派发 leave + 限流状态复位） |

**新增配置键**（`config.json` 未改，走默认值）：
| 键 | 默认 | 说明 |
|---|---|---|
| `aoi_broadcast` | `true` | 是否向 watcher 广播移动。**单客户端 ⇒ 恒 0 条 ⇒ 零回归** |
| `aoi_view_range` | `15` | 玩家视野（瓦片） |
| `aoi_tower_size` | `8` | AOI 塔格边长（已有） |
| `move_rate_limit` | **`false`** | ⚠ **默认关闭**——12 格/秒未按真机标定，打开会误杀（P5）。标定后再开 |
| `move_max_tiles_per_sec` / `move_burst` | `12.0` / `6` | 限流参数（P5 标定入口，已有） |

### 8.4 验证结果（4 层）

| 层 | 内容 | 结果 |
|---|---|---|
| 编译 | 三个文件 `py_compile` | ✅ |
| 模块单元 | AOI 六项修复 + 寻路五项 + A2 缓存语义 | ✅ |
| 协议回归 | **真启动**（备用端口 8099/9099）→ 10001/1110/10102/10200/10201/10204/10205/1199 | ✅ `SC_10204` 内容与接线前**完全一致**；`bcast=0 watchers=0` |
| 广播集成 | 用**真实接线函数** + 两个假 handler（不同 rid） | ✅ 对方收到 `SC_10204{rid,srv_id,x,y}`；不污染发送者；走出视野后 `watchers=∅` |

**新增测试工具**（可直接复用）：
- `tools/test_aoi_wire.py` — 协议回归（**先读 DB 原坐标、测后恢复**，不污染共享状态）
- `tools/test_aoi_broadcast.py` — 广播链路集成测试
- `tools/test_map_collision.py` — **碰撞校验回归**（可走格放行 / 阻挡格拦截并纠正 / DB 不污染）
- `tools/extract_config_mapblock.py` — 从 APK 提取 `Config.MapBlock` → `server/map_block.json`

---

## 九、★ 第二轮：P3 阻挡数据已接入（2026-09-18 22:15–22:55，**已实施并验证**）

> 上一轮我把 P3 列为"🔴 仍然是纸面校验"。本轮**用客户端自带配置把它解决了**。

### 9.1 数据来源与逆向（全部实测，非推测）

| 项 | 内容 |
|---|---|
| 来源 | **APK 内 `assets/src/config/config_map_block.luac` 的 `Config.MapBlock`** ⇒ 合规（APK 是最终标准，不是参考项目） |
| 结构 | 每行是一个 Lua 数组 `[None, c1, c2, ...]`，**行长 = cols + 1** |
| 分段 | 字节码 `TDUP <行表>; TSETB A=2 D=<行号>`，**行号 = `D & 0xff`**，**行号归 1 = 新场景** |
| 对齐 | 按 (行数, 行宽) 顺序对齐 `Config.Map` ⇒ **26 块全部对齐、0 未匹配**；其余 **90/124 场景无碰撞数据** |
| 产物 | `server/map_block.json`（126 KB，每行是数字字符串） |

### 9.2 ★ 格值语义：**被真实数据修正过一次**（重要教训）

| 值 | 占比 | 判定 | 依据 |
|---|---|---|---|
| `0` | 62.6% | **可走** | 判据A：95 个配置实体点 94.7% 落在 0；判据B：真实轨迹 375/386 = 97.2% |
| `1` | 62.6%→ 见下 | **阻挡** | 判据B：真实轨迹落在 1 上 **0/386（0%）** ⇒ 从未站上去 |
| `2` | 2.6% | **可走** | ⚠ **首版我判 2 为阻挡（理由是"无实体落在其上 + 邻接 1"），被真实轨迹否证**：真实 10204 坐标有 **11/386（2.8%）落在 2 上** ⇒ 客户端确实会走上去 |
| `4` | 7 格 | **可走**（宽容） | 样本不足，**避免误拦优先** |

> **教训**：静态判据（NPC 坐标）只能定"极性"，**定不了"哪些值算阻挡"**；
> 必须用**真实运行轨迹**（`server/logs/tcp.log` 的 10204 坐标）做动态验证。
> 首版若直接上线，会产生 **2.8% 的误拦/橡皮筋回拉**。

**最终误拦率（回归门槛）**：
```
tcp.log 387 个真实 10204 坐标 → 被拦下 0 个 = 0.00%   ✅
```

### 9.3 服务端接入点

| 位置 | 内容 |
|---|---|
| `load_mapblock()`（新） | 懒加载 `server/map_block.json`；缺失/失败 ⇒ `{}` ⇒ 全部 `allow_all`（**不因缺数据而阻断服务**） |
| `_scene_grid(bid)`（新） | 按场景建 `MapGrid` 并缓存；**只有 `'1'` 是阻挡**；无数据场景返回 `None` |
| `get_mapgrid(bid=None)` | **向后兼容扩展**：给 bid ⇒ 该场景网格或 None；不给 ⇒ 旧行为（256×256 allow_all） |
| `_current_bid(handler)`（新） | 取当前场景（`spawn.bid`），失败返回 None ⇒ 退化 allow_all |
| `_scene_validate_move` | 用**当前场景**网格判可走；**新增 fail-open**：若玩家**当前格本身**不可走则跳过校验 |
| 配置键 | `map_collision`（默认 **`true`**）；若要临时关闭碰撞只需置 `false` |

**★ 为什么必须 fail-open**：实测 **5/26 张场景的默认出生点本身落在阻挡格上**
（`20010/20100/20302/20303/20305`）。若一律拦截，这些场景的玩家会被**永久困死**。
现在改为：当前格不可走 ⇒ 放行并打日志。

### 9.4 本轮验证（4 层，全绿）

| 层 | 内容 | 结果 |
|---|---|---|
| 数据 | 26/26 块对齐；极性双判据；**真实轨迹误拦率** | ✅ 0.00% |
| 连通性 | 26 张场景从出生点出发的连通分量 / 可走格 | ✅ 21 张 85–110%（不会被困）；玩家位置可达 **25/25** NPC |
| 单元 | `get_mapgrid(10001)`：`walkable(79,53)=True`、阻挡格 `(79,52)=False`；无数据场景 → `None`；旧入口 → allow_all | ✅ |
| 协议 | 真启动回归：可走格放行、**阻挡格被拦并回权威坐标**、**DB 未被污染**、既有 10204/10205 链路不变 | ✅ |

### 9.5 ⚠ 并发与"在线服务版本"记录（**必须知道，含一条我自己的回归**）

**(1) 并发编辑风险**：本轮期间 **`mock_server.py` 被并行 Agent 同时修改过**（我编辑时收到
"file changed since it was read"）。我的改动经复查**全部仍在**；但同文件多人编辑是真实风险，
故本节登记哈希作为"我这版"基线。

**(2) 🔴 在线服务正运行"错版碰撞规则"（我引入的中间版本，必须重启修正）**

| 进程 | 启动时间 | 加载的阻挡格数（场景 10001） | 规则 | 结论 |
|---|---|---|---|---|
| **在线服务 `:9000`（PID 44148）** | **22:47:56** | **9094** | `!= '0'`（**把 `2` 也当阻挡**） | 🔴 **错版** |
| 我的修正版（`:9099` 测试实例） | 22:50:24 | **8522** | `== '1'`（正确） | ✅ |

**证据**：`9094 − 8522 = 572`，**恰好等于 scene 10001 中值 `2` 的格数（572）**。
（日志：`server.log` 第 312–313 行 vs 第 350–351 行）

**影响**：在线服务会**多拦 572 个客户端实际可走的格**；按真实轨迹统计，约 **2.8%** 的位置会被
拒绝并触发**橡皮筋回拉**（11/387 个已知坐标）。**症状可感知，但不致命。**

**修正方式（二选一）**：
1. ✅ **推荐**：**重启在线服务**（修正后的代码与 `map_block.json` 已在磁盘上，重启即生效，且保留碰撞功能）；
2. 权宜：把 `config.json` 的 `map_collision` 置 `false`（**同样需重启**才被读到；或用
   `/DSH_ADMIN/*` 运行时接口改 `CFG`，可立即生效，但会**暂时关闭碰撞**）。

> ⚠ 我**没有**擅自重启或改动在线服务（那是用户的进程，且重启者可能正在测试该功能）。
> 此处只作事实登记与操作建议。

### 9.6 仍未解决 / 未验证

| 项 | 状态 |
|---|---|
| **90/124 场景无碰撞数据** | ⚠ 这些场景仍是 `allow_all`（**不能阻挡未知的东西**）。若需覆盖，要从其他表（`gridType`/`fill_type`/客户端 TMX）再找数据源 |
| **`4` 的语义** | 【未知】全库仅 7 格，取"宽容=可走" |
| **P5 限流仍未标定** | 🔴 默认关闭（`move_rate_limit=false`）。**已有真实轨迹可供标定**：387 个坐标的相邻位移分布可直接算出合理阈值 |
| **真机双客户端端到端** | 🔴 仍被 `TcpHandler.cfg` 全连接共享（单 rid）阻塞 |
| **怪物/NPC 移动** | 未接线（缺"服务端自走器"；`10212/10213` 字段待定性） |
| **在线服务需重启** | ⚠ 修复与碰撞数据都要**重启服务**才生效 |

### 8.5 ⚠ 仍未解决 / 未验证（诚实边界）

| 项 | 状态 |
|---|---|
| **P3 阻挡数据未接入** | 🔴 **仍然是纸面校验**：`get_mapgrid()` 用 `allow_all=True`。接线已完成，**但 `walkable` 恒真** ⇒ 防穿墙无效。数据源待定（`_config_map_block.luac` / 场景图层） |
| **P5 限流未标定** | 🔴 默认**关闭**。需真机 10204 采样后打开 |
| **真机双客户端端到端** | 🔴 **被现有单角色设计阻塞**：`TcpHandler.cfg` 是**类属性、全连接共享** ⇒ 所有连接共用 `rid=1001` ⇒ AOI 只有 1 个实体。真机开两个客户端也**看不到广播**。要真正多角色，需把 `cfg` 改为**按连接独立**（牵动 `self.cfg` 的全局可变语义与 `json.dump(self.cfg)`），**本次未做**（风险 > 收益） |
| **怪物/NPC 移动** | 未接线（`10212/10213` 字段仍"待定性"；也缺"服务端自走器"） |
| **`SC_10201` 多角色** | 未改：仍只发 `roles=[自己]`。要让新进场的玩家看到别人，需要把其它连接的 role 也塞进 `10201`（已有开关 `send_roles_in_10201`，但**多角色编码未验证**） |
| **在线服务需重启才生效** | ⚠ 当前 PID 38492 跑的是**旧代码**；本文件的修复**要重启服务才会生效** |
