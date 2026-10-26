# Survive 场景 / 地图 / AOI / 寻路审计（逐文件 · 类/函数级）

> 对象：`gameserver/{map,maplogic,avatar,areatrigger,triggerfunction,util,snail,robot}.lua`、`groupserver/map.lua`、`groupserver/survive.lua`、`common/{aoi.c,aoi.h,lua_aoi.c,astar.c,astar.h,lua_astar.c,point.h,idmgr.h,Bresenhamline.lua}`、`gameserver/*.meta`
> 状态标记：【已确认】【待验证】【未知】；方法：`zipfile` 按需读取原文（**未修改任何文件**）
> 对照目标：**JSTM**（`analysis/1.4.9/scene/`、`movement/` 已有客户端协议事实；服务端**目前无 AOI、无寻路**）

---

## 一、结论速览（**本文件是六个报告中与 JSTM 缺口重合度最高的一份**）

| 项 | 结论 | 状态 |
|---|---|---|
| AOI 实现 | **C 模块**（`common/aoi.c` + `common/lua_aoi.c`），**网格分块 + 位图集合运算**，超出视距由**回调**通知 Lua（`enter_see`/`leave_see`） | 【已确认】 |
| 寻路实现 | **C 模块**（`common/astar.c` + `common/lua_astar.c`），A\* 8 邻域 + **直线视线裁剪**（Bresenham） | 【已确认】 |
| 碰撞数据 | 每张地图一个 **`.meta` 文本文件**：首行 `xcount`、次行 `ycount`、随后 `x*y` 个逗号分隔整数（0=可走） | 【已确认】 |
| 网格尺度 | `util.lua: gridpixel = 8` ⇒ **1 格 = 8 像素**；`TableMap[k].GridLength=400`、`ViewRadiu=600`（**像素**） | 【已确认】 |
| 移动同步策略 | **客户端只发目标点**；服务端算路径后**只广播"速度 + 目标点"**（不广播路径点）；服务端另有 **100ms 定时器**按路径推进自己的坐标 | 【已确认】 |
| 服务端移动推进 | `map.movtimer` 每 100ms 调 `map:process_mov()` → `avatar:process_mov()`，用**时间预算 `movmargin`** 一帧可跨多格（保证与客户端大致同步） | 【已确认】 |
| 视野事件 | AOI 回调直接落到 Lua 的 `avatar:enter_see(other)` / `leave_see(other)`，维护 `view_obj`/`watch_me` 双向表 | 【已确认】 |
| 实体 id | **`mapid << 16 \| 图内 idx`**（idx 来自每图一个 `IdMgr.New(4096/1024)`）；`GetMapById(id) = id >> 16` | 【已确认】 |
| 玩法派生 | `maplogic.lua` 里 **4 种 MapLogic**：通用 `maplogic` / `FiveVE`（5人PVE）/ `FiveVP`（5V5）/ `Survive`（生存赛），由 `TableMap[k].PlayType` + `maptype` 决定 | 【已确认】 |
| 场景分配 | **groupserver** 负责：按 `PlayType` 决定 `open`（占位进现有图）/`personal`（单开）/`mutil`（排队凑人），并用 `GetInstanceByType`/`GetMinGame` 挑 game | 【已确认】 |
| **对 JSTM 的价值** | **AOI 与寻路是 JSTM 完全缺失的两块，Survive 是五个参考项目里唯一给出可直接照抄"设计+算法"的**；但**代码不可复制**（无 LICENSE + C 模块还带 GPLv3 头） | 【已确认】 |

---

## 二、世界尺度与坐标

| 参数 | 值 | 出处 | 说明 |
|---|---|---|---|
| 网格 ↔ 像素 | **1 格 = 8 像素** | `gameserver/util.lua: local gridpixel = 8` | `Pixel2Grid(p)=floor(p/8)`，`Grid2Pixel(g)=g*8` |
| 地图格长 | `GridLength = 400`（像素） | `TableMap` | 用于 `Aoi.create_map(Pixel2Grid(400)=50, Pixel2Grid(600)=75, 0,0,xcount-1,ycount-1)` |
| 视距 | `ViewRadiu = 600`（像素）= 75 格 | `TableMap` | AOI 的 `radius` |
| 碰撞文件 | `Colision = "1400004.meta"` 等，11 个 `.meta` | `TableMap` + `gameserver/` 目录 | 见 §4.3 |
| 速度 | `avatar.speed = 27`；`process_mov` 里 `speed = self.speed * grid_edge * 1.2` | `avatar.lua` | 单位含义：`27 * 8 * 1.2 = 259.2` 像素/秒 |
| 方向 | 0/90/180/270/45/135/225/315（8 向）；`Util.Dir` 用 `atan2` + 转换 | `util.lua:Dir/DirTo/convertDir` | |
| 攻击距离等 | 表里单位是**像素**，代码里 `Pixel2Grid` 后再比较 | `util.lua:TooLong/TooClose` | |

⚠️ **`TableMap[205]` 被显式跳过**：`for k,v in pairs(TableMap) do if k ~= 205 then v.astar,v.xcount,v.ycount = Astar.create(...) end end` —— 理由【未知】；但 205 是 `garden`（家园），注释里另有 `require "common.TableScene_Pond"` 被注释 ⇒ 家园玩法未完成【已确认】。

---

## 三、AOI（C 模块）——**机制全解**

### 3.1 数据结构（`common/aoi.h`）【已确认】

```c
typedef struct { kn_dlist aoi_objs; uint32_t x, y, index; } aoi_block;   // 一个管理格 = 一个侵入式双向链表

typedef struct aoi_object {
    kn_dlist_node node;            // 挂在某个 aoi_block 的链表上
    uint32_t      id;              // 由 idmgr 分配，同时是"视野位图"的位下标
    bit_set_t     view_objs;       // ★ 当前对象视野内的对象集合（位图！）
    point2D       pos;
    void*         ud;              // 用户数据（Lua 侧是 luaRef_t*）
    struct aoi_map* map;
    uint8_t (*in_myscope)(aoi_object*,aoi_object*);   // 是否在视野内（本项目恒返回 1）
    void    (*cb_enter)(aoi_object*,aoi_object*);     // other 进入 self 视野
    void    (*cb_leave)(aoi_object*,aoi_object*);     // other 离开 self 视野
} aoi_object;

typedef struct aoi_map {
    bit_set_t  new_block_set, old_block_set;      // 移动时的"新/旧管理格集合"
    aoi_block **new_blocks, **old_blocks;         // 预分配的重用数组（避免移动时反复 malloc）
    aoi_block **enter_blocks, **unchange_blocks, **leave_blocks;
    point2D    top_left, bottom_right;
    uint32_t   x_size, y_size;                    // 管理格数量（= 地图尺寸 / _length 向上取整）
    uint32_t   radius;                            // ★ 视距（注意：同时也是"管理格边长"）
    uint32_t   max_aoi_objs;
    idmgr_t    _idmgr;
    aoi_block  blocks[];                          // 柔性数组
} aoi_map;
```

**★ 三个关键设计（值得借鉴的核心）**
1. **`view_objs` 位图**：每个对象用**位图**记录"我视野里有哪些对象"，`is_set(o->view_objs, cur->id)` 判断"是否已在我的视野" ⇒ **避免重复 enter 回调**，O(1)。位图大小固定 4096 位（`lua_aoi.c: new_bitset(4096)`），与 `aoi_create(4096, ...)` 的第一个参数对应 ⇒ **单图 AOI 对象上限写死 4096**【已确认】。
2. **"移动 = 集合运算"**：一次移动只做 3 类管理格的差集运算（`enter_blocks` / `unchange_blocks` / `leave_blocks`），**只对 enter/leave 处理全量遍历，unchange 里只做"距离检查"**。
3. **预分配重用数组**：`new_blocks` 等按"视距最多覆盖多少格"一次性 `calloc`（`radius_blocksize = (ceil(radius/_length))*2+1` 的平方），后续移动**零分配**。

