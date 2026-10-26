# Survive 架构审计（逐文件 · 类/函数级）

> 审计对象：`C:\Users\xu\Desktop\DSH\cankao\Survive-master.zip`（207.7 MB / 2618 文件）
> 审计方法：Python + `zipfile` **按需读取**（未解压、未修改 `cankao/` 与 `server/` 下任何文件）
> 状态标记：【已确认】= 直接读到源码/文档；【待验证】= 读到代码但语义存疑；【未知】= 未读到
> 目标项目：**JSTM（《绝世唐门》1.4.9 私服兼容服务端）**，现状为 **单进程 Python + SQLite + 自研 Protocol Adapter**（见 `../FINAL_SERVER_ARCHITECTURE.md`）

---

## 一、结论速览

| 项 | 结论 | 状态 |
|---|---|---|
| 项目性质 | 用 **distri.lua** 框架写的**小型手游服务端示例**（副本玩法 ARPG，猫狗题材） | 【已确认】 |
| 语言构成 | 游戏逻辑 **全部 Lua**；AOI / astar / 网络 / redis / 定时器等为 **C 模块**（`distrilua` 二进制） | 【已确认】 |
| 服务划分 | **gateserver（可多台）/ groupserver（唯一）/ gameserver（1~n 场景）** 三件套 + 可选 notiserver | 【已确认】 |
| 通信方式 | 全部 **TCP 长连接**；客户端协议为自定义二进制包；服务间另有 **自研 RPC**（同一条 TCP 上复用） | 【已确认】 |
| 启动方式 | `./distrilua <server>.lua` 逐进程手工启动；或用 `daemon.lua` + PHP 管理台（`php/manage.php`） | 【已确认】 |
| 配置来源 | `setconfig.lua` 把部署表写进 **redis hash `deploy`**；各进程启动时 `common/config.lua` 反查自己该监听哪个 ip/port | 【已确认】 |
| 持久化 | **redis/ssdb**（文档同时提到两者），`common/db.lua` + `lua/redis.lua`（C 模块 `CRedis`） | 【已确认】 |
| 线程模型 | 官方 README 明写「逻辑服务采用**单进程单线程**」；并发靠**协程调度器** `lua/sche.lua` | 【已确认】 |
| 与 JSTM 的根本差异 | Survive 是 **多进程 C+Lua + 网关分层 + Redis**；JSTM 是 **单进程 Python + SQLite 直连**。**架构形态不可照搬，分层思想可借鉴** | 【已确认】 |

---

## 二、目录与文件规模（实测 `namelist()` 计数）

| 顶层目录 | 文件数 | 内容 | 状态 |
|---|---|---|---|
| `php/` | 1267 | Web 运维台（`manage.php` / `control_action.php` / `webix` 前端库） | 【已确认】 |
| `client/` | 1170 | Cocos2d-x 客户端 `src/` + 资源 `res/` + `runtime/win32/battle.exe` | 【已确认】 |
| `common/` | 67 | 配置表 `Table*.lua`（40+）+ 共享模块 + **C 源码**（aoi/astar/encode/decode/wordfilter） | 【已确认】 |
| `gameserver/` | 27 | **16 个 .lua** + 11 个 `.meta` 寻路碰撞文件 | 【已确认】 |
| `groupserver/` | 20 | **19 个 .lua** | 【已确认】 |
| `gateserver/` | 3 | **2 个 .lua** | 【已确认】 |
| `notiserver/` | 6 | 5 个 .lua，**主体被整段注释掉**（未完成） | 【已确认】 |
| `netcmd/` | 3 | `netcmd.lua`（命令号表）+ `msghandler.lua`（分发） | 【已确认】 |
| `lua/` | 15 | distri.lua 的 **Lua 层框架**（协程/套接字/RPC/定时器…） | 【已确认】 |
| `doc/` | 8 | 中文架构文档 4 篇 + 流程 JPG 4 张 | 【已确认】 |
| 根目录 | 6 | `README.md` `Makefile` `setconfig.lua` `daemon.lua` `robotclient.lua` `distrilua`(2.6 MB 二进制) `aoi.so` `astar.so` `cjson.so` | 【已确认】 |

**★ 关键发现：框架 C 核心是二进制**——`distrilua`（2,692,440 字节）无源码；
`Makefile` 只编译 `aoi.so` / `astar.so`，且依赖 **`../KendyNet/libkendynet.a`、`../deps/lua-5.2.3/src`**，
**这两个依赖在 ZIP 内不存在** ⇒ 【已确认】**本项目在 ZIP 内不可完整重编译**。

