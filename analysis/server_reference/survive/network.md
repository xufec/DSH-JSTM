# Survive 网络层审计（逐文件 · 类/函数级）

> 对象：`cankao/Survive-master.zip` 中 `gateserver/`、`netcmd/`、`lua/{socket,application,rpc,tcpserver,distri}.lua` 及三端进程入口
> 状态标记：【已确认】【待验证】【未知】；方法：`zipfile` 按需读取原文
> 对照目标：**JSTM**（单进程 Python，线格式 `[u32 BE len][u16 BE cmd][body]`）——其协议**已由 APK 锁定，不可改**

---

## 一、结论速览

| 项 | 结论 | 状态 |
|---|---|---|
| 连接谁 | 客户端 → **gate**；gate → **group**；gate → **game**；game → **group**（反连）；group **从不主动连** | 【已确认】 |
| 协议载体 | distri 自研二进制包，由 C 模块 `CPacket`/`CSocket` 提供；**字节序未知（C 源码未读到）** | 【待验证】 |
| 一包多协议 | **同一条 TCP 上混跑 RPC 包与业务包**，靠 `Peek_uint32` 读命令号分流 | 【已确认】 |
| 业务命令号 | `netcmd/netcmd.lua` 分段编号（0/200/300/400/500/600/700/800/900/655xx） | 【已确认】 |
| 分发机制 | `netcmd/msghandler.lua`：`cmd → handler` **注册表**，各业务文件自注册 | 【已确认】 |
| 路由附加信息 | gate → group 在**包尾**追加 `u16 groupsession`；gate → game 在**包尾**追加 `u32 gamesession`；接收方用 `Reverse_read_*` **从尾部读** | 【已确认】 |
| 广播优化 | 内部 → gate 时，包尾附**接收者 sessionid 列表**，gate 拆开后逐个发；**同一 gate 的玩家只发一份包体** | 【已确认】 |
| RPC | 自研（`lua/rpc.lua`）：魔术命令号 `0xABCDDBCA/0xDBCAABCD`，函数名派发，`Write_table` 序列化，**超时 5s + 重试 2 次 + identity 去重** | 【已确认】 |
| 心跳 | 框架提供 `CMD_PING=0xABABCBCB` + `recvtimeout`/`pinginterval`，但 **本项目三端均未启用** | 【已确认】 |
| 限流 | `application.lua` 的 `max_recver_per_socket` 判断**被注释掉** ⇒ 实际无限流 | 【已确认】 |
| 对 JSTM 的价值 | **「收包循环 + cmd→handler 注册表 + 路由附加信息写尾读尾 + 广播合并」四点高度可借鉴；协议与包格式完全不可借鉴** | 【已确认】 |

---

## 二、连接拓扑与建立顺序【已确认】

```
① groupserver 先起，只 Listen(group_ip, group_port) —— 从不主动连谁
        ▲                                    ▲
        │ GateLogin RPC                      │ GameLogin RPC
        │ (gate 反连)                        │ (game 反连)
② gateserver：connect_to_group() ────────────┘
      拿到 group 返回的 gameserver 列表 ret={{name,ip,port},...}
      对每个 game 调 connect_to_game(name,ip,port) → Login RPC("gate1")
③ gameserver：connect_to_group() → GameLogin RPC("game1",ip,port)
      group 收到后 BoradCast2Gate(CMD_GA_NOTIFY_GAME, name, ip, port)
      → 各 gate 收到后再 connect_to_game(...)（因为 gate 可能比 game 先起）
④ gateserver 等 togroup 与 Db.Finish() 均就绪后，才 Listen 客户端端口
```

| 文件 | 函数 | 机制 | 状态 |
|---|---|---|---|
| `gameserver/gameserver.lua` | `connect_to_group()` | `Sche.Spawn` 死循环：`Socket.Stream.New` → `Connect(group_ip,group_port)` → `Establish(CSocket.rpkdecoder(65535))` → `gameApp:Add(sock,MsgHandler.OnMsg,connect_to_group)` → `RPC.MakeRPC(sock,"GameLogin"):CallSync("game1",ip,port)`；失败 `sock:Close()` + `Sleep(1000)` 重试 | 【已确认】 |
| `gateserver/gateserver.lua` | `connect_to_group()` | 同上，但 RPC 是 `GateLogin("gate1")`；成功后 `for k,v in pairs(ret) do connect_to_game(v[1],v[2],v[3]) end` | 【已确认】 |
| `gateserver/gateserver.lua` | `connect_to_game(name,ip,port)` | `Sche.Spawn` 死循环 + **已连上就直接 return**（`if name2game[name] and name2game[name].sock then return end`）；连上后 `RPC.MakeRPC(sock,"Login"):CallSync("gate1")`；断线回调里 `Player.OnGameDisconnected(s)` + 置空 `name2game[name].sock` + **递归调用自己重连** | 【已确认】 |
| `groupserver/groupserver.lua` | `TcpServer.Listen(ip,port,function(sock) sock:Establish(CSocket.rpkdecoder(65535)); groupApp:Add(sock,MsgHandler.OnMsg,on_disconnected) end)` | 单一入口，所有内部服务（gate/game）连到同一个端口；`on_disconnected` 按 `sock.type`（在 RPC Login 里被打上 `"gate"`/`"game"`）分派 | 【已确认】 |
| `gateserver/gateserver.lua` | `TcpServer.Listen(ip,port,function(sock) sock:Establish(CSocket.rpkdecoder(4096),1024); toclient:Add(sock,OnClientMsg,Player.OnPlayerDisconnected) end)` | 客户端包解码缓冲 **4096**，接收缓冲 **1024** | 【已确认】 |
| `gameserver/gameserver.lua` | `TcpServer.Listen(ip,port,function(sock) sock:Establish(CSocket.rpkdecoder(65535)); gameApp:Add(sock,MsgHandler.OnMsg,Gate.OnGateDisconnected) end)` | gameserver 的对外端口**只给 gate 连**（客户端不可能直连） | 【已确认】 |

