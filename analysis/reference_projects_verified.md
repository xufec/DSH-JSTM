# 参考项目可借鉴能力与许可状态 · 核实报告（PHASE 0 全量审计子任务）

> 生成日期：2026-10-02
> 性质：**只读审计**。本轮仅用 `python zipfile` 列目录清单 + 在内存中读取个别许可文件头；**未解压任何 zip 到 `server/` 或项目根目录，未复制任何参考项目代码到项目内**。
> 目的：独立核实 `analysis/server_reference/` 既有结论，并标注证据等级与差异点。

---

## 〇、纪律红线（重申，最高优先级）

1. **JSTM（绝世唐门）1.4.9 APK 是唯一事实标准。** 与参考项目冲突时 **APK > 参考项目**。
2. **参考项目只作架构/设计参考**。以下内容**一律不得**从参考项目搬入 JSTM，必须以 JSTM APK（`assets/src/config/*.luac`、`all_proto.luac`、真机 `tcp.log`）为准：
   - 通信**协议/命令号/字段编排**
   - **数值**（属性公式、成长曲线、掉落、经济汇率）
   - **任务**定义与流程模型
   - **装备/技能/怪物/伙伴**数据
   - **属性体系**与**战斗规则**（JSTM 1.4.9 为独立回合制战斗场景，已裁决）
3. 参考项目的**代码文件**不得进入 `server/`；即使是 MIT 框架，也只借鉴**结构与思想**，不照抄实现。
4. 证据分级：【已验证】=本轮 zipfile/文件头实测；【已确认】=既有逐文件审计实测结论被本轮复核一致；【待验证】=本轮未直接取证。

---

## 一、计数更正：实际发现 **5 个**参考项目（非用户提示的"四份"）

`cankao/` 实测存在 **5 个 zip**，本报告全部列出并逐项目核实：

| 文件 | 大小 | 对应既有分析子目录 |
|---|---|---|
| `Survive-master.zip` | 207.7 MB | `survive/` |
| `kongkongxiyou-master.zip`（空空西游） | 331.8 MB | `kongkongxiyou/` |
| `CXEngine-master.zip`（原罪西游引擎 = YZXY，用户已确认同一项目） | 14.8 MB | `yzxy/` |
| `MahatmaComeBack-master.zip`（大圣归来） | 18.2 MB | `mahatma/` |
| `ChivalrousMan-master.zip`（侠客行） | 51.2 MB | `chivalrousman/` |

---

## 二、逐项目核实

### 2.1 Survive（`Survive-master.zip`）

- **技术栈**：Lua 手游服务端，基于自研 `distrilua` 框架；高频模块以预编译 C 扩展提供（顶层 `aoi.so` / `astar.so` / `cjson.so`）；另带 PHP 后台（`php/`，68 个 php 文件）。
- **zip 顶层结构（实测 depth-1）**：`client/` `common/` `doc/` `gameserver/` `gateserver/` `groupserver/` `notiserver/` `php/` `lua/` `netcmd/` + `Makefile` `daemon.lua` `distrilua` `setconfig.lua` `robotclient.lua` `aoi.so` `astar.so` `cjson.so` `README.md`。
- **有无服务端**：有，且是多进程服务组 —— `gateserver`（前端连接，可多台）/ `groupserver`（中心，单台）/ `gameserver`（战斗+地图，单线程、每服务加载 1~N 场景）/ `notiserver`。
- **能给 JSTM 借鉴什么（仅设计层）**：
  - **服务组拆分思想**（gate 接入 / group 全局 / game 场景战斗 三进程解耦）—— JSTM 现为单进程，此为演进方向。
  - **AOI 设计**（均匀网格、新旧视野集合差、双向 enter/leave 回调）—— 仅可读思想。
  - **寻路设计**（A* 8 邻域 + Bresenham 直线裁剪）—— 仅可读思想。
  - **buff/skill/bufffunction 的逻辑组织**、`groupserver` 承载全局系统（成就、每日签到、商城/背包/装备等跨场景逻辑）的分层。
  - PHP **Web 后台/GM** 的组织方式。
