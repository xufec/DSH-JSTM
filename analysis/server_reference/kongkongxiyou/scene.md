# Scene 玩家管理 与 AOI 接入（场景层审计）

> 参照物：`kongkongxiyou-master/lordofpomelo/game-server/app/domain/**` 与 `app/servers/area/**`
> 结论标记：**【已确认】** / **【待验证】** / **【未知】**

---

## 1. 场景层的类层次

```
app.areaManager                              ← 一台 area 进程的「进程级注册表」
│   （app.js 按 curServer 三选一注入：AreaManager | InstancePool | Scene）
├─ AreaManager（大区服，本项目实际使用：area-server 带 "areas":"[...]"）
│    ├─ this.scenes{areaId: Scene}           ← 用 config/data/area.json 里的 12 个场景预建
│    ├─ this.players{playerId: Player}       ← 在线玩家对象池（跨场景）
│    ├─ this.playerIds[]                     ← 插入顺序数组
│    ├─ this.playerCaches{playerId: Player}  ← 刚下线的玩家对象（60s 后 clear）
│    ├─ this.playerIdCaches[]
│    ├─ this.instances{instanceId: {instanceId, playerIds{}}}
│    ├─ this.playerIdToInstanceId{}
│    ├─ this.requestList{playerId: playerId} ← 防并发重复查库的「占位锁」
│    └─ this.instancePool : InstancePool
├─ Scene                                    ← 极薄的包装：this.area = new Area(map)
│    └─ getPlayerInArea() / removePlayerByUid()
├─ Instance                                 ← 副本：this.area = new Area(map, instanceId)；lifeTime=300000
│    └─ start/close/getArea/isAlive/removePlayerByUid   （isAlive: 空场超过 lifeTime → 回收）
├─ InstancePool                             ← 副本池：instances{}；setInterval(check, 60000)
│    └─ create/remove/removePlayerByUid/getPlayerInArea/onClose
└─ Area  ← 真正的世界（domain/area/area.js，注意类名仍叫 Instance）
     ├─ map : Map                          ← 碰撞图 + 寻路器 + 刷怪区数据
     ├─ areaId / type / areaKind           ← 来自 map.areaConfigData
     ├─ players{playerId: entityId}
     ├─ users{userId: playerId}            ← 反查表（按账号）
     ├─ entities{entityId: Entity}
     ├─ items{entityId: entityId}
     ├─ npcs{kindId: NPC}
     ├─ zones{zoneId: MobZone|ItemZone}
     ├─ channel : pomelo Channel           ← 场景频道（广播用）
     ├─ aoi                                  ← pomelo-aoi 实例（tower 300×300）
     ├─ aiManager / patrolManager / actionManager
     ├─ timer : Timer                       ← 100ms 主循环
     ├─ areaLogic                           ← 按 areaKind 选择的策略对象（工厂）
     └─ 运行态：playerNum / emptyTime / nextBossGenTime / bossEntityId
```

**`areaLogic` 是策略模式**（`domain/area/areaLogic.js`，33 KB，最大领域文件）【已确认】：

| 策略类 | 触发条件（`createAreaLogic`） | 覆写的行为 |
|---|---|---|
| `AreaLogic`（基类） | — | `attack / multiAttack / killReward / diedInArea / reviveInArea / finishFight` |
| `AreaNormalLogic` | 普通场景 | 仅 `startLogic` |
| `AreaDomainLogic` | 城战/领地场景 | `initDomainArea / update1 / update3 / reviveInArea / enterArea / pushDomainInfo / updateDomainBattle / onDomainBattle / onUpdateDomain` |
| `AreaFightLogic` | 竞技场副本 | `enterArea / exitArea / diedInArea / startLogic / finishFight(loserId)` |
| `AreaMyBossLogic` | 个人 BOSS | `enterArea / exitArea / reviveInArea / startLogic` |
| `AreaWorldBossLogic` | 世界 BOSS | `enterArea / exitArea / reviveInArea / startLogic` |

---

