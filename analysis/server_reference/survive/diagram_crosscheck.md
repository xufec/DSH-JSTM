# 作者流程图 × 代码 交叉核对（闭合 R1 的最后一处【未读到】）

> **背景**：`architecture.md` 的【未读到】清单里留了一条——`doc/` 下 4 张流程 JPG **本轮为文本审计未做 OCR**。
> 由于我整套报告很大程度是**从代码反推**架构与流程，用**作者自己画的图**验证是必要的诚实性工作。
> **方法**：`zipfile` 释放到 `analysis/_tmp/survive_doc/`（**未修改 `cankao/`**），用视觉模型逐张读取。
> **图片清单**（原文件名 → 分析用名）
> | 原文件名 | 分析用名 | 大小 |
> |---|---|---|
> | `doc/服务器结构图.jpg` | `diagram_1.jpg` | 86,115 B |
> | `doc/玩家进入地图处理.jpg` | `diagram_2.jpg` | 137,639 B |
> | `doc/登陆流程.jpg` | `diagram_3.jpg` | 88,267 B |
> | `doc/角色创建.jpg` | `diagram_4.jpg` | 94,496 B |
>
> ⚠ **方法学说明**：视觉模型读图**不是无损的**，且对箭头方向/小字可能有误读。因此本文件把每条结论与**代码事实**并列，**凡两者冲突的，以代码为准**（因为代码是可复读的原文）。

---

## 一、结论速览：**7 处「图 ≠ 代码」**

| # | 图说的 | 代码说的 | 判定 | 重要度 |
|---|---|---|---|---|
| **G1** | 结构图：`gateserver`、`groupserver`、`gameserver` **三者都连**"帐号数据库 + 角色数据库" | `gameserver.lua` **没有 `Db.Init`、不 require `common/db`** ⇒ game **完全不碰 DB** | **图 ≠ 代码** | 🟠 中（影响"场景进程无状态"的评价） |
| **G2** | 结构图：角色数据库画成 **3 个叠放圆柱**（多实例）；文档写"角色库可部署多个，按 chaid hash 分布" | `common/db.lua` **只有单一 `toredis` 单连接**；无任何 hash 分片代码 | **图/文档 = 设计意图；代码未实现** | 🟠 中（已记入 `database.md` §6，此处补证据） |
| **G3** | 登陆流程：**第 5~7 步由 `gateserver` 去角色数据库取角色数据并判断** | **`groupserver` 在 `PlayerLogin` 里 `hmget chaid:<chaid> nickname avatarid chainfo bag skills ...`**；gateserver 只做 `get <actname>`（账号库） | **图 ≠ 代码（职责位置不同）** | 🔴 高（我 `role.md §8` 的反推与代码一致，与图不一致 ⇒ 需明确） |
| **G4** | 角色创建：失败统一"**通知服务器繁忙请稍后再试**" | 代码三档文案：`invaild nickname` / `invaild weapon` / `retry` | 图较粗，**代码更细（代码更优）** | 🟢 低 |
| **G5** | 角色创建：两次写入都指向"**帐号数据库**" | 代码：`set <actname> <chaid>`（账号库）+ `hmset chaid:<chaid> ...`（按设计属**角色库**） | **图内部不自洽**（与结构图/文档矛盾） | 🟢 低 |
| **G6** | 玩家进入地图图：**完全没有 AOI/视野初始化**，也**没有断线重连分支** | 代码两者都有：`Aoi.enter_map` 出现在 `maplogic:entermap` / `CreateNPC` / `CreateDrop`；`CliReConn` RPC + `gameplayer:ReConnect()` + gate `IsVaild` 二次确认 | **图是 happy path，工程复杂度在代码里** | 🟠 中 |
| **G7** | 玩家进入地图图：未标注 group↔game 的通信机制 | 代码是**自研 RPC**（`lua/rpc.lua`，`Write_table` + identity 去重 + 5s 超时重试） | 图未表达（非矛盾） | 🟢 低 |

---

## 二、逐图核对

### 2.1 `diagram_1.jpg`（服务器结构图）

**图中出现的全部文字**：`client`、`gateserver`×3、`groupserver`、`gameserver`×3、`帐号数据库`、`角色数据库`（**无端口号、无"可部署多台"等标注、无 redis/ssdb 字样**）

