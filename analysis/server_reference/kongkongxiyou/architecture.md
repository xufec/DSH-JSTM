# 空空西游（kongkongxiyou）服务端架构审计 —— 总体架构 + 8 问答案

> 审计对象：`cankao/kongkongxiyou-master.zip`（331.8 MB，22486 文件）
> 审计方式：**ZIP 内按需读取（未解压到磁盘）**，用 `zipfile` 精确读取目标文件；跳过 `**/node_modules/**`（7909 文件）与 `cocosjs/`（7504 文件，客户端）。
> 审计目标：为《绝世唐门》1.4.9 私服兼容项目 **JSTM**（单进程 Python）提供设计参考。
> 结论标记：**【已确认】**=有源码直接证据；**【待验证】**=有间接证据/外部资料但未读到实现；**【未知】**=ZIP 内读不到。

---

## 0. 审计范围、已读清单与未读清单

### 0.1 实际被审计的代码树

| 路径（ZIP 内） | 文件数 | 性质 | 本次处理 |
|---|---|---|---|
| `cankao/.../kongkongxiyou-master/lordofpomelo/game-server/app/**` | 约 150 js | **作者自研游戏逻辑（核心审计对象）** | 逐文件读/签名级读 |
| `.../lordofpomelo/game-server/config/**` | 约 80 | 配置、数值表、地图碰撞数据 | 读 servers/master/session/instance/字典/protos |
| `.../lordofpomelo/pomelo/lib/**` | 94 js | Pomelo 1.2.0 框架本体 | 签名级读 + 重点文件全文 |
| `.../lordofpomelo/shared/**` | 4 | code.js / token.js / mysql.json | 读 |
| `.../lordofpomelo/web-server/**` | 8 js | HTTP 登录/OAuth/热更新 | 未细读【待验证】 |
| `.../lordofpomelo/game-server_backup/**` | 约 150 | **旧版本备份**（同一份代码的早期快照） | 仅比对差异，不单独分析 |
| `.../lordofpomelo/pomelo/node_modules/**` | 5200 | 第三方包 | **跳过**（按任务书要求） |
| `.../cocosjs/**`, `characterRes/`, `ccsbuilder/`, `plistbuild/` | 约 15000 | 客户端 cocos2d-js 工程与美术资源 | **不在本次审计范围** |
| `.../pomelo-admin-web/**` | 4563 | 运维 Web 控制台 | 未读【待验证】 |

### 0.2 关键发现：三个「读不到实现」的依赖

`package.json`（`game-server/package.json`）中声明的以下依赖**没有随 ZIP 一起打包**（全 ZIP 搜索 `pomelo-aoi` / `pomelo-pathfinding` / `pomelo-bt` / `pomelo-collection` / `pomelo-sync` 命中数均为 **0**）：

| npm 包 | 用途 | ZIP 内是否有源码 | 影响 |
|---|---|---|---|
| `pomelo-aoi >=0.3.4` | **AOI 服务（塔式算法）** | **无** | 只能读到「调用契约」，算法内部【未知】 |
| `pomelo-pathfinding >=0.1.0` | A* 寻路器 `buildFinder` | **无** | 只能读到 `weightMap` 接口契约 |
| `pomelo-bt >=0.0.1` | 行为树（Sequence/Select/Loop/If/Node） | **无** | 节点语义靠外部资料【待验证】 |
| `pomelo-collection >=0.1.0` | 优先队列（PathCache 用） | **无** | 只知用了 `priorityQueue` |
| `pomelo-sync-plugin` | DAO 脏数据定时落库 | **无** | 只能读 `app/dao/mapping/*Sync.js` 的同步表结构 |
| `pomelo-logger` / `pomelo-rpc` / `pomelo-loader` / `pomelo-admin` / `pomelo-scheduler` / `node-zookeeper-client` | 框架支撑 | 无 | 只按调用点推断行为 |

**因此：AOI 与寻路的具体算法，本报告只能给出「本项目如何接入 + 外部官方资料佐证」，内部实现一律标注【未知】，不做猜测。**

---

## 1. 项目定性

| 结论 | 内容 | 置信度 |
|---|---|---|
| 项目谱系 | `lordofpomelo/` 是 **网易 NetEase 开源 demo `lordofpomelo` 的分支/魔改**：`lordofpomelo/README.md` 原文即 lordofpomelo 介绍，`lordofpomelo/LICENSE` 是 `Copyright (c) 2012-2013 Netease, Inc.` 的 MIT 许可 | 【已确认】 |
| 作者自研部分 | 在 lordofpomelo 骨架上**补完了一个完整传奇类 MMORPG**：公会、城战（Domain）、师徒/市场/钱庄、选举（Federation）、VIP/充值、行为树 AI、巡逻、塔式 AOI、寻路、聊天，以及大量存档 DAO | 【已确认】 |
| 客户端 | `cocosjs/` = cocos2d-js 工程；服务端 `config/data/*.json` 是策划 Excel 转换产物（`exceldata/`） | 【已确认】 |
| 服务端框架版本 | `game-server/package.json` → `"pomelo":"1.2.0"`；`pomelo/` 目录是 1.2.x 的**内嵌源码**（含 `lib/application.js` 26 KB 等） | 【已确认】 |
| 项目版本 | `"name": "lord_of_pomelo", "version": "0.3.0"` | 【已确认】 |
| 代码规模 | `app/**` 纯逻辑约 **585 KB / 约 150 个 js**；`pomelo/lib` 约 300 KB / 94 js | 【已确认】 |
| 作者自述定位 | 根 `README.md`：「本项目首次尝试用 js 开发前后端大型网游，**未经历上线考验**」；「node.js 由于太灵活不太适合做多人的大项目」；「pomelo 的消息传输机制太臃肿，应该自己定义一套网络传送机制」；「尽量减少 pomelo 的服务器集群的规模」 | 【已确认】 |

