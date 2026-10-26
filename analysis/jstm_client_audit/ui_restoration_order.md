# 下一阶段客户端界面复原顺序 ui_restoration_order

> **PHASE C0 只读审计派生交付物 ②**
> 生成时间：2026-10-15
> 输入：ui_inventory.json（A/B/C/D 分类与模块）、server_capability_needs.md（各系统服务端状态）、client_server_matrix.json（已实现系统）、system_dependency_graph.md（依赖）、HANDOFF.md（已闭环清单）。
> **只读审计**：本文档不修改任何既有文件，仅给出复原顺序建议。

---

## 1. 排序原则

1. **服务端已具备优先**：【已具备】且客户端模块资源齐备（B 类）的界面优先 —— 复原成本最低、闭环最快。
2. **核心主流程依赖链优先**：登录 → 角色创建/选择 → 主界面 HUD → 场景 → 任务 → 背包 → 装备 → 战斗。
3. **依赖未就绪排后**：用 system_dependency_graph.md 的依赖链排序，被依赖系统先复原。
4. **A 类已实机验证为参照基准**：18 个 A 类界面**无需重做**，仅用于校准新复原界面的布局/交互/数据格式。
5. **服务端【缺失】系统的 B 类界面本轮不排**：待服务端建成后再排期（见 §7 不建议清单）。

---

## 2. A 类参照基准（18 个，无需重做）

> 这些界面已实机验证，作为新复原界面的校准参照。

| ui_name | system_id | system_name |
|---|---|---|
| login panel | SYS_CORE_001 | 登录 |
| role ctrl | SYS_ROLE_001 | 角色属性 |
| backpack ctrl | SYS_ECON_002 | 背包 |
| battle ctrl | SYS_BATTLE_001 | 回合战斗 |
| mission panel | SYS_QUEST_001 | 任务 |
| shop ctrl | SYS_ECON_003 | 商城 |
| skill panel | SYS_GROWTH_001 | 技能 |
| hero ctrl | SYS_FRIEND_001 | 伙伴 |
| friend panel | SYS_SOCIAL_002 | 好友 |
| guild base panel | SYS_SOCIAL_004 | 公会 |
| daily panel | SYS_QUEST_002 | 日常 |
| automate panel | SYS_BATTLE_002 | 挂机 |
| equipforge panel | SYS_EQUIP_002 | 锻造 |
| map view | SYS_MAP_001 | 世界地图 |
| vip ctrl | SYS_ROLE_004 | VIP |
| answer panel | SYS_ACT_007 | 答题 |
| scratcher ctrl | SYS_ACT_005 | 刮刮乐 |
| set panel | SYS_CORE_009 | 设置 |

---

## 3. 分阶段复原队列

### 阶段 1：核心主流程补全（服务端已具备，B 类面板，8 界面）

> 目标：补齐主流程中 A 类未覆盖的支撑面板，使主界面 HUD → 场景 → 交互链路完整。

| # | 界面名称 | system_id | 当前分类 | 服务端状态 | 优先级理由 | 前置依赖 | 建议动作 |
|---|---|---|---|---|---|---|---|
| 1.1 | durable panel（耐久面板） | SYS_CORE_003 | B | 已具备 | 主界面 HUD 耐久提示，核心展示层 | SYS_CORE_001 登录（A 已闭环） | MuMu 实机打开主界面，校准耐久条显示 |
| 1.2 | npc ctrl（NPC 交互控制器） | SYS_CORE_005 | B | 已具备 | 场景 NPC 对话/商店/任务触发入口 | SYS_CORE_005 场景（A map view 已闭环） | 实机走到 NPC 旁，校准对话气泡与交互按钮 |
| 1.3 | scene view（场景视图） | SYS_CORE_005 | B | 已具备 | 场景渲染层，主流程必需 | 同上 | 实机进场景，校准角色/怪物/NPC 站位渲染 |
| 1.4 | warehouse panel（仓库） | SYS_ECON_004 | B | 已具备 | 背包扩展存储，已闭环服务端 | SYS_ECON_002 背包（A 已闭环） | 实机打开仓库，校准格子/分页/存取 |
| 1.5 | mail ctrl（邮件控制器） | SYS_ECON_009 | B | 已具备 | 邮件收发/附件领取，已闭环服务端 | 无（独立） | 实机打开邮件，校准列表/附件领取按钮 |
| 1.6 | nav ctrl（导航控制器） | SYS_MAP_001 | B | 已具备 | 自动寻路导航，主流程辅助 | SYS_CORE_005 场景 | 实机点任务寻路，校准导航箭头 |
| 1.7 | tp menu view（传送菜单） | SYS_MAP_001 | B | 已具备 | 世界地图传送入口 | 同上 | 实机打开传送菜单，校准地图点列表 |
| 1.8 | mission nycollect panel（任务日常收集） | SYS_QUEST_001 | B | 已具备 | 任务面板补充页签 | SYS_QUEST_001 任务（A 已闭环） | 实机打开任务面板页签，校准收集进度显示 |

