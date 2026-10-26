# Pomelo 服务划分、Gate/Connector/Logic 协作、RPC(remote) 机制

> 参照物：`kongkongxiyou-master/lordofpomelo/pomelo/`（Pomelo 1.2.x 源码）+ `game-server/`（业务装配）
> 所有「文件路径」均相对 `kongkongxiyou-master/`。
> 置信度标记：**【已确认】** 有源码证据；**【待验证】** 外部资料/间接推断；**【未知】** ZIP 内无源码。

---

## 1. Pomelo 的「服务划分」—— 三把刀

### 1.1 第一把刀：`serverType` 切进程

**唯一真源是 `lordofpomelo/game-server/config/servers.json`。【已确认】**

```json
{ "development": {
    "connector":[{"id":"connector-server-1","host":"127.0.0.1","port":3150,"clientPort":3010,"frontend":true}],
    "area":     [{"id":"area-server","host":"127.0.0.1","port":3270,
                  "areas":"[1001,2003,3001,3002,3003,3004,3005,6001,6002,6003,6004,6005]","area":0}],
    "auth":     [{"id":"auth-server-1","host":"127.0.0.1","port":3650}],
    "gate":     [{"id":"gate-server-1","host":"127.0.0.1","clientPort":3014,"frontend":true}],
    "manager":  [{"id":"manager-server-1","host":"127.0.0.1","port":3750}],
    "trade":    [{"id":"trade-server-1","host":"127.0.0.1","port":3850}]
} }
```

启动契约（`pomelo/lib/util/appUtil.js#processArgs` + `parseArgs`）：命令行 `key=value` 形式，`serverType=` / `id=` / `mode=`(默认 `cluster`) / `env=`(默认 `development`)。

| 解析出的 app 属性 | 来源 | 用途 |
|---|---|---|
| `app.serverType` | `serverType=` | `app.configure(env, type, fn)` 的匹配键 |
| `app.serverId` | `id=` 或 `master.json` 的 id | 日志/RPC 目标标识 |
| `app.curServer` | `servers.json` 中该 id 的记录 | 端口、`clientPort`、`areas`、`instance` 等自定义字段都从这里读 |
| `app.master` | `config/master.json` | master 地址（端口 3005） |
| `app.env` | `env=` 或 `NODE_ENV` | 生产/开发配置切换 |

**`app.js` 是唯一的装配点**，全部使用 `app.configure('production|development', '<serverType>|<serverType>', fn)`：

| configure 目标 | 装配内容（原文摘要） |
|---|---|
| `production`（全局） | `app.before(pomelo.filters.toobusy())`；`app.enable('systemMonitor')`；`app.registerAdmin(onlineUser)`；构建 `app.set('areaIdMap', {areaId: serverId})`（**只收录非 instance 的 area 记录**）；`app.set('proxyConfig',{cacheMsg:true,interval:30,lazyConnection:true})`；`app.set('remoteConfig',{cacheMsg:true,interval:30})`；`app.route('area', routeUtil.area)`；`app.route('connector', routeUtil.connector)`；`app.loadConfig('mysql', .../shared/config/mysql.json)` |
| `auth` | `app.set('session', require('./config/session.json'))` → `{secret:'pomelo_session_secret', expire:-1}`（**永不过期**） |
| `area` | `app.before(playerFilter())`；`areaService.init()`（预建所有 `Map`）；按 `curServer.areas` / `curServer.instance` 三选一：`AreaManager`（大区服）/ `InstancePool`（副本服）/ `Scene`（单场景服），统一挂到 `app.areaManager` |
| `area|auth|connector|master|trade|manager|fight` | `mysql.init(app)` → `app.set('dbclient', ...)`；**`app.use(sync, {sync:{path:__dirname+'/app/dao/mapping', dbclient}})`** |
| `manager` | `app.event.on(ADD_SERVERS, instanceManager.addServers)`；`REMOVE_SERVERS` 同理；`app.set('guildService', new GuildService(app))`；`fightService.init()`；`app.set('chatService', new ChatService(app))` |
| `connector` | `app.set('connectorConfig', {connector: hybridconnector, heartbeat:30, useDict:true, useProtobuf:false, disconnectOnTimeout:true, setNoDelay:true, handshake:(msg,cb)=>cb(null,{})})` |
| `gate` | `app.set('connectorConfig', {connector: hybridconnector, useProtobuf:false})` |
| `chat` | `app.set('chatService', new ChatService(app))`（**servers.json 无此进程**） |
| `trade` | `app.set('marketService', new MarketService(app))`；`federationService.init()` |
| `fight` | `fightService.init()`（**servers.json 无此进程**） |

### 1.2 第二把刀：目录约定切「能力面」（约定优于配置）

**`pomelo/lib/util/pathUtil.js`【已确认】：**

```js
getHandlerPath(appBase, serverType)  => appBase + '/app/servers/' + serverType + '/handler'
getUserRemotePath(appBase, serverType)=> appBase + '/app/servers/' + serverType + '/remote'
getCronPath(appBase, serverType)     => appBase + '/app/servers/' + serverType + '/cron'
getSysRemotePath(role)               => pomelo/lib/common/remote/{frontend|backend}
listUserRemoteDir(appBase)           => 列出 app/servers/ 下所有子目录（用于启动时批量建 RPC 代理）
```

