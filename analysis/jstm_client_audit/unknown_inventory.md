# 未知/未确认内容清单 unknown_inventory

> **PHASE C0 只读审计派生交付物 ①**
> 生成时间：2026-10-15
> 证据等级五档：CONFIRMED > VERIFIED > STRONG_INFERENCE > INFERENCE > UNKNOWN
> 本文件由 `_raw/_aggregate_unknown.py` 从既有 8 个主交付物 JSON 聚合生成，**未修改任何既有文件**。
> 每条记录标注：条目名称 / 所属交付物与 system_id / 当前证据状态 / 已知证据（来源文件）/ 缺失什么 / 建议动作。

---

## 0. 总览统计

| 类别 | 数量 | 主要来源交付物 |
|---|---|---|
| 系统级 present_in UNKNOWN（1.3.0） | 20 | systems_master.json |
| 系统级 present_in UNKNOWN（1.4.9） | 10 | systems_master.json |
| 系统级 present_in UNKNOWN（1.4.11） | 10 | systems_master.json |
| 系统级 confidence != CONFIRMED | 75 | systems_master.json |
| 协议级 fields.json 两向无映射补录 token | 55（跨 7 系统） | protocol_inventory.json / systems_master.json |
| 协议级方向不一致（record vs systems_master） | 10 | protocol_inventory.json `_meta.systems_master_direction_mismatches` |
| 界面级 B 类未运行验证 | 338 | ui_inventory.json |
| 界面级 C 类仅图标证据 | 27 | ui_inventory.json |
| 界面级 D 类 1.4.11 已移除 | 8 | ui_inventory.json |
| 数据级未确认 | 17 | data_inventory.json |
| 协议级含 unresolved | 759 | protocol_inventory.json |
| 协议级无字段（no_fields） | 73 | protocol_inventory.json |
| 协议级 INFERENCE 补录 | 55 | protocol_inventory.json |
| 矩阵级 evidence_tier=UNKNOWN | 9 | client_server_matrix.json |
| 矩阵级 evidence_tier=INFERENCE | 17 | client_server_matrix.json |
| 版本矩阵 UNKNOWN 单元格 | 8 | version_diff_matrix.json |
| 参考能力表 UNKNOWN 格 | 4 | reference_capability_table.json |
| 服务端能力【缺失】系统 | 35 | server_capability_needs.md |
| 服务端能力【部分】系统 | 29 | server_capability_needs.md |
| 全局待办（真服标定类） | 9 项 | HANDOFF.md §六 |

**条目总数（去重后逐条记录）：见下文各节累加；约 200+ 条独立待取证项。**

---

## 1. 系统级（来源：systems_master.json）

### 1.1 present_in 版本存在性 UNKNOWN

#### 1.3.0 扫描中判 UNKNOWN（20 系统）
> 判定口径：`lua_modules/config_files/protocol-chunk` basename 在 1.3.0 apk_scan 的 lua_set/mod_set/cfg_set/chunk_set 中**无任何候选可判定**（来源：systems_master.json `_meta.present_in_rule`）。