`distrilua` 二进制中提取到的 Lua 侧 C 模块名（ASCII 串）【已确认】：
`C` `CSocket` `CPacket` `CLog` `CRedis` `CHttp` `CTimeUtil` `CMinHeap` `CBase64`
以及内建库 `base/coroutine/table/string/math/io/os/package/debug/bit32/utf8`（**Lua 5.2 系**）。
运维相关：`C.ForkExec` `C.StopProcess` `C.KillProcess` `C.AddTopFilter` `C.Top` `C.RunOnce` `C.GetSysTick`。

---

## 三、服务划分（README + doc/README.md 原文，两者一致）

| 服务 | 部署量 | 职责（原文摘要） | 状态 |
|---|---|---|---|
| **gateserver** | 可多台 | 前端连接服务器：保持与客户端的长连接，把客户端消息转发到内部服务器组，把内部消息转发给玩家 | 【已确认】 |
| **groupserver** | 只有一台（中心服务器） | 账号验证、角色创建、角色数据保存、基本游戏逻辑、**副本管理**（排队/分配实例） | 【已确认】 |
| **gameserver** | 1~n 场景/进程 | 战斗及地图服务：玩家在场景中的移动、战斗；**单线程，每个服务上可加载 1-n 个场景** | 【已确认】 |
| **notiserver** | — | 通知/邮件服务；**源码存在但 `notiserver.lua` 主体整段被注释** | 【已确认】 |

### 3.1 连接拓扑（【已确认】，由代码中的 Connect/Listen 调用点反推）

```
  客户端 ──TCP──▶ gateserver ──TCP──▶ groupserver ──TCP(反连)──▶ gameserver
                      │  ▲                                          ▲
                      │  └──────────── 广播/通知（CMD_GA_*） ───────┘
                      └──────────── 转发到 game（CMD_CS_*） ────────┘
  gameserver ──启动时主动 Connect──▶ groupserver（GameLogin RPC）
  gateserver ──启动时主动 Connect──▶ groupserver（GateLogin RPC）→ 拿到 game 列表 → 逐个 Connect gameserver（Login RPC）
```

- **groupserver 从不主动连谁**，只被动 Listen（`groupserver/groupserver.lua: TcpServer.Listen`）。
- **gate 与 game 都反连 group**；game 上线后由 group 用 `CMD_GA_NOTIFY_GAME` 通知所有 gate，gate 再去连 game。 【已确认】
- 所有连接均为**长连接**（`doc/README.md`：图中所有连接线均表示 tcp 长连接）。 【已确认】

**★ 与作者结构图的差异（`diagram_crosscheck.md` G1/G2，【已确认】）**
| 项 | `doc/服务器结构图.jpg` | 代码 | 结论 |
|---|---|---|---|
| **DB 连线** | `gateserver`、`groupserver`、**`gameserver` 三者都连**"帐号数据库 + 角色数据库" | `gameserver.lua` **没有 `Db.Init`、不 require `common/db`** ⇒ **game 完全不碰 DB** | **图 ≠ 代码**：代码把数据职责**更彻底地**集中到 group ⇒ 我在 §7 对「场景进程无状态」（D26）的正面评价**成立且被强化**，且属**代码超越文档**之处 |
| **角色库实例数** | 角色数据库画成 **3 个叠放圆柱**（多实例）；`doc/README.md` 亦写"角色库可部署多个、按 chaid hash 分布" | `common/db.lua` **只有单一 `toredis` 单连接**，零分片代码 | **设计有、代码无**（已记入 `database.md` §6，此处补图证据） |

> 方法学：读图非无损，**凡图与代码冲突处，一律以代码为准**（代码是可复读原文）。另见 `diagram_crosscheck.md` G3（登陆流程图中"角色数据由 gate 读"与代码"由 group 读"不一致）与 G6（图**不含** AOI/断线重连，二者只在代码里）。

---

## 四、启动顺序与配置（实测）

```
1) 启动 redis/ssdb
2) ./distrilua setconfig.lua          # 把 deployment 表写入 redis: hmset deploy <key> <json>
3) ./distrilua groupserver/groupserver.lua
4) ./distrilua gameserver/gameserver.lua
5) ./distrilua gateserver/gateserver.lua
```