**★ 设计要点（值得借鉴）**：**中心服务器（group）只被连、不主动连**，所以它天然是「单点、无状态外连」；gate 与 game 都是**主动注册方**，注册内容（name/ip/port）由中心**转告**给其他成员，从而避免配置里写死实例列表。JSTM 若多开，这是比"配置文件互指"更可靠的拓扑。

---

## 三、封包格式（逐层还原）

### 3.1 客户端 ↔ gateserver

| 方向 | 格式 | 证据（函数） |
|---|---|---|
| 客户端 → gate | `[u16 cmd][payload...]`（业务/登录包） | `gateserver.lua:OnClientMsg` 先 `rpk:Peek_uint16()` 判断段 |
| gate → 客户端 | 直接转发**内部包的内层 blob**，其首部已是 `[u16 cmd]` | `OnInnerMsg` 中 `CPacket.NewWPacket(rpk:Read_string())` 后再 `ply:Send2Client(CPacket.NewWPacket(wpk))` |

**`OnClientMsg` 的三段分流【已确认】**
```lua
local cmd = rpk:Peek_uint16()
if cmd >= NetCmd.CMD_CG_BEGIN and cmd <= NetCmd.CMD_CG_END then ForwardGroup(sock,rpk)
elseif cmd >= NetCmd.CMD_CS_BEGIN and cmd <= NetCmd.CMD_CS_END then ForwardGame(sock,rpk)
else MsgHandler.OnMsg(sock,rpk) end
```

| 转发函数 | 机制 | 状态 |
|---|---|---|
| `ForwardGroup(sock,rpk)` | `wpk = CPacket.NewWPacket(rpk)`（**原地包装，不复制内容**）→ `wpk:Write_uint16(player.groupsession)` → `togroup:Send(wpk)` | 【已确认】 |
| `ForwardGame(sock,rpk)` | `wpk = CPacket.NewWPacket(rpk)` → `wpk:Write_uint32(player.gamesession.id)` → `player.gamesession.sock:Send(wpk)` | 【已确认】 |

⇒ **路由信息（会话 id）写在包尾**，接收方用「从尾部反向读」的 API 取回：
`rpk:Reverse_read_uint16()`（group 侧）/ `rpk:Reverse_read_uint32()`（game 侧）。

**★ 这是一个很实用的技巧**：转发层**不需要理解业务包体**，只要在尾部追加路由键；业务层在解析完业务字段后再从尾部取路由键。JSTM 的 Protocol Adapter 目前是「先解 len/cmd 再解 body」，若未来做**多进程多开**，这个「尾部追加路由键」的模式可以用极低代价复用。

### 3.2 内部 → gateserver（广播包）

**发送侧**（`gameserver/avatar.lua:Send2view` / `gameserver/gameplayer.lua:Send2Client`）【已确认】：
```lua
local gates = {}                       -- 按 gatesession 分组，避免给同一个 gate 发多份
for k,v in pairs(self.watch_me) do
    if v.gatesession and not isInExclude(v) then
        local t = gates[v.gatesession]; if not t then t={}; gates[v.gatesession]=t end
        table.insert(t,v)              -- v 是"能看到我"的玩家
    end
end
for k,v in pairs(gates) do             -- k 是 gate 连接（含 sock）
    local w = CPacket.NewWPacket(512)
    local rpk = CPacket.NewRPacket(wpk)
    w:Write_uint16(rpk:Read_uint16())  -- ① 外层的 cmd（= 内层 cmd，冗余一份，供 gate 分流）
    w:Write_wpk(wpk)                   -- ② 内层完整包（含 cmd + payload）
    w:Write_uint16(#v)                 -- ③ 接收者数量
    for k1,v1 in pairs(v) do
        w:Write_uint32(v1.gatesession.sessionid)  -- ④ 每个接收者的 sessionid
    end
    k.sock:Send(w)
end
```
⇒ 内部 → gate 的格式：**`[u16 cmd][blob 内层包][u16 N][u32 sessionid × N]`**

