# 五项目 × JSTM 映射矩阵（R3）

> 依据附件任务书第七/十七节。评分：0=不适合 1=仅概念 2=部分参考 3=高度参考 4=非常适合 5=与 JSTM 结构高度匹配

> ⚠ 评分仅为**工程适配度**，**不能替代 APK 协议证据**。

## 一、综合评分矩阵

| 模块 | Survive | YZXY/CXEngine | 大圣归来 | 侠客行 | 空空西游 | **JSTM 最终方案** |
|---|---|---|---|---|---|---|
| **网络层** | 5 | 3 | 2 | 1 | 4 | 保留 JSTM 自定义 TCP（已验证）；层次思想参考空空西游 connector |
| **登录** | 4 | 3 | 3 | 3 | 4 | JSTM 已实现，不动 |
| **角色** | 4 | 4 | 3 | 3 | 4 | JSTM 已实现；数据组织参考 Survive gameplayer.lua |
| **场景** | 4 | 3 | 2 | 1 | 5 | JSTM 已实现基础；参考空空西游 area/domain 分离 |
| **AOI** | 4 | 3 | 1 | 0 | 4 | ★ **缺**；参考 Survive（C 模块）自行实现 |
| **寻路** | 4 | 3 | 3 | 1 | 4 | ★ **缺**；参考 Survive astar 自行实现 |
| **任务** | 3 | **❓未取证** | 3 | 4 ⚠ | **5** ✅ | JSTM 已实现（4 态 `mission_status` + 13 列表 + 线性链 + `mission_chain_max`）。★ **参考项已更正（R5）**：首选 **空空西游 `app/domain/task/*.js`**（`TaskState` 4 态与 JSTM `mission_status 0/1/2/3` **1:1 同构**、`TaskType` 3 类、怪侧上报进度、下线批量落库），**侠客行**为第二个独立 4 态样本（+ 11 个任务模板数值 + 三态对话）。⚠ **YZXY 由 4 降为「❓未取证」**：其 `addon/quest.lua` **从未被任何审计读过**。⚠ 侠客行的 4 分只代表"四态 + 三类型"的形状，其权威模型（客户端每 15 秒随机生成 / 不落库 / 不走协议 / 本地发奖）不可借鉴。详见 `task_matrix.md` |
| **战斗** | 4 | **5** | 2 | 3 | 4 | ★ **JSTM 是回合制**（用户 2026-09-18 裁决）⇒ CXEngine 回合 FSM **结构可借鉴**。★ **R6 更正**：原写「**推进权必须在服务端（客户端 `CS_20014` ACK 后才推）**」**已作废** —— 真机 `CS_20011`/`CS_20014` **从未发出**，**无 ACK 可依赖**，JSTM 由**服务端自定节拍（2.5 s 自续期）**。CXEngine FSM 仍不可照搬，但理由是 **5 条字段级理由**（阵法/波次、单位每回合重推、线格式、四套独有子系统、安全模型），见 §三 与 `battle_matrix.md`。现流程已通，**数值 TEST_ONLY** |
| **EXP/等级** | 4 | 4 | 3 | 3 | 4 | JSTM 已实现 |
| **背包** | 4 | 4 | 3 | 3 | 4 | JSTM 已实现（含仓库/跨囊） |
| **装备** | 4 | 4 | 3 | 3 | 4 | JSTM 已实现（按部位定槽） |
| **技能** | 4 | 4 | 3 | 3 | 4 | ★ **缺**；参考 Survive skill.lua |
| **伙伴** | 2 | 2 | 1 | 1 | 3 | JSTM 仅列表；属性/技能未做 |
| **副本** | 4 | 3 | 2 | 2 | 4 | ★ **缺** |
| **数据库** | 3 | 3 | ~~4~~ **1** | **4** | 4 | 保留 SQLite；★ 表结构参考 **ChivalrousMan**（5 表 33 字段）—— Mahatma 只有 1 张 11 字段表 |
| ****LICENSE 可用性**** | 0（无；`aoi.h/astar.h` 内嵌 GPLv3） | 0（无） | 0（**GPL-3.0**） | 0（无） | 0（无） | ★ **5 个项目全部不可复制代码**，但**原因不同**：仅 **大圣归来是 GPL-3.0 强 copyleft**；其余 4 个是**无许可依据（默认保留全部权利）**。详见 `license_audit.md` |