---

### 阶段 2：角色与成长面板（服务端已具备，B 类面板，10 界面）

> 目标：补齐角色养成相关面板，依赖角色基础数据（SC_10300 系列已闭环）。

| # | 界面名称 | system_id | 当前分类 | 服务端状态 | 优先级理由 | 前置依赖 | 建议动作 |
|---|---|---|---|---|---|---|---|
| 2.1 | role main view（角色主视图） | SYS_ROLE_001 | B | 已具备 | 角色属性面板主体（A 仅有 ctrl） | SYS_CORE_003 角色基础 | 实机打开角色面板，校准属性条/战力数值 |
| 2.2 | role show panel（角色展示） | SYS_ROLE_001 | B | 已具备 | 角色外观/称号展示 | 同上 | 校准装备外观/称号显示 |
| 2.3 | title ctrl（称号控制器） | SYS_ROLE_003 | B | 已具备 | 称号佩戴/切换，已闭环服务端 | 同上 | 实机打开称号面板，校准 175 项称号列表 |
| 2.4 | gradebreak seal panel（等级突破封印） | SYS_ROLE_005 | B | 已具备 | 等级突破玩法，已闭环服务端 | SYS_ROLE_001 | 实机打开突破面板，校准突破进度/奖励 |
| 2.5 | gradebreak reward panel（突破奖励） | SYS_ROLE_005 | B | 已具备 | 突破奖励领取 | 同上 | 校准奖励列表/领取按钮 |
| 2.6 | wing fashion star panel（翅膀星级） | SYS_APPEAR_001 | B | 已具备 | 翅膀养成面板，已闭环服务端 | SYS_CORE_003 | 实机打开翅膀面板，校准星级/属性 |
| 2.7 | footmark ctrl（足迹控制器） | SYS_APPEAR_001 | B | 已具备 | 足迹系统入口 | 同上 | 校准足迹列表/激活状态 |
| 2.8 | horse info panel（坐骑信息） | SYS_APPEAR_002 | B | 已具备 | 坐骑面板，已闭环服务端 | 同上 | 实机打开坐骑面板，校准坐骑状态/技能 |
| 2.9 | beast info panel（灵兽信息） | SYS_APPEAR_003 | B | 已具备 | 灵兽面板，已闭环服务端 | 同上 | 校准灵兽属性/培养按钮 |
| 2.10 | artifact main ui（神器主界面） | SYS_APPEAR_005 | B | 已具备 | 神器面板，已闭环服务端 | 同上 | 校准神器列表/使用中状态 |

---

### 阶段 3：战斗与副本面板（服务端已具备，B 类面板，9 界面）

> 目标：补齐战斗/副本相关面板，依赖战斗链路（CS_20002 已闭环）。