### 3.2 函数逐一【已确认】

| 函数 | 机制 | 备注 |
|---|---|---|
| `aoi_create(max_aoi_objs,_length,radius,top_left,bottom_right)` | 计算 `x_size/y_size`（`length/_length` 向上取整）；**`if(radius > length \|\| radius > width) return NULL;`**；`if(radius < _length) radius = _length;`；`calloc` 整块 `blocks`；为每格 `kn_dlist_init`；建 2 个位图 + 5 个指针数组；`_idmgr = new_idmgr(0, max_aoi_objs-1)` | ⚠️ **`radius` 同时被当作"视距"和"管理格边长"用**（`get_block_by_point` 里 `x = (pos.x-top_left.x)/m->radius`）⇒ 本项目 `length` 与 `radius` 必须相等（否则格子尺寸与视距脱钩）。调用处 `Aoi.create_map(Pixel2Grid(GridLength)=50, Pixel2Grid(ViewRadiu)=75, ...)` ⇒ **length=50、radius=75 ≠ 50**，于是 `if(radius < _length)` 不触发，`get_block_by_point` 用 **radius=75 当格边长** ⇒ 实际管理格是 75 格（600 像素）见方，而预分配数组按 `ceil(75/50)*2+1 = 5` → 25 个格位 ⇒ **可能不足以覆盖 radius=75 时能进入的所有格**。**这是一个真实的越界隐患**【待验证】——需实测 `x_size/y_size` 与 `radius_blocksize` 的组合是否安全 |
| `get_block_by_point(m,pos)` | `x = (pos.x - top_left.x)/m->radius`；越界返回 NULL | 见上 |
| `cal_blocks(m,blocks,block_set,pos,radius)` | 由 `pos±radius`（并夹到地图边界）算出左上/右下格 → 双层循环把所有格写入 `blocks[]` 并 `set_bit(block_set, ...)` → `blocks[c]=NULL` 结尾 | 数组以 NULL 结尾（哨兵），后续 `for(i=0; blocks[i]; ++i)` |
| `cal_blockset(m,newpos,oldpos,radius)` | 同时算新旧集合 → 逐个旧格：若在 `new_block_set` 中 ⇒ `unchange`，否则 `leave`；逐个新格：若不在 `old_block_set` ⇒ `enter`；**最后清位图**（`clear_bit`） | 位图复用 |
| `enter_me/leave_me(me,other)` | `set_bit/clear_bit(me->view_objs, other->id)` + 调 `cb_enter/cb_leave` | |
| `block_process_enter(m,bl,o)` | 遍历该格链表，**双向检查**：`o` 看 `cur`、`cur` 看 `o`，各自满足 `in_myscope` 且不在视野才 `enter_me` | |
| `block_process_unchange` | 遍历该格，`o != cur` 时**双向确认**：在范围内且未在视野 ⇒ enter；不在范围但已在视野 ⇒ leave | ★ **"unchanged 格里也要做距离检查"**——因为对象位置变了，同一个格里也可能超出视距 |
| `block_process_leave` | 遍历该格，**已在视野的对象直接 leave** | |
| `aoi_moveto(o,x,y)` | ① `cal_blockset(new,old,radius)`；② `o->pos = new`；③ 若跨格 → `kn_dlist_remove(&o->node)`；④ 依次处理 `enter_blocks` → `unchange_blocks` → `leave_blocks`；⑤ 若跨格 → `kn_dlist_push(&new_block->aoi_objs, &o->node)` | **顺序很关键**（先 enter 再 unchanged 再 leave） |
| `aoi_enter(m,o,x,y)` | 置位 → 找格（失败返回 -1）→ `get_id(_idmgr,&o->id)`（失败返回 -1）→ `ENTER_BLOCKS`（**不写 block_set**，因为不需要差集）→ 逐格 `block_process_enter` → `kn_dlist_push` → **`enter_me(o,o)`（自己进自己视野）** → `o->map = m` | ★ **自己也在自己视野里**（Lua 侧 `avatar:SendEnterSee(o)` 因此会收到自己，客户端 "self enter see" 见 `robotclient.lua`） |
| `aoi_leave(o)` | `kn_dlist_remove` → `LEAVE_BLOCKS` → 逐格 `block_process_leave` → `leave_me(o,o)` → `release_id` → `o->map = NULL` | |
| `aoi_destroy(m)` | `free` 5 个数组 + 2 个位图 + idmgr + m | |

### 3.3 Lua 绑定（`common/lua_aoi.c`）【已确认】

| C 函数 | Lua 名 | 机制 |
|---|---|---|
| `lua_create_aoimap` | `Aoi.create_map(length,radius,tlx,tly,brx,bry)` | `aoi_create(4096, length, radius, ...)`，返回 `lightuserdata` |
| `lua_destroy_aoimap` | `Aoi.destroy_map(m)` | |
| `lua_create_aoi_obj` | `Aoi.create_obj(luaTable)` | **`toluaRef(L,1)` 把 Lua 表存成注册表引用**；`o->ud = luaRef_t*`；`o->view_objs = new_bitset(4096)`；返回 lightuserdata |
| `lua_destroy_aoi_obj` | `Aoi.destroy_obj(o, onmapdestroy)` | `onmapdestroy==0` 时 `aoi_leave(o)`；释放 `luaRef` + bitset |
| `lua_aoi_enter` | `Aoi.enter_map(m,o,x,y)` | 返回 bool |
| `lua_aoi_leave` | `Aoi.leave_map(o)` | |
| `lua_aoi_moveto` | `Aoi.moveto(o,x,y)` | |
| `cb_enter` | → **`LuaCallTabFuncS(*self, "enter_see", "r", *other)`** | 调用 Lua 表上的 `enter_see(self, other)` |
| `cb_leave` | → `LuaCallTabFuncS(*self, "leave_see", "r", *other)` | |
| `in_myscope` | **`return 1;`（恒真，且原 Lua 回调代码被整段注释）** | ⇒ **视距判定完全依赖 `cal_blocks` 的格子范围，不做精确圆形判定**；所以 `avatar.see_radius = 5` 是**死字段** |

**★ 结论**：AOI 的"业务感知"只有两个回调 **`enter_see` / `leave_see`**（Lua 侧实现见 §5.3），C 侧不认识"玩家/怪物/掉落物"的区别。这是很好的分层（**C 只做空间索引，语义全在 Lua**），**JSTM 可以完全照此设计**（Python 里用 `dict` + `set` 或直接 `shapely`/自写网格）。

### 3.4 AOI 复用到哪儿【已确认】

| 使用方 | 代码 | 说明 |
|---|---|---|
| 地图 | `map:new`: `o.aoi = Aoi.create_map(Pixel2Grid(GridLength), Pixel2Grid(ViewRadiu), 0,0, xcount-1, ycount-1)` | 每张地图实例一个 AOI map |
| 玩家/NPC/掉落物 | `avatar:Init`: `self.aoi_obj = Aoi.create_obj(self)`；`maplogic:entermap`/`CreateNPC`/`CreateDrop`: `Aoi.enter_map(map.aoi, obj.aoi_obj, x, y)` | |
| 区域触发器 | `areatrigger:Init`: 同样 `create_obj` + `enter_map`（**触发器也是 AOI 对象**） | |

---

## 四、寻路（C 模块）

