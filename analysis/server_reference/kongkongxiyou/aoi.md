# AOI 算法与实现（空空西游 / pomelo-aoi）

> **本文件是整个审计中「信息最不完整」但「对 JSTM 价值最高」的一节。**
> 结论标记：**【已确认】**（ZIP 内源码）/ **【待验证】**（外部官方资料）/ **【未知】**（ZIP 内无源码且未验证）

---

## 0. 最重要的前提：AOI 内核不在参考项目里

| 事实 | 证据 | 置信度 |
|---|---|---|
| 项目通过 `var aoiManager = require('pomelo-aoi')` 使用 AOI | `app/domain/area/area.js` 第 13 行 | 【已确认】 |
| `pomelo-aoi` **作为 npm 依赖声明**，未随 ZIP 打包 | `game-server/package.json`: `"pomelo-aoi": ">=0.3.4"` | 【已确认】 |
| 全 ZIP 22486 个文件中，路径/文件名含 `pomelo-aoi` 的 **0 个**；对 `pomelo/lib/**` 全文搜索 `aoi`（不区分大小写）**0 命中** | 脚本扫描结果 | 【已确认】 |
| `pomelo/node_modules/` 里也**没有** pomelo-aoi（该依赖在 `game-server/node_modules`，而 game-server 的 node_modules 未打包） | ZIP 文件清单 | 【已确认】 |
| `game-server_backup/` 里的 `aoiEventManager.js`（9246 B）与主目录（9257 B）几乎相同，**同样只有调用没有算法** | 体积与抽样比对 | 【已确认】 |

> **所以：本报告能给出的「已经确认」内容是「本项目如何使用 AOI」；「塔式 AOI 内部如何计算」在 ZIP 内【未知】，只能借助外部官方资料做【待验证】的说明，绝不做代码级断言。**
> JSTM 如果要落地 AOI，**必须自己实现算法**，不能指望从参考项目里抄到。

---

## 1. 【待验证】外部资料：pomelo-aoi 是「塔式（tower）AOI」