| # | 界面名称 | system_id | 当前分类 | 服务端状态 | 优先级理由 | 前置依赖 | 建议动作 |
|---|---|---|---|---|---|---|---|
| 3.1 | boss ctrl（BOSS 控制器） | SYS_BATTLE_005 | B | 已具备 | BOSS 面板，已闭环服务端 | SYS_BATTLE_001 战斗（A 已闭环） | 实机打开 BOSS 面板，校准 BOSS 列表/刷新状态 |
| 3.2 | fire main ui（副本主界面） | SYS_DUNGEON_001 | B | 已具备 | 副本入口面板，已闭环服务端 | 同上 | 实机打开副本列表，校准 34 副本条目 |
| 3.3 | fb info ui（副本信息） | SYS_DUNGEON_001 | B | 已具备 | 副本详情/奖励预览 | 同上 | 校准副本奖励/进入条件 |
| 3.4 | fb team ui（副本组队） | SYS_DUNGEON_001 | B | 已具备 | 副本组队匹配 | SYS_MAP_002 组队 | 校准队伍匹配界面 |
| 3.5 | failure panel（失败面板） | SYS_DUNGEON_001 | B | 已具备 | 副本失败结算 | SYS_BATTLE_001 | 校准失败提示/复活按钮 |
| 3.6 | arena panel（竞技场） | SYS_COMM_002 | B | 已具备 | 竞技场面板，已闭环服务端 | SYS_BATTLE_001 | 实机打开竞技场，校准对手列表/挑战按钮 |
| 3.7 | peakwar ctrl（巅峰战控制器） | SYS_COMM_003 | B | 已具备 | 巅峰战入口，已闭环服务端 | 同上 | 校准巅峰战状态/赛程显示 |
| 3.8 | race ctrl（竞速控制器） | SYS_COMM_004 | B | 已具备 | 魂师大赛竞速，已闭环服务端 | 同上 | 校准竞速报名/赛程 |
| 3.9 | team screen panel（组队屏幕） | SYS_MAP_002 | B | 已具备 | 队伍信息展示，已闭环服务端 | SYS_CORE_005 场景 | 实机组队后校准队员列表/站位 |

---

### 阶段 4：社交与活动面板（服务端已具备，B 类面板，10 界面）

> 目标：补齐社交/日常活动面板，依赖聊天/好友链路已闭环。

| # | 界面名称 | system_id | 当前分类 | 服务端状态 | 优先级理由 | 前置依赖 | 建议动作 |
|---|---|---|---|---|---|---|---|
| 4.1 | chat panel（聊天主面板） | SYS_SOCIAL_001 | B | 已具备 | 聊天频道，已闭环服务端 | SYS_CORE_006 网络层 | 实机打开聊天，校准频道切换/消息列表 |
| 4.2 | chat private panel（私聊面板） | SYS_SOCIAL_001 | B | 已具备 | 私聊窗口 | SYS_SOCIAL_002 好友 | 校准私聊消息收发 |
| 4.3 | contact ctrl（联系人控制器） | SYS_SOCIAL_002 | B | 已具备 | 好友列表（A 已有 friend panel） | 同上 | 校准好友列表/在线状态 |
| 4.4 | daily calendar panel（日常日历） | SYS_QUEST_002 | B | 已具备 | 日常活跃日历，已闭环服务端 | SYS_QUEST_001 任务 | 实机打开日常面板，校准活跃度/奖励档位 |
| 4.5 | achieve panel（成就面板） | SYS_QUEST_003 | B | 已具备 | 成就系统，已闭环服务端（342 条） | SYS_CORE_003 | 校准成就分组/进度条 |
| 4.6 | dailysign panel（签到面板） | SYS_ACT_001 | B | 已具备 | 30 天签到，已闭环服务端 | 无 | 实机打开签到，校准 30 天奖励显示 |
| 4.7 | invest panel（投资面板） | SYS_ACT_003 | B | 已具备 | 投资计划，已闭环服务端 | SYS_ECON_001 货币 | 校准投资返利档位 |
| 4.8 | wedding ring panel（婚戒面板） | SYS_SOCIAL_005 | B | 已具备 | 结婚系统，已闭环服务端 | SYS_SOCIAL_002 好友 | 校准婚戒进阶/属性 |
| 4.9 | sworn main panel（结拜主面板） | SYS_SOCIAL_006 | B | 已具备 | 结拜系统，已闭环服务端 | 同上 | 校准结拜成员/技能 |
| 4.10 | cash shop panel（现金商城） | SYS_ECON_003 | B | 已具备 | 商城子页签（A 已有 shop ctrl） | SYS_ECON_001 货币 | 校准商品列表/价格显示 |

