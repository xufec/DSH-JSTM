# Survive 可借鉴点清单（reuse_candidates）

> 配套文件：`architecture.md` / `network.md` / `role.md` / `scene.md` / `battle.md` / `database.md`
> 审计对象：`C:\Users\xu\Desktop\DSH\cankao\Survive-master.zip`（207.7 MB / 2618 文件，服务端 Lua 明文）
> 目标项目：**JSTM（《绝世唐门》1.4.9 私服兼容服务端）**，现状：**单进程 Python + SQLite + 自研 1.4.9 协议 Adapter**
> 状态标记：【已确认】【待验证】【未知】

---

## 一、总览

| 项 | 数值 |
|---|---|
| 审计的服务端 Lua 文件 | **42 个**（gameserver 16 + groupserver 19 + gateserver 2 + notiserver 5，逐文件全部读到） |
| 审计的框架 Lua 文件 | **15 个**（`lua/`） |
| 审计的 C 源文件 | **8 个**（`common/{aoi.c,aoi.h,lua_aoi.c,astar.c,astar.h,lua_astar.c,point.h,idmgr.h}` + b64 3 个） |
| 审计的配置表文件 | **40+ 张** `common/Table*.lua`（抽样读完 38 张的表头/结构） |
| 审计的文档 | `README.md`、`doc/README.md`、`doc/管理系统的.md`、`doc/系统部署与管理.md` |
| **★ 头等设计点（值得或明确不值得借鉴的"架构级"发现）** | **26 条**（见 §2） |
| **★ 已确认的实现缺陷（不可照学）** | **23 处**（见 §6） |
| **★ LICENSE 结论** | **无顶层 LICENSE ⇒ 只能借鉴设计，绝对不能复制代码**；**另发现部分 C 头文件内嵌 GPLv3 声明，限制更严**（见 §4） |

---

## 二、★ 头等设计点清单（26 条）

> 判据：**"是否会改变 JSTM 的架构决策"**。只是实现细节的放 §6。
> 「是否适合 JSTM」：✅适合 / ⚠️部分 / ❌不适合

