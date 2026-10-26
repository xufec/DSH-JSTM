# ChivalrousMan（侠客行）—— 可复用候选与许可说明（★ 无 LICENSE）

> 对象：`cankao/ChivalrousMan-master.zip`（51.2 MB / 1539 条目）
> 用途：给 JSTM（《绝世唐门》1.4.9 私服兼容项目）判断"哪些东西可以借鉴、哪些不能碰"。

---

## 一、★ 许可状况（必须先读）

### 1.1 实测事实

| 项 | 实测 | 标注 |
|---|---|---|
| 是否存在 `LICENSE` / `COPYING` / `LICENCE` 文件 | **不存在** —— 全仓库递归扫描 `^(license\|copying\|licence)` **0 命中** | 【已确认】 |
| 源码文件内是否有 SPDX / 版权头 | **未见**（`Classes/*.{h,cpp}` 头部只有 `#pragma once` 与 `#include`） | 【已确认】 |
| `README.md` 是否声明许可 | **未声明**（README 只讲玩法、截图、部署、以及服务端在 `gitee.com/lsylovews/CM-Server`） | 【已确认】 |
| 仓库内是否含第三方组件 | ✅ 大量：`cocos2d-x`（`proj.android/src/org/cocos2dx/lib/` 26 个 Java、`include/` 68 个 MySQL 头）、`CocosPlay`（`com.chukong.cocosplay.client.CocosPlayClient`、`com.enhance.gameservice.IGameTuningService`）、`libmysql.dll/libmysql.lib/mysqlclient.lib`、`luajit/curl/openssl` 等引擎内嵌库 | 【已确认】 |
| 第三方组件各自的 LICENSE 文件是否随包分发 | **未读到**任何第三方 LICENSE 文件 | 【已确认】 |

### 1.2 ★ 无 LICENSE 的实际含义（关键区分）

> ## ✅ **本项目不是 copyleft，不存在 GPL 传染问题。**
> 与 `../mahatma/`（**GPL-3.0 强 copyleft**）形成鲜明对比：
> **ChivalrousMan 没有 GPL 那类"一旦并入即要求 JSTM 整体开源"的强制条款。**
>
> ## ⚠ 但"无 LICENSE"**不等于**"已获授权"。
> 按通行版权规则，**未声明许可 = 默认保留全部权利**（并非自动进入公有领域）。
> 本项目在 R1 阶段确立的【原则 3】对此已给出可执行口径：
> **「LICENSE 不明确时：可研究、可借鉴设计、不要直接复制代码。」**
> 本文件与全部子报告都遵循该口径。

### 1.3 对 JSTM 的实操口径

| 允许 ✅ | 建议避免 ⚠ | 禁止 ❌ |
|---|---|---|
| 阅读全部源码、资源与 `README` | 大段逐字复制 `Classes/` 的 C++ 代码进 JSTM | 声称这些代码是 JSTM 自研 |
| **借鉴设计**：分层形状、协议字段清单、数据表结构、状态机、宏定义语义 | 直译（逐行翻译）后作为自研代码 | 把 `Resources/` 的**美术资源**（`player1..4/` 共 228 个 png、`Monster/` 78、`Skill/` 123、`Thing/` 133、`WorldMap.png`、`.ttf` 等）直接用于 JSTM 发行 |
| **借鉴字段语义**（`Model.h` 的 5 张表字段清单） | 复制 `Resources/GameData.xml`、`*.xxp`、`*.att`、`*.tsk` 等配置文本 | 复制 `libmysql.dll` / `mysqlclient.lib` 等第三方二进制（受 MySQL 自身许可约束） |
| 记录"该设计来自 ChivalrousMan"作为来源说明 | 把带 `com.chukong` / `com.enhance` 的 CocosPlay 代码并入 | 把硬编码的数据库凭据当作"可复用配置"使用（见 §1.4） |
| 用其**业务表结构**作为 JSTM 表设计的对照基线 | 复制 `proj.android/bin/*.class`（第三方编译产物） | — |

### 1.4 ⚠ 安全提醒（不是许可问题，但同样重要）