- **绝不能直接采用**：AOI/寻路的 C 实现（GPLv3，见下）；其协议命令号、属性表（`attr.lua`）、技能/buff 数值、场景地图数值 —— 全部以 JSTM APK 为准。
- **许可结论**：🔴 **核心模块明确 copyleft**。本轮只读文件头实测：`common/aoi.h`、`common/astar.h`、`common/wordfilter.h` 三个文件头均内嵌 **GPLv3 全文声明**（`Copyright (C) 2012 huangweilook@21cn.com`）。无顶层 LICENSE 文件。
  - ⇒ AOI/寻路/敏感词三块**连"翻译成 Python"都有传染风险**，必须完全自写，只借鉴算法思想。
- **证据等级**：服务组布局【已验证】（本轮 depth-1 清单）；GPLv3 文件头【已验证】（本轮读文件头原文）。

---

### 2.2 kongkongxiyou / 空空西游（`kongkongxiyou-master.zip`）

- **技术栈**：**Node.js + Pomelo 分布式框架**（服务端在 `lordofpomelo/game-server/`），客户端为 Cocos2d-JS（`cocosjs/`）。js 文件 4271 个；含 `pomelo-admin-web/`（ExtJS 管理台）。
- **zip 顶层结构（实测 depth-1）**：`cocosjs/` `lordofpomelo/` `pomelo-admin-web/` `exceldata/` `ccsbuilder/` `characterRes/` `publicResource/` `plistbuild/` + 多个 `*.command` 启停脚本 + `README.md`。
- **服务端位置（实测）**：`lordofpomelo/game-server/app/servers/area/handler/{boss,chat,equip,federate,fight,guild,market,player,resource,shop,skill,task,team}Handler.js` + `area/remote/*`（跨进程 RPC）+ `auth/` `connector/` `chat/`；库结构 `game-server/config/schema/Pomelo.sql`。
- **能给 JSTM 借鉴什么（仅设计层）**：
  - **按业务域切 handler**（task/skill/shop/team/boss…）+ `remote` 做跨进程 RPC —— 直接对应 JSTM 把"单文件 if 长链 CMD 分发"按域拆 handler 的重构方向。
  - **connector 网关**分层（连接/角色入口与场景业务分离）。
  - **场景内 area 服务器 + domain 模型**分离；任务 `TaskState` 多态状态机（与 JSTM `mission_status 0/1/2/3` 同构，既有 `task_matrix.md` 已论证）。
  - Excel→JSON 配置表管线（`exceldata/`）的思路。
- **绝不能直接采用**：其 handler 里的业务数值/任务链/商店商品/掉落；`exceldata` 内任何数值表；协议路由串（pomelo route 字符串）。这些以 JSTM APK 为准。
- **许可结论（★ 本轮与既有结论有差异，见第四节）**：
  - 本轮实测 `lordofpomelo/LICENSE` 与 `lordofpomelo/pomelo/LICENSE` 文件头 = **The MIT License，Copyright (c) 2012-2014 Netease, Inc. and other pomelo contributors**。即 **pomelo 框架与 lordofpomelo 服务端骨架本身是 MIT（宽松许可）**。
  - 但 **kongkongxiyou 项目自身（根目录）无 LICENSE**；其在 lordofpomelo 之上叠加的游戏逻辑、`exceldata` 数值、客户端美术资源**无授权依据**。
  - `pomelo-admin-web/` 基于 **ExtJS**（历史版本为 GPL/双授权）—— 即任务书背景提到的"ExtJS 传染风险"，仅影响该管理台，不影响游戏服核心。
  - ⇒ **结论细化**：借鉴 pomelo/lordofpomelo 的**服务端分层与 handler/remote 结构**在 MIT 下是安全的（保留署名即可）；但 **kongkongxiyou 自己的游戏内容（数值/任务/装备/配置）仍不可复制**。
- **证据等级**：Pomelo/Node.js 栈与服务端目录【已验证】（本轮 depth-1 + app_servers 清单）；MIT 框架许可【已验证】（本轮读 LICENSE 文件头原文）；项目内容无许可【已确认】。

---

### 2.3 CXEngine = YZXY / 原罪西游（`CXEngine-master.zip`）