来源：官方仓库 README（[NetEase/pomelo-aoi](https://github.com/NetEase/pomelo-aoi)、[README.md](https://github.com/NetEase/pomelo-aoi/blob/master/README.md)），以及 [Pomelo 作者谢成超的演讲材料](http://velocity.oreilly.com.cn/2012/ppts/xiechengchao.pdf)。以下是**外部资料的转述**，非 ZIP 内代码：

> "The aoi module include a set of aoi interface, and **an implementation of tower aoi algorithm**."
> 配置形如 `config = { map:{width:3200,height:2400}, tower:{width:300,height:300} }`，`aoiManager.getService(config)`。
> 接口：`addObject(obj,pos)` / `removeObject(obj,pos)` / `updateObject(obj,oldPos,newPos)` / `addWatcher(watcher,pos,range)` / `removeWatcher(watcher,pos,range)` / `updateWatcher(watcher,oldPos,newPos,oldRange,newRange)`。
> 事件：**对象**产生 `'add'`、`'remove'`、`'update'`；**观察者**产生 `'updateWatcher'`。
> "The event of tower aoi are: 'add', 'remove', 'update' for aoi object, and 'updateWatcher' for watcher."

**关键交叉验证【已确认】：** 外部 README 声明的 4 个事件名（`add` / `remove` / `update` / `updateWatcher`）与 `aoiEventManager.js` 里 `aoi.on('add'|'remove'|'update'|'updateWatcher', ...)` **完全一致** → 说明参考项目用的确实是这个 tower AOI 实现，且**用的是「原始事件接口」，没有封装**。

**由此可推断（【待验证】，未见实现）：**
1. 地图被切成 `ceil(width/towerW) × ceil(height/towerH)` 的**塔格**；本项目 `width/height` 来自 `config/data/area.json`，`towerW=towerH=300`。
2. `addObject/updateObject` 维护「每个塔里有哪些物体」的**倒排索引**（`tower → objects`）。
3. `addWatcher(watcher, pos, range)` 维护「每个塔里有哪些观察者」+ 「一个观察者覆盖了哪些塔」（由 `range` 推出的塔矩形）。
4. `getWatchers(pos, types)`：取 `pos` 所在塔里的 watcher 集合（**注意：这是「同塔」而不是「半径内」—— 塔格粒度带来的近似**）。
5. `getIdsByPos(pos, range)` / `getIdsByRange(pos, range, types)`：按 `range` 覆盖的塔矩形聚合物体 id。
6. 「九宫格」式优化是塔 AOI 的常见做法（只查相邻塔），**但本项目传的 `range` 是实体自身的 `entity.range`，不是塔尺寸**，因此**具体是「同塔」还是「半径过滤后处理」【未知】**。

> ⚠️ **不可断言**：塔 AOI 的判定到底是「格子级近似」还是「格子粗筛 + 精确距离过滤」，README 未说明，ZIP 内无从验证。JSTM 自研时应**明确选择「格子粗筛 + 精确距离过滤」**，语义更可控。

---

## 2. 【已确认】本项目如何接入 AOI（调用契约全集）

### 2.1 AOI 实例的创建与参数

```js
// app/domain/area/area.js  （Area 构造器，即「世界」根对象）
var aoiManager = require('pomelo-aoi');
...
var opts = map.areaConfigData;        // 来自 config/data/area.json
opts.towerWidth  = 300;               // ★ 硬编码，覆盖任何配置
opts.towerHeight = 300;               // ★ 硬编码
this.aoi = aoiManager.getService(opts);
...
// app/domain/area/area.js  start()
aoiEventManager.addEvent(this, this.aoi.aoi);   // ★ 注意是 this.aoi.aoi（再取一层）
```

| 观察 | 意义 |
|---|---|
| **每个 Area 一个 AOI 实例**（不是全服一个） | 与官方 README「each area use the aoi module should use it's own aoi instance」一致，**副本之间视野隔离** |
| `towerWidth/towerHeight = 300` **硬编码** | 全部 12 个场景共用一个粒度；若地图宽 3200，则 x 方向 11 个塔；若地图宽 8000，则 27 个塔（塔格变大不影响正确性，只影响精度/性能曲线） |
| `aoiEventManager.addEvent(this, this.aoi.aoi)` 取的是 `service.aoi` | 说明 `getService()` 返回的是**包装层**，真正的 aoi 对象（EventEmitter）在 `.aoi` 字段上；`getService` 返回对象上另有 `addObject/addWatcher/...` 代理方法。**JSTM 只需一个类即可，无需这种双层结构** |

### 2.2 全部 AOI 调用点（脚本统计：ZIP 内 `app/**` 共 37 处）

| 调用 | 次数 | 位置 | 语义 |
|---|---|---|---|
| `aoi.addWatcher({id,type}, entity, range)` | 8 | `area.addEntity`（PLAYER、MOB 各一次）等 | 注册观察者，`range` = 实体视野半径 |
| `aoi.removeWatcher({id,type}, entity, range+1)` | 8 | `area.removeEntity` | 注销观察者，**半径刻意 +1** |
| `aoi.updateWatcher({id,type}, oldPos, newPos, range, range)` | 10 | `action/move.js#update`、`handler.move`、`handler.clMove` | 观察者移动后重算视野 |
| `aoi.addObject({id,type}, entity)` | — | `area.addEntity` 末尾（**所有类型统一**） | 注册被观察物体 |
| `aoi.removeObject({id,type}, entity)` | — | `area.removeEntity` 末尾 | 注销 |
| `aoi.updateObject({id,type}, oldPos, newPos)` | — | `action/move.js#update`、`handler.move`、`handler.clMove` | 物体移动 |
| `aoi.getWatchers(pos, types)` | 3 | `timer.getWatcherUids`、`timer.getWatchers` | 查「谁在 pos 附近」→ 用于推送 |
| `aoi.getIdsByPos(pos, range)` | 2 | `area.getAreaInfo`、`area.getAreaInfoStrip` | 查「pos 附近有什么」→ 用于进场快照 |
| `aoi.getIdsByRange(pos, range, types)` | 2 | `area.getEntitiesByPos`、`aoiEventManager.onMobAdd` | 按类型+范围查 id |

**注意《本项目使用的实体类型枚举》**（`consts.EntityType`）：`PLAYER:1, MOB:2, NPC:3, EQUIPMENT:4, ITEM:5, BAG:6`。**只有 PLAYER 和 MOB 注册为 watcher；ITEM/EQUIPMENT 只注册为 object（能被看见但不能感知）；NPC 完全不进 AOI。**

### 2.3 双注册模型（JSTM 必须理解）

```
                   ┌──────────── addWatcher(watcher, pos, range) ────────────┐
   实体进入场景 ──▶ │  PLAYER ✅   MOB ✅   NPC ❌   ITEM ❌   EQUIPMENT ❌    │
                   └────────────────────────────────────────────────────────┘
                   ┌──────────── addObject(obj, pos) ───────────────────────┐
   实体进入场景 ──▶ │  PLAYER ✅   MOB ✅   NPC ❌   ITEM ✅   EQUIPMENT ✅    │
                   └────────────────────────────────────────────────────────┘
```

- **watcher** = 有视野的实体 → 参与 `getWatchers`（AOI 驱动的事件推送对象）。
- **object** = 可被看见的实体 → 参与 `getIdsByPos/getIdsByRange`（快照/范围查询对象）。
- 玩家与怪物**两者都注册**；物品只作为被观察对象；NPC 走「进场全量下发」（`getAreaInfoStrip` 里单独把 `this.npcs` 全塞进去）。

---

## 3. 【已确认】AOI 事件 → 客户端消息 的翻译层（`domain/aoi/aoiEventManager.js`）

### 3.1 事件处理器总表

| AOI 事件 | 分派 | 处理函数 | 工作机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|---|---|
| `add` | `EntityType.PLAYER` | `onPlayerAdd(params)` | `params = {watchers, id}`；从 `watchers[PLAYER]` 里捞出其他玩家 → 收集 `{uid,sid}`（`sessionData`）→ `onAddEntity(uids, player)`；`watchers[MOB]` 里的怪：`isActiveAttack` 则 `mob.onPlayerCome(entityId)`（**主动怪索敌由 AOI 事件驱动，不是 AI 轮询**）；`area.getEntity` 取不到的 watcher 直接 `delete playerWatchers[id]`（**顺手清理脏数据**） | ✅ **强适合** | 「物进视野 → 推 onAddEntities」是 AOI 的唯一产出；**「顺手 delete 失效 watcher」是必备的自愈机制** |
| `add` | `EntityType.MOB` | `onMobAdd(params)` | 对 `watchers[PLAYER]` 推 `onAddEntities(mob)`；再加一段：`mob.isActiveAttack` 时反向 `getIdsByRange(mob, mob.range, [PLAYER])` 主动查找玩家并 `onPlayerCome`（**覆盖「怪先在那里、玩家后进来」和「怪刷新在玩家旁边」两种情形**） | ✅ 强适合 | **双向感知**：既由 AOI 事件触发，也允许主动查询兜底 |
| `add` | `EntityType.ITEM` | `onItemAdd(params)` | 同 PLAYER 分支的推送部分 | ✅ | 掉落物同步 |
| `remove` | PLAYER | `onPlayerRemove(params)` | 遍历 `watchers[类型]`，取 `playerWatchers` → 收集 `{uid,sid}` → `onRemoveEntity(uids, entityId)`；**跳过自己**（`entityId !== watcher.entityId`） | ✅ 强适合 | 注意 **MOB 的 remove 分支在 switch 里被注释掉了** → 怪物死亡消失的「别人看得见吗」依赖 `area.tick()` 里对 items 的 `channel.pushMessage('onRemoveEntities')` 兜底【已确认，属于覆盖不全】 |
| `update` | PLAYER / MOB | `onObjectUpdate(params)` | **核心差量算法**（见下） | ✅ **强适合** | 塔 AOI 最关键的实现技巧 |
| `updateWatcher` | PLAYER | `onPlayerUpdate(params)` | `params = {removeObjs, addObjs, addTowers}`；`removeObjs.length > 0` → 删掉 `"length"` 字段后推 `onRemoveEntities(removeObjs)`；`addObjs` 逐个查 `area.entities[entityId]`，**跳过自己**，按 type 分组 `entity.strip()` 后推 `onAddEntities`；**查不到的 id 会去 `params.addTowers[j].removeById(id)` 尝试清理（脏数据回写）** | ✅ **强适合** | **「观察者移动 → 只推增删差集」是这个 AOI 最省流量的设计**；`removeById` 回写尤其值得学 |

### 3.2 差量算法：`onObjectUpdate`（对象移动时的双向差集）【已确认】

```js
function onObjectUpdate(params) {          // params = {oldWatchers, newWatchers, id}
  var removeWatchers = {}, addWatchers = {};

  // ① old - new  → 要推 onRemoveEntities 的观察者
  for (type in oldWatchers) {
    if (!newWatchers[type]) { removeWatchers[type] = oldWatchers[type]; continue; }
    w1 = oldWatchers[type]; w2 = newWatchers[type];
    removeWatchers[type] = {};
    for (id in w1) if (!w2[id]) removeWatchers[type][id] = w1[id];   // 差集
  }
  // ② new - old  → 要推 onAddEntities 的观察者
  for (type in newWatchers) {
    if (!oldWatchers[type]) { addWatchers[type] = newWatchers[type]; continue; }
    w1 = oldWatchers[type]; w2 = newWatchers[type];
    addWatchers[type] = {};
    for (id in w2) if (!w1[id]) addWatchers[type][id] = w2[id];      // 差集
  }
  // ③ 复用 add/remove 处理函数
  switch (params.type) {
    case PLAYER: onPlayerAdd({area, id, watchers: addWatchers});
                 onPlayerRemove({area, id, watchers: removeWatchers}); break;
    case MOB:    onMobAdd({...}); onMobRemove({...}); break;
  }
}
```

**这就是「AOI 差量同步」的完整实现，不到 40 行。JSTM 可以直接照这个结构写（Python dict 差集更简单）。**

> 设计要点：
> 1. AOI 库只负责算出 `oldWatchers` / `newWatchers` 两个「谁看得见我」的集合；
> 2. **业务层自己做差集** → 转成 `onAddEntities` / `onRemoveEntities` 两条推送；
> 3. **不做全量重推**，网络开销与「视野变化量」成正比，与视野内实体总数无关。

### 3.3 「观察者视角」与「物体视角」的分工（很容易搞混，务必分清）

| 变化 | AOI 事件 | 谁收到 | 收到什么 |
|---|---|---|---|
| **我走进你的视野**（我移动） | `updateWatcher` | **我** | `onAddEntities`（我该看见的新实体）/ `onRemoveEntities`（我该忘记的实体） |
| **我移动到你的视野里**（我移动） | `update`（我是 object） | **你** | `onAddEntities`（你看见了我）/ `onRemoveEntities`（你看不见我了） |
| **我出生/进场** | `add` | 视野内其他人 | `onAddEntities` |
| **我离开/死亡** | `remove` | 视野内其他人 | `onRemoveEntities`（**MOB 的这条链路被注释掉了**） |

**结论【已确认】：`updateWatcher` 服务「自己的视野」，`update` 服务「别人的视野」。移动时必须两个都调，本项目在 `move.js#update` 里正是这么做的。**

---

## 4. 【已确认】AOI 与移动的耦合（最关键的运行时路径）

```js
// app/domain/action/move.js  —— Move.prototype.update(currentTime)
//  每 100ms 被 actionManager.update() 调一次
this.pos = pos;  this.index = index;
entity.x = Math.floor(pos.x);
entity.y = Math.floor(pos.y);

// Update the aoi module
var watcher = {id : entity.entityId, type : entity.type};
area.timer.updateObject(watcher, oldPos, pos);                        // ① 我是 object：通知「能看见我的人」
area.timer.updateWatcher(watcher, oldPos, pos, entity.range, entity.range); // ② 我是 watcher：重算「我能看见谁」
```

| 步骤 | 作用 | 产生的推送 |
|---|---|---|
| `updateObject` | 把「我」从旧塔挪到新塔 | 对**双向差集**里的观察者推 `onAddEntities`/`onRemoveEntities`（**别人看我**） |
| `updateWatcher` | 把「我的视野矩形」从旧塔集挪到新塔集 | 对**我自己**推 `onAddEntities`/`onRemoveEntities`（**我看别人**） |

**性能含义【已确认】：玩家每 100ms 移动一次 → 每 tick 两次 AOI 更新 + 最多 2 次群推。**
- 塔格（300×300）+ 角色移动速度决定「过塔频率」：若速度为 300 px/s，则**约 1 秒过一次塔**，差集为空 → 零推送。这是塔 AOI 省流量的根本原因。
- 若塔格过小（如 64×64），过塔频繁 → 差集计算与查询次数暴涨；若过大（如 1000×1000），单塔 watcher 过多 → 每次移动的差集计算成本高。**300 是 Pomelo 官方 demo 的经验值。**
- 本项目作者**没有对 AOI 做任何性能埋点或降频**（没有「N 帧才更新一次 AOI」的节流）—— `move.js` 里有一段 `// if (this.tickNumber % 20 === 0) entity.save();` 说明作者曾考虑过节流但**只用在存盘上，没用在 AOI 上**【已确认】。

---

## 5. 【已确认】AOI 群推出口：`getWatcherUids` → `channelService`

```js
// app/domain/messageService.js
exp.pushMessageByAOI = function (area, route, msg, pos, ignoreList) {
  var uids = area.timer.getWatcherUids(pos, [EntityType.PLAYER], ignoreList);
  if (uids.length > 0) exp.pushMessageByUids(uids, route, msg);
};
exp.pushMessageByUids = function (uids, route, msg) {
  if (!channelService) channelService = pomelo.app.get('channelService');
  channelService.pushMessageByUids(route, msg, uids, errHandler);
};
function errHandler(err, fails) {                  // ⚠️ 意图是「惰性掉线检测」，但实际是空操作
  for (var i in fails) { pomelo.app.areaManager.removePlayerByUid(fails[i]); }
  // fails 里装的是 uid（channelService 的 groups[sid]=[uid,...]）
  // 而 removePlayerByUid → getCanUsedPlayer → this.players[uid]，players{} 是按 playerId 索引的
  // ⇒ uid ≠ playerId ⇒ 必然查不到 ⇒ 静默 return。详见 pomelo.md 第 4.2 节。
}

// app/domain/area/timer.js
Timer.prototype.getWatcherUids = function (pos, types, ignoreList) {
  var watchers = area.aoi.getWatchers(pos, types);
  var result = [];
  if (!!watchers && !!watchers[EntityType.PLAYER]) {
    for (var entityId in watchers[EntityType.PLAYER]) {
      var player = area.getEntity(entityId);
      if (!!player && !!player.userId && (!ignoreList || !ignoreList[player.userId]))
        result.push({uid: player.userId, sid: player.serverId});   // ★ 转成网络投递地址
    }
  }
  return result;
};
```

**链路：`pos` → AOI 塔查询 → `entityId` 列表 → `area.entities` 取实体 → `{uid, sid}` → channelService 按 sid 分组 RPC 到各 connector → socket。**

**这里是 AOI 与网络层的唯一接缝**，也是 JSTM 最该照抄的抽象：**AOI 只产出 entityId / 网络地址，绝不碰 socket**。

### 5.1 AOI 相关的推送路由（`config/dictionary.json` 里的协议名）

| route | 触发者 | payload |
|---|---|---|
| `onAddEntities` | `onPlayerAdd` / `onMobAdd` / `onItemAdd` / `onPlayerUpdate` | `{ type: [entity.strip(), ...] }`（**按 EntityType 分组**） |
| `onRemoveEntities` | `onPlayerRemove` / `onPlayerUpdate` / `area.tick`(item died) | `{ entities: [entityId, ...] }` |
| `onMove` | `Character.move`（AI/巡逻）/ `handler.move` | `{entityId, path:[{x,y},...]}`（玩家版另带 `areaId`） |
| `onClMove` | `handler.clMove` | `{entityId, areaId, x, y}`（**忽略发送者自己**） |
| `onStand` | `Character.stand` | `{entityId, x, y}` |
| `onTeamChange` | `playerRemote.leaveTeam` | `{playerId, teamId}` |
| `onUserLeave` | `area.onUserLeave` | `{playerId}` |

`strip()` 家族（`entity/entity.js` / `character.js` / `player.js#strip / playerStrip / upgradeStrip` / `mob.js#strip / npc.js#strip`）负责**把内存对象裁成客户端可用的最小字段集**——这是「同步宽表」问题的答案：**不同实体类型有不同 strip，且玩家有 `strip`（给别人看）与 `playerStrip`（给自己看）两份**【已确认】。

---

## 6. 【未知】与【待验证】清单（诚实边界）

| 问题 | 状态 | 说明 |
|---|---|---|
| 塔 AOI 的塔内数据结构（数组/字典/链表） | **【未知】** | ZIP 内无 pomelo-aoi 源码 |
| `getWatchers(pos, types)` 是「同塔集合」还是「半径内精确过滤」 | **【未知】** | 官方 README 未说明；两者语义差异巨大（决定是否漏同步/多同步） |
| `update()` 事件里 `oldWatchers`/`newWatchers` 的粒度（是塔集合还是实体集合） | **【未知】** | 从 `aoiEventManager` 的用法看，**是「按类型的 entityId 字典」**（因为代码直接 `for (id in playerWatchers)` 并拿 `id` 去 `area.getEntity`）——这一点由**使用方式反推**，置信度较高但仍是推断 |
| `range` 的单位（像素 or 塔数） | **【待验证】** | 本项目传 `entity.range`（实体视野半径），且 `removeWatcher` 用 `range+1` 做包含修正 → **强烈提示是像素半径**，但内部如何换算成塔格【未知】 |
| AOI 在大批量实体下的性能 | **【未知】** | 无压测、无埋点；作者自述「未经历上线考验」 |
| `aoi.aoi` 双层结构的由来 | **【待验证】** | 推测 `getService` 返回带事件代理的 wrapper，真实实现在 `.aoi` |
| `params.addTowers` / `tower.removeById(id)` 的数据结构 | **【未知】** | 仅在 `onPlayerUpdate` 里出现，是脏数据回写通道 |
| `getIdsByPos` 与 `getIdsByRange` 的区别 | **【待验证】** | 前者无 `types` 参数（返回全部），后者按类型过滤 |

---

## 7. ★ JSTM 落地方案建议（基于以上全部证据）

### 7.1 推荐架构（Python 单进程）

```
Scene/Map
  └─ TowerAOI (每个 Area 一个实例)
       ├─ tower_w, tower_h  (配置化，默认 300，但要按地图尺寸自适应)
       ├─ towers: dict[(tx,ty)] -> set_of_object_ids
       ├─ watchers: dict[(tx,ty)] -> set_of_watcher_ids
       ├─ objects: dict[obj_id] -> (x, y)
       ├─ watcher_meta: dict[wid] -> (x, y, range, covered_towers:set)
       └─ 事件回调表: on_add / on_remove / on_update / on_update_watcher

messageService.push_by_aoi(area, route, msg, pos, ignore=None)
  uids = area.timer.get_watcher_uids(pos, [PLAYER], ignore)
  channel_push_by_uids(uids, route, msg, on_fail=lambda f: area_manager.remove_player_by_uid(f))
```

### 7.2 从本项目**照搬**的部分（设计，非代码）

| # | 借鉴点 | 出处 |
|---|---|---|
| 1 | **每个 Area（含副本）独立 AOI 实例** | `area.js` |
| 2 | **watcher（有视野）+ object（被看见）双注册模型** | `area.addEntity/removeEntity` |
| 3 | **4 个事件的接口契约**（`add` / `remove` / `update` / `update_watcher`） | `aoiEventManager.js` |
| 4 | **`update` 用 old/new watchers 双向差集** → 只推增删 | `onObjectUpdate` |
| 5 | **观察者移动单独走 `updateWatcher`**（自己视野变化） | `move.js#update` 双调用 |
| 6 | **`getWatcherUids(pos, types, ignoreList)` 把 AOI 结果翻译成投递地址** | `timer.js` |
| 7 | **推送失败即从场景移除玩家**（❌ 只借鉴**思想**：参考实现 `messageService.errHandler` 因 uid/playerId 错配**是空操作**，JSTM 必须自己写对，见 `pomelo.md` 4.2） | `messageService.errHandler` |
| 8 | **处理事件时顺手 `delete` 失效 watcher**（自愈） | `onPlayerAdd/onMobAdd/onPlayerUpdate` |
| 9 | **主动怪索敌由 AOI `add` 事件驱动**，另用 `getIdsByRange` 兜底 | `onMobAdd` |
| 10 | **NPC 不进 AOI、进场全量下发** | `getAreaInfoStrip` |
| 11 | **`strip()` 分层**：给自己看 vs 给别人看 | `player.playerStrip` vs `strip` |
| 12 | **`onRemoveEntities` 用 id 数组、`onAddEntities` 用按类型分组对象** | `aoiEventManager` |

### 7.3 本项目**不能照抄**、JSTM 必须自研/加强的部分

| 必须改进 | 原因 |
|---|---|
| **必须真正实现塔内/半径的精确判定** | 参考项目内核【未知】，无法复制；且「同塔即视野」会导致角落漏同步 |
| **必须给 towers 的几何计算加配置** | 参考项目硬编码 300，JSTM 应按地图尺寸/在线密度自适应 |
| **必须补 `range` 的语义定义与单位** | 参考项目把 `entity.range` 直传，语义未文档化 |
| **必须给 AOI 更新加节流/降频选项** | 参考项目 100ms 无条件双次更新，无降频开关 |
| **必须补 MOB 的 `remove` 分支** | 参考项目里被注释掉，怪物尸体同步靠别的兜底 |
| **必须加 AOI 埋点**（塔数、单塔实体数、差集大小、群推人数分布） | 参考项目零埋点，无法调优 |
| **不要用「双层 `service.aoi`」结构** | 无必要，一个类即可 |
| **`removeWatcher` 的 `range+1` 语义要显式化** | 参考项目靠魔法数字修正边界，JSTM 应用「按覆盖塔集合精确移除」 |