| 目录 | 谁加载 | 谁能调用 | 命名空间 |
|---|---|---|---|
| `app/servers/<T>/handler/**` | `common/service/handlerService.js` → `pomelo-loader.load(path, app)` | **客户端** | route = `<T>.<fileName>.<method>`（`server/server.js#parseRoute` 强制 `split('.').length === 3`） |
| `app/servers/<T>/remote/**` | `components/remote.js#getRemotePaths` → `pomelo-rpc`.server | **其它服务器** | `app.rpc.<T>.<fileName>.<method>` |
| `app/servers/<T>/cron/**` | `server/server.js#loadCronHandlers` | 调度器 | `config/cron.json` 里 `action = "<fileName>.<method>"` |
| `pomelo/lib/common/remote/{frontend,backend}/**` | 同上（`sys` 命名空间） | 框架自身 | `app.sysrpc.<T>.<name>.<method>` |

业务侧的对应实例【已确认】：
- handler 名即**文件名**：`area/playerHandler.js` → route `area.playerHandler.move`
- remote 名即**文件名**：`area/playerRemote.js` → `app.rpc.area.playerRemote.playerLeave`
- 系统 remote 实例：`pomelo/lib/common/remote/frontend/sessionRemote.js`、`channelRemote.js`；`backend/msgRemote.js`（**`doForward` 用的就是它**）

### 1.3 第三把刀：组件（component）切关注点

**`pomelo/lib/components/` 共 12 个；`appUtil.loadDefaultComponents` 按条件装载【已确认】：**

```js
if (serverType === 'master')            app.load(pomelo.master,  masterConfig)
else {
  app.load(pomelo.proxy,  proxyConfig)                       // 永远
  if (curServer.port)  app.load(pomelo.remote, remoteConfig)  // 有 RPC 端口才起
  if (app.isFrontend()) {
     app.load(pomelo.connection,  connectionConfig)
     app.load(pomelo.connector,   connectorConfig)
     app.load(pomelo.session,     sessionConfig)
     app.load(pomelo.pushScheduler, pushSchedulerConfig)
  }
  app.load(pomelo.backendSession, backendSessionConfig)
  app.load(pomelo.channel,        channelConfig)
  app.load(pomelo.server,         serverConfig)
}
app.load(pomelo.monitor, monitorConfig)
```

| 组件（`name` 属性） | 文件 | 作用 | 本项目是否启用 |
|---|---|---|---|
| `__master__` | `components/master.js` | master 进程：把 `servers.json` 分发给各 server、`ADD_SERVERS/REMOVE_SERVERS` 事件 | ✅（master 端口 3005） |
| `__proxy__` | `components/proxy.js` | **RPC 客户端**：为每个远端生成代理，挂 `app.rpc` / `app.sysrpc` / `app.rpcInvoke` | ✅ 全部后端 |
| `__remote__` | `components/remote.js` | **RPC 服务端**：扫描本机 `remote/` 与系统 remote 目录并注册 | ✅ 有 port 的（auth/area/manager/trade） |
| `__connection__` | `components/connection.js` → `connectionService.js` | 连接计数、登录用户表、`max-connections` 保护 | ✅ frontend |
| `__connector__` | `components/connector.js` | 网络层、session 创建、消息路由 / `doForward` | ✅ connector + gate |
| `__session__` | `components/session.js` → `sessionService.js` | session 池、`bind/unbind/kick/pushAll` | ✅ frontend |
| `__pushScheduler__` | `components/pushScheduler.js` | 推送调度（direct / buffer，默认 buffer 合并 30 ms） | ✅ frontend |
| `__backendSession__` | `components/backendSession.js` | 后端访问前端 session 的服务 | ✅ |
| `__channel__` | `components/channel.js` → `channelService.js` | **频道广播**（聊天、AOI 群推都走它） | ✅（chat 靠它） |
| `__server__` | `components/server.js` → `server/server.js` | handler 分发、过滤器链、cron | ✅ |
| `__dictionary__` | `components/dictionary.js` | route 字符串 → 数字压缩（`useDict:true`） | ✅ connector |
| `__protobuf__` | `components/protobuf.js` | protobuf 编解码 | ❌（`useProtobuf:false`） |
| `__master__` / `__monitor__` | `components/{master,monitor}.js` | 监控 | `app.enable('systemMonitor')` |

**三把刀的关系：** serverType 决定「装配哪些组件」（纵向），目录约定决定「暴露哪些方法」（横向），组件决定「横切能力」（正交）。**没有一处需要手写注册表 —— 全靠 `fs.readdirSync` + `require`。**

---

## 2. Gate / Connector / Logic 协作（含完整登录时序）