### 4.1 A\*（`common/astar.c` / `astar.h`）【已确认】

| 项 | 实现 |
|---|---|
| 节点 | `AStarNode { kn_dlist_node list_node; struct heapele heap; parent; float G,H,F; uint32 x:16,y:15,block:1; }` —— **位域**：x 16 位、y 15 位、block 1 位 |
| 地图 | `AStar { int xcount,ycount; minheap_t open_list; kn_dlist close_list, neighbors; AStarNode map[0]; }`（柔性数组，一次 `calloc`） |
| 8 邻域 | `direction[8][2] = {上,下,左,右,左上,右上,左下,右下}` |
| 直线代价 | `cost_2_neighbor`: 前 4 个方向 **50.0f**，后 4 个 **60.0f**（≈ √2×50 的近似） |
| 启发函数 | `cost_2_goal`: **`(dx + dy) * 50.0f`（曼哈顿距离）** ⚠️ 对 8 邻域 A\* 用曼哈顿是**非一致（inadmissible 偏高）**启发，会牺牲最优性（可能返回次优路径）【已确认】 |
| `get_neighbors` | 清空共享 `neighbors` 链表 → 8 方向取节点 → **`if(tmp->list_node.pre \|\| tmp->list_node.next) continue;`（判断"是否在 close 表"靠链表指针非空）** → `block` 为假才 push |
| `find_path` | 起终点合法性检查（`from==to` 或 `to->block` 直接 0）→ `minheap_insert(open, &from->heap)` → 循环 `minheap_popmin` → 命中 `to` 时**回溯 parent 并 `push_front` 到 path**（**跳过起点自身**）→ `reset(astar)`；否则入 close 表 + 取邻居 → 邻居在 open 表（`n->heap.index`）则松弛，否则计算 `G/H/F` 入堆 |
| `reset(astar)` | 清空 close 链表（顺便把 `G/H/F` 归零）+ `minheap_clear(open_list, _clear)` |
| `isblock(astar,x,y)` | 供 `lineto` 用 |
| **内存** | `create_AStar`: `calloc(1, sizeof(*astar) + sizeof(AStarNode)*xsize*ysize)` ⇒ **一张 300×300 图 ≈ 90000 节点 × (~56B) ≈ 5 MB**，且 `map[205]` 之外**每张表里的地图都在进程启动时全部创建**（`map.lua` 顶层 for 循环）⇒ **启动即占几十~上百 MB**【已确认】 |

### 4.2 直线视线裁剪（`lua_astar.c:lua_lineto` → `Astar.lineto`）【已确认】

```
输入 astar(可 nil), (x1,y1) -> (x2,y2)
① 若 x1==y2 and x2==y2（原文如此，疑似应为 x1==x2 and y1==y2）→ 返回单点
② Bresenham：ux/uy 取 ±1；eps 累加；dx>dy 时沿 x 步进，否则沿 y 步进
③ 每步：if(astar && isblock(astar,x,y)) return 1;   ← ★ 撞墙即"提前返回已走的点"
④ 循环结束前把终点也 push（若终点不阻塞）
⑤ 返回 Lua 数组 {{x,y},...}
```
**★ 它做的是"射线检测（LOS）"，不是路径搜索**：从 A 到 B 沿直线走，遇障碍就停在障碍前。
⇒ 本项目用它实现：
- `Util.DirTo(map,pos,r,dir)`：从当前位置朝某方向走 `r` 像素（**走到障碍前就停**）
- `Util.ForwardTo(map,from,to,range)`：从 `from` 朝 `to` 前进 `range` 像素（同样遇障碍停）
⇒ **这是"击退、位移、追踪点、攻击落点"的计算器**（见 `battle.md`）。

### 4.3 `.meta` 碰撞文件格式（`lua_astar.c:lua_create_astar` + `readline`）【已确认】

```
readline(f, buf, ',', 1024) 逐个逗号分隔读取：
  第 1 个值 = xcount
  第 2 个值 = ycount
  之后 xcount*ycount 个值 = 每格 block 标志（0 = 可走，非 0 = 障碍）
```
- 每个值用 `atol` 解析；读到 0 长度即失败 → `lua_pushnil`。
- `coli[i]` **直接作为 `block` 位域（1 位）** ⇒ C 里 `tmp->block = flags[i*xsize+j]`（**只保留最低位**）【已确认】。
- ⚠️ **行/列主序**：`tmp = &astar->map[i*xsize+j]` 且 `tmp->y = i; tmp->x = j;`，读文件时也是 `coli[i] = ...` 顺序 ⇒ **文件是按行(y)优先**。JSTM 若要把 APK 的 `_config_map_block` 转成 `.meta` 格式，**必须注意行列序**。
- 示例文件大小：`1400003.meta`/`1400004.meta`/`1400005.meta` = 37,706 字节；`206.meta` = 452,384 字节 ⇒ **是文本数字**（不是二进制位图）。

### 4.4 寻路在场景里的用法【已确认】

| 位置 | 调用 | 说明 |
|---|---|---|
| `map:findpath(from,to)` | `Astar.findpath(self.astar, from[1],from[2], to[1],to[2])` | **网格坐标**（像素必须除 8） |
| `avatar:Mov(x,y)` | `self.map:findpath(self.pos,{x,y})` → 成功则 `self.path={cur=1,path=path}` + `map:beginMov(self)` + 广播 `CMD_SC_MOV` | ⚠️ `self.pos` 是**网格坐标**（AOI 也是网格坐标）⇒ **服务端全程用网格，只有速度/距离的表参数用像素** |
| `util.DirTo/ForwardTo` | `Astar.lineto(map.astar, ...)` | ⚠️ **注意：`lineto` 用的是 `map.astar`（原 AStar_t），而 `findpath` 也用它** ⇒ **两者共用同一个 `open_list`/`close_list`/`neighbors` 缓冲区**。由于 `find_path` 结束时会 `reset`，且 `lineto` 只用 `isblock`（不碰堆/链表），**实际安全**；但若将来有人把两者混在同一个协程里嵌套调用就会串数据【待验证】 |

---

## 五、场景实体与视野同步（`gameserver/avatar.lua`）

### 5.1 字段【已确认】
| 字段 | 含义 |
|---|---|
| `id` | `mapid<<16 \| idx` |
| `map` / `pos`{x,y} / `dir` / `speed`(27) | 空间状态 |
| `path` | `{cur=, path={{x,y},...}}` 当前路径；`nil` = 静止 |
| `lastmovtick` / `movmargin` | 移动推进的时间预算 |
| `aoi_obj` | AOI 对象句柄 |
| `view_obj` | **我看到的** `[id]=obj` |
| `watch_me` | **看到我的** `[id]=obj`（用于反向广播） |
| `avatid` / `avattype` / `nickname` / `teamid` / `fashion` / `weapon` | 表现数据 |
| `buff` | buff 管理器 |
| `skillmgr` | 技能管理器（玩家/NPC 都有） |
| `robot` | AI（掉线托管或 NPC） |
| `traceme` / `traceme_size` | **"谁在追踪我"**（AI 用，见 `battle.md`） |
| `hide` | 不进 AOI 视野（触发器用） |
| `isTrigger` / `Pickable` / `invisible` / `stick` | 语义标记 |
| `isRelease` | 已释放哨兵 |