> ⚠️ 作者自述「未经历上线考验」+「服务端未做完整压测」，意味着以下所有分布式设计都是**「写出来但未被生产验证」**的。对 JSTM 而言，**只能取设计思想，不能当成「经过验证的最佳实践」**。

---

## 2. 部署拓扑：声明了 9 类服务，实际只跑 6 类

### 2.1 `config/servers.json`（真实运行的服务）【已确认】

| serverType | serverId | 端口 | frontend? | 职责 |
|---|---|---|---|---|
| `connector` | connector-server-1 | 3150（clientPort **3010**） | ✅ | 客户端长连接、登录、建号、收发包 |
| `gate` | gate-server-1 | —（clientPort **3014**） | ✅ | 只提供 `queryEntry`，做连接分派 |
| `auth` | auth-server-1 | 3650 | ❌ | 只提供 `authRemote.auth`，校验 token |
| `area` | **area-server（单台！）** | 3270 | ❌ | **全部场景逻辑**；`areas:"[1001,2003,3001,3002,3003,3004,3005,6001,6002,6003,6004,6005]"` 12 个场景挤在 1 个进程里 |
| `manager` | manager-server-1 | 3750 | ❌ | 全局单例服务：公会、队伍、聊天/邮件、竞技场、副本管理 |
| `trade` | trade-server-1 | 3850 | ❌ | 拍卖行（MarketService）、元老会/选举（federationService） |

`config/master.json`：master 端口 3005。`config/masterha.json` 声明了 zookeeper 高可用双节点，但 `app.js` 中 `masterhaPlugin` 整段被**注释掉** → 高可用**未启用**。【已确认】

### 2.2 `config/adminServer.json` 声明了 9 类（含未部署的 3 类）【已确认】

`connector, chat, gate, auth, manager, path, area, trade, fight` —— 其中：

| 声明但 servers.json 中没有 | 实际发生了什么 |
|---|---|
| `chat` | **`app.js` 里有 `app.configure('production|development','chat',...)` 并在 `app/servers/chat/` 下有完整 handler+remote，但 servers.json 没有 chat 进程。** 代码通过 `app/consts/handleRemote.js` 把所有原来 `rpc.chat.chatRemote.xxx` 调用**硬编码改指向 `rpc.manager.chatRemote.xxx`** → **聊天功能被合并进 manager 进程** |
| `path` | 无对应目录、无实现。**残留声明** |
| `fight` | `app/servers/fight/` 有完整 handler+remote，`app.js` 也 `configure('...','fight')`，但 servers.json 未部署；竞技场实际由 `app/servers/manager/handler/fightHandler.js` + `fightService.js` 承担 |

> **这是本项目最重要的架构事实之一：作者在演进中把「本该独立的多进程」逐个并回了 manager/area，实际是一个「1 connector + 1 area + 1 manager + 1 trade + 1 auth + 1 gate」的**准单体**集群。**
> 对 JSTM（单进程 Python）而言，这等于**免费验证了「合服变成单体」的可行性**：作者自己就从多进程退回了准单体，并留下了完整的 `handleRemote` 适配层模式。

### 2.3 端口/连接全链路

```
客户端
  │ 1) HTTP(S) → web-server(express, config/oauth.json)  登录/注册/热更新拿 token
  │ 2) WebSocket → gate:3014   gate.queryEntry(uid) → 返回 {host, port:3010}
  │ 3) WebSocket → connector:3010
  │      connector.entryHandler.entry(token)   ── RPC ──▶ auth.authRemote.auth(token)
  │      connector.entryHandler.entryPlayer(uid, playerId)
  │      session.bind(uid) + session.pushAll()
  │ 4) 之后所有业务包 route 形如 `area.playerHandler.move`，由 connector 的
  │      server.globalHandle → doForward → sysrpc[area].msgRemote.forwardMessage 转发到 area
  └─ area 处理完成后 resp 原路回到 connector → socket → 客户端
```

`connectorConfig`：`hybridconnector`、`heartbeat:30`、`useDict:true`、`useProtobuf:false`、`disconnectOnTimeout:true`、`setNoDelay:true`、`handshake` 空实现（无鉴权握手）。【已确认】

---

## 3. 服务端分层（文件级）