| # | 设计点 | 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|---|---|
| **D1** | **三件套分层（中心只被连、成员主动注册）** | `groupserver/groupserver.lua`、`gateserver/gateserver.lua`、`gameserver/gameserver.lua` | `connect_to_group` / `GateLogin` / `GameLogin` / `CMD_GA_NOTIFY_GAME` | group 只 Listen；gate/game 反连并报 `name,ip,port`；group 把 game 列表返回给 gate，并在新 game 上线时广播通知所有 gate | ⚠️ 部分 | ★ **思想值得借鉴**（免配置实例列表、中心转告成员）；❌ **形态不适合 JSTM**——JSTM 单进程已跑通闭环，多进程是过度设计（`FINAL_SERVER_ARCHITECTURE.md` 已判定）。**仅在"将来多开"时**取出这套拓扑 |
| **D2** | **命令号分段 + cmd → handler 注册表** | `netcmd/netcmd.lua`、`netcmd/msghandler.lua` + 各业务文件 | `SetCmdNum/NextCmdNum`、`regHandler/onMsg` | 命令号按通信方向分十段；各业务文件在 `require` 时用 `MsgHandler.RegHandler(cmd, f)` 自注册；分发只做一次查表 | ✅ **适合（结构）** / ❌ 不适合（编号方式） | ★ **注册表 + 按域拆文件**正是 JSTM 应从"单文件 if 链"改成的形态（P0）；❌ 但**绝不能用"自增生成命令号"**——JSTM 已被 APK 锁死命令号，必须显式常量表 |
| **D3** | **路由键"写尾读尾"（转发层不懂业务）** | `gateserver/gateserver.lua`、`gameserver/map.lua`、`groupserver/groupplayer.lua` | `ForwardGroup/ForwardGame` + `Reverse_read_uint16/uint32` | gate 在包**尾部**追加 `u16 groupsession` / `u32 gamesession`；接收方顺序解业务字段、再**从尾部**取路由键 | ✅ **适合（思想）** | ★ **转发层零业务知识**；JSTM 若将来多开，可直接复用此模式（成本极低） |
| **D4** | **同屏广播按连接合并 + 只在 `watch_me` 上广播** | `gameserver/avatar.lua`、`gameserver/gameplayer.lua` | `Send2view(wpk, exclude)` | 把"能看到我的玩家"按 gate 连接分组；同 gate 只序列化**一份** payload，附上 N 个 `u32 sessionid` | ✅ **高度适合（思想）** | ★ JSTM 的同屏广播必须这么做（省带宽/省 CPU）；**必须用 `watch_me`（谁看我）而非 `view_obj`（我看谁）** |
| **D5** | **同步写法、异步实现（协程化 socket）** | `lua/socket.lua`、`lua/application.lua` | `stream.Recv/Send/Connect/Accept` + `Sche.Block/WakeUp` | `Recv` 无包时把自己压入等待链再 `Block()`；C 回调来时 `WakeUp` | ✅ **高度适合（思想）** | ★ JSTM 用 asyncio 或同步线程模型时，都应提供"像阻塞一样写"的 API；**代码不可移植**（依赖 `CSocket`） |
| **D6** | **单线程 + 每连接/每实体一协程 + 定时最小堆** | `lua/sche.lua`、`lua/timer.lua` | `Spawn/Yield/Sleep/Block/WakeUp/Schedule`、`timer:Run` | 就绪链跑空 → 弹超时堆 → 把 yield 的重新入队；`Timer` 回调返回 nil 表示续期 | ✅ 适合（思想） / ❌ 不适合（自研调度器） | ★ **"返回 nil 就续期"** 的定时约定很省代码；❌ **不需要复刻六态协程调度器**（Python 有事件循环） |
| **D7** | **自研 RPC：函数名派发 + 超时重试 + identity 去重 + 断线批量失败** | `lua/rpc.lua`、`lua/socket.lua` | `ProcessCall/ProcessResponse/MakeRPC`、`CallSync/CallAsync/CallNoRet`、`process_c_disconnect_event` | 请求 `{f, identity={h,l}, arg}`；服务端按 `rpc_record` 去重；调用方 5s 超时、重试 2 次（**同一 identity**）；断线时把所有 pending 调用以 `"remote connection lose"` 唤醒 | ✅ **高度适合（思想）** / ❌ 协议不可移植 | ★ **"至少一次投递 + 服务端去重 = 恰好一次"**；★ **断线不能只挂起**；❌ `Write_table` 是 distri 私有序列化，**不可移植** |
| **D8** | **属性：下标化 + 派生不落库 + 登录全量重算** | `common/name2idx.lua`、`groupserver/attr.lua`、`groupserver/groupplayer.lua` | `attr_db_save = attack-1`、`DbStr`、`CalAttr` | 只持久化前 23 项（输入项）；`attack/defencse/maxlife/dodge/crit/hit` 每次登录由 `CalAttr` 重算 | ✅ **高度适合（思想）** ❌ 不适合（用数组下标存） | ★ **杜绝"存档与公式不一致"**；❌ **但必须改成命名字段**——Survive 存的是**无键数组**，`name2idx` 一改顺序全部老档错位（见 §6） |
| **D9** | **属性可见性白名单 + 一次变更两个包** | `gameserver/attr.lua` | `attr2view = {level, life, maxlife}`、`on_entersee`、`NotifyUpdate` | 视野内玩家只收 3 个属性；自己收全量；同一次变更生成"视野包 + 自身包" | ✅ **高度适合** | ★ **隐私 + 带宽 + 反外挂**三重收益；JSTM 若把全属性广播给同屏玩家，应立刻收敛 |
| **D10** | **改动后发"重算信号"而不是就地改派生值** | `groupserver/bag.lua`、`groupserver/groupplayer.lua` | `Swap` 返回 `true,"recalattr"` → `ply:CalAttr(true)` | 装备位变动时 `Swap` 只改数据并返回信号；上层据此重算 | ✅ **高度适合（思想）** | ★ 解耦"数据变更"与"属性计算"，是 D8 的必要配套 |
| **D11** | **AOI：网格 + 每对象视野集合 + 新旧集合差 + 双向回调** | `common/aoi.c`、`common/lua_aoi.c` | `aoi_create/enter/moveto/leave`、`cal_blockset`、`block_process_enter/unchange/leave`、`cb_enter/cb_leave` | 地图切格；对象带 `view_objs` 位图去重；移动只算 `enter/unchange/leave` 三类格；只有 enter/leave 全量配对，unchange 只做距离检查；C 只回调 `enter_see/leave_see` | ✅ **最高价值（JSTM 完全缺失）** | ★ **JSTM 的 P0 缺口**。可直接照搬设计（网格/集合/差集/回调）。⚠️ 但**不要**照学"`radius` 兼作格边长""上限写死 4096"（见 §6） |
| **D12** | **寻路：A\* + LOS 直线裁剪 + 与客户端共享碰撞网格** | `common/astar.c`、`common/lua_astar.c`、`gameserver/util.lua`、`gameserver/map.lua` | `find_path`、`isblock`、`lua_lineto`、`DirTo/ForwardTo` | A\* 8 邻域；`lineto` 用 Bresenham 做射线，**遇障碍即停并返回已走的点**，用于击退/位移/追踪点 | ✅ **最高价值（JSTM 完全缺失）** | ★ **`lineto` 比 A\* 便宜得多且用途更广**；★ 前提是**服务端与客户端用同一张阻挡表**（文档明写"共享同样的寻路网格"）；⚠️ 启发函数用曼哈顿对 8 邻域不一致，JSTM 应用 Octile |
| **D13** | **移动同步：客户端只发目标点、服务端只广播目标点、服务端按时间预算自走** | `gameserver/avatar.lua`、`gameserver/map.lua` | `Mov`、`process_mov`、`movmargin`、`CMD_SC_MOV/MOV_ARRI/MOV_FAILED` | 客户端发目标点 → 服务端算路径 → **只广播"速度+目标点"**（不广播路径）；服务端另有 100ms 定时器，用 `movmargin` 时间预算一帧跨多格 | ✅ **高度适合（思想）** | ★ **大幅省带宽**（路径由客户端本地用同一网格重算）；★ **服务端必须自己也走**（否则 NPC 追击/AOI/拾取范围全偏）；⚠️ JSTM 的移动包格式**必须来自 APK**（本轮未读 `movement_protocol.md`） |
| **D14** | **进视野/重连时补发"运动状态 + Buff 状态"** | `gameserver/avatar.lua`、`gameserver/buff.lua`、`gameserver/gameplayer.lua` | `SendEnterSee`（补 `CMD_SC_MOV`）、`buffmgr:OnEnterSee`、`ReConnect`（遍历 `view_obj` 重建） | 新人进视野时，若对方在移动则补发移动包；重连时逐个 `SendEnterSee` | ✅ **高度适合（缺口）** | ★ **极易遗漏**，否则新人看到"静止的移动者 / 没 buff 的人"；★ 对应 JSTM 目前"移动/NPC 对话未闭环"的同类问题 |
| **D15** | **掉线托管 AI / 人不够用机器人补位** | `gameserver/maplogic.lua` | `OnClientDisconnect`（`Robot.New(ply,1)`）、`FiveVE/FiveVP:entermap`（`CreateNPC`） | 真人掉线 ⇒ 同实体挂 AI 继续战斗；组队人不够 ⇒ 造机器人玩家 | ✅ **高度适合** | ★ **单机/小服可玩性的关键**——否则副本/竞技场永远凑不齐人 |
| **D16** | **玩法逻辑统一 6 方法接口（扩展点）** | `gameserver/maplogic.lua`、`gameserver/map.lua` | `MapLogic.New(map)` + `Init/entermap/leavemap/Tick/OnAvatarDead/OnClientDisconnect/OnEnterMap` | 按 `TableMap.PlayType` + `maptype` 返回不同 logic 对象；战斗代码只调接口 | ✅ **高度适合（思想）** | ★ **新增玩法只加一个类文件 + 一行配置**；JSTM 的"普通场景/副本/竞技场"分流应照此 |
| **D17** | **匹配队列：凑够就开、超时也开 + 原子入场 + 空图回收** | `groupserver/map.lua`、`gameserver/maplogic.lua` | `ReqQue:Push/ProcessEnter/Tick`、`freeidx:Len() < #plys`、`map:Release` | 队列满 `plyMax` 或队首等待超 `MaxWait` ⇒ 开图；入场先检查空位（要么全进、要么全不进）；`plycount==0` ⇒ 回收地图**并停定时器** | ✅ **高度适合（思想）** | ★ **超时也开**对低人服必需；★ **原子入场**保证组队一致；★ **回收必须停定时器**（防泄漏） |
| **D18** | **发奖"先全量校验、再全部落地"** | `groupserver/bag.lua`、`groupserver/equip.lua` | `AddItems`（先收集 `bagpos` 全部成功才写）、`CMD_CG_COMPOSITE`（先校验全部材料） | 两阶段：校验阶段只读、不写；通过后才写入 | ✅ **高度适合（思想）** | ★ 防"发一半奖励失败"；JSTM 的发奖/合成/进图等都应先校验后落地 |
| **D19** | **配置驱动回调（表里写函数名 → 代码里查函数表）** | `gameserver/bufffunction.lua`、`gameserver/triggerfunction.lua`、`gameserver/skill.lua`、`common/TableBuff.lua` | `GetTabFunction(tb,name)`、`BuffFunc`、`TriggerFunc`、`Suffer_Script` + `_G[name]` | `TableBuff.OnBegin = "LifeRecover_OnBegin"` → `BuffFunc["LifeRecover_OnBegin"]` | ✅ **高度适合（思想）** / ⚠️ 需补校验 | ★ 让策划改表即可改行为；⚠️ **Survive 未做"启动时校验引用存在"** ⇒ 写错名字只静默失效，JSTM 必须补 |
| **D20** | **"一个角色 = 一次读写"（单次多字段 hmset/hmget）** | `groupserver/groupplayer.lua`、`groupserver/*.lua` | `CMD_CG_CREATE`（一条 `hmset` 写 8 field）、`PlayerLogin`（一条 `hmget` 读 9 field） | 创角/登录各自**一次往返**完成全部字段 | ✅ **适合（思想）** | ★ 减少往返；SQLite 里对应一次多列 `SELECT/INSERT`；⚠️ JSTM 应**同时加事务**（Survive 没有） |
| **D21** | **脏标记 + 异步落库（只写变更）** | `groupserver/{attr,bag}.lua` | `dbchange` / `flag` / `if self.dbchange then ... end` | 只有改动过才写；`flag` 记录"哪些槽位变了"用于增量推送 | ✅ **适合（思想）** | ★ 避免高频无谓写库；⚠️ 但 `everydaytask:OnEvent` 每事件都写（反面），JSTM 应加节流 |
| **D22** | **用真实协议写压测机器人** | `robotclient.lua` | `ConnectAndLogin(name)` + `MsgHandler.RegHandler` | 50 个协程各自连 gate、登录、创角、进图、循环随机移动 | ✅ **适合（方法）** | ★ JSTM 已有真协议，写 Python bot 做回归/压测比 Survive 更容易；★ 也能用来复现"移动/NPC 对话"问题 |
| **D23** | **状态机 + 每个命令入口前置校验** | `groupserver/groupplayer.lua`、`gateserver/gateplayer.lua` | `createcha/creating/loading/playing/queueing/entermap/leavingmap/releasing`、`if ply.status ~= playing then ... return end` | 每个 `CMD_CG_*` 入口先判 status 并**分别打日志说明原因** | ✅ **适合（思想）** ⚠️ 不适合（两套编号） | ★ 防"重复进图/进图途中发包"；⚠️ **Survive 在 gate 与 group 各定义了一套同名不同意的常量**（可读性隐患），JSTM 应统一 |
| **D24** | **限时活动骨架：定时开启 + 报名窗口 + 延迟批量传送 + 结束结算** | `groupserver/survive.lua` | `Apply/Confirm/Transfer/TransferTimerTick`、`CMD_GAMEG_SURVIVE_FINISH` | `nextTime/applyDeadLine` 用 `Timer` 滚动；确认时抽奖得带入道具；`waitForTransfer` 到点批量 RPC 传送；结束后由 group 发奖 | ✅ **适合（结构）** | ★ 完整的最小活动骨架；⚠️ **全在内存、重启即丢**（JSTM 应落库）、且 `selectVipItem` 未定义会崩（见 §6） |
| **D25** | **AI = 协程 + 三态状态机 + 事件驱动唤醒** | `gameserver/robot.lua` | `robot:main/Wakeup/StartRun/Stop`、`stateMachine:execute`、`state_partol/trace/atk`、`AddTraceMe/NotifyTargetPosChange` | AI 是协程，`Mov` 后 `Sche.Block()` 等"到达"唤醒；目标每次移动就通知追踪者；状态机"返回下一状态号" | ✅ **适合（思想）** | ★ **不需要"我到哪了"的轮询**；★ 追击是事件驱动（省 CPU）；★ 极简 transition（返回状态号） |
| **D26** | **场景进程无状态（数据只在逻辑层）** | `gameserver/gameserver.lua`、`groupserver/map.lua` | gameserver **无 `Db.Init`**；group 侧 `mapinstance` 记账 | 场景进程不碰 DB，可随意重启；玩家数据只在 group | ✅ **适合（思想）** ⚠️ 不适合（账本在内存） | ★ **"场景只算不存"**是好设计；⚠️ 但 Survive 的**场景实例账本在 groupserver 内存**，重启即不一致 —— JSTM 应把"哪个实例在哪/有哪些人"也落库或可重建 |