| system_id | 系统名 | 缺失什么 | 建议动作 |
|---|---|---|---|
| SYS_FRIEND_005 | Partner Fetter 羁绊 | 1.3.0 是否存在该系统无证据 | 解包 1.3.0 extracted/ 后按 config_partner_fetter basename 复核 |
| SYS_APPEAR_008 | Vehicle/Chair 座驾 | 1.3.0 无 role_chair 候选 | 1.3.0 extracted/config/ 全量 grep chair |
| SYS_DUNGEON_002 | Endless Dungeon 无尽/深渊 | 1.3.0 无独立无尽模块候选 | 1.3.0 解包目录树核对 config_dungeon_tower |
| SYS_DUNGEON_004 | Mystic Realm 秘境 | 1.3.0 无 mijing 候选 | 1.3.0 extracted 全量 grep mijing |
| SYS_ACT_005 | Scratch Card 刮刮乐 | 1.3.0 无 scratch 候选 | 1.3.0 解包 grep scratch/刮刮乐 |
| SYS_ACT_012 | Return/Back Flow 回归 | 1.3.0 无回归候选 | 1.3.0 grep return/backflow |
| SYS_BACK_001 | Server Backend/DB | 1.3.0 为客户端 APK，服务端表本不在其中（口径性 UNKNOWN） | 标记为"不适用"，从 UNKNOWN 计数中剔除需人工复核 |
| SYS_BACK_002 | Cross-server backend 跨服后台 | 同上，客户端 APK 不含跨服后台 | 同上，口径性 UNKNOWN |
| SYS_HIDDEN_002 | XiuLuo 修罗 | 1.3.0 无 xiuluo_data 候选 | 1.3.0 grep xiuluo |
| SYS_HIDDEN_003 | Chief 会长/百官 | 1.3.0 无候选 | 1.3.0 grep chief/baiguan |
| SYS_HIDDEN_007 | Balloon 气球活动 | 1.3.0 无 holiday_balloon 候选 | 1.3.0 grep balloon |
| SYS_UNKNOWN_003 | Insight 顿悟 | 1.3.0 无 roles.insight_status 候选 | 1.3.0 roles schema 复核 |
| SYS_EQUIP_005 | Equip Refine 装备洗练 | 1.3.0 无专属 config/module/protocol | 1.3.0 grep refine/xilian |
| SYS_EQUIP_006 | Gem/Socket 宝石 | 1.3.0 镶嵌协议未取证 | 1.3.0 反编译镶嵌 CS 命令 |
| SYS_GROWTH_006 | Soul Bone 魂骨 | 1.3.0 无 soulbone 候选 | 1.3.0 grep soulbone/hungu |
| SYS_GROWTH_007 | Augment/Amplify 增幅 | 1.3.0 无 amplification 候选 | 1.3.0 grep amplification |
| SYS_CORE_008 | Red Dot/Badge 红点 | 1.3.0 无红点专属 config/module | 1.3.0 grep redpoint/badge |
| SYS_CORE_009 | UI State Sync | 1.3.0 无 UI 状态同步帧候选 | 1.3.0 反编译 UI sync 帧 |
| SYS_ROLE_007 | Combat Power 战力 | 1.3.0 战力系数表未在 1.3.0 定位 | 1.3.0 提取 _attr_data.json 对照 |
| SYS_FRIEND_006 | Partner Training 伙伴培养消耗 | 1.3.0 喂养消耗真值未取证 | 1.3.0 实机喂养一次取证 |

#### 1.4.9 与 1.4.11 判 UNKNOWN（各 10 系统，两版相同）
> 来源：systems_master.json `present_in_1_4_9` / `present_in_1_4_11`。这 10 个系统在 1.4.9 与 1.4.11 均无候选可判定：

```
SYS_BACK_001, SYS_BACK_002, SYS_EQUIP_005, SYS_EQUIP_006,
SYS_GROWTH_006, SYS_GROWTH_007, SYS_CORE_008, SYS_CORE_009,
SYS_ROLE_007, SYS_FRIEND_006
```

- **已知证据**：apk_scan_1_4_9.json / apk_scan_1_4_11.json 的 lua_set/mod_set/cfg_set/chunk_set 均无 basename 命中。
- **缺失什么**：这些系统要么是服务端侧模块（SYS_BACK_*、SYS_ROLE_007 战力推导），要么是客户端入口未取证（SYS_EQUIP_005/006、SYS_GROWTH_006/007、SYS_CORE_008/009、SYS_FRIEND_006）。
- **建议动作**：
  - SYS_BACK_* 为口径性 UNKNOWN（客户端 APK 本不含服务端后台），建议在 systems_master 标注"不适用客户端版本扫描"。
  - 其余 8 项需做 1.4.11 luac 反编译入口取证（grep refine/socket/soulbone/amplification/redpoint/ui_sync/partner_feed）。

### 1.2 current_project_status=UNKNOWN

- **结果**：0 条（124 系统全部已归档到 implemented / partial / unimplemented）。
- **来源**：systems_master.json `current_project_status` 字段全量扫描。

### 1.3 confidence != CONFIRMED（75 系统）

> 来源：systems_master.json `confidence` 字段。这些系统证据等级低于 CONFIRMED（多为 VERIFIED / STRONG_INFERENCE / INFERENCE）。
> 完整清单见 `_raw/_aggregated_unknown.json → systems_master.evidence_NOT_CONFIRMED`（75 条）。
> 典型条目（节选）：

| system_id | 系统名 | confidence | 缺口 |
|---|---|---|---|
| SYS_GROWTH_005 | Morale 士气 | STRONG_INFERENCE | 权威士气状态+协议未建 |
| SYS_FRIEND_005 | Partner Fetter 羁绊 | STRONG_INFERENCE | 仅 config_partner_fetter，无 DB |
| SYS_DUNGEON_005 | Shadow/Palace dungeon | STRONG_INFERENCE | config_dungeon_gods/smjz 仅配置 |
| SYS_ROLE_004 | VIP System | VERIFIED | VIP 等级逻辑/每日礼包/特权结算缺失 |
| SYS_GROWTH_002 | Talent 天赋 | VERIFIED | 天赋加点/解锁逻辑缺失 |
| SYS_APPEAR_010 | Halo 光环 | VERIFIED | 光环升级未实现 |
| SYS_ECON_006 | Black Market 黑市 | VERIFIED | 黑市独立刷新/限购逻辑缺失 |
| SYS_ECON_010 | Recharge 充值 | VERIFIED | 真实支付回调/累计充值档位未接 |
| SYS_QUEST_005 | Guide System 引导 | VERIFIED | 引导服务器态/进度同步未接 |