```
game-server/
├── app.js                         ← 唯一的组装点：按 serverType 注册组件/服务/过滤器/路由
├── app/
│   ├── servers/                   ← 「接入层」：按 serverType 分包，handler=客户端可调用, remote=进程间可调用
│   │   ├── gate/handler/gateHandler.js          queryEntry
│   │   ├── connector/handler/{entryHandler,roleHandler}.js
│   │   ├── area/handler/*.js  (13 个)           ← 场景内所有业务入口
│   │   ├── area/remote/*.js   (3 个)            ← area 对外暴露的 RPC
│   │   ├── area/filter/playerFilter.js          ← 全局前过滤器：把 player/session.area 注入 handler
│   │   ├── auth/remote/authRemote.js
│   │   ├── manager/{handler,remote}/*.js        ← 全局单例逻辑（含聊天）—— 真正的「逻辑服」
│   │   ├── trade/{handler,remote}/*.js
│   │   ├── fight/{handler,remote}/*.js          （未部署）
│   │   └── chat/{handler,remote}/*.js           （未部署）
│   ├── domain/                    ← 「领域层」：纯游戏世界模型，不依赖 pomelo 网络
│   │   ├── area/{area,scene,areaManager,instance,instancePool,timer}.js
│   │   ├── aoi/aoiEventManager.js              ← AOI 事件 → 客户端消息 的翻译层
│   │   ├── map/{map,mobzone,itemzone,zone}.js  ← 地图 + 刷怪区 + 寻路
│   │   ├── entity/{entity,character,player,mob,npc,item,equipment,team}.js
│   │   ├── action/{action,actionManager,move,revive}.js  ← 服务端权威位置推进
│   │   ├── task/*, bag*, equipments, fightskill, buff, playerBank, myBoss, federation
│   │   ├── messageService.js                    ← 全服推送统一出口
│   │   └── persistent.js                        ← 存档接口
│   ├── ai/                        ← 行为树 AI（brain/action/node/meta/service）
│   ├── patrol/                    ← 巡逻状态机（single/loop/composite/wait）
│   ├── services/                  ← 「应用服务」：跨场景/全局单例业务（market, guild, federation, fight, chat, instance, team）
│   ├── dao/                       ← MySQL 持久化（+ mapping/*Sync.js 供 pomelo-sync-plugin 定时落库）
│   ├── consts/                    ← consts.js / formula.js / handleRemote.js
│   ├── modules/                   ← pomelo-admin 监控模块（onlineUser, sceneInfo）
│   └── util/                      ← dataApi（配置表）、dispatcher、routeUtil、channelUtil、geometry、pathCache、utils
└── config/                        ← servers.json, master.json, session.json, instance.json, data/*.json（策划表）, map/mapEntity*.json（碰撞）, schema/Pomelo.sql
```

**分层要点（对 JSTM 极其重要）【已确认】：**
1. `servers/` 与 `domain/` 分离清晰：`domain` 里**没有任何 handler/session 概念**（只有 `messageService` 这一个出网口），handler 只做「取 session.player → 调 domain → 回 code」。
2. 所有出网消息经 `domain/messageService.js` 统一出口，且**只认 `{uid, sid}`**，不认 socket。
3. 全局单例业务放在 `services/`，由 `app.js` 在对应 serverType 上 `app.set('xxxService', new XxxService(app))` 注入。

---

## 4. 任务书 8 问：逐条回答（摘要，详见对应专文）

### 问 1：Pomelo 如何划分服务？→ 详见 `pomelo.md`
**答【已确认】——「三把刀」切分：serverType × 目录约定 × 组件。**

1. **纵向按 serverType 切进程**：`config/servers.json` 是唯一真源；`app.js` 里 `app.configure(env, 'area|auth|...', fn)` 按类型装配。启动方式 `node app.js serverType=area id=area-server`。
2. **横向按目录约定切「能力面」**（Pomelo 用**约定优于配置**，靠路径扫描自动注册，见 `pomelo/lib/util/pathUtil.js`）：
   - `app/servers/<serverType>/handler/**` → **客户端可调用**（`pomelo-loader` 自动加载，route = `serverType.handlerName.methodName`）
   - `app/servers/<serverType>/remote/**` → **服务器间可调用**（RPC 服务端自动挂载，命名空间 `app.rpc.<serverType>.<remoteName>.<method>`）
   - `app/servers/<serverType>/cron/**` → 定时任务
   - `pomelo/lib/common/remote/{frontend,backend}/**` → 系统级 RPC（`sessionRemote`、`channelRemote`、`msgRemote`）
3. **正交按组件切关注点**：`pomelo/lib/components/` 共 12 个组件，`appUtil.loadDefaultComponents` 按「是否 master / 是否有 port / 是否 frontend」条件装载：`master, proxy, remote, connection, connector, session, pushScheduler, backendSession, channel, server, monitor`。本项目又额外 `app.use(sync, {sync:{path:.../dao/mapping, dbclient}})` 引入 pomelo-sync-plugin。
4. **frontend / backend 二分**：`frontend:true` 的（connector、gate）才有 `clientPort` + connection/connector/session 组件；backend 只有 `port` + remote 组件。这是 Pomelo 里「接入」与「逻辑」的第一性划分。

### 问 2：Gate / Connector / Logic 如何协作？→ 详见 `pomelo.md`
**答【已确认】：**

| 角色 | 代码 | 职责 | 关键点 |
|---|---|---|---|
| **Gate** | `servers/gate/handler/gateHandler.js#queryEntry` | **唯一的负载均衡入口**：客户端先用 uid 问「我该连哪个 connector」 | 返回 `{host, port}`；`host` 被**硬编码改写**为「本机第一个非 127.0.0.1 的网卡 IP」（`os.networkInterfaces()`），`dispatcher.dispatch` 用 `uid % connectors.length` 取模（`util/dispatcher.js`，**crc 版本被注释掉了**） |
| **Connector** | `servers/connector/handler/*.js` + `pomelo/lib/components/connector.js` | 长连接、session 生命周期、**消息转发中枢** | `handleMessage` → `server.globalHandle(msg, session.toFrontendSession())` → 若 `routeRecord.serverType !== 本机 serverType` → `doForward()` → `app.sysrpc[serverType].msgRemote.forwardMessage(session, msg, session.export(), cb)`；回包再由 connector `send()` → `__pushScheduler__` |
| **Logic** | `area` / `manager` / `trade` | 纯业务 | 收 `msg.body`（`doHandle` 里 `msg = msg.body`，并把 `msg.__route__` 注入；注意本项目 `useProtobuf:false`，所以 `msg.body` 由 hybridconnector 的 decode 产出） |