**接收侧**（`gateserver.lua:OnInnerMsg`）【已确认】：
```lua
local cmd = rpk:Peek_uint16()
if (cmd >= CMD_GC_BEGIN and cmd <= CMD_GC_END) or (cmd >= CMD_SC_BEGIN and cmd <= CMD_SC_END) then
    rpk:Read_uint16()                          -- 丢弃外层 cmd
    local wpk = CPacket.NewWPacket(rpk:Read_string())   -- 取出内层 blob（已含 cmd）
    local size = rpk:Read_uint16()
    for i = 1,size do
        local gatesession = rpk:Read_uint32()
        local ply = Player.GetPlayerById(gatesession)
        if ply then
            if cmd == NetCmd.CMD_SC_ENTERMAP then           -- 特例：进图成功后绑定 game 连接
                ply.gamesession = {sock = sock, id = rpk:Read_uint32()}
            elseif cmd == NetCmd.CMD_GC_BACK2MAIN then      -- 特例：回主城，解绑 game
                ply.gamesession = nil
            end
            ply:Send2Client(CPacket.NewWPacket(wpk))
        end
    end
else MsgHandler.OnMsg(sock,rpk) end
```

**★ 三个可借鉴的点**
1. **按 gate 合并**：同一份 payload 对同一 gate 只序列化一次，N 个接收者只传 N 个 4 字节 id —— 这是 2014 年级别的广播优化，对 JSTM 的「同屏广播」仍然有效。
2. **控制消息夹带状态变更**：`CMD_SC_ENTERMAP` 这一条消息**顺便完成了 gate 侧的 `gamesession` 绑定**（读一个额外的 selfid）。这是"用业务回包驱动连接状态"的做法，省掉一次握手。
3. **同一函数处理两种来源**：`OnInnerMsg` 既分流广播包、又把非广播包丢给 `MsgHandler`（于是 `CMD_AG_CLIENT_DISCONN`、`CMD_GA_NOTIFY_GAME` 也走同一入口）。

### 3.3 groupserver ↔ gameserver

| 方向 | 追加的尾部 | 接收方读取 | 证据 |
|---|---|---|---|
| group → game | `wpk:Write_uint32(gamesession)` | `rpk:Reverse_read_uint32()` | `groupserver/groupplayer.lua:Send2Game` / `gameserver/maplogic.lua:OnEnterMap` 之外 |
| game → group | 无（直接 `togroup:Send(wpk)`） | 直接顺序读 | `gameserver/gameserver.lua:Send2Group` |

⚠️ **已知不一致【已确认】**：`gameserver/map.lua` 中 `CMD_CS_MOV` / `CMD_CS_USESKILL` / `CMD_CS_PICKUP` 的处理用 `Reverse_read_uint32()` 取玩家 id；
而 `CMD_GGAME_CLIDISCONNECTED` 也用 `Reverse_read_uint32()`。
但 game 侧处理的是 **gate 转发来的客户端包**（gate 追加的是 `u32 gamesession`），所以此处读到的其实是 **gamesession**，然后 `GetPlayerById(id)`（内部按 `mapid<<16|idx` 查实体）。
⇒ 说明 **`gamesession` 与实体 id 在本项目里被设计成"恰好相等"**（由 `EnterMap` RPC 返回值绑定，见 `scene.md`）—— 这是一个**隐式契约**，JSTM 若要借鉴必须显式化。

### 3.4 转包原语（C 侧）【已确认的用法】

| 原语 | 用途 | 出现处 |
|---|---|---|
| `CPacket.NewWPacket(n)` | 新建写包（带初始容量） | 全项目 |
| `CPacket.NewWPacket(rpk)` | **以已有包为模板/包装**新建写包（原地改） | `ForwardGame`/`ForwardGroup` |
| `CPacket.NewWPacket(string)` | 用一段字节建写包（用于转发 blob） | `OnInnerMsg` |
| `CPacket.NewRPacket(wpk)` | 建读包（用于"读一下再写"） | `Send2view`/`Send2Client` 里读 cmd |
| `CPacket.NewRawPacket(s)` | 裸包（HTTP 响应、daemon 回包） | `lua/http.lua`、`daemon.lua` |
| `wpk:Write_wpk(wpk2)` | 把一个完整包当作 blob 写入 | `Send2view` |
| `rpk:Read_string()` / `wpk:Write_string(s)` | 变长字符串（blob 传输即用它） | `OnInnerMsg` |
| `Get_write_pos()` / `Rewrite_uint8/uint16(pos,v)` | **先占位写长度、循环后回填** | `attr:on_entermap`、`bag:NotifyUpdate`、`friends:Pack`、`mail:SendMailList` 等 |
| `Peek_uint16/Peek_uint32` | 不动读指针查看命令号 | `OnClientMsg`/`OnInnerMsg`/`recver` |
| `Reverse_read_uint16/uint32` | **从包尾反向读** | 所有 `CG_*` / `CS_*` / `GGAME_*` 处理 |