- **缺失什么**：这些系统多数服务端仅有面板读取或 stub，完整玩法闭环未建。
- **建议动作**：按 server_capability_needs.md 各系统"缺口/后续"列逐项补建。

### 1.4 fields.json 两向皆无映射的 55 个协议 token（跨 7 系统）

> 来源：protocol_inventory.json `_meta.supplemented_cmds`；systems_master.json `protocol_ids` 字段中带 `[UNCONFIRMED: fields.json 两方向均无映射]` 标记的条目。
> 这些 cmd 在 `protocol/cmd_table.json` 有名、在 `protocol/fields.json` 无字段定义，且 systems_master 引用了它们。PHASE C0 已按 prior analysis 引用补录为 INFERENCE 级记录（fields=[]）。

| system_id | 补录 cmd 数 | cmd 段 | 缺失什么 | 建议动作 |
|---|---|---|---|---|
| SYS_ECON_003 Mall/Shop 商城 | 41 | CS_12804~12852（商城购买族）、CS_13404~13414（兑换族） | fields.json 无这些 cmd 的字段定义 | 反编译 1.4.11 luac 抓取这些 cmd 的 CS/SC 包体结构，补 fields.json |
| SYS_GM_001 GM Tools | 5 | CS_10926~10929, CS_11999 | GM 命令族字段未定义 | hook GM 面板抓包，或反编译 gm_ctrl.luac |
| SYS_COMM_005 Cross-server 跨服 | 2 | CS_30100, CS_31299 | 跨服网关协议未实现 | 跨服工程启动时再取证（当前单体进程） |
| SYS_COMM_001 Rank 排行榜 | 1 | CS_16902 | 排行榜子命令字段未定义 | 反编译 rank_panel.luac |
| SYS_COMM_002 Arena 竞技场 | 1 | CS_11310 | 竞技场子命令字段未定义 | 反编译 arena_panel.luac |
| SYS_SOCIAL_004 Guild 公会 | 1 | CS_17500 | 公会族起始命令字段未定义 | 反编译 guild_ctrl.luac |
| SYS_DUNGEON_003 Tower 塔 | 1 | SC_13752 | 塔回包字段未定义 | 反编译 tower_panel.luac 抓 SC |

- **已知证据**：protocol_inventory.json `_meta.supplemented_cmds` 完整列表（55 个）；systems_master.json 各系统 `protocol_ids` 中带 `[UNCONFIRMED]` 后缀的条目。
- **建议动作**：优先取证 SYS_ECON_003 的 41 个商城/兑换 cmd（影响商城面板复原）；其余按系统复原节奏排期。

### 1.5 方向不一致（10 条，systems_master token vs protocol_inventory record）

> 来源：protocol_inventory.json `_meta.systems_master_direction_mismatches`。
> 这些 cmd 在 protocol_inventory 已有记录（方向已定），但 systems_master 引用的 token 方向标签与记录不一致。**不补录，待 systems_master 侧修复**。

| cmd | record 方向 | systems_master token 方向 |
|---|---|---|
| 10500 | sc | cs |
| 11202 | sc | cs |
| 11304 | sc | cs |
| 11307 | sc | cs |
| 12420 | sc | cs |
| 13203 | sc | cs |
| 19511 | sc | cs |
| 19513 | sc | cs |
| 20012 | sc | cs |
| 10300 | cs | sc |

- **缺失什么**：systems_master.json 的 `protocol_ids` 方向标签与 protocol_inventory.json 记录冲突，需统一。
- **建议动作**：以 protocol_inventory.json 为准（其 fields.json 方向为权威），修正 systems_master 引用标签。

---

## 2. 界面级（来源：ui_inventory.json）

### 2.1 B 类：资源模块存在但未运行验证（338 条）

> 判定口径：`ui_by_module` 有模块文件 + `res_categories` 有资源，未运行验证（来源：ui_inventory.json `_meta.status_definitions.B`）。
> 按系统分组共 76 个系统，完整清单见 `_raw/_b_grouped.json`。
> 这些是**下一阶段界面复原的主要输入池**，详见 `ui_restoration_order.md`。

- **已知证据**：apk_scan_1_4_11.json 的 `ui_by_module[module]` 与 `res_categories`。
- **缺失什么**：未在 MuMu 12 实机运行验证面板是否能正常打开、控件是否齐全、数据是否正确渲染。
- **建议动作**：按 ui_restoration_order.md 分阶段队列逐批实机验证。

### 2.2 C 类：仅图标/字符串证据，模块缺失（27 条，逐条列出）