### 5.2 函数逐一
| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `avatar:Init(id,avatid,map,nickname,attr,skillmgr,pos,dir,teamid)` | 建档 + `Aoi.create_obj(self)` + `Buff.New(self)` | ⚠️ | 见 `role.md`（参数过多） |
| `avatar:Send2view(wpk,exclude)` | **按 `gatesession` 分组**（同 gate 的玩家合成一个包）→ 每个 gate 一包（尾部附 sessionid 列表）；`exclude` 是排除列表 | ✅ **高度适合（思想）** | 见 `network.md` §3.2；**同屏广播必备优化** |
| `avatar:PackEnterSee(wpk)` | `u32 id + u8 avattype + u16 avatid + string nickname + u16 teamid + u16 pos.x + u16 pos.y + u16 dir + attr:on_entersee + u16 fashion + packWeapon` | ✅ 适合（字段可对照） | **"别人看我"要发什么字段** —— JSTM 的 `scene_init_protocol.md` 可逐项比对 |
| `packWeapon(wpk,weapon)` | `u16 id + u16 count + u8 条数 + (u8 下标 + u32 值)*`；无武器则 `u16 0` | ⚠️ | 与 `item:Pack` 格式重复 |
| `avatar:SendEnterSee(other)` | `CMD_SC_ENTERSEE` + `other:PackEnterSee(wpk)`；**若 `other.path` 存在，额外发一条 `CMD_SC_MOV`（速度 + 目标点）**；再 `other.buff:OnEnterSee(self)` | ✅ **高度适合（思想）** | ★ **"新人进入视野时，如果对方正在移动，必须补一条移动包"** —— 否则客户端看到对方原地不动。这是**极容易被忽略的同步细节** |
| `avatar:enter_see(other)` | 由 AOI 回调：`self.view_obj[other.id]=other; other.watch_me[self.id]=self;` + `self:SendEnterSee(other)`；若自己在跑 AI 则 `robot:NotifyEnterSee()`（**巡逻中停下来**） | ✅ 适合 | AOI 回调的语义实现 |
| `avatar:leave_see(other)` | 反向清理 + `CMD_SC_LEAVESEE` | ✅ 适合 | |
| `avatar:Mov(x,y)` | 守卫（`stick`/`isRelease`/`isDead`/无 aoi_obj）→ `map:findpath`；**失败发 `CMD_SC_MOV_FAILED`**；成功设 `path` + `beginMov` + **广播 `CMD_SC_MOV(id, speed, target)`**（**只发目标点！**） | ✅ **高度适合（思想）** | ★ **移动同步的核心思想**：服务端算路径，只广播**目标点**，客户端本地算同样的路径 ⇒ **省掉整条路径的带宽** |
| `avatar:process_mov()` | 见 §5.4 | ✅ 适合（思想） | |
| `avatar:StopMov()` | `self.path = nil`；唤醒 AI | ✅ 适合 | |
| `avatar:TransferTo(point)` | 瞬移：`StopMov` + `Aoi.moveto` + `pos=point` + 广播 `CMD_SC_TRANSFERMOVE` | ✅ 适合 | 传送/跳区 |
| `avatar:SetSpeed(speed)` | 变速；若正在移动则**重发一条 `CMD_SC_MOV`**（带新速度 + 原目标） | ✅ 适合 | ★ 速度变化要用**同一条移动包语义**通知，客户端才知道按新速度走 |
| `avatar:onRelease` / `avatar:Release(onMapDestroy)` | 清 path → `Aoi.destroy_obj` → 停 AI → **归还 idx（`self.map.logic.freeidx:Release(band(id,0xFFFF))`）** → `Gate.UnBind` → 清 `traceme` → 调自定义 `onRelease` | ⚠️ | ⚠️ `common/idmgr.lua` 的 `Release` **本身有 bug（用了未定义 `idx`）** ⇒ 归还的 id 是 `v=nil`，`Get()` 返回 nil，可能导致 id 池被"吃掉"【已确认】 |
| `avatar:Tick(tick)` | 只调 `self.buff:Tick(tick)` | ✅ 适合 | 实体心跳由 `map.generalTimer`（500ms）驱动 |
| `avatar:isDead()` | `attr:Get("life") <= 0` | ✅ 适合 | |
| `avatar:OnDead(atker,skillid)` | `buff:OnAvatarDead()` → `map.logic:OnAvatarDead(self,atker,skillid)` → 停 AI → `StopMov` | ✅ 适合 | 死亡交由**玩法逻辑**处理（复活/掉落/计分） |
| `avatar:DirTo(o)` | `Util.Dir(pos,target.pos)` | ✅ | |
| `avatar:AddTraceMe/RemTraceMe/SizeTraceMe/NotifyTraceMe/ClearTraceMe` | **追踪者登记表**（`traceme[id] = ava.robot`）；`NotifyTraceMe` 在每个移动节点推进时回调 `robot:NotifyTargetPosChange()` | ✅ 适合（AI 专用） | ★ AI 的"目标移动 → 唤醒追踪者"解耦设计 |
| `avatar:AssignAtkPoint(avatar,atkdistance)` | 单追踪者：算"离目标 `atkdistance` 的位置"（`ForwardTo`）；多追踪者：**轮流给 8 个方向**（`AtkDir` 队列）避免重叠 | ✅ 适合（AI 专用） | ★ 多怪围攻的**站位轮换**技巧 |
| `avatar:GetFollowPos(curdir)` | 8 方向轮询找"不与其他实体重叠（`CheckOverLap`）"的跟随点 | ✅ 适合（AI 专用） | |

### 5.3 视野同步时序（【已确认】，由代码推导）

```
A 移动一格 → Aoi.moveto → C 侧集合运算
   ├─ 对新进入的格：block_process_enter → 若互不在视野 → cb_enter
   │        └─ Lua: A:enter_see(B)  → A.view_obj[B]=B;  B.watch_me[A]=A;  A:SendEnterSee(B)   ← A 收到 B 的资料
   │              +  C 侧同时：B:enter_see(A) → B.view_obj[A]=A;  A.watch_me[B]=B;  B:SendEnterSee(A)  ← B 收到 A 的资料
   ├─ 对未变化的格：block_process_unchange → 距离检查后可能 enter 或 leave
   └─ 对离开的格：block_process_leave → cb_leave
            └─ Lua: A:leave_see(B) → 双向清理 + A:Send2Client(CMD_SC_LEAVESEE, B.id)
```
**★ `view_obj` / `watch_me` 是互为镜像的两张表**，`Send2view` 用 `watch_me`（"谁能看到我 → 我要广播给谁"），"谁在我的视野里"用 `view_obj`（AI 选目标、`CheckOverLap`）。**这是这套 AOI 的核心用法，JSTM 直接照做即可。**

### 5.4 移动推进：`avatar:process_mov()`（**本节是移动同步的算法核心**）【已确认】

```lua
function avatar:process_mov()
    if self.isRelease or self:isDead() or not self.path then return false end
    local path = self.path.path
    local now  = C.GetSysTick()
    local movmargin = self.movmargin + now - self.lastmovtick   -- ★ 本帧可用的"时间预算"
    local cur, size = self.path.cur, #path
    while cur <= size do
        local node   = path[cur]
        local newdir = Util.Dir(self.pos, node)
        local dis    = distance(newdir)                          -- 正交=8，对角=8*1.41
        local speed  = self.speed * grid_edge * 1.2              -- 27*8*1.2 = 259.2 像素/秒
        local elapse = dis / speed * 1000                        -- 走过这一格需要多少 ms（像素/速度）
        if elapse < movmargin then
            self.dir = newdir
            self.pos = node
            self:NotifyTraceMe()                                 -- 唤醒追踪我的 AI
            cur = cur + 1
            movmargin = movmargin - elapse
            Aoi.moveto(self.aoi_obj, node[1], node[2])           -- ★ 可能触发 enter_see/leave_see
            if not self.path then return false end               -- ★ AOI 回调里可能 StopMov
        else
            break                                                -- 预算不够，下一帧继续
        end
    end
    self.path.cur   = cur
    self.movmargin  = movmargin
    self.lastmovtick= C.GetSysTick()
    if self.path.cur > #self.path.path then
        self.path = nil
        self:Send2Client({CMD_SC_MOV_ARRI})                      -- ★ 到达通知
        if self.robot then self.robot:Wakeup() end
        return false                                             -- 返回 false ⇒ 移出 movingavatar 表
    else
        return true
    end
end
```