**连线（均为无标注实线单向箭头）**
```
client      → gateserver(×3)
gateserver  → groupserver
gameserver  → groupserver
gateserver  → 帐号数据库 / 角色数据库     ← ★ 与代码一致
groupserver → 帐号数据库 / 角色数据库     ← ★ 与代码一致
gameserver  → 帐号数据库 / 角色数据库     ← ★ 与代码【不一致】(G1)
```

| 核对点 | 图 | 代码 | 结论 |
|---|---|---|---|
| 客户端只连 gate | ✅ | ✅ `TcpServer.Listen` 只在 gate 对客户端开放 | **一致**（【已确认】） |
| gate 可多台 | ✅ 画 3 个 | ✅ `name2game`/`name2gate` 按名字管理；`CMD_GA_NOTIFY_GAME` 广播给所有 gate | **一致** |
| game 可多台 | ✅ 画 3 个 | ✅ `GetMinGame()` 挑最闲的 game | **一致** |
| group 只被连 | ✅ 无出边指向 gate/game | ✅ group 从不主动 Connect | **一致** |
| **game 连 DB** | ✅ 有连线 | ❌ 无 `Db.Init` | **G1：图 ≠ 代码** |
| **角色库多实例** | ✅ 3 个圆柱 | ❌ 单连接，无分片 | **G2：设计有、代码无** |

**★ G1 的意义（对我 `architecture.md` 的影响）**：
图上"三个服务都连数据库"是**设计意图**；代码把**数据职责集中到了 groupserver**（gate 只读一个账号键，game 完全不碰 DB）。
⇒ 这**恰好印证了我给出的正面评价**："场景进程无状态"（D26）在代码里执行得**比图更彻底**。
⇒ 因此 `architecture.md §7` 的"与 JSTM 的整体对照"里"场景进程无状态"的结论**成立且得到强化**，但应注明**这是代码超越文档之处**。

### 2.2 `diagram_3.jpg`（登陆流程）

**图（时序）**
```
1) client → gateserver         : 客户端输入帐号
2) gateserver → 帐号数据库      : 以帐号为 key 查询 chaid
3) 帐号数据库 → gateserver      : 返回 chaid
4) gateserver → groupserver    : chaid 缺失则置 0，把【帐号名 + chaid】发往 groupserver
5) groupserver → gateserver    : 判断 chaid == 0 ?
     ├─ 是 → gateserver → client : 通知客户端创建角色
     └─ 否 → gateserver → 角色数据库 : 请求【角色数据】
6) 角色数据库 → gateserver      : 返回角色信息
7) gateserver 判断：是否有关联角色信息？
     ├─ 否 → client : 通知创建角色
     └─ 是 → client : 通知进入游戏
   （图中未画出 sessionid 的生成/返回步骤）
```

| 核对点 | 图 | 代码（`gateserver.lua:CMD_CA_LOGIN` / `groupplayer.lua:PlayerLogin`） | 结论 |
|---|---|---|---|
| client 先连 gate | ✅ | ✅ | **一致** |
| 账号校验 = `get <actname>` → chaid | ✅ 步骤 2-3 | ✅ `Db.CommandSync("get " .. actname)` | **一致**（【已确认】） |
| chaid==0 ⇒ 通知创角 | ✅ | ✅ `NotifyCreate()` 返回 `{true, groupsession, "create"}` → gate 发 `CMD_GC_CREATE` | **一致** |
| **有 chaid ⇒ 由 gate 读角色数据** | ✅ 步骤 5-6 | ❌ **由 group 读**：`hmget chaid:<chaid> nickname avatarid chainfo bag skills everydaysign everydaytask achievement mail` | **G3：图 ≠ 代码** |
| "有 chaid 但无角色数据 ⇒ 也要创角" | ✅ 步骤 7 | ✅ `if not result or not result[1..5] then return ply:NotifyCreate()` | **一致**（★ 图印证了这条**双创角分支**，我在 `role.md §4.1` 正是这样反推的） |
| sessionid | 图未画 | 代码：gate 造 `sessionid=(idx<<16)+(GetSysTick()&0xFFFF)` 并随 `PlayerLogin` RPC 传给 group | 图未表达（非矛盾） |

**★ G3 的意义**：图把"读角色数据"放在 gate，代码放在 group。
⇒ 代码的做法**更符合"账号库唯一 / 角色库归中心"的文档主张**（gate 不该持有角色数据）。
⇒ 我 `role.md §8` 的登录流程反推（gate 只查账号库、group 读全角色）**以代码为准是正确的**；`architecture.md §3.1` 的拓扑描述无需修改，但应注明图与代码在此不同。