> 判定口径：仅图标/字符串证据，模块缺失或极弱。这些界面**不建议本轮复原**。

| ui_name | module | system_id | system_name |
|---|---|---|---|
| 运营活动-新消耗排行榜 | xfphb | SYS_COMM_001 | Operation Activity |
| 运营活动-新充值排行榜 | czphb | SYS_COMM_001 | Operation Activity |
| 运营活动-合服首充 | hfsc | SYS_ECON_010 | Operation Activity |
| 运营活动-飞升返利礼包 | flyUp_gift | SYS_ACT_013 | Operation Activity |
| 运营活动-奖池转盘 | jiangchi | SYS_ACT_004 | Operation Activity |
| 运营活动-充值翻倍 | charge_double | SYS_ACT_013 | Operation Activity |
| 运营活动-老玩家回归 | recruit | SYS_ACT_012 | Operation Activity |
| 运营活动-合服 | hefu | SYS_UNKNOWN_002 | Operation Activity |
| 运营活动-竞猜 | guess | SYS_ACT_008 | Operation Activity |
| 运营活动-幸运转盘 | lucky_turntable | SYS_ACT_004 | Operation Activity |
| 运营活动-众神联赛场景 | godwarscene | SYS_BATTLE_004 | Operation Activity |
| 运营活动-FC | fc | SYS_UNKNOWN_002 | Operation Activity |
| 运营活动-门派 | menpai | SYS_ROLE_002 | Operation Activity |
| 运营活动-跨服公会战 | kuafu_guildwars | SYS_SOCIAL_009 | Operation Activity |
| 运营活动-活动排行榜 | actionrank | SYS_COMM_001 | Operation Activity |
| 运营活动-投资_sec | invest_sec | SYS_ACT_003 | Operation Activity |
| 运营活动-奖励 | reward | SYS_ACT_006 | Operation Activity |
| 运营活动-跨服仙魔 | kuafu_xianmo | SYS_BATTLE_004 | Operation Activity |
| 运营活动-运营兑换 | yunyingduihuan | SYS_ECON_007 | Operation Activity |
| 运营活动-送花 | flower | SYS_SOCIAL_007 | Operation Activity |
| 运营活动-幸运宝箱 | luckbox | SYS_ACT_006 | Operation Activity |
| 运营活动-祈福墙 | zhufuqiang | SYS_ACT_010 | Operation Activity |
| 运营活动-幸运翻牌 | xingyunfanpai | SYS_ACT_006 | Operation Activity |
| 运营活动-密令 | miling | SYS_UNKNOWN_002 | Operation Activity |
| 运营活动-巨龙/神龙 | julong | SYS_HIDDEN_006 | Operation Activity |
| 运营活动-成长目标 | target | SYS_QUEST_004 | Operation Activity |
| 运营活动-一元夺宝 | duobao | SYS_ACT_011 | Operation Activity |

- **已知证据**：res_categories 中存在对应图标/字符串。
- **缺失什么**：无对应 `*_panel.luac` / `*_view.luac` 模块文件；服务端多数为【缺失】或【部分】。
- **建议动作**：全部推迟到对应服务端系统建成后再考虑；当前仅作资源占位记录。

### 2.3 D 类：1.4.11 扫描中缺失（8 条）

> 判定口径：1.3.0 有而 1.4.11 无，config/UI 被移除。

| ui_name | module | system_id | 说明 |
|---|---|---|---|
| garden | garden | SYS_UNKNOWN_002 | 1.3.0 已移除 |
| jingjie | jingjie | SYS_UNKNOWN_002 | 1.3.0 已移除 |
| moneytree | moneytree | SYS_ACT_009 | 1.3.0 已移除（摇钱树旧版） |
| xiulianhulu | xiulianhulu | SYS_UNKNOWN_002 | 1.3.0 已移除 |
| glz main ui | dungeon | SYS_UNKNOWN_002 | Legacy file (glz_main_ui.luac) |
| friend view | friend | SYS_UNKNOWN_002 | Legacy file (friend_view.luac) |
| mail panel | mail | SYS_UNKNOWN_002 | Legacy file (mail_panel.luac) |
| libao view | shop | SYS_UNKNOWN_002 | Legacy file (libao_view.luac) |

- **已知证据**：1.3.0 apk_scan 有对应文件，1.4.11 apk_scan 无。
- **缺失什么**：这些界面在 1.4.11 客户端已被移除/重命名。
- **建议动作**：**不建议复原**；仅作为版本差异记录。

---

## 3. 数据级（来源：data_inventory.json）

> 17 条未确认，完整清单见 data_inventory.json `unconfirmed_items`。