| 观察 | 结论 | 状态 |
|---|---|---|
| **时间预算 `movmargin`** | 一帧可推进**多格**，只要累计耗时不超过两次 100ms tick 之间的真实时间差 ⇒ **服务端坐标不会因 tick 抖动而落后客户端** | ✅ **高度适合（思想）** |
| `dis` 用 `distance(dir)` 按方向返回 8 或 11.28（`grid_edge*1.41`），**不是真实像素距离** | ⚠️ `speed` 也是 `27*8*1.2` ⇒ 量纲能对上，但名字有误导性 | 【已确认】 |
| `Aoi.moveto` 可能触发 `enter_see` → `robot:NotifyEnterSee()` → `StopMov()` ⇒ **`self.path` 被置 nil**，故有 `if not self.path then return false end` 的保护 | ✅ 好做法（**注释里明确写出了这个陷阱**） | 【已确认】 |
| `map:process_mov()` 遍历 `self.movingavatar`，**返回 false 的就从表里摘除** | ✅ 适合 | 只遍历"正在移动的实体"，**静态实体零开销** |
| `map.movtimer` = `Timer.New("runImmediate"):Register(function() o:process_mov() end, 100)` | ✅ 适合 | 10 Hz |
| `map.generalTimer` = 500ms：遍历所有 avatar 调 `Tick`（buff）+ `logic:Tick` | ✅ 适合 | buff/AI 逻辑 2 Hz |

---

## 六、地图实例与玩法派生（`gameserver/map.lua` + `maplogic.lua`）

### 6.1 `gameserver/map.lua`【已确认】

| 函数/代码 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| **模块顶层 for** | 遍历 `TableMap`（跳过 205）→ `v.astar,v.xcount,v.ycount = Astar.create("./gameserver/"..v.Colision)` | ⚠️ 部分 | ★ **思想：地图碰撞在进程启动时一次性加载并常驻**（避免运行时 IO）；⚠️ 但**同时创建所有地图的 A\* 结构**会浪费大量内存，JSTM 应**懒加载**（首次进图才建） |
| `maps` / `mapidx = IdMgr.New(65535)` | 所有地图实例 + **mapid 分配器（上限 65535）** | ✅ 适合 | ★ **"高 16 位是 mapid"** 直接对应 65535 上限 |
| `GetMapById(id)` | `maps[bit32.rshift(id,16)]` | ✅ 适合 | |
| `map:new(mapid,maptype)` | 建 `movingavatar` 表、`mapdef`、`astar`、**`Aoi.create_map`**、**`movtimer`(100ms)**、`MapLogic.New(o)`、**`generalTimer`(500ms)**、`maps[mapid]=o` | ✅ 适合（思想） | **"一个地图实例 = 一个 AOI map + 两个定时器 + 一个玩法逻辑对象"**，结构清晰 |
| `map:GetAvatar(id)` | `self.avatars[id]` | ✅ | |
| `map:findpath(from,to)` | 包装 `Astar.findpath` | ✅ | |
| `map:beginMov(avatar)` / `map:process_mov()` | 见 §5.4 | ✅ | |
| `map:Release()` | `onMapDestroy=1` → 逐实体 `Release(onMapDestroy)` → `Aoi.destroy_map` → **停两个定时器** → `maps[id]=nil` + `mapidx:Release(mapid)` → 清 logic | ✅ **高度适合（思想）** | ★ **"地图空了就回收，定时器必须一起停"**（否则泄漏）；JSTM 若有临时副本，这套回收流程直接照做 |
| `RegRpcService(app)` | 4 个 RPC：`EnterSurvive` / `EnterMap` / `LeaveMap` / `CliReConn` | ⚠️ | ⚠️ **`EnterSurvive` 引用了未定义的全局 `g_logic`**（`g_logic.start_tick` / `g_logic:entermap`）⇒ **该 RPC 一旦被调用必然报错**（`g_logic` 全项目无赋值）【已确认】 |
| `EnterMap(mapid,type,plys)` | `pcall` 包住：`mapid==0` ⇒ 新图（`map:new(mapid,type)`），否则取现有图；`m.logic:entermap(plys)`；失败则 `mapid==0` 时 `m:Release()`；返回 `{true,mapid,plyids}` / `{false,reason}` | ✅ **高度适合（思想）** | ★ **"用 `pcall` 保住 RPC 层不炸 + 失败回滚刚创建的地图"**；JSTM 的副本创建必须这样兜底 |
| `LeaveMap(id)` | `GetMapById(id).logic:leavemap(id)` | ✅ | |
| `CliReConn(id,gatesession)` | 查实体 → `Gate.GetGateByName(name)` → `Gate.Bind` → `ply:ReConnect()` | ✅ | |
| 消息处理 | `CMD_CS_MOV`（读 `Reverse_read_uint32` 取玩家 + `u16 x,y`）/`CMD_CS_USESKILL`/`CMD_CS_PICKUP`/`CMD_GGAME_CLIDISCONNECTED` | ⚠️ | 见 `network.md` §3.3（id 隐式相等契约） |
| `CMD_CS_PICKUP` | `ply.map:GetAvatar(objid)` → 若 `obj.Pickable` → `TableAvatar[obj.avatid].Item_ID` → **若 `Item_Type < 5`（装备）⇒ 直接变成玩家的 `weapon`**（`{id,count=1,attr={0×10}}`）+ `CMD_SC_UPDATEWEAPON` 广播；否则 `battleitems:AddItem` + `NotifyUpdate` → `obj:Release()` | ⚠️ 部分 | ★ 掉落物用 `TableAvatar.Item_ID` 反查道具（**用"单位表"描述掉落物**）；⚠️ **装备掉落直接替换武器、不校验等级/背包**，且**不通知 group 落库**（拾取只在场景内生效）【已确认】 |
| 监控定时器 | 每 5s 打 map 统计 | ✅ 适合（可观测性） | |

### 6.2 `gameserver/maplogic.lua` —— 4 种玩法【已确认】

**统一接口**（每个 logic 必须实现）：`Init(map)` / `GetAvatar(id)` / `leavemap(id)` / `OnClientDisconnect(ply)` / `OnEnterMap(wpk)` / `entermap(plys)` / `OnAvatarDead(avatar,atker,skillid)` / （可选 `Tick(tick)`）