**三条协作链（已确认）：**
- **登录链**：`gate.queryEntry` → `connector.entry` → `authRemote.auth(token)` → `connector.entryPlayer`（`sessionService.kick(uid)` 挤掉旧连接 → `session.bind(uid)` → `pushAll` → 注册 `session.on('closed')` → 广播 `chatRemote.add` / `guildRemote.enterGuild`）。
- **业务链**：`routeUtil.area` 直接返回 `session.get('serverId')`，即**玩家的所有 area 请求永远被投递到 session 里记录的那台 area 进程**；换场景时 `session.set('serverId', areaIdMap[targetId])` + `session.pushAll()` 来迁移归属。【已确认】
- **下线链**：`session.on('closed')` → `onUserLeave` → 依次 RPC：`area.playerRemote.playerLeave`（存档+退出AOI+移入 playerCaches）、`manager.guildRemote.playerLeave`、`manager.fightRemote.kick`、`chatRemote.kick`、`trade.marketRemote.kick`。

### 问 3：Scene 服务器如何管理玩家？→ 详见 `scene.md`
**答【已确认】：三层容器 + 100 ms 心跳 tick。**

- **容器三层**：`AreaManager`（一台 area 进程的全局注册表：`scenes{}` 场景表、`players{}` 在线玩家、`playerCaches{}` **下线缓存**、`instances{}` 副本、`playerIdToInstanceId{}`） → `Scene`（薄包装，一个 `Area`） / `InstancePool`（`instances{}` + 60 s 回收定时器） → **`Area`（真正的世界）**：`players{playerId→entityId}`、`users{userId→playerId}`、`entities{}`、`items{}`、`npcs{}`、`zones{}`、`aoi`、`aiManager`、`patrolManager`、`actionManager`、`timer`、`areaLogic`。
- **主线 Tick（`domain/area/timer.js`）**：`setInterval(tick, 100)`
  - 每 100 ms：`area.tick()` = 遍历 items 更新 + `actionManager.update()`（**推进行走/复活动作、每步都更新 AOI**）+ `aiManager.update()`（行为树）+ `patrolManager.update()`
  - 每 1 s（`timeCount%10`）：`area.update1()` → `areaLogic.update1()`
  - 每 3 s（`timeCount>30`）：`area.update3()` → `areaLogic.update3()`（城战/复活等低频逻辑）
  - 另有 `updatePlayers()` 单独遍历在线玩家做**超时踢人**：`currentTime > entity.kickTime` → `exitArea`（`consts.KICKTIME = 1800000`，30 分钟；每次 move/clMove 刷新 `kickTime`）
- **进场景（`servers/area/handler/playerHandler.js#enterScene`）**：`area.getPlayer` 已存在则先 remove → 校验 `session.uid === player.userId` → 同步 session.level → 取 teamId → 血量兜底 → `area.enterArea(player)`（先 `timer.abortAllAction`，再走 `areaLogic.enterArea`） → 若 `!map.isReachable` 则放到 `map.getBornPoint()` → **`area.getAreaInfoStrip(player, player.range)` 先取 AOI 快照** → `area.addEntity(player)`（**在 addEntity 里才 `aoi.addWatcher`**） → 返回 `{areaId, entities, curPlayer}`。
- **换场景/副本（`areaManager.changeArea`）**：`dataApi.area.findById(targetId).type` 决定走 `gotoScene`（同进程 `scenes[targetId]`，只改 `player.areaId` + 出生点 + 存档）还是 `gotoInstance`（经 `manager.instanceRemote.create` 建副本，instanceId 规则：`fight_/my_/sin_/team_ + ...`）。**注意：本仓库里 `areaManager.gotoScene/gotoInstance` 是「新实现」，同时 `services/areaService.js` 里还留着旧的同名实现（走 session/async.series）——两套并存，`handler.changeArea` 走的是新的一套。**【已确认】
- **玩家下线**：`playerRemote.playerLeave` → 若在副本则回场景出生点、`hp==0` 补半血 → `userDao.updatePlayer` + `taskDao.tasksUpdate` → `area.exitArea` → **`areaManager.addPlayerCaches(player)`（缓存对象，60 s 后 `clearPlayerCaches` 把字段全 delete）**。

### 问 4：AOI 如何处理？→ 详见 `aoi.md`
**答【已确认调用契约 / 【未知】内部算法】：采用外部包 `pomelo-aoi` 的「塔式（tower）AOI」，本项目只做「参数配置 + 事件翻译 + 消息推送」。**

- **配置**：`domain/area/area.js` 构造时 `opts.towerWidth=300; opts.towerHeight=300; this.aoi = aoiManager.getService(opts)` —— **塔宽高被硬编码为 300×300**（覆盖配置表）。
- **两类对象**：*Object*（被观察者，`addObject/removeObject/updateObject`）与 *Watcher*（观察者，带 `range`，`addWatcher/removeWatcher/updateWatcher`）。本项目**玩家和怪物都同时注册为 watcher**（`addWatcher({id:entityId,type}, e, e.range)`），NPC 完全不进 AOI。
- **事件 → 客户端消息**（`domain/aoi/aoiEventManager.js`，只监听 4 个事件）：

| AOI 事件 | 处理函数 | 产生什么推送 |
|---|---|---|
| `add` | `onPlayerAdd` / `onMobAdd` / `onItemAdd` | 对「已在此范围内的其他 watcher」推 `onAddEntities`；**MOB 额外触发主动怪 `mob.onPlayerCome(entityId)` 或 `isActiveAttack` 时反向索敌** |
| `remove` | `onPlayerRemove`（**只处理 PLAYER**，MOB/ITEM 的 remove 分支被注释掉） | 推 `onRemoveEntities` |
| `update` | `onObjectUpdate` | 做 `oldWatchers` vs `newWatchers` **双向差集** → 复用 `onPlayerAdd/onPlayerRemove`（这就是「AOI 差量同步」） |
| `updateWatcher` | `onPlayerUpdate` | 直接推 `onRemoveEntities(removeObjs)` + `onAddEntities(addObjs)`，并对已被移出塔的对象回写 `tower.removeById` 做脏数据清理 |