| data_id | name | parse_confidence | 缺失什么 | 建议动作 |
|---|---|---|---|---|
| item_fashion | 时装表+时装类物品 | PARTIAL | 时装进阶消耗表 config_fashion_up.json 仅 2 字节（空表）；未逐条统计条目数 | 反编译 config_fashion_up.luac 确认真实行数 |
| item_currency | 货币类物品 | UNVERIFIED | 货币类型枚举表未找到；coin/hero_coin/vip_exp 与 bid 对应关系未成文 | 对照 server/currency/service 账目与 item_config type 0/12/20 |
| skill_raw | 技能原始表（4000 行） | PARTIAL | 列语义未完全定义；学习/升级消耗字段不存在 | 反编译 config_skill.luac 逐列标注；消耗走 config_skill SkillPoint |
| attr_meta | 属性数组元数据 | PARTIAL | items 条目逐属性含义未逐条核对 | 对照 _attr_data.json 31 属性系数逐列标注 |
| role_career | 职业配置表 | UNVERIFIED | 未逐条统计；职业 ID 与伙伴 career 字段（1-4）对应关系未成文 | 反编译 config_role_career.luac 逐条统计 |
| wing_data | 翅膀数据 | UNVERIFIED | 未逐条统计；翅膀消费曲线未成文 | 反编译 config_wing_data.luac 逐条统计 |
| shenqi | 神器表（574KB） | UNVERIFIED | 未逐条统计 | 反编译 config_shenqi.luac 逐条统计 |
| formation | 阵法表 | UNVERIFIED | 未逐条统计 | 反编译 config_formation.luac 逐条统计 |
| buff_data | Buff/增幅数据表（102KB） | UNVERIFIED | "增幅"类别无直接命名证据；映射到 buff_data 为最佳推断 | 人工对照 config_buff.luac 确认映射 |
| mon_data | 怪物表 | PARTIAL | 1.4.11 主表解构失败；怪物 HP/ATK 由服务端公式计算，静态不可得 | 真服抓包 / 反编译服务端公式（见全局待办 #1） |
| npc_main | NPC 主表（195KB） | UNVERIFIED | 未逐条统计 | 反编译 config_npc.luac 逐条统计 |
| npcs_10001 | 单地图 NPC 坐标快照 | FAILED | JSON 不可解析；仅按 "id" 出现次数统计（21 次=19 数值+2 哨兵） | 重新提取 1.4.11 map 10001 NPC 坐标 |
| map_main | 地图主表（83KB） | UNVERIFIED | 未逐条统计 | 反编译 config_map.luac 逐条统计 |
| dungeon_corpus | 副本群解构语料 | UNVERIFIED | 未逐条统计 | 反编译 config_dungeon_* 系列逐条统计 |
| mall_zhenbao | 珍宝阁商品 | PARTIAL | 非原版配置真值；原版珍宝阁配方是否在 APK 内未确认 | 反编译 config_mall_zhenbao.luac 确认 |
| mall_exchange | 商城兑换配方 | PARTIAL | 非原版配置真值；config_exchange.json(40KB) 解构表未对齐 | 对齐 config_exchange.json 与 13403 兑换族 |
| answer_key | 答题答案表 | PARTIAL | 非客户端 config_answer.luac 直提；与原版答案一致性未验证 | 反编译 config_answer.luac 对照 |

- **已知证据**：data_inventory.json `records[*].evidence` 字段（各表来源文件路径）。
- **建议动作**：FAILED 的 npcs_10001 优先重新提取；PARTIAL/UNVERIFIED 的表按系统复原节奏反编译补全。

---

## 4. 协议级（来源：protocol_inventory.json）

### 4.1 含 unresolved 的协议（759 条）

> 统计：protocol_inventory.json `stats.has_unresolved = 759`。
> 高频原因分类：

| 原因 | 约略数量 | 说明 | 建议动作 |
|---|---|---|---|
| cs 无字段（fields.json 无 CS 方向条目） | ~600 | 大部分 CS 命令在 fields.json 仅有 SC 或无定义 | 反编译对应 luac 补 CS 字段 |
| 实机 CS 带 rid 与 fields 冲突 | 13 | 实机观测到 CS 包体带 rid 字段，但 fields.json 未定义 | 以实机抓包为准，修正 fields.json |
| 补录 INFERENCE（systems_master 引用但 fields/cmd_table 均无） | 55 | 见 §1.4 | 反编译取证 |
| related_system=UNKNOWN | 146 | 协议未映射到具体系统 | 按 cmd 段聚类到系统 |

- **已知证据**：protocol_inventory.json `protocols[*].unresolved` 数组。
- **建议动作**：优先处理 13 条实机 CS 带 rid 冲突（影响已闭环系统的字段对齐）；600 条 cs 无字段按系统复原节奏补。

### 4.2 无字段协议（73 条，no_fields）