**★ 模式「占位-回填」**（`Get_write_pos` + `Rewrite_uintX`）在本项目被**大量**使用（数组长度未知时先写 0，最后回填真实条数）。这是手写二进制协议的标准技巧，**思想适合 JSTM**（Python 里可用 `struct.pack_into` 或"先收集 list 再拼"）；⚠️ 但它**极易出错**：`common/lua_astar.c:lua_lineto` 里就有同类逻辑，`groupplayer.lua:friends` 的 `Pack` 更出现 **`Write_uint16` 占位却用 `Rewrite_uint8` 回填**的位置不一致【已确认】。

---

## 四、命令号与分发

### 4.1 `netcmd/netcmd.lua`（命令号表）

| 函数/表 | 机制 | 状态 |
|---|---|---|
| `SetCmdNum(num)` / `NextCmdNum()` | 段首固定、段内自增；`netcmd` 表在**模块加载时**一次性求值 | 【已确认】 |
| 段划分 | 见 `architecture.md` §6 表 | 【已确认】 |
| `GenC_NetCmd()` | **被整段注释掉**的「把命令号导出成 `netcmd.h`」函数 ⇒ 说明 C 侧曾需同步命令号 | 【已确认】 |
| `noti_equipupgrade_success=1` 等四个常量 | 4 个 UI 提示码挂在模块全局 | 【已确认】 |

⚠️ **陷阱**：`netcmd.lua` 的段首由 `SetCmdNum` **重置计数器**，所以**插入/删除一个命令号会让其后同段命令号整体漂移**。JSTM 已被 APK 锁定命令号 ⇒ **绝对不能采用这种"自增生成"方式**，必须**显式常量表**。

### 4.2 `netcmd/msghandler.lua`（分发器）—— **本项目最值得 JSTM 借鉴的 40 行**

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `regHandler(cmd,f)` | `handler[cmd] = f`；业务文件在 `require` 时自注册 | ✅ 适合 | **正是 `FINAL_SERVER_ARCHITECTURE.md` 建议 JSTM 从「单文件 if 链」改为「cmd → handler 注册表」的现成范例**；Python 里可用装饰器 `@register(CMD_X)` 等价实现，且**天然按域拆文件** |
| `onMsg(sock,rpacket)` | `cmd = Read_uint16()` → 查表 → 有则 `f(sock,rpacket)`，无则 `print("unknow cmd",cmd)` | ⚠️ 部分适合 | 查表派发与"未知命令只打日志不崩"的正确性适合；但**它把 `sock` 直接交给业务函数**（业务里再 `Reverse_read` 取会话）耦合偏紧；JSTM 已有 session 概念，可用 `(session, cmd, body)` 分层 |

**注册点分布（实测，可见"按域拆文件"的自然结果）**：
| 文件 | 注册的命令 |
|---|---|
| `gameserver/map.lua` | `CMD_CS_MOV` `CMD_CS_USESKILL` `CMD_GGAME_CLIDISCONNECTED` `CMD_CS_PICKUP` |
| `gateserver/gateserver.lua` | `CMD_GA_NOTIFY_GAME` `CMD_CA_LOGIN` |
| `groupserver/groupplayer.lua` | `CMD_CG_CREATE` `CMD_CG_ENTERMAP` `CMD_CG_LEAVEMAP` `CMD_AG_CLIENT_DISCONN` `CMD_CG_PVE_GETAWARD` `CMD_CG_CHAT` `CMD_CG_ADDPOINT` `CMD_CG_COMMIT_INTRODUCE_STEP` `CMD_CG_COMMIT_SPVE` `CMD_GAMEG_PVPAWARD` `CMD_GAMEG_5PVEAWARD` `CMD_GAMEG_KICK` |
| `groupserver/bag.lua` | `CMD_CG_USEITEM` `CMD_CG_REMITEM` `CMD_CG_LOADBATTLEITEM` `CMD_CG_UNLOADBATTLEITEM` `CMD_CG_SWAP` `CMD_CG_SINGLE_USE_ITEM` |
| `groupserver/equip.lua` | `CMD_CG_EQUIP_UPRADE` `CMD_CG_EQUIP_UNINSET` `CMD_CG_EQUIP_INSET` `CMD_CG_EQUIP_ADDSTAR` `CMD_CG_STONE_COMPOSITE` `CMD_CG_COMPOSITE` |
| `groupserver/skill.lua` | `CMD_CG_UPGRADESKILL` `CMD_CG_UNLOCKSKILL` |
| `groupserver/everydaysignin.lua` | `CMD_CG_EVERYDAYSIGN` |
| `groupserver/everydaytask.lua` | `CMD_CG_EVERYDAYTASK` `CMD_CG_EVERYDAYTASK_GETAWARD` |
| `groupserver/achievement.lua` | `CMD_CG_ACHIEVE` `CMD_CG_ACHIEVE_AWARD` |
| `groupserver/friends.lua` | `CMD_CG_FRIEND_PEEKINFO` `CMD_CG_FRIEND_GETALL` `CMD_CG_FRIEND_ADD` `CMD_CG_FRIEND_REMOVE` |
| `groupserver/mail.lua` | `CMD_CG_GETMAILLIST` `CMD_CG_MAILMARKREAD`（`CMD_CG_MAILDELETE`/`MAILGETATTACH` 被注释） |
| `groupserver/homeisland.lua` | `CMD_CG_HOMEBALANCE` `CMD_CG_HOMEACTION` |
| `groupserver/survive.lua` | `CMD_CG_SURVIVE_APPLY` `CMD_CG_SURVIVE_CONFIRM` `CMD_GAMEG_SURVIVE_FINISH` |