---

## 三、分模块可借鉴点索引（详细机制见对应文件）

| 模块 | 对应报告 | **该报告中最值得看的 3 节** |
|---|---|---|
| 整体架构 / 服务划分 / 启动 | `architecture.md` | §3 服务划分、§4 启动与配置、§5 框架层 `lua/` |
| 网络 / 协议 / 分发 / RPC | `network.md` | §3 封包格式、§4 命令号与分发、§6 RPC、§8 断线与重连 |
| 角色 / 属性 / 背包 / 装备 | `role.md` | §3 属性白名单与脏标记、§4 `CalAttr` 公式、§5 背包与位打包 |
| 场景 / AOI / 寻路 / 移动 | `scene.md` | **§3 AOI 机制全解**、**§4 寻路**、**§5.4 `process_mov` 时间预算**、§9 落地建议 |
| 战斗 / Buff / AI / 结算 | `battle.md` | §3 `UseSkill` 主流程、§4 Buff 系统、§5 AI 状态机、§8 建议 |
| 持久化 | `database.md` | §3 键空间、§4 `chaid:<id>` 9 field、§6 风险清单 |

---

## 四、LICENSE 审计（**强制项**）

### 4.1 实测结果

| 检查项 | 结果 | 状态 |
|---|---|---|
| 顶层 `LICENSE` / `COPYING` / `NOTICE` | **不存在**（扫描 2618 个文件名：`license`/`copying`/`gpl` 全部无命中） | 【已确认】 |
| `README.md` 内的授权声明 | 只有项目简介与联系方式（`huangweilook@21cn.com`），**无任何许可条款** | 【已确认】 |
| **⚠️ 新发现：部分 C 源文件内嵌 GPLv3 声明** | `common/aoi.h`、`common/astar.h`、`common/wordfilter.h` 文件头：<br>`Copyright (C) <2012> huangweilook@21cn.com`<br>`This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.` | 【已确认】 |
| 第三方代码 | `common/b64.h` / `encode.c` / `decode.c` **来自 `joseph werle` 的 b64 库**（文件头 `copyright (c) 2014 joseph werle`，**未附许可文本**） | 【已确认】 |