---

### 阶段 5：服务端【部分】系统的面板展示层（可先做 UI，交互待补，8 界面）

> 目标：服务端仅有面板读取或 stub 的系统，可先复原展示层，交互逻辑待服务端补全后再接。

| # | 界面名称 | system_id | 当前分类 | 服务端状态 | 优先级理由 | 前置依赖 | 建议动作 |
|---|---|---|---|---|---|---|---|
| 5.1 | halo ctrl（光环控制器） | SYS_APPEAR_010 | B | 部分 | 光环穿戴已接，升级未实现；先复原展示层 | SYS_APPEAR_001 翅膀 | 校准光环列表/穿戴状态；升级按钮置灰 |
| 5.2 | auction main ui（拍卖主界面） | SYS_ECON_008 | B | 部分 | 一口价已接，竞价未实现；先复原列表展示 | SYS_ECON_002 背包 | 校准拍卖列表/一口价按钮；竞价按钮置灰 |
| 5.3 | market buy more panel（市场购买） | SYS_ECON_005 | B | 已具备 | 交易市场，已闭环服务端 | 同上 | 校准市场商品列表 |
| 5.4 | blackmarketeer main panel（黑市） | SYS_ECON_006 | B | 部分 | 仅 18909 通用 stub；先复原展示层 | 同上 | 校准黑市商品列表；刷新按钮置灰 |
| 5.5 | endless main panel（无尽主面板） | SYS_DUNGEON_002 | B | 部分 | 共用 dungeon_progress；先复原层数展示 | SYS_DUNGEON_001 副本 | 校准无尽层数/奖励预览 |
| 5.6 | demontower ctrl（恶魔塔控制器） | SYS_DUNGEON_003 | B | 部分 | 13035/13038 已接；先复原塔层列表 | 同上 | 校准恶魔塔层数/奖励 |
| 5.7 | linshi rank panel（临时排行榜） | SYS_COMM_001 | B | 部分 | 派生榜（本服唯一角色第 1）；先复原展示层 | SYS_ROLE_001 | 校准排行榜名次/数值显示 |
| 5.8 | jewelvip base panel（宝石 VIP 基础） | SYS_ROLE_004 | B | 部分 | VIP 等级逻辑未完整；先复原展示层 | SYS_ECON_010 充值 | 校准 VIP 等级/特权列表 |

---

## 4. 阶段汇总

| 阶段 | 主题 | 界面数 | 服务端状态 |
|---|---|---|---|
| 阶段 1 | 核心主流程补全 | 8 | 全部已具备 |
| 阶段 2 | 角色与成长面板 | 10 | 全部已具备 |
| 阶段 3 | 战斗与副本面板 | 9 | 全部已具备 |
| 阶段 4 | 社交与活动面板 | 10 | 全部已具备 |
| 阶段 5 | 服务端【部分】展示层 | 8 | 部分（UI 先做，交互置灰） |
| **合计** | | **45** | |

---

## 5. 复原节奏建议

1. **每阶段完成后跑 miniloop 145/145 回归**，确认未破坏既有闭环。
2. **每复原一个界面，在 MuMu 12 实机截图存档**（`analysis/runtime_evidence/shots/`），并在 ui_inventory.json 中将该条目从 B 升级为 A。
3. **阶段 1-4 为服务端已具备系统**，复原后应可完整闭环（面板打开 → 数据正确 → 交互可操作）。
4. **阶段 5 为服务端部分系统**，复原后仅展示层闭环，交互按钮需根据服务端补全进度分批接通。

---

## 6. 依赖链说明（来自 system_dependency_graph.md）

```
核心链：SYS_CORE_001(登录) → SYS_CORE_002(建角) → SYS_CORE_004(进游戏)
      → SYS_CORE_003(主界面HUD) → SYS_CORE_005(场景) → SYS_QUEST_001(任务)
      → SYS_ECON_002(背包) → SYS_EQUIP_001(装备) → SYS_BATTLE_001(战斗)
```

- 阶段 1-2 沿此链展开。
- 战斗链（SYS_BATTLE_001）依赖 Skill/Buff/Partner/Equipment，故阶段 3 在阶段 2（成长面板）之后。
- 社交链（SYS_SOCIAL_002 好友）依赖 Inventory/Battle/Skill，故阶段 4 在阶段 2-3 之后。

