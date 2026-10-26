# 1.4.11 全量回归汇总（Phase 1–16 + 扩展轮 收官）

> 日期：2026-10-02 | 单机 mock 游戏服（mock_server.py）垂直闭环迁移收官
> 状态：[PHASE 1-16 + 扩展轮 COMPLETE]

---

## 一、注册命令清单（DISPATCH_TABLE，共 19 个 CS 命令）

| 命令 | 功能 | 阶段 |
|---|---|---|
| 1110 | 登录 | 既有 |
| 10101 | 建角/角色数据 | 既有 |
| 10200 | 场景 | 既有 |
| 10301/10302/10303 | 属性/角色/技能推送 | 既有 |
| 10304/10306 | 战力/资产推送 | 既有 |
| 10502 | 背包同步 | 既有 |
| 12400/12401/12408 | 任务列表/NPC | 既有 |
| 15203 | **元宝兑换宝图**（⚠ 原记"NPC 交互"**有误**，据 `cmd_table` 更正；见 `PHASE2_17` 与 `dead_protocols_and_traffic.md` §八） | 既有 |
| 11215 | 伙伴面板 | P8 |
| 10622 | 已学技能 | P8 |
| 10601/10610 | 天赋/修炼面板 | P8+ |
| 10651 | 天赋列表 | P8+ |
| 11600 | 翅膀面板 | P9 |

> 注：深耦合面板编码器（命格19400/副本130xx/挂机154xx/商城128xx/签到141xx/邮件108xx/公会183xx/成就16400）留旧链，避免帧字节漂移；闭环经 GM 端点程序化验证。

---

## 二、各阶段闭环汇总

| Phase | 内容 | 闭环状态 | 证据 |
|---|---|---|---|
| P8 | 伙伴/技能 | ✅ 伙伴面板+培养、技能学习/升级 | partner_feed/skill_learn/skill_up |
| P9 | 成长族 | ✅ 翅膀/神器/命格升阶 | wing_up/shenqi_up/mingge_activate |
| P10 | 副本/挂机 | ✅ 副本34列表+首通、挂机累积+幂等领取 | dungeon_clear/afk_claim |
| P11 | 商城/签到 | ✅ 购买扣币+限购、每日签到幂等 | mall_buy/sign_do |
| P12 | 邮件/排行 | ✅ 邮件领附件幂等、九维breakdown | mail_claim/power.breakdown |
| P13 | GM 正式链路 | ✅ setlevel/setassets 走 service + gm.log | §36 达成 |
| P16 | 掉落+D2收口 | ✅ 掉落表接线、不可渲染bid过滤 | drop_test + build_bag_items 过滤 |
| 扩展轮 | 数值真值提取 | ✅ 强化/签到/掉落/战力系数/伙伴曲线/技能消耗 | truth_values + gap_dig |
| 扩展轮 | 实机 UI 取证 | ✅ 技能/伙伴/挂机面板 UI 显示值采集 | ui_display_values |

---

## 三、真实数据覆盖分级

### CONFIRMED（已从配置表提取真值）

| 系统 | 数据项 | 来源 |
|---|---|---|
| 强化 | 成功率 L1=100%/L3=75%、金币 L1=2400→L15 | config_intensify.json |
| 签到 | 30天逐日奖励 Day1=coin250000/Day7=item36500x15 | config_checkin.json |
| 掉落 | 29组金币/首通池（20001~20029） | config_drop.json |
| 战力系数 | AttrPower 31属性（攻速450/躲闪275/暴击183/物攻106） | config_attr.json |
| 伙伴曲线 | PartnerLevUp 201级经验、神器 L1=2400→L5=18000 | config_partner_base.json |
| 技能消耗 | SkillPoint L1=10g→L10=100g、修炼学习 86exp | config_skill.json |
| 修炼升级 | L1→L2=402exp, L2→L3=852exp（192级） | config_skill_xiulian.json |
| 成就 | 342条成就配置（server/achievement/service.py） | config_chengjiu.json |
| 挂机地图 | GuajiInfo 8个区域（map_bid/等级范围/mon_bid） | config_guaji.json |
| 宝石合成 | 192条合成消耗 2000~4000金/次 成功率100% | config_item_fuse.json |