### 4.2 结论（**比"无 LICENSE"更严格**）

| 允许 | 禁止 |
|---|---|
| ✅ 阅读全部服务端源码（Lua / C / 表 / 文档） | ❌ **复制任何代码文件进 `server/`**（无顶层许可 ⇒ 无授权依据） |
| ✅ 借鉴**架构、分层、算法、数据结构、协议设计思想** | ❌ **复制 `common/aoi.h`、`common/astar.h`、`common/wordfilter.h` 及其派生实现**（**GPLv3 copyleft**，一旦并入 JSTM ⇒ JSTM 需整体以 GPLv3 发布） |
| ✅ 在报告中引用其文档与代码片段**作为设计来源说明** | ❌ 把 GPL 代码"改写一下再用"（**衍生作品仍受 GPL 约束**） |
| ✅ 用 JSTM 自己的协议/语言**重新实现**同一思想 | ❌ 复制 `b64.h`/`encode.c`/`decode.c`（来源许可不明） |
| ✅ 借鉴 AOI/寻路的**算法思想**（均匀网格、集合差、A\*、Bresenham） | ❌ 声称这些代码是自研 |

> **⇒ 对 AOI 与寻路这两块"最想借鉴"的内容：正是 GPLv3 声明所在的文件。**
> **⇒ 因此 JSTM 只能"读设计、写自己的实现"**——这恰好也是正确的工程做法（Python 里本来就要重写）。

### 4.3 与既有审计的衔接

`../license_audit.md` 已记录：**Survive 无 LICENSE ⇒ 只可借鉴设计**。本报告**补充一条**：
> **除"无顶层 LICENSE"外，`common/aoi.h`/`common/astar.h`/`common/wordfilter.h` 内嵌 GPLv3 ⇒ 对这三块内容的限制从"默认不可复制"升级为"明确 copyleft 传染"。**
> 建议在 `../license_audit.md` 的 §二-1 与本报告中同时登记该发现。

---

## 五、★ 对 JSTM 的建议

### 5.1 值得借鉴的设计思想（**借鉴什么**）

> 每条都写明「借鉴什么 + 从哪里来 + 拿到 JSTM 要变成什么」。