## 二、协议矩阵（聚焦真机实际使用的 128 个 CMD）

> 任务书最终决定原则：**以 APK 协议为准**。
> 故本矩阵**只列真机发过的命令**，而非 1652 个全部协议。

| CMD | 方向 | JSTM 实现 | 字段（来自 cmd_resolve） | 参考项目对应 | 最终方案 |
|---|---|---|---|---|---|
| 1110 | CS+SC | ✅ | CS:CSAccountLogin_1110 SC:SCAccountLogin_1110 | 工程推断 | 保留（已验证） |
| 1199 | CS+SC | ✅ | CS:CSheartbeast_1199 SC:SCheartbeast_1199 | 工程推断 | 保留（已验证） |
| 10001 | CS | ✅ | CS:CSFirstPack_10001 SC: | Survive 登录 | 保留（已验证） |
| 10103 | CS+SC | ✅ | CS:CSRoleReLogin_10103 SC:SCRoleReLogin_10103 | 工程推断 | 保留（已验证） |
| 10204 | CS+SC | ✅ | CS:CS_10204 SC:SC_10204 | 工程推断 | 保留（已验证） |
| 10300 | CS | ✅ | CS:CSRoleInit_10300 SC: | 均有 | 保留（已验证） |
| 10301 | CS+SC | ✅ | CS:CS_10301 SC:SC_10301 | 均有 | 保留（已验证） |
| 10302 | CS+SC | ✅ | CS:CS_10302 SC:SC_10302 | 均有 | 保留（已验证） |
| 10303 | CS+SC | ✅ | CS:CS_10303 SC:SC_10303 | 均有 | 保留（已验证） |
| 10331 | CS+SC | ✅ | CS:CS_10331 SC:SC_10331 | 均有 | 保留（已验证） |
| 10341 | CS+SC | ❌ | CS:CS_10341 SC:SC_10341 | 均有 | ★待实现 |
| 10401 | CS+SC | ✅ | CS:CSHeroBag_10401 SC:SCHeroBag_10401 | 空空西游 area | 保留（已验证） |
| 10402 | CS+SC | ✅ | CS:CSHeroInfo_10402 SC:SCHeroInfo_10402 | 空空西游 area | 保留（已验证） |
| 10403 | CS+SC | ✅ | CS:CSHeroAll_10403 SC:SCHeroAll_10403 | 空空西游 area | 保留（已验证） |
| 10404 | CS+SC | ✅ | CS:CSHeroBase_10404 SC:SCHeroBase_10404 | 空空西游 area | 保留（已验证） |
| 10502 | CS+SC | ✅ | CS:CSRoleBag_10502 SC:SCRoleBag_10502 | CXEngine addon/bag | 保留（已验证） |
| 10505 | CS+SC | ✅ | CS:CSDblclickItem_10505 SC:SCDblclickItem_10505 | CXEngine addon/bag | 保留（已验证） |
| 10509 | CS+SC | ✅ | CS:CS_10509 SC:SC_10509 | CXEngine addon/bag | 保留（已验证） |
| 10511 | CS+SC | ✅ | CS:CS_10511 SC:SC_10511 | CXEngine addon/bag | 保留（已验证） |
| 10512 | CS+SC | ✅ | CS:CS_10512 SC:SC_10512 | CXEngine addon/bag | 保留（已验证） |
| 10514 | CS+SC | ❌ | CS:CS_10514 SC:SC_10514 | CXEngine addon/bag | ★待实现 |
| 10527 | CS+SC | ✅ | CS:CS_10527 SC:SC_10527 | CXEngine addon/bag | 保留（已验证） |
| 10528 | CS+SC | ✅ | CS:CS_10528 SC:SC_10528 | CXEngine addon/bag | 保留（已验证） |
| 10532 | CS+SC | ❌ | CS:CS_10532 SC:SC_10532 | CXEngine addon/bag | ★待实现 |
| 10534 | CS+SC | ✅ | CS:CS_10534 SC:SC_10534 | CXEngine addon/bag | 保留（已验证） |
| 10552 | CS+SC | ✅ | CS:CS_10552 SC:SC_10552 | CXEngine addon/bag | 保留（已验证） |
| 10554 | CS+SC | ✅ | CS:CS_10554 SC:SC_10554 | CXEngine addon/bag | 保留（已验证） |
| 10560 | CS+SC | ❌ | CS:CS_10560 SC:SC_10560 | CXEngine addon/bag | ★待实现 |
| 10570 | CS+SC | ✅ | CS:CS_10570 SC:SC_10570 | CXEngine addon/bag | 保留（已验证） |
| 10589 | CS+SC | ✅ | CS:CS_10589 SC:SC_10589 | CXEngine addon/bag | 保留（已验证） |
| 10621 | CS+SC | ✅ | CS:CS_10621 SC:SC_10621 | 工程推断 | 保留（已验证） |
| 10640 | CS+SC | ❌ | CS:CS_10640 SC:SC_10640 | 工程推断 | ★待实现 |
| 10650 | CS+SC | ✅ | CS:CS_10650 SC:SC_10650 | 工程推断 | 保留（已验证） |
| 10800 | CS+SC | ❌ | CS:CS_10800 SC:SC_10800 | 工程推断 | ★待实现 |
| 10921 | CS+SC | ❌ | CS:CS_10921 SC:SC_10921 | Survive map/maplogic | ★待实现 |
| 10922 | CS+SC | ✅ | CS:CS_10922 SC:SC_10922 | Survive map/maplogic | 保留（已验证） |
| 10923 | CS+SC | ✅ | CS:CS_10923 SC:SC_10923 | Survive map/maplogic | 保留（已验证） |
| 10924 | CS+SC | ❌ | CS:CS_10924 SC:SC_10924 | Survive map/maplogic | ★待实现 |
| 10932 | CS+SC | ❌ | CS:CS_10932 SC:SC_10932 | Survive map/maplogic | ★待实现 |
| 10999 | CS | ❌ | CS:CS_10999 SC: | Survive map/maplogic | 无需应答 |
| 11200 | CS+SC | ✅ | CS:CS_11200 SC:SC_11200 | 空空西游 equipHandler | 保留（已验证） |
| 11206 | CS+SC | ❌ | CS:CS_11206 SC:SC_11206 | 空空西游 equipHandler | ★待实现 |
| 11215 | CS+SC | ❌ | CS:CS_11215 SC:SC_11215 | 空空西游 equipHandler | ★待实现 |
| 11216 | CS+SC | ❌ | CS:CS_11216 SC:SC_11216 | 空空西游 equipHandler | ★待实现 |
| 11300 | CS+SC | ❌ | CS:CS_11300 SC:SC_11300 | 工程推断 | ★待实现 |
| 11301 | CS+SC | ✅ | CS:CS_11301 SC:SC_11301 | 工程推断 | 保留（已验证） |
| 11600 | CS+SC | ❌ | CS:CS_11600 SC:SC_11600 | 工程推断 | ★待实现 |
| 11700 | CS+SC | ✅ | CS:CS_11700 SC:SC_11700 | 无对应 | 保留（已验证） |
| 11701 | CS+SC | ✅ | CS:CS_11701 SC:SC_11701 | 无对应 | 保留（已验证） |
| 11702 | CS+SC | ✅ | CS:CS_11702 SC:SC_11702 | 无对应 | 保留（已验证） |
| 11703 | CS+SC | ✅ | CS:CS_11703 SC:SC_11703 | 无对应 | 保留（已验证） |
| 11704 | CS+SC | ✅ | CS:CS_11704 SC:SC_11704 | 无对应 | 保留（已验证） |
| 11710 | CS+SC | ✅ | CS:CS_11710 SC:SC_11710 | 无对应 | 保留（已验证） |
| 11712 | CS+SC | ✅ | CS:CS_11712 SC:SC_11712 | 无对应 | 保留（已验证） |
| 12400 | CS+SC | ✅ | CS:CS_12400 SC:SC_12400 | CXEngine addon/quest | 保留（已验证） |
| 12403 | CS+SC | ✅ | CS:CS_12403 SC:SC_12403 | CXEngine addon/quest | 保留（已验证） |
| 12409 | CS+SC | ✅ | CS:CS_12409 SC:SC_12409 | CXEngine addon/quest | 保留（已验证） |
| 12801 | CS+SC | ✅ | CS:CS_12801 SC:SC_12801 | 空空西游 shopHandler | 保留（已验证） |
| 12803 | CS+SC | ✅ | CS:CS_12803 SC:SC_12803 | 空空西游 shopHandler | 保留（已验证） |
| 12805 | CS+SC | ✅ | CS:CS_12805 SC:SC_12805 | 空空西游 shopHandler | 保留（已验证） |
| 12823 | CS+SC | ❌ | CS:CS_12823 SC:SC_12823 | 空空西游 shopHandler | ★待实现 |
| 12831 | CS+SC | ✅ | CS:CS_12831 SC:SC_12831 | 空空西游 shopHandler | 保留（已验证） |
| 12832 | CS+SC | ❌ | CS:CS_12832 SC:SC_12832 | 空空西游 shopHandler | ★待实现 |
| 12836 | CS+SC | ❌ | CS:CS_12836 SC:SC_12836 | 空空西游 shopHandler | ★待实现 |
| 12853 | CS+SC | ❌ | CS:CS_12853 SC:SC_12853 | 空空西游 shopHandler | ★待实现 |
| 13042 | CS+SC | ❌ | CS:CS_13042 SC:SC_13042 | 工程推断 | ★待实现 |
| 13200 | CS+SC | ❌ | CS:CS_13200 SC:SC_13200 | 工程推断 | ★待实现 |
| 13300 | CS+SC | ❌ | CS:CS_13300 SC:SC_13300 | 工程推断 | ★待实现 |
| 13340 | CS+SC | ✅ | CS:CS_13340 SC:SC_13340 | 工程推断 | 保留（已验证） |
| 13369 | CS+SC | ✅ | CS:CS_13369 SC:SC_13369 | 工程推断 | 保留（已验证） |
| 13401 | CS+SC | ❌ | CS:CS_13401 SC:SC_13401 | 工程推断 | ★待实现 |
| 13403 | CS+SC | ❌ | CS:CS_13403 SC:SC_13403 | 工程推断 | ★待实现 |
| 13569 | CS+SC | ❌ | CS:CS_13569 SC:SC_13569 | 工程推断 | ★待实现 |
| 13579 | CS+SC | ❌ | CS:CS_13579 SC:SC_13579 | 工程推断 | ★待实现 |
| 13580 | CS+SC | ❌ | CS:CS_13580 SC:SC_13580 | 工程推断 | ★待实现 |
| 13701 | CS+SC | ❌ | CS:CS_13701 SC:SC_13701 | 工程推断 | ★待实现 |
| 13702 | CS+SC | ❌ | CS:CS_13702 SC:SC_13702 | 工程推断 | ★待实现 |
| 13703 | CS+SC | ❌ | CS:CS_13703 SC:SC_13703 | 工程推断 | ★待实现 |
| 13704 | CS+SC | ❌ | CS:CS_13704 SC:SC_13704 | 工程推断 | ★待实现 |
| 13741 | CS+SC | ❌ | CS:CS_13741 SC:SC_13741 | 工程推断 | ★待实现 |
| 13771 | CS+SC | ❌ | CS:CS_13771 SC:SC_13771 | 工程推断 | ★待实现 |
| 13772 | CS+SC | ❌ | CS:CS_13772 SC:SC_13772 | 工程推断 | ★待实现 |
| 13781 | CS+SC | ❌ | CS:CS_13781 SC:SC_13781 | 工程推断 | ★待实现 |
| 13806 | CS+SC | ❌ | CS:CS_13806 SC:SC_13806 | 工程推断 | ★待实现 |
| 13841 | CS+SC | ❌ | CS:CS_13841 SC:SC_13841 | 工程推断 | ★待实现 |
| 13901 | CS+SC | ❌ | CS:CS_13901 SC:SC_13901 | 工程推断 | ★待实现 |
| 14000 | CS+SC | ❌ | CS:CS_14000 SC:SC_14000 | 工程推断 | ★待实现 |
| 14009 | CS+SC | ✅ | CS:CS_14009 SC:SC_14009 | 工程推断 | 保留（已验证） |
| 14100 | CS+SC | ✅ | CS:CS_14100 SC:SC_14100 | 工程推断 | 保留（已验证） |
| 14101 | CS+SC | ❌ | CS:CS_14101 SC:SC_14101 | 工程推断 | ★待实现 |
| 14600 | CS+SC | ✅ | CS:CS_14600 SC:SC_14600 | 无对应 | 保留（已验证） |
| 14901 | CS+SC | ✅ | CS:CS_14901 SC:SC_14901 | 工程推断 | 保留（已验证） |
| 15203 | CS+SC | ✅ | CS:CS_15203 SC:SC_15203 | 工程推断 | 保留（已验证） |
| 15405 | CS+SC | ❌ | CS:CS_15405 SC:SC_15405 | 工程推断 | ★待实现 |
| 15501 | CS+SC | ❌ | CS:CS_15501 SC:SC_15501 | 工程推断 | ★待实现 |
| 15700 | CS+SC | ❌ | CS:CS_15700 SC:SC_15700 | 工程推断 | ★待实现 |
| 15801 | CS+SC | ❌ | CS:CS_15801 SC:SC_15801 | 工程推断 | ★待实现 |
| 16400 | CS+SC | ❌ | CS:CS_16400 SC:SC_16400 | 工程推断 | ★待实现 |
| 16500 | CS+SC | ❌ | CS:CS_16500 SC:SC_16500 | 工程推断 | ★待实现 |
| 16603 | CS+SC | ❌ | CS:CS_16603 SC:SC_16603 | 工程推断 | ★待实现 |
| 16605 | CS+SC | ❌ | CS:CS_16605 SC:SC_16605 | 工程推断 | ★待实现 |
| 16701 | CS+SC | ❌ | CS:CS_16701 SC:SC_16701 | 工程推断 | ★待实现 |
| 16704 | CS+SC | ❌ | CS:CS_16704 SC:SC_16704 | 工程推断 | ★待实现 |
| 16706 | CS+SC | ❌ | CS:CS_16706 SC:SC_16706 | 工程推断 | ★待实现 |
| 16900 | CS+SC | ❌ | CS:CS_16900 SC:SC_16900 | 工程推断 | ★待实现 |
| 16903 | CS+SC | ❌ | CS:CS_16903 SC:SC_16903 | 工程推断 | ★待实现 |
| 17100 | CS+SC | ❌ | CS:CS_17100 SC:SC_17100 | 工程推断 | ★待实现 |
| 17200 | CS+SC | ❌ | CS:CS_17200 SC:SC_17200 | 工程推断 | ★待实现 |
| 17600 | CS+SC | ❌ | CS:CS_17600 SC:SC_17600 | 工程推断 | ★待实现 |
| 17703 | CS+SC | ❌ | CS:CS_17703 SC:SC_17703 | 工程推断 | ★待实现 |
| 17800 | CS+SC | ❌ | CS:CS_17800 SC:SC_17800 | 工程推断 | ★待实现 |
| 17801 | CS+SC | ❌ | CS:CS_17801 SC:SC_17801 | 工程推断 | ★待实现 |
| 18803 | CS+SC | ❌ | CS:CS_18803 SC:SC_18803 | 工程推断 | ★待实现 |
| 18900 | CS+SC | ❌ | CS:CS_18900 SC:SC_18900 | 工程推断 | ★待实现 |
| 19400 | CS+SC | ❌ | CS:CS_19400 SC:SC_19400 | 工程推断 | ★待实现 |
| 19406 | CS+SC | ❌ | CS:CS_19406 SC:SC_19406 | 工程推断 | ★待实现 |
| 19600 | CS+SC | ❌ | CS:CS_19600 SC:SC_19600 | 工程推断 | ★待实现 |
| 20002 | CS+SC | ✅ | CS:CS_20002 SC:SC_20002 | 工程推断 | 保留（已验证） |
| 20014 | CS | ✅ | CS:CS_20014 SC: | 工程推断 | 保留（已验证） |
| 20021 | CS | ❌ | CS:CS_20021 SC: | 工程推断 | 无需应答 |
| 20100 | CS+SC | ❌ | CS:CS_20100 SC:SC_20100 | 工程推断 | ★待实现 |
| 20500 | CS+SC | ❌ | CS:CS_20500 SC:SC_20500 | 工程推断 | ★待实现 |
| 20501 | CS+SC | ❌ | CS:CS_20501 SC:SC_20501 | 工程推断 | ★待实现 |
| 20504 | CS+SC | ❌ | CS:CS_20504 SC:SC_20504 | 工程推断 | ★待实现 |
| 20800 | CS+SC | ❌ | CS:CS_20800 SC:SC_20800 | 工程推断 | ★待实现 |
| 21306 | CS+SC | ❌ | CS:CS_21306 SC:SC_21306 | 工程推断 | ★待实现 |
| 21312 | CS+SC | ❌ | CS:CS_21312 SC:SC_21312 | 工程推断 | ★待实现 |
| 30715 | CS+SC | ❌ | CS:CS_30715 SC:SC_30715 | 工程推断 | ★待实现 |