> 统计：protocol_inventory.json `stats.no_fields = 73`。
> 这些 cmd 在 cmd_table 有名但 fields.json 完全无字段定义。
> 样例（前 20 条）见 `_raw/_aggregated_unknown.json → protocol_inventory.no_fields_samples`。

- **缺失什么**：CS/SC 包体结构完全未知。
- **建议动作**：按系统复原优先级反编译对应 cmd_resolve_*.luac。

### 4.3 INFERENCE 补录协议（55 条）

> 即 §1.4 的 55 个 supplemented_cmds，证据等级 INFERENCE（fields=[]，方向按 token 前缀推断）。
> 来源：protocol_inventory.json `stats.supplemented_records = 55`。

---

## 5. 矩阵级（来源：client_server_matrix.json）

### 5.1 evidence_tier = UNKNOWN（9 系统）

| system_id | system_name | impl_status | 缺失什么 | 建议动作 |
|---|---|---|---|---|
| SYS_GROWTH_006 | Soul Bone 魂骨 | 未实现 | server/soulbone/ 目录存在但无接入命令；持久化 UNKNOWN | 接线 soulbone 模块 + 取证 CS 命令 |
| SYS_GROWTH_007 | Augment/Amplify 增幅 | 未实现 | server/amplification/ 目录存在但无接入命令 | 接线 amplification 模块 + 取证 CS 命令 |
| SYS_CORE_008 | Red Dot/Badge 红点 | 未实现 | 无 config/module/protocol；红点推送/聚合协议未建 | 反编译红点客户端逻辑 + 建聚合协议 |
| SYS_CORE_009 | UI State Sync UI状态 | 未实现 | 无专属同步协议；UI 状态同步帧未建 | 反编译 UI sync 帧 + 建 SC 同步 |
| SYS_UNKNOWN_001 | Dan War 丹药战 | 未实现 | 仅 config_dan_war 配置；入口/协议未取证 | 反编译客户端入口 + 建权威玩法 |
| SYS_UNKNOWN_002 | YunYing Ops 运营活动 | 未实现 | config_function.json 未命名 id；无活动框架 | 逐个识别功能 id + 建活动框架 |
| SYS_UNKNOWN_004 | Color/Head 染色 | 未实现 | 仅 config_color 配置；染色状态/协议未建 | 反编译染色入口 + 建持久化 |
| SYS_EQUIP_005 | Equip Refine 装备洗练 | 未实现 | APK inventory 未发现专属 config/module/protocol | 先取证客户端入口与协议 |
| SYS_FRIEND_006 | Partner Training 伙伴培养消耗 | 部分实现 | 喂养消耗数值 UNKNOWN（配置无显式值） | 实机喂养一次 UI 取证（需先获得伙伴） |

### 5.2 evidence_tier = INFERENCE（17 系统）

| system_id | system_name | impl_status | 说明 |
|---|---|---|---|
| SYS_ROLE_006 | Avatar/Head & Chat Bubble 头像框气泡 | 部分实现 | 仅 role 头像/气泡字段；获取与佩戴协议未接 |
| SYS_FRIEND_004 | Partner Recruit 伙伴招募/抽卡 | 部分实现 | 无专用招募命令；抽卡概率/保底未接 |
| SYS_APPEAR_008 | Vehicle/Chair 座驾 | 已实现 | role_chair 表存在；无独立 CS 命令（并入外观族） |
| SYS_ECON_007 | Exchange 兑换 | 部分实现 | 13403 兑换已接；完整兑换表/币别未闭环 |
| SYS_MAP_001 | World Map 世界地图 | 已实现 | 随场景 10200；区域解锁条件未完整 |
| SYS_DUNGEON_002 | Endless Dungeon 无尽/深渊 | 部分实现 | 共用 dungeon_progress；独立层数/奖励未闭环 |
| SYS_ACT_002 | Seven-Day Login 七日签到 | 部分实现 | 共用 sign_got；独立七日档位未闭环 |
| SYS_ACT_004 | Turntable/Lucky Draw 转盘 | 部分实现 | 仅 dial reward stub；概率/次数/奖励未接 |
| SYS_ACT_009 | Money Tree 摇钱树 | 已实现 | role_tree 表；摇钱次数/产出规则未完整 |
| SYS_ACT_010 | Pray/QiFu 祈福 | 已实现 | role_qifu 表；奖励/冷却未完整 |
| SYS_ACT_014 | Point/QingFu 点/dnf/live | 部分实现 | role_point 已持久化；活动未接 |
| SYS_SOCIAL_003 | Moments 朋友圈 | 已实现 | role_moments 表；动态发布/点赞协议未接 |
| SYS_SOCIAL_010 | Guild Tree/Animal/Skill 公会科技神兽 | 部分实现 | 共用 role_guild；成长结算未闭环 |
| SYS_HIDDEN_004 | Star Soul 星魂 | 部分实现 | 复用 role_runes；独立逻辑未取证 |
| SYS_UNKNOWN_003 | Insight 顿悟/洞察 | 部分实现 | 仅 roles.insight_status 字段；无逻辑 |
| SYS_EQUIP_006 | Gem/Socket 宝石 | 部分实现 | 合成 192 条已接；镶嵌 CS 命令未取证 |
| SYS_ECON_012 | Drop/Loot Table 掉落 | 部分实现 | config_drop 29 组；概率 pp/1000 基准 INFERENCE |