| 文件 | 类/函数 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `setconfig.lua` | 顶层脚本 | `Db.Init("127.0.0.1",6379)` → `Db.CommandSync("hmset deploy <key> <cjson(deployment)>")`；`deployment` 是 `{"db"=..., "group"=..., "gate1"=..., "game1"=...}` 的 ip/port 表 | ⚠️ 部分适合 | **"用中心配置库下发监听地址"**这一思想对 JSTM 有价值（多开/换端口免改代码）；但 JSTM 目前单进程、配置在 `config.json`，**引入 Redis 只为一个 ip 表是过度设计**。可借鉴为「配置文件 + 热重载」 |
| `common/config.lua` | `Init(key,ip,port)` / `Get(key)` | 连接配置库 → `hmget deploy <key>` → `cjson.decode` 存为模块级 `deployment`；`Get` 返回 `deployment[key]`（形如 `{ip,port}`） | ⚠️ 部分适合 | 设计思想（**进程按名字取自己的地址**）适合；实现（模块级单例 + 全局 redis 连接 + `while not toredis do Sleep(100) end` 忙等）不适合 JSTM 的同步单进程模型 |
| `gameserver/gameserver.lua` | 顶层脚本 | `Config.Init("测试1服","127.0.0.1",6379)` → 取 group/game1 地址 → `App.New()` → 注册 `Gate.RegRpcService` / `Map.RegRpcService` → `connect_to_group()` 反连 group 并 `RPC.MakeRPC(sock,"GameLogin"):CallSync("game1",ip,port)` → `TcpServer.Listen(ip,port,...)` 等 gate 连进来 | ⚠️ 部分适合 | **"逻辑进程启动先向中心注册、再开监听"**的顺序值得借鉴；`Exit()` 直接杀进程（无重试/无退避）不适合 JSTM 稳定性要求 |
| `gameserver/gameserver.lua` | `Send2Group(wpk)`（全局函数） | 把包直接投到与 group 的那条 socket | ⚠️ 部分适合 | 全局函数 + 全局 socket 变量是最简 RPC 发送方式；JSTM 单进程不需要，但可借鉴为「连接句柄集中注册表」 |
| `groupserver/groupserver.lua` | 顶层脚本 | `Config.Init` → `Db.Init` → `while not Db.Finish() do Sche.Yield() end`（**等 redis 连上才继续**）→ `App.New(65536)` → 注册 `Gate/Game/Player` 三个 RPC 服务 → `TcpServer.Listen` | ⚠️ 部分适合 | **先等外部依赖就绪再对外服务**是对的，值得借鉴；`App.New(65536)` 这个参数（recver 协程上限）不适合 Python 模型 |
| `gateserver/gateserver.lua` | 顶层脚本 | `Config.Init` → 建两个 App：`toinner`（内部连接）与 `toclient`（客户端连接）→ `connect_to_group()`（GateLogin，拿回 game 列表后逐个 `connect_to_game`）→ **等 `togroup` 与 `Db.Finish()` 都就绪才 Listen 客户端端口** | ✅ 适合（思想） | **"依赖未就绪不对外监听"** + **"客户端连接与内部连接分成两个 App/两套回调"**这两点非常适合 JSTM：JSTM 的 `mock_server.py` 目前是一条连接一套逻辑，可以照此把「客户端入口」与「后端/DB」解耦 |
| `daemon.lua` | 顶层脚本 + `RunDaemonServer()` | 监听 `127.0.0.1:8800` 接受 PHP 的 JSON 指令（Start/Stop/Kill）→ `C.ForkExec("./distrilua",luafile,group,logicname)` / `C.StopProcess(pid)` / `C.KillProcess(pid)`；主循环每秒 `C.Top()` 采机器/进程状态，`CBase64.encode(cjson(...))` 后写 redis `hmset MachineStatus <ip> ...` | ⚠️ 部分适合 | **"进程状态上报中心库 + Web 一键启停"**是很好的运维思想（JSTM 的 17 个 GM 动作可扩展成同类控制面）；但 `C.ForkExec/Top/StopProcess` 是 distri 专有 C API，JSTM（Python）**完全不能照抄**，只能自写 `subprocess`/`psutil` 版本 |
| `doc/管理系统.md`、`doc/系统部署与管理.md` | 文档 | 描述区/组/服务逻辑名（`groupname:logicname`）、`router:8888`、`daemonserver:8889`、`globaldb` 存 `process` 表（key=`world.ip.name`，字段 `info/pid/lastupdate/startcount`）、运维客户端命令（`list world` / `start worldname ip name` / `kill ip pid`） | ⚠️ 部分适合（仅思想） | **【已确认】文档描述的这套 router/daemonserver 体系在 ZIP 内找不到对应源码**（只有简化版 `daemon.lua`）⇒ 属"设计蓝图"，可作为 JSTM 未来多开时的运维参考，**不可当作已实现事实** |
| `robotclient.lua` | `ConnectAndLogin(name)` + 多个 `MsgHandler.RegHandler` | 起 50 个协程，各自连 gate、发 `CMD_CA_LOGIN`、处理创角/进图/移动/到达后继续随机移动 —— **压测机器人** | ✅ 适合（方法） | **"用协议客户端当压测机器人"**非常适合 JSTM：JSTM 已有真实 1.4.9 协议，写一个 Python 版 bot 即可做回归/压测，比 Survive 的 Lua 版更容易 |
| `testBresenham.lua` | 顶层脚本 | 验证 `Astar.lineto(nil,0,0,5,5)` 的 Bresenham 直线 | ⚠️ 参考 | 最小验证脚本的形式可借鉴（为 AOI/寻路写单点验证） |