### INFERENCE（基于配置推断，未实机标定）

| 系统 | 数据项 | 说明 |
|---|---|---|
| 掉落概率 | pp/1000 基准 | 需实机战斗标定 |
| 挂机收益 | GOLD=200/EXP=100 每分钟 | 配置有地图，收益系数推断 |
| 九维战力 | 公式结构 CONFIRMED，分项计算 INFERENCE | 系数表有，组合公式待验证 |
| D2 渲染根因 | 客户端图标资源缺失假设 | INFERENCE，未 hook 验证 |

### UNKNOWN（配置表中无数据，需实机/真服抓取）

| 系统 | 数据项 | 原因 |
|---|---|---|
| 怪物 HP/ATK | config_mon_data.luac 反构造失败 | 服务端公式计算，静态提取不可得 |
| 伙伴基础喂养 | FEED_GOLD=1000/FEED_EXP=500 | INFERENCE 占位，无配置真值 |
| 宝石镶嵌加成 | ItemJewel 反构造全 null | 镶嵌后属性加成无显式配置 |
| 修炼消耗/拥有 EXP 数值 | 进度条 35/50 正确但消耗/拥有栏空白 | 字段偏移待定位 |
| 巡逻按钮激活 | 自动巡逻按钮点击无 CS 命令 | 客户端 UI 态待证 |
| chengjiu_has.state | 成就完成状态字段 | CS 回包未实现，字段偏移待 hook |

---

## 四、剩余缺口清单（终版）

| # | 缺口 | 尝试通道 | 后续通道 | 状态 |
|---|---|---|---|---|
| 1 | 怪物 HP/ATK 真值 | 静态提取 config_mon_data + 1.4.9 对照 | MuMu 实机战斗抓包 / 真服流量 | UNKNOWN |
| 2 | 伙伴基础喂养消耗 | 全部 partner 配置表扫描完成，无消耗字段 | 客户端硬编码/服务端逻辑 | UNKNOWN（配置表无显式值） |
| 3 | 宝石镶嵌后属性加成 | `ItemMiscAttrJewel` 总属性表已提取 + **本会话完成相邻等级差推算** | 单个宝石语义（累计 vs 单级）| **总表 CONFIRMED / 增量 INFERENCE**（见 `analysis/extraction/jewel_attr_derived.md`：lev 3→10 全 11 项属性总值已列全，增量已算；**语义假设未取证**） |
| 4 | 修炼 UI "50"语义 | 用户协助截图 xiulian_panel_35of50.png | — | **CONFIRMED**（50=本级进度满值；35=当前修炼经验 bid=10822 exp=35） |
| 5 | 修炼消耗/拥有 EXP 数值下发 | UI 证据：进度条 35/50 正确但消耗/拥有栏空白 | **客户端 hook**（服务端已穷举，勿再加帧） | **服务端半 CONFIRMED / 客户端半**：全协议仅 10302/10303/10304 含 `practice_exp`，三帧**实测均为 35**，另 10305 推 `label9=35`；面板反汇编证实读 `RoleVo.practice_exp`（`skill_train.luac` proto#10）——**经用户实机回证仍空白** ⇒ **不是缺帧，是客户端渲染**。详见 `analysis/extraction/xiulian_frame_spec.md` 第五轮 |
| 6 | 巡逻按钮激活条件 | 5 种交互变体实机验证 | hook 按钮回调 / 真服对照 | 待证（待挂机场景下用户协助观察） |
| 7 | chengjiu_has.state 字段偏移 | 配置表结构分析 | 实机 hook CS 回包解析 | UNKNOWN |
| 8 | 真服抓包（全量数值标定） | 静态提取已穷尽 | 真服可达后抓包标定所有 INFERENCE | 待办 |
| 9 | 20002 注册下沉 | 8件套逐字抽取风险 | 下批分两小步：① guaji两件+map_def_xy ② scene_npcs/scene_mons | 断点 |

---

## 五、全量回归（六项）