- **推送出口**：`messageService.pushMessageByAOI(area, route, msg, pos, ignoreList)` → `area.timer.getWatcherUids(pos, [PLAYER], ignoreList)` → `aoi.getWatchers(pos, types)` → 转成 `{uid:userId, sid:serverId}` 列表 → `channelService.pushMessageByUids(...)`。**AOI 查询结果永远被翻译成「userId+frontendId」，再交给 channelService 跨进程推送。**
- **移动与 AOI 的耦合点**：`domain/action/move.js#update` 每 tick 算完新坐标后两连发：`area.timer.updateObject({id,type}, oldPos, pos)` + `area.timer.updateWatcher({id,type}, oldPos, pos, entity.range, entity.range)`。
- 另一条 AOI 反查：`area.getEntitiesByPos(pos, types, range)`（用 `getIdsByRange`）用于技能范围判定，`getAreaInfoStrip(pos, range)` 用于进场快照。
- ⚠️ **`getAreaInfoStrip` 的调用参数是 `(player, player.range)`，但函数签名是 `(pos, range)`** —— 靠 JS 鸭子类型（player 有 x/y）侥幸可用，**这是一个真实的可疑点**。【已确认代码不一致】

### 问 5：寻路如何处理？→ 详见 `pathfinding.md`
**答【已确认项目侧 / 【未知】A* 内核】：tile 代价图 + 外部 A* + 两级路径压缩 + LRU 路径缓存。**

- **代价图**：`domain/map/map.js` 从 `config/map/mapEntity<pathId>.json` 读 `collisions`，`getWeightMap()` 生成 `rectW × rectH` 网格，障碍格 = `Infinity`，可走格 = `1`；`isReachable(x,y)` = 世界坐标 → tile → `weightMap[x][y] === 1`。
- **邻居扩展**：`forAllReachable(x,y,cb)` **只给上下左右 4 邻域**（无对角线），即 A* 内部是曼哈顿式扩展。
- **`findPath(x,y,x1,y1,useCache)` 流程**（【已确认】）：
  1. 越界 / 起终点不可走 → `null`
  2. **`_checkLinePath` 直线可达则直接返回两点路径**（直线采样步长 = `tileW/2`，`_testLine` 额外检查跨格时的中点）
  3. 否则 `pathCache.getPath(tileX1…tileX2)` 查缓存，未命中则 `this.pfinder(tx1,ty1,tx2,ty2)`（**外部 `pomelo-pathfinding.buildFinder(this)`，返回 tile 路径，内核【未知】**）
  4. 命中才 `addPath` 写缓存（`useCache` 默认 **false**）
  5. tile → 世界坐标（`transPos`，取格子中心） → `compressPath2`（去掉共线中点） → 若 >2 点再 `compressPath1(path,3)`（**j += 2 的跳跃式拉直，最多 3 轮**）+ 再次 `compressPath2`
- **缓存**：`util/pathCache.js` 自己实现：`key = x1_y1_x2_y2`（tile 坐标）+ `pomelo-collection.priorityQueue`（按 time 的 **二次队列**做 LRU 淘汰）；map 里实例化 `limit:1000`，类默认 30000。
- **服务端-客户端协同（重要！）**：
  - `Character.prototype.move(x,y,useCache,cb)`（AI/巡逻用）：服务端自己 `map.findPath` → 建 `Move` action → 广播 `onMove {entityId, path}`。
  - `handler.move(msg)`（玩家用）：**msg 本身就是客户端算好的整条 path**，服务端直接 `new Move({entity, path: msg})` 并广播 —— **服务端信任客户端路径，没有做 `verifyPath` 校验**（`Map.prototype.verifyPath` 存在但**在项目里 0 处调用**）。这是**可作弊设计**，JSTM 不能照抄。【已确认】
  - `handler.clMove(msg)`：客户端只报终点 `{x,y}`，服务端补 `[{当前点},{msg}]`。
- **位置推进**：`domain/action/move.js#update(currentTime)` 按 `speed*Δt/1000` 沿折线滑行，支持一 tick 跨越多个路径点；每 tick 更新 AOI；`singleton=true` 保证「一个实体同一时刻只有一个 MOVE action」。

### 问 6：AI 如何处理？→ 详见 `reuse_candidates.md`（AI 章节）
**答【已确认】：行为树（外部 `pomelo-bt`）+ 黑板 + 按「角色名」注册的 Brain 表；AI 与巡逻是两套可互相切换的模块。**

- **装配（`app/ai/ai.js`）**：`fs.readdirSync(__dirname+'/brain')` **扫描 brain 目录自动注册**，`brain.name || filename` 作为 brain 类型名；`ai.createManager({area})` 每个 Area 一个 `AiManager`。
- **选脑（`app/ai/service/brainService.js`）**：`getBrain(type, blackboard)` —— **`if (type !== 'autoFight' && type !== 'player') type = 'tiger';`** 即**所有怪物共用 tiger 一套脑**（目前 brain 目录只有 `tiger.js`、`player.js`）；`brain.clone({blackboard})` 复制一份。
- **黑板**：`{manager, area, curCharacter}` + 运行期字段（`curTarget, targetPos, moved, distanceLimit`）。
- **两棵树**：
  - `tiger`（怪）：`Select[ If(有目标) → Loop(TryAndAdjust{adjust: MoveToTargetForAttack, try: TryAttack}) , If(无目标) → Patrol ]`
  - `player`（自动挂机）：`Select[ 攻击If, 拾取If(TryPick), 对话If(TryTalkToNpc) ]`
  - `TryAndAdjust` 是自定义组合节点：`Select[ tryAction , Sequence[ adjustAction, tryAction ] ]` —— **「先试，失败则调整（走过去）再试」的通用范式**。