| 实现 | 选择条件 | 核心机制 | 对 JSTM 的价值 |
|---|---|---|---|
| `maplogic`（通用/开放图） | `mapdef.PlayType == "open"` | 玩家自由进出；`leavemap` 后若 `plycount==0` 则 `map:Release()`；**`OnClientDisconnect` 把掉线玩家交给 AI 托管**（`ply.robot = Robot.New(ply,1); robot:StartRun()`） | ✅ **"掉线托管成机器人"**是很有价值的容错设计，JSTM 若做实时场景值得借鉴 |
| `FiveVE`（5 人 PVE） | `maptype == 203` | 进图时 `start_tick = now+10000`（10 秒准备）；**人数不足 5 就用 `CreateNPC` 造机器人玩家补位**；`StartRound()`：按 `TableTower_Defense[平均等级]` × `TableTower_Coefficient[轮次]` 生成 5 只怪（`attack/defence/maxlife`）；怪全灭 → 下一轮；玩家全灭 → 发 `CMD_GAMEG_5PVEAWARD` 给 group + 5 秒后 `KickAll` | ✅ 适合（**关卡数值结构**） | ★ **"塔防式无限轮次 + 系数表递增"** 是低成本无限副本的标准做法；⚠️ **系数不可抄**（`Fighter`/`Tower_Defense` 是编的） |
| `FiveVP`（5V5 PVP） | `maptype == 204/207/208` | 交错分队（`teamid` 1/2 交替）+ 固定出生点数组；人数不足用机器人补位；两队列存活计数归零判胜负；发 `CMD_GAMEG_PVPAWARD` + 5 秒 `KickAll` | ✅ 适合（**分队/胜负结构**） | ★ **"人数不足用机器人补位"** 对 JSTM 的单机/低人服**非常实用**（否则副本永远凑不齐人） |
| `Survive`（生存赛） | `maptype == 206` | 把地图按 `xcount/4 × ycount/3` 切成 **12 个区域**（`area`）；用 `snail.lua` 预计算的**螺旋遍历方案**决定爆炸顺序；每 10 秒炸掉一个区域（区域内玩家 `attr:Set("life",0)`）；区域内有 `TransferTo` 触发器供跳区；最后 1 人获胜 | ✅ 适合（**缩圈玩法结构**） | ★ **"缩圈 + 区域爆炸 + 传送跳区"** 是吃鸡类玩法的完整最小实现；JSTM 若有类似玩法可直接借结构 |
| `area`（区域对象） | —— | `Init(logic,index,leftTop,rightBottom,x,y)`：在四边中点造 `Trigger.New(...,1,pos)`（`TableTrigger[1].OnEnterRange = "TransferTo"`）+ 造 5 个掉落物；`InArea(pos)` 矩形判定；`Boom()` 杀区域内玩家 + 释放自己与友邻的跳区触发器；`NofifyBoom(t)` 倒计时广播 | ✅ 适合 | ★ **"用多边形/矩形做区域 + 用触发器做边界门"** 的思路清晰；⚠️ `RandomDrop()` 里 `CreateDrop(logic,...)` 用了**未定义全局 `logic`** ⇒ **一旦执行必崩**【已确认】 |
| 工厂 | `MapLogic.New(map)` | 按 `mapdef.PlayType` 与 `map.maptype` 返回对应 logic；**不认识则返回 nil** | ✅ 适合 | ★ **"配置驱动的玩法选择"**：JSTM 可用同样方式把"普通场景/副本/竞技场"分流 |

### 6.3 NPC 与掉落物创建【已确认】

| 函数 | 机制 |
|---|---|
| `CreateNPC(logic,avatid,nickname,weapon,attr,skills,pos,dir,teamid,aiid,runAi)` | 取 idx → `id = mapid<<16 \| idx` → `Avatar.New(...)` → `Aoi.enter_map` → `npc.robot = Robot.New(npc,aiid)` → 可选 `StartRun()`；失败返回 nil |
| `CreateDrop(logic,avatid,pos)` | 取 idx → `Avatar.New(id,avatid,map,"",{},nil,pos,1,0)` → `Aoi.enter_map` → **`drop.Pickable = true`** → 入 `avatars` |
| `maplogic:entermap(plys)` | **先检查 `freeidx:Len() < #plys`**（不够则整体失败）→ 逐个 `Player.New(...)` → `Gate.Bind` → `ply:on_entermap()` → `plycount+1` → `Aoi.enter_map`；返回 `gameids` 数组 |
| `maplogic:leavemap(id)` | `ply:Release()` → `plycount-1` → 删表 → **若 `plycount==0` 则 `map:Release()`** |

**★ `freeidx:Len() < #plys`**：**"要么全进、要么全不进"**的批量入场语义。`ReqQue:ProcessEnter` 依赖它（5 人副本必须一次进 5 个）。JSTM 的组队副本应照此做**原子入场**。

---

## 七、区域触发器（`gameserver/areatrigger.lua` + `triggerfunction.lua`）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `areaTrigger:Init(id,map,triggerid,pos)` | 查 `TableTrigger[triggerid]` → 存入 **`map.avatars[id]`** 与 **模块级 `triggers[id]`** → 读 `Hide/AvatID/Range` → 从 `TriggerFunc` 表取 `OnEnterRange`/`OnLeaveRange` 函数指针 → `Aoi.create_obj` + `enter_map` | ⚠️ | ⚠️ **触发器也是 AOI 对象**（好）；但 `triggers` 是**模块级全局表**而 id 来自**每图独立的 `freeidx`** ⇒ **不同地图的触发器 id 会冲突**，`triggers[id]` 互相覆盖【已确认】 |
| `TriggerTimer`（模块顶层） | `Timer.New("runImmediate"):Register(function() for k,v in pairs(triggers) do v:RangeCheck() end end, 50)` | ❌ 不适合 | ★ **50ms 全局轮询所有触发器**——而不是让 AOI 直接回调。**放弃了 AOI 的优势**，无谓消耗；JSTM 应让"进入区域"由 AOI 的 `enter_see` 触发 |
| `areaTrigger:RangeCheck()` | 遍历 `self.view_obj`，用 `Util.TooClose(pos, v.pos, range/2)` 判进入/离开 → 收集 `enterRange`/`leaveRange` → 逐个 `EnterRange/LeaveRange` | ⚠️ | 双表（`view_obj` 提供候选、`obj_range` 记录状态）避免重复触发，思路可用 |
| `areaTrigger:EnterRange/LeaveRange(o)` | 更新 `obj_range[o.id]` + `DoCallBack("OnEnterRange"/"OnLeaveRange", o)` | ✅ 适合 | |
| `areaTrigger:DoCallBack(f,o)` | `pcall(self[f], self, o)` + 错误日志 | ✅ 适合 | 触发器回调异常不应影响主循环 |
| `areaTrigger:enter_see/leave_see(other)` | 只把**非触发器**对象记入 `view_obj` | ✅ 适合 | 触发器互不感知 |
| `triggerfunction.lua` | `TriggerFunc = { TransferTo = function(self,avatar) local area = self.survive:GetArea(self.targetID); if area and not area.Boomed then avatar:TransferTo(self.targetPoint) end end }` | ✅ 适合（表驱动） | ★ **"配置表里的字符串 → 函数表"** 的派发模式（与 `bufffunction`/`skill.Suffer_Script` 一致），JSTM 的 NPC 对话/传送点/触发区都可用 |

---