---

## 6. 版本差异矩阵级（来源：version_diff_matrix.json）

### 6.1 UNKNOWN 单元格（8 个）

> 均为 item/mission/mall/partner 配置条数在 1.3.0 与 1.4.9 的取值。

| dimension | column | 缺失什么 | 建议动作 |
|---|---|---|---|
| item 配置条数 | v130 | 1.3.0 仅 config 表存在性证据，条数 UNKNOWN | 解包 1.3.0 extracted/config/config_item.luac 计数 |
| item 配置条数 | v149 | 同上（1.4.9） | 解包 1.4.9 对应文件计数 |
| mission 配置条数 | v130 | 1.3.0 mission 条数 UNKNOWN | 解包 config_mission.luac 计数 |
| mission 配置条数 | v149 | 1.4.9 mission 条数 UNKNOWN | 同上 |
| mall 配置条数 | v130 | 1.3.0 mall 条数 UNKNOWN | 解包 config_mall.luac 计数 |
| mall 配置条数 | v149 | 1.4.9 mall 条数 UNKNOWN | 同上 |
| partner 配置条数 | v130 | 1.3.0 partner 条数 UNKNOWN | 解包 config_partner_base.luac 计数 |
| partner 配置条数 | v149 | 1.4.9 partner 条数 UNKNOWN | 同上 |

- **已知证据**：version_diff_matrix.json `scan_metrics[*].v130/v149` = "UNKNOWN"。
- **建议动作**：从 `analysis/version_compare/1.3.0/extracted/config/` 与 1.4.9 已解包目录直接计数（不影响 1.4.11 主目标，优先级低）。

---

## 7. 参考能力表级（来源：reference_capability_table.json）

| project | dimension | status | evidence_level | 缺失什么 |
|---|---|---|---|---|
| chivalrousman | 测试和日志 | 无 | UNKNOWN | 该项目测试/日志能力未取证 |
| mahatma | 测试和日志 | 无 | UNKNOWN | 同上 |
| yzxy | 任务 | UNKNOWN | VERIFIED | yzxy 任务系统能力不可借鉴（VERIFIED 级确认其无对应实现） |
| yzxy | 持久化 | 部分 | UNKNOWN | yzxy 持久化实现细节未取证 |

- **建议动作**：参考项目仅作架构参考；这 4 格不影响 JSTM 主目标，仅作参考表完整性记录。

---

## 8. 服务端能力级（来源：server_capability_needs.md）

### 8.1 【缺失】系统（35 个）

> 这些系统 mock_server 无 handler、无权威状态、无持久化。完整列表见 `_raw/_aggregated_unknown.json → server_capability_needs.缺失`。
> 主要包括：SYS_GROWTH_005 士气、SYS_BATTLE_003 战报、SYS_BATTLE_004 神魔战、SYS_FRIEND_003 伙伴图鉴、SYS_FRIEND_005 伙伴羁绊、SYS_DUNGEON_004 秘境、SYS_DUNGEON_005 其余副本、SYS_ACT_006 节日运营、SYS_ACT_008 竞猜、SYS_ACT_012 回归、SYS_ACT_013 累计充值、SYS_ACT_015 全球许愿、SYS_SOCIAL_007 送花、SYS_SOCIAL_008 宴会、SYS_COMM_005 跨服、SYS_COMM_006 采矿、SYS_COMM_008 攻城、SYS_COMM_009 押镖、SYS_COMM_010 金银塔、SYS_BACK_002 跨服后台、SYS_HIDDEN_001 封印、SYS_HIDDEN_002 修罗、SYS_HIDDEN_003 百官、SYS_HIDDEN_005 神位、SYS_HIDDEN_006 巨龙、SYS_HIDDEN_007 气球、SYS_UNKNOWN_001 丹药战、SYS_UNKNOWN_002 运营活动、SYS_UNKNOWN_004 染色、SYS_EQUIP_005 洗练、SYS_GROWTH_006 魂骨、SYS_GROWTH_007 增幅、SYS_CORE_008 红点、SYS_CORE_009 UI状态。

- **建议动作**：这些系统的客户端界面（B/C 类）**本轮不建议复原**，待服务端建成后再排期。

