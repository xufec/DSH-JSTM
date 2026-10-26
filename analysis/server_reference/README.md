# R1：五项目 + JSTM APK 架构审计

> 依据附件任务书执行。**本阶段只审计，不写新功能、不改现有服务端代码。**
> 所有结论分为【已确认】【已验证】【待验证】【未知】；**不把 INFERRED 写成 CONFIRMED**。

---

## 一、审计对象与实测基础

### 1.1 五个参考项目（**实测自 `cankao/*.zip`，非推测**）

| # | 项目 | ZIP | 文件数 | 服务端代码位置（实测） |
|---|---|---|---|---|
| 1 | **Survive** | 207.7 MB | 2618 | `gameserver/`（16 lua）+ `gateserver/` + `groupserver/` |
| 2 | **CXEngine = YZXY / 原罪西游**（★ **用户已确认**） | 14.8 MB | 501 | `scripts/server/`、`scripts/combat/`、`scripts/share/`、`server/src/` |
| 3 | **MahatmaComeBack** | 18.2 MB | 164 条目（**136 文件**） | `Server/游戏服务器`（**15**，R2 逐条目更正）+ `Server/gametable.sql` |
| 4 | **ChivalrousMan** | 51.2 MB | 1539 条目（**1411 文件**） | **无服务端目录**（自研代码仅 `Classes/` 191 文件；服务端在作者另开的 `gitee.com/lsylovews/CM-Server`，不在 ZIP）⚠ 但客户端 libmysql 直连 MySQL ⇒ **反推出 5 表 / 33 字段业务库结构** |
| 5 | **kongkongxiyou** | 331.8 MB | 22486 | `lordofpomelo/game-server/app/servers/`（39 js）+ `app/domain/`（48） |

**★ 身份确认（用户于 2026-09-18 确认）**：任务书第 2 项「YZXY / 原罪西游」
**就是 `CXEngine-master.zip`** ⇒ 本报告中 `CXEngine` 与 `YZXY` 指同一项目。
（C++ 54 / Lua 67 / `.wpal` 121；`scripts/{client,server,combat,share}` 布局）

### 1.2 JSTM 1.4.9 APK（已由前序工作建立事实基础）

| 事实 | 状态 |
|---|---|
| Cocos2d-x 3.6 + LuaJIT 2.0 bytecode | 【已确认】 |
| 线格式 `[u32 BE len][u16 BE cmd][body]` | 【已验证】 |
| `code == TRUE(1)` 才成功 | 【已确认】 |
| **347 张配置表**（`assets/src/config/*.luac`） | 【已验证】（通用读取器实测） |
| `all_proto.luac` / `cmd_resolve_*.luac` 协议定义 | 【已验证】 |
| 物品 3535 条、任务 846 条、商城 134 件、礼包 496 个 | 【已验证】 |
| 服务端已实现：登录/角色/场景/任务/背包/装备/仓库/商城/聚宝盆 等 | 【已验证】 |

---

## 二、★ 五个参考项目的架构要点（实测）

### 2.1 Survive —— **实时手游多服务组架构**（最有价值）

**README 原文（已确认）：**
```
Survive 是使用 distri.lua 框架实现的一个小型手游服务端示例.
除了 aoi 和 astar 两个模块以外, 所有游戏逻辑皆使用 lua 编写.

服务组成：
  gateserver  前端连接服务器, 可部署多台。负责把玩家消息转发到内部服务器组 / 把内部消息发往玩家
  groupserver 中心服务器, 只有一台。管理整个服务器组 + 处理全局逻辑
  gameserver  战斗及地图服务。负责玩家在场景中的移动、战斗。**单线程, 每个服务可加载 1-n 个场景**
```
**服务端 lua 文件（实测 16 个）**：
`gameserver.lua` `gameplayer.lua` `gate.lua` `map.lua` `maplogic.lua` `areatrigger.lua`
`attr.lua` `avatar.lua` `battlebag.lua` `buff.lua` `bufffunction.lua` `skill.lua`
`robot.lua` `snail.lua` `triggerfunction.lua` `util.lua`

**⇒ 可借鉴点**：**服务组拆分（gate/group/game）+ 单线程多场景 + 逻辑全 Lua**。
**⇒ 与 JSTM 的差异**：JSTM 是 **单进程 Python mock**，无网关分层。