---

## 五、框架层：`lua/`（distri.lua 的 Lua 侧）——**逐文件**

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `lua/sche.lua` | `Spawn/SpawnAndRun/Yield/Sleep/Block/WakeUp/Schedule/Running/SwitchTo/add2Ready/Exit` | **自己实现的非对称协程调度器**：就绪链 `ready_list`(LinkQue) + 超时最小堆 `sche.timer`(C 的 `CMinHeap`)；`_block(ms,stat)` 用 `coroutine.yield` 挂起并把协程按 ms 插堆；`Schedule` 每轮把就绪链跑空 → 弹超时堆 → 把本次 yield 的重新入就绪链 | ⚠️ 部分适合 | **"单线程 + 每连接一个协程 + 定时堆"**是核心思想，JSTM 可用 `asyncio` 对应；但**自研调度器（含 `stat_ready/sleep/yield/dead/block/running` 六态机）不需要复刻**——Python 有成熟事件循环。⚠️注意 `SwitchTo` 用 `coroutine.resume` 且**无 resume 返回值/异常检查**（`start_fun` 里 xpcall 兜底），是脆弱点 |
| `lua/socket.lua` | `stream.Listen/Accept/Connect/Recv/Send/SendSync/Establish/process_c_packet_event/process_c_disconnect_event`、`datagram.*`、`socket:new/new2/Close` | 把 C 的 `CSocket` 包成**看起来阻塞的接口**：`Recv` 无包时把自己压进 `block_recv` 链再 `Sche.Block()`；`__on_packet` 回调来时唤醒 `recv_wakeup` 或弹一个等待者；`Establish(decoder,recvbuf)` 绑定解码器（`rpkdecoder`/`rawdecoder`）；断线时 `process_c_disconnect_event` 唤醒所有 recv 等待者 + 遍历 `pending_call` 回调 `remote connection lose` | ✅ 适合（思想） | **"同步写法、异步实现"**是 JSTM 最值得抄的**思想**：目前 Python 版可用 `await` / 或在 `asyncio` 上包一层同步 API。**代码不可抄**（依赖 CSocket/CPacket 专有对象） |
| `lua/application.lua` | `application:new/Add/RPCService`、`recver(app,socket)` | 一个连接一个「收包应用」：`Add(socket,on_packet,on_disconnected,recvtimeout,pinginterval)` 重写 `socket.__on_packet` → 有多余等待协程就 `WakeUp`，否则 `SpawnAndRun(recver)`；`recver` 死循环 `socket:Recv()` → 先 Peek `uint32`，**若为 RPC 命令号则交给 RPC 处理，否则交给 `socket.process_packet`**；另有两个心跳定时器（`recvtimeout` 超时 Close、`pinginterval` 发 `CMD_PING`） | ✅ 适合（思想） | **"同一条 TCP 上先分流 RPC / 再分流业务包"**与**"每个 socket 一个 xpcall 收包循环"**值得借鉴；⚠️**`max_recver_per_socket` 的限流判断在代码中被注释掉了**（`--if socket.recver_count > app.max_recver_per_socket`），即**限流实际失效**【已确认】，这一点**不能照学** |
| `lua/rpc.lua` | `ProcessCall/ProcessResponse/MakeRPC`、`rpcCaller:CallSync/CallAsync/CallNoRet`、`gen_rpc_identity/identity_to_string/init_timeout_checker` | 自研 RPC：命令号 `CMD_RPC_CALL=0xABCDDBCA` / `CMD_RPC_RESP=0xDBCAABCD`；请求体是 **`Write_table`**（`{f=函数名, identity={h=os.time(),l=计数器}, arg={...}, noret=bool}`）；响应 `{identity, ret=table, err=str}`；`CallSync` 用 `Sche.Block()` 挂起，`CallAsync` 用回调；两者**超时 5000ms + 最多重试 2 次**（`minheap:Insert(ctx, tick+5000)`）；服务端按 `s.rpc_record` 做**单调 identity 去重**（防重放） | ✅ 适合（思想，**协议不可抄**） | 值得借鉴的三点：**① 函数名派发的通用 RPC**；**② 调用方的超时+重试**；**③ 服务端的 identity 单调去重**。❌ 不适合照搬：`Write_table` 是 distri 私有序列化；`identity` 用 `os.time():counter` 且比较写成 `if identity.l > ... or identity.h > ...`（**应为 and**，是缺陷）【已确认】 |
| `lua/timer.lua` | `timer:New/Register/Remove/Stop/Run` | 每个 Timer 一个 `CMinHeap`；`Register(callback,ms)` 插 `GetSysTick()+ms`；`Run()` 是**常驻协程**，`Pop(now)` 取到期项执行，**回调返回 nil 表示要续期**（`self:Register(v.callback,v.ms,...)`），返回非 nil 则停止 | ✅ 适合（思想） | **"返回 nil 就续期、返回字符串就停表"**这个延续约定很省代码，JSTM 的定时任务（心跳/日重置/在线奖励）可直接采用；⚠️ `Stop` 只置标志，重启要小心 |
| `lua/alarmclock.lua` | `SetAlarm/CheckAlarm/RemoveAlarm` | **墙上时钟闹钟**：`alarmtime={year,mon,day,hour,min,sec}` → `CTimeUtil.GetTS(...)` 换算成时间戳；同样时间戳的闹钟聚成一个 `slot`（`LinkQue`）由最小堆排序；内部起一个 1000ms 的 `Timer` 轮询 `Pop(os.time())` | ✅ 适合（思想） | **"到点触发（每日 5:00 重置等）"**对 JSTM 的每日任务/签到/限时活动直接有用；`CTimeUtil` 是 C 模块（**它是 UTC 还是本地时区未读到文档**）【待验证】。JSTM 应用 Python `datetime`+时区显式处理 |
| `lua/linkque.lua` | `LinkQue:new/Push/Front/Remove/Pop/IsEmpty/Len` | **侵入式双向链表**（哨兵 head/tail；节点自带 `__pre/__next/__owner`，**已在某个队列的节点再次 Push 会被拒绝**——防重复入队） | ✅ 适合（思想） | **"节点自带 owner、可 O(1) 从队列中间摘除"**对 JSTM 的场景实体/怪物列表管理有参考价值（Python 用 `OrderedDict`/`set` + 懒删除等价） |
| `lua/queue.lua` | `Que:Push/Front/Pop/IsEmpty/Len` | 纯 Lua table 数组队列（`table.insert` + `table.remove(1)` ⇒ **O(n)**） | ❌ 不适合 | 性能差（每次 Pop 移动整个数组），且 `lua/linkque.lua` 的注释块里已放着更早的链表版实现 ⇒ 属**被淘汰的旧实现** |
| `lua/lock.lua` | `lock:Lock/Unlock` | 协程互斥：`while self.flag do 把自己压 block 链; Sche.Block() end`，解锁时弹一个 `Sche.Schedule(co)` | ⚠️ 部分适合 | 单线程下用于保护「查重名 → 写重名」这类**跨协程等待的临界区**是必要的（见 `groupplayer.lua:_checkDuplicateName`）；JSTM 单进程同步模型可用普通锁/事务替代 |
| `lua/channel.lua` | `channel:Send/Recv` | 协程间消息队列（`chan` + `block`），`Recv` 无消息则挂起 | ⚠️ 部分适合 | 可用于 actor 式解耦；但 JSTM 单进程不需要跨协程通道 |
| `lua/redis.lua` | `Connect(ip,port,on_disconnected)`、`redisconn:CommandSync/CommandAsync/Close` | 包装 C 的 `CRedis`：`CommandSync` 把当前协程做成 `cbObj.co` 挂起，C 回调回来 `Sche.WakeUp`；`CommandAsync` 直接给回调；断线由 `__on_disconnected` 触发重连回调 | ⚠️ 部分适合 | **"同步接口包异步驱动"**思想同 `socket.lua`；❌ 不可抄代码；JSTM 用 sqlite3（同步）即可，无需此层 |
| `lua/http.lua` | `http_server:CreateServer/Listen`、`http_response:WriteHead/End/Send`、`process_server` | 用 C 的 `CHttp` 解码器做**极简 HTTP 服务**（`Transfer-Encoding: chunked`，`Date` 头**硬编码**为 `Tue, 26 Aug 2014`） | ❌ 不适合 | 玩具级实现（硬编码日期、无 keep-alive 语义、`Read_string` 拼包）；JSTM 若需 HTTP（GM 后台）应用现成框架 |
| `lua/tcpserver.lua` | `Listen(ip,port,process)` | 15 行的封装：`Socket.Stream.New` → `Listen` → `Sche.Spawn` 死循环 `Accept` → 每个连接 `Sche.Spawn(process, sock)` | ✅ 适合（思想） | **"一个 Accept 协程 + 每连接一个处理协程"**是最小可用服务器骨架，JSTM 网络层可直接对应 |