`Classes/DBDao.h:107-110` 硬编码了**一个公网 MySQL 库的账号密码**：
```cpp
m_host("47.93.235.6"), m_passwd("3252918599lsy"), m_username("game"), m_dbname("chivalrousman")
```
这**不是**"可复用的配置"，而是一个**已泄露的凭据**。JSTM 中**绝不可**出现同类做法（客户端直连数据库、凭据进客户端）。

---

## 二、★ 本项目对 JSTM 的独特价值（一句话）

> **它是唯一一个把"传统 MMORPG 的完整业务数据结构"以可读代码形式暴露出来的参考项目。**
> Mahatma 只有 1 张账号表；ChivalrousMan 的 `Model.h` 一次给出 **5 张表 / 33 个字段**，
> 且每条持久化路径（增删改查）都有明确调用点。
> **⇒ 价值定位：数据库结构与业务流程的"对照基线"，而不是代码来源。**

---

## 三、可复用候选清单（**全部为"设计/字段语义"层面**）

### 3.1 数据库与数据模型（★ 最高价值）

| # | 来源 | 借鉴内容 | 复用形态 | JSTM 应如何落地 | 标注 |
|---|---|---|---|---|---|
| D1 | `Classes/Model.h` → `GamePlayer` / 表 `player` | **账号表 3 字段**：`playername`、`playerpsw`、`nums`（角色数计数） | **字段清单** | ★ **"账号表用一个计数列管理角色上限"** 的极简做法可参考（JSTM 建议改用 `COUNT(*)` + 上限校验） | 【已确认】 |
| D2 | `Classes/Model.h` → `PlayerInfo` / 表 `playerinfo` | ★ ★ **角色表 15 字段全清单**：`playername, rolename, roletype, glod, grade, blood, mana, attack, defense, speed, exp, maxexp, destx, desty, level` | **字段清单** | JSTM 的角色表设计可直接对照；特别注意 `destx/desty`（下线点）与 `level`（实为**地图号**，见 D6） | 【已确认】 |
| D3 | `Classes/NewGameLayer.cpp::constructPlayerInfo` | ★ **建号初值 "配方"**：attack 100 / blood 300 / defense 20 / glod 300 / grade 1 / mana 150 / speed 4 / exp 0 / maxExp 100 / destx 100 / desty 100 / level 1 | **数值配方** | JSTM 需要一套"1 级新角色的属性基线"，这是可直接对照的最小可用数值组 | 【已确认】 |
| D4 | `Classes/Model.h` → `SkillInfo` / 表 `skillinfo` | **技能表 4 字段**：`playername, rolename, skillname, skillgrade` | **字段清单** | JSTM 技能表可对照；但 JSTM 有 8 个技能上限与 CD/等级上限，需扩展 | 【已确认】 |
| D5 | `Classes/Model.h` → `EquipmentInfo` / 表 `equipmentinfo` | **装备表 5 字段**：`playername, rolename, equipmentname, grade, type`；`type` = **槽位**（非物品分类） | **字段清单 + 设计意图** | ★ **"一张表用 `type` 表达槽位、同槽穿新卸旧"** 的做法很紧凑；JSTM 若用 `slot` 列可对照 | 【已确认】 |
| D6 | `Classes/Model.h` → `BackPack` / 表 `backpack` | **背包表 6 字段**：`playername, rolename, thingname, thingtype, thingnums, thinggrade`；一张表容纳 **药品/装备/技能书** 三类 | **字段清单 + 统一容器设计** | ★ **"统一容器 + 类型字段"** vs "按类型分表"是 JSTM 需要做的一个明确取舍；本项目给出了统一容器方案 | 【已确认】 |
| D7 | `Classes/PreProcess.h:104-113` | ★ **物品/装备/任务/状态宏定义**：<br>`MEDICATION 1001` / `EQUIPMENT 1002` / `SKILL 1003`<br>`EM_HEAD 1005` / `EM_WEPON 1006` / `EM_JEWELRY 1007` / `EM_CLOTH 1008` / `EM_FOOT 1009`<br>`T_KILL 2001` / `T_COLLECT 2002` / `T_ACCESS 2003`<br>`NS_FREE 3001` / `NS_HTASK 3002` / `NS_WSTASK 3003` / `NS_STASK 3004`<br>`P_STATUS_NORMAL 4001` / `P_STATUS_HEADER 4002` / `P_STATUS_MEMBER 4003`<br>`TB_DISSOLVE 5001` / `TB_QUIT 5002` / `TB_KICKOUT 5003` / `TB_NULL 5004` | ★ **枚举取值定义**（千位分段：1xxx 物品、2xxx 任务、3xxx NPC、4xxx 玩家、5xxx 队伍） | ★ ★ **这是本项目最值得借鉴的一处**：**用千位分段给全局枚举编号**，一个头文件即可读懂所有领域常量。JSTM 可据此自查自己的常量命名空间 | 【已确认】 |
| D8 | `Classes/DBDao.h`（`generateSql`/`generateWhere`/`generateValues`/`generateUpdate`） | **泛型 DAO 的 SQL 生成形状**（`Model` 自描述表名 + 字段名 + 序号映射） | **设计形状** | ★ "实体自描述表结构 → DAO 泛型化"是干净思路；但 JSTM **必须**改为参数化 + 事务 + UPSERT（本项目这三项全缺，且 `saveXxxInfo` 用 INSERT 导致数据膨胀） | 【已确认】 |