## 2. 逐文件表格（Scene 玩家管理）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `lordofpomelo/game-server/app.js` | `app.configure(...,'area',fn)` | 按 `curServer` 三选一：有 `areas` → `new AreaManager()` + `areaManager.initScenes(server.areas)` + `new InstancePool()`；有 `instance` → 只用 InstancePool；否则 → 单 `Scene`。统一挂 `app.areaManager` | ✅ **强适合** | **「一台逻辑服可以托管 N 个场景」的判定逻辑**可直接照搬：JSTM 单进程就是一个 `AreaManager` 管全部场景 |
| `.../domain/area/areaManager.js` | `AreaManager` 构造器 | 初始化 8 个容器（见上） | ✅ 强适合 | 数据结构清晰，Python 直接对应 dict/list |
| 同上 | `initScenes(areaIds)` | 遍历配置里的 areaId → `dataApi.area.findById` → `new Scene(areaData)` | ✅ | 配置驱动建场景 |
| 同上 | `getCanUsedPlayer(playerId)` | **两级缓存读**：先查 `players{}`，未中查 `playerCaches{}`，命中则**提升回 `players{}` 并删缓存** | ✅ **强适合** | 「下线缓存 60s 内重登复用对象」避免重复查库+重建，**私服高频重连场景收益明显** |
| 同上 | `getPlayerWithPlayerIdCb(playerId, cb)` | 先查缓存/在线；否则 `requestList[playerId]` **占位防并发**（已存在则回调 `'waiting'` 错误）→ `userDao.getPlayerAllInfo` → `addPlayer` | ⚠️ 部分 | 防并发思路对，但**用字符串错误码 `'waiting'` 通知调用方，调用方 playerFilter 把它当致命错误 `next(new Error(...))`** → **高并发首登会偶发登录失败**。JSTM 应用 asyncio 锁 + 等待而非拒绝 |
| 同上 | `addPlayer / removePlayer / addPlayerCaches / clearPlayerCaches` | `addPlayerCaches` 记录 `recycleTime = now+60000` 并立刻调 `clearPlayerCaches()`；**`clearPlayerCaches` 一次性把队列里所有缓存对象的字段全部 `delete` 掉** | ❌ 不适合 | **「边写边全清」是明显 bug**：刚 put 进去的缓存会被立刻清空，等于缓存形同虚设（且把对象掏空为 `{}`，若外部仍持有引用会拿到空对象）。JSTM 应做**带过期时间的真 LRU** |
| 同上 | `getAreaWithPlayer(player)` | **优先按 `scenes[player.areaId]` 找，找不到再按 `player.instanceId` 找副本**；都失败则把 `player.areaId` 强制改回 `1001` 并重试 | ⚠️ 部分 | 兜底回主城避免卡死是好的；但**静默改写玩家数据**会让问题被掩盖。JSTM 应记警告+落库 |
| 同上 | `getPlayerInArea(instanceId, playerId)` | `player.instanceId ? instancePool.getPlayerInArea : scenes[player.areaId].getPlayerInArea()` | ✅ | 注意**参数 `instanceId` 实际被忽略**，真实依据是 player 自己身上的 `instanceId` |
| 同上 | `changeArea(args)` | `dataApi.area.findById(targetId).type` → `<=SCENE` 走 `gotoScene`，`==TEAM_INSTANCE` 走 `gotoTeamInstance`，否则 `gotoInstance`；返回数字 code（111/112/200） | ✅ 强适合 | **「目标区域类型决定迁移策略」的单一分派点**非常清晰 |
| 同上 | `gotoScene(args)` | `area.exitArea(player)` → `areaService.getInitPoint(targetId, curAreaId, transportId)` 算落点（支持传送点双向反转：`transport.targetArea === curAreaId` 时偏移 `x+60,y-30`）→ 改 `player.areaId/instanceId=0/x/y` → `player.save()` | ✅ 强适合 | **「传送点带来源方向反查落点」**是细节亮点，传奇类地图必备，JSTM 直接借鉴 |
| 同上 | `gotoInstance(args)` | 按 `areaKind` 生成 instanceId：`FIGHT_AREA→"fight_"+argId`；`MY_BOSS_AREA→"my_"+playerId+targetId%10`；`WORLD_BOSS_AREA→"boss"`；其他→`"sin_"+playerId`；最终 `instanceId = targetId + '_' + argId` | ✅ **强适合** | **instanceId 命名规则就是「副本共享域」的定义**：个人 BOSS 一人一实例、世界 BOSS 全服一实例、队伍副本按 teamId 共享。JSTM 应原样采用这套命名约定 |
| 同上 | `removePlayerByUid / removeInstance / createInstance` | 场景删 / 副本删 / 副本建 + `playerIdToInstanceId` 双向映射维护 | ✅ | 注意 `createInstance` 里 `var instance = this.instances[instanceId]` 后立刻 `this.instancePool.create(...)`，新对象覆盖了 `instance`，**存在逻辑异味** |
| `.../domain/area/scene.js` | `Scene` / `init` / `getPlayerInArea` / `removePlayerByUid` / `toString` | `init` 取 `areaService.getMap(opts.id)`（**全服共享同一 Map 实例**），没有则 `new Map(opts)`；`this.area = new Area(map)`；`this.id = this.area.areaId` | ✅ **强适合** | **Map 对象全服共享、Area 各自持有引用** → 内存里碰撞图只存一份，这是关键优化，JSTM 必须照做 |
| `.../domain/area/instance.js` | `Instance` / `start` / `close` / `isAlive` | `lifeTime = 300000`（5 分钟）；`isAlive()`：`area.isEmpty() && (now - area.emptyTime) > lifeTime` → false | ✅ 强适合 | **「空场 5 分钟回收」**的策略直接可用 |
| `.../domain/area/instancePool.js` | `init` / `check` / `create` / `remove` / `getPlayerInArea` | `setInterval(check, 60000)`；`check` 遍历找 `!isAlive()` 的 → **RPC `manager.instanceRemote.remove`** → `onClose` 里 `instance.close()` + `delete` | ⚠️ 部分 | 回收思路适合；**但「本进程的实例对象要跨进程问 manager 才能删」是纯分布式开销**，JSTM 应直接本地删 |
| `.../domain/area/timer.js` | `Timer` / `run` / `tick` / `getWatcherUids` / `updateObject` / `updateWatcher` | `setInterval(tick,100)`；tick 内 `area.tick()`；`timeCount%10===0` → `update1()`（1s）；`timeCount>30` → 归零 + `update3()`（3s） | ✅ **强适合** | **「一个 100ms 主循环 + 分频子逻辑」是单进程服务器最优解**，JSTM 必须采用 |
| 同上 | `enterAI(entityId)` / `patrol(entityId)` | 二者**互斥**：`enterAI` = 删巡逻 + `abortAction(MOVE,id)` + `aiManager.addCharacters`；`patrol` = 删 AI + 用 `entity.path` 建巡逻 | ✅ 强适合 | AI/巡逻互斥是「怪物状态机」的简洁表达 |
| 同上 | `getWatcherUids(pos, types, ignoreList)` | `aoi.getWatchers(pos, types)` → 取 `watchers[PLAYER]` → 转 `[{uid: player.userId, sid: player.serverId}]`，按 `ignoreList[userId]` 过滤 | ✅ **强适合** | **「AOI 查询结果 → 网络投递地址」的唯一翻译点** |
| 同上 | `updateObject / updateWatcher` | 纯转发到 `area.aoi.*` | ✅ | — |
| `.../domain/area/area.js` | `Instance`（即 Area）构造器 | 从 `map.areaConfigData` 取 areaId/type/kind；**硬编码 `opts.towerWidth=300; opts.towerHeight=300`**；`this.aoi = aoiManager.getService(opts)`；`aiManager / patrolManager / actionManager / timer / areaLogic` 全在此组装；**构造器末尾就调 `areaLogic.startLogic()`** | ✅ 强适合（结构）| **「Area 是世界的组装根」**这一点非常适合 JSTM；⚠️ tower 尺寸硬编码应改为配置 |
| 同上 | `enterArea / exitArea` | 都先 `timer.abortAllAction(player.entityId)`；`exitArea` 再 `areaLogic.exitArea` + `removePlayer(player.id)` | ✅ 强适合 | **进出场景先清动作**，避免残留 Move action 把人带着跑 |
| 同上 | `tick()` | ① 遍历 `items` 更新（`item.update(currentTime)`，`died` 则广播 `onRemoveEntities` + `removeEntity`）② `actionManager.update()` ③ `aiManager.update()` ④ `patrolManager.update()` | ✅ 强适合 | 顺序有讲究：**动作先于 AI**（AI 在同一 tick 里能读到最新位置） |
| 同上 | `updatePlayers()` | 遍历 `players`：`currentTime > entity.kickTime` → **`exitArea`（踢人）**；否则 `entity.update()` | ✅ 强适合 | **「心跳超时踢人」集成在主循环**；JSTM 需要（1.4.9 客户端断线不一定发 FIN） |
| 同上 | `update1()` / `update3()` | 转 `areaLogic.update1/update3` | ✅ | 分频业务逻辑 |
| 同上 | `updateZones()` | 遍历 `zones` 各自 update（刷怪/刷物品） | ✅ **强适合** | 【已确认】`area.tick()` 里**不**调它，而是由 `AreaLogic.prototype.update1`（`areaLogic.js:89`）和 `AreaDomainLogic.prototype.update1`（`areaLogic.js:347`）调用 → **刷怪挂在 1 秒分频上，而不是 100ms 主 tick 上**（这是刻意的性能分层，JSTM 应照做） |
| 同上 | `start()` | 幂等（`isStartRun`）→ `aoiEventManager.addEvent(this, this.aoi.aoi)` → `initMobZones()` → `initNPCs()` → `aiManager.start()` → `timer.run()` | ✅ **强适合** | **「先挂 AOI 事件，再刷怪，再起 AI，最后起 tick」的启动顺序**至关重要（顺序错了会丢首批同步事件） |
| 同上 | `close()` | `timer.close()` + `areaLogic.close()` + `setTimeout(()=>{ 把 self 所有字段 delete; self=null }, 100)` | ⚠️ 部分 | 手动掏空对象在 JS 里是「手动 GC」土办法；Python 用 `del` + 解除引用即可 |
| 同上 | `getChannel()` | **懒创建**：`pomelo.app.get('channelService').getChannel(name, true)`；name = `area_<instanceId>` 或 `area_<areaId>` | ✅ **强适合** | **「实例用 instanceId、场景用 areaId 作频道名」**——与 `channelUtil.getAreaChannelName` 一致，JSTM 直接照搬 |
| 同上 | `initMobZones()` | 遍历 `map.getMobZones()`：`opts.area = this`；**`opts.level` 有值 → MobZone，无值 → ItemZone** | ⚠️ 部分 | 用 `level` 字段区分刷怪区/刷物区**很脆弱**，JSTM 应用显式 `type` |
| 同上 | `initNPCs()` | `map.getNPCs()` → `dataApi.npc.findById(kindId)` → 补 `data.areaId` → `addEntity(new NPC(data))` | ✅ | NPC 是静态的，**不进 AOI**（见下） |
| 同上 | `addEntity(e)` | 按类型分支：PLAYER → 查重 → `channel.add(userId, serverId)` → `aoi.addWatcher({id,type}, e, e.range)` → `players[e.id]=e.entityId`、`users[e.userId]=e.id`、`playerNum++`；MOB → `aiManager.addCharacters([e])` + `aoi.addWatcher`；ITEM/EQUIPMENT → 只进 `items{}`（**不进 AOI 的 watcher 表**）；NPC → `npcs[kindId]` 后直接 return；**统一末尾 `aoi.addObject({id,type}, e)`** | ✅ **强适合** | **「watcher（有视野，参与感知）+ object（只被看见，参与同步）」双注册模型**是 AOI 的核心用法，JSTM 必须理解并保留 |
| 同上 | `removeEntity(entityId)` | PLAYER → `channel.leave` + 清 AI/巡逻/动作 + 双向 `forgetHater/forgetEnemy` + `aoi.removeWatcher(..., range+1)` + 删 players/users + `playerNum--` + **为空则记 `emptyTime`**；MOB → 从 zone 删 + 同上；ITEM → 从 zone 删；末尾统一 `aoi.removeObject` + `delete entities[id]`；**非玩家才把字段全 delete** | ✅ **强适合** | **「清理顺序：关系表 → AOI → 索引 → 对象」**；`range+1` 是为了让 AOI 内部的边界包含判定能覆盖到 |
| 同上 | `getAreaInfo / getAreaInfoStrip / getEntitiesByPos` | 前者 `aoi.getIdsByPos(pos,range)` → 实体表；中者再 `.strip()` 并**额外把该场景所有 NPC 全塞进结果**；后者 `aoi.getIdsByRange(pos,range,types)`（跳过 NPC/ITEM） | ✅ 强适合 | **「NPC 不走 AOI、进场时全量下发」**是网游常见折中（NPC 数量少且固定）；⚠️ **`getAreaInfoStrip` 被 `enterScene` 以 `(player, range)` 调用，签名是 `(pos, range)`** —— 靠鸭子类型侥幸工作【已确认不一致】 |
| 同上 | `getAllPlayers / getAllEntities / getPlayer / removePlayer / removePlayerByUid` | 常规查询/删除；`removePlayerByUid` 用 `users[uid]` 反查 playerId | ✅ | `users{}` 反查表是必要的（uid ≠ playerId） |
| 同上 | `isEmpty()` | `playerNum === 0` | ✅ | 副本回收依据 |
| `.../domain/area/areaManager.js` | `AreaManager.prototype.getBossGenTimes()` | 遍历 6001..6005 场景，收集 `scene.getPlayerInArea().getBossGenTime()` | ⚠️ 部分 | **硬编码场景号区间**，JSTM 应配置化 |
| `.../servers/area/handler/playerHandler.js` | `handler.enterScene(msg,session,next)` | ① 若已在 area 则先 remove ② 校验 `session.uid === player.userId` ③ 同步 session.level（变了才 set+push）④ 取 teamId ⑤ `hp<=2` 补半血 ⑥ `area.enterArea` ⑦ `!map.isReachable` → 出生点 ⑧ `entities = area.getAreaInfoStrip(player, player.range)` ⑨ `area.addEntity(player)`，失败返回 code 13 ⑩ 返回 `{code:200, areaId, entities, curPlayer: player.playerStrip()}` | ✅ **强适合** | **注意顺序：先取 AOI 快照，再 addEntity** —— 若反过来，玩家会在自己的可见列表里看到自己（`onPlayerAdd` 里有 `watcher.entityId !== entityId` 的保护，但快照会重复）。JSTM 照此顺序即可 |
| 同上 | `handler.changeArea(msg,session,next)` | `session.area.areaId === msg.targetId` → code 136；否则组装 `args{playerId,area,player,targetId,argId}` → `areaManager.changeArea(args)` | ✅ | 走的是**新实现 `AreaManager.changeArea`**；旧实现 `areaService.changeArea` 仍在文件里但无人调用 |
| 同上 | `handler.move(msg,session,next)` | `player.died` → 直接 return；**`path = msg`（整个 msg 就是路径数组）**；`new Move({entity:player, path})`；`timer.addAction` 成功则**校验起点并 `timer.updateObject/updateWatcher` 校正 AOI**，再 `pushMessageByAOI(area,'onMove',{entityId,areaId,path}, startPoint)`；最后 `player.kickTime = now + 30min` | ❌ **不可照抄** | **服务端完全信任客户端上传的 path**（无 `verifyPath`、无速度/距离校验）→ 可穿墙、可瞬移、可拉怪。JSTM **必须**在服务端重算或至少校验：路径点可达 + 单 tick 位移 ≤ speed×Δt×容差 + 起点与服务器记录的位置吻合 |
| 同上 | `handler.clMove(msg,session,next)` | `msg` 是 `[x,y]`（终点）；服务端拼 `[{player.x,player.y},{x,y}]` 后同上；广播 `onClMove` 且**忽略自己**（`ignoreList[player.userId]=true`） | ⚠️ 部分 | 「客户端只报终点、服务端补起点」比 `move` 安全，但**仍然没有终点可达性/距离校验** |
| 同上 | `handler.stop` | `setIsMoving(true)` → `timer.abortAction(MOVE, entityId)` → `player.isStop=true` → `player.stand()`（内部广播 `onStand`） | ⚠️ 部分 | `player.setIsMoving(true)` 后立刻 abort 再 stand，**语义混乱（应为 false）**；`stand()` 里又根据 `isStop` 决定是否忽略自己，逻辑绕 |
| 同上 | `handler.getEntity` | 玩家请求补发某实体的完整数据 → 直接推 `onAddEntities` 给自己（**无距离/可见性校验 → 可枚举任何 entityId 拿全服实体数据**） | ❌ 不适合 | 信息泄露/透视风险。JSTM 应校验目标在自身 AOI 范围内 |
| 同上 | `handler.getProperty` | 先查 `areaManager.getCanUsedPlayer` 内存，未中查 `userDao.getSQLPlayer` + `equipmentDao` 拼装备列表返回 | ✅ 部分 | 「查看他人属性」流程可用，但**同样无可见性校验** |
| 同上 | `handler.npcTalk / revive / fightMode` | NPC 对话（`npc.talk(player)`，返回 `NPC.SUCCESS/NOT_IN_RANGE`）、切复活、切战斗模式 | ✅ | 简单直接 |
| `.../servers/area/handler/resourceHandler.js` | `handler.loadAreaResource` | 遍历 `session.area.getAllEntities()` **统计各类型 kindId 去重集合**，返回 `{players,mobs,npcs,items,equipments, mapName}` 给客户端做资源预加载 | ✅ **强适合** | **「进服先下发需要的资源清单」**对 1.4.9 这类老客户端非常重要（避免运行时缺资源卡顿），JSTM 必做 |
| `.../servers/area/filter/playerFilter.js` | `Filter.prototype.before` | 见 `pomelo.md` 第 2.1 节 | ✅ **强适合** | 「handler 前置守卫」范式 |
| `.../domain/messageService.js` | `errHandler` | 意图「推送失败 → `areaManager.removePlayerByUid(failUid)`」，**但实际是空操作**（`channelService` 的 `failIds` 装 uid，`removePlayerByUid` 查 playerId 键的 `players{}`）⇒ 见 `pomelo.md` 第 4.2 节核验链路 | ❌ **不能照抄** | 思想可用，但**参考实现是坏的**：JSTM 必须自己写，并显式区分 uid / player_id |
| `.../modules/sceneInfo.js` | `monitorHandler/masterHandler/clientHandler` | 场景监控模块（**注册代码在 app.js 里被注释，未启用**） | ✅ 思想适合 | 可作为 JSTM 运维面板的「场景状态上报」模板 |