**⚠ 说明**：“参考项目对应”列是**工程推断**（按功能段推），
**不是**从参考项目里读出来的事实 —— 它们各自有自己的协议，**不可直接对应**。

---

## 三、★★ 前提裁决（用户 2026-09-18 确认）

> **JSTM 是回合制战斗。**

**取证依据**：

| 证据 | 内容 |
|---|---|
| `analysis/1.4.9/battle/battle_flow.md` §一 | 「1.4.9 使用「独立回合制战斗场景」」 |
| `analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1（**真机订正，权威**） | 真机 `tcp.log` 无 `cmd=20011` / `cmd=20014`；客户端收到 `SC_20020` 后主动发 `CS_20021` |
| `protocol_index.md` | `20000~20099` 段 **25 条** CMD |

**⇒ 故以前写的「JSTM 是动作/实时 ⇒ 不能借鉴回合制状态机」已**作废**。**

> ### ⚠️ **R6 更正：原「ACK 节流」结论不成立（本节第一版有错，已订正）**
>
> **第一版写的是**：JSTM「服务端推 `SC_20012/20013` → 客户端播完发 `CS_20014` 回执 → 服务端推进」的 **ACK 节流模型**，因此「两者回合节奏所有权相反」。
> **该表述依据错误**：它引自 `battle_chain_verified.md`，而那份文档描述的**是我们自己 `mock_server.py` 的实现**
> （`行 2445 if cmd == 20014:` —— **我们自己把 20014 当成了推进条件**），**不是真实客户端行为**。
>
> **订正后的正确表述**：
> - JSTM 真机客户端**同样不给"我播完了"的回执**（`CS_20011`/`CS_20014` 从未发出）⇒ **JSTM 也必须由服务端自定节拍**（现实现：`SC_20010` 之后 **2.5 秒/回合、自续期**）；
> - **CXEngine 与 JSTM 在"服务端不等客户端"这一点上其实是相似的**（CXEngine：客户端自己推；JSTM：服务端自己推）⇒ **「所有权相反」不成立**；
> - **「照搬会丢掉 `CS_20014` 节流」这一理由作废**（**没有节流可丢**）。
> - **「JSTM 是回合制」这一判定不受影响**（不依赖 `20014`）。
>
> **⇒ CXEngine 回合 FSM 仍「不可照搬」，但真正理由是 5 条字段级理由**：①JSTM 有阵法/回合波次而 `BattleMT:Serialize()` 只有 `{id,team_type,pos_id}`；②JSTM 每回合全量重推单位状态而 CXEngine **无重推机制、buff 完全不上线**；③线格式不同（`[u32BE len][u16BE cmd][二进制]` vs `[LE][LE][JSON]`）；④JSTM 另有观战/录像/自动战斗/客户端演算校验四套子系统；⑤安全模型与内容不可复用。
> 详见 `comparison/battle_matrix.md` §三。

**修正后的真正约束：可借鉴的是**机制**，不是**状态机**本身**

| | CXEngine / YZXY | **JSTM 1.4.9** |
|---|---|---|
| 回合推进 | **客户端本地 `NextTurn()`** | **服务端自定节拍**（2.5 s 自续期） |
| 客户端回执 | ❌ 无 | ❌ **同样无**（`CS_20011`/`CS_20014` 从未发出） |
| ⇒ 关系 | **两者都是"服务端不等客户端"** ⇒ 原"所有权相反"**不成立** | — |
| 照搬后果 | — | **不是"丢节流"，而是①丢字段（阵法/波次/单位重推/Cd/怒气）②丢子系统（观战/录像/自动战斗）③丢了服务端的节拍控制**（CXEngine 让客户端推回合） |

**⇒ 可借鉴（8 条，全部为机制）：按速度降序定出手顺序 / 先快照收件人再结算 / 服务端摇随机结果下发 / 目标失效自动换目标 + 封禁校验 / buff 的"表 + 按 id 脚本回调 + 回合统一结算"骨架 / 侠客行的双档超时托管 / 空空西游的仇恨表 / 空空西游 `areaKind` 策略模式。**
**⇒ 不可照搬：客户端推回合、buff 不上线、`BattleMT` 双向引用无保护。**

---

## 四、R2 更正与取证说明（2026-09-18，主审计员按逐条目实测回填）

| # | 位置 | 原值 | 更正为 | 依据（可复核） |
|---|---|---|---|---|
| 1 | 本文档「LICENSE 可用性」行 | 「★ 全部不可复制（**GPL-3.0 传染**）」 | **仅大圣归来是 GPL-3.0 强 copyleft**；其余 4 个为「无许可依据（未声明 = 默认保留全部权利）」，另 Survive 的 `aoi.h`/`astar.h`/`wordfilter.h` **文件头内嵌 GPLv3** | `license_audit.md` §一/§1.5 |
| 2 | 本文档「任务」行（侠客行 4 分） | 无注 | 加注：**该 4 分只代表"四态状态机 + 三种类型"的形状**；其任务是客户端每 15 秒随机生成、**不落库 / 不走协议 / 本地发奖** ⇒ 权威模型不可借鉴 | `chivalrousman/task.md` 附录 D；`TaskSystem.cpp:35/52-63/101-102` |
| 3 | 本文档「数据库」行 | 已改（`~~4~~ **1**` / 表结构参考 ChivalrousMan 5 表 33 字段） | **维持**，并确认字段计数正确：`player 3 + playerinfo 15 + skillinfo 4 + equipmentinfo 5 + backpack 6 = 33` | `chivalrousman/database.md` §2 |
| 4 | 各根级文档的项目文件数 | Mahatma「164 文件」/「`Server/游戏服务器`(17)」；ChivalrousMan「1539 文件」；`license_audit.md` 写其顶层为 `client/` | **136 文件**（164 条目）；**15**（`Server/` 合计 19）；**1411 文件**（1539 条目）；**无 `client/` 目录** | `zipfile` 逐条目实测，见 `README.md` §6.1 |
| **5** | 本文档「任务」行 + `FINAL_SERVER_ARCHITECTURE.md` §四「任务 参考谁」 | 「任务 → **CXEngine `addon/quest`** 的目标类型」 | ①**YZXY 任务由 4 分降为「❓未取证」** —— `scripts/client/addon/quest.lua` **从未被读过**（`yzxy/architecture.md:214`、`yzxy/lua_server.md:422` 均记录"未读/仅片段"）；②**参考项改为空空西游 `app/domain/task/*.js`**（`TaskState` 4 态与 JSTM `mission_status 0/1/2/3` **1:1 同构**，已读）+ 侠客行（第二个独立 4 态样本）；③**维度更正**：参考项目的 `TaskType`（3 类）对应 JSTM 的 **`progress` 计算方式**，**不是** `MissionType`（28 类业务分类）| `comparison/task_matrix.md` §三/§四/§八；`analysis/1.4.9/task/task_data_model.md` §三 |
| **6** | `FINAL_SERVER_ARCHITECTURE.md` / 本文档「任务」行的 kongkongxiyou 评分 | 4 | **5**（唯一"已读 + 同构 + 服务端权威 + 下线批量落库"四项全中的任务参考） | `task_matrix.md` §五.1 |
| **7** | 本文档 §三 + §一「战斗」行 + `R1_SUPPLEMENT.md` §二 + `FINAL_SERVER_ARCHITECTURE.md` 共 **9 处** | 「JSTM 有 **`CS_20014` ACK 节流**」「回合节奏**所有权相反**」「照搬会**丢掉 ACK 节流**」 | ★ **全部作废** —— 真机 `tcp.log` **无 `cmd=20011` / `cmd=20014`**，客户端收到 `SC_20020` 后只发 `CS_20021`。原结论引自 `battle_chain_verified.md`，**而那份文档描述的是我们自己的 `mock_server.py` 实现**（`行 2445 if cmd == 20014:`）。⇒ JSTM **必须由服务端自定节拍**；「所有权相反」**不成立**（两者都是"服务端不等客户端"）；不可移植的真正理由是 **5 条字段级理由** | `analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1（真机订正）；`yzxy/battle.md:523-548`、`yzxy/architecture.md:28-43`、`yzxy/reuse_candidates.md:327-332` |
| **8** | `FINAL_SERVER_ARCHITECTURE.md` §〇 取证依据 | 引 `battle_chain_verified.md` 为「✅ **决定性结果**」 | **降级为「我们自己 mock 的实现记录」**（非真机取证）；真机取证以 `battle_protocol_matrix.md` §3.0/§3.1 为准 | `yzxy/architecture.md:28-35` |
| **9** | 全库对 `jstm_1.4.9/battle_protocol.md` 的引用 | 视为"战斗协议" | ⚠ 其覆盖的 `13000~13099`（98 条）**实为副本/爬塔/章节/成就**（`dung_bid`/`CengList`/`floor`/`chengjiu`）；**真实战斗在 `20000~20099`（25 条）** | `battle_matrix.md` §2.1 |

**★ 本矩阵的"评分"是工程适配度判断，不是事实断言；**上表 1~6 是事实更正**，可作为后续引用的口径。**
**★ 逐文件一手证据位置**：`survive/`（10 篇）、`yzxy/`（7 篇）、`kongkongxiyou/`（7 篇）、`chivalrousman/`（5 篇）、`mahatma/`（5 篇）、`comparison/`（3 篇）。