### 3.2 协议与网络分层

| # | 来源 | 借鉴内容 | 复用形态 | JSTM 应如何落地 | 标注 |
|---|---|---|---|---|---|
| N1 | `Classes/ShareData.h` | ★ ★ **23 个 `M_Type` 命令枚举**（`M_EntryGame`…`M_PlayerDie`）+ **22 个定长 `*_Msg` 结构体** | **命令清单 + 字段清单** | ★ 可对照 JSTM 的协议覆盖度：本项目覆盖了 移动/位置校验/属性同步/聊天(世界+私聊)/组队(8 种)/战斗(6 种)/用药/离线。**JSTM 应逐项核对哪些已有、哪些缺** | 【已确认】 |
| N2 | `Classes/ShareData.h` → `Player_Info` | 远端玩家广播字段：`playername, rolename, blood, mana, attack, defense, curmap, playertype, x, y, grade, fd` | **字段清单** | JSTM 的 AOI 实体字段可对照 | 【已确认】 |
| N3 | `Classes/ShareData.h` → `UpdateData_Msg` | **属性变化单独一条消息**（`blood, mana, attack, defense, grade, fd`） | **设计** | ★ "进场景全量（`InitData`）+ 运行期增量（`UpdateData`）"的两段式属性同步值得参考 | 【已确认】 |
| N4 | `Classes/ShareData.h` → `VerifyPos_Msg` + `CMClient::VerifyPlayerPos/doPlayerPosVerifyMsg` | ★ **存在"服务端下达位置校验、客户端校准"的消息**（Mahatma 完全没有） | **设计** | ★ JSTM 的移动反外挂可参考该形状（但要修 bug：`doPlayerPosVerifyMsg` 循环条件写错，见 §4） | 【已确认】 |
| N5 | `Classes/ShareData.h` → 组队 8 条 | `TeamApply`/`AgreeTeam`/`RefuseTeam`/`TeamMove`/`TeamGotoMap`/`DissolveTeam`/`QuitTeam`/`KickOutteam` + `TeamManage_Msg`/`TeamFight_Msg` | **命令划分** | ★ 组队流程的**消息粒度**可直接对照（见 `task.md`） | 【已确认】 |
| N6 | `Classes/ShareData.h` → `UseMedication_Msg` | **药品使用走独立的 TCP 消息**（不是本地直接生效） | **设计** | 与"药品效果在客户端本地结算"的事实并存 —— 说明它只用来**广播给队友**（见 `task.md`/`battle.md`） | 【已确认】 |
| N7 | `Classes/TCPClient.{h,cpp}` | ★ **传输层职责单一**：`connect`/`send`/`recv` + 虚 `OnRecv`，完全不知道业务 | **分层设计** | ★ ★ 值得 JSTM 对照其分层清晰度（Mahatma 把网络塞在 WinForms Form 里） | 【已确认】 |
| N8 | `Classes/CMClient.{h,cpp}` | ★ **协议分发层**：`OnRecv` 里 `switch(type)` → 22 个 `doXxxMsg`；发送侧 15+ 个 `SendXxxMsg` | **分层设计** | ★ "收 switch 分发 + 发一消息一函数" 的对称形状值得参考；**但**它同时持有全部业务缓存（`m_playerlist`/`m_worldTalkMsgs`/`m_privateTalkMsgs`/`m_applyTeamList`/`m_gotoMapMsgs`）⇒ 职责偏重，JSTM 应把缓存移到领域层 | 【已确认】 |
| N9 | `Classes/public.h:27` | `#define CLOSE_MESSAGE "~#@**close**@#~"`（断线哨兵串） | **反面** | 在无分帧的裸 TCP 上用魔数字符串当断线信号 ⇒ 与真实消息内容可能冲突；JSTM 用连接状态而非哨兵 | 【已确认】 |
| N10 | `Resources/server.cfg` | 服务器地址外置（`serverIp` / `port`） | **做法** | JSTM 已有区服配置 | 【已确认】 |

