# 寻路（Pathfinding）审计

> 参照物：`kongkongxiyou-master/lordofpomelo/game-server/app/domain/map/map.js`（17.9 KB）、`app/util/pathCache.js`、`app/domain/action/move.js`、`app/servers/area/handler/playerHandler.js`
> 结论标记：**【已确认】** / **【待验证】** / **【未知】**

---

## 0. 前提：A* 内核同样不在仓库里

| 事实 | 证据 | 置信度 |
|---|---|---|
| 通过 `require('pomelo-pathfinding').buildFinder` 使用 A* | `map.js` 第 1 行 | 【已确认】 |
| `pomelo-pathfinding >=0.1.0` 声明为依赖，**未随 ZIP 打包** | `game-server/package.json`；全 ZIP 搜索 `pomelo-pathfinding` **0 命中** | 【已确认】 |
| `PriorityQueue` 来自 `pomelo-collection`，同样未打包 | `pathCache.js` 第 1 行 | 【已确认】 |

**所以本报告能确认的是「项目侧怎么用」，A* 的启发函数/开放列表实现【未知】。但契约很清晰：**

```js
this.pfinder = buildFinder(this);        // 传入 map 自身作为「可达性提供者」
// 内部会回调 map.forAllReachable(x, y, processReachable) 拿邻居
paths = this.pfinder(tx1, ty1, tx2, ty2);  // 传入/返回的都是【tile 坐标】
```

由 `forAllReachable` 只提供**上下左右 4 邻域** → **A* 是 4 向（曼哈顿）扩展【已确认】**（依据是被调用的邻居回调只有 4 个方向）。

---