**★ `groupserver/bag.lua` 与 `gameserver/battlebag.lua` 注册了同名命令（`CMD_CG_USEITEM` 等）**——因为二者运行在**不同进程**，各自的 `handler` 表互不干扰。⚠️ 这也意味着**同一命令号在不同进程语义不同**（转发目标由 gate 的段判断决定，而两者都在 `CMD_CG_*` 段内 ⇒ **gate 永远把这些包发给 group，game 侧的 battlebag 注册实际是死代码**）【已确认】。

---

## 五、收包循环（`lua/application.lua`）

| 函数 | 机制 | 状态 |
|---|---|---|
| `application:Add(socket,on_packet,on_disconnected,recvtimeout,pinginterval)` | 绑定 `socket.process_packet = on_packet`；包住 `on_disconnected` 先清 `sock.app`；若给 `recvtimeout` 则注册 1s 心跳定时器（超时 `socket:Close()`）；若给 `pinginterval` 则定期发 `CMD_PING` | 【已确认】 |
| `socket.__on_packet` 重写 | 有新包时：`socket.packet:Push({packet})` → 若有 `recv_wakeup` 协程则唤醒 → 否则若 `recver_count < max_recver_per_socket` 就 `Sche.SpawnAndRun(recver,app,socket)` | 【已确认】 |
| `recver(app,socket)` | `socket.recver_count+1` → `while true do local rpk,err = socket:Recv() ...`；读 `Peek_uint32` = cmd → **若为 RPC 命令号走 RPC**，若为 `CMD_PING` 直接 `return`（结束协程），否则 `xpcall(socket.process_packet, handler, socket, rpk)` | 【已确认】 |
| 异常兜底 | `xpcall` + `debug.traceback()` 写 `CLog.SysLog(LOG_ERROR, ...)` | 【已确认】 |

**★ 值得借鉴**：`xpcall` 包住每个包的业务处理 ⇒ **单包异常不会打断收包循环**。JSTM 的 `mock_server.py` 应对每个 cmd 处理包 try/except 并记录，而不是让连接整体崩掉。

**⚠️ 三处缺陷（不建议照学的部分）**
1. **限流无效**：`--if socket.recver_count > app.max_recver_per_socket then break end` 被注释掉，`while true` 永不退出 ⇒ 只要 `socket:Recv()` 不报错，协程就一直活着；而 `recver_count` 的 `-1` 只在函数返回时执行 ⇒ **计数可能只增不减**（`return` 分支才减）。
2. **心跳参数未使用**：本项目三端调用 `App:Add(...)` 时**都没传** `recvtimeout`/`pinginterval` ⇒ 框架层心跳、`CMD_PING`、超时断连**全部未生效**。客户端掉线只能靠 TCP 层感知。**JSTM 已有 1199 心跳**，不应退回此状态。
3. `CMD_PING` 分支直接 `return` ⇒ 收到 ping 不是"回 ping"而是"结束收包协程"，语义容易误解（框架的 ping 是**单向**的，仅用于打破阻塞）。

---

## 六、RPC（`lua/rpc.lua`）—— 逐函数