### 2.2 kongkongxiyou —— **Pomelo 分布式**

**实测的服务器模块：**
```
auth/remote/authRemote.js
connector/handler/entryHandler.js + roleHandler.js      ← 连接/角色入口
area/handler/{boss,chat,equip,federate,fight,guild,market,
              player,resource,shop,skill,task,team}Handler.js   ← 场景内业务
area/remote/{area,guild,player}Remote.js                ← 跨服 RPC
chat/handler + chat/remote
```
**⇒ 可借鉴点**：**按业务域切 handler（task/skill/shop/team…）+ remote 做跨进程 RPC**。
**⇒ 与 JSTM 的差异**：JSTM 的 CMD 分发是**单文件 if 链**，无模块化 handler 注册。

### 2.3 CXEngine —— C++/Lua 引擎 + combat 分离

```
scripts/client/{actor_manager,actor_metatable,addon/{action,bag,battle,hud,options,props,quest},...}
scripts/server/  scripts/combat/  scripts/share/
server/src/（C++ 7 文件）
```
**⇒ 可借鉴点**：**`scripts/share`（共享定义）+ 独立 `combat`** 的分层；`addon/` 按功能插件化。
**⇒ ⚠ 待确证**：它是否就是任务书所指的 YZXY。

### 2.4 MahatmaComeBack —— Cocos 客户端 + 独立 Server 目录 + MySQL

```
Server/游戏服务器（**15 文件**；`Server/` 下合计 19，R2 逐条目更正，原写 17） + Server/gametable.sql
```
**⇒ 可借鉴点**：**客户端/服务端物理分离 + 用 `.sql` 定义表结构**。
**🔴 限制**：**GPL-3.0 传染 ⇒ 代码不得进入 JSTM。**

### 2.5 ChivalrousMan —— **实测无服务端**

1539 文件中**没有 `server/` 目录**，以 `.cpp/.h/.java/.class` 为主（客户端）。
**⇒ 作为"传统 MMORPG 业务流程参考"的**价值限于客户端侧**（任务/装备/技能的客户端流程）。**

---

## 三、统一比较维度（任务书第五节）—— 逐项打分

**评分口径**：0=不适合 1=仅概念 2=部分参考 3=高度参考 4=非常适合 5=与 JSTM 结构高度匹配

| 维度 | Survive | CXEngine | Mahatma | 侠客行 | 空空西游 | **JSTM 现状** |
|---|---|---|---|---|---|---|
| 网络层 | **5** | 3 | 2 | 1 | **4** | 自定义 TCP（已验证） |
| 网关 Gateway | **5** | 2 | 1 | 0 | **5** | **无** |
| 角色 | 4 | 4 | 3 | 3 | 4 | **已实现** |
| 场景 | 4 | 3 | 2 | 1 | **5** | 已实现（基础） |
| **AOI** | **4**（C 模块） | 3 | 1 | 0 | **4** | **无** |
| 寻路 | **4**（astar C 模块） | 3 | 3 | 1 | **4** | **无** |
| 任务 | 3 | **4**（addon/quest） | 3 | **4** | **4** | **已实现** |
| 战斗 | **4** | **4**（combat） | 2 | 3 | **4** | 部分（TEST_ONLY） |
| EXP/等级 | 4 | 4 | 3 | 3 | 4 | **已实现** |
| 背包 | **4** | **4**（addon/bag） | 3 | 3 | **4** | **已实现** |
| 装备 | **4** | 4 | 3 | 3 | **4** | **已实现** |
| 技能 | **4**（skill.lua） | 4 | 3 | 3 | **4** | 未实现 |
| 伙伴 | 2 | 2 | 1 | 1 | 3 | 部分（列表） |
| 副本 | **4**（单人/5人/5V5） | 3 | 2 | 2 | 4 | **无** |
| 数据库 | 3 | 3 | **4**（.sql） | 3 | 4 | SQLite（已实现） |
| Lua/C++ 结构 | **5** | **5** | 2 | 1 | 4 | 纯 Python |
| **LICENSE 可用性** | 0（无） | 0（无） | **0（GPL）** | 0（无） | 0（无） | — |

**⚠ 打分只是工程适配度，**不能替代 APK 协议证据**。**

---

## 四、★ 关键判断（任务书第十六节 58 问的回答）