## 1. 逐文件表格

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `lordofpomelo/game-server/app/domain/map/map.js` | `Map(opts)` / `init(opts)` | `this.mapPath = process.cwd()+"/config/map/mapEntity"+opts.pathId+".json"`；`require(mapPath)` 拿 `{collisions, mob, npc, collision, birth, transport}`；算 `rectW=ceil(width/tileW)`、`rectH=ceil(height/tileH)`；`this.weightMap = getWeightMap(map.collisions)`；`this.pathCache = new PathCache({limit:1000})`；`this.pfinder = buildFinder(this)` | ✅ **强适合** | **「世界坐标 + tileW/tileH 网格」的双坐标体系**是 2D 端游标配；JSTM 应照搬 `width/height/tileW/tileH/rectW/rectH` 这 6 个字段 |
| 同上 | `getWeightMap(collisions)` | 建 `rectW × rectH` 二维数组，全填 `1`；遍历 `collisions[x]`（**按 x 列组织的 `[[startY, length], ...]` 压缩格式**），把障碍格置为 `Infinity` | ✅ **强适合** | **「碰撞按列压缩成 (起始y, 长度) 段」**非常省内存，且构造 O(障碍数) 而非 O(格子数)。JSTM 直接采用 |
| 同上 | `forAllReachable(x,y,processReachable)` | 边界 clamp 后回调 4 个方向，**带权重参数**：`processReachable(x, y-1, weightMap[x][y-1])` 等 | ✅ **强适合** | 这是 A* 的「邻居提供者」契约；**把权重一起给出**，A* 就不需要再回查地图 |
| 同上 | `getWeight(x,y)` | 返回 `weightMap[x][y]` | ✅ | — |
| 同上 | `isReachable(x,y)` | **世界坐标** → `x1=floor(x/tileW), y1=floor(y/tileH)` → 越界/无行/无列 → false → 返回 `weightMap[x1][y1] === 1`；外面包了 `try/catch` 兜底 | ⚠️ 部分 | 逻辑正确但 **「`=== 1` 的严格判定」意味着任何非 1 非 Infinity 的权重（如减速地形）都会被判为不可走**；JSTM 应用 `weight < INF` 判定，以支持沼泽/减速等 |
| 同上 | `_checkLinePath(x1,y1,x2,y2)` | **直线可达性检测**：`px===0` 沿 y 逐步 `+= tileW/2` 检查；`py===0` 沿 x；斜线则按 `dis` 归一化方向向量，步长 `tileW/2` 逐段 `_testLine` | ✅ **强适合** | **「先测直线，通了就免 A*」是寻路性能的第一大杀器**（大多数点击移动都是直线可达）。JSTM 必做 |
| 同上 | `_testLine(x,y,x1,y1)` | 两端可达 → 若同 tile 行/列直接 true；否则算跨格处的中点 `(x3,y3) = ((x0+maxTileX)/2, ...)` 再验 | ⚠️ 部分 | 采样法有漏检可能（薄墙）；且**用 `this.tileW` 算 tileY**（`floor(y/this.tileW)` 而非 `tileH`）——**当 tileW ≠ tileH 时是 bug**【已确认】 |
| 同上 | `findPath(x,y,x1,y1,useCache)` | ① 越界→null ② 起点不可达→null ③ 终点不可达→null ④ **`_checkLinePath` 通过 → 直接返回 `[{x,y},{x1,y1}]`** ⑤ 转到 tile 坐标 ⑥ `pathCache.getPath(tx1,ty1,tx2,ty2)` ⑦ 未命中 → **`pfinder(tx1,ty1,tx2,ty2)`** ⑧ `useCache` 为真才 `addPath` ⑨ tile→世界坐标 `transPos` ⑩ `compressPath2` ⑪ 点数 > 2 时 `compressPath1(path,3)` + 再 `compressPath2` | ✅ **强适合** | 流程完整且顺序合理（快路径 → 缓存 → A* → 坐标转换 → 压缩）。**唯一问题：`useCache` 默认 `false`**，导致玩家点击移动永远不写缓存 |
| 同上 | `compressPath2(tilePath)` | 去掉「三点共线」的中间点：`isLine(oldPos, pos, nextPos)` 为真则丢弃 mid | ✅ **强适合** | 15 行解决「格子路径锯齿」，必做 |
| 同上 | `compressPath1(path, loopTime)` | **跳跃式拉直**：以 `j += 2` 的节奏尝试用直线替换中间点（`_checkLinePath(start.x,start.y,end.x,end.y)` 通过则跳过去），最多 `loopTime=3` 轮 | ⚠️ 部分 | 思路（视野拉直 / string pulling）是对的，但**`j += 2` 会跳过候选点，不是最优拉直**；且实现里 `newPath = [path[0]]`、边界补点逻辑绕，**最后 `return newPath` 而非 `path`**（循环结束后 `path` 已赋值，语义等价但可读性差）。JSTM 建议用标准「漏斗算法/射线拉直」（每点向最远可直达点连边） |
| 同上 | `verifyPath(path)` | 校验：① 长度 ≥ 2 ② 每个点 `isReachable` ③ 相邻点 `_checkLinePath` 通过 | ✅ **强适合** | **★ 关键：这个方法在本项目里从未被调用（脚本 grep：`app/**` 0 处调用）★** —— JSTM **必须**在接收客户端路径时调用它（见第 4 节） |
| 同上 | `getBornPlace / getBornPoint / generatePoint(pos,w,h)` | `generatePoint` 在给定矩形内随机取点，**最多重试 10 次**且每次都要 `isReachable`；都失败返回 `undefined` | ✅ 强适合 | 「随机点 + 可达性重试 + 上限」是标准做法 |
| 同上 | `genPos(pos, range)` | `generatePoint(pos, range, range)`，失败则退回 `pos` | ✅ | — |
| 同上 | `genPatrolPath(entity,w,h,pathCount=3)` | 以实体当前位置为起点，连续 `genRandomPoint` N 次（每次以上一个点为新原点），**最后把起点补回路径尾部**（形成闭环）→ 写 `entity.path` | ✅ **强适合** | **「巡逻路径 = 随机游走 + 闭环」**，配合巡逻 `Loop` 模式即可无限巡逻；JSTM 可加「限定在刷怪区内」的约束 |
| 同上 | `genRandomPoint(ox,oy,w,h,count)` | 在 `[ox±w/2, oy±h/2]` 随机取点，越界则镜像到另一侧；`checkPoint` 不通过则**递归重试，超过 10 次返回 undefined** | ⚠️ 部分 | 有上限是对的；但**递归实现**在大范围/高障碍率地图上可能深递归 |
| 同上 | `checkPoint(ox,oy,dx,dy)` | `isReachable(dx,dy)` && **`findPath(ox,oy,dx,dy)` 存在** | ❌ **性能陷阱** | **为了验证一个随机点，跑一次完整寻路！** 刷怪/巡逻每次生成点都可能触发 A*。JSTM 应改为「直线可达或距离阈值内」的轻量检查 |
| `.../app/util/pathCache.js` | `PathCache(opts)` / `genKey` / `getPath` / `addPath` | `limit = opts.limit \|\| 30000`（map 里传 `1000`）；`cache = {key: path}`；key = `"x1_y1_x2_y2"`（**tile 坐标**）；`addPath`：命中则更新 + 标记 `update=true` + 刷新 `time`；未满则 `queue.offer({time,key})`；**已满则 `pop()` 出最旧 key 并删除**（跳过 `update===true` 的，把它们重新 offer） | ⚠️ 部分 | **「key 用起终点对」意味着「起点不同但路线相同」无法复用**（可用「从某点到某点」的语义接受）；LRU 实现有 **崩溃风险**（见下） |
| 同上 | `comparator(a,b) → a.time < b.time` + `pomelo-collection.priorityQueue` | 期望是「按 time 的最小堆」 | ⚠️ 部分 | **比较函数返回布尔值而非负数/正数，是否被 priorityQueue 正确解释取决于该库实现【待验证】**；若按数值处理，`true/false` 会被强转为 `1/0`，**可能退化为恒等比较（假 LRU）** |
| 同上 | `addPath` 淘汰分支 | `var delKey = this.queue.pop().key; while (this.cache[delKey].update === true) {...}` | ❌ **有 bug** | 队列为空时 `pop()` 返回 `undefined` → `undefined.key` 抛异常；且**内层循环里 `delKey = this.queue.pop()` 取到的是对象而非 `.key`**（对比第一行 `.key`）→ `this.cache[对象]` 必然 undefined。**JSTM 不要照抄 LRU 实现** |
| `.../app/domain/entity/character.js` | `Character.prototype.move(targetX,targetY,useCache,cb)` | `area.map.findPath(this.x,this.y,targetX,targetY,useCache)` → 有路径则 `new Move({entity,path,speed:walkSpeed})` → **`area.timer.addAction(action)` 成功则 `messageService.pushMessageByAOI(area,'onMove',{entityId,path},this)`** → `cb(null,true)`；无路径 → `logger.warn` + `cb('find path error', false)` | ✅ **强适合** | **★ 这是「服务端自己算路径」的正确形态（AI/巡逻走这条）**；注意第 4 个参数 `this` 被当成 `ignoreList` 传给 `pushMessageByAOI(area,route,msg,pos,ignoreList)`，**实参个数与形参不匹配（pos 变成了 entity）** —— 靠 `getWatcherUids(pos,...)` 里 `aoi.getWatchers(entity, ...)` 鸭子类型工作【已确认，同 `getAreaInfoStrip` 的问题】 |
| `.../app/domain/action/move.js` | `Move(opts)` | `type=MOVE`、`id=entity.entityId`、**`singleton=true`**、`path=opts.path`、`speed=opts.speed\|\|entity.walkSpeed`、`index=1`、`pos=path[0]` | ✅ **强适合** | **`singleton=true` 保证一个实体同时只有一个移动动作**（`actionManager.addAction` 会先 `abortAction` 同类同 id） |
| 同上 | `Move.prototype.update(currentTime)` | `travelDistance = speed*(currentTime-this.time)/1000`；`while(travelDistance > 0)` 沿折线消耗距离：够到下一节点则 `index++`（越界则 `finished=true`、`setIsMoving(false)`），否则插值出中间点；更新 `entity.x/y = floor(pos)`；**然后两连发 AOI 更新**；`this.time = currentTime` | ✅ **强适合** | **「按速度沿折线滑行 + 单 tick 可跨多节点」**是无状态插值的正确写法（不依赖固定 tick 间隔）。**每 tick 更新 AOI 是必要的**（否则别人看不到你移动） |
| 同上 | `stopMove()` | `if (!entity.isMoving && entity.stand) entity.stand()` | ⚠️ 部分 | 只在新位置广播 `onStand`；`isMoving` 语义与 `handler.stop` 混用，容易漏推 |
| `.../app/servers/area/handler/playerHandler.js` | `handler.move(msg,session,next)` | **`var path = msg;`** → `new Move({entity:player, path})` → `timer.addAction` → 若起点与服务器记录不符，用 `timer.updateObject/updateWatcher` **把客户端起点当成权威** → `pushMessageByAOI(area,'onMove',{entityId,areaId,path},startPoint)`；末尾刷新 `player.kickTime` | ❌ **不可照抄** | **服务端把客户端上传的整条路径直接当作玩家真实路径**，无 `verifyPath`、无速度/长度/可达性校验 → 可穿墙、瞬移、加速、拉怪。【已确认】 |
| 同上 | `handler.clMove(msg,session,next)` | 客户端只给终点 `[x,y]`；服务端拼 `[{player.x,player.y},{x,y}]` → `Move` → 广播 `onClMove`（**忽略发送者**） | ⚠️ 部分 | 比 `move` 安全（起点服务端说了算），**但终点仍未校验可达性/距离** |
| 同上 | `handler.stop` | `timer.abortAction(ActionType.MOVE, player.entityId)` + `player.isStop=true` + `player.stand()` | ⚠️ 部分 | 服务端**不做位置回滚/校正**，客户端只需停发 move 就能停在任意（可能非法）位置 |
| `.../app/services/areaService.js` | `exp.getInitPoint(targetId,curAreaId,transportId)` | 无 `transportId` → `map.getBornPoint()`；有则遍历 `map.map.transport`，找 `transport.targetArea === curAreaId` 的那条，返回 `{x: transport.x+60, y: transport.y-30}` | ✅ **强适合** | **传送点数据驱动 + 来源反转查落点**，避免「从 B 回 A 时落在 A 的传送阵里」循环。JSTM 必做 |
| `.../config/map/mapEntity<pathId>.json` | 数据文件 | 每个场景一份（本次见到 `mapEntity{100,200,202,203,301..305,401,501..505,600..605}.json`，共 22 份，最大 27.7 KB）；包含 `collisions`（按列压缩）、`collision`（多边形）、`mob`（刷怪区）、`npc`、`birth`（出生区）、`transport`（传送点） | ✅ **强适合** | **「地图 = 数据文件，非代码」**这一原则必须继承；JSTM 应改为 JSON/YAML 便于 1.4.9 地图导入 |

