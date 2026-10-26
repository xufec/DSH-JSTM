# 可借鉴点清单（reuse_candidates.md）

> 面向：《绝世唐门》1.4.9 私服兼容项目 **JSTM**（单进程 Python）
> 参照物：kongkongxiyou（空空西游）
> 结论标记：**【已确认】** / **【待验证】** / **【未知】**

---

# ★ 对 JSTM 的建议

## ★1. 值得借鉴的**设计思想**（按优先级排序）

### 第一梯队：直接决定 JSTM 骨架能不能立住（强烈建议照做）

| # | 设计思想 | 出处（kongkongxiyou） | 为什么对 JSTM 重要 | 落地形态（Python） |
|---|---|---|---|---|
| **B1** | **场景容器五层结构：`AreaManager → Scene/InstancePool → Instance → Area → (map/entities/zones/aoi/timer)`** | `app/domain/area/*` | 单进程要同时托管「多张大地图 + 若干副本 + 分线」，没有这层结构必然写成面条代码。这套层次经过作者在真实 MMORPG 规模上的使用，**且完全不依赖 Pomelo** | 5 个类，一一对应；`AreaManager` 持有 `scenes: dict[int, Scene]`、`players: dict[int, Player]`、`instance_pool` |
| **B2** | **100ms 主循环 + 分频子逻辑**（`%10 → 1s`、`>30 → 3s`） | `app/domain/area/timer.js` | 私服必须让「移动/AI/AOI」有确定的推进节奏；分频避免了每 tick 都跑重逻辑（城战状态机、BOSS 刷新、存档） | `asyncio` 定时任务或 `loop.call_later`；一个 tick 里按计数器分派 |
| **B3** | **AOI 双注册模型：`watcher`（有视野，参与感知）+ `object`（被看见，参与同步）** | `area.addEntity/removeEntity` | 这是 AOI 唯一正确的抽象。玩家/怪两者都注册；掉落物只做 object；NPC 不进 AOI | `aoi.add_watcher(wid, pos, range)` / `aoi.add_object(oid, pos)`，**严格区分两套索引** |
| **B4** | **AOI 4 事件契约：`add / remove / update / update_watcher`** | `domain/aoi/aoiEventManager.js`（且与 [pomelo-aoi 官方 README](https://github.com/NetEase/pomelo-aoi/blob/master/README.md) 完全一致【待验证】） | JSTM 自研 AOI 时，**照着这 4 个事件设计接口**就能直接复用所有业务侧的同步逻辑，省掉大量返工 | `on_add` / `on_remove` / `on_update` / `on_update_watcher` 回调表 |
| **B5** | **AOI 差量同步：`old_watchers` ∪ `new_watchers` 求双向差集，只推增删** | `aoiEventManager.onObjectUpdate`（< 40 行） | 网络开销正比于「视野变化量」而非「视野内实体数」。这是塔式 AOI 省流量的根本 | `old - new` → `onRemoveEntities`；`new - old` → `onAddEntities`；**Python set 差集更短** |
| **B6** | **AOI 结果 → 网络地址的唯一翻译点：`getWatcherUids(pos, types, ignore)` → `[{uid, sid}]`** | `domain/area/timer.js` | **AOI 绝不碰 socket**。「谁看得见」与「怎么发过去」彻底解耦，单进程/多进程都能用 | 一个函数返回 `[(uid, sid)]`，由 `message_service.push_by_uids` 统一投递 |
| **B7** | **出网「按受众分两条通道」**：定向推送收口到 `messageService`（单人/`ByUids`/`ByAOI`/Tips），频道广播走 `channel.pushMessage`；两者应再收敛到**同一个底层 `send()`** | `domain/messageService.js` + `area.getChannel()`/`Guilder.getChannel()`/`team.channel` | ① 定向推送集中一处便于加日志/统计；② 结构上为「推送即掉线检测」留了位置 | ❌ **参考项目这里坏了两处**：① 初版报告写的「唯一出口」是错的，实际有 20+ 处直接 `channel.pushMessage`；② `errHandler` 因 **uid/playerId 类型错配**（channelService 的 `failIds` 装的是 uid，`removePlayerByUid` 却查 playerId 键的 `players{}`）而**是空操作**，且只挂在定向通道上。JSTM 应：`MessageService.send_to(player,route,msg)` 与 `Channel.push_message(route,msg)` **共用同一个 `send()`**；失败回调携带 `player_id`；错误处理只写一次 |
| **B8** | **「客户端路径 + 服务端校验」的移动模型**（但**必须补校验**，见 ★2） | `handler.move` / `Map.verifyPath` | 面向 1.4.9 客户端协议，客户端大概率就是上传整条路径；**照抄「接受」的部分，必须自己补「校验」的部分** | 接受 path → `verify_path()` + 起点一致性 + 总位移/速度上限 + 每玩家限流 + 周期位置回执 |
| **B9** | **`Action` + `ActionManager` 把「行走」抽象为可中断对象（`singleton` 保证一实体一动作）** | `domain/action/*` | 移动/AI 追击/巡逻三处共用一套位置推进，避免三份重复逻辑 | `class MoveAction`；`action_manager.add/abort/abort_all/update` |
| **B10** | **服务端权威位置推进：按 `speed × Δt` 沿折线滑行，支持单 tick 跨多个路径点** | `action/move.js#update` | 不依赖固定 tick 间隔，抗抖动；是「服务端说了算」的前提 | 纯数学函数，30 行以内 |

### 第二梯队：显著提升开发效率与可维护性（建议照做）

| # | 设计思想 | 出处 | 价值 |
|---|---|---|---|
| **B11** | **`route` 字符串约定 `serverType.handlerName.methodName` + 「文件名即模块名、函数名即方法名」的零注册约定** | `pomelo/lib/server/server.js#parseRoute`、`handlerService.js`、`util/pathUtil.js` | JSTM 即使单进程，也建议保留「**协议名 = 模块.方法**」的字符串路由，理由：① 与旧客户端协议天然对齐；② 日后若要拆进程几乎零改动；③ 便于日志与限流按 route 统计 |
| **B12** | **handler 前置守卫（filter）：统一「取玩家 → 校验归属 → 注入 `session.player` → 异常时纠正客户端」** | `servers/area/filter/playerFilter.js` | 消除 13 个 handler 里的重复代码；异常时主动推 `onChangeArea` 让客户端自愈，**对协议不完整的老客户端尤其重要** |
| **B13** | **配置驱动的数据层 `dataApi`：`new Data('area')` 把「数组表」映射为「按字段名索引的对象表」，提供 `findById/findBy/findBigger/findSmaller/all`** | `util/dataApi.js` | 30 行实现，却是全项目 28 张配置表的统一访问口。JSTM 直接移植成 Python `DataTable` 类 |
| **B14** | **`forbid_word` 敏感词表 + 集中错误码表 `error_code.json` + 统一 Tips 推送（`onLogTips` / `onTipsBox`）** | `config/data/{forbid_word,error_code}.json`、`messageService.pushLogTipsToPlayer` | ① 错误码集中管理，前后端对齐；② 提示分「飘字」和「弹窗」两档，是 MMORPG 的刚需 |
| **B15** | **频道（Channel）抽象 + 频道命名规则：全局 `"pomelo"` / `area_<areaId>` / `team_<teamId>` / `guild_<guildId>`** | `util/channelUtil.js`、`services/chatService.js`、`pomelo/lib/common/service/channelService.js` | 单进程里用一个 `dict[str, set[uid]]` 就能实现；命名规则直接沿用，与「实例/队伍/公会」的三级社交结构天然对应 |
| **B16** | **聊天频道枚举 `{WORLD:1, AREA:2, FACTION:3, TEAM:4, PRI:5, SYSTEM:6, MARQUEE:7}` + 按频道分流** | `consts/consts.js`、`servers/manager/handler/chatHandler.js#send` | 枚举值应与 1.4.9 客户端协议对齐（**需核对**）；分流逻辑可直接翻译 |
| **B17** | **AI = 行为树（黑板 + 按名字注册 brain）+ 「先试、失败则调整再试」的 `TryAndAdjust` 范式** | `app/ai/**`（`tryAndAdjust.js`） | 行为树比状态机更易扩展；`TryAndAdjust = Select[try, Sequence[adjust, try]]` 这个组合节点可以用在「攻击/拾取/对话」全部场景。**JSTM 用 100 行 Python 就能实现 Select/Sequence/Loop/If/Node 五件套** |
| **B18** | **AI 与巡逻是两套互斥模块，可运行时切换（`timer.enterAI` / `timer.patrol`）** | `domain/area/timer.js` | 「怪出生先巡逻，被打/看到玩家切 AI，脱战回巡逻」是标准需求，用两个独立管理器 + 一个切换点表达最清晰 |
| **B19** | **怪物脱战边界：`\|x - spawnX\| > 500 或 \|y - spawnY\| > 500` 即 `forget_hater` 回家** | `ai/action/moveToTarget.js` | 防止怪被拉到大半个地图；实现只需一个 if |
| **B20** | **主动怪索敌由 AOI `add` 事件驱动（而非 AI 轮询全场）** | `aoiEventManager.onMobAdd/onPlayerAdd` | 避免每 tick 遍历全部怪做距离检测；**这是 AOI 存在的主要收益之一** |
| **B21** | **巡逻路径 = 随机游走 + 闭环（末点回填起点）** | `map.genPatrolPath` | 免手工配置路径点，配合 `Loop` 状态机（`rounds=-1`、`standTick=50`）即可无限巡逻 |
| **B22** | **副本 instanceId 命名即语义：`sin_`（单人）/`my_`（个人BOSS）/`team_`（队伍）/`fight_`（竞技）/`boss`（世界BOSS）** | `areaManager.gotoInstance` | 免去额外元数据；「谁和谁共享同一个副本」由 id 规则自解释 |
| **B23** | **空场回收 + 下线对象缓存（两个粒度）**：副本 `emptyTime > 5min` 回收；玩家对象下线后 60s 缓存供重登复用 | `instance.isAlive`、`areaManager.playerCaches` | 私服玩家频繁重连/掉线，60s 缓存能显著减少查库与对象重建。**注意参考项目的实现有 bug（见 ★2）** |
| **B24** | **`loadAreaResource`：进服先下发「本场景需要哪些资源（kindId 去重集合）」** | `servers/area/handler/resourceHandler.js` | 老客户端（1.4.9）在运行时缺资源会卡死，**进服预加载清单是刚需** |
| **B25** | **`strip()` 分层：`strip()`（给别人看）与 `playerStrip()`（给自己看）分开** | `domain/entity/{character,player,mob,npc}.js` | 解决「同步宽表」问题的直接办法：不同视角给不同字段集 |
| **B26** | **`handleRemote` 迁移适配层：把一个功能从 A 进程搬到 B 进程时，加一层薄转发，调用点零改动** | `consts/handleRemote.js`（把 chat RPC 全改指 manager） | **这是本审计中对 JSTM 最有价值的一条工程实践**：JSTM 从「多进程设计」落地为「单进程」，用同样手法可以把每个跨进程调用点逐个换成函数调用，重构风险极低 |
| **B27** | **DAO 层 + `dao/mapping/*Sync.js` 同步表 + `pomelo-sync-plugin` 定时脏刷** | `app/dao/**`、`app/dao/mapping/{player,bag,equipment,guild,task,...}Sync.js` | **「内存对象 + 脏标记 + 定时批量 UPDATE」**（而非每次操作都写库）是 MMORPG 存档的正确做法；JSTM 应自研等价的 `dirty_registry` + 定时 flush |
| **B28** | **玩家下线清理清单（顺序化、每步独立容错）** | `entryHandler.onUserLeave` | 可直接作为 JSTM 的 checklist：存档 → 退出场景（含 AOI/频道/仇恨清理）→ 公会 → 竞技 → 聊天 → 拍卖行 |
| **B29** | **登录顺序：`bind session → pushAll → 先回包 → 再补做跨系统注册`** | `entryHandler.entryPlayer` | 避免登录超时；附属注册失败不影响玩家进游戏 |
| **B30** | **容灾通道：允许客户端上报异常状态（`fixLeaveArea`），服务端做兜底清理** | `entryHandler.fixLeaveArea` | 面对协议不完整/客户端崩溃的老版本客户端，**「自愈接口」是私服的救命功能** |

### 第三梯队：运维与工程化（可选借鉴）

| # | 设计思想 | 出处 | 价值 |
|---|---|---|---|
| **B31** | admin 监控模块三段式 `monitorHandler/masterHandler/clientHandler` + `moduleId` 约定 | `app/modules/onlineUser.js` | 给 JSTM 做「在线数/场景状态」Web 面板的模板 |
| **B32** | 过滤器链 `befores[]` + `afters[]`（`afters` 用 `unshift` 保证逆序执行） | `pomelo/lib/common/service/filterService.js` | 中间件链的经典实现 |
| **B33** | 请求超时过滤器（记录 `setTimeout`，after 里 clear） | `pomelo/lib/filters/handler/timeout.js` | 排查「请求卡死」的必备工具（**但要真的中断/回收，不能只打日志**） |
| **B34** | 同 session 请求串行化（`taskManager`） | `pomelo/lib/filters/handler/serial.js` | Python 里用「每玩家 `asyncio.Lock`」更轻 |
| **B35** | 连接黑名单（正则数组 + 动态回调） | `pomelo/lib/components/connector.js#hostFilter` | 封 IP / 反外挂钩子 |
| **B36** | `reloadHandlers` 热重载 handler | `handlerService.watchHandlers` | 私服开发期改代码不重启（Python: `importlib.reload`） |
| **B37** | **`game-server_backup/` 本身**：作者保留了旧版快照，可看出「多进程 → 准单体」的演进路径 | `lordofpomelo/game-server_backup/**` | 做 JSTM 架构决策时，可对比新旧版本判断哪些抽象是必需的、哪些被作者自己抛弃了【待验证：需逐行 diff】 |

---

## ★2. 完全不能借鉴的（JSTM 是单进程 Python，没有 Pomelo）

### ★2.1 因「单进程」而整体作废

| 类别 | 具体文件/包 | 为什么不能借鉴 |
|---|---|---|
| **Pomelo 框架本体** | `lordofpomelo/pomelo/lib/**` 全部 94 个 js（`application.js`、`pomelo.js`、`server/server.js`、`components/*`、`connectors/*`、`common/service/*`、`master/*`、`modules/*`、`filters/*`、`pushSchedulers/*`、`util/*`） | JSTM 没有 Pomelo，也没有等价的分布式运行时。整个 `lib/` 只能作为**「分布式游戏服务器是怎么组织的」的读物**，不能作为实现蓝本 |
| **RPC 机制** | `pomelo/lib/components/{remote,proxy}.js`、`common/remote/**`、外部 `pomelo-rpc` | 跨进程 RPC 在单进程内是纯开销（序列化 + 网络 + 回调）。JSTM 应直接函数调用；**唯一保留的应是「调用点的命名习惯」**（`namespace.service.method`） |
| **跨进程转发** | `server/server.js#doForward`、`msgRemote.forwardMessage`、`session.export()` | 把整个 msg + session 快照发到另一进程；单进程下不存在 |
| **Session 的「副本 + pushAll」模型** | `common/service/sessionService.js`（`Session` / `FrontendSession` / `import/importAll/pushAll`）、`backendSessionService.js` | 「后端拿到的是 session 副本，改字段必须 push 才生效」是分布式特有的坑。JSTM 单进程里 session 就是普通对象，**但要注意：不要因此写出「多处持有同一 player 对象」的竞态，仍需单写入口** |
| **ChannelService 的跨进程广播** | `common/service/channelService.js`（`sendMessageByGroup`、`restoreChannel`、`addToStore/loadAllFromStore`、`genKey/genValue`） | 单进程下频道就是 `dict[str, set]`，直接遍历推送即可；**不需要按 sid 分组、不需要 store 持久化** |
| **连接与协议层** | `components/connector.js`、`components/connection.js`、`connectors/hybridconnector.js`、`connectors/hybrid/{switcher,tcpsocket,tcpprocessor,wsprocessor}.js`、`connectors/{sioconnector,siosocket,mqttconnector,udpconnector}.js`、`connectors/commands/{handshake,heartbeat,kick}.js`、`connectors/common/{coder,handler}.js` | 这套是 Pomelo 的混合 TCP/WS 协议实现。JSTM 面向 1.4.9 客户端，**协议必须按客户端来**，与 Pomelo 无关 |
| **服务发现与集群管理** | `components/master.js`、`master/{starter,watchdog,master}.js`、`modules/{masterwatcher,monitorwatcher}.js`、`util/{countDownLatch,moduleUtil}.js` | master 分发 servers.json、进程守护、跨机监控 —— 单进程统统不需要 |
| **高可用** | `config/masterha.json`、`scripts/createZKMasterhaNode.js`、外部 `node-zookeeper-client` / `pomelo-masterha-plugin` | 分布式高可用（本项目**已注释未启用**）。JSTM 的可用性靠「崩溃自动重启 + 存档一致性」解决 |
| **推送调度器** | `components/pushScheduler.js`、`pushSchedulers/{buffer,direct}.js` | 「合并 30ms 再发」是为跨进程 RPC 省开销；单进程直接 send 即可（**但「批量合并推送」的思想在万人同屏时仍值得保留**） |
| **消息字典 / protobuf** | `config/dictionary.json`（route → 数字）、`components/{dictionary,protobuf}.js`、`config/{clientProtos,serverProtos}.json` | `dictionary` 是为移动网络省流量；`useProtobuf:false` 本项目也没用。**除非 1.4.9 客户端强制要求，否则不引入** |
| **RSA 加密通道** | `components/connector.js#setPubKey/verifyMessage`、外部 `node-bignumber`、`useCrypto` | 未启用；即使启用也不该照抄 |

### ★2.2 因「实现有缺陷」而**绝对不能照抄**（即使单进程也需要同类功能，也必须重写）

| # | 反模式（有源码证据） | 出处 | 风险 | JSTM 正确做法 |
|---|---|---|---|---|
| **N1** | **完全信任客户端上传的移动路径**；`Map.verifyPath` 定义了但**全项目 0 处调用** | `handler.move`（`var path = msg`）、`map.js` | 穿墙 / 瞬移 / 加速 / 拉怪 | 每次 move 都校验（点可达 + 相邻直线可达 + 起点一致 + 总位移上限 + 限速 + 限流） |
| **N2** | `handler.getEntity` 按 id 直接返回任意实体数据，**无可见性校验** | `playerHandler.getEntity` | 透视全服 / 枚举实体 | 校验目标在自身 AOI 范围内 |
| **N3** | `AreaManager.clearPlayerCaches` **边写边全清**：刚 put 进缓存就被清空，且把对象字段全部 `delete` | `areaManager.js` | 缓存失效 + 外部持有的引用变成空对象 | 真正的 TTL/LRU 缓存，过期才删 |
| **N4** | `getPlayerWithPlayerIdCb` 用字符串 `'waiting'` 表示并发冲突，调用方当致命错误处理 | `areaManager.js` + `playerFilter.js` | 高并发首登偶发失败 | `asyncio.Lock` 等待而非拒绝 |
| **N5** | `PathCache.addPath` 的 LRU 淘汰：`this.queue.pop().key` 可能 `undefined`；循环内 `delKey = this.queue.pop()` **漏了 `.key`** | `util/pathCache.js` | 抛异常崩溃 | `OrderedDict` 或 `heapq` + 惰性删除，配单元测试 |
| **N6** | `PathCache.comparator` 返回布尔值 `a.time < b.time` 交给优先级队列 | `util/pathCache.js` | LRU 可能退化（比较语义【待验证】） | 用明确的 `(timestamp, key)` 元组排序 |
| **N7** | `Map._testLine` 用 `this.tileW` 计算 y 方向的 tile 行 | `map.js` | `tileW ≠ tileH` 时判定错误 | 分别用 `tileW` / `tileH` |
| **N8** | `Map.isReachable` 用 `weight === 1` 严格判定 | `map.js` | 无法支持减速/沼泽地形（非 1 的权重一律不可走） | `weight < INF` 判定，权重参与 A* 代价 |
| **N9** | `Map.checkPoint` 为了验证「点是否可达」**跑完整 `findPath`** | `map.js` | 刷怪/巡逻频繁触发 A* | 轻量检查（直线可达 / 距离阈值） |
| **N10** | `findPath(..., useCache)` 默认 `false`，玩家侧几乎不写缓存 | `map.js` + `character.move` | A* 重复计算 | 默认开启缓存 |
| **N11** | `compressPath1` 用 `j += 2` 跳跃式拉直 | `map.js` | 非最优路径（多绕路） | 标准射线拉直 / 漏斗算法 |
| **N12** | `getAreaInfoStrip(player, player.range)` 与签名 `(pos, range)` 不符；`pushMessageByAOI(area,route,msg,this)` 与 `(area,route,msg,pos,ignoreList)` 不符 | `area.js` / `character.move` | 靠鸭子类型侥幸工作，一旦 `pos` 被用于塔查询就会错 | 显式传 `(x, y)` 或 `Pos` 对象；加类型注解/断言 |
| **N13** | 用 `opts.level` 是否存在来区分 `MobZone` / `ItemZone` | `area.js#initMobZones` | 加字段即崩 | 显式 `type` 字段 |
| **N14** | `AreaManager.getBossGenTimes` 硬编码场景号 `6001..6005` | `areaManager.js` | 加地图要改代码 | 配置化 |
| **N15** | AOI 的 `towerWidth/towerHeight` 硬编码 300 | `area.js` | 大地图/小地图同一粒度 | 按地图尺寸与预期密度自适应，并暴露为配置 |
| **N16** | `removeEntity` 里 **MOB 的 `remove` 事件分支被注释掉** | `aoiEventManager.js` | 怪物消失的同步覆盖不全（靠 `area.tick` 里 items 兜底） | 补齐所有类型的 remove 分支 |
| **N17** | 敏感词判据 `searchIndex > 0`（位置 0 命中会漏检）；`checkForbid` 每词只替换第一处 | `roleHandler.createPlayer`、`manager/handler/chatHandler.js` | 敏感词漏过 | `>= 0` + 循环替换 + AC 自动机 |
| **N18** | `utils.myPrint` 的 `isPrintFlag = true` **硬编码**，且用 `Error.prepareStackTrace` 取调用栈 | `util/utils.js` | 生产环境全量 console.log + 每行日志构造异常栈 → 性能与日志双爆 | 用标准 logging，级别可配，**禁止在热路径打日志** |
| **N19** | `uncaughtException` 只 `console.error` 不退出 | `app.js` 末尾 | 进程带病运行、状态不一致 | 记录后**优雅下线/重启**，或至少标记为「不可信状态」 |
| **N20** | 两套 `changeArea` 实现并存（`AreaManager.changeArea` 与 `AreaService.changeArea`），只有一套被调用 | `areaManager.js` / `areaService.js` | 维护陷阱、改错地方 | 删掉死代码 |
| **N21** | `handler.stop` 里 `setIsMoving(true)` 后立刻中止移动；`isStop` / `isMoving` 语义混乱 | `playerHandler.stop`、`character.stand` | 状态难追踪 | 明确的 `MoveState` 枚举 + 单一状态机 |
| **N22** | 管理端 SYSTEM 频道的 `@1|...` 命令是**内置发奖后门**（直接发 9001×100 + 6101×1 邮件） | `manager/handler/chatHandler.js#send` | 任意玩家可能触发（取决于客户端能否发 SYSTEM 频道） | 显式权限校验 + 独立管理通道 |
| **N23** | `instancePool.check` 回收实例要跨进程问 manager | `instancePool.js` | 单进程下纯浪费 | 本地回收 |
| **N24** | `map.init` 用 `process.cwd()` 拼地图路径 | `map.js` | 必须在特定目录启动 | 基于配置根解析 |
| **N25** | `AreaManager.gotoScene/gotoInstance` 静默改写 `player.areaId = 1001` 等兜底 | `areaManager.js` | 掩盖数据问题 | 记警告 + 上报 + 落库，不静默 |
| **N26** | 玩家实体清理时把字段全 `delete`（`for key in e: delete e[key]`），`area.close` 里也把 self 掏空 | `area.js`、`areaManager.clearPlayerCaches` | JS 手工 GC 土办法，易造成悬挂引用 | Python 靠解除引用 + `weakref`，不要手动清字段 |
| **N27** | `handler.move/clMove` **无限流**，且每 tick 都要更新 AOI | `playerHandler.js` | 恶意客户端可打爆主循环 | 每玩家限流 + AOI 更新节流（如每 N tick 或位移超过阈值才更新） |
| **N28** | 无任何寻路/AOI 性能埋点 | `map.js`、`aoiEventManager.js` | 无法调优、无法发现退化 | 记录 A* 次数/耗时 P95、缓存命中率、单塔实体数、差集大小、群推人数分布 |

### ★2.3 参考项目「本身就没有的东西」（JSTM 必须自研，别指望能借鉴）

| 缺什么 | 证据 | JSTM 必须自研 |
|---|---|---|
| **AOI 算法本体** | `pomelo-aoi` 未随 ZIP 打包；`pomelo/lib` 里 `aoi` 0 命中 | 塔式（或四叉树/网格）AOI 的完整实现 |
| **A* 算法本体** | `pomelo-pathfinding` 未打包 | 4 向/8 向 A* + 开放列表 + 启发函数 |
| **行为树运行时** | `pomelo-bt` 未打包（只见到使用 `Sequence/Select/Loop/If/Node`） | 极简行为树（约 100 行 Python） |
| **优先级队列** | `pomelo-collection` 未打包 | `heapq` |
| **定时脏刷落库** | `pomelo-sync-plugin` 未打包（只剩 `dao/mapping/*Sync.js` 表结构，这半份是有的） | `dirty_registry` + 定时 flush |
| **网络协议栈** | 依赖客户端 1.4.9 协议 | 必须根据 JSTM 目标客户端逆向/实现 |
| **数据库设计与迁移** | `config/schema/Pomelo.sql`（18.8 KB）在，但对应的是**空空西游的数据模型**，与《绝世唐门》1.4.9 不同 | 需按目标客户端重新设计 |
| **客户端预测/回滚** | `cocosjs/` 未审计【未知】 | 需先确认客户端行为 |

---

## ★3. 许可问题：**kongkongxiyou 没有项目级 LICENSE ⇒ 只能借鉴设计，绝不能复制代码**

### ★3.1 事实核验（本次做了全 ZIP 文件名 + 内容扫描）【已确认】

| 位置 | 有无 LICENSE | 内容 |
|---|---|---|
| **`kongkongxiyou-master/` 根目录** | ❌ **无任何 LICENSE / COPYING / NOTICE 文件** | —— |
| `kongkongxiyou-master/README.md`（根） | ⚠️ 有**口头授权声明**，非正式许可 | 原文：「本项目完全由我一个人完成，**授权大家随便使用该项目**。使用和转发需要注明博客地址。教程：http://blog.csdn.net/linyouhappy」 |
| `lordofpomelo/LICENSE` | ✅ 有 | **(The MIT License) Copyright (c) 2012-2013 Netease, Inc. and other pomelo contributors** —— **继承自上游 lordofpomelo**，覆盖的是 **Pomelo 框架与 lordofpomelo demo 部分**，不覆盖作者的原创业务代码 |
| `lordofpomelo/pomelo/LICENSE` | ✅ 有 | 同上（MIT, Netease） |
| `lordofpomelo/README.md` | ✅ 内含 License 段 | MIT（Netease 2012-2013） |
| `pomelo-admin-web/LICENSE` | ✅ 有 | 第三方（运维面板） |
| `pomelo-admin-web/public/ext-4.0.7-gpl/license.txt` | ⚠️ **GPL** | ExtJS 4.0.7 的 GPL 许可 —— **GPL 具有传染性，绝不能把 ExtJS 代码并入 JSTM** |
| `cocosjs/frameworks/cocos2d-x/licenses/`（30 个 LICENSE_*.txt） | ✅ 有 | cocos2d-x 及 20+ 第三方库许可（box2d、chipmunk、libpng、lua、spine 等），**均为客户端依赖** |
| 其余 22486 个文件中 | 无项目级许可 | 全库（排除 node_modules）符号许可文件共 34 个，**全部是第三方依赖自带** |

### ★3.2 结论与红线

> ### ★ **kongkongxiyou 项目自身（作者原创的客户端 + 服务端业务代码）没有任何正式 LICENSE 文件。**
> ### 仓库里能找到的许可**全部是第三方继承而来**：Pomelo / lordofpomelo 的 MIT（NetEase）、cocos2d-x 及其依赖的各类许可、pomelo-admin-web 与 ExtJS（**GPL**）。
> ### 作者在 README 里写的「授权大家随便使用该项目」**只是口头/博客声明，不是可依赖的正式许可文本**（无授权主体、无范围、无免责、无版本）。
>
> ## ⇒ **JSTM 的硬性红线（三条）**
>
> | # | 红线 | 说明 |
> |---|---|---|
> | **R1** | **绝不复制任何一行业务代码** | 无论是 `game-server/app/**`（作者原创，无许可）、`lordofpomelo/**`（MIT 但仅覆盖上游部分、且是 JS）、还是 `cocosjs/**`（客户端）。**服务端一律不看源码写 Python，只看设计。** |
> | **R2** | **绝不复制任何数据表/配置/数值/资源** | `config/data/*.json`（策划数值）、`config/map/mapEntity*.json`（地图碰撞）、`characterRes/`、`plistbuild/`、`ccsbuilder/`、`spriteSheets/` 等**都是作者（或版权方）的资产**。《绝世唐门》1.4.9 的资源与数值应来自 JSTM 自己的合法来源 |
> | **R3** | **绝不引入 GPL 传染源** | `pomelo-admin-web/public/ext-4.0.7-gpl/`（ExtJS, GPL）。若 JSTM 需要 Web 面板，**不要把 ExtJS 代码并进项目**；用独立服务或换成宽松许可的前端框架 |
>
> ## 允许的做法
>
> | ✅ 允许 | 说明 |
> |---|---|
> | **借鉴设计思想、架构分层、算法思路** | 本文件 ★1 的 37 条全部属于「思想」，可以自由使用。**思想不受版权保护**（版权保护表达，不保护思想/方法/系统） |
> | **在 JSTM 自己的代码与文档里注明「设计参考自 kongkongxiyou（作者 linyouhappy，无正式许可，仅作设计参考）」** | 学术/工程上的诚实做法，也呼应作者 README 里「使用和转发需要注明博客地址」的诉求 |
> | **独立实现同类功能** | 如自研塔式 AOI、自研 A*、自研行为树，**用 Python 从零写**，不与参考实现产生代码级相似 |
> | **把 kongkongxiyou 当作「行为规格说明书」使用** | 例如「怪物脱战距离 500」「副本空场 5 分钟回收」「塔格 300」这类**数值参数**可以作为设计起点，但要在 JSTM 里明示这是**参考值，需按项目实测调整** |
>
> ## 建议动作（合规留痕）
>
> 1. 在 JSTM 仓库放一份 `THIRD_PARTY_NOTES.md`，声明：「本项目在架构设计上参考了开源项目 kongkongxiyou（https://github.com/linyouhappy/kongkongxiyou）。该项目根目录未提供正式 LICENSE；参考项目内的 Pomelo / lordofpomelo 部分为 NetEase MIT 许可，cocos2d-x 相关为其各自第三方许可，pomelo-admin-web 的 ExtJS 部分为 GPL。**本项目未复制其任何源代码、数据表或美术资源，仅借鉴设计思想。**」
> 2. 如果 JSTM 未来需要直接使用 Pomelo 或 lordofpomelo 的**任何代码**，**只应直接从上游 NetEase 仓库获取并保留其 MIT 版权声明**，不要经由 kongkongxiyou 转发（避免权利链不清）。
> 3. 本审计报告自身也**不含**参考项目的源码片段（引用均为必要的接口签名与少量表述，用于说明机制）。

---

# 附：完整可借鉴点清单（表格汇总）

> 列定义：**文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因**
> 「文件路径」以 `kongkongxiyou-master/` 为根。

## A. 架构与框架层

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `lordofpomelo/game-server/app.js` | `app.configure(env,type,fn)` × 10 段 | 唯一装配点：按 serverType 注册组件/服务/过滤器/路由 | ⚠️ 部分适合 | **「显式装配表」思想适合**（JSTM 用一个 `bootstrap.py` 按环境注册子系统）；`app.configure` 本身不适合（无 Pomelo） |
| `.../app.js` | `app.route('area', routeUtil.area)` | 覆盖 RPC 路由函数 | ❌ 不适合 | 跨进程路由 |
| `.../app.js` | `app.set('areaIdMap', ...)` | 建立「场景 id → 服务器 id」映射 | ✅ 思想适合 | 单进程可退化为「场景 id → Scene 对象」的注册表 |
| `.../app.js` | `app.use(sync, {path: dao/mapping, dbclient})` | 挂载 pomelo-sync-plugin 定时脏刷 | ✅ 思想适合 | 「脏标记 + 定时批量落库」必做；插件本身不可用 |
| `.../app.js` | `app.registerAdmin(onlineUser, {app})` | 注册运维监控模块 | ✅ 适合 | 三段式监控模块可作 JSTM 运维面板模板 |
| `lordofpomelo/pomelo/lib/util/pathUtil.js` | `getHandlerPath/getUserRemotePath/getCronPath` | 目录约定即注册 | ✅ **思想强适合** | 「目录约定 + 自动装载」在 Python 用 `pkgutil`/`importlib` 复刻，能省大量注册样板代码 |
| `lordofpomelo/pomelo/lib/server/server.js` | `parseRoute(route)` | `type.handler.method` 三段式 | ✅ **强适合** | 保留该协议名格式，与老客户端对齐且便于限流/统计 |
| 同上 | `Server.prototype.globalHandle` / `doHandle` | 全局过滤器 → 目标判断 → doForward / doHandle；`msg = msg.body`，注入 `msg.__route__` | ⚠️ 部分 | **「信封与 body 分离 + 注入 route」适合**；`doForward` 不适合 |
| 同上 | `doForward` | `sysrpc[type].msgRemote.forwardMessage(session,msg,session.export())` | ❌ 不适合 | 跨进程转发 |
| `lordofpomelo/pomelo/lib/common/service/handlerService.js` | `handle / getHandler / loadHandlers / watchHandlers` | 懒加载 handler 表 + 可选 `fs.watch` 热重载；handler 是「每 serverType 一份实例」 | ✅ 部分适合 | 热重载适合（`importlib.reload`）；**「共享实例有状态」是隐患，JSTM 应无状态化** |
| `lordofpomelo/pomelo/lib/common/service/filterService.js` | `before/after/beforeFilter/afterFilter` | 前链 `push`、后链 `unshift`；`next(err,resp,opts)` | ✅ **强适合** | 中间件链经典实现，Python 装饰器/生成器可平移 |
| `lordofpomelo/pomelo/lib/filters/handler/timeout.js` | `Filter.before/after` | `setTimeout` 记录 `session.__timeout__`，after 清除 | ✅ 思想适合 | 必备可观测性；**但必须真中断，不能只 warn** |
| `lordofpomelo/pomelo/lib/filters/handler/serial.js` | `Filter.before/after` | `taskManager.addTask(session.id, ...)` 串行化同 session 请求 | ⚠️ 部分 | Python 用「每玩家 asyncio.Lock」更合适 |
| `lordofpomelo/pomelo/lib/filters/rpc/rpcLog.js` | `Filter.before/after` | 记录 RPC 耗时 | ❌ 不适合 | 无 RPC；但**「耗时埋点」思想适合** |
| `lordofpomelo/pomelo/lib/util/moduleUtil.js` | `loadModules/registerDefaultModules` | admin 模块装载 | ⚠️ 部分 | 思路可借鉴，实现依赖 pomelo-admin |
| `lordofpomelo/game-server/app/modules/onlineUser.js` | `monitorHandler/masterHandler/clientHandler` | 各前端上报连接统计 → master 聚合 → 控制台读取 | ✅ 思想适合 | JSTM 运维面板模板 |
| `lordofpomelo/game-server/app/modules/sceneInfo.js` | 同上 | 场景状态上报（**本项目注册被注释**） | ✅ 思想适合 | 同上 |
| `lordofpomelo/game-server/app/consts/handleRemote.js` | `chatRemote_add/_kick/_readMail/_pushWorld/_pushMarquee` | 薄转发层，把 chat RPC 全改指 manager | ✅ **★ 强适合** | **迁移适配层**：JSTM 从多进程设计收敛到单进程时，用同样手法逐点替换，风险极低 |
| `lordofpomelo/game-server/app/util/dispatcher.js` | `dispatch(uid, connectors)` | `uid % n` 取模 | ⚠️ 部分 | 单进程不用；若未来多进程应改一致性哈希（crc 版本已被作者注释） |
| `lordofpomelo/game-server/app/util/routeUtil.js` | `exp.area` / `exp.connector` | 路由函数只读 session 上的 `serverId` / `frontendId` | ✅ **强适合** | **「玩家归属记在 session，路由只读」**是正确的归属模型，单进程也可用来做「分线」 |
| `lordofpomelo/game-server/app/servers/gate/handler/gateHandler.js` | `queryEntry` | 返回 `{host, port}`；host 用本机非 loopback IP | ⚠️ 部分 | 「入口握手」思路适合；IP 探测逻辑不适合（多网卡/容器会错） |
| `lordofpomelo/game-server/app/servers/connector/handler/entryHandler.js` | `entry` | token → authRemote.auth → 查角色列表 → 返回选角数据 | ✅ **强适合** | 登录三步流程可直接照搬（token 可简化为 HMAC） |
| 同上 | `entryPlayer` | kick 同账号 → bind → 读角色 → 写 session → `on('closed')` → `pushAll` → **回包后再做 chat/guild 注册** | ✅ **★ 强适合** | 「先回包，后补副作用」避免登录超时；顺序化下线清理 |
| 同上 | `onUserLeave` | 依次清理 area/guild/fight/chat/trade，每步独立容错 | ✅ **★ 强适合** | 直接作为 JSTM 的下线 checklist |
| 同上 | `fixLeaveArea` | 客户端上报异常 → 服务端兜底清理 | ✅ **强适合** | 私服兼容老客户端的救命功能 |
| `lordofpomelo/game-server/app/servers/connector/handler/roleHandler.js` | `createPlayer` | 敏感词检查 → 查重 → 建号 → 建主线任务 + 初始技能 | ⚠️ 部分 | 流程适合；**敏感词判据 `> 0` 是 bug** |
| `lordofpomelo/game-server/app/servers/auth/remote/authRemote.js` | `auth` / `checkExpire` | token 解析 + `expire < 0` 表示永不过期 | ✅ **强适合** | 极简可照搬；**建议 JSTM 设正数 expire** |
| `lordofpomelo/game-server/app/servers/area/filter/playerFilter.js` | `Filter.before` | 统一取玩家 → 校验场景归属 → 注入 `session.player` → 异常推 `onChangeArea` | ✅ **★ 强适合** | handler 前置守卫范例 |

## B. 场景与 AOI 层

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `.../app/domain/area/areaManager.js` | `AreaManager` 构造器 | 维护 scenes/players/playerCaches/instances/instancePool/requestList 六容器 | ✅ **强适合** | 容器设计清晰，Python 平移 |
| 同上 | `initScenes(areaIds)` | 配置驱动建场景 | ✅ | — |
| 同上 | `getCanUsedPlayer` | 两级缓存（在线 → 下线缓存提升） | ✅ 强适合 | 私服重连频繁，省查库 |
| 同上 | `getPlayerWithPlayerIdCb` | 占位防并发 + 查库 + `addPlayer` | ⚠️ 部分 | 思路适合；**`'waiting'` 字符串当错误会导致首登偶发失败** |
| 同上 | `addPlayerCaches` / `clearPlayerCaches` | 60s 下线缓存 | ❌ 不适合 | **实现有 bug（边写边全清 + 掏空对象）**，JSTM 需重写为真 TTL 缓存 |
| 同上 | `getAreaWithPlayer` | 先按 areaId，再按 instanceId，失败回退 1001 | ⚠️ 部分 | 兜底思路好，**静默改写玩家数据不好** |
| 同上 | `changeArea` | 按区域 type 分派 gotoScene / gotoTeamInstance / gotoInstance | ✅ **强适合** | 单一分派点，清晰 |
| 同上 | `gotoScene` | exitArea → 算落点（支持传送点反转）→ 改玩家坐标 → save | ✅ **强适合** | 传送点方向反查是亮点 |
| 同上 | `gotoInstance` | 按 areaKind 生成 instanceId 命名规则 | ✅ **★ 强适合** | **instanceId 命名即共享域**，语义自解释 |
| 同上 | `getBossGenTimes` | 硬编码 6001..6005 | ❌ 不适合 | 场景号硬编码 |
| `.../app/domain/area/scene.js` | `Scene.init` | 取全服共享 Map → `new Area(map)` | ✅ **★ 强适合** | **Map 共享、Area 各自持有**是内存优化关键 |
| `.../app/domain/area/instance.js` | `isAlive` | 空场超 `lifeTime=300000` 即回收 | ✅ **强适合** | 副本回收策略 |
| `.../app/domain/area/instancePool.js` | `init/check/create/remove` | `setInterval(check, 60000)`；回收要跨进程问 manager | ⚠️ 部分 | 回收思路适合；**跨进程问 manager 不适合** |
| `.../app/domain/area/timer.js` | `run/tick` | 100ms 主循环 + `%10`→1s + `>30`→3s | ✅ **★ 强适合** | 单进程最优 tick 分层 |
| 同上 | `enterAI` / `patrol` | AI 与巡逻互斥切换 | ✅ **强适合** | 怪物状态机简洁表达 |
| 同上 | `getWatcherUids(pos,types,ignoreList)` | AOI 查询结果 → `[{uid,sid}]` | ✅ **★ 强适合** | AOI 与网络的唯一接缝 |
| 同上 | `updateObject` / `updateWatcher` | 转发到 aoi | ✅ | — |
| `.../app/domain/area/area.js` | `Instance(map, instanceId)` | 世界组装根：map/entities/players/zones/channel/aoi/ai/patrol/action/timer/areaLogic | ✅ **★ 强适合** | 结构值得照搬；tower 尺寸硬编码需改 |
| 同上 | `enterArea` / `exitArea` | 先 `abortAllAction` 再进/出 | ✅ **强适合** | 防残留动作 |
| 同上 | `tick()` | items → actions → AI → patrol，顺序固定 | ✅ **强适合** | 顺序有讲究（动作先于 AI） |
| 同上 | `updatePlayers()` | 超时踢人 + 实体 update | ✅ **强适合** | 心跳超时踢人集成在主循环 |
| 同上 | `start()` | 幂等 → 挂 AOI 事件 → 刷怪 → 建 NPC → 起 AI → 起 tick | ✅ **★ 强适合** | **启动顺序至关重要** |
| 同上 | `getChannel()` | 懒创建 `area_<instanceId>` / `area_<areaId>` 频道 | ✅ **强适合** | 频道命名规则可用 |
| 同上 | `addEntity` | PLAYER/MOB → `channel.add` + `aoi.addWatcher`；ITEM/EQ → 只进 items；NPC → 直接 return；末尾统一 `aoi.addObject` | ✅ **★ 强适合** | **watcher/object 双注册模型** |
| 同上 | `removeEntity` | 关系表 → AI/巡逻/动作 → 双向 forget → `aoi.removeWatcher(range+1)` → 索引 → `aoi.removeObject` | ✅ **★ 强适合** | 清理顺序值得照抄 |
| 同上 | `getAreaInfo` / `getAreaInfoStrip` / `getEntitiesByPos` | AOI 快照（strip 版额外塞全部 NPC）/ 按类型范围查询 | ⚠️ 部分 | 思路适合；**参数与签名不符** |
| `.../app/domain/aoi/aoiEventManager.js` | `addEvent(area, aoi)` | 注册 4 个事件 → 按 EntityType 分派 | ✅ **★ 强适合** | AOI 事件契约核心 |
| 同上 | `onPlayerAdd` / `onMobAdd` / `onItemAdd` | 推 `onAddEntities`；主动怪索敌；**顺手清理失效 watcher** | ✅ **★ 强适合** | 含自愈机制 |
| 同上 | `onPlayerRemove` / `onMobRemove` | 推 `onRemoveEntities`（**MOB 分支被注释**） | ⚠️ 部分 | 需补齐 MOB remove |
| 同上 | `onObjectUpdate` | **old/new watchers 双向差集** → 复用 add/remove | ✅ **★★ 最值得借鉴** | AOI 差量同步的核心 |
| 同上 | `onPlayerUpdate` | 直接推 remove/add；`tower.removeById` 脏数据回写 | ✅ **强适合** | 观察者视野差集 + 回写 |
| `.../app/domain/messageService.js` | `pushMessageByAOI` / `pushMessageByUids` / `pushMessageToPlayer` | **定向推送**出口（**不是唯一出口**：另有 20+ 处直接 `channel.pushMessage`，见 B7 勘误） | ✅ **★ 强适合** | 定向推送集中一处；**JSTM 应把它与频道广播收敛到同一个底层 `send()`** |
| 同上 | `errHandler` | 意图「推送失败 → 从场景移除该玩家」，但**实际是空操作**：`channelService` 的 `failIds` 装的是 **uid**，`removePlayerByUid` 查的是 **playerId** 键的 `players{}` ⇒ 必然查不到、静默返回；且只挂在定向通道，频道广播的失败无人处理 | ❌ **不能照抄** | 思想（推送即掉线检测）值得做，但**参考实现是坏的**。JSTM 必须自己写，并显式区分 uid / player_id |
| 同上 | `pushLogTipsToPlayer` / `pushTipsBoxToPlayer` | 错误码 → 飘字/弹窗 | ✅ **强适合** | MMORPG 刚需 |
| `.../app/servers/area/handler/playerHandler.js` | `enterScene` | 校验 → 校正出生点 → AOI 快照 → addEntity → 返回完整场景数据 | ✅ **★ 强适合** | **快照在 addEntity 之前**的顺序要保留 |
| 同上 | `changeArea` | 组装 args → `areaManager.changeArea` | ✅ | — |
| 同上 | `move` / `clMove` | 客户端路径 → Move action → 广播 | ❌ **不可照抄** | **完全信任客户端路径** |
| 同上 | `stop` | abort MOVE + stand | ⚠️ 部分 | `isMoving` 语义混乱 |
| 同上 | `getEntity` | 按 id 直接推实体数据 | ❌ 不适合 | 无可见性校验（透视） |
| 同上 | `getProperty` | 内存/库查他人属性+装备 | ⚠️ 部分 | 同样缺可见性校验 |
| 同上 | `npcTalk` / `revive` / `fightMode` | NPC 对话 / 复活 / 战斗模式 | ✅ | 简单直接 |
| `.../app/servers/area/handler/resourceHandler.js` | `loadAreaResource` | 统计本场景需要的 kindId 集合下发 | ✅ **★ 强适合** | 老客户端资源预加载刚需 |
| `.../app/services/areaService.js` | `init/getMap` | 为每个 area 建一个 Map，全服共享 | ✅ **强适合** | 内存优化 |
| 同上 | `getInitPoint` | 传送点数据 + 来源反转 | ✅ **强适合** | 双向传送不出错 |
| 同上 | `gotoScene/gotoInstance/gotoTeamInstance/changeArea` | **旧实现，与新 `areaManager.*` 并存** | ❌ 不适合 | 死代码，不要照抄 |

## C. 寻路层

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `.../app/domain/map/map.js` | `init` | 读 `mapEntity<pathId>.json`；建 weightMap / pathCache / pfinder | ✅ **强适合** | 双坐标体系；**`process.cwd()` 拼路径需改** |
| 同上 | `getWeightMap` | 碰撞按列压缩 `[startY,length]` → 网格标 Infinity | ✅ **★ 强适合** | 内存/构建成本极低 |
| 同上 | `forAllReachable` | 4 邻域回调，带权重 | ✅ **强适合** | A* 解耦干净 |
| 同上 | `isReachable` | 世界坐标 → tile → `weight === 1` | ⚠️ 部分 | 应改 `weight < INF` 以支持减速地形 |
| 同上 | `_checkLinePath` / `_testLine` | 直线采样可达性 | ✅ 部分 | **直线快路径价值极大**；`_testLine` 有 tileW/tileH 混用 bug |
| 同上 | `findPath` | 越界→可达性→直线快路径→缓存→A*→转坐标→两级压缩 | ✅ **★ 强适合** | 流程正确；**`useCache` 默认 false 是缺陷** |
| 同上 | `compressPath2` | 去共线点 | ✅ **强适合** | 15 行显著减点 |
| 同上 | `compressPath1` | `j += 2` 跳跃拉直 | ⚠️ 部分 | 思路对，实现非最优 |
| 同上 | **`verifyPath`** | 点可达 + 相邻直线可达 | ✅ **★ 强适合（但本项目 0 调用）** | **JSTM 必须调用它** |
| 同上 | `getBornPoint` / `generatePoint` / `genPos` | 矩形内随机 + 可达重试（上限 10） | ✅ 强适合 | 标准做法 |
| 同上 | `genPatrolPath` / `genRandomPoint` | 随机游走 + 闭环；递归重试上限 10 | ✅ 强适合（递归可改迭代） | 免手工路径点 |
| 同上 | `checkPoint` | **可达性判断里跑完整 findPath** | ❌ **性能陷阱** | 刷怪时反复触发 A* |
| `.../app/util/pathCache.js` | `PathCache` / `getPath` / `addPath` / `genKey` | 起终点对为 key 的 LRU（limit=1000） | ✅ 思想强适合 | **LRU 实现有崩溃 bug，比较语义可疑** ⇒ 重写 |
| `.../app/domain/entity/character.js` | `move(x,y,useCache,cb)` | 服务端 findPath → Move action → AOI 广播 | ✅ **强适合** | 服务端自算路径的正确形态（**实参数量与形参不匹配**） |
| `.../app/domain/action/move.js` | `Move(opts)` | `singleton=true`、`path`、`speed`、`index=1` | ✅ **强适合** | 一实体一移动动作 |
| 同上 | `update(currentTime)` | 按 `speed*Δt` 沿折线滑行（可跨多节点）→ 更新坐标 → AOI 双更新 | ✅ **★ 强适合** | 无状态插值，抗抖动 |
| 同上 | `stopMove` | 广播 `onStand` | ⚠️ 部分 | `isMoving` 语义混乱 |
| `.../config/map/mapEntity*.json` | 数据文件（22 份） | collisions(列压缩) / collision / mob / npc / birth / transport | ✅ 思想适合 | **「地图是数据不是代码」必须继承**；**具体数据不可复制（版权）** |

## D. AI 与巡逻层

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `.../app/ai/ai.js` | `createManager(opts)` | `fs.readdirSync(brain)` 自动注册 brain；每 Area 一个 AiManager | ✅ **强适合** | 「目录扫描自动注册 AI 类型」在 Python 用 `pkgutil.iter_modules` 复刻 |
| `.../app/ai/service/aiManager.js` | `addCharacters/removeCharacter/update` | 分 players/mobs 两组存 brain，`update` 逐个 `brain.update()` | ✅ **强适合** | 结构简单清晰 |
| `.../app/ai/service/brainService.js` | `getBrain(type,bb)` / `registerBrain` | **`type` 非 `autoFight`/`player` 一律当 `tiger`**；`brain.clone({blackboard})` | ⚠️ 部分 | 注册表机制适合；**「所有怪共用一套脑」是偷懒，JSTM 应支持多脑** |
| `.../app/ai/meta/blackboard.js` | `Blackboard.create(opts)` | `{manager, area, curCharacter}` + 运行期字段 | ✅ **强适合** | 黑板是行为树的标准配套 |
| `.../app/ai/brain/tiger.js` | `Brain` | `Select[ If(有目标)→Loop(TryAndAdjust{MoveToTargetForAttack, TryAttack}), If(无目标)→Patrol ]` | ✅ **强适合** | 怪物 AI 的标准骨架 |
| `.../app/ai/brain/player.js` | `Brain` | `Select[ 攻击If, 拾取If(TryPick), 对话If(TryTalkToNpc) ]` | ✅ 强适合 | 挂机 AI 骨架 |
| `.../app/ai/node/tryAndAdjust.js` | `Node` | `Select[ tryAction, Sequence[ adjustAction, tryAction ] ]` | ✅ **★ 强适合** | 通用范式：「先试，失败则调整再试」 |
| `.../app/ai/action/moveToTarget.js` | `doAction` | 距离够 → 中止 MOVE 返回 SUCCESS；否则 `character.move`；**怪离 spawn 超 500 则脱战**；目标移动且距离近则重算 | ✅ **★ 强适合** | 含脱战边界与「目标移动重算」两个细节 |
| `.../app/ai/action/moveToTargetForAttack.js` | `doAction` | 类似，针对攻击距离 | ✅ | — |
| `.../app/ai/action/tryAttack.js` | `doAction` | 无 `curSkill` / 目标消失 / 目标变更 → `RES_FAIL`；`character.attack` 返回 SUCCESS/MISS → `RES_SUCCESS` | ✅ 强适合 | 行为树叶子节点的标准写法 |
| `.../app/ai/action/tryPick.js` | `doAction` | 尝试拾取 | ✅ | — |
| `.../app/ai/action/tryTalkToNpc.js` | `doAction` | 尝试 NPC 对话 | ✅ | — |
| `.../app/ai/action/findNearbyPlayer.js` | — | 找附近玩家（**tiger 脑里已注释，未启用**） | ⚠️ 部分 | 索敌实际靠 AOI 事件驱动，此法不必要 |
| `.../app/ai/action/patrol.js` | `doAction` | 把 character 交给 `area.timer.patrol` | ✅ **强适合** | AI → 巡逻的切换点 |
| `.../app/patrol/patrol.js` | `RES_FINISH=0` / `RES_WAIT=1` + `createManager` | 巡逻返回值契约 | ✅ **强适合** | 极简状态机契约 |
| `.../app/patrol/service/patrolManager.js` | `addCharacters/removeCharacter/update` | `genAction` 默认生成 `Loop{rounds:-1, standTick:50}` | ✅ 强适合 | 无限巡逻 + 5s 休息 |
| `.../app/patrol/mode/single.js` | `Mode.update` | 沿路径走一遍即 FINISH | ✅ 强适合 | 定点巡逻 |
| `.../app/patrol/mode/loop.js` | `Mode.update` | 循环 + `standTick` 休息 + `rounds` 计数 | ✅ **强适合** | 主力巡逻模式 |
| `.../app/patrol/mode/composite.js` | `Mode.update` | 子模式顺序执行 | ✅ | 组合 |
| `.../app/patrol/mode/wait.js` | `Mode.update` | 等 N tick | ✅ | 组合零件 |
| `.../app/domain/map/mobzone.js` | `MobZone.update/generateMobs` | `nextGenTime` 节流；每次刷 `genCount=3` 只到 `limit`（默认 10）；随机点 → `new Mob` → `genPatrolPath` → `addEntity` | ✅ **强适合** | 刷怪区标准实现（【已确认】由 `AreaLogic.update1`→`area.updateZones()` 每 **1 秒**驱动，不在 100ms 主 tick 上） |
| `.../app/domain/map/itemzone.js` | `ItemZone.update/generateItems` | 同上的刷物版 | ✅ 强适合 | — |
| `.../app/domain/map/zone.js` | `Zone` | 基类：zoneId/x/y/width/height/area | ✅ | — |
| `.../app/ai/**`, `.../app/patrol/**` 的 `test/` 目录 | `tigerTest.js` / `autoFightTest.js` / `singleTest.js` / `loopTest.js` / `compositeTest.js` | 用 mocha 对 AI/巡逻做的单元测试 | ✅ **强适合** | **行为树与巡逻状态机是最适合写单测的部分**，JSTM 应配套单测 |

## E. 聊天 / 公会 / 队伍 / 交易 / 任务

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `.../app/services/chatService.js` | 构造器 | `uidMap/nameMap/channelMap` 三表 + 邮件池（上限 1000 FIFO）+ 聊天物品池（上限 150） | ✅ **强适合** | 上限 + FIFO 的池化设计，防内存无界增长 |
| 同上 | `add/leave/kick` | 频道加入/退出/踢出；**频道人数为 0 时销毁频道** | ✅ 强适合 | 懒创建 + 自动回收 |
| 同上 | `pushByChannel/pushByPlayerId` | 按频道/按玩家推送 | ✅ | — |
| 同上 | `pushMail/readMail/pushMailToPlayer` | 邮件池 + 附件领取 + **登录后延迟 3s 补推未读** | ✅ **强适合** | 「延迟补推」避免登录瞬间洪峰 |
| 同上 | `findItem` | 解析 `<#GkindId\|id>` 富文本 → RPC 回 area 取物品属性 | ✅ 强适合 | 聊天展示装备的通用方案 |
| `.../app/util/channelUtil.js` | `getGlobalChannelName/getAreaChannelName/getTeamChannelName/getGuildChannelName` | 频道命名规则 | ✅ **强适合** | 直接沿用 |
| `.../app/consts/consts.js` | `Channel` 枚举 | WORLD/AREA/FACTION/TEAM/PRI/SYSTEM/MARQUEE | ✅ 适合 | **需与 1.4.9 协议核对** |
| `.../app/servers/manager/handler/chatHandler.js` | `send` | 敏感词替换 → `findItem` → 按频道分流（世界/场景/公会/队伍/私聊/跑马灯/系统） | ✅ **强适合** | 分流逻辑可直接翻译；**SYSTEM 频道有 GM 后门需加权限** |
| 同上 | `checkForbid` | 逐词 `indexOf` 替换（只替换第一处） | ⚠️ 部分 | 应改 AC 自动机 + 循环替换 |
| `.../app/servers/area/handler/chatHandler.js` | `readMail` | 领邮件附件 → `player.addItem` | ✅ 强适合 | — |
| `.../app/services/teamManager.js` | `createTeam/leaveTeamById/disbandTeamById/inviteJoinTeam/acceptInviteJoinTeam/applyJoinTeam/acceptApplicantJoinTeam/kickOut/dragMember2gameCopy/updateMemberInfo/chatInTeam` | 队伍全生命周期（邀请/申请/回复/踢人/拉进副本） | ✅ **强适合** | 队伍系统完整可参考（**注意本项目队伍对象是全局单例列表，单进程更简单**） |
| `.../app/services/guildService.js`（22.8 KB）+ `Guilder.js`（16.5 KB） | 大量 | 公会：成员/职位/申请/邀请/踢人/任免/公会物品/建筑升级/城战领地/公会频道/延迟存档 | ✅ 强适合 | **`Guilder.delaySave()`（延迟批量存档）值得单看**；`getChannel()` 让公会自带频道 |
| `.../app/services/federationService.js`（20 KB） | `initOffices/producePushCandidates/abdicate/impeach/voteTicket/election/topDonations/timeToVote/tick` | 元老会/选举/弹劾/任期投票 | ✅ 适合 | 玩法系统，可按需 |
| `.../app/services/marketService.js`（34 KB，最大文件） | `checkOrder/buyOrder/sellOrder/cancelOrder/finishTrade/updateTrade/updateCheck/recordItemTradeData/getPriceByKindId/update` + 内建 `Timer` | 拍卖行：买卖挂单、撮合、价格记录、定时 `tick` 清理 | ✅ 强适合 | **「核心服务自带 Timer 做定时撮合/清理」**是值得学的模式 |
| `.../app/domain/task/{task,taskMain,taskReward,tasks}.js` | `TaskState{NOT_START/NOT_COMPLETED/NOT_DELIVERY/COMPLETED}`、`TaskType{KILL_MOB/COLLECT/TALK_NPC}`、`updateTaskData/updateCollectTaskData` | 任务状态机 + 三类进度更新 | ✅ **强适合** | 任务系统的最小可用模型，JSTM 直接借鉴状态机 |
| `.../app/domain/bag.js` / `bagItem.js` / `equipments.js` / `equipment.js` | — | 背包 / 装备 | ✅ 强适合 | 标准容器模型 |
| `.../app/domain/fightskill.js` + `buff.js` | `judge/attack/coolDownTime`、`addBuff/removeBuff` | 技能判定 + BUFF | ✅ 适合 | 战斗系统骨架 |
| `.../app/domain/playerBank.js` + `dao/playerBankDao.js` | — | 钱庄/银行 | ✅ 适合 | 交易系统的必要组成 |
| `.../app/dao/**`（30 文件）+ `dao/mapping/*Sync.js`（7 文件） | `userDao`（14.9 KB，最大 DAO）、`taskDao`、`guildDao`… | MySQL 访问 + pomelo-sync 同步表声明 | ✅ **强适合** | **「DAO 分层」+「mapping 声明哪些字段需要定时落库」**值得照搬结构（**SQL 与表结构不可复制**） |
| `.../app/dao/mysql/{mysql,dao-pool}.js` | `init(app)`、连接池 | 连接池 + 封装查询 | ✅ 思想适合 | Python 用 SQLAlchemy / aiomysql 池 |
| `.../app/domain/persistent.js` | 存档接口 | 领域对象统一存档入口 | ✅ 强适合 | — |
| `.../config/data/error_code.json`（7.4 KB）/ `forbid_word.json`（31 KB） | 数据表 | 集中错误码 / 敏感词 | ✅ 结构适合 | **数据内容不可复制（版权）**，需按 JSTM 目标客户端重建 |

## F. 战斗与区域策略

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `.../app/domain/area/areaLogic.js`（33 KB） | `AreaLogic` 基类 | `attack/multiAttack/killReward/diedInArea/reviveInArea/finishFight` | ✅ **强适合** | **策略模式：按 areaKind 选不同 AreaLogic** 是本项目最优雅的设计之一 |
| 同上 | `AreaNormalLogic` | 普通场景 | ✅ | — |
| 同上 | `AreaDomainLogic`（约 550 行，含大段注释） | 城战：`initDomainArea / updateDomainBattle / onDomainBattle / onUpdateDomain / pushDomainInfo`；`DomainConst{START_HOUR:20,START_MINUTE:30,END_HOUR:21}` | ✅ 适合 | 定时 PVPVE 玩法的参考实现 |
| 同上 | `AreaFightLogic` | 竞技场：`enterArea/exitArea/diedInArea/finishFight(loserId)` | ✅ 适合 | — |
| 同上 | `AreaMyBossLogic` / `AreaWorldBossLogic` | 个人 BOSS / 世界 BOSS：进入/退出/复活/`startLogic` | ✅ 适合 | — |
| 同上 | `createAreaLogic(area)` | 按 `area.areaKind` 工厂选择 | ✅ **强适合** | 工厂 + 策略，JSTM 直接照搬 |
| 同上 | `attack(attacker,target,skill)` / `multiAttack` | 攻击判定、伤害、仇恨、掉落 | ✅ 强适合 | 战斗核心 |
| 同上 | `killReward(attacker,target,msg,items)` | 击杀奖励（经验/掉落） | ✅ 强适合 | — |
| `.../app/consts/formula.js` | `refreshProperty / distance / inRange` 等 | 数值公式集中 | ✅ **强适合** | **公式集中管理**是必须的；**具体公式需按 JSTM 目标客户端重算** |
| `.../app/servers/area/handler/fightHandler.js` | `useSkillAttack(msg,session,next)` / `fightPrize` | 技能攻击入口 | ✅ 强适合 | — |
| `.../app/services/fightService.js`（10 KB） | `enterFight/exitFight/readyFight/changeFight/cancelFight/prepareFight/finishFight/pushFighter/pushCompetitor/pushPlayerToArea` | 竞技场匹配与流程 | ✅ 适合 | 可用于 JSTM 的 PVP 模块 |
| `.../app/services/instanceManager.js` | `addServers/removeServers/isInInstance/leaveInstance/getInstance/createInstance/remove` | 跨服副本管理（监听 `ADD_SERVERS`/`REMOVE_SERVERS`） | ❌ 不适合 | 分布式副本调度；单进程下用 `InstancePool` 即可 |
| `.../app/domain/entity/character.js` | `attack/getAvailableSkill/checkSkillAvailable/hit/reduceHp/reduceMp/addBuff/removeBuff/addEnemy/forEachEnemy/forgetEnemy/increaseHateFor/getMostHater` | 战斗实体：技能冷却、命中、仇恨表、敌人表 | ✅ **强适合** | 战斗实体模型完整可参考 |
| `.../app/domain/entity/player.js`（22.5 KB） | `equip/unEquip/useItem/pickItem/addItem/learnSkill/upgradeSkill/setTotalAttackAndDefence/upgrade/onHpMp/onHp2All...` | 玩家全套行为 + 客户端推送方法 | ✅ **强适合** | **「领域对象的 onXxx 方法直接负责推送给客户端」**是本项目的风格（如 `onExp/onMoney/onHpMp`）——JSTM 可借鉴但要注意别让领域层依赖网络层 |
| `.../app/domain/entity/mob.js` | `enterAI/isHate/increaseHateFor/getMostHater/dropItem/_dropEquipment/getEquipmentsByLevel/resetPosition/returnToSpawningPosition/getKillExp/hit/strip/updateTaskData` | 怪物：仇恨、掉落、回位、刷新 | ✅ **强适合** | 掉落与回位逻辑完整 |
| `.../app/domain/entity/npc.js` | `talk(player)` / `strip()` | NPC 对话（含传送 NPC，`NpcType{TALK_NPC:'0',TRAVERSE_NPC:'1'}` + `consts.TraverseNpc` 映射） | ✅ 强适合 | 传送 NPC 用 id→areaId 映射，简单有效 |
| `.../app/domain/entity/entity.js` | `Entity` | `entityId / type / x / y / range / strip` | ✅ 强适合 | 基类最小字段集 |

## G. 工程化（不适合借鉴的部分汇总）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `lordofpomelo/pomelo/lib/**`（94 文件全部） | — | Pomelo 框架本体 | ❌ 不适合 | 无 Pomelo |
| `lordofpomelo/pomelo/lib/connectors/**`（20 文件） | — | 网络协议实现 | ❌ 不适合 | 协议层整体作废 |
| `lordofpomelo/pomelo/lib/master/**` + `modules/{masterwatcher,monitorwatcher}.js` | — | 多机部署 | ❌ 不适合 | 单进程 |
| `lordofpomelo/pomelo/lib/common/service/{sessionService,backendSessionService,channelService,connectionService}.js` | — | 跨进程会话/频道/连接 | ❌ 不适合 | 分布式特有；**但 channel/连接统计的「概念」仍需在 JSTM 里以简化形式存在** |
| `lordofpomelo/pomelo/lib/components/{master,monitor,dictionary,protobuf,connector,pushScheduler}.js` | — | 框架组件 | ❌ 不适合 | 同上 |
| `lordofpomelo/game-server/app/util/httpServer.js` | 内嵌 HTTP 服务 | 脚本里 `require` 被注释，未启用 | ❌ 不适合 | 未启用 |
| `lordofpomelo/web-server/**` | `app.js` / `lib/oauth.js` | 登录/OAuth/热更 | ⚠️ 待评估 | **JSTM 需要一个登录/更新 HTTP 服务，但实现方式应自研**（本次未细读） |
| `lordofpomelo/bin/*.sh`、根目录 `*.command` | 部署脚本 | 打包/替换 IP/关机 | ⚠️ 部分 | 「打包 + 替换 IP 发布」的工程化思路可借鉴 |
| `lordofpomelo/game-server/config/{masterha.json,scheduler.json}`、`scripts/createZKMasterhaNode.js` | — | 高可用/调度 | ❌ 不适合 | 未启用 |
| `pomelo-admin-web/**`（4563 文件） | — | 运维 Web 面板 | ❌ **严禁** | **含 GPL 的 ExtJS（`public/ext-4.0.7-gpl/license.txt`）**，绝不引入 |

---

# 附：本清单的置信度分布

| 置信度 | 条目数（约） | 说明 |
|---|---|---|
| **【已确认】**（有 ZIP 内源码证据） | 全部 ★1 / ★2 条目的机制描述 | 见 `architecture.md` 第 5 节 20 条结论、`pomelo.md`、`scene.md`、`aoi.md`、`pathfinding.md` 的表格 |
| **【待验证】**（外部资料或间接推断） | AOI 塔式算法细节、`pomelo-bt` 节点内部语义、`pomelo-collection` 比较语义、`masterha` 是否真的未启用、客户端是否支持服务端下发路径、`config/data/*.json` 与 1.4.9 的对应关系 | 见各专文末尾「未知/待验证」清单 |
| **【未知】** | `pomelo-aoi` / `pomelo-pathfinding` / `pomelo-bt` / `pomelo-collection` / `pomelo-sync-plugin` 内部实现；`cocosjs/` 客户端；`pomelo-admin-web/` 细节；`marketService` / `federationService` 算法细节；`dao/**` 逐表结构 | 无法从 ZIP 获得，**不做任何猜测性断言** |