### 3.3 业务流程（详情见 `task.md` / `battle.md`）

| # | 业务 | 借鉴内容 | 复用形态 | 标注 |
|---|---|---|---|---|
| B1 | **登录/注册/建号/选角** | 完整时序 + 三条校验（用户名非空、密码非空、**两次密码一致** `SurePasswd`）+ 角色上限 3 | 流程 | 【已确认】 |
| B2 | **任务系统** | ★ `Task{n}.tsk`（8 字段：`name/schedulewho/glodreward/expreward/index/curschedule/allschedule/type`）+ `Task{n}.tk` / `EndTask.tk` / `NoEndTask.tk`（**任务三态对话**）+ NPC 任务状态宏（`NS_HTASK`/`NS_WSTASK`/`NS_STASK`） | **数据结构 + 状态机** | 【已确认】 |
| B3 | **背包/物品** | ★ `Thing/*.att` 的 4 字段物品属性（`buyglod/sellglod/addblood/addmana`）+ `*.dec`（名 + 描述）+ 堆叠（`thingnums` 读改写） | **数据结构** | 【已确认】 |
| B4 | **装备** | ★ 5 槽位（头/武器/首饰/衣服/鞋）+ **精炼 = `grade += 1`** + 穿新卸旧 | **数据结构 + 规则** | 【已确认】 |
| B5 | **技能** | `SkillFactory` 按名字 `if-else` 创建 8 个技能对象；伤害 `(baseAttack + 30×grade) − defense`（下限 1） | **公式 + 反面（无配置表）** | 【已确认】 |
| B6 | **药品** | 战斗内/外使用；多人时用 `UseMedication_Msg` 广播 | 流程 | 【已确认】 |
| B7 | **组队** | 申请/同意/拒绝/移动/切图/解散 全链路 + 玩家状态宏（`P_STATUS_HEADER`/`P_STATUS_MEMBER`） | **流程 + 状态** | 【已确认】 |
| B8 | **聊天** | 世界（`m_worldTalkMsgs` 上限 100）与私聊（按 fd 分组、每会话上限 18）两条本地队列 | **数据结构** | 【已确认】 |
| B9 | **战斗** | 回合制逻辑 + 实时定时器调度；`FightLayer` 的 8 个标志位状态机；战斗失败/逃跑也照发奖 | **反面为主**（权威在客户端） | 【已确认】 |
| B10 | **移动/寻路** | `FindRoad`（A\*）+ `MapInfo`（`map{n}.mp` 网格 + `mapinfo.xxp` 地图表）+ `MoveTo_Msg(less)` | **数据结构** | 【已确认】 |
| B11 | **静态数据外置** | `GameData.xml`（plist，名字即索引）+ `mapinfo.xxp`（地图表）+ `.att/.dec/.tsk/.tk` | **做法** | 【已确认】 |

### 3.4 工程组织

| # | 来源 | 借鉴内容 | 复用形态 | 标注 |
|---|---|---|---|---|
| E1 | `Classes/typelist.h`（19 KB） | 集中前向声明/聚合包含 | 工程手法 | 【已确认】 |
| E2 | `Classes/PreProcess.h` | ★ **单例宏 `GET_SINGLE_OBJECT` / `SINGLE_ATTRIBUTES` / `DEFINE_SINGLE_ATTRIBUTES`（原子 + 双检锁）**、`PROPERTY__REF`（getter 返回 const 引用）、`Inherit(__TYPE__)`、`GettingAndSetting` | 工程手法 | 【已确认】 |
| E3 | `Classes/Commen.h` | UI 宏（`LISTEN_TOUCH`、`ADD_EDIT`、`COMMEN_BTN`、`CONTAIN_POINT`、`ATTACH_OR_DETACH`、`STONE_STATION`、`GO_BACK_*`） | 工程手法 | 【已确认】 |
| E4 | `proj.android/` + `proj.ios_mac/` + `proj.win32/` | 三平台工程并存 | 工程组织 | 【已确认】 |