---

## 2. 完整寻路流程（`findPath` 决策树）

```
findPath(x, y, x1, y1, useCache=false)
  │
  ├─ 越界?                                  → null
  ├─ isReachable(x,y) == false?             → null + warn
  ├─ isReachable(x1,y1) == false?           → null + warn
  │
  ├─ _checkLinePath(x,y,x1,y1) == true?     ──── 是 ──▶ return [{x,y}, {x1,y1}]     ★ 快路径，无 A*
  │                                                    （注释里还留着带 cost 的版本）
  └─ 否
     ├─ tx1=floor(x/tileW) ty1=floor(y/tileH) tx2=... ty2=...
     ├─ pathCache.getPath(tx1,ty1,tx2,ty2)
     │    命中 → 直接用
     └─ 未命中 → pfinder(tx1,ty1,tx2,ty2)     ← 外部 pomelo-pathfinding A*（4 邻域，内核【未知】）
                    失败 → null + warn
                    useCache 时 addPath(...)   ← 默认 false，所以几乎不写缓存
     ├─ transPos：tile → 世界坐标（取格子中心 x*tileW + tileW/2）
     ├─ compressPath2   （去共线中点）
     └─ 若 length > 2 → compressPath1(path, 3) → compressPath2  （拉直 + 再去共线）
```