### 2.1 三方职责表

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|---|
| `lordofpomelo/game-server/app/servers/gate/handler/gateHandler.js` | `Handler` 构造器 | 遍历 `os.networkInterfaces()`，取**最后一个非 `127.0.0.1` 的 IPv4** 作为 `this.serverId`；取不到则退回 `127.0.0.1` | ⚠️ 部分 | 「客户端先问入口」的思路适合（JSTM 可直接返回固定 host:port）；**IP 探测逻辑不适合**（多网卡/容器必然错）【已确认】 |
| 同上 | `Handler.prototype.queryEntry(msg,session,next)` | `uid` 为空 → `Code.FAIL`；`getServersByType('connector')` 为空 → `Code.GATE.FA_NO_SERVER_AVAILABLE`；否则 `dispatcher.dispatch(uid, connectors)` 取一台，**强制覆盖 `res.host = this.serverId`**，返回 `{code, host, port: clientPort}` | ✅ 适合 | 极简：拿 uid → 取模 → 返回地址。JSTM 单进程可直接返回本地地址，但**保留该握手步骤**有利于日后扩服 |
| `.../app/util/dispatcher.js` | `dispatch(uid, connectors)` | `index = Number(uid) % connectors.length`（顶部 `//var crc = require('crc')` 被注释） | ⚠️ 部分 | 取模实现简单但**增删节点会全量重映射**；JSTM 若单进程则无需分派，但**若未来多进程应换一致性哈希**【已确认注释掉的 crc 版本说明作者也考虑过】 |
| `pomelo/lib/components/connector.js` | `Component` / `start` / `afterStart` / `send` / `handleMessage` | `start` 强校验依赖 `__server__`、`__session__`（缺则报错）；`afterStart` 里 `this.connector.on('connection', hostFilter.bind(this, bindEvents))`；`handleMessage` → `server.globalHandle(msg, session.toFrontendSession(), cb)` → 回包 `send(msg.id, msg.route, resp, [session.id], {type:'response'}, ...)` | ❌ 不适合 | 强绑定 pomelo 的 connector/session/pushScheduler 组件与 hybridconnector 协议。**仅「session 与 socket 分离」的思想可借鉴** |
| 同上 | `bindEvents(self, socket)` | 维护 `closed` 幂等标志；`session.closed` 事件、`session.on('bind'/'unbind')` 用于连接统计与 `BIND_SESSION/UNBIND_SESSION` 事件 | ⚠️ 部分 | 「session 生命周期的幂等关闭 + 绑定事件」在任何服务器都需要，JSTM 应自建等价物 |
| 同上 | `hostFilter(cb, socket)` | 动态黑名单（正则匹配 IP）+ 静态 `blacklistFun(cb)` | ✅ 思想适合 | 反外挂/封 IP 的黑名单钩子，JSTM 可照抄设计（正则数组 + 回调） |
| `pomelo/lib/server/server.js` | `Server.prototype.globalHandle` | `parseRoute(msg.route)` → 全局 beforeFilter → **若 `app.serverType !== routeRecord.serverType` 则 `doForward`，否则 `doHandle`** | ⚠️ 部分 | **「route 首段即目标服务器类型」是 Pomelo 的核心路由约定**；单进程 JSTM 可简化为「本地 dispatcher 表」，但**保留 route 字符串格式**（`type.handler.method`）便于日后拆分 |
| 同上 | `doForward(app,msg,session,routeRecord,cb)` | `app.sysrpc[serverType].msgRemote.forwardMessage(session, msg, session.export(), cb)` —— **把整个 msg + 序列化后的 session 一起转发** | ❌ 不适合 | 进程间转发 + 全量 session 导出是分布式成本；JSTM 单进程是直接函数调用 |
| 同上 | `doHandle(server,msg,session,routeRecord,cb)` | `msg = msg.body \|\| {}`；**注入 `msg.__route__ = originMsg.route`**；→ `handlerService.handle(routeRecord, msg, session, cb)` | ✅ 思想适合 | **「把 route 注入 msg 供业务/过滤器使用」+「body 与信封分离」是好设计**，JSTM 应采用 |
| `pomelo/lib/common/service/handlerService.js` | `Service.prototype.handle` / `getHandler` / `loadHandlers` | 按 `serverType` 懒加载 handler 表（`pomelo-loader.load(path, app)`，每个 handler 用 `module.exports = function(app){ return new Handler(app) }` 工厂）；找不到 handler/method 记 warn 返回 null；**`opts.reloadHandlers` 时 `fs.watch` 热重载** | ✅ 部分适合 | 「handler 工厂函数 + 懒加载 + 热重载」在 Python 里可用 `importlib.reload` 复刻；**值得注意的是 handler 是「每 serverType 一份实例」而不是每请求新建**（有状态风险） |
| `.../app/util/routeUtil.js` | `exp.area` / `exp.connector` | `area`: 直接返回 `session.get('serverId')`，取不到则报错；`connector`: 返回 `session.frontendId` | ✅ **思想极适合** | **「玩家归属服务器存在 session 里，路由函数只读 session」** —— JSTM 即使单进程，把「玩家归属场景/分线」记在会话对象上是正确做法 |
| `.../app/servers/connector/handler/entryHandler.js` | `pro.entry(msg,session,next)` | `async.waterfall`：① `app.rpc.auth.authRemote.auth(session, token, cb)` ② 校验 code/user，`user.lastLoginTime/loginCount` 更新 ③ `userDao.getPlayersByUid` ④ 返回 `{code:200, uid, time, kindId, players:[{playerId,name,kindId,level}]}` | ✅ 流程适合 | **登录三步：校验 token → 查角色列表 → 返回选角数据**，JSTM 可完全照搬流程（token 校验可简化为 HMAC） |
| 同上 | `pro.entryPlayer(msg,session,next)` | ① **`app.get('sessionService').kick(uid, cb)`（同账号挤下线）** ② `session.bind(uid, cb)` ③ 查角色并校验 `playerId` 属于该 uid ④ `userDao.updateKindId` ⑤ `session.set(serverId/playerName/level/kindId/playerId/guildId/vip)`；**`serverId` 被硬编码为 `"area-server"`**（原区域分派逻辑整段注释） ⑥ `session.on('closed', onUserLeave.bind(null,app))` ⑦ `session.pushAll(cb)` ⑧ 回调后再 `handleRemote.chatRemote_add(...)` + `rpc.manager.guildRemote.enterGuild(...)` | ✅ **强适合** | 这是「登录完成后才做跨服注册」的正确顺序，**callback 先返回再补副作用**避免登录超时；JSTM 应学「先推 session，再挂附属注册」 |
| 同上 | `onUserLeave(app,session,reason)` | 依次：`area.playerRemote.playerLeave`（必做/存档）、`manager.guildRemote.playerLeave`、`manager.fightRemote.kick`、`chatRemote.kick`、`trade.marketRemote.kick` | ✅ **强适合** | **下线清理清单**可直接作为 JSTM 的 checklist；注意每步独立容错（`if (!!err) logger.error`）不中断后续 |
| 同上 | `pro.fixLeaveArea(msg,session,next)` | 兜底修复：客户端报「我在 X 场景卡住了」，服务端按 `areaData.type` 广播 `playerRemote.fixPlayerLeave` 到所有单场景服或所有副本服 | ✅ 思想适合 | **「允许客户端上报异常状态并做服务端修复」的容灾通道**，私服兼容项目很需要（JSTM 面对 1.4.9 客户端协议不完整时尤其实用） |
| `.../app/servers/connector/handler/roleHandler.js` | `Handler.prototype.createPlayer` | 名字非空 → **遍历 `forbid_word.json` 逐词 `indexOf` 检查（注意判据是 `searchIndex > 0`，**位置 0 的敏感词会漏检**）** → `getSQLPlayerByName` 查重（code 66）→ `userDao.createPlayer` → `async.parallel` 建主线任务 + 装配初始技能 | ✅ 部分 | 建号流程适合；**敏感词判据 `> 0` 是 bug**，JSTM 应用 `>= 0` 并改用 Trie/AC 自动机 |
| `.../app/servers/auth/remote/authRemote.js` | `Remote.prototype.auth(token,cb)` | `tokenService.parse(token, this.secret)` → 非法返回 `FA_TOKEN_ILLEGAL` → `checkExpire`（**`expire < 0` 视为永不过期**；本项目 `session.json` 是 `-1`）→ `userDao.getUserById` → `cb(null, Code.OK, user)` | ✅ 强适合 | 极简 token 校验模型。**「secret 默认值 + expire 可配 -1」**可直接照搬；JSTM 建议至少把 expire 设为正数 |
| `.../app/servers/area/filter/playerFilter.js` | `Filter.prototype.before(msg,session,next)` | 首次调用懒取 `pomelo.app.areaManager`；`areaManager.getPlayerWithPlayerIdCb(playerId, cb)`：命中内存/缓存直接返回，否则查库并 `addPlayer`；补 `player.serverId/sessionData`；`areaManager.getAreaWithPlayer(player)` 决定 area，**`session.area = area`**；**若玩家不在 area 里：只有 route 以 `enterScene` 结尾才放行，否则推 `onChangeArea` 并 `next(new Error(...))`** | ✅ **极适合** | 这是**「请求前置守卫」的教科书式实现**：统一取玩家 → 校验归属 → 注入 `session.player` → 异常时纠正客户端。JSTM 应做等价装饰器/middleware |