**★ 框架层最重要的三点【已确认】**
1. `application.lua` 的 `CMD_PING = 0xABABCBCB` 与 `rpc.lua` 的两个魔术号是**框架级保留号**，与业务命令号空间不冲突。
2. 业务包与 RPC 包**共用一个 socket**，靠 `Peek_uint32` 分流——这是 distri 的核心设计。
3. `distri.lua`（`lua/distri.lua`）本身只有：`push_c_callback` / `push_c_obj_callback` / `process_c_callback`（把 C 侧回调搬进协程里执行）/ `Exit` / `distri_lua_start_run`（`loadfile` 主脚本 + `Spawn` + `while C.RunOnce(ms,50)` 主循环）。**主循环只有 `C.RunOnce` + `Sche.Schedule` 两步。**

---

## 六、消息/命令号体系（`netcmd/netcmd.lua`）——【已确认】

命令号按**通信方向分段**（`SetCmdNum` 定段首，`NextCmdNum` 自增）：

| 段 | 起始 | 含义 | 走向 |
|---|---|---|---|
| `CMD_CA_*` | 0 | client ↔ auth/gate（仅 `CMD_CA_LOGIN`） | 客户端 → gate |
| `CMD_CS_*` | 200 | client ↔ game：`MOV` / `USESKILL` / `PICKUP` | 客户端 → game（gate 转发） |
| `CMD_SC_*` | 300 | game → client：进图/入视野/离开视野/移动/到达/攻击/受击/属性/ Buff / 5PVE 轮次/结算/背包/爆炸/胜负/换武器 | game → gate → 客户端 |
| `CMD_CG_*` | 400 | client ↔ group：创角/进图/离图/领奖/道具/换位/加点/聊天/家园/装备强化升星镶嵌/技能升级/签到/任务/成就/合成/好友/宝石/邮件 | 客户端 → gate → group |
| `CMD_GC_*` | 500 | group → client | group → gate → 客户端 |
| `CMD_AG_*` | 600 | group → gate：`CMD_AG_CLIENT_DISCONN`（客户端断线通知） | group → gate |
| `CMD_GA_*` | 700 | group → gate：`CMD_GA_NOTIFY_GAME`（新 gameserver 上线） | group → gate（广播） |
| `CMD_GGAME_*` | 800 | game → group：`CMD_GGAME_CLIDISCONNECTED` | game → group |
| `CMD_GAMEG_*` | 900 | game → group：生存赛结束/5V5 奖励/5PVE 奖励/踢人 | game → group |
| `CMD_CC_*` | 65530~65534 | dummy：连接成功/失败/断线/单人副本结果/Ping | — |