**成本分析【已确认】：**
- 直线可达时 **0 次 A***。
- 缓存命中时 **0 次 A***（但见下：`useCache` 默认 false，玩家侧实际不命中）。
- 其余情况 1 次 A*（4 邻域，格数 = `rectW × rectH`）。
- `_checkLinePath` 本身的采样次数 = `直线距离 / (tileW/2)`；**长距离直线检测可能比 A* 还贵**（大地图上点一次很远的目标，会先做一次全程采样）。

**★ 性能陷阱汇总（【已确认】）★**

| 陷阱 | 位置 | 后果 |
|---|---|---|
| `checkPoint` 里调 `findPath` 做「点是否可达」判定 | `map.js` | **每次刷怪、每次随机巡逻点生成都可能触发完整 A\*** |
| `useCache` 默认 false | `findPath` 签名 | 反复寻路同一目标（追击/巡逻）无法复用 |
| `_checkLinePath` 全程采样 | `map.js` | 远距离直线检测成本线性增长 |
| 玩家每 tick 可能触发新寻路 | `handler.move` 由客户端驱动 | 恶意客户端可高频请求（**无限流**） |
| 主循环 100ms 内完成全部 action/AI/AOI | `timer.js` | 大量同时寻路会阻塞整个 Area（**单线程阻塞**） |