---

## 7. 不建议本轮复原清单

### 7.1 C 类（27 条，仅图标证据，模块缺失）

> 全部推迟到对应服务端系统建成后再考虑。完整清单见 `unknown_inventory.md §2.2`。
> 主要包括：运营活动系列（xfphb/czphb/hfsc/flyUp_gift/jiangchi/charge_double/recruit/hefu/guess/lucky_turntable/godwarscene/fc/menpai/kuafu_guildwars/actionrank/invest_sec/reward/kuafu_xianmo/yunyingduihuan/flower/luckbox/zhufuqiang/xingyunfanpai/miling/julong/target/duobao）。

### 7.2 D 类（8 条，1.4.11 已移除）

> 这些界面在 1.4.11 客户端已被移除/重命名，**不建议复原**。完整清单见 `unknown_inventory.md §2.3`。

### 7.3 服务端【缺失】系统的 B 类面板（共 ~120 条）

> 服务端无 handler、无权威状态、无持久化，本轮不排。包括：

| system_id | 系统名 | B 类面板数 | 原因 |
|---|---|---|---|
| SYS_ACT_006 | 节日/运营活动 | 48 | 服务端缺失，活动框架未建 |
| SYS_COMM_006 | 采矿 | 13 | 服务端缺失 |
| SYS_BATTLE_004 | 帝国战/神魔战 | 11 | 服务端缺失 |
| SYS_HIDDEN_004 | 星魂 | 11 | 服务端部分（复用 role_runes，独立逻辑未取证） |
| SYS_SOCIAL_006 | 结拜 | 15 | 注：结拜服务端已具备，已排入阶段 4；此处排除 |
| SYS_DUNGEON_005 | 跨服副本 | 3 | 服务端缺失 |
| SYS_QUEST_005 | 新手引导 | 3 | 服务端缺失 |
| SYS_ACT_012 | 回归 | 3 | 服务端缺失 |
| SYS_COMM_005 | 跨服 | 2 | 服务端缺失（单体进程） |
| SYS_CORE_008 | 红点 | 3 | 服务端缺失（协议未建） |
| SYS_CORE_009 | UI 状态同步 | 4 | 服务端缺失（协议未建） |
| SYS_UNKNOWN_002 | 封测/活动运营 | 2 | 服务端缺失 |
| SYS_BATTLE_003 | 战报 | 1 | 服务端缺失 |
| SYS_GROWTH_005 | 士气 | 1 | 服务端缺失 |
| SYS_HIDDEN_002 | 修罗 | 1 | 服务端缺失 |
| SYS_HIDDEN_003 | 百官 | 1 | 服务端缺失 |
| SYS_HIDDEN_005 | 神位 | 2 | 服务端缺失 |
| SYS_COMM_009 | 押镖 | 2 | 服务端缺失 |
| SYS_FRIEND_006 | 伙伴武器 | 1 | evidence_tier=UNKNOWN（喂养消耗未取证） |

> 注：SYS_SOCIAL_006 结拜服务端已具备，已排入阶段 4；上表仅列真正【缺失】的系统。

---

## 8. 自检记录

- [x] 排序基于 ui_inventory.json B 类聚合（`_raw/_b_grouped.json`，76 系统 338 面板）。
- [x] 服务端状态交叉引用 server_capability_needs.md（已具备/部分/缺失三档）。
- [x] 依赖链引用 system_dependency_graph.md。
- [x] A 类 18 界面列为参照基准，未排入复原队列。
- [x] 每阶段 8-10 界面（阶段 1=8、阶段 2=10、阶段 3=9、阶段 4=10、阶段 5=8）。
- [x] 每条含：界面名称、system_id、当前分类、服务端状态、优先级理由、前置依赖、建议动作。
- [x] 不建议清单覆盖：C 类 27、D 类 8、服务端缺失 B 类 ~120。
- [x] 未修改任何既有文件；本文件与 `_raw/_b_grouped.json` / `_raw/_group_b.py` 为新建派生。