1. miniloop 145/145 ×3 稳定 PASS。
2. py_compile+import+registered_cmds(19) PASS。
3. /status lv70 gold=1799840 coin=9904599 scene=10001 PASS。
4. 实机：登录序列连上、史莱克城 DSH lv70 战力 57.7万；setlevel pushed=1。
5. shadow_lint 空。
6. server/dispatch/reward/gm.log 无异常。

### 五之补 · 06 日复核（新 agent 接手批次，未改任何代码）

服务端重启后实测（`D:\Python\python.exe server/mock_server.py --http 8080 --game 9000`）：

| 项 | 结果 |
|---|---|
| miniloop | `python server/minloop/selftest.py` → **检查项 145 / 通过 145 / 失败 0** ✓（注：HANDOFF 写的路径 `server/min_loop_server.py` 不存在，实际为 `server/minloop/`） |
| py_compile | `server/mock_server.py` OK；`@register` 注册点 = **19** ✓ |
| shadow_lint | `tools/lint_dispatch_shadow.py` → **✓ 无分发遮蔽**（专用 1430 / 默认 0 / 未开放 0） |
| 当前运行日志 | 本次启动（14:20:45 起）**无异常**；历史 `_dedicated_cmds NameError(re)` 已由 R150b 局部 `import re as _re` 修复（非当前问题） |
| `/status` | **注意**：`GET /status` 是**游戏网关**端点（回 `{code:0,msg:"ok",...}`）；管理面基线在 **`GET /DSH_ADMIN/status`** |
| 基线值 | lv70 / career1 / **scene_id=10001** ✓；gold=**1800140**、coin=**9904629**（与文档基线 1799840 / 9904599 差 **+300 / +30**） |

> **基线漂移已解释**：`/DSH_ADMIN/reward_log` 有 9 条**正常发放**记录
> （battle kill:20001、achievement ×2、mail_claim、daily_sign、shop、afk_claim、dungeon_clear、gm-giveitem），
> 均带 `reference_id` 幂等键 ⇒ 漂移来自基线记录之后的**合法奖励**，非数据损坏。
> 后续回归建议以**漂移后现值**为准，或先记录当次现值。

---

## 六、关键交付文档索引

| 文档 | 路径 | 内容 |
|---|---|---|
| 内容计数清单 | analysis/jstm_game_content_inventory.json | 全系统条数统计 |
| 计数明细 | analysis/jstm_game_content_inventory_counts.md | 按表列出行数/来源/证据等级 |
| 怪物数值提取 | analysis/extraction/monster_values.md | 怪物 HP/ATK 提取结论 |
| 数值真值替换 | analysis/extraction/truth_values.md | 真服探测+深度静态提取 |
| 4缺口深挖 | analysis/extraction/gap_dig.md | 技能/伙伴/宝石/怪物逐项结论 |
| UI 显示值取证 | analysis/extraction/ui_display_values.md | 实机面板显示值采集 |
| 修炼帧规格 | analysis/extraction/xiulian_frame_spec.md | 10621 字段偏移+填值方案 |
| 挂机进图验证 | analysis/extraction/afk_enter_verify_report.md | 巡逻按钮实测结论 |
| 巡逻按钮规格 | analysis/extraction/patrol_button_spec.md | 激活条件分析+变体测试 |
| 校准 UI 坐标 | analysis/calibrated_ui_coords.md | 2560x1440 分辨率坐标清单 |
| Phase16 准备 | analysis/phase16_prep.md | D2 背包/掉落表/UI 核对 |
| 战斗注册设计 | analysis/battle_register_design.md | 战斗系统接线设计 |
| 持久化下沉 | analysis/persistence_down_sink.md | 数据持久化方案 |
| Phase2 设计 | analysis/phase2_design.md | Phase2 全系统设计 |

---

## 七、结论

**[PHASE 1-16 + 扩展轮 COMPLETE]**

- 注册命令：19 个 CS 命令闭环
- 系统覆盖：背包/装备/伙伴/技能/成长/副本/挂机/商城/签到/邮件/排行/翅膀/成就/GM 共 14+ 系统
- 数据分级：CONFIRMED 11 项 / INFERENCE 4 项 / UNKNOWN 6 项 + 2 项待证
- 剩余缺口：9 项（详见第四节），深耦合族留断点（20002 注册待两小步下沉）
- 非全部系统 100% 闭环：怪物数值/伙伴喂养/宝石镶嵌/修炼消耗字段/巡逻激活等待后续实机 hook + 真服抓包标定