| 函数 | 机制 | 状态 |
|---|---|---|
| `gen_rpc_identity()` | 返回 `{h=os.time(), l=自增计数器}`；`identity_to_string` → `"h:l"` | 【已确认】 |
| `init_timeout_checker()` | 起一个 1ms 的 `Timer`，`minheap:Pop(GetSysTick())` 取超时 context 并调 `on_timeout` | 【已确认】 |
| `RPC_Process_Call(app,s,rpk)` | `request = rpk:Read_table()` → 取 `identity`；**用 `s.rpc_record` 做去重**（只有 identity 大于记录值才处理）；`func = app._RPCService[request.f]`；**`table.insert(request.arg, s)` ⇒ 业务函数最后一个参数是 socket**；`noret` 则不回包，否则回 `{identity, ret=pack(...)}` 或 `{identity, err=...}` | 【已确认】 |
| `RPC_Process_Response(s,rpk)` | `response = rpk:Read_table()` → 按 `identity` 取 `s.pending_call[id]` → `minheap:Remove(ctx)` → 有 `callback` 走回调，否则 `co.response = response; Sche.WakeUp(co)` | 【已确认】 |
| `rpcCaller:CallSync(...)` | 构造 `{f, identity, arg}` + `CMD_RPC_CALL` → `Send` → 登记 `pending_call` → `minheap:Insert(ctx, tick+5000)` → `Sche.Block()` → 醒来取 `co.response` 返回 `(err, ret...)` | 【已确认】 |
| `rpcCaller:CallAsync(callback,...)` | 同上但用 `context.callback`；回调签名为 `(err, ret...)` | 【已确认】 |
| `rpcCaller:CallNoRet(...)` | 只发不登记 pending，但仍插超时项做**重试**（重试 2 次） | 【已确认】 |
| `on_timeout` | `trycount <= 2` 就**重发同一个 request（含同一 identity）**并再插 5s；否则 `co.response={err="timeout"}` / 调回调 `{err="timeout"}` | 【已确认】 |
| 断线清理 | 在 `lua/socket.lua:stream.process_c_disconnect_event`：遍历 `pending_call` → 同步调用者 `co.response={err="remote connection lose"}`，异步回调 `pcall(v.callback,{err="remote connection lose"})` | 【已确认】 |

**注册侧（各服务的 `RegRpcService`）**
| 文件 | 服务名（`RPCService`） | 参数形态（末尾自动追加 `sock`） |
|---|---|---|
| `gameserver/gate.lua` | `Login` | `(name, sock)` |
| `gameserver/map.lua` | `EnterSurvive` `EnterMap` `LeaveMap` `CliReConn` | `(ply,starttime,grouptime,sock)` / `(mapid,type,plys,sock)` / `(id,sock)` / `(id,gatesession,sock)` |
| `groupserver/gate.lua` | `GateLogin` | `(name, sock)` |
| `groupserver/game.lua` | `GameLogin` | `(name,ip,port, sock)` |
| `groupserver/groupplayer.lua` | `PlayerLogin` | `(actname,chaid,sessionid, sock)` |

**★ 可借鉴（思想）**
1. **函数名派发**：`request.f` 直接查注册表 ⇒ 新增服务不用改协议号。
2. **同步/异步/无回包三种调用形态**：一个 `CallSync` 配 `Sche.Block/ WakeUp`，代码量极小。
3. **超时 + 幂等重试**：重试用**同一个 identity**，配合服务端 `rpc_record` 去重 ⇒ **"至少一次投递 + 服务端去重 = 恰好一次语义"**的经典做法。JSTM 若做任何跨进程/跨模块调用都可借鉴。
4. **断线时批量失败所有 pending 调用**，而不是让调用方永久挂起。

**❌ 不可借鉴（缺陷 / 不可移植）**
| 缺陷 | 说明 | 状态 |
|---|---|---|
| `Write_table/Read_table` 是 distri 私有序列化 | JSTM 应用 JSON/`struct`/protobuf，**不可移植** | 【已确认】 |
| identity 去重比较写成 `or` | `if identity.l > s.rpc_record[2] or identity.h > s.rpc_record[1]` 应为 `and`；同秒内 `h` 相等时判断退化为只看 `l` | 【已确认】 |
| `rpc_record` 是**每个 socket 单调** | 意味着同一 socket 上**乱序抵达**的合法请求会被**静默丢弃且不回包** ⇒ 调用方只能等超时 | 【待验证】 |
| `CallNoRet` 也做重试 | "无回包"却重试，语义可疑（可能造成重复执行），只有服务端 `rpc_record` 去重兜底 | 【待验证】 |
| `minheap` 是**模块级全局**（`local minheap = CMinHeap.New()`） | 所有 socket 的超时项共用一个堆，`rpcCaller:new` 里 `s.minheap = s.minheap or minheap`；但 `CallSync` 里 `minheap:Remove(context)` 用的是模块堆 ⇒ 与 `s.minheap` 有混用风险 | 【待验证】 |
| `context` 无 `cancel` | 调用方若提前 Close socket，`pending_call` 由断线清理处理，但**同步调用者已 Block 的协程**要靠 `WakeUp` 才能醒 | 【已确认】 |

---

## 七、会话与身份标识（三个 id 体系）【已确认】

| 标识 | 生成处 | 结构 | 用途 |
|---|---|---|---|
| **gatesession** | `gateserver/gateplayer.lua:player:new()` | `sessionid = (idx << 16) + (GetSysTick() & 0xFFFF)`；`idx` 来自 `IdMgr.New(4096)`；`GetId()` 取 idx，`GetTStamp()` 取低 16 位 | gate 侧玩家唯一键；**也用作"给谁发包"的地址**（附着在包尾） |
| **groupsession** | `groupserver/groupplayer.lua:player:new()` | `IdMgr.New(4096)` 分配的纯整数 id | group 侧玩家唯一键；gate 用 `Reverse_read_uint16` 附着 |
| **gamesession** | `gameserver/maplogic.lua:entermap` 返回值（= `mapid<<16 \| idx`） | 高 16 位 = mapid，低 16 位 = 该图内 `freeidx`(4096/1024) | game 侧实体 id；group 用 `Write_uint32` 附着 |