### 2.2 登录时序（原文级还原）【已确认】

```
[客户端]  ──1 HTTP──▶ web-server(express:3001?)  登录/OAuth → 返回 token
[客户端]  ──2 WS ──▶ gate:3014
             gate.queryEntry({uid})
             ← {code:200, host:<本机非loopback IP>, port:3010}
[客户端]  ──3 WS ──▶ connector:3010
   connector.entryHandler.entry({token})
     └─ RPC ▶ auth.authRemote.auth(session, token)
              tokenService.parse(token, 'pomelo_session_secret')
              checkExpire: expire=-1 → 恒真
              userDao.getUserById(uid) → cb(null, 200, user)
     ├─ entryHandler: user.lastLoginTime=now; user.loginCount++; userDao.updateUser
     ├─ userDao.getPlayersByUid(uid) → players[]
     └─ next(null,{code:200, uid, time, kindId:user.lastKindId, players:[...]})

   connector.entryHandler.entryPlayer({uid, playerId})
     ├─ app.get('sessionService').kick(uid)          ← 同账号踢下线
     ├─ session.bind(uid)
     ├─ userDao.getPlayersByUid(uid) → 找到 player
     ├─ userDao.updateKindId(uid, player.kindId)
     ├─ session.set('serverId', "area-server")       ← 硬编码
     ├─ session.set(playerName/level/kindId/playerId/guildId?/vip?)
     ├─ session.on('closed', onUserLeave)
     ├─ session.pushAll()                            ← 把上述字段同步到所有前端
     ├─ next(null,{code:200})
     └─ (回调之后) handleRemote.chatRemote_add(session, userId, playerId, "pomelo")
                   rpc.manager.guildRemote.enterGuild(session, userId, guildId, playerId, noop)

[客户端]  ──4 area.??? ──▶ connector
    connector.handleMessage → server.globalHandle
      routeRecord.serverType = 'area' ≠ 'connector'
      → doForward → sysrpc.area.msgRemote.forwardMessage(session, msg, session.export())
        → area: handleMessage → doHandle → beforeFilter(playerFilter)
           → playerFilter: areaManager.getPlayerWithPlayerIdCb → session.area / session.player
           → handlerService.handle(routeRecord=area.playerHandler.enterScene, ...)
     area.playerHandler.enterScene → area.enterArea → map.isReachable 校正 → getAreaInfoStrip(AOI快照)
                                   → area.addEntity(player)（内部 aoi.addWatcher + channel.add）
     ← {code:200, areaId, entities, curPlayer}
     → 回到 connector → pushScheduler.schedule → socket.write
```

**协作要点小结【已确认】：**
1. **Gate 不参与业务**，只在登录前给一次地址。
2. **Connector 是唯一持有 socket 与 session 的进程**；它同时是**路由器**（`doForward`）。
3. **Area 只拿到 `msg` + 一份「session 快照」**（`session.export()`），因此业务 handler 里的 `session.get('playerId')` 读的是快照值 —— **写 `session.set()` 必须靠 `session.push()`/`pushAll()` 才会回写前端**。这是 Pomelo 最容易踩的坑（本项目 `gotoScene` 里就正确用了 `session.pushAll`）。
4. **路由靠 session 上的 `serverId`**（`routeUtil.area`），切换场景时 `session.set('serverId', ...)` + `pushAll()` 完成「玩家跨场景迁移」。