- **技术栈**：**C++ 引擎 + Lua 脚本**（`cxluax` 为 C++/Lua 绑定层；`CMakeLists.txt` 构建）。C++ 54 / Lua 67；另有 `scripts/{client,server,combat,share,generator,examples}` 布局。
- **zip 顶层结构（实测 depth-1）**：`client/` `server/` `scripts/` `common/` `cxluax/` `externals/` `internals/` `assets/` `cmake/` `.vscode/` + `CMakeLists.txt` `launcher.sh/bat` `readme.md`。
- **有无服务端**：有脚本层服务端 `scripts/server/` + 独立 `scripts/combat/` + `scripts/share/`（共享定义），外加 `server/src/` C++ 层。
- **能给 JSTM 借鉴什么（仅设计层）**：
  - **`scripts/share`（客户端/服务端共享定义）+ 独立 `combat` 战斗层** 的分层思想。
  - `addon/` 按功能插件化（bag/props/quest/battle/hud）的模块组织。
  - 战斗/技能/魔法的**框架骨架**（既有 `yzxy/battle.md`、`yzxy/impl/` 已抽取）。
- **绝不能直接采用**：其战斗数值、技能/魔法公式、怪物属性、`addon/quest` 的任务类型定义、协议字段 —— 以 JSTM APK 为准（JSTM 为回合制战斗，不可照搬其实时战斗状态机）。
- **许可结论**：无 LICENSE 文件（本轮实测 `license_like` 为空）⇒ **未声明许可，默认保留全部权利，只可借鉴设计**。
- **证据等级**：C++/Lua 引擎栈与分层【已验证】（本轮 depth-1 + CMakeLists/cxluax 线索）；无许可【已验证】（本轮清单）。"参考价值有限"的既有判断本轮**维持**：它是引擎/战斗框架参考，而非完整服务端运维参考。

---

### 2.4 MahatmaComeBack / 大圣归来（`MahatmaComeBack-master.zip`）

- **技术栈**：客户端 Cocos2d-x C++（`Classes/`、`Resources/`、`proj.android/`、`proj.win32/`）；**服务端为 C#/.NET**（本轮实测 `Server/游戏服务器.sln` + `Server/游戏服务器/游戏服务器.csproj`，8 个 `.cs` 文件）+ `Server/gametable.sql` 建库脚本。
- **zip 顶层结构（实测 depth-1）**：`Classes/` `Resources/` `Server/` `proj.android/` `proj.win32/` + `LICENSE` `ReadMe.md` `CMakeLists.txt` + 若干 `buildTo*`.bat。
- **有无服务端**：有（`Server/游戏服务器`，约 15 个文件；既有 R2 已逐条目更正）。
- **能给 JSTM 借鉴什么（仅设计层）**：
  - **客户端/服务端物理分离**的仓库组织。
  - **用 `.sql` 文件集中定义业务库表结构**（`gametable.sql`）的持久化建模思路 —— 只看表结构组织方式，不导其文本。
- **绝不能直接采用**：🔴 GPL-3.0 传染 —— **其任何代码、`.sql` 文本、美术资源都不得进入 JSTM**（既有 `mahatma/reuse_candidates.md` 已界定"连 gametable.sql 也不得导入建库脚本"）；数值/属性/流程一律以 JSTM APK 为准。
- **许可结论**：🔴 **GNU GPL v3**。本轮读 `LICENSE` 文件头原文确证：`GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007, Copyright (C) 2007 Free Software Foundation`。
  - ⇒ 强 copyleft：一旦并入，JSTM 整体须以 GPL-3.0 发布。**代码不得进入 JSTM**，仅可读设计思路。
- **证据等级**：GPLv3【已验证】（本轮读 LICENSE 原文）；C#/.NET 服务端【已验证】（本轮 sln/csproj 清单）；表结构借鉴定位【已确认】。

---

### 2.5 ChivalrousMan / 侠客行（`ChivalrousMan-master.zip`）