| # | 借鉴什么（**具体到可执行**） | 出处 | 拿到 JSTM 变成什么 |
|---|---|---|---|
| **A1** | **借"cmd → handler 注册表 + 按域拆文件"**：每个业务模块在自己被导入时注册自己负责的命令号；分发器只做一次查表 | `netcmd/msghandler.lua` + `groupserver/{bag,equip,skill,mail,friends,...}.lua` | 把 `mock_server.py` 的 if 链拆成 `protocol/registry.py` + `logic/<域>/handler.py`；用 `@register(CMD_X)` 装饰器 |
| **A2** | **借"分包异常隔离"**：每个包的业务处理用 `xpcall` 包住并记 traceback，单包异常不打断收包循环 | `lua/application.lua:recver` | 每个 handler 外包 `try/except` + JSON 日志；未知 cmd 只记日志不崩 |
| **A3** | **借"连接级 session 与角色级 id 分离"**：gate/group/game 三套编号空间，跨进程显式传 session | `gateserver/gateplayer.lua` / `groupserver/groupplayer.lua` / `maplogic.lua` | 即使单进程，也应把 `conn_id`（连接）与 `role_id`（角色）分开，避免"连接即角色"的耦合 |
| **A4** | **借"断线三态 + 二次确认 + 60s 可重连 + 重连重建视野"** | `gateplayer.lua:OnPlayerDisconnected/IsVaild`、`groupplayer.lua:PlayerLogin` 重连分支、`gameplayer.lua:ReConnect` | JSTM 的"重连"与"移动/NPC 对话"是同源问题：都需要**进场景后重建客户端可见状态** |
| **A5** | **借"属性：只存输入、派生每次重算"** | `name2idx.attr_db_save` + `groupplayer.lua:CalAttr` | JSTM 的 `role_attr` 若存了 `attack/maxlife` 等派生值，改为**只存基础项**，登录时统一重算 |
| **A6** | **借"属性可见性白名单 + 一次变更两个包"** | `gameserver/attr.lua:attr2view/on_entersee/NotifyUpdate` | 同屏只广播 `level/life/maxlife`（或 JSTM 客户端真正需要的字段），自己收全量 |
| **A7** | **借"改动 → 发信号 → 重算"的解耦** | `bag.lua:Swap` 返回 `"recalattr"` | 背包/装备/加点/强化任何改动后，统一调一次 `recalc_attrs(role)` |
| **A8** | **借"发奖两阶段：先全量校验、再全部落地"** | `bag.lua:AddItems`、`equip.lua:CMD_CG_COMPOSITE` | JSTM 的任务奖励/礼包/合成/进图都先校验再写 |
| **A9** | **借"配置驱动的效果回调（表里写函数名 → 注册表）"** | `bufffunction.lua`/`triggerfunction.lua`/`skill.Suffer_Script` | JSTM 的 Buff/技能效果/NPC 对话/传送点都用同一套派发；**必须补"启动时校验引用存在"** |
| **A10** | **借"AOI 的均匀网格 + 视野集合去重 + 新旧集合差 + 双向 enter/leave 回调"**（**不是抄 C 代码**） | `common/aoi.c`（⚠️ GPLv3 头，只读设计） | Python 自写：`dict[(gx,gy)] = set(obj)`；每个实体一个 `set()` 存视野内 id；移动只算 `enter/unchange/leave`；暴露 `on_enter(a,b)/on_leave(a,b)` |
| **A11** | **借"A\* + LOS 射线裁剪（lineto）+ 服务端与客户端共享同一张阻挡表"** | `common/astar.c`、`lua_astar.c` | Python `heapq` 实现 A\*（建议 Octile 启发）；`line_of_sight()` 用 Bresenham 做击退/位移/追踪点；**阻挡表必须与 APK 的 `_config_map_block` 同源** |
| **A12** | **借"移动同步：客户端只发目标点、服务端只广播目标点、服务端按时间预算自走"** | `avatar.lua:Mov/process_mov` | JSTM 的移动包格式**取自 APK**；服务端必须自己也推进坐标（否则怪物追击/拾取/AOI 全偏） |
| **A13** | **借"进视野/重连补发运动与 Buff 状态"** | `avatar.lua:SendEnterSee` + `buff.lua:OnEnterSee` | 补发"对方在移动"和"对方有 buff" |
| **A14** | **借"人不够用机器人补位、掉线交 AI 托管"** | `maplogic.lua` | 单机/小服副本与 PvP 的可玩性关键 |
| **A15** | **借"玩法 logic 的统一 6 方法接口"** | `maplogic.lua` 家族 | `init/enter/leave/tick/on_avatar_dead/on_client_disconnect`；新增玩法不改战斗代码 |
| **A16** | **借"匹配队列：凑够就开、超时也开 + 原子入场 + 空图回收（含停定时器）"** | `groupserver/map.lua:ReqQue` | JSTM 若做组队副本必须如此 |
| **A17** | **借"AI = 协程 + 三态状态机 + 事件驱动唤醒"** | `robot.lua` | Python 里用 `asyncio` 或"状态机 + 事件队列"；追击靠"目标移动通知"而不是每帧算距离 |
| **A18** | **借"场景进程无状态"** | gameserver 无 `Db.Init` | 场景模块不直接写库；数据由逻辑层负责 |
| **A19** | **借"用真实协议写压测机器人"** | `robotclient.lua` | Python bot 做回归 + 压测 + 复现问题 |
| **A20** | **借"限时活动骨架"** | `groupserver/survive.lua` | 定时开启 + 报名窗口 + 延迟批量传送 + 结束结算（**但时间和名单要落库**） |
| **A21** | **借"运维状态上报 + 一键启停"的思想** | `daemon.lua` + `php/manage.php` | JSTM 的 17 个 GM 动作可扩展为"进程/在线/负载"只读面板（**不照抄 C.ForkExec**） |
| **A22** | **借"中心服务只被连、成员主动注册、中心转告成员列表"** | `GateLogin` 返回 game 列表 + `CMD_GA_NOTIFY_GAME` | **仅在 JSTM 将来多开时**使用 |

### 5.2 完全不能借鉴（**必须避免**）