---

## 3. RPC（remote）机制详解

### 3.1 服务端（`pomelo/lib/components/remote.js`）【已确认】

```js
pro.name = '__remote__';
pro.start = function(cb) {
  this.opts.port = this.app.getCurServer().port;   // 用 config/servers.json 里的 port 起 RPC 监听
  this.remote = genRemote(this.app, this.opts);    // pomelo-rpc 的 server
  this.remote.start();
};
getRemotePaths(app):   // 只收集两类路径
  if (app.isFrontend()) role='frontend' else role='backend'
  paths.push( sys : pathUtil.getSysRemotePath(role) )              // pomelo/lib/common/remote/{frontend,backend}
  paths.push( user: pathUtil.getUserRemotePath(base, serverType) ) // app/servers/<T>/remote
```

**没有 `port` 的服务器不加载 remote 组件** → `gate` 没有 `port`（只有 clientPort）→ **gate 不能被 RPC 调用，也不提供 remote**。这解释了为什么 `gateHandler` 只有 `queryEntry` 一个方法。

### 3.2 客户端（`pomelo/lib/components/proxy.js`）【已确认】

```js
pro.afterStart = function(cb) {
  this.app.__defineGetter__('rpc',    () => this.client.proxies.user);  // app.rpc.<serverType>.<remote>.<method>
  this.app.__defineGetter__('sysrpc', () => this.client.proxies.sys);   // app.sysrpc.<serverType>.<name>.<method>
  this.app.set('rpcInvoke', this.client.rpcInvoke.bind(this.client), true);
  this.client.start(cb);
};
// 服务发现：监听 app.event 的 ADD_SERVERS / REMOVE_SERVERS / REPLACE_SERVERS
var genProxies = (client, app, sinfos) => sinfos.forEach(item => {
  if (hasProxy(client, item)) return;
  client.addProxies(getProxyRecords(app, item));   // 为每个 serverType 生成一层代理对象
});
```

**默认路由函数（`genRouteFun` + `defaultRoute`）【已确认】：**
```js
routes = app.get('__routes__');                 // 由 app.route(serverType, fn) 注册
route = routes[msg.serverType] || routes['default'];
if (route) route(session, msg, app, cb);
else cb(null, list[ Math.abs(crc.crc32(uid)) % list.length ].id );  // 一致性哈希缺省实现
```
本项目覆盖了 `area`（按 `session.serverId`）和 `connector`（按 `session.frontendId`）两条路由，其余（auth/manager/trade）走默认 crc32 取模。

### 3.3 调用形式（本项目全部用法）【已确认】

| 形式 | 示例 | 语义 |
|---|---|---|
| `app.rpc.<type>.<remote>.<method>(session, ...args, cb)` | `app.rpc.auth.authRemote.auth(session, token, cb)` | 带 session 的 RPC，路由函数可用 session 决策 |
| 第一参传 `null` | `app.rpc.manager.teamRemote.leaveTeamById(null, params, cb)` | 不带 session（路由退化为 crc32(uid='')） |
| `app.rpcInvoke(serverId, {namespace, service, method, args}, cb)` | `chatService.findItem` 里调用 `playerRemote.getChatItem` | **指定 serverId 的底层调用**；`namespace` 为 `'user'`（对应 `app/servers/.../remote/`） |
| `app.sysrpc.<type>.msgRemote.forwardMessage(...)` | `server.js#doForward` | 框架内部转发 |
| 服务端方法签名 | `Remote.prototype.auth = function(token, cb)`<br>`exp.playerLeave = function(args, cb)`<br>`exp.enterGuild = function(userId, guildId, playerId, cb)` | **参数里没有 session**：`app.rpc.x.y(session, a, b, cb)` 中 session 只参与路由，**不传入被调函数**，被调函数只收到 `(a, b, cb)`【已确认，易错点】 |

### 3.4 远程调用配置与性能

| 配置 | 值 | 代码位置 | 含义 |
|---|---|---|---|
| `remoteConfig` | `{cacheMsg:true, interval:30}` | `app.js` | RPC 消息**合并缓冲，每 30 ms 发一次**（`opts.bufferMsg = opts.bufferMsg \|\| opts.cacheMsg`） |
| `proxyConfig` | `{cacheMsg:true, interval:30, lazyConnection:true}` | `app.js` | 同上 + 懒建连 |
| `rpcFilter` | 全部被注释 | `app.js` | `pomelo.rpcFilters.rpcLog()` **未启用** → 没有 RPC 耗时日志 |
| RPC 过滤器实现 | `pomelo/lib/filters/rpc/rpcLog.js` | — | `before` 记 `opts.__start_time__`，`after` 打 `{route, args, time, timeUsed}`（**若要压测 RPC，把这个打开即可**） |

### 3.5 过滤器（handler 侧）

| 文件 | 机制 | 是否适合 JSTM |
|---|---|---|
| `pomelo/lib/common/service/filterService.js` | `befores[]`（`push`）+ `afters[]`（`unshift`）；`beforeFilter` 串行 `next(err,resp,opts)`；`afterFilter` 串行，`after` 不能改变请求流 | ✅ **链式中间件思想完全适合**，Python 可用装饰器/生成器复刻 |
| `pomelo/lib/filters/handler/timeout.js` | `before` 起 `setTimeout` 记 `session.__timeout__`，`after` 清除；超时只打 warn，**不中断请求**；`maxSize=500` 超限则跳过监控 | ✅ 思想适合（**但必须真的中断/回收，而不是只打日志**） |
| `pomelo/lib/filters/handler/serial.js` | 用 `taskManager.addTask(session.id, ...)` **把同一 session 的请求串行化** | ⚠️ 部分 | 单线程 Python 里若用 asyncio，同类竞态用「每玩家 asyncio.Lock」更轻 |
| `pomelo/lib/filters/handler/toobusy.js` | 生产环境启用的过载保护 | ✅ 适合 |
| `pomelo/lib/filters/rpc/rpcLog.js` | 见上 | ✅ 适合 |