---

## 3. 缓存设计（`PathCache`）

| 参数 | 值 | 出处 |
|---|---|---|
| `limit` | **1000**（map 传入）／类默认 30000 | `map.js` `new PathCache({limit:1000})` |
| key | `"x1_y1_x2_y2"`（**tile 坐标**，非世界坐标） | `genKey` |
| 逐出策略 | 按 `time`（写入/更新时间）的优先级队列，满了逐出最旧 | `addPath` + `comparator` |
| 更新标记 | 已存在时置 `path.update = true`（**挂在 path 对象上**，容易被覆盖） | `addPath` |

**问题清单（【已确认】/【待验证】）：**

| 问题 | 类型 | 说明 |
|---|---|---|
| `priorityQueue.pop()` 返回 `undefined` 时 `undefined.key` 崩溃 | **【已确认】bug** | 队列空而 cache 满（逻辑上不该发生，但 update 标记路径会导致队列/缓存不同步） |
| `while` 内 `delKey = this.queue.pop()` 缺少 `.key` | **【已确认】bug** | 与上一行取值方式不一致，直接导致 `this.cache[Object]` = undefined → 下一轮 `undefined.update` 抛异常 |
| `comparator` 返回布尔值 | **【待验证】** | 依赖 `pomelo-collection` 内部实现；若按 `a-b` 语义处理则 LRU 退化为 FIFO/无效 |
| 缓存 key 不含「地图/场景」 | **【已确认】** | 不同场景的 `rectW/rectH` 不同 → **tile 坐标相同但含义不同**。不过每个 Area 有独立 Map 实例（`areaService.getMap` 全服共享同一 Map 对象！）→ **共享 Map 时不同场景若共享同一 weightMap 也是错的**【待验证】：`areaService.init()` 为每个 `area.id` 各建一个 `Map`，`maps[areaId]`，所以**每个场景一个 Map + 一个 PathCache，key 冲突不跨场景**，此点安全 |
| 缓存路径点位的坐标已 `transPos`（世界坐标），而 key 是 tile 坐标 | 【已确认】无害 | 只要 tile 尺寸不变 |

---

## 4. ★ 安全红线：本项目把移动完全交给客户端

### 4.1 证据链（三条独立证据）【已确认】