| # | 不能借鉴的东西 | 出处 | 为什么 |
|---|---|---|---|
| **B1** | **多进程三件套形态**（gate/group/game 分开部署） | README / `doc/README.md` | JSTM 已在**单进程 Python** 上跑通 登录→角色→场景→任务→战斗→奖励 的闭环；拆分只会引入 RPC/序列化/一致性成本，**不解决任何现存缺口**。JSTM 缺的是 **AOI / 寻路 / 技能 / 副本** 四项功能，不是架构重构 |
| **B2** | **它的具体协议**（包格式、命令号、命令号自增生成、`CPacket/CSocket` 语义、`Write_table` RPC 序列化、`CMD_PING=0xABABCBCB`） | `netcmd/netcmd.lua`、`lua/rpc.lua`、`lua/application.lua` | **JSTM 的协议来自 1.4.9 APK，是不可替代的资产**；`FINAL_SERVER_ARCHITECTURE.md` 的最高原则："APK 是最终标准，与参考项目冲突时 APK > 参考项目"。抄协议等于**丢掉唯一优势** |
| **B3** | **Redis/ssdb + JSON 字符串拼接的持久化** | `common/db.lua`、各 `DbStr/DbSave` | JSTM 用 SQLite：应**参数化 + 事务**，而不是"拼字符串 + 异步不检查 + 无事务" |
| **B4** | **`name2idx` 的"无键数组"属性存档** | `groupserver/attr.lua:DbStr` | 下标顺序一变，**全部老档作废**；JSTM 应存命名字段或 SQLite 列 |
| **B5** | **位打包**（`attr[3]` 高 16 位=强化、低 16 位=升星；`attr[1]/[2]` 装 4 个宝石） | `groupserver/item.lua` | 省带宽但**不可读、不可查、易错位**；JSTM 有 SQLite，应显式列 |
| **B6** | **用属性下标当货币**（`4001=shell/4002=pearl/4003=soul/4004=exp/4005=stamina`） | `groupserver/util.lua:NewRes` | 硬编码 `if id == 4001 then ...`；JSTM 应把货币当独立资源或按 `Item_Type` 路由 |
| **B7** | **它的所有数值**（伤害系数 2.5/2/22.5、命中 0.02/0.01/0.1、`Attack_Coefficient`、`TableTower_*`、`TableSkill_Addition` 全为 2 的占位、`Skill_CD/Public_CD/Energy`） | `role.md §4`、`battle.md §2` | **这些是编的**。`FINAL_SERVER_ARCHITECTURE.md` 已确认《绝世唐门》的**战力/技能公式【未知】**、**怪物战斗数值 APK 里不存在** ⇒ 只能"结构参考"，数值一个都不能抄 |
| **B8** | **它的地图/碰撞数据格式（`.meta`）与世界尺度（`GridLength=400`、`ViewRadiu=600`、`gridpixel=8`、`speed=27`）** | `common/lua_astar.c`、`TableMap`、`gameserver/util.lua` | JSTM 的坐标尺度与阻挡必须与 APK 一致（`_config_map_block.luac`），否则"服务端算的路径客户端走不了" |
| **B9** | **技能形态编号语义**（`Attack_Types` 0/3=单体、1=点选、2=方向）与 `Category/Check_Buff/Touch_Buff/Repel_Range` 等字段名 | `common/TableSkill.lua`、`gameserver/skill.lua` | 必须由 JSTM 客户端协议决定；字段名照搬会误导实现 |
| **B10** | **"服务端只做队友/死亡过滤"的战斗校验** | `skill.lua:UseSkill` | **反外挂缺失**：不限距离、不限角度、不限目标数、不校验能量/冷却/是否学会技能、不认识技能 id 就自动学会 ⇒ JSTM 若照抄等于**开放全图秒杀** |
| **B11** | **它的日志与可观测性** | `CLog` 用法 + 大量 `print()` | **成功也打 `LOG_ERROR`**、生产路径打 `print(cmd)`（含全量数据）⇒ 无法按级别告警；JSTM 应自建结构化日志 |
| **B12** | **`daemon.lua` 的进程管理**（`C.ForkExec/StopProcess/KillProcess/Top`） | `daemon.lua` | distri 专有 C API，Python 不可用；且其 ip 硬编码、无健康检查。思想可借，**代码与机制不可借** |
| **B13** | **`lua/http.lua` 这类玩具实现**（硬编码 `Date` 头、chunked 拼包） | `lua/http.lua` | 若要 GM HTTP 后台，用成熟框架 |
| **B14** | **它的两套状态机常量**（gate 侧 1..5 与 group 侧 1..8 语义不同） | `gateserver/gateplayer.lua` vs `groupserver/groupserver.lua` | 可读性隐患；JSTM 应统一枚举 |
| **B15** | **未完成的模块**（`notiserver` 主体被注释、`mailservice.lua` 空函数、`lua/queue.lua` 被淘汰、`common/log.lua` 未完成） | 各文件 | 不要以"它有"为理由去实现 |

### 5.3 ⚠️ LICENSE 红线（**必须写进 JSTM 的开发规范**）

> **★ Survive 没有 LICENSE ⇒ 只能借鉴设计，绝对不能复制代码。**

| 红线 | 说明 |
|---|---|
| 🚫 **不得把 Survive 的任何文件（.lua/.c/.h/.meta/表）复制或改写入 `server/`** | 无授权依据 |
| 🚫 **不得把 `common/aoi.h`、`common/astar.h`、`common/wordfilter.h` 的代码/结构体/算法实现逐行翻译** | 这三个文件**内嵌 GPLv3**（copyleft）⇒ 衍生实现同样受 GPL 约束，会迫使 JSTM 整体 GPL |
| 🚫 **不得复制 `common/b64.h`/`encode.c`/`decode.c`** | 来源为第三方（`joseph werle`），**许可文本缺失** |
| ✅ **可以**：读源码理解设计；在 JSTM 代码注释/文档中**注明"设计参考来源"**；用 Python 从零实现同样的思想 |
| ✅ **可以**：借鉴算法（均匀网格 AOI、A\*、Bresenham、位图集合运算）——**算法本身不受版权保护**，但**具体表达（代码）受保护** |
| 📝 **登记要求**：任何"拟复用"的代码段，必须在 `../license_audit.md` §四 登记表里填写「来源文件 / LICENSE / 功能 / 与 JSTM 差异 / 是否可复用 / 是否进入 JSTM」，**并默认填"否"** |