---

## 3. 玩家在场景中的完整生命周期（时序）

```
① 连接期（connector）
   entry(token) → authRemote.auth → 返回角色列表
   entryPlayer(uid, playerId) → sessionService.kick(uid) → session.bind(uid)
                               → session.set(serverId='area-server', playerId, level, ...)
                               → session.on('closed', onUserLeave) → session.pushAll()
                               → chatRemote.add + guildRemote.enterGuild

② 进场景（area，经 connector doForward）
   playerFilter.before:
       areaManager.getPlayerWithPlayerIdCb(playerId)
         ├ 命中 players{} / playerCaches{}  → 直接返回
         └ 未命中 → userDao.getPlayerAllInfo → areaManager.addPlayer(player)
       player.serverId / player.sessionData 兜底填充        ← 回包地址在此确定
       session.area = areaManager.getAreaWithPlayer(player)  ← 按 areaId 或 instanceId 定位
       不在 area 中 → 仅 enterScene 路由放行，否则推 onChangeArea 并报错
   playerHandler.enterScene:
       area.enterArea(player)      → timer.abortAllAction + areaLogic.enterArea
       map.isReachable 校正 → 出生点
       entities = area.getAreaInfoStrip(player, player.range)   ← AOI 快照（含全部 NPC）
       area.addEntity(player):
            channel.add(userId, serverId)          ← 进场景频道
            aoi.addWatcher({id,type}, player, range)  ← 成为观察者，触发 add 事件
            players[playerId]=entityId; users[userId]=playerId; playerNum++
            aoi.addObject({id,type}, player)          ← 成为被观察者
       → 返回 {areaId, entities, curPlayer}

③ 运行期（每 100ms）
   timer.tick → area.tick
        ├ items 更新（超时消失 → onRemoveEntities）
        ├ actionManager.update → Move.update
        │      沿折线按 speed*Δt 推进 → entity.x/y 更新
        │      → aoi.updateObject({id,type}, oldPos, pos)      ← 更新物体覆盖的塔
        │      → aoi.updateWatcher({id,type}, oldPos, pos, range, range) ← 重算视野差集
        │         → onPlayerUpdate → 推 onRemoveEntities / onAddEntities（差量同步）
        ├ aiManager.update  → 每怪的 brain.update()（行为树）
        │      → tryAttack / moveToTarget / patrol 切换
        └ patrolManager.update → 巡逻状态机推进
   timer.tick 分频 → update1(1s) / update3(3s)
   area.updatePlayers()（在 areaLogic.update1/3 中调用，【待验证】）→ kickTime 超时踢人

④ 移动（玩家主动）
   handler.move(msg=path)  → new Move → timer.addAction → pushMessageByAOI('onMove')
   handler.clMove([x,y])   → 服务端补起点 → 同上，推 'onClMove'
   handler.stop            → abortAction(MOVE) → player.stand() → 推 'onStand'

⑤ 换场景 / 进副本
   handler.changeArea → areaManager.changeArea:
       type <= SCENE          → gotoScene:   exitArea → 目标场景出生点/传送点 → save
       type == TEAM_INSTANCE  → (旧实现 gotoTeamInstance，新实现走 gotoInstance)
       其它                    → gotoInstance: 生成 instanceId → instancePool.create
                                            → exitArea → player.instanceId = instanceId
       （旧路径还会 session.set('serverId', areaIdMap[targetId]) + pushAll，迁移归属）
   → 客户端重新 enterScene → 重复 ②

⑥ 下线
   session.on('closed') → onUserLeave(app, session, reason):
       area.playerRemote.playerLeave
            → 副本内则回场景出生点；hp==0 补半血
            → userDao.updatePlayer + taskDao.tasksUpdate(player.curTasks)
            → area.exitArea(player)   → abortAllAction + areaLogic.exitArea + removeEntity
                 removeEntity: channel.leave + 清 AI/巡逻/动作 + 双向 forget
                               + aoi.removeWatcher(range+1) + 删索引 + playerNum--
                               + 空场记 emptyTime + aoi.removeObject
            → areaManager.addPlayerCaches(player)   ← 进 60s 下线缓存
            → area.onUserLeave(playerId)  → channel.pushMessage('onUserLeave')
       （若为空副本）areaManager.removeInstance(instanceId)
       → manager.guildRemote.playerLeave / fightRemote.kick
       → handleRemote.chatRemote_kick → manager.chatRemote.kick
       → trade.marketRemote.kick

⑦ 副本回收（area 进程内，每 60s）
   instancePool.check → instance.isAlive()===false
       → rpc.manager.instanceRemote.remove(instanceId) → onClose → instance.close() + delete
```