- **怪物 AI 的边界约束**（`ai/action/moveToTarget.js`）：`|x - spawnX| > 500 || |y - spawnY| > 500` → **脱战回家**（`forgetHater` + `RES_FAIL`）。
- **AI ↔ 巡逻切换**（`domain/area/timer.js`）：`timer.enterAI(entityId)`（删巡逻、加 AI）/ `timer.patrol(entityId)`（删 AI、加巡逻，路径取 `entity.path`）。怪出生时 `apply` 巡逻（`mobzone.generateMobs` → `map.genPatrolPath` → `patrolManager`），被玩家触发后切 AI。
- **巡逻**（`app/patrol/`）：不是行为树，是**独立状态机**，`mode/{single,loop,composite,wait}.js` 返回 `RES_FINISH=0 / RES_WAIT=1`；`Loop` 模式带 `standTick=50`（×100 ms = 5 s 间隔休息）和 `rounds=-1` 无限循环。
- **主动怪的「感知」不走 AI 轮询**，而是**由 AOI 的 add 事件驱动**（`aoiEventManager.onMobAdd` → `mob.onPlayerCome`），被动怪则等玩家攻击后 `increaseHateFor` 进仇恨表。

### 问 7：聊天如何独立？→ 详见 `pomelo.md` 第 6 节
**答【已确认】：设计上「独立进程 + ChannelService 广播」，实际上「被并进 manager 进程」，靠一层 `handleRemote` 适配层收口。**

- **独立设计（原本）**：`app/servers/chat/` 有 `handler/chatHandler.js`（客户端入口）+ `remote/chatRemote.js`（RPC 服务），`ChatService`（`app/services/chatService.js`）维护 `uidMap/nameMap/channelMap` 三张表 + 邮件池（`mails/mailIds/mailPlayerIds/playerIdMails`，上限 1000 封 FIFO）+ 聊天物品池（`chatItems`，上限 150）。
- **频道模型**：`consts.Channel = {WORLD:1, AREA:2, FACTION:3, TEAM:4, PRI:5, SYSTEM:6, MARQUEE:7}`；频道名由 `util/channelUtil.js` 生成：全局固定 `"pomelo"`、`area_<areaId>`、`team_<teamId>`、`guild_<guildId>`。
- **广播靠框架的 ChannelService**（`pomelo/lib/common/service/channelService.js`）：`getChannel(name, true)` 懒创建 → `channel.pushMessage(route='onChat', msg, cb)`；Channel 内部按 `sid`（前端服务器 id）分组，`sendMessageByGroup` 里逐组走 RPC 到对应 connector 推送；成员为 0 时 `destroyChannel`；且有 `addToStore/loadAllFromStore`（**基于 `app.get('backendSessionService')`/store 的跨进程频道恢复**）。
- **实际部署（重要）**：`config/servers.json` **没有 chat 进程**；`app/consts/handleRemote.js` 把 `chatRemote_add / _kick / _readMail / _pushWorld / _pushMarquee` 全部改写成 `pomelo.app.rpc.manager.chatRemote.*`，调用方（entryHandler、area/chatHandler 等）只依赖 `handleRemote`。
- **聊天内容入口在 manager**：`app/servers/manager/handler/chatHandler.js#send` —— 先 `checkForbid()` 用 30 KB 的 `config/data/forbid_word.json` 做 `*` 替换，再按频道分流：WORLD/AREA → `chatService.pushByChannel`；FACTION → `rpc.manager.guildRemote.chatInGuild`；TEAM → `rpc.manager.teamRemote.chatInTeam`；PRI → `pushByPlayerId` 双向；MARQUEE/SYSTEM → 全局频道（SYSTEM 频道有 `@1|...` 的**内置 GM 命令后门**：直接给自己发 9001×100 + 6101×1 邮件）。【已确认】
- **rich text 物品链接**：`<#GkindId|id>` 语法，由 `ChatService.findItem` 解析后经 `rpcInvoke` 回 area 的 `playerRemote.getChatItem` 取物品属性。
- **area 内的 `chatHandler.js` 只剩 `readMail`**（领邮件附件）；频道加入/退出由 `entryHandler`/`area.addEntity`（`this.getChannel().add(userId, serverId)`）与 `removeEntity`（`channel.leave`）自动完成。

### 问 8：服务端模块如何扩展？→ 详见 `pomelo.md` 第 7 节
**答【已确认】：Pomelo 提供 7 个扩展点，本项目全部用到。**