**★ 与 JSTM 的对照**：JSTM 是 `[u32 len][u16 cmd][body]` 的**单一扁平命令号空间**（`_observed_cmds.txt` / `proto_defs.py`）。
Survive 的**分段编号**（每 100 号一段、段名编码方向）是一个**可选的组织手段**，但 **JSTM 已被 APK 锁死命令号，不可改编号**，只能借鉴「段内按域再分子段」的**命名规范**。

**★ `msghandler.lua` 的注册模式【已确认】（值得借鉴）**
```lua
local handler = {}
local function regHandler(cmd,f) handler[cmd] = f end
local function onMsg(sock,rpacket)
    local cmd = rpacket:Read_uint16()
    local f = handler[cmd]
    if f then f(sock,rpacket) else print("unknow cmd",cmd) end
end
```
- **命令号 → 函数**的注册表，各业务文件在**自己被 require 时**用 `MsgHandler.RegHandler(NetCmd.CMD_XX, function(sock,rpk) ... end)` 自注册。
- **这正是 `FINAL_SERVER_ARCHITECTURE.md` 第二节建议 JSTM 从「单文件 if 链」改为「cmd → handler 注册表」的现成范例。** ✅ 高度适合借鉴。

---

## 七、与 JSTM 的整体对照（架构级）