**三套 session 的关系**（登录/进图时逐级绑定）：
```
客户端登录 → gate 造 gatesession → 随 PlayerLogin RPC 交给 group
进图      → group 随 EnterMap RPC 把 gatesession{name,id} 交给 game
          → game 造 gamesession（其内部实体 id）→ 随 CMD_SC_ENTERMAP 回包交给 gate
          → gate 在 OnInnerMsg 里顺手完成 ply.gamesession 绑定
```
**★ 借鉴点**：「**会话在不同进程用不同编号空间、跨进程时显式传递**」是干净的做法。JSTM 单进程不需要三套，但**至少应把"连接级 session"与"角色级 id"分开**——目前 JSTM 的 `mock_server.py` 若把二者混用，将来多开会很痛。

⚠️ **已知缺陷**：`ReleaseIdx(idx)` 里 `print("ReleaseIdx",idx)` 说明 id 会被回收重用；而 `gatesession` 低 16 位是 `GetSysTick() & 0xFFFF` ⇒ **同一 idx 被回收后短时间内可能生成完全相同的 sessionid**（`map.lua` 里 `GetPlayerById` 依赖它）【待验证】。

---

## 八、断线与重连

| 文件 / 函数 | 机制 | 状态 |
|---|---|---|
| `gateserver/gateplayer.lua:OnPlayerDisconnected(sock,errno)` | 清 `sock2player`；按状态分流：`verifying`/`login2group` 只置 `status=releasing`（等 RPC 回来再清理）；否则 `ReleasePlayer` | 【已确认】 |
| `gateserver/gateplayer.lua:ReleasePlayer(ply)` | 若有 `groupsession` → 发 `CMD_AG_CLIENT_DISCONN` 给 group；删 `id2player`；`ReleaseIdx` | 【已确认】 |
| `gateserver/gateplayer.lua:OnGameDisconnected(sock)` | 遍历所有玩家，把 `gamesession` 指向该 sock 的清空（**不断客户端连接**） | 【已确认】 |
| `gateserver/gateplayer.lua:OnGroupDisconnected()` | **把所有客户端 `sock:Close()`**（group 没了就不服务了） | 【已确认】 |
| `groupserver/groupplayer.lua:CMD_AG_CLIENT_DISCONN` | `Gate.UnBind(ply)`；若有 `gamesession` → 发 `CMD_GGAME_CLIDISCONNECTED` 给 game（game 随后交给 AI 托管，见 `battle.md`）；否则起 `LogOutTimer`（`release_timeout = 1*60*1000` = 60s）后 `ReleasePlayer` | 【已确认】 |
| `groupserver/groupplayer.lua:PlayerLogin`（重连分支） | 若 `GetPlayerByActname(actname)` 已存在且**无** `gatesession` ⇒ 视为断线重连：移除登出定时器 → `Gate.Bind` → 按 `status` 处理；`playing/queueing/entermap` 分支会 `Sche.Spawn` 调 `NotifyBeginPlay()` 并 **RPC `CliReConn`** 通知 game | 【已确认】 |
| `gameserver/map.lua:RPCService("CliReConn")` | 查实体 → `Gate.GetGateByName(gatesession.name)` → `Gate.Bind(gate,ply,gatesession.id)` → `ply:ReConnect()` | 【已确认】 |
| `gameserver/gameplayer.lua:ReConnect(maptype)` | 停 AI → `on_entermap()`（重发进图包）→ **遍历 `view_obj` 逐个 `SendEnterSee`** 重建客户端视野 | 【已确认】 |
| `gateserver/gateplayer.lua:IsVaild(ply)` | `ply.status ~= releasing` —— 用于 RPC 返回后二次确认连接是否已断（防止"RPC 回来了但人已走"） | 【已确认】 |

**★ 可借鉴**：
- **三态处理断线**（未验证 / 已交给 group / 正在游戏中）比"一刀切断开"可靠得多；
- **`IsVaild` 二次确认**是防竞态的最小成本手段，JSTM 的登录 RPC 场景同样适用；
- **"断线后 60s 保留角色、期间可重连"** 与 **"重连时重建视野（逐个 ENTERSEE）"** 正是 JSTM 目前**缺**的一环（`FINAL_SERVER_ARCHITECTURE.md` 提到移动/NPC 对话未闭环，重连后的视野重建是同类问题）。

**❌ 不适合**：`OnGroupDisconnected` 直接踢掉**所有**客户端——在 JSTM 单进程里等价于"DB 挂了就断所有人"，应对策略应是**拒绝新请求 + 保连接**。

---

## 九、日志与可观测性