| # | 扩展点 | 机制 | 本项目的实例 |
|---|---|---|---|
| 1 | **新增 serverType** | 在 `servers.json` 加一段 + 建 `app/servers/<type>/{handler,remote}/` + `app.configure(env,'<type>',fn)`；handler/remote 由 `pomelo-loader` **按目录自动加载**，无需注册 | `trade`、`manager`、`fight`、`chat` 都是这样加的 |
| 2 | **新增 handler/remote 方法** | 直接在目录里加 export，route 即 `serverType.fileName.methodName`；`reloadHandlers` 选项还能 `fs.watch` 热重载（`handlerService.js`） | 13 个 area handler |
| 3 | **过滤器 filter** | `app.filter()`（按类型）/`app.globalFilter()`/`app.before()`/`app.after()`；`filterService` 是 `befores[]`+`afters.unshift()` 链 | `playerFilter`（area 专属）、`pomelo.filters.toobusy()`（production） |
| 4 | **RPC 过滤器** | `app.rpcFilter(pomelo.rpcFilters.rpcLog())` | 被注释掉 |
| 5 | **组件 component** | `app.load(component, opts)`；组件有 `start/afterStart/stop` 生命周期，可 `__defineGetter__` 往 `app` 上挂属性 | `pomelo-sync-plugin`（脏存档定时落库）；`app.set('chatService', ...)` |
| 6 | **插件 plugin** | `app.use(plugin, opts)`：插件可选带 `components/`、`events/`、`crons/` 目录，框架自动装载（`application.js` `Application.use`） | `pomelo-sync-plugin`、`pomelo-masterha-plugin`（注释） |
| 7 | **admin 模块** | `app.registerAdmin(module, opts)`；模块实现 `monitorHandler/masterHandler/clientHandler` 三段式，被 pomelo-admin 控制台调用 | `app/modules/onlineUser.js`（在线数）、`sceneInfo.js`（场景状态，**注册被注释**） |

---

## 5. 关键结论 / 风险清单（跨文件汇总）

| # | 结论 | 证据 | 置信度 |
|---|---|---|---|
| 1 | 服务切分靠「serverType + 目录约定」，`servers.json` 是唯一真源 | `config/servers.json`, `util/pathUtil.js`, `handlerService.js`, `components/remote.js` | 【已确认】 |
| 2 | 实际部署已退化为准单体（12 个场景挤 1 个 area 进程；chat 并入 manager） | `servers.json`, `consts/handleRemote.js`, `adminServer.json` | 【已确认】 |
| 3 | gate 只做 `uid % n` 取模分派，**无一致性哈希**（crc 代码被注释），connector 增减会打乱映射 | `util/dispatcher.js`, `gateHandler.js` | 【已确认】 |
| 4 | `queryEntry` 返回的 host 用「本机第一块非 loopback 网卡 IP」，**多网卡/容器环境会返回错 IP** | `gateHandler.js` | 【已确认】 |
| 5 | 玩家所有 area 请求靠 `session.serverId` 静态路由，换场景靠 `session.pushAll()` 迁移 → **广播式会话同步** | `util/routeUtil.js`, `areaService.gotoScene` | 【已确认】 |
| 6 | AOI 内部算法不在仓库（外部 `pomelo-aoi`），本项目只做 towerWidth=300 配置 + 4 事件翻译 | `area.js`, `aoiEventManager.js` | 【已确认】/算法【未知】 |
| 7 | AOI 差量同步用「oldWatchers vs newWatchers 双向差集」实现，是**可复用的核心思想** | `aoiEventManager.onObjectUpdate` | 【已确认】 |
| 8 | 寻路内核同样外部（`pomelo-pathfinding.buildFinder`）；项目侧实现「代价图 + 直线快路径 + 两级压缩 + LRU 缓存」 | `map.js`, `pathCache.js` | 【已确认】/内核【未知】 |
| 9 | **玩家移动路径完全信任客户端**（`handler.move` 直接吃 msg 当 path，`verifyPath` 从不调用）→ 可穿墙/瞬移 | `playerHandler.js`, `map.js`（verifyPath 0 调用） | 【已确认】 |
| 10 | Move 推进是「按速度沿折线滑行 + 每 tick 更新 AOI」，服务端权威位置 | `action/move.js` | 【已确认】 |
| 11 | AI = 行为树（外部 `pomelo-bt`）+ 黑板 + 按名字注册 brain；怪物共用 tiger 脑；ai/patrol 两模块互斥切换 | `ai/**`, `patrol/**`, `timer.js` | 【已确认】（bt 节点内部语义【待验证】） |
| 12 | 聊天靠框架 ChannelService 广播，频道成员在 channel 内按 `sid` 分组后 RPC 到各 connector | `chatService.js`, `channelService.js` | 【已确认】 |
| 13 | 存在两套并存的换场景实现（`areaManager.*` 与 `areaService.*`），实际走 `areaManager` | `areaManager.js`, `areaService.js`, `playerHandler.changeArea` | 【已确认】 |
| 14 | `getAreaInfoStrip(player, range)` 参数与签名不符（代码靠鸭子类型侥幸工作） | `area.js` vs `playerHandler.js` | 【已确认】 |
| 15 | 无 `protobuf`（`useProtobuf:false`）、无 `pomelo` 加密（`useCrypto` 未开）、`handshake` 空实现 | `app.js` | 【已确认】 |
| 16 | `uncaughtException` 只打日志不退出（`app.js` 末尾） | `app.js` | 【已确认】 |
| 17 | `utils.myPrint` 的 `isPrintFlag = true` 且**硬编码**、走 `Error.prepareStackTrace` 取调用栈 → 生产环境**全量 console.log + 抛异常构造栈**，性能/日志双爆 | `util/utils.js` | 【已确认】 |
| 18 | `pathCache` 的 LRU 淘汰逻辑里 `this.queue.pop()` 在 `delKey` 为 `undefined` 时会崩（`this.cache[delKey].update`） | `util/pathCache.js` | 【已确认】 |
| 19 | 项目根目录**无 LICENSE**；`lordofpomelo/` 有继承自 NetEase 的 MIT LICENSE；作者在 README 里口头写「授权大家随便使用」 | 全 ZIP 文件名扫描 + 3 个 LICENSE 文件内容 | 【已确认】 |
| 20 | `game-server_backup/` 是同一份代码的旧快照（`areaLogic.js` 22 KB vs 33 KB），**可作为「作者演进路线」的参考** | 文件清单+体积对比 | 【待验证】（未逐行 diff） |