## 八、groupserver 侧的场景分配（`groupserver/map.lua` + `survive.lua`）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `mapinstance`（`{game,size,max,id,type}`） | group 侧的"场景实例账本"；`AddPlyCount/SubPlyCount`；**人数归零则从 `maps[type]` 摘除** | ✅ 适合 | ★ **"中心节点记账本、场景节点执行"** 的分工（单进程 JSTM 可把两者合一，但**账本概念要保留**） |
| `GetInstanceByType(type,count)` | 遍历该 type 的实例：`if not v.game.sock then m[k]=nil`（**顺手清理掉线的 game**）；能容纳 `count` 则返回 `{game,instance}`；否则 `{Game.GetMinGame(),nil}`（**挑人数最少的 game 去开新图**） | ✅ **高度适合（思想）** | ★ **"能塞进已有实例就复用，否则找最闲的进程开新实例"** —— 这是负载均衡的最小实现 |
| `PackPlayer(ply)` | 把 group 角色的**必要子集**打包给 game：`nickname/actname/gatesession{name,id}/groupsession/avatid/fashion/weapon{id,count,attr}/attr:Pack2Game()/skills:GetSkills()/battleitem:FetchBattleItem()` | ✅ **高度适合（思想）** | ★ **跨进程传角色必须显式定义"场景需要哪些字段"**（Survive 的答案是上面 10 项）；JSTM 若把场景逻辑独立成模块，这个字段集就是**接口契约** |
| `EnterMapOpen` | `GetInstanceByType(type,1)` → `RPC EnterMap(0 或 现有 mapid, maptype, plys)` → `Game.Bind` → 若新建实例则记入 `maps[type]` → `ply.mapinstance=inst; status=playing` | ✅ 适合 | |
| `EnterMapPersonal` | 只回 `CMD_GC_ENTERPSMAP(maptype)`（**由客户端自己发起单人副本？**）⇒ **单人副本的进入并未真正走服务端 RPC** | ⚠️ **不完整** | 【待验证】单人副本（`CMD_CG_COMMIT_SPVE` 提交关卡）与 `personal` 地图的关系未读到完整闭环 |
| `ReqQue`（排队器） | `new(maptype,mapdef)`：`que=LinkQue`，`maxWait=mapdef.MaxWait or 5000`，`plyMax=mapdef.MaxPly`；`Push(ply)` 置 `status=queueing` + 记 `ReqTick`；`Tick()` 每 1 秒：**人数够了就 `ProcessEnter()`**，或队首等待超过 `maxWait` 也 `ProcessEnter()`（**人不够也开**）；`ProcessEnter()` 组 `plys` → `RPC EnterMap(0, maptype, plys)` → 建 `mapinstance` → 逐个 `Game.Bind` + 按 maptype 触发 5PVE/5PVP 的成就与任务 | ✅ **高度适合（思想）** | ★ **"凑够就开、超时也开"** 是低人服匹配的必备语义；JSTM 若做组队副本必须如此（否则永远进不去） |
| `MapReqQues` + 后台协程 | `Sche.Spawn(while true do for ... v.Tick() end; Sche.Sleep(1000) end)` | ✅ 适合 | 1 Hz 全局排队检查 |
| `EnterMap(ply,type)` | 判定顺序：**家园动作中禁止进图**（`fishing_start/gather_start/sit_start` 非 0）→ `type==206` 走 `Transfer`（生存赛）→ `PlayType == "open"/"personal"/"mutil"` 分流 | ✅ 适合 | ★ **"状态互斥检查前置"** |
| `LeaveMap(ply)` | `RPC LeaveMap(gamesession)` → `mapinstance:SubPlyCount(1)` → `Game.UnBind` → `mapinstance=nil` → `CMD_GC_BACK2MAIN` → `bag:SynBattleItem()` | ✅ 适合 | ★ **离图后重同步战斗背包**（因为战斗中的消耗只发生在 game 侧） |
| `groupserver/survive.lua` | 生存赛的**开启/报名/确认/传送**调度：`nextTime/applyDeadLine` 用 `Timer` 每小时滚动；`Apply` 校验时间与重复报名；`Confirm` 用 `Util.GenItem` 从 `TablePond` 抽奖得带入道具 → 记 `waitForTransfer` → `TransferTimerTick`（100ms）到点 `RPC EnterSurvive(PackPlayer(ply,item), nextTime+5*60, os.time())`；`CMD_GAMEG_SURVIVE_FINISH` 发奖给胜者 | ✅ 适合（**活动调度结构**） | ★ **"定时开启 + 报名窗口 + 延迟批量传送 + 结束结算"** 是限时活动的完整骨架；⚠️ **`waitForTransfer` 用 `table.insert` 存对象（数组），但 `TransferTimerTick` 里 `waitForTransfer[k]=nil`**，数组中间留洞（Lua 下 `pairs` 仍能遍历，但 `#` 会不可靠）；且 **`selectVipItem` 未定义**（`GenerateItem(selectVipItem)`）⇒ **确认入场必崩**【已确认】 |

---

## 九、对 JSTM 的建议（场景层）——**本报告的落地优先级最高**

### 9.1 AOI（JSTM 完全没有 ⇒ **P0**）

| 借鉴什么 | Survive 的做法 | JSTM 应如何做 |
|---|---|---|
| **空间索引 = 均匀网格** | 地图按"格边长 = 视距"切成 `x_size × y_size` 个 `aoi_block`，每格挂一条对象链表 | Python 用 `dict[(gx,gy)] = set(obj)` 或 `list`；格边长取 `max(view_radius, 一屏大小)` |
| **每个对象一个"视野位图/集合"** | `bit_set_t view_objs`（位下标 = AOI id），用于"是否已在视野 ⇒ 不重复回调" | Python 用 `set()` 存"我视野里的 obj id"；**必须做这个去重**，否则每次移动都会疯狂重复 enter |
| **移动 = 新旧集合差** | `cal_blockset` 算出 `enter / unchange / leave` 三类格，**只对这三类做处理** | 每次移动算 `new_cells - old_cells`、`old_cells - new_cells`、交集 |
| **只对 enter/leave 全量遍历；unchange 只做距离检查** | `block_process_enter/leave` 全量配对；`block_process_unchange` 只在 `o != cur` 时做范围判定 | 这是性能关键：**同一格内的其他对象不需要重新配对**（已在视野），只需检查是否超出视距 |
| **业务语义全在 Lua，C 只做索引** | C 只回调 `enter_see(self,other)` / `leave_see(self,other)` | Python 侧同样只暴露 `on_enter(a,b)` / `on_leave(a,b)` 两个钩子 |
| **两张镜像表 `view_obj` / `watch_me`** | `view_obj` = 我看到谁（AI 选目标 / 重叠检查）；`watch_me` = 谁看到我（**广播时用**） | ★ **广播必须用 `watch_me`**，否则会给看不到我的人发包 |
| **自己也在自己的视野里** | `aoi_enter` 里 `enter_me(o,o)` | 让客户端在自己进图时也收到一条"ENTERSEE 自己"（`robotclient.lua` 就依赖这个行为） |
| **`in_myscope` 可注入** | 本项目恒返回 1（视距由格子近似）；接口保留 | JSTM 若要做**扇形/圆形精确视距**，可在此挂钩（例如"朝向 ±60° 内才可见"） |
| **地图销毁必须显式释放** | `Aoi.destroy_map` + `map:Release()` 停定时器 | Python 里要显式从所有格子的集合里删对象，否则内存泄漏 |

⚠️ **不要照学的地方**：
- **`radius` 同时当"视距"和"格边长"**（本项目 `length=50`、`radius=75`，参数语义混乱，是隐患）；
- **AOI 上限 4096 写死在 C 里**（`new_bitset(4096)`、`aoi_create(4096,...)`）——JSTM 不要设死上限；
- **区域触发器不用 AOI 回调、改 50ms 全局轮询**（`areatrigger.lua` 的做法）——这是**反面教材**；
- **`triggers` 模块级全局表 + 每图独立 id** 造成的 id 冲突。

### 9.2 寻路（JSTM 完全没有 ⇒ **P0**）