---

## 四、明确**不要借鉴**清单（反面教训，可指回代码）

| # | 项 | 证据 | 原因 | 标注 |
|---|---|---|---|---|
| X1 | **客户端直连 MySQL 做全部持久化** | `Classes/DBDao.h` + 8 个调用点 | 架构性安全漏洞：客户端可任意改自己的金币/等级/装备；数据库暴露于公网 | 【已确认】 |
| X2 | **数据库凭据硬编码在客户端** | `DBDao.h:107-110` | 已泄露凭据；JSTM 绝不可重现 | 【已确认】 |
| X3 | **无参数化 SQL（字符串拼接）** | `DBDao.h:204` `m_sql += var.first + "='" + var.second + "'"` | SQL 注入 | 【已确认】 |
| X4 | **无事务** | `DBDao` 无任何事务 API | 建号 = INSERT playerinfo + UPDATE player；中途失败即不一致 | 【已确认】 |
| X5 | **存档用 INSERT 而非 UPSERT** | `BackPackManager.cpp:113`、`EquipmentManager.cpp:99`、`SkillManager.cpp:102` | 🔴 每次存档新增全量副本 ⇒ 数据膨胀、数量累加 | 【已确认】 |
| X6 | **全字段 `std::string` + `std::stoi`** | `Model.h` 全部 `GettingAndSetting(std::string, ...)` | 数值类型缺失；`stoi("")` 抛异常 | 【已确认】 |
| X7 | **子表用 `(playername, rolename)` 双字符串做外键**，无 `roleId` | 3 个子表前两列 | 改名即断链、无法索引、无法跨服 | 【已确认】 |
| X8 | **密码明文**，且以 `WHERE playername=? and playerpsw=?` 比对 | `LoginLayer.cpp:149-153` | 拖库即泄露；SQL 里出现明文密码 | 【已确认】 |
| X9 | **协议：结构体内存裸发，无长度前缀、无序列化、无端序处理** | `SendMsg((char*)&msg, sizeof(msg))`；`*((M_Type*)buff)` | 依赖编译器布局；粘包/半包直接错乱 | 【已确认】 |
| X10 | **无心跳、无重连、无发送队列** | `TCPClient.cpp` 全文 | 弱网不可用 | 【已确认】 |
| X11 | **接收线程直接操作 Cocos 场景图** | `CMClient::doInitPlayerPosMsg` → `CurGameScene()->getObjectLayer()->addPlayer(...)` | 跨线程渲染风险 | 【已确认】 |
| X12 | **战斗/伤害/奖励结算全在客户端** | `FightLayer.cpp` 伤害公式与 `addGlod/addExp` | 可任意刷金币经验；`battle.md` 详述 | 【已确认】 |
| X13 | **`doPlayerPosVerifyMsg` 循环条件写错** | `CMClient.cpp:256` `var != m_playerlist.begin()` | 🔴 循环体永不执行 ⇒ 位置校验从未生效 | 【已确认】 |
| X14 | **`removeBackPackThing` 迭代器失效后解引用** | `BackPackManager.cpp:52-53` `erase(it); deleteBackpack(*it);` | use-after-erase（UB） | 【已确认】 |
| X15 | **`DBDao::queryModel` 未 `mysql_free_result`** | `DBDao.h:147-164` | 结果集内存泄漏 | 【已确认】 |
| X16 | **技能"最多 8 个"未实现** | `SkillManager::skillNumbers()` 零调用；`DealLayer::checkBuy` 只挡重复 | 约束只在 README 里，不在代码里 | 【已确认】 |
| X17 | **退队/踢人复用"全员解散"** | `MemberItem.cpp:11` 宏；`M_QuitTeam`/`M_KickOutteam` 已定义未实装 | 功能缺失且语义错位 | 【已确认】 |
| X18 | **无 LICENSE** | 全仓库无 `LICENSE` | **无授权依据** ⇒ 按原则 3 只借鉴设计 | 【已确认】 |
| X19 | `Resources/` 的**全部美术/字体/地图资源**（约 748 张图） | `Resources/**` | 版权与商标风险；**不要用于 JSTM 发行** | 【已确认】 |
| X20 | 第三方二进制（`libmysql.dll` / `mysqlclient.lib` / `libcocos2d*.a` / `*.class`） | `lib/`、`proj.android/bin/` | 受各自许可约束（本次**未读到**其许可文件） | 【已确认】 |