| # | 证据 | 位置 |
|---|---|---|
| 1 | `handler.move` 里 `var path = msg;` —— **客户端发来的整个 msg 就是路径数组**，直接喂给 `new Move({entity:player, path})` | `servers/area/handler/playerHandler.js` |
| 2 | `Map.prototype.verifyPath` **定义了但全项目 0 处调用**（脚本对 `app/**` 全文搜索） | `domain/map/map.js` |
| 3 | `Move.prototype.update` 只按 `speed` 推进，**`speed` 来自 `entity.walkSpeed`（服务端字段）**，但**路径本身可任意长、可穿墙** —— 因为路径点是客户端给的，服务端不做可达性校验 | `domain/action/move.js` |

**即：客户端可以上传 `[{自己位置},{墙对面位置}]`，服务端会照单执行并广播给别人（别人也会看到你穿墙）。速度看似由服务端控制（`walkSpeed`），但「路径任意」这一点已经足够作弊。**

### 4.2 JSTM 必须做的加固（按成本从低到高）

| 级别 | 措施 | 实现要点 |
|---|---|---|
| **L1 必做** | **路径校验**：对客户端上传的 path 调用等价于 `verifyPath` 的检查（每个点 `is_reachable` + 相邻点直线可达） | 直接移植 `verifyPath` 逻辑（约 20 行），并**对每次 move 都调用** |
| **L1 必做** | **起点一致性校验**：`path[0]` 与服务器记录的 `player.x/y` 的距离 ≤ 阈值（如 `tileW/2`） | 本项目在 `handler.move` 里发现不符时是「跟着客户端走」，JSTM 应**拒绝并纠正**（下发 `onStand` 强制回到服务端位置） |
| **L2 强烈建议** | **总位移/速度上限**：`sum(segment_length) / (now - last_move_time)` ≤ `walkSpeed × 容差`（如 1.3） | 防加速外挂 |
| **L2 强烈建议** | **路径长度上限**：点数 ≤ N、总长 ≤ `walkSpeed × 3s` | 防一次上传超长路径造成 A*/AOI 风暴 |
| **L2 强烈建议** | **移动请求限流**：每玩家每秒最多 K 次 `move`/`clMove` | 本项目**无限流**，恶意客户端可打爆主循环 |
| **L3 推荐** | **服务端主导模式**：客户端只发目标点（类似 `clMove` 的语义），**服务端 `findPath` 后下发路径**，客户端只做表现 | 最安全；代价是与 1.4.9 客户端协议可能不兼容（**需先确认客户端是否支持服务端下发路径驱动移动**）【待验证】 |
| **L3 推荐** | **位置回执/漂移校正**：服务端周期性下发权威位置，客户端超过阈值就拉回 | 私服兼容老客户端时通常需要 |

> ⚠️ **对 JSTM 的特别提醒：** JSTM 的上位目标是「兼容《绝世唐门》1.4.9 客户端」，**客户端协议很可能就是「上传整条路径」**（这类 2D 引擎普遍如此）。因此 **L3 的服务端主导模式可能不可行**，应把重点放在 **L1 + L2**：接受客户端路径，但**逐条校验 + 限速 + 限流 + 位置回执**。

---

## 5. 【未知】/【待验证】清单

| 问题 | 状态 |
|---|---|
| A* 的具体实现（启发函数、开放列表、是否支持对角、是否有权重支持） | **【未知】**（`pomelo-pathfinding` 未打包） |
| `pomelo-collection.priorityQueue` 的比较语义 | **【待验证】** |
| `compressPath1` 的 `j += 2` 是否是作者有意简化（原版 lordofpomelo 是否相同） | **【待验证】**（可对比 `game-server_backup/app/domain/action/move.js` 与上游 lordofpomelo；本次未做逐行 diff） |
| 大地图（`rectW × rectH` 数量级）下的 A* 实际耗时 | **【未知】**（无埋点、无压测） |
| 客户端如何计算并上传路径（是否有预测/本地 A*） | **【未知】**（`cocosjs/` 未审计） |
| `mapEntity*.json` 的 `collisions` 压缩格式的完整语义 | **【待验证】**（本次只从 `getWeightMap` 反推出「按 x 列，每项 `[startY, length]`」） |
| `process.cwd()` 依赖 | **【已确认】风险**：`mapPath = process.cwd()+"/config/map/..."` → **必须从 `game-server/` 目录启动**，否则地图加载失败。JSTM 应用「相对模块/配置根」的路径解析 |