---

## 附：persistence/config 下沉盘点（2026-10-02 06:35 UTC+8）

### 已注册命令（DISPATCH_TABLE，19 条）
1110, 10101, 10200, 10301, 10302, 10303, 10304, 10306, 10502, 10601, 10610, 10622, 10651, 11215, 11600, 12400, 12401, 12408, 15203。

### 已下沉模块（from-import 无损）
- core/runtime: CFG/LIVE_CONNECTIONS/LIVE_LOCK/CUR_VER。
- persistence/db: db_conn/db_release。
- protocol/fields+frame: _sc_fields/pack_frame/w_*。
- attribute/service: db_role_attr/db_get_attr/db_save_attr/attr_row_bytes/_ATTR_ALIAS。
- currency/service: db_get_assets/db_add_assets/db_set_assets。
- role/storage: db_get_role/db_save_role/role_state。
- task/service: db_get_missions/db_save_mission/mission_cfg/mission_def/mission_chain/mission_rows/build_12400。
- equipment/service: 10601/10610/10651 handler。
- scene/service: 8 件套（static_mons/quest_spawn/map_cfg/scene_npcs/scene_mons/map_def_xy/guaji_spots/guaji_spot_for_lev）——模块已建+接线，本地 def 仍遮蔽（行为等价）。

### 20002 战斗族状态：仍断点（未注册）
- 阻塞：20002 入口（候选场景查找+self.battle+Timer kick）未抽 handler；8 件套本地 def 未注释。
- replay 锚点：battle_replay(mon_id=20001) 确定性 hex（server/backup/replay_before.json）。
- 解锁前置：注释 8 件套本地 def（is==True）→ 抽 20002 handler → replay hex 对比。

### 剩余缺口终版
- 20002 战斗族注册（断点）。
- scene 8 件套本地 def 注释（is==True，行为等价未改）。
- AOI 邻居帧/20002 帧逐字节对比需第二在线客户端。

- [更新 06:50] guaji 三件本地 def 已注释（is==True）；scene 六件仍遮蔽。registered=19。replay 一致。

- [最终 07:00] scene 8 件套全部 is==True。20002 最终裁定：保留旧链运行（self 上下文传递面过大）。registered=19。replay 一致。

---

## 附二、★ 状态刷新（2026-10-06，PHASE 2.11 ~ 2.17）

> 本节的目的是**纠正本文档中已过期的数字与结论**，接手者请以本节为准。

### 1. 注册命令：19 → **34**

新增 15 条（全部有独立模块 + 可复跑测试）：

| 系统 | 命令 | 模块 |
|---|---|---|
| 答题 | 16100 / 16101 / 16102 / 16103 | `server/answer/` |
| 刮刮乐 | 16651 / 16652 | `server/scratch/` |
| 开服成长计划 | 30500 / 30501 / 30502 | `server/growth_target/` |
| 好友 | 13300 / 13303 / 13305 / 13307 / 13321 / 13323 | `server/friend/` |

外加（非注册命令）：`16900` 读真值、GM `GET /DSH_ADMIN/setcharge`、`14901` 接 `role_title`。

**一键回归**：`pwsh -File tests/1.4.11/RUN_TESTS.ps1 -SelfStart`（详见 `NEW_SYSTEMS_REGRESSION.md`）。

### 2. 本文档内已更正的事实

| 处 | 原记 | 更正（证据） |
|---|---|---|
| §二 命令表 | `15203 = NPC 交互` | **`15203 = 元宝兑换宝图`**（`protocol/cmd_table.json`，CONFIRMED）|

### 3. 本批新增的**方法学**（判"回空"必用）

**死协议判据**：先查 `server/logs/tcp.log` 的 `>> cmd=N`；**发=0 一律不实现**。
据此已排除：**送花**(13324/13326/13328/16300)、**聊天**(127xx)、
**好友扩展**(13306/13310/13314/13319/13320/13341/13342/13349)、`30503/30506`。

**空表 4 类判定法**（缺一步会误判）：