---

## 4. 场景层的「好设计 vs 坏设计」速查

### 4.1 值得 JSTM 直接采用（【已确认】）

| # | 设计 | 位置 | 价值 |
|---|---|---|---|
| 1 | **AreaManager / Scene / Area / Instance / InstancePool 五层容器** | `domain/area/*` | 一套结构同时支撑「多场景 + 副本 + 分线」，Python 平移成本极低 |
| 2 | **Map 全服共享、Area 各自引用** | `scene.js#init` | 碰撞图/寻路器只占一份内存 |
| 3 | **100ms 主循环 + 1s/3s 分频** | `timer.js` | 单进程的最优 tick 分层 |
| 4 | **actionManager 把「行走」建模成可中断的 Action** | `domain/action/*` | 位置推进、AI 追击、巡逻共用一套机制 |
| 5 | **watcher（有视野）+ object（被看见）双注册** | `area.addEntity` | AOI 的正确用法 |
| 6 | **instanceId 命名即共享域**（`sin_/my_/team_/fight_/boss`） | `areaManager.gotoInstance` | 副本语义自解释，免去额外元数据 |
| 7 | **空场 5 分钟回收 + 下线 60s 对象缓存** | `instance.isAlive` / `playerCaches` | 两个不同粒度的资源回收 |
| 8 | **进出场景先 abortAllAction** | `area.enterArea/exitArea` | 防残留动作把角色带跑 |
| 9 | **NPC 不进 AOI、进场全量下发** | `getAreaInfoStrip` | 折中且有效 |
| 10 | **`loadAreaResource` 预下发资源清单** | `resourceHandler.js` | 老客户端的刚需 |
| 11 | ~~推送失败即视作断线并清理场景~~ → **改到 4.2 反模式表**：思想可借鉴，但参考实现（`errHandler`）因 uid/playerId 错配是空操作 | `messageService.errHandler` | ❌ 参考实现不可用 |
| 12 | **传送点方向反查落点** | `areaService.getInitPoint` | 双向传送不出错 |
| 13 | **handler 前置过滤器统一注入 session.player** | `playerFilter.js` | 消除重复代码 |