---

## 五、按 JSTM 子系统归口的采纳建议

| JSTM 子系统 | 从 ChivalrousMan 采纳什么 | 形态 | 优先级 |
|---|---|---|---|
| **数据库设计** | ★ ★ D2/D3/D4/D5/D6（5 表 33 字段 + 建号初值配方）+ D1（账号-角色 1:N） | **字段清单 + 数值配方** | **最高** |
| **常量/枚举体系** | ★ ★ D7（千位分段的全局枚举） | 设计 | **最高** |
| 协议设计 | N1/N3/N4（23 命令清单、全量+增量属性同步、位置校验消息） | 思想 | 高 |
| 组队系统 | N5/B7（8 条消息 + `P_STATUS_*`） | 流程 + 结构 | 高 |
| 任务系统 | B2（`.tsk` 8 字段 + 三态对话 + `NS_*` 状态宏） | 数据结构 + 状态机 | 高 |
| 背包/装备/技能 | B3/B4/B5（`.att` 4 字段、5 槽位、精炼=grade+1） | 数据结构 | 高 |
| 分层组织 | N7/N8（传输/协议/实体/持久/Manager 五段式） | 设计 | 高 |
| 静态数据外置 | B11（名字即索引 + 文本表） | 做法 | 中 |
| 聊天系统 | B8（世界/私聊两队列 + 容量上限） | 数据结构 | 中 |
| 移动/寻路 | B10（`map{n}.mp` + `mapinfo.xxp` + `FindRoad`） | 数据结构 | 中 |
| 战斗系统 | B9 —— **只借鉴"状态与流程的拆解"，不借鉴其权威模型**（客户端权威是致命缺陷） | 反面 | 中 |
| 工程手法 | E1/E2/E3（单例宏 / UI 宏 / 类型聚合） | 手法 | 低 |
| **任何代码与美术资源** | ❌ 无 LICENSE ⇒ 不复制代码；美术资源另行取得授权 | — | — |

---

## 六、登记表（JSTM 侧台账模板）

| 来源项目 | 文件路径 | LICENSE | 拟复用内容 | 复用形态 | 是否可复用 | 是否进入 JSTM |
|---|---|---|---|---|---|---|
| ChivalrousMan | `Classes/Model.h`（字段名/表名） | **无** | 5 张表 / 33 字段 | 字段语义 | ⚠ 仅语义 | ❌ 代码不进入；表结构由 JSTM 自行设计 |
| ChivalrousMan | `Classes/PreProcess.h`（宏取值） | **无** | 千位分段枚举 | 取值定义 | ⚠ 仅语义 | ❌ 同上 |
| ChivalrousMan | `Classes/ShareData.h`（命令集合） | **无** | 23 命令 / 22 结构体 | 命令划分 | ⚠ 仅语义 | ❌ 同上 |
| ChivalrousMan | `Resources/**`（美术/配置文本） | **无** | — | — | ❌ | ❌ |

---

## 七、一句话总结

> **ChivalrousMan 无 LICENSE ⇒ 它不是 GPL 那样的"传染源"，但也**没有**给出任何授权；
> 按本项目【原则 3】：可研究、可借鉴设计、不要直接复制代码。**
> 它对本项目的独特价值在于**"业务数据结构与流程的对照基线"**：
> **5 张表 / 33 个字段 / 建号数值配方 / 23 条协议命令 / 千位分段枚举 / 5 槽位装备 / 8 字段任务表 / 两队列聊天 / 组队 8 消息** ——
> 这些都是 JSTM **自行设计时最需要拿来比对的东西**；
> 而它的**权威模型（客户端直连 MySQL、客户端结算伤害与奖励）是必须明确拒绝的反面模式**。