### 5.4 落地优先级（**建议 JSTM 的执行顺序**）

| 优先级 | 事项 | 依赖 | 对应设计点 |
|---|---|---|---|
| **P0** | 协议层按域拆 handler（注册表 + 异常隔离 + 未知 cmd 不崩） | 无 | D2、A1、A2 |
| **P0** | **AOI**（自写：网格 + 视野集合 + 差值 + enter/leave 回调） | 需先确定 `scene` 侧实体模型 | **D11、A10** |
| **P0** | **寻路**（自写 A\* + LOS；阻挡表与 APK 同源） | 需 `_config_map_block` 解析 | **D12、A11** |
| **P0** | **移动同步**（依 APK 协议实现"只发目标点、服务端自走、到达/失败回执、进视野补发"） | AOI + 寻路 | **D13、D14、A12、A13** |
| **P0** | 属性系统改造：**只存输入 + 登录重算 + 可见性白名单** | 无 | **D8、D9、A5、A6** |
| **P1** | 战斗：服务端权威 + **距离/角度/目标数/能量/冷却校验** + Buff 到期必定 `OnEnd` | 移动/属性就绪 | **D19、B10、A9** |
| **P1** | 发奖/合成/进图：两阶段校验 | 无 | **D18、A8** |
| **P1** | 断线重连与状态重建 | 移动就绪 | **D23、A4** |
| **P1** | 玩法 logic 接口 + 匹配队列 + 副本骨架 | AOI/寻路/战斗 | **D16、D17、A15、A16** |
| **P2** | AI（协程/状态机）+ 机器人补位 + 掉线托管 | 战斗 + 场景 | **D15、D25、A14、A17** |
| **P2** | 持久化强化（事务 + 参数化 + `updated_at` + `data_version` + 昵称/账号唯一索引） | 无 | **D20、D21、B3、B4** |
| **P2** | 压测机器人 | 协议 + 移动 | **D22、A19** |
| **P2** | 限时活动骨架（时间表落库） | 副本骨架 | **D24、A20** |
| **P3** | 运维面板（只读 + 一键启停） | 无 | **A21** |
| **条件** | 多进程拆分（**仅当单进程成为瓶颈时**） | 全部 P0/P1 | **D1、D3、D4、D26、A22** |

---

## 六、已确认的实现缺陷清单（**23 处，明确不可照学**）

> 这些是"**看起来能用，实际有坑**"的地方；JSTM 只借结构时必须绕开。

| # | 缺陷 | 位置 | 后果 | 状态 |
|---|---|---|---|---|
| 1 | **`max_recver_per_socket` 限流被注释掉**，`while true` 收包循环无退出条件 | `lua/application.lua:recver` | 协程数可能无界增长 | 【已确认】 |
| 2 | **心跳参数从未传入**（三端 `App:Add` 都没给 `recvtimeout/pinginterval`） | `gateserver/gameserver/groupserver` 入口 | 框架心跳、`CMD_PING`、超时断连**全部未生效** | 【已确认】 |
| 3 | **RPC identity 去重比较用 `or`**（应为 `and`） | `lua/rpc.lua:RPC_Process_Call` | 同秒内乱序请求会被静默丢弃且不回包 | 【已确认】 |
| 4 | **`rpcCaller:CallSync` 的 `minheap:Remove` 用模块级堆，而 `s.minheap` 可能不同** | `lua/rpc.lua` | 超时项清理不确定 | 【待验证】 |
| 5 | **`common/idmgr.lua:Release(id)` 用了未定义变量 `idx`** | `common/idmgr.lua` | 归还的 id 是 `v=nil` ⇒ **id 池被吃掉**（`avatar:Release` 每死一个实体吃一个 id） | 【已确认】 |
| 6 | **`GetAvailableSkill` 运算符优先级错误** | `gameserver/skill.lua` | AI **无视技能 CD 连放** | 【已确认】 |
| 7 | **`skillmgr:UseSkill` 对未学会的技能"现场创建"** | `gameserver/skill.lua` | 客户端可放任意技能 | 【已确认】 |
| 8 | **`skill.tb` 可能为 nil，下一行直接取下标** | `gameserver/skill.lua:UseSkill` | 非法技能 id 触发异常（靠 xpcall 兜住） | 【已确认】 |
| 9 | **`notify_suffer(..., cirt, ...)` 拼写错误** | `gameserver/skill.lua:UseSkill` | AOE 暴击表现失效 | 【已确认】 |
| 10 | **`Touch_Buff` 的 `releaser` 传成受害者自己** | `gameserver/skill.lua:UseSkill` | buff 归属错误 | 【已确认】 |
| 11 | **`TableBuff_Nexus` 查表键类型不匹配**（`["BUFF2"]` vs 数字 id） | `gameserver/buff.lua` | **Buff 互斥/替换/打断规则全部失效** | 【已确认】 |
| 12 | **`SpeedChange_OnBegin` 公式漏除 100** | `gameserver/bufffunction.lua` | 加速/减速一律被夹到上限 ⇒ **效果无差异** | 【已确认】 |
| 13 | **`buff.Range` 存了但无消费方** | `gameserver/buff.lua` | 范围型 buff 实际无范围 | 【已确认】 |
| 14 | **`achievement.lua:CMD_CG_ACHIEVE_AWARD` 里 `if awarded then return end`** | `groupserver/achievement.lua` | `awarded` 是未定义全局 ⇒ **防重复领取失效** | 【已确认】 |
| 15 | **`skills:Upgrade` 在无升级表项（满级）时仍升级且不扣钱** | `groupserver/skill.lua` | 满级后可无限免费升级 | 【已确认】 |
| 16 | **`friends.lua:DbSave` 用 `self.owner`，而 `Init` 设的是 `self.ply`** | `groupserver/friends.lua` | 好友落库必报错；且登录不读 `friends` ⇒ **好友完全不持久化** | 【已确认】 |
| 17 | **`bag:PeekInfo` 的边界判断取反**（`if end_index > beg_index ... return false`） | `groupserver/bag.lua` | 正常调用直接失败 | 【已确认】 |
| 18 | **`bag:RemItem` 的 `for i=0,self.bag.size`**（从 0 开始且越界一位） | `groupserver/bag.lua` | 弱越界；"按 id 取最后一个匹配格"语义奇怪 | 【已确认】 |
| 19 | **`friends:Pack` 用 `Write_uint16` 占位却 `Rewrite_uint8` 回填** | `groupserver/friends.lua` | 条数字段位置错位 | 【已确认】 |
| 20 | **邮件 id = `os.time():counter`，`counter` 每次构造重置为 1** | `groupserver/mail.lua` | 同一秒重登会**覆盖同 id 邮件**；`SendMailList` 回填宽度不匹配 | 【已确认】 |
| 21 | **`g_logic` 从未定义却被 `EnterSurvive` RPC 使用** | `gameserver/map.lua` | 该 RPC 一旦被调用必崩 | 【已确认】 |
| 22 | **`area:RandomDrop` 里 `CreateDrop(logic, ...)` 的 `logic` 是未定义全局** | `gameserver/maplogic.lua` | 生存赛掉落刷新必崩 | 【已确认】 |
| 23 | **`areatrigger.lua` 的 `triggers` 是模块级全局、id 来自每图独立的 `freeidx`** | `gameserver/areatrigger.lua` | 跨地图触发器 id 冲突互相覆盖；且用 **50ms 全局轮询**代替 AOI 回调 | 【已确认】 |