### 2.3 `diagram_4.jpg`（角色创建）

**图（流程）**
```
用户输入角色名 → [chaid==0?] →(否) 申请一个唯一 chaid → 更新(角色名,chaid) → 帐号数据库
   → [更新成功?] →(否) 通知"服务器繁忙请稍后再试"
                →(是) 初始化角色数据 → 更新(chaid,角色数据) → 帐号数据库(第二个)
   → [更新成功?] →(否) 通知"服务器繁忙请稍后再试"
                →(是) 通知进入游戏
（图中未标注昵称唯一性检查、未标注武器合法性检查）
```
> ⚠ 图中"chaid==0? →(否)"的方向可能是误读（逻辑上应是"是"才申请新 chaid）。**不据此下结论**，只记录原文。

| 核对点 | 图 | 代码（`groupplayer.lua:CMD_CG_CREATE`） | 结论 |
|---|---|---|---|
| 申请唯一 chaid | ✅ | ✅ `Db.CommandSync("incr chaid")` | **一致**（【已确认】） |
| 写账号名→chaid | ✅ | ✅ `set <actname> <chaid>` | **一致** |
| 初始化角色数据（第二次写） | ✅ | ✅ `hmset chaid:<chaid> nickname avatarid chainfo bag skills everydaysign everydaytask achievement`（**一条命令 8 字段**） | **一致** |
| 失败 ⇒ "服务器繁忙请稍后再试" | ✅ 统一 | ⚠ 代码三档：`NotifyCreateError("invaild nickname" / "invaild weapon" / "retry")` | **G4：图较粗，代码更细** |
| 昵称唯一性 | 图未标 | ✅ `checkDuplicateName()`（`lua/lock.lua` 保护 + `hmget nickname`） | 图未表达 |
| 武器合法性 | 图未标 | ✅ `TableItem[weapon]["Item_Type"] ~= 2 ⇒ NotifyCreateError("invaild weapon")` | 图未表达 |
| 第二次写落在哪个库 | 图：帐号数据库 | 代码：`chaid:<chaid>`（按文档设计属**角色库**） | **G5：图内部不自洽** |

**★ 意义**：图对我的 `role.md §8` 创角流程是**正面印证**（chaid 分配 → 写账号库 → 初始化角色数据 → 成功/失败两分支），而代码在**校验与错误粒度上超出图**（昵称查重、武器类型、三档文案）。

### 2.4 `diagram_2.jpg`（玩家进入地图处理）——**对场景/AOI 最关键**

**图（流程）**
```
玩家请求进入地图
  → [开放地图?]
      ├─(否) 进入战场地图排队 → 排队完成 → 将 mapid、地图类型、玩家 发送到 game
      └─(是) 查找空闲地图实例；找不到 ⇒ 选人数最少的 gameserver 且 mapid = 0
              → [mapid == 0?]
                  ├─(是) 创建地图实例 → 玩家进入地图
                  └─(否) 按 mapid 找到地图实例 → 玩家进入地图
  → 将【玩家所在 game 与 gameid】返回 group，group 结束请求
  → 将 game 与 gameid 通告玩家所在 gate，完成后通知玩家进入地图
图中【没有】AOI/视野初始化；【没有】断线重连分支；未标注 group↔game 通信机制
```