| 类 | 表现 | 例 | 处置 |
|---|---|---|---|
| ① 真缺口（半接）| 写入侧/GM 有数据源，**读侧没接** | `14901`（已修）| ✅ 可修 |
| ② 角色无数据 | 读侧已接，**表里没这行** | `11300`、`13369` | 无需动 |
| ③ 有意回空 | 读侧**故意**不填（注释写明）| `11700`/`16605`/`10924`/`10923` | 待实机语义 |
| ④ 配置侧未填 | handler 读了 config 键，但**键缺失/为空** | `10527`、`10532` | **需真值来源** |

### 4. 剩余缺口的**真实性质**（比"9 项"更准确）

本文 §四 的 9 项缺口，经本轮核查后**无一属于"工时不够"**，全部阻塞在**证据**：

- **需实机（MuMu）**：`16605`/`10924`/`16903`/`10923` 的取值语义；§三 的修炼消耗字段、巡逻激活、`chengjiu_has.state`。
- **需真值来源**：`10527`/`10532`（config 键从未填）、`14009`（数据源未取证）。
- **已明确留白**（不猜）：怪物 HP/ATK、伙伴喂养、宝石镶嵌的多项 UNKNOWN。

> ⇒ **结论**：在"不编造 + 不启动模拟器 + 不引入外部真值"的前提下，
> **客户端流量驱动的缺口挖掘已到尽头**。后续产出必须依赖 **实机** 或 **真服抓包**。

**证据文档索引**：`analysis/extraction/dead_protocols_and_traffic.md`（死协议 + 流量画像 + 空表 4 类法）
· `analysis/gap_map.txt`（缺口地图）· `analysis/extraction/core_gameplay_candidates.md`（候选评估）
· `analysis/PHASE2_1{2,3,4,5,6,7}_*.md`（本批 5 系统阶段文档）。

### 5. ★ §四 九项缺口的**阻塞类型**标签（接手者一眼定位"该找谁"）

> 给 §四 每项打上"卡在哪"，避免"看起来都是缺口、其实要的资源完全不同"。

| # | 缺口 | 阻塞类型 | 需要什么 |
|---|---|---|---|
| 4 | 修炼 UI "50"语义 | ✅ **已解决** | 已 CONFIRMED（50=本级满值；35=bid 10822 exp）|
| 9 | 20002 注册下沉 | ✅ **已裁定关闭** | 最终裁定：**保留旧链，不再尝试下沉**（self 上下文传递面过大）|
| 5 | 修炼消耗/拥有 EXP 下发 | 🔴 **需实机（客户端侧）** | 服务端已穷举（**勿再加帧**）⇒ 需 hook `rgp_hander10302/3/4` 或 `skill_train.updateOwnExp` |
| 6 | 巡逻按钮激活条件 | 🔴 **需实机观察** | 挂机场景下观察按钮回调（需用户协助）|
| 7 | `chengjiu_has.state` 偏移 | 🔴 **需实机 hook** | hook CS 回包解析 |
| 1 | 怪物 HP/ATK 真值 | 🔵 **需真值** | 静态提取已穷尽 ⇒ 实机战斗抓包 / 真服流量 |
| 2 | 伙伴基础喂养消耗 | 🔵 **需真值** | 全部 partner 配置表扫描完毕，**无消耗字段** ⇒ 客户端硬编码或服务端逻辑 |
| 3 | 宝石镶嵌属性加成 | 🟡 **部分已推进** | 本会话新增：`config_item_misc.EqmJewel`（装备→孔位/等级）+ `ItemMiscAttrJewel`（总属性表）⇒ 单个宝石属性仍 INFERENCE |
| 8 | 真服全量数值标定 | 🟠 **需真服可达** | 真服能连后才能批量标定所有 INFERENCE |

**汇总**：**2 项已收口**（#4/#9）、**3 项需实机 MuMu**（#5/#6/#7）、**3 项需真值**（#1/#2/#3，其中 #3 已部分推进）、**1 项需真服**（#8）。

> ⇒ 与 §附二.4 结论一致：**没有任何一项是"工时不够"**。
> 若要继续推进目标第 (2) 部分，**启动模拟器（A）是收益最高的唯一入口**。