---

## 4. Session 与 Channel：跨进程状态的两块基石

### 4.1 SessionService（`pomelo/lib/common/service/sessionService.js`）

| 方法 | 作用 |
|---|---|
| `create(sid, frontendId, socket)` | 建 session |
| `bind(sid, uid, cb)` | 绑定 uid，触发 `bind` 事件（connector 里监听用于统计） |
| `unbind(sid, uid, cb)` | 解绑 |
| `get(sid)` / `getByUid(uid)` | 查询 |
| `import/importAll(sid, key/value, cb)` | **把前端 session 数据导入后端** |
| `kick(uid, reason, cb)` / `kickBySessionId(sid, ...)` | 踢下线（**`entryPlayer` 用它实现同账号互挤**） |
| `sendMessage(sid,msg)` / `sendMessageByUid(uid,msg)` | 直发 |
| `pushAll(cb)` | **把当前 session 的全部字段推给所有前端服务器**（Pomelo 里后端 session 的字段是「副本」，必须显式 push） |

**`Session` vs `FrontendSession`【已确认】：** connector 里 `server.globalHandle(msg, session.toFrontendSession(), cb)`；后端拿到的 session 是 `session.export()` 的**纯数据副本**，只有 `bind/unbind/set/get/push/pushAll/on` 这些会「回写前端」的方法。

### 4.2 ChannelService（`pomelo/lib/common/service/channelService.js`）—— AOI 群推与聊天的共同底座

| 方法 | 作用 |
|---|---|
| `createChannel(name)` / `getChannel(name, create)` / `destroyChannel(name)` | 频道生命周期 |
| `Channel.add(uid, sid)` / `leave(uid, sid)` / `getUserAmount()` / `getMembers()` | 成员管理（**成员 = `{uid, sid}`，即「用户 + 前端服务器」二元组**） |
| `Channel.pushMessage(route, msg, opts, cb)` | 向频道广播 |
| `pushMessageByUids(route,msg,uids,opts,cb)` | **按 `{uid,sid}` 列表推送：内部 `add(uid,sid,groups)` 按 sid 分组，再 `sendMessageByGroup` 逐组 RPC 到各前端** |
| `pushMessageByUid(route,msg,{uid,sid},opts,cb)` | 单点推送 |
| `broadcast(stype, route, msg, opts, cb)` | 按前端类型全广播（`opts.binded` / `opts.filterParam`） |
| `restoreChannel` / `addToStore` / `loadAllFromStore` | **频道状态持久化到 store**（跨进程/重启恢复），基于 `genKey(name)`、`genValue(sid,uid)` |

**回调用例——⚠️ 这是一个「看起来很好但实际是坏的」实现（已核验）：** `domain/messageService.js#errHandler(err, fails)` 遍历 `fails` 调 `pomelo.app.areaManager.removePlayerByUid(fails[i])`，意图是**把「推送不到的 session」当成「玩家已断线」从场景里清掉（惰性掉线检测）**。

**但它不工作。** 核验链路：

| 步骤 | 代码 | 事实 |
|---|---|---|
| 1 | `channelService.pushMessageByUids` → `add(record.uid, record.sid, groups)`（`channelService.js:358`） | 分组结构是 `groups[sid] = [uid, ...]` |
| 2 | `sendMessageByGroup` 里 `failIds.concat(fails)`，最终 `cb(null, failIds)`（`channelService.js:410-435`） | **`fails` 装的是 `uid`（账号 id）** |
| 3 | `errHandler(err, fails)` → `removePlayerByUid(fails[i])`（`messageService.js`） | 把 uid 当成参数传进去 |
| 4 | `AreaManager.removePlayerByUid(playerId)` → `this.getCanUsedPlayer(playerId)` → `this.players[playerId]`（`areaManager.js`） | **`players{}` 是按 `playerId`（角色 id）索引的** |
| 5 | `Area.addEntity`: `this.players[e.id] = e.entityId; this.users[e.userId] = e.id;`（`area.js:318`） | **项目里 `id`(playerId) 与 `userId`(uid) 是两个不同的键**，正因如此才需要 `users{}` 反查表 |

⇒ **uid ≠ playerId，`this.players[uid]` 必然查不到，函数静默返回（`if (!player) return;`）。所以参考项目的「惰性掉线检测」是一个空操作。**【已确认】

**对 JSTM 的结论修正：不要把它当作「参考项目已验证的优点」来抄。** 正确做法是自己实现，且**必须显式区分两个 id**：`ChannelService` 的失败回调应携带能唯一定位玩家的键（建议直接用 `player_id`，或在推送地址结构里同时带 `uid` 与 `player_id`），再按该键清理。同时注意参考项目的第二层问题：**该回调只挂在定向推送通道上，20+ 处 `channel.pushMessage` 的失败无人处理**（见第 5 节勘误）。

---

## 5. `messageService`：**定向推送**的统一出口（值得 JSTM 直接模仿）