---

## 6. ★ JSTM 寻路落地方案建议

### 6.1 推荐模块划分（Python）

```
map/
  map_data.py      # 加载 mapEntity*.json：collisions(列压缩) / birth / transport / mob / npc
  weight_map.py    # 建 rectW×rectH 权重网格；is_reachable / get_weight / for_all_reachable(4向)
  line_check.py    # check_line_path / test_line（采样法）
  astar.py         # 4 向 A*（自己实现，heapq 开放列表 + 曼哈顿启发）
  path_cache.py    # 起终点对的 LRU（正确的 LRU：OrderedDict 或 时间戳堆）
  compress.py      # compress_collinear / pull_string（标准射线拉直）
  finder.py        # find_path：直线快路径 → 缓存 → A* → 坐标转换 → 压缩
```

### 6.2 照搬的设计（【已确认】优点）

| # | 借鉴点 | 原因 |
|---|---|---|
| 1 | **世界坐标 + tile 网格双坐标体系** | 2D 端游标准 |
| 2 | **碰撞按列压缩为 `[startY, length]` 段** | 内存/构建成本极低 |
| 3 | **`for_all_reachable` 把权重一起回调给 A*** | A* 无需回查地图，解耦干净 |
| 4 | **「先直线快路径，再 A*」** | 大多数移动不触发 A* |
| 5 | **`compress_collinear` 去共线点** | 15 行显著减少路径点与后续 AOI 更新量 |
| 6 | **路径 LRU 缓存（起终点对）** | 追击/巡逻反复走同一段路时收益大（**记得把 `use_cache` 默认打开**） |
| 7 | **`singleton` 移动 Action** | 一个实体同时只有一个移动动作 |
| 8 | **按速度沿折线滑行、单 tick 可跨多节点** | 不依赖固定 tick，天然抗抖动 |
| 9 | **每 tick 同步 AOI** | 别人才能看到你移动 |
| 10 | **传送点数据驱动 + 来源反转查落点** | 双向传送不出错 |
| 11 | **巡逻路径 = 随机游走 + 闭环 + 回填起点** | 免手工路径点 |
| 12 | **出生点 = 矩形内随机 + 可达性重试（上限 10）** | 简单可靠 |

### 6.3 绝对不要照抄（【已确认】缺陷）

| # | 缺陷 | JSTM 的正确做法 |
|---|---|---|
| 1 | **信任客户端路径、`verifyPath` 从不调用** | 每次 move 都校验 + 起点一致性 + 限速 + 限流 + 位置回执 |
| 2 | **`checkPoint` 里跑完整 `findPath`** | 改用「直线可达」或「距离阈值内随机取点」 |
| 3 | **`useCache` 默认 false** | 默认开启（配合合理的 limit 与正确的 LRU） |
| 4 | **`PathCache` 的 LRU 实现有崩溃 bug + 比较语义可疑** | 用 `OrderedDict` 或 `heapq` + 惰性删除，写单元测试 |
| 5 | **`_testLine` 用 `tileW` 算 y 的 tile 行** | 分别用 `tileW`/`tileH` |
| 6 | **`isReachable` 用 `weight === 1`** | 用 `weight < INF`，为减速地形留空间 |
| 7 | **`compressPath1` 的 `j += 2` 近似拉直** | 标准射线拉直（对每个点向右找最远可直达点） |
| 8 | **`process.cwd()` 拼地图路径** | 基于配置根/包路径解析 |
| 9 | **无寻路性能埋点** | 记录 A* 调用次数/耗时 P95/缓存命中率，作为压测基线 |
| 10 | **寻路在主线程同步执行** | 若单进程 Python 用 asyncio，需给「大批量寻路」设预算（每 tick 最多 N 次 A*，其余入队） |