| 文件 / 函数 | 机制 | 状态 |
|---|---|---|
| `CLog.New(name)` / `log_xxx:Log(level,msg)` | C 模块日志对象；各进程入口建 `log_gameserver`/`log_groupserver`/`log_gateserver` **全局变量** | 【已确认】 |
| `CLog.SysLog(LOG_INFO/LOG_ERROR, msg)` | 框架级日志（socket 异常、RPC 异常、定时器异常都走这里） | 【已确认】 |
| `common/log.lua` | 包了一层 `New/Log`，但模块返回时引用了**未定义的局部 `Init`**（落到 nil 全局）且把 `CLog.LOG_INFO` 在加载期求值 ⇒ 属**未完成/未使用**模块 | 【已确认】 |
| 日志级别误用 | `groupserver/groupserver.lua` 中**成功启动也打 `LOG_ERROR`**（`"start server on %s:%d"`）；`groupplayer.lua` 的 `PlayerLogin` 全程 `LOG_ERROR`。⇒ **不能按级别告警** | 【已确认】 |
| 调试输出 | 全项目大量 `print()`（含 `print(chaid, sessionid)`、`print(rpk)`）在**生产路径**上 | 【已确认】 |
| 状态上报 | `gameserver/map.lua` 每 5s 打一次 map 统计（mapid/maptype/plycount/avatar count/ai count）；`daemon.lua` 每秒 `C.Top()` 写 redis `MachineStatus` | 【已确认】 |

**结论**：Survive 的**可观测性是不可用的**（级别误用 + print 泛滥 + 无结构化输出）。JSTM 应自建 JSON 日志与 cmd 级统计，**不要照学其日志层**。

---

## 十、对 JSTM 的具体建议（网络层）

| 优先级 | 建议 | 依据（Survive 出处） | 可否用代码 |
|---|---|---|---|
| **P0** | 把 `mock_server.py` 的单文件 if 链改为 **`cmd → handler` 注册表 + 按域拆模块**（login/role/scene/battle/item/...），并给每包加异常兜底 | `netcmd/msghandler.lua` + 各业务文件自注册 | ❌ 只借结构，自行实现（可用 Python 装饰器） |
| **P0** | 保留并强化 JSTM 现有 `[u32 len][u16 cmd][body]`；**显式常量表**（禁用自增生成命令号） | `netcmd.lua` 的自增方式导致命令号漂移 | ❌ 反例警示 |
| **P1** | 连接级 session 与角色级 id **分离**，跨模块调用显式传 session | gate/group/game 三套 session | ❌ 借思想 |
| **P1** | 每个 cmd 处理包 `try/except` + 未知 cmd 只记日志不崩 | `application.lua:recver` 的 `xpcall` | ❌ 借思想 |
| **P1** | 断线三态处理 + 二次确认（`IsVaild` 模式）+ **保留 60s 可重连** + 重连重建视野 | `gateplayer.lua` / `groupplayer.lua:PlayerLogin` / `gameplayer.lua:ReConnect` | ❌ 借思想 |
| **P2** | 同屏广播**按连接合并**（同一 payload 只序列化一次，附接收者 id 列表） | `avatar.lua:Send2view` | ❌ 借思想 |
| **P2** | 若将来多开：中心服务只被连、成员主动注册、中心把成员列表转告其他成员 | `GateLogin` 返回 game 列表 + `CMD_GA_NOTIFY_GAME` | ❌ 借思想 |
| **P2** | 内部调用用「函数名派发 + 超时重试 + 服务端 identity 去重」 | `lua/rpc.lua` | ❌ 借思想（**不可移植 `Write_table`**） |
| **P3** | 用真实协议写**压测机器人**做回归 | `robotclient.lua`（50 协程） | ❌ 借方法 |
| **禁止** | 抄 `CPacket/CSocket` 的包格式、`Write_table` 序列化、`CMD_PING=0xABABCBCB`、分段自增命令号 | — | 🚫 **协议层全部禁止** |

---

## 十一、【未读到】/【未知】

| 项 | 状态 |
|---|---|
| `CPacket/CSocket` 的 C 源码与**字节序** | 【未读到】（在 `distrilua` 二进制内） |
| `Write_table/Read_table` 的**具体编码** | 【未读到】 |
| `Peek_uint16` 的越界行为 | 【未读到】 |
| 是否使用 TCP_NODELAY / 粘包如何处理 | 【待验证】由 `Establish(decoder, recvbuf)` 推断为**长度前缀式解码器**，但解码器实现在 C 里 |
| 客户端侧 `UILogin.lua:Connect` 的协议实现 | 【未读到】（在 `client/src/`，本轮未审计客户端） |
| notiserver 是否参与网络 | 【未读到】（主体被注释） |
| `php/manage.php` 的下行 JSON 指令格式 | 【待验证】由 `daemon.lua:processMsg` 反推为 `{op="Start"/"Stop"/"Kill", ip, group, logicname}` |