- **技术栈**：**仅 Cocos2d-x C++ 客户端**（`Classes/` 自研约 191 文件：92 .cpp + 99 .h；`.java`/`.class` 均为 cocos2d-x 框架文件）。`proj.win32/ChivalrousMan.sln`。
- **zip 顶层结构（实测 depth-1）**：`Classes/` `Resources/` `cocosstudio/` `include/` `lib/` `proj.android/` `proj.ios_mac/` `proj.win32/` + `config.json` `README.md` 等 6 个顶层文件。**无 `client/`、无 `server/` 目录**。
- **有无服务端**：**本 zip 内无服务端目录**（服务端在作者另开的 `gitee.com/lsylovews/CM-Server`，不在包内）。⚠ 但该"客户端"用 **libmysql 直连公网 MySQL**（`Classes/DBDao.h` 硬编码 IP/账号/明文口令/库名），据此反推出一套 **5 表 / 33 字段**的 MMORPG 业务库结构 —— 这是其唯一"数据层"价值。
- **能给 JSTM 借鉴什么（仅设计层）**：
  - **传统 MMORPG 业务流程的客户端侧参考**（任务/装备/技能的交互流程组织）。
  - 作为**业务库字段语义的对照基线**（仅字段含义/表组织思想，不复制其连接串与库结构文本）。
- **绝不能直接采用**：🔴 **其"任务系统"权威模型不可借鉴** —— 既有 `chivalrousman/task.md` 已确证：任务**不走 TCP、不落库，客户端每 15 秒随机生成**（`TaskSystem.cpp`），是错误示范；其协议/数值/装备/技能/怪物（62 个 `.att`）以 JSTM APK 为准。⚠ 其泄露的 MySQL 凭据**严禁**在 JSTM 中复用或连接。
- **许可结论**：无 LICENSE（本轮实测为空）⇒ 未声明许可，只可借鉴设计/字段语义，不复制代码与美术资源。
- **证据等级**：无服务端目录【已验证】（本轮 depth-1 清单）；无许可【已验证】；任务随机生成模型【已确认】（既有逐文件审计）。

---

## 三、汇总对照表

| 项目 | 技术栈 | 有无服务端（包内） | 可借鉴（仅设计层） | 绝不能采用 | 许可结论 | 证据等级 |
|---|---|---|---|---|---|---|
| **Survive** | Lua(distrilua) + C 扩展(aoi/astar/cjson .so) + PHP 后台 | 有：gate/group/game/notise 多进程 | gate/group/game 服务组拆分、单线程多场景、AOI/寻路算法思想、buff/skill 逻辑组织、PHP GM 后台 | AOI/astar/wordfilter 的 C 实现（GPLv3）；协议/属性/技能/场景数值 | 🔴 无顶层 LICENSE，但 aoi.h/astar.h/wordfilter.h **内嵌 GPLv3**（已读文件头确证） | 布局【已验证】GPL头【已验证】 |
| **kongkongxiyou** | Node.js + **Pomelo**(lordofpomelo) + Cocos2d-JS | 有：area/auth/connector/chat 多服务器 | 按业务域切 handler + remote 跨服 RPC、connector 网关、area+domain 分离、任务状态机、Excel→JSON 配置管线 | handler 业务数值/任务链/商店/掉落、exceldata 数值表、pomelo route 串 | 🟡 **pomelo/lordofpomelo 框架 = MIT（已读确证）**；kongkongxiyou 自有游戏内容/美术无 LICENSE；admin-web 为 ExtJS（传染风险，仅管理台） | 栈【已验证】MIT头【已验证】 |
| **CXEngine/YZXY** | C++(CMake,cxluax) + Lua 脚本 | 有（脚本层 server/combat/share + server/src C++） | share 共享定义 + 独立 combat 层、addon 插件化、战斗框架骨架 | 实时战斗状态机、技能/魔法公式、怪物属性、quest 任务类型、协议字段 | ⚠ 无 LICENSE（未声明），只借鉴设计 | 栈【已验证】无许可【已验证】 |
| **MahatmaComeBack** | 客户端 Cocos2d-x C++；**服务端 C#/.NET**(.sln/.csproj) + gametable.sql | 有：`Server/游戏服务器` | 客户端/服务端物理分离、`.sql` 集中建表的持久化建模思路 | 🔴 全部代码/.sql 文本/美术（GPL-3.0 传染）；数值/属性/流程 | 🔴 **GNU GPL v3**（已读 LICENSE 原文确证） | GPLv3【已验证】C#服【已验证】 |
| **ChivalrousMan** | 仅 Cocos2d-x C++ 客户端 | **无**（服务端在包外另仓） | 传统 MMORPG 客户端业务流程组织、业务库字段语义对照基线 | 🔴 客户端随机生成任务模型（错误示范）；泄露的 MySQL 凭据严禁复用；协议/数值/装备/技能/怪物 | ⚠ 无 LICENSE（未声明），只借鉴设计/字段语义 | 无服务端【已验证】任务模型【已确认】 |