> ### ⚠️ 勘误（初版报告的错误，已核验更正）
> 初版把 `messageService` 写成「全服出网**唯一**出口」，**这是错的**。脚本核验 `app/**` 后发现**共 20+ 处直接绕过 messageService 的推送**，
> 集中在 `domain/area/area.js`（`this.channel.pushMessage('onRemoveEntities'/'onRunArea'/'onDragArea'/'onUserLeave')`）、
> `domain/area/areaLogic.js`（`onFinishFight`/`onRunArea`/`onDragArea`/`onDomainBattle`/`onUpdateDomain`）、
> `domain/entity/team.js`（`onDisbandTeam`/`onUpdateTeam`/`onTeammateLeaveTeam`/`onChat`/`onDragMember2gameCopy`）、
> `services/Guilder.js`（`onChat`/`onApplyGuild`）、`services/chatService.js`（`Event.chat`）。
>
> **真实形态是「两条出网通道，按受众划分」**：
>
> | 通道 | 出口 | 受众 | 用于 | 是否走 messageService |
> |---|---|---|---|---|
> | **A. 定向推送** | `messageService.pushMessageToPlayer / ByUids / ByAOI / pushLogTipsToPlayer` | 明确的 `{uid, sid}` 集合（单人 / AOI 结果集） | 实体增删同步、移动广播、错误提示 | ✅ 是 |
> | **B. 频道广播** | `channel.pushMessage(route, msg)`（`area.getChannel()` / `guild.getChannel()` / `team.channel`） | 频道全体成员 | 场景事件（城战/战斗结果/玩家离开）、公会/队伍聊天与通知 | ❌ 否，直接打频道 |
>
> **对 JSTM 的正确结论**：不要照抄「唯一出口」，而应照抄**「按受众分两条通道」**——定向推送收口到一个 `MessageService`，频道广播收口到一个 `ChannelService`，
> 两者都最终调用**同一个底层 `send(player, route, msg)`**。参考项目在这里有两个叠加缺陷：
> ① 两条通道各自直接调 `channelService`/`channel`，没有共同的底层落点；
> ② 唯一的错误回调 `errHandler` 既**只挂在通道 A** 上，又**因为 uid/playerId 类型错配而实际是空操作**（详见上文核验链路）。
> ⇒ JSTM 应把两者收敛到同一个 `send`，统一挂错误处理，并在推送地址里显式携带 `player_id`。

`lordofpomelo/game-server/app/domain/messageService.js`【已确认】（下表仅覆盖通道 A）

| 函数 | 工作机制 | 适合 JSTM |
|---|---|---|
| `pushMessageByUids(uids, route, msg)` | `pomelo.app.get('channelService').pushMessageByUids(route,msg,uids,errHandler)` | ✅ |
| `pushMessageToPlayer({uid,sid}, route, msg)` | `channelService.pushMessageByUid` | ✅ |
| `pushMessageToPlayerEntity(player, route, msg)` | 从 `player.serverId` + `player.userId` 拼 uid 后转发 | ✅ **「实体自带回包地址」**是关键设计 |
| `pushLogTipsToPlayer(player, errorCode)` | 查 `dataApi.error_code` 拼 `{code,msg}` → 推 `onLogTips` | ✅ **错误码集中管理**，JSTM 应做 |
| `pushTipsBoxToPlayer(player, errorCode)` | 同上，推 `onTipsBox`（弹窗） | ✅ |
| `pushMessageByAOI(area, route, msg, pos, ignoreList)` | `area.timer.getWatcherUids(pos,[PLAYER],ignoreList)` → `pushMessageByUids` | ✅ **AOI 群推抽象成一个函数**，JSTM 必做 |

---

## 6. 聊天为什么「看起来独立、实际不独立」

| 证据 | 位置 | 结论 |
|---|---|---|
| 有完整 `app/servers/chat/{handler,remote}` 与 `app.configure(...,'chat',fn)` | `app.js`、`app/servers/chat/**` | 设计上**是**独立服务 |
| `config/servers.json` **没有** `chat` 项 | `config/servers.json` | 实际**没有** chat 进程 |
| `adminServer.json` 仍列 `chat` 与 `path` | `config/adminServer.json` | 残留声明（`path` 连目录都没有） |
| **`app/consts/handleRemote.js` 把所有 chat RPC 硬编码改指 manager** | `consts/handleRemote.js`：`handleRemote.chatRemote_add = (…) => pomelo.app.rpc.manager.chatRemote.add(…)` 等 6 个 | **真正的「适配层」，调用方只依赖 handleRemote，不再关心聊天在哪台** |
| `manager` 有 `handler/chatHandler.js`（**唯一有 `send` 的地方**）和 `remote/chatRemote.js` | `servers/manager/**` | 聊天逻辑已迁入 manager |

**`handleRemote.js` 是本次审计中最值得 JSTM 借鉴的「迁移模式」：** 当把一个功能从 A 进程搬到 B 进程时，**加一层薄转发模块，让所有调用点不动**。JSTM 从多进程设计合并到单进程时，用同样手法可以把「跨进程调用」逐个改成「函数调用」，改造成本极低。

聊天频道与广播链路（`servers/manager/handler/chatHandler.js#send`）【已确认】：

| 频道 | `Channel` 常量 | 目标 | 走哪条路 |
|---|---|---|---|
| 世界 WORLD | 1 | 全局频道 `"pomelo"` | `chatService.pushByChannel` → `channel.pushMessage('onChat')` |
| 场景 AREA | 2 | `area_<msg.areaId>` | 同上 |
| 阵营/公会 FACTION | 3 | `guild_<guildId>` | `rpc.manager.guildRemote.chatInGuild` → `Guilder.chatInGuild` |
| 队伍 TEAM | 4 | `team_<teamId>` | `rpc.manager.teamRemote.chatInTeam` → `teamManager.chatInTeam` |
| 私聊 PRI | 5 | 发送方 + 接收方各推一次 | `chatService.pushByPlayerId`（先 `checkOnline(toName)`） |
| 系统 SYSTEM | 6 | 全局 | 仅接受 `@` 开头；**`@1\|...` 是内置 GM 发奖后门** |
| 跑马灯 MARQUEE | 7 | 全局 | `pushByChannel` |