**另有 2 处"设计级"隐患**：
| # | 隐患 | 位置 | 说明 |
|---|---|---|---|
| 24 | **`aoi_map.radius` 同时当"视距"和"管理格边长"**，且 `Aoi.create_map` 传入 `length=50 / radius=75` | `common/aoi.c` | `cal_blocks` 的预分配数组按 `ceil(radius/_length)*2+1` 计算，与 `get_block_by_point` 的除法基数不一致 ⇒ **潜在越界**【待验证】 |
| 25 | **AOI/位图上限写死 4096**（`new_bitset(4096)`、`aoi_create(4096,...)`、`IdMgr.New(4096)`） | `lua_aoi.c`、`aoi.c`、`gateplayer.lua` | 单图/单服实体数硬上限；JSTM 不应设死 |

---

## 七、【未读到】/【未知】（严格不猜）

| 项 | 状态 |
|---|---|
| **JSTM 侧的对照材料** | 【未读】本轮**未打开** `analysis/jstm_1.4.9/*`（batch/battle/scene/movement/skill 等协议）、`analysis/1.4.9/*`、`server/mock_server.py`、`server/battle.py`、`server/proto_defs.py`。⇒ **本清单只声明"Survive 有什么"，不声明"JSTM 该怎么写协议"**；具体映射需下一轮（R3）做矩阵对照 |
| distri.lua 的 C 源码 | 【未读到】ZIP 内只有二进制 `distrilua` + `Makefile`（指向不存在的 `../KendyNet`、`../deps/lua-5.2.3`） ⇒ **本项目在 ZIP 内不可完整重编译**【已确认】 |
| `bitset.h` / `kn_dlist.h` / `minheap.h` / `kn_string.h` / `lua_util.h` | 【未读到】外部依赖，ZIP 内不存在 |
| `CPacket/CSocket` 的字节序与编解码细节 | 【未读到】 |
| `doc/` 下 4 张流程 JPG（服务器结构图/登陆流程/角色创建/玩家进入地图） | 【未读到】**本轮为文本审计，未做 OCR**；如需可用图像工具读取 |
| `php/`（1267 文件）管理台 | 【未读到】（本轮聚焦服务端逻辑） |
| `client/`（1170 文件，Cocos2d-x） | 【未读到】（本轮不审计客户端；"客户端与服务端共享寻路网格"来自文档描述，**代码层未验证**） |
| `notiserver` 是否曾运行 | 【未知】（`notiserver.lua` 主体被注释） |
| 地图 `.meta` 的逐文件数值 | 【未读到】（只确认格式：首行 xcount、次行 ycount、随后 `x*y` 个逗号分隔整数） |
| `CTimeUtil` 的时区语义（`GetTSWeeHour` 是"当日 5:00"还是"本周 5:00"） | 【待验证】 |
| Survive 的作者是否另有授权声明（README 只留邮箱） | 【未知】——**在取得明确授权前，一律视为"无许可"** |

---

## 八、审计边界声明

- **只读**：全部结论来自 `zipfile.namelist()/read()`，**未解压、未修改 `cankao/` 与 `server/` 下任何文件**。
- **逐文件**：覆盖 `gameserver/`(16) + `groupserver/`(19) + `gateserver/`(2) + `notiserver/`(5) + `common/`(67，含 40+ 表 + 8 C 源) + `lua/`(15) + `netcmd/`(2) + 根目录(6) + `doc/`(4 md)。
- **不猜**：凡未读到的，一律标【未读到】/【未知】；凡读到但语义存疑的，标【待验证】。
- **红线**：**Survive 无 LICENSE ⇒ 只能借鉴设计、绝对不复制代码**；`common/{aoi.h,astar.h,wordfilter.h}` **内嵌 GPLv3**，限制更严。