| 维度 | Survive | JSTM 现状 | 结论 |
|---|---|---|---|
| 进程形态 | gate/group/game 多进程（文档称世界级可配 N 组） | 单进程 Python | ❌ **不可照搬**（JSTM 已有可跑通的单进程闭环，多进程是过度设计） |
| 语言 | Lua（逻辑）+ C（框架/网络/AOI/寻路） | Python | ❌ 不可照搬 |
| 并发模型 | 自研协程调度器（单线程） | 同步/可能 asyncio | ⚠️ **思想可借鉴**（每连接/每实体一个协程） |
| 协议 | 自定义二进制 + 私有 `Write_table` RPC | **1.4.9 原版协议（最大资产）** | ❌ **绝对不能借鉴其协议**；JSTM 已有真协议 |
| 数据 | Redis/ssdb，角色按 chaid hash 分库 | SQLite 单库 | ⚠️ 分库思想可参考，实现不适配 |
| AOI/寻路 | **C 模块实现，是 JSTM 目前完全缺失的两块** | 无 | ✅ **最值得优先借鉴的部分**（见 `scene.md`） |
| 配置表 | `common/Table*.lua` 明文 Lua 表（40+ 张） | APK 内 347 张 `.luac` 已解出 | ✅ 只是同类物，无需借鉴 |
| 运维 | daemon + PHP 管理台 + redis 状态表 | 17 个 GM 动作（单机） | ⚠️ 「一键启停 + 状态上报」思想可借鉴 |

---

## 八、`gameserver/` 16 个 Lua 文件职责一览【已确认】

| 文件 | 职责 | 详见 |
|---|---|---|
| `gameserver.lua` | 进程入口：读配置、注册 RPC、反连 group、开监听 | 本文件 §4 |
| `gate.lua` | **gameserver 侧**的 gate 连接簿记（`sock2gate`/`name2gate`/`Bind`/`UnBind`/`OnGateDisconnected`/`RegRpcService("Login")`/`BoradCast2Gate`） | `network.md` |
| `map.lua` | 地图实例：加载所有 TableMap 的 astar、建 AOI map、两个定时器（100ms 移动、500ms 实体 Tick）、`findpath`、RPC（`EnterMap`/`EnterSurvive`/`LeaveMap`/`CliReConn`）、`CMD_CS_MOV`/`CMD_CS_USESKILL`/`CMD_CS_PICKUP`/`CMD_GGAME_CLIDISCONNECTED` 处理 | `scene.md` |
| `maplogic.lua` | **具体玩法逻辑**：通用 `maplogic` + `FiveVE`（5人PVE塔防式）+ `FiveVP`（5V5）+ `Survive`（生存赛 12 格缩圈爆炸）+ `area`；`CreateNPC`/`CreateDrop`/`entermap`/`leavemap`/`Tick` | `scene.md` / `battle.md` |
| `avatar.lua` | **非玩家实体基类**（NPC/掉落物/触发器都用它）：AOI 对象、视野表 `view_obj`/`watch_me`、`Send2view`（按 gate 分组打包）、`Mov`/`process_mov`/`StopMov`/`TransferTo`、`PackEnterSee`、`OnDead` | `scene.md` |
| `gameplayer.lua` | **玩家实体**（继承 avatar）：多一个 `groupsession`、`Send2Client`（经 gate）、`on_entermap`、`ReConnect`、`battleitems` | `role.md` |
| `attr.lua` | 实体属性（**索引数组**，`Name2idx` 数字下标）：`Get/Set/Add/Sub/NotifyUpdate/on_entermap/on_entersee`，`attr2view` 白名单只同步 level/life/maxlife | `role.md` |
| `skill.lua` | 技能使用与**伤害结算**：`UseSkill`/`CalDamage`/`process_hp_change`、`notify_atk_*`、特殊脚本 `skill1060`/`skill1120`、`skillmgr`（CD/公共CD） | `battle.md` |
| `buff.lua` | Buff 管理器：`NewBuff`（互斥表 `TableBuff_Nexus`：替换/排斥/打断）、`Tick`、`OnEnterSee`、`OnAvatarDead` | `battle.md` |
| `bufffunction.lua` | Buff 回调函数表（按表名派发）：回血、变速、隐身、眩晕、加成 | `battle.md` |
| `robot.lua` | **AI 状态机**：`state_partol/trace/atk`（+ `_npc` 变体）、`AiTable[1|2]`、`robot:main` 协程循环、`AiUseSkill` 按 `Attack_Types` 分单目标/方向/点选 | `battle.md` |
| `areatrigger.lua` | 区域触发器：Aoi 对象 + **50ms 全局定时器** `RangeCheck` → `OnEnterRange/OnLeaveRange` | `scene.md` |
| `triggerfunction.lua` | 触发器回调表（只有 `TransferTo`：跳到相邻区域） | `scene.md` |
| `battlebag.lua` | **战斗背包**（6 格，位置 5~10）：`AddItem/RemItem/NotifyUpdate/on_entermap/Save` | `role.md` |
| `snail.lua` | 预计算 4×3 网格的**螺旋遍历方案**（全排列搜索），供生存赛爆炸顺序使用 | `battle.md` |
| `util.lua` | 纯函数工具：`Pixel2Grid`(grid=8) / `Grid2Pixel` / `Distance` / `TooLong` / `TooClose` / `CheckOverLap` / `Dir` / `DirTo` / `ForwardTo` / `SplitString` | `scene.md` |