内容安全：`checkForbid(chatContent)` 用 `config/data/forbid_word.json`（30 KB）逐词 `indexOf` 后把命中处替换成 `*`（**只替换第一处，未循环**）。富文本物品链接 `<#GkindId|id>` 由 `ChatService.findItem` 解析，回 area 取属性（`rpcInvoke` → `playerRemote.getChatItem`）后进 `chatItems` 池（上限 150）。

---

## 7. 服务端模块扩展：7 个扩展点（表格）

| # | 扩展点 | 触发方式 | 关键代码 | 本项目实例 | 适合 JSTM |
|---|---|---|---|---|---|
| 1 | **新增 serverType** | 改 `servers.json` + 建 `app/servers/<T>/{handler,remote}/` + `app.configure(env,'<T>',fn)` | `pathUtil.getHandlerPath` / `getUserRemotePath`；`appUtil.loadServers` | `trade`、`manager`、`fight`、`chat` | ⚠️ 单进程无需；但**「按业务域分目录 + 显式装配表」**适合 |
| 2 | **新增 handler / remote 方法** | 在目录内加 export | `handlerService.loadHandlers`（`pomelo-loader`）+ `remote.js#getRemotePaths` | 13 个 area handler + 3 个 area remote | ✅ **「文件名即模块名、函数名即方法名」的零注册约定**极适合 |
| 3 | **handler 热重载** | `app.load(pomelo.server, {reloadHandlers:true})` | `handlerService.watchHandlers`（`fs.watch` + 重新 `Loader.load`） | 未启用 | ✅ 私服开发期极有用（Python 可用 `importlib.reload`） |
| 4 | **过滤器** | `app.filter()` / `app.before()` / `app.after()` / `app.globalFilter()` / `app.rpcFilter()` | `application.js` `Application.{filter,before,after,globalFilter,rpcFilter}` + `filterService.js` | `playerFilter`（area）、`pomelo.filters.toobusy()`（全局 production） | ✅ **强适合**（中间件链） |
| 5 | **组件 component** | `app.load(componentFactory, opts)`；生命周期 `start/afterStart/stop` | `application.js` `Application.load`；`appUtil.loadDefaultComponents` | `pomelo-sync-plugin`（`app.use(sync,...)`） | ✅ 思想适合（JSTM 的「子系统注册 + start/stop」） |
| 6 | **插件 plugin** | `app.use(plugin, opts)`：插件可带 `components/`、`events/`、`crons/` 目录，框架自动 scan | `application.js` `Application.use`（`dir = path.dirname(plugin.components)`；按 `Constants.DIR.COMPONENT/EVENT` 扫描） | `pomelo-sync-plugin`；`pomelo-masterha-plugin`（注释） | ⚠️ 部分：Python 无同名机制，但**「插件目录约定 + 自动装载」**可用 `pkgutil`/入口点复刻 |
| 7 | **admin 监控模块** | `app.registerAdmin(module, opts)`；模块实现 `monitorHandler/masterHandler/clientHandler` | `util/moduleUtil.js#loadModules`；`application.js#registerAdmin` | `app/modules/onlineUser.js`（在线用户数）、`sceneInfo.js`（**注册代码被注释**） | ✅ 思想适合（私服运维面板）；本项目 `app/modules/sceneInfo.js` 恰好是**给场景服看 AOI/玩家数的模板** |

**`app/modules/onlineUser.js` 实现细节（可作为 JSTM 运维面板模板）【已确认】：**
```js
module.exports.moduleId = 'onlineUser';
Module = function(opts){ this.app=opts.app; this.type=opts.type||'pull'; this.interval=opts.interval||5; }
monitorHandler(agent,msg){ agent.notify('onlineUser', this.app.components.__connection__.getStatisticsInfo()); }  // 各前端上报
masterHandler(agent,msg){ if(!msg){ agent.notifyByType('connector','onlineUser'); return; }  // 定时拉
                          var d = agent.get('onlineUser')||{}; d[msg.serverId]=msg; agent.set('onlineUser', d); }
clientHandler(agent,msg,cb){ cb(null, agent.get('onlineUser')); }  // 控制台读
```

---

## 8. 本文件涉及的「不适合 JSTM」清单（明确排除）

| 项 | 原因 |
|---|---|
| `pomelo/lib/components/connector.js`（全文件） | 绑定 hybridconnector 握手/心跳/编码协议、`__session__`/`__pushScheduler__` 组件耦合 |
| `pomelo/lib/connectors/**`（hybrid/switcher/tcp/ws/mqtt/sio/udp 共 20 文件） | 网络传输层整体作废；JSTM 用 Python socket/asyncio |
| `pomelo-rpc`（外部：`components/{remote,proxy}.js` 里的 `require('pomelo-rpc')`） | 进程间 RPC 在单进程内是纯开销 |
| `server/server.js#doForward` | 跨进程转发 |
| `components/master.js` / `master/starter.js` / `master/watchdog.js` / `modules/masterwatcher.js` | 多机部署与进程守护 |
| `node-zookeeper-client` / `masterha` 相关 | 分布式高可用 |
| `config/dictionary.json`（route → 数字压缩表） | 是为省移动网络流量设计的；JSTM 面向本地/局域网可忽略（**但要留意 1.4.9 客户端是否已内置该字典**） |
| `useCrypto`（RSA 验签，`node-bignumber`） | 未启用；若启用也不适合照抄 |