| 问题 | 结论 |
|---|---|
| **网络层**参考谁 | **kongkongxiyou**（pomelo 分层）+ **Survive**（C 层处理高频） |
| **Gateway** 参考谁 | **kongkongxiyou**（connector）+ **Survive**（gateserver 可多台） |
| **角色系统**参考谁 | 以 **JSTM APK 协议**为准；实现思路参考 Survive `gameplayer.lua` |
| **场景系统**参考谁 | **kongkongxiyou**（area + domain 分离） |
| **AOI** 参考谁 | **Survive**（C 模块；JSTM 目前**无**） |
| **寻路** 参考谁 | **Survive**（astar C 模块） |
| **任务** 参考谁 | **CXEngine `addon/quest`** + **kongkongxiyou `taskHandler`**（JSTM 已实现，可对照） |
| **战斗** 参考谁 | **CXEngine `scripts/combat`** + **Survive `skill.lua`** |
| **背包/装备** 参考谁 | **CXEngine `addon/{bag,props}`**（JSTM 已实现） |
| **技能** 参考谁 | **Survive `skill.lua`** + **CXEngine** |
| **数据库** 参考谁 | **MahatmaComeBack 的 `.sql` 组织方式**（**只看结构，不用代码**） |
| **Lua/C++ 结构** 参考谁 | **Survive（distri.lua）** + **CXEngine** |
| **哪些代码可合法复用** | **一个都不能直接复制**（见 `license_audit.md`） |
| **哪些只能参考** | **全部 5 个项目**（4 个无许可 + 1 个 GPL） |
| **JSTM 真实协议放哪层** | **Protocol Adapter 层**（与 Game Core 解耦）—— 见下 |
| **现有服务端哪些保留** | **全部保留**（协议实现已验证，是最大资产） |
| **哪些需要重构** | CMD 分发的 `if` 长链 ⇒ 建议按域拆 handler（借鉴 kongkongxiyou） |
| **哪些需重新实现** | **AOI / 寻路**（JSTM 目前完全没有） |
| **推荐目录结构** | 见 `FINAL_SERVER_ARCHITECTURE.md` |
| **最小 Vertical Slice** | 已在运行（登录→角色→场景→NPC→任务→战斗→奖励） |
| **第二阶段应做什么** | 协议层解耦（Protocol Adapter）+ AOI/寻路 |
| **第三阶段应做什么** | 副本/技能/伙伴等外围系统 |

---

## 五、★ 与 JSTM 的**根本差异**（必须正视）

| 维度 | 参考项目 | **JSTM 现状** |
|---|---|---|
| 服务形态 | 多为 **gate/group/game 多进程** | **单进程 Python** |
| 语言 | C+Lua / Node.js / C++ | **Python** |
| 协议 | 自研二进制 | **逆向后适配的 1.4.9 原版协议** |
| 数据 | MySQL 为主 | **SQLite** |
| AOI/寻路 | 多数有 | **无** |

**⇒ 结论：参考项目的**代码**几乎不可用，但**分层思想**高度可用。
JSTM 最大的独特资产是 **已经跑通的 1.4.9 原版协议实现** —— 这是任何参考项目都没有的。**

---

## 六、完成度自评（R2 更新）

| 项 | R1 状态 | **R2 状态** |
|---|---|---|
| 5 个项目结构 + 服务端定位 | ✅ 实测完成 | ✅ 完成 |
| LICENSE 审计 | ✅ 完成 | ✅ 完成并**更正 2 处**（Mahatma `Server/游戏服务器` 15 而非 17；ChivalrousMan **无 `client/` 目录**） |
| 统一维度比较 | ✅ 完成 | ✅ 完成 |
| JSTM APK 事实基础 | ✅ 沿用前序已验证结论 | ✅ 完成（协议 3553 / CMD 1652） |
| **逐文件架构深读（每一层类的类/函数）** | ⚠️ **未完成**（仅到"目录级 + 关键文件级"） | ✅ **五项目全部完成**，落到 `survive/` `yzxy/` `kongkongxiyou/` `mahatma/` `chivalrousman/` 各子目录 |
| **五项目 × JSTM 映射矩阵（R3）** | ⏳ 待做 | ✅ **已产出**：`comparison/architecture_matrix.md` |
| 5 个项目 × 逐文件报告数量 | — | **39 个 Markdown**：Survive 10 / YZXY 7 / kongkongxiyou 7 / 侠客行 5 / 大圣归来 5 / 矩阵 1 / 根级 4（实测计数） |