| 借鉴什么 | Survive 的做法 | JSTM 应如何做 |
|---|---|---|
| **A\* 8 邻域 + 直线代价** | 正交 50、对角 60（≈√2×50） | 同构即可（Python 用 `heapq`） |
| **启发函数** | 曼哈顿 × 50 —— ⚠️ **对 8 邻域不一致**（会次优） | 建议用 **Octile（对角距离）**，公式见下 |
| **碰撞数据与客户端同源** | 服务端读 `.meta`（`xcount,ycount,block...`），**客户端也用同一份碰撞网格**（文档明写"服务器和客户端共享同样的寻路网格"） | ★ **这是关键前提**：JSTM 必须保证服务端与客户端用**同一张阻挡表**，否则"服务端算的路径客户端走不了"。JSTM 的 `_config_map_block.luac` 应作为唯一真源 |
| **直线视线（LOS）** | `Astar.lineto` = Bresenham 射线，**遇障碍即停并返回已走的点** | ★ 用于**击退/位移/追踪点/技能落点**，比 A\* 便宜得多。Python 只需 20 行 Bresenham |
| **内存与加载** | 启动时把所有地图的 A\* 结构全建好（柔性数组一次 `calloc`） | ⚠️ 反面：JSTM 应**按需加载**（首次进图建，LRU 淘汰）；且节点应用"二维数组 + 懒重置"而非每节点带 parent/G/H/F（Python 里用 `dict[cell] = (g,parent)` 即可，无需预分配整图） |
| **`findpath` 与 `lineto` 共用缓冲区** | 靠"lineto 只用 isblock"侥幸安全 | ⚠️ 不要照学；JSTM 应让两者**互不共享可变状态** |

**Octile 距离（建议 JSTM 采用）**：
```
dx,dy = abs(x1-x2), abs(y1-y2)
h = 50*(dx+dy) + (60-2*50)*min(dx,dy)      # = 50*(dx+dy) - 40*min(dx,dy)
```

### 9.3 移动同步（**P0，直接决定"玩家能不能动"**）

| 借鉴什么 | Survive 的做法 | JSTM 的注意点 |
|---|---|---|
| **客户端只发目标点** | `CMD_CS_MOV(x,y)` | ⚠️ **JSTM 的移动包格式必须来自 APK**（参见 `analysis/1.4.9/movement/movement_protocol.md`，**本轮未读该文件**）【未知】 |
| **服务端算路径 + 只广播目标点** | `CMD_SC_MOV(id, speed, x, y)` | ★ **省掉整条路径的带宽**；客户端本地用同一张网格重算路径 |
| **服务端自己也按路径走（时间预算）** | `process_mov` 的 `movmargin` 机制，10 Hz | ★ **必须做**：否则 NPC 追击、AOI 触发、拾取范围全都会偏 |
| **到达通知 `MOV_ARRI` / 失败 `MOV_FAILED`** | 分开的两种回执 | ★ 客户端据此结束/纠正本地移动 |
| **变速要重发移动包** | `SetSpeed` 若在移动中则重发 `CMD_SC_MOV` | ★ 否则客户端仍按旧速度走 |
| **新人进视野补移动包** | `SendEnterSee` 里若 `other.path` 存在则补 `CMD_SC_MOV` | ★ **极易遗漏**；否则新人看到的是"静止的移动者" |
| **AOI 回调可能打断移动** | `Aoi.moveto` → `enter_see` → `robot:NotifyEnterSee` → `StopMov` ⇒ 代码里显式检查 `if not self.path` | ★ 写 Python 时同样要防"回调里改了状态" |
| **`map.movingavatar` 只装移动者** | 静止实体不参与每帧遍历 | ★ 性能要点 |

### 9.4 场景分配 / 副本（**P1**）

| 借鉴什么 | 出处 | 价值 |
|---|---|---|
| **`PlayType` 配置驱动玩法**（open/personal/mutil ⇒ 不同 logic） | `TableMap` + `maplogic.lua:New` | ★ 新增玩法只加配置 + 一个 logic 文件 |
| **统一 logic 接口**（`entermap/leavemap/Tick/OnAvatarDead/OnClientDisconnect`） | `maplogic.lua` | ★ 场景容器与玩法解耦 |
| **凑够就开 / 超时也开** 的匹配队列 | `ReqQue:Tick` | ★ 低人服必需 |
| **人数不足用机器人补位** | `FiveVE/FiveVP:entermap` | ★ 单机/小服必需 |
| **原子入场**（`freeidx:Len() < #plys` 整体失败） | `maplogic:entermap` | ★ 组队副本一致性 |
| **地图空即回收**（含停定时器） | `map:Release` | ★ 防泄漏 |
| **批量入场用 `pcall` + 失败回滚刚建的地图** | `map.lua:EnterMap` RPC | ★ 防 RPC 层崩溃 |
| **掉线玩家交给 AI 托管** | `maplogic:OnClientDisconnect` | ★ 容错（也可换成"原地待机"） |
| **`PackPlayer` 显式字段集** | `groupserver/map.lua` | ★ 跨模块接口契约 |
| **限时活动骨架**（定时开启/报名窗口/延迟传送/结束结算） | `groupserver/survive.lua` | ★ 可直接借结构 |

### 9.5 禁止 / 警示

| 项 | 原因 |
|---|---|
| 🚫 **抄 `.meta` 格式与 `TableMap` 字段** | JSTM 的地图/阻挡来自 APK（`_config_map_block.luac`），**格式必须自成一套** |
| 🚫 **抄 `GridLength=400 / ViewRadiu=600 / speed=27` 等数值** | 这些是 Survive 自己的世界尺度；JSTM 的坐标尺度必须与 APK 一致 |
| 🚫 **抄 `Aoi.create_map` 的参数语义**（`radius` 兼作格边长） | 参数语义混乱，是隐患 |
| ⚠️ **`areatrigger.lua` 的 50ms 全局轮询** | 反面教材 |
| ⚠️ **`g_logic` 未定义**、**`area:RandomDrop` 的 `logic` 未定义**、**`common/idmgr.lua:Release` 用未定义 `idx`**、**触发器 id 跨图冲突** | 至少 4 处会崩/会错的实现缺陷，**不要借鉴其实现细节** |
| ⚠️ **`CMD_CS_PICKUP` 拾取装备直接替换武器且不落库** | 数据一致性风险 |

---

## 十、【未读到】/【未知】

| 项 | 状态 |
|---|---|
| **JSTM 的移动/场景协议细节** | 【未读】`analysis/1.4.9/movement/movement_protocol.md`、`analysis/1.4.9/scene/scene_init_protocol.md` 等本轮**未打开**；因此本报告只声称"Survive 的做法如何"，**不对 JSTM 应当如何包格式下结论** |
| `.meta` 文件的**具体数值内容** | 【未读到】只确认格式（首行 xcount 等），未逐文件核对（`206.meta` 452 KB、`escape.meta` 508 KB 等） |
| `map[205]`（garden）为何跳过 | 【未知】 |
| `personal`（单人副本）的完整闭环 | 【未读到】`groupserver/map.lua:EnterMapPersonal` 只回一个包，**未见服务端创建地图**；与 `CMD_CG_COMMIT_SPVE`、`TableSingle_Copy` 的关系【未知】 |
| `Aoi` 的 `x_size/y_size` 与 `radius_blocksize` 是否匹配（越界隐患） | 【待验证】需实测或读 `bitset.h`/`kn_dlist.h`（**两文件不在 ZIP 内**，属 KendyNet） |
| `bitset.h` / `kn_dlist.h` / `minheap.h` / `kn_string.h` / `lua_util.h` | 【未读到】—— 这些是 `Makefile` 引用的外部依赖（`../KendyNet`、`../deps`），**ZIP 内不存在** |
| 客户端侧寻路实现（`client/src/GameScene.lua` 等） | 【未读到】——"客户端与服务端共享寻路网格"来自文档描述，**代码层未验证**（本轮不审计客户端） |
| `CTimeUtil` 时区语义 | 【待验证】见 `role.md` |
| `TableScene_Pond` / 家园（maptype 205）玩法 | 【未实现】`maplogic.lua` 里相关 `require` 被注释 |