---

## 九、【未读到】与【未知】（严格遵守"不猜"）

| 项 | 状态 |
|---|---|
| distri.lua 框架的 **C 源码**（`distrilua` 二进制对应的工程） | 【未读到】ZIP 内只有二进制与 `Makefile`（Makefile 指向不存在的 `../KendyNet`、`../deps/lua-5.2.3`） |
| `aoi.so` / `astar.so` / `cjson.so` 的**编译产物来源** | 二进制在 ZIP 根目录，C 源码在 `common/`（可读），但无构建脚本一次性产出（见 `Makefile`） |
| `notiserver` 是否曾运行 | 【未知】`notiserver.lua` 主体为注释；`mailservice.lua` 仅空函数骨架 |
| `php/` 管理台的具体接口 | 【未读到】（1267 文件，本轮聚焦服务端逻辑；仅从 `daemon.lua` 反推其下发 JSON 的格式） |
| `doc/*.jpg`（4 张流程图：服务器结构图/登陆流程/角色创建/玩家进入地图） | ✅ **已补齐**：4 张已用视觉模型逐张读取并**逐条与代码交叉核对** ⇒ 见 **`diagram_crosscheck.md`**（发现 **7 处「图 ≠ 代码」**，关键 2 处：**G1** game 连 DB / **G3** 角色数据由谁读；另 **G6**：图**不含** AOI 与断线重连，二者只在代码里）⚠️ 读图非无损，冲突处**以代码为准** |
| 地图 `.meta` 碰撞文件格式 | 【部分已确认】从 `common/lua_astar.c` 的读取逻辑可确认：**首行 xcount，次行 ycount，随后 x*y 个（逗号分隔）整数阻塞位** |
| 客户端与服务器的**打包/解包严格字节序** | 【待验证】服务端侧只见 `Write_uint16/uint32/uint8/string/wpk`，其字节序由 C 模块 `CPacket` 决定，**未读到 C 源码** |
| 是否有 LICENSE | 【已确认】**ZIP 内无任何 `LICENSE/COPYING/NOTICE` 文件**；但 `common/aoi.h`、`common/astar.h`、`common/wordfilter.h` **文件头内嵌 GPLv3 声明**（`Copyright (C) <2012> huangweilook@21cn.com`）⇒ 见 `reuse_candidates.md` §4 |

---

## 十、审计边界声明

- 本次审计**只读**：使用 `zipfile.namelist()/read()`，未解压、未写入 `cankao/` 与 `server/` 任何文件。
  （唯一例外：把 `doc/` 下 4 张流程 JPG **释放到 `analysis/_tmp/survive_doc/`** 以便用视觉模型读取——**源 ZIP 未被修改**。）
- 所有结论均可回溯到 `gameserver/`、`groupserver/`、`gateserver/`、`common/`、`lua/`、`netcmd/`、`doc/`、根目录的原文。
- 本文件与 `network.md` / `role.md` / `scene.md` / `battle.md` / `database.md` / `reuse_candidates.md` 构成一套完整审计。
- **R3 续作（第二轮）**：`jstm_mapping.md`（26 设计点 × JSTM 现状 + 4 条自我修正）、`aoi_pathfind_review.md`（对 `server/aoi.py`+`pathfind.py` 的对照审查）、`diagram_crosscheck.md`（本文件 §3.1/§9 的图证据）。