### 6.1 R2 事实更正登记（本轮发现并已修正）

| # | 位置 | 原值 | 更正为 | 依据 |
|---|---|---|---|---|
| 1 | 本文件 §1.1 / `license_audit.md` / `FINAL_SERVER_ARCHITECTURE.md` / `mahatma/architecture.md` | Mahatma `Server/游戏服务器`（**17** 文件） | **15 文件**（`Server/` 下合计 19） | `zipfile` 逐条目实测 |
| 2 | 同上 | Mahatma「164 文件」 | **136 文件**（164 是含 28 个目录的**条目数**） | 同上 |
| 3 | 同上 | ChivalrousMan「1539 文件」 | **1411 文件**（1539 是条目数） | 同上 |
| 4 | `license_audit.md` §4 | ChivalrousMan「顶层：`client/`」 | **无 `client/` 目录**；顶层为 `Classes/ Resources/ cocosstudio/ include/ lib/ proj.android/ proj.ios_mac/ proj.win32/` + 6 文件 | 同上 |
| 5 | `comparison/architecture_matrix.md` LICENSE 行 | 「★ 全部不可复制（**GPL-3.0 传染**）」 | **仅大圣归来是 GPL-3.0**；其余 4 个为「无许可依据（默认保留全部权利）」 | `license_audit.md` |
| 6 | `mahatma/architecture.md` §〇 | `Resources/` 68；`proj.android + proj.win32` 24 | `Resources/` **54**；`proj.android` **24** + `proj.win32` **11** | `zipfile` 逐条目实测 |
| 7 | `mahatma/role.md`、`mahatma/architecture.md` §九 | `attackAction()` / `state::DEAD`【待验证】 | 【已确认】**无调用点 / 零引用** | 全 `Classes/` grep |
| 8 | `mahatma/architecture.md` §5.2 | `map.tmx` 阻挡格【待验证】 | 【已确认】**202/520 格为墙，GID 全为 1041** | base64+zlib 解码 |
| 9 | `chivalrousman/architecture.md` §5 | 8 技能 / 10 怪物 `.att`【未读到】 | 【已确认】**全部读到并列出完整数值表** | 逐份读取 |
| 10 | `chivalrousman/architecture.md` §9 | 任务是否走 TCP【待验证】 | 【已确认】**不走 TCP、不落库，客户端每 15 秒随机生成** | `TaskSystem.cpp:35/52-63/101-102` |
| 11 | `comparison/architecture_matrix.md` 任务行 | 侠客行任务 4 分无注 | 加注：**其权威模型（客户端随机生成 + 本地发奖）不可借鉴** | `chivalrousman/task.md` 附录 D |
| **12** | `FINAL_SERVER_ARCHITECTURE.md` §四 / `comparison/architecture_matrix.md` 任务行 | 「任务 → **CXEngine `addon/quest`** 的目标类型」 | ① **YZXY 任务降为「❓未取证」** —— `scripts/client/addon/quest.lua` **从未被读过**；② 首选参考改为 **空空西游 `app/domain/task/*.js`**（`TaskState` 4 态与 JSTM `mission_status 0/1/2/3` **1:1 同构**）+ 侠客行（第二个独立 4 态样本）；③ 维度更正：参考项目的 `TaskType`（3 类）对应 JSTM 的 **`progress` 计算方式**，**不是** `MissionType`（28 类业务分类） | `comparison/task_matrix.md` §三/§八；`yzxy/architecture.md:214`、`yzxy/lua_server.md:422` |
| **13** | `comparison/` 矩阵缺口 | 无 `database_matrix` / `task_matrix` | 已产出：`comparison/database_matrix.md`（R4）+ `comparison/task_matrix.md`（R5） | 见两文件头部「闭环 R1_SUPPLEMENT §六」说明 |
| **14** | `comparison/architecture_matrix.md` §三+§一 / `R1_SUPPLEMENT.md` §二 / `FINAL_SERVER_ARCHITECTURE.md`（**共 9 处**） | 「JSTM 有 **`CS_20014` ACK 节流**」「回合节奏**所有权相反**」「照搬会**丢掉 ACK 节流**」 | ★ **全部作废**：真机 `tcp.log` **无 `cmd=20011`/`cmd=20014`**，客户端收 `SC_20020` 后只发 `CS_20021`。原结论引自 `battle_chain_verified.md`，**而那份文档描述的是我们自己的 `mock_server.py` 实现**（`行 2445 if cmd == 20014:`）⇒ JSTM **必须服务端自定节拍**（2.5 s 自续期）；「所有权相反」**不成立**；不可移植的真正理由是 **5 条字段级理由** | `analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1；`yzxy/battle.md:523-548`；`comparison/battle_matrix.md` §三 |
| **15** | `FINAL_SERVER_ARCHITECTURE.md` §〇 取证依据 | 引 `battle_chain_verified.md` 为「✅ **决定性结果**」 | **降级为「我们自己 mock 的实现记录」**（非真机取证） | `yzxy/architecture.md:28-35` |
| **16** | 全库对 `jstm_1.4.9/battle_protocol.md` 的引用 | 视为"战斗协议" | ⚠ 其覆盖的 `13000~13099`（98 条）**实为副本/爬塔/章节/成就**；**真实战斗在 `20000~20099`（25 条）** | `comparison/battle_matrix.md` §2.1 |
| **17** | `analysis/1.4.9/role/role_persistence.md` | 「先用 **JSON 落盘**」「当前只落地了 **rid + x + y**」「`name/lev/career/scene_id/hp/mp/uid` 全部 ⬜ 未存」 | 🔴 **已过期**（Phase 4E 之前的状态）：`save_role_pos()` docstring 自证「**Phase 4E 起以 DB 为准**」；实测 `roles` 表 **23 列**已含上述全部字段。**已在该文件头部加 R7 过期横幅** | `server/mock_server.py:2399-2401`；`roles` 表 23 列 |
| **18** | `survive/role.md:17` | 「`attr_db_save = attack-1` ⇒ **只持久化前 31 项**」 | **23 项**（同文 `:158` 已自证 `= 23`；`attack` 为第 24 项）⇒ 原为笔误 | `survive/role.md:146/:158` |
| **19** | `comparison/database_matrix.md` G4 行 | 「`role_attr` 的 26 列输入项与派生项混存」（P1） | **量化 + 升 P0**：属性系统 **`AttrLen = 64`** 而 `role_attr` 只有 **25 个属性列** ⇒ **落库 25/64、39 个未落库**（其中 21 个是不该落库的派生项） | `analysis/1.4.9/level/_attr.json`；`role_attr` 26 列 |

---

## 七、`R1_SUPPLEMENT.md` §六「仍未做」清单的推进状态

| # | 原未做项 | 状态 | 产出 |
|---|---|---|---|
| ① | `comparison/database_matrix.md` | ✅ **R4 完成** | `comparison/database_matrix.md`（285 行；含 JSTM 11 表 98 列实测、五项目存储模型、缺口 G1~G10、15 条反例） |
| ② | `comparison/` 其余矩阵（`protocol`/`role`/`task`/`battle`/`scene`/`license`） | 🟡 **已完成 3/6** | `comparison/task_matrix.md`（R5：4 态/3 类收敛、逐字段映射、缺口 G1~G8、★ 纠正 CXEngine quest 未取证）<br>`comparison/battle_matrix.md`（R6：JSTM `20000` 段真实战斗模型、`SC_20012/20013` 字段、缺口 B1~B8、★ 传播「ACK 节流」更正）<br>`comparison/role_matrix.md`（R7：**`AttrLen=64` vs `role_attr` 25 列**、五项目属性系统四方对照、缺口 G1~G10、★ 标注 `role_persistence.md` 过期）<br>余 `protocol` / `scene` / `license` **3 个** |
| ③ | `jstm/` 的 8 个模型文档 | ⏳ 未做 | 需 JSTM 侧实现知识，建议交给熟悉 `server/` 的 agent |
| ④ | R3 矩阵"逐项细化"（子代理设计点逐条映射进 CMD 矩阵） | ⏳ 未做 | 跨 5 项目，建议主 agent 统筹 |

**⇒ `comparison/` 目录现有 5 个矩阵**：`architecture_matrix.md`（R3）+ `database_matrix.md`（R4）+ `task_matrix.md`（R5）+ `battle_matrix.md`（R6）+ `role_matrix.md`（R7）。