| 核对点 | 图 | 代码 | 结论 |
|---|---|---|---|
| "开放地图?" 分流 | ✅ | ✅ `TableMap[k].PlayType`：`"open"` / `"personal"` / `"mutil"` | **一致**（【已确认】） |
| 非开放 ⇒ 排队 ⇒ 排队完成 | ✅ | ✅ `ReqQue:Push` → `Tick`（凑够 `plyMax` **或**队首超 `MaxWait` 即 `ProcessEnter`） | **一致**（★ 图印证了 `groupserver/map.lua:ReqQue`） |
| 找空闲实例；没有就选**人数最少**的 game 且 **mapid=0** | ✅ | ✅ `GetInstanceByType(type,count)`：能容纳则复用；否则 `return {Game.GetMinGame(), nil}`；`EnterMap(0, maptype, plys)` | **一致**（【已确认】，`scene.md §8` 的反推被证实） |
| `mapid==0` ⇒ 创建地图实例 | ✅ | ✅ `gameserver/map.lua` RPC `EnterMap`：`if mapid == 0 then mapid = mapidx:Get(); m = map:new(mapid,type)` | **一致** |
| 返回 game + gameid | ✅ | ✅ `entermap` 返回 `gameids` 数组 → `Game.Bind(game,ply,gameids[i])` | **一致** |
| 通告玩家所在 gate ⇒ 通知玩家进入地图 | ✅ | ✅ game 回 `CMD_SC_ENTERMAP`（带 `u32 self.id`）→ **gate 在 `OnInnerMsg` 里顺手完成 `ply.gamesession` 绑定** | **一致**（★ 这条"用业务回包驱动连接绑定"我在 `network.md §3.2` 反推过，图证实了**通告 gate** 这一步） |
| **AOI/视野初始化** | ❌ 无 | ✅ `Aoi.enter_map(map.aoi, obj.aoi_obj, x, y)` 出现在 `maplogic:entermap` / `CreateNPC` / `CreateDrop`；视野靠 `enter_see/leave_see` 回调 | **G6：图是 happy path** |
| **断线重连** | ❌ 无 | ✅ `CliReConn` RPC + `gameplayer:ReConnect()`（逐个 `SendEnterSee` 重建视野）+ gate 的 `IsVaild` 二次确认 + group 的 60s `LogOutTimer` | **G6：同上** |
| group↔game 通信机制 | 未标注 | 自研 RPC（`lua/rpc.lua`） | **G7：图未表达** |

**★ G6 的意义（对 JSTM 的直接启示）**：
> **作者的"设计文档"只覆盖 happy path；AOI、视野、断线重连这些都是工程阶段补进代码的。**
> ⇒ 对 JSTM 的启示：**不要把 `doc/` 级设计图当作完整需求**；JSTM 的 `FINAL_SERVER_ARCHITECTURE.md` 里已列出的"移动/NPC 对话未闭环""重连"等问题，**正是这类"happy path 之外"的部分**——它们在 Survive 里也**不在图里，只在代码里**。
> ⇒ 这也反向支持我 `scene.md §9` 的建议清单（D11–D14）**必须实现，不能只画在图上**。

---

## 三、本次核对对既有报告的**修订/补强**

| 报告 | 位置 | 动作 | 说明 |
|---|---|---|---|
| `architecture.md` | §9【未读到】表 | ✅ **闭合**"4 张流程 JPG 未读"这一条 | 指向本文件 |
| `architecture.md` | §3.1 连接拓扑 | 🔧 **补注 G1/G2** | 结构图显示三个服务都连 DB（含 game），**代码里 game 不碰 DB** ⇒ "场景进程无状态"是**代码超越文档**之处 |
| `architecture.md` | §7 与 JSTM 对照 | 🔧 **补注** | 同上：D26 的评价因此更成立 |
| `role.md` | §8 登录/创角流程 | ✅ **被图印证**（除 G3 的职责位置、G4 的错误粒度） | 我按代码反推的流程**与图基本一致** |
| `scene.md` | §8 场景分配 | ✅ **被图完整印证** | `GetInstanceByType`/`GetMinGame`/`mapid=0`/`ReqQue` 全部对上 |
| `network.md` | §3.2 | ✅ **被图印证**"通告 gate + 用回包驱动 gamesession 绑定" | — |
| `database.md` | §6 风险"分库未实现" | ✅ **补证据**（G2：结构图画了 3 个角色库实例，代码零分片） | — |

---

## 四、【未知】与局限

| 项 | 状态 |
|---|---|
| 图的**画图时间**（是否与最终代码同期） | 【未知】ZIP 内无元数据可用于判断；**G1/G3 的差异可能是"图旧代码新"或"图是理想/代码是取舍"** |
| `diagram_4` 中 `[chaid==0?] →(否)` 的箭头方向 | 【待验证】读图可能误读；**本文件不据此下任何结论** |
| 箭头是否有颜色/虚实区分（可能表达"可多台"） | 【未读到】视觉描述未提及颜色 |
| 图中文字是否有小字注记（如"可部署多台"） | 视觉模型明确回答"无"；但**小字漏读风险存在** |
| `doc/管理系统的.md` 描述的 router/daemonserver | 已确认 **ZIP 内无对应源码**（见 `architecture.md` §4），与本次核对无关 |