---

## 6. 与 JSTM（单进程 Python）的总对照

| 维度 | 空空西游 | JSTM（单进程 Python） | 可迁移性 |
|---|---|---|---|
| 进程模型 | 6 类进程 + RPC | 1 进程 | ❌ 进程/RPC 全部作废，但**「先按 serverType 切模块，再合并」的代码组织**可保留 |
| 网络层 | pomelo-hybridconnector + WebSocket | 自行实现 | ❌ 完全不可借鉴 |
| 并发模型 | 单线程事件循环 + 100 ms 全服 tick | asyncio/线程 + tick | ✅ **tick 分层（100ms/1s/3s）可直接照搬** |
| 场景容器 | AreaManager/Scene/Area/InstancePool | 同构的 Python 类 | ✅ **强烈推荐照搬层次** |
| AOI | 塔式 300×300 + watcher(range) | 需自研 | ✅ **「塔 + watcher.range + 4 事件 + 差集同步」是最值得借鉴的部分** |
| 寻路 | 外部 A* + 代价图 + 压缩 + LRU 缓存 | Python A* | ✅ 设计可借鉴；但**必须补 `verifyPath` 服务端校验** |
| AI | 行为树 + 黑板 | 可简化 | ✅ **行为树 + 黑板 + 「先试后调」范式**值得借鉴（无需 pomelo-bt） |
| 聊天 | 独立进程 → 并入 manager | 进程内频道 | ✅ **频道抽象 + 频道名规则 + 内容过滤**可借鉴 |
| 存档 | MySQL DAO + pomelo-sync 定时脏刷 | 需自研 | ✅ **「内存对象 + 脏标记 + 定时批量落库」思想可借鉴** |
| 许可 | 根无 LICENSE | —— | ⚠️ **只能借鉴设计，绝不复制代码**（详见 `reuse_candidates.md`） |

---

## 7. 遗留未读（诚实声明）

| 未读内容 | 原因 | 影响 |
|---|---|---|
| `pomelo-aoi` / `pomelo-pathfinding` / `pomelo-bt` / `pomelo-collection` 源码 | 未随 ZIP 打包（全库 0 命中） | AOI/寻路/BT 内核【未知】，只能给契约 + 官方 README 佐证 |
| `cocosjs/**`（7504 文件，客户端） | 超出服务端审计范围 | 客户端如何算路径/预测移动【未知】 |
| `pomelo-admin-web/**`（4563 文件） | 运维面板，非服务端逻辑 | 监控指标口径【未知】 |
| `web-server/app.js` + `lib/oauth.js`（7.7 KB） | 本次聚焦 game-server | HTTP 登录/第三方授权细节【待验证】 |
| `dao/**` 逐个 SQL 细节（约 30 文件） | 只做签名级+抽查 | 表结构与 `config/schema/Pomelo.sql`（18.8 KB）未逐字段核对 |
| `services/marketService.js`（34 KB，最大单文件） | 只读签名+关键流程 | 拍卖行撮合算法细节【待验证】 |
| `services/federationService.js`（20 KB） | 只读签名 | 选举/任期算法细节【待验证】 |
| `game-server_backup/**` 逐行 diff | 时间成本 | 演进路线【待验证】 |

---

## 8. 附：本报告引用的原始文件清单

**game-server/app/**
`app.js`, `consts/{consts,handleRemote}.js`, `util/{routeUtil,dispatcher,channelUtil,geometry,pathCache,utils,dataApi}.js`,
`servers/gate/handler/gateHandler.js`, `servers/connector/handler/{entryHandler,roleHandler}.js`, `servers/auth/remote/authRemote.js`,
`servers/area/filter/playerFilter.js`, `servers/area/handler/{player,chat,...}Handler.js`, `servers/area/remote/{area,player,guild}Remote.js`,
`servers/manager/handler/chatHandler.js`, `servers/manager/remote/*.js`, `servers/{chat,trade,fight}/**`,
`domain/{messageService,persistent}.js`, `domain/area/{scene,area,areaManager,areaLogic,instance,instancePool,timer}.js`,
`domain/aoi/aoiEventManager.js`, `domain/map/{map,mobzone,itemzone,zone}.js`,
`domain/entity/{entity,character,player,mob,npc}.js`, `domain/action/{action,actionManager,move}.js`,
`ai/**`（14 文件）, `patrol/**`（6 文件）, `services/{areaService,chatService,teamManager,instanceManager,...}.js`, `modules/{onlineUser,sceneInfo}.js`

**pomelo/lib/**
`application.js`, `pomelo.js`, `util/{appUtil,pathUtil,moduleUtil,constants,events}.js`,
`components/{connector,remote,proxy,session,channel,pushScheduler}.js`,
`common/service/{handlerService,filterService,sessionService,channelService,connectionService}.js`,
`server/server.js`, `filters/handler/{timeout,serial}.js`, `filters/rpc/rpcLog.js`, `connectors/hybridconnector.js`, `pushSchedulers/direct.js`

**config/**
`servers.json`, `master.json`, `masterha.json`, `session.json`, `instance.json`, `scheduler.json`, `adminServer.json`,
`dictionary.json`, `clientProtos.json`, `serverProtos.json`, `data/*.json`, `map/mapEntity*.json`

**其他**
`lordofpomelo/README.md`, `lordofpomelo/LICENSE`, `lordofpomelo/pomelo/LICENSE`, `kongkongxiyou-master/README.md`, `game-server/package.json`