### 4.2 明确不要照抄（【已确认】）

| # | 反模式 | 位置 | 风险 |
|---|---|---|---|
| 1 | **完全信任客户端移动路径** | `handler.move` | 穿墙/瞬移/拉怪 |
| 2 | **`getEntity` 无可见性校验** | `handler.getEntity` | 透视全服实体 |
| 3 | **`clearPlayerCaches` 边写边全清** | `areaManager.js` | 缓存失效 + 对象被掏空 |
| 4 | **`getPlayerWithPlayerIdCb` 用 `'waiting'` 字符串当并发错误** | `areaManager.js` | 高并发首登偶发失败 |
| 5 | **tower 尺寸硬编码 300/300** | `area.js` | 大地图/小地图都一个粒度 |
| 6 | **`getAreaInfoStrip(player, range)` 参数与签名不符** | `area.js` vs `playerHandler.js` | 隐性 bug |
| 7 | **用 `opts.level` 是否存在区分 MobZone/ItemZone** | `area.js#initMobZones` | 加字段就崩 |
| 8 | **场景号区间硬编码 6001..6005** | `areaManager.getBossGenTimes` | 加地图要改代码 |
| 9 | **两套 changeArea 实现并存** | `areaManager.js` / `areaService.js` | 维护陷阱 |
| 10 | **`utils.myPrint` 全局硬编码开启 + `Error.prepareStackTrace`** | `util/utils.js` | 生产日志/性能双爆 |
| 11 | **`uncaughtException` 只打日志** | `app.js` 末尾 | 进程带病运行 |
| 12 | **`isStop`/`isMoving` 语义混乱** | `handler.stop`、`character.stand` | 状态难追踪 |
| 13 | **`instancePool` 的回收要跨进程问 manager** | `instancePool.check` | 单进程下纯浪费 |