---

## 四、与既有 `analysis/server_reference` 结论的差异点（本轮核实登记）

1. **★ kongkongxiyou 许可被既有结论低估（重要差异）**
   - 既有 `license_audit.md` §5 与 `FINAL_SERVER_ARCHITECTURE.md` §1.1 称 kongkongxiyou「仅 cocos2d-x 自带 licenses，**无项目自身 LICENSE**」。
   - 本轮实测：zip 内存在 `lordofpomelo/LICENSE` 与 `lordofpomelo/pomelo/LICENSE`，文件头均为 **MIT（Copyright Netease pomelo contributors）**。
   - **更正/细化**：**pomelo 框架与 lordofpomelo 服务端骨架本身是 MIT 宽松许可**。因此借鉴其"handler/remote 按域拆分、connector 网关、area+domain"的服务端**结构**在 MIT 下是安全的（保留署名即可），证据强度高于"纯思想参考"。
   - **但不改变红线**：kongkongxiyou 在此框架之上叠加的**自有游戏内容**（`exceldata` 数值、任务链、客户端美术）**仍无授权**，不可复制；`pomelo-admin-web` 的 **ExtJS** 是另一个独立的传染风险面（仅管理台）。⇒ 建议后续在 `license_audit.md` 补登此条。

2. **MahatmaComeBack 服务端语言细化**：既有文档记录了"Server/游戏服务器 15 文件 + gametable.sql"，本轮进一步确证其为 **C#/.NET 工程**（`游戏服务器.sln` + `.csproj` + 8 个 `.cs`），而非脚本服务端。不影响 GPL-3.0 结论，仅补全技术栈。

3. **其余结论全部一致、被本轮复核确认**：
   - Survive 服务组（gate/group/game/notise）+ C 扩展模块；其 aoi/astar/wordfilter 内嵌 GPLv3 —— 本轮读文件头**独立确证**。
   - Mahatma 根目录 LICENSE = GPL v3 —— 本轮读文件头**独立确证**。
   - ChivalrousMan 无服务端目录、无 LICENSE、客户端 libmysql 直连 MySQL —— 本轮 depth-1 清单**确认**（无 `server/`、无 `client/`）。
   - CXEngine 无 LICENSE、C++/Lua 引擎分层 —— 本轮确认。

---

## 五、最终许可裁决（汇总）

| 允许 | 禁止 |
|---|---|
| ✅ 阅读全部 5 个项目源码与结构 | ❌ 复制 MahatmaComeBack 任何代码/.sql/资源（GPL-3.0 传染） |
| ✅ 借鉴架构/算法/分层**思想**（全部项目） | ❌ 复制 Survive 的 aoi/astar/wordfilter C 实现（GPLv3，含"翻译重写"） |
| ✅ 在 MIT 条款（保留署名）下参考 pomelo/lordofpomelo 的服务端结构 | ❌ 复制其余项目无许可代码进 `server/` |
| ✅ 以 JSTM APK 为准自行实现一切协议/数值 | ❌ 采用任何参考项目的协议/数值/任务/装备/技能/怪物/属性/战斗规则 |
| ✅ 引用公开 README 说明设计来源 | ❌ 连接/复用 ChivalrousMan 泄露的公网 MySQL 凭据 |

> **一句话总结**：5 个参考项目**没有一个可直接复用代码**；其中 pomelo/lordofpomelo 的服务端骨架因 MIT 而可安全参考其结构，Survive 的 AOI/寻路与 Mahatma 的全部代码因 GPL copyleft 而只能读思想。**JSTM 唯一权威数据源是 1.4.9 APK，任何参考项目的协议/数值/规则都不得搬入。**