### 8.2 【部分】系统（29 个）

> 服务端仅有面板读取或 stub，完整闭环未建。完整列表见 `_raw/_aggregated_unknown.json → server_capability_needs.部分`。
> 典型：SYS_CORE_007 版本更新、SYS_ROLE_004 VIP、SYS_ROLE_006 头像框、SYS_GROWTH_002 天赋、SYS_EQUIP_002 锻造、SYS_EQUIP_004 升星、SYS_APPEAR_010 光环、SYS_ECON_006 黑市、SYS_ECON_007 兑换、SYS_ECON_008 拍卖、SYS_ECON_010 充值、SYS_DUNGEON_002 无尽、SYS_DUNGEON_003 塔、SYS_ACT_002 七日、SYS_ACT_004 转盘、SYS_ACT_011 夺宝、SYS_ACT_014 点/dnf/live、SYS_SOCIAL_009 公会战、SYS_SOCIAL_010 公会科技、SYS_COMM_001 排行、SYS_HIDDEN_004 星魂、SYS_UNKNOWN_003 顿悟、SYS_EQUIP_006 宝石、SYS_ROLE_007 战力、SYS_FRIEND_006 伙伴培养、SYS_FRIEND_007 伙伴装备、SYS_ECON_012 掉落、SYS_QUEST_004 成长目标。

- **建议动作**：这些系统的客户端界面可**部分复原**（面板展示层可先做，交互层待服务端补全）。

---

## 9. 全局待办（来源：HANDOFF.md §六 剩余缺口清单 9 项）

| # | 缺口 | 状态 | 后续通道 |
|---|---|---|---|
| 1 | 怪物 HP/ATK 真值 | UNKNOWN（公式在服务端，配置无显式值） | 真服抓包 / 反编译服务端公式 |
| 2 | 伙伴基础喂养消耗 | UNKNOWN（配置无显式值，账号无伙伴无可观察） | 实机喂养一次 UI 取证（需先获得伙伴） |
| 3 | 宝石镶嵌加成 | 部分 CONFIRMED（总属性表已接线）；单宝石拆分 INFERENCE | ItemJewel 反构造失败；真服 |
| 4 | 修炼 UI "50" 语义 | **CONFIRMED**：50=修炼进度条本级满值（35/50） | — |
| 5 | 修炼消耗/拥有 EXP 下发 | 进行中：practice_exp 已改动态读取=35，待用户二次回证 | 若仍空白则另有独立帧，继续 luac 定位 |
| 6 | 巡逻按钮激活条件 | 待证（客户端本地 UI 态） | 挂机场景下用户观察 / hook 客户端回调 |
| 7 | chengjiu_has.state 子字段语义 | UNKNOWN | frida-tools 原生 hook / 真服 / 用户协助 |
| 8 | 真服全量数值标定 | 待办（真服大概率已下线，原版地址被补丁替换） | 真服恢复后按 gap_dig.md 清单取证 |
| 9 | 20002 战斗族注册 | 最终裁定：保留旧链运行 | 不改 |

- **来源**：HANDOFF.md §六；tests/1.4.11/FINAL_REGRESSION.md 同步。
- **建议动作**：#1/#2/#3/#7/#8 为真服标定类，需真服恢复或 frida hook；#5/#6 为进行中待用户回证。

---

## 10. 自检记录

- [x] 数据来源：全部从既有 JSON/MD 程序化聚合，未手工抄录。
- [x] present_in UNKNOWN 计数：1.3.0=20、1.4.9=10、1.4.11=10（与 systems_master.json `_meta` 口径一致）。
- [x] ui 分类计数：A=18、B=338、C=27、D=8（与 ui_inventory.json `summary_by_status` 一致）。
- [x] data 未确认：17 条（与 data_inventory.json `unconfirmed_items` 长度一致）。
- [x] protocol unresolved：759（与 protocol_inventory.json `stats.has_unresolved` 一致）。
- [x] csm UNKNOWN evidence_tier：9 系统（与任务书列出的 9 个 system_id 完全一致）。
- [x] csm INFERENCE evidence_tier：17 系统。
- [x] version_diff UNKNOWN 单元格：8（item/mission/mall/partner × 1.3.0/1.4.9）。
- [x] reference_capability_table UNKNOWN 格：4。
- [x] 55 个补录 cmd 跨 7 系统（SYS_ECON_003/SYS_GM_001/SYS_COMM_005/SYS_COMM_001/SYS_COMM_002/SYS_SOCIAL_004/SYS_DUNGEON_003）。
- [x] 未修改任何既有文件；本文件与 `_raw/_aggregated_unknown.json` / `_raw/_aggregate_unknown.py` / `_raw/_dump_unknown.py` / `_raw/_group_b.py` 为新建派生。
