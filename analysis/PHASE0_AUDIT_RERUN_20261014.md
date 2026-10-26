# JSTM 1.4.11 复原工程 — PHASE 0 全量审计（复核 #2 / 2026-10-14）

> 本次为**只读复核**。未修改 `server/` 下任何 `.py/.lua/.db`，未启动/停止任何游戏进程。
> 复核手段：PowerShell 文件系统实测 + Python AST 静态解析 + SQLite `mode=ro` 只读连接 +
> 实跑 `server/minloop/selftest.py`。所有数字均为**本次实测**，非引用旧文档。

---

## 〇、结论先行（会影响你下一步做什么）

1. **PHASE 0 已于 2026-10-02 完成并交付**（`analysis/PHASE0_AUDIT.md`，A–M 全量，含 `[PHASE 0 AUDIT COMPLETE]` 标记）。
   本次复核确认其 **A–K 结论全部仍成立**，但 **B/E/L 三节的数字已过期**（项目在 10-02→10-06 之间推进到 PHASE 2.17）。
2. **当前没有任何私服进程在运行**：无 python 进程、9000/8080 未监听、MuMu 未启动、adb 无设备。
   最后一次服务端运行 = `server/logs/tcp.log` 最后写入 **2026-10-06 19:23**。
   ⇒ "现有私服"目前是**代码资产**，不是**运行态**；任何实现阶段的第一步都是先起 `server/mock_server.py`。
3. **PHASE 0 的 13 个子项里，11 项已交付；2 项仍是缺口**（§N）：
   `0.x` 中的「1.4.9 / 1.4.11 逐条内容计数」与「1.4.11 实机运行态证据链」未闭合。

---

## A. 当前项目结构（实测）

根 = `C:\Users\xu\Desktop\DSH`（= 当前工作目录）

```
DSH/
├── anzbao/         3 个原版 APK（1.4.11 / 1.4.9 / 1.3.0）
├── patched/        补丁 APK（1.4.11 fakelogin / minloop / solo / urlonly / dex …）
├── server/         46 个子目录 + mock_server.py(19,383 行) + minloop/ + state/roles.db + 4 套 cfg*
├── analysis/       审计产物（1,454 项）：PHASE0_AUDIT.md / version_compare/ / jstm_game_systems/
│                   client_server_matrix.md / server_capability_verified.md / reference_projects_verified.md
│                   extraction/ / runtime_evidence/ + 230+ 轮临时取证 txt + PHASE2_* 阶段文档
├── protocol/       cmd_table.json(1,643) / fields.json(3,553) / cmd_classes.json(121) / registry_classes.json(3,061)
├── tools/          738 个 .py 取证/修复/门禁脚本（+ jadx/frida/unluac/apktool 工具链）
├── tests/          1.4.11/{RUN_TESTS.ps1, FINAL_REGRESSION.md, NEW_SYSTEMS_REGRESSION.md, regression_baseline.md}
│                   + 1.4.9 回归文档
├── docs/           7 篇：ARCHITECTURE / TECHNICAL / RESTORE / SUMMARY / HANDOVER×2 / PLAN
├── cankao/         5 个参考工程 zip
├── _tmp_cfg/       1.4.11 config_*.luac 提取（305 文件）
├── _tmp_* 系列     按系统临时分析目录（battle/buff/cfg/cr112/daily/fashion/form/god/halo/hero/
│                   kaifu/rc/role/train/wedding/scratch … 共 22 个）
├── report/         100+ 轮进展报告；shots/(34) photo/(20) logs/(180) backup/(27)
└── 根级 *.md       绝世唐门APK鉴定报告 / 三包对比与选型 / 自研模拟器路线图 / HANDOFF.md / 单机版内置服务端
```

**APK 身份（本次实算 sha256 前 16 位，CONFIRMED）**

| 版本 | 文件 | 字节 | sha256[:16] |
|---|---|---|---|
| 1.4.11（主） | `anzbao/jstm_142165.apk` | 280,804,346 | `e120d165783ba78f` |
| 1.4.9 | `anzbao/jstm.apk` | 241,663,327 | `4919af2d4da54d65` |
| 1.3.0 | `anzbao/dldlJl.apk` | 142,437,549 | `c4b44b1c18b39eb3` |
| 1.4.11 补丁 | `patched/jstm_1411_fakelogin_aligned.apk` | 280,472,477 | `4595af9807618441` |

**用户建议目录结构 vs 实际**：建议 42 个模块目录中，**29 个已实体化**
（core/protocol/session/account/role/scene/npc/task/monster/level/attribute/power/item/inventory/
equipment/skill/partner/dungeon/afk/currency/package/activity/reward/guild/mail/achievement/gm/persistence/config），
4 个**改名等价**（enhancement→`enhance`、shop→`mall`、social→`friend`、battle→`battle_service`），
8 个**尚无独立目录**（wing/soulbone/fashion/amplification/artifact/destiny/formation/ranking）——
后 8 者目前活在 `mock_server.py` 单文件分发 + `role_wing/role_mingge/role_shenqi/role_fashion/`
`role_form/role_halo/role_runes/role_ride/role_lingshou` 表中（正是 Phase 2 要下沉的债）。

---

## B. 当前已实现的系统（代码级实测，CONFIRMED by code）

| 指标 | **本次实测（2026-10-14）** | 10-02 审计口径 | 变化 |
|---|---|---|---|
| `mock_server.py` | **19,383 行 / 1,086,680 B** | 18,506 行 | **+877 行** |
| `if/elif cmd == N` 分支 | 574 处 | — | — |
| `def` / `class` | 362 / 3 | — | — |
| 注册 CS 命令 | **34**（19 既有 + 本批 15，见 `analysis/INDEX.md`） | 19 | **+15** |
| `/DSH_ADMIN/*` 动作 | **72 个（唯一）** | 44 | **+28** |
| SQLite（`state/roles.db`） | **64 表 / 438,272 B** | 55 表 | **+9 表** |
| `game.db` | **0 B（空壳，未使用）** | — | ⚠ 真实库是 `state/roles.db` |
| 配置来源 | cfg=231 / kconst=285 / kconfig=245 / kconfig2=245 | 同 | 不变 |
| 端口 | TCP 9000 / HTTP 8080 | 同 | 不变 |

**本次新核实的两个关键事实**：

1. `_GENERIC_DEFAULT_CMDS` 与 `_UNSUPPORTED_ACTION_CMDS` **确为空集**
   （用 `ast.literal_eval` 实测条目 = 0；两处 `frozenset([...])` 内部**全是注释**，
   是"哪些命令曾经落在这里、为什么必须移出"的可执行文档 —— 10-02 审计的"空 frozenset"结论**成立**）。
2. `CMD_NAMES` 只有 9 条（命令名表），**不等于**已实现命令数；已实现命令数以 `if cmd==` 分支（574）与
   `DISPATCH_TABLE`（34）计。引用旧文档时勿混用这两个口径。

**活库数据（`state/roles.db` 只读实测，角色 1001）**：
`accounts 2 / roles 1 / bag_items 7 / equip_items 6 / role_heros 18 / role_mail 195 / mall_bought 44 /
reward_log 12 / dungeon_progress 15 / missions 5 / role_assets 13 / role_wing·role_ride·role_shenqi·
role_mingge·role_form·role_tree·role_lingshou 各 1 / role_skills 1 / role_build_learn 2`。

**逐系统状态**（沿用 10-02 的三分组，本次未推翻）：
- ✅ 结构与闭环 CONFIRMED：登录/建角/登角/进场景/移动/背包/仓库/装备/任务/商城/黑市/邮件/排行/副本/
  挂机/签到/日常/成就/结拜/结婚/拍卖/法宝/翅膀/坐骑/魂兽/元神/神器/命格/椅子/时装/光环/符文/投资/BOSS/
  称号/阵法书/伙伴面板/技能学习/GM。
- ⚠ 数值真实性待实机（45 项 `needs_mumu_runtime`）：战斗数值、伤害公式、装备/强化/洗练/宝石、
  各成长族每阶属性、`role_power()` vs 客户端 UI、经验表、掉落 bid/数量、商城实付。
- ❓ UNKNOWN：技能升级曲线、魂骨、增幅、聊天实时广播、公会本体（多表 0 行）、NPC 对话 UI。

**PHASE 2.11–2.17 新增（10-02 后，INDEX.md 记载 + 模块目录实测）**：
答题 `16100~16103`（`server/answer/`）、开服成长计划 `30500~30502`（`server/growth_target/`）、
刮刮乐 `16651/16652`（`server/scratch/`）、好友 `13300/13303/13305/13307/13321/13323`（`server/friend/`）、
称号 `14901`、累计充值 `16900`。

---

## C. 客户端发现的全部系统（124 系统 / 18 分类，JSON 实测）

`analysis/jstm_game_systems/systems_master.json`（118,607 B 的 md 版 = 2,296 行）

| 分类 | 数量 | 分类 | 数量 |
|---|---|---|---|
| A 核心 9 | B 角色 7 | C 成长 7 | D 战斗 5 |
| E 装备 6 | F 伙伴 7 | G 外观 10 | H 资源经济 12 |
| I 任务 5 | J 地图 2 | K 副本 5 | L 活动 15 |
| M 社交 10 | N 商业/对抗 10 | O GM 1 | P 后台 2 |
| Q 隐藏/未命名 7 | R 未知 4 | | **合计 124** |

confidence 实测分布：**CONFIRMED 50 / VERIFIED 49 / STRONG_INFERENCE 12 / INFERENCE 2 / UNKNOWN 11**，
`needs_mumu_runtime = true` **45 项**。未发现"UNKNOWN 写成 CONFIRMED"违规项。

---

## D. 三个 APK 的差异（24 维度矩阵）

`analysis/version_compare/version_diff_matrix.md`(9,340 B) / `.json`(9,036 B) + `_apk_structural_compare.json`(38,996 B)

| 项 | 1.3.0 = `dldlJl.apk` | 1.4.9 = `jstm.apk` | 1.4.11 = `jstm_142165.apk` |
|---|---|---|---|
| 渠道 / NOW_VERSION | ewan·91CW / 35 | 360·qihoo / 186 | baidu2 / **208** |
| 总条目 / `.luac` | 10,670 / 1,557 | 16,379 / 2,234 | **19,106 / 2,297** |
| `config_*.luac` / `cmd_resolve` | 168 / 89 | 227 / 122 | **233 / 124** |
| game 模块目录 / assets | 92 / 135.1 MB | 116 / 241.3 MB | **119 / 276.2 MB** |

- 24 维度**三版本均存在**，无整维度新增/删除，差异均在维度内子项级。
- **1.3.0 独有**（找回对象）：`garden`(庄园) / `jingjie`(境界) / `moneytree`(摇钱树) / `xiulianhulu`(修炼葫芦)
  + `config_holiday.luac`；`moneytree/garden` 在 1.4.11 改名为 `config_money_tree/config_garden_data`，
  `jingjie/xiulianhulu` 存废 = **UNKNOWN**。
- **1.4.11 新增**：31 个模块（auction/blackmarketeer/chair/chief/crossdungeon/endless/footmark/friendback/
  godwar/gradebreak/guildrace/guildsecretarea/guildtarget/halo/jewelvip/kunshentower/loadres/mine/peakwar/
  scratcher/script/soulstar/sworn/treasure_plane/yuangu/yuanshen/battlevideo/actionanswer/animaequip/contact/flyup）
  + 66 张配置表。
- 解包深度：**1.3.0 已全量解包**（`version_compare/1.3.0/extracted/` = 310 文件 / 293 `.luac`，含
  `config/protocal/` 下 164 张 config + 90 个 `cmd_resolve/all_proto` + 4 个独有模块目录）；
  **1.4.9 / 1.4.11 只有 `inventory.md`，无 `extracted/`** ⇒ 三版本"同维度逐条 diff"目前**只能做到 1.3.0 侧**。

---

## E. mock_server 当前能力

单体 Python + SQLite（`state/roles.db` 64 表 · 438 KB），多线程 TcpHandler，TCP 9000 + HTTP 8080。

- **协议层**：`pack_frame`/`FrameParser` + `_sc_fields` 规格缓存 + AutoConstruct 规范编码；
  `protocol/fields.json` 3,553 条 SC/CS 规格（权威源）、`cmd_table.json` 1,643 条命令名。
- **业务层**：单文件 574 个 `if cmd==` 分支（核心逻辑）+ 模块化下沉（`server/core/dispatch.py` 等）；
  配置读取覆盖 4 套来源（cfg 231 / kconst 285 / kconfig 245 / kconfig2 245）。
- **数据层**：64 表覆盖角色/资产/属性/背包/装备/任务/伙伴/多维成长/活动/市场/邮件/公会/挂机/结拜/结婚/拍卖。
- **工程层**：`battle.py` / `power.py` / `pathfind.py` / `aoi.py` / `quest_spawn.py` + `world/`（area/entities/move/ticker/jstm_bridge）。
- **管理面**：`/DSH_ADMIN/*` **72 个动作**（status/setlevel/setassets/additem/setequip/setheros/mall_buy/
  wing_up/shenqi_up/mingge_activate/skill_learn/partner_feed/afk_claim/mail_send/reward_log/battle_replay/reload…），
  改等级走 `LevelService→AttributeService→PowerService`，禁直改 DB（`gm.log` 审计）。
- **局限（未变）**：战斗数值 `TEST_ONLY`、战力/成长公式 `INFERENCE`、单进程 GIL、数值真实性全待实机取证。

---

## F. miniloop 可借鉴能力（本次**实跑**验证）

`server/minloop/{min_loop_server.py, selftest.py, replay_real_frames.py, replay_stateful.py}`

- **`selftest.py` 本次实跑：检查项 145，通过 145，失败 0**（2026-10-14 12:45，独立临时 DB + 独立端口，
  未触碰 `state/roles.db`）。落盘 `C:\WINDOWS\TEMP\minloop_selftest_*\test.db`。
- 它做的事：用**真实协议规格**严格解码每一帧（多/少字节即 FAIL），走完
  登录→角色→进场景→接任务→打怪→结算→掉落→提交→奖励→背包 全链，并断言业务结果。
- 价值：**兼容性度量尺 + 回归基座**；"不猜、宁可空但合法"的纪律可复用。
- 局限：不实现 AOI/多人在线/商城/邮件/活动等横向系统；自检只验**结构**不验**数值**。

---

## G. 参考项目可借鉴能力（`cankao/` 实测 5 个 zip，非 4 份）

| 项目 | 技术栈 | 可借鉴（仅设计） | 许可（zip 级已核） |
|---|---|---|---|
| Survive | Lua(distrilua)+C .so+PHP 后台 | 服务组拆分、单线程多场景、AOI/寻路思想、GM 后台 | 无顶层 LICENSE；`aoi.h/astar.h/wordfilter.h` 内嵌 GPLv3 |
| kongkongxiyou | Node.js+Pomelo+Cocos2d-JS | 按域切 handler、connector 网关、area+domain、任务状态机、Excel→JSON 管线 | **pomelo/lordofpomelo = MIT**（本轮新发现）；游戏内容无 LICENSE |
| CXEngine/YZXY | C++(CMake,cxluax)+Lua | share 共享层 + 独立 combat、addon 插件化 | 无 LICENSE |
| MahatmaComeBack | Cocos C++ 客户端 / C# 服务端 | 客/服分离、.sql 集中建表思路 | **GPLv3** |
| ChivalrousMan | 仅 Cocos C++ 客户端 | MMORPG 客户端流程、业务字段语义 | 无 LICENSE；含泄露 MySQL 凭据（**禁用**） |

**纪律重申**：5 项目只借架构/模块/数据模型/工程经验；协议/数值/任务/装备/技能/怪物/属性/战斗规则
一律不得当 JSTM 数据。最高权威 = 3 个原版 APK + 资源 + 协议 + 实机运行结果。

---

## H. 客户端系统 → 服务端需求矩阵

`analysis/client_server_matrix.md`（23,237 B，**124 行数据行**，其中 **46 行**标 `⏳需MuMu取证`）
每行 5 列齐全：APK 入口 / 协议 / 数据 / 服务端归属 / 状态。节选：

| 系统 | APK 入口 | 协议 | 数据 | 服务端 | 状态 |
|---|---|---|---|---|---|
| 登录 | denglu_* | 1110 | accounts | login | ✅ |
| 角色 | role_ctrl/role_data | 10301–10306 | roles/role_attr | role | ✅ |
| 任务 | mission_* | 12400–12421 | missions | task | ✅ |
| 战斗 | battle_* | 20000 族 | (内存) | battle.py | ⚠ 需实机取证 |
| 背包 | backpack_* | 10500–10593 | bag_items | inventory | ✅ |
| 装备/强化/洗练/宝石 | backpack/equip | 105xx/106xx | bag_items/equip | equipment | ⚠ 需实机取证 |
| 商城 | shop_* | 12801–12856 | mall_bought | shop(mall) | ⚠ 实付需取证 |
| 伙伴 | hero_ctrl | 11215/11210 | role_heros | partner | ⚠ 部分 |
| 翅膀/魂骨/神器/命格/阵法 | 各 ctrl | 各自 | role_* | 各成长系统 | ⚠ 部分 |
| 结婚/结拜/跨服 | marry/jiebai/race | 各 | 部分落表 | social(friend/guild) | ⚠ 部分/未实现 |

---

## I. 系统依赖图（`jstm_game_systems/system_dependency_graph.md`，复核仍成立）

```
角色 → 等级 → 经验 → 属性(AttributeService) → 战力(PowerService) → 客户端同步
装备 → 属性 → 战力        伙伴 → 属性 → 战力
翅膀/坐骑/法宝/命格/神器/元神/时装/图腾/椅子/五行/强化/升级 → 属性 → 战力
阵法 → 伙伴 → 战斗        任务 → 条件(ConditionService) → 奖励(RewardService)
战斗 → 奖励(EXP/货币/掉落) → 任务进度 → 战斗循环
商城/活动 → 货币(CurrencyService) → 扣费 → RewardService → 发货（幂等 reference_id）
全部系统 → PersistenceService(SQLite) → ClientSync
```

**红线**：任一成长系统禁止自算属性/战力；资产变动禁止绕过 Currency/Reward；奖励必带 `reference_id` 防重；
原版公式未知一律标 `JSTMCompatiblePowerFormula` + `INFERENCE` 并留替换点。

---

## J. 未实现系统清单（42 项）

`analysis/jstm_game_systems/unimplemented_systems.md`（28,307 B / 563 行 / 44 表格行）。
含：版本与资源更新、士气、战斗回放、神魔战、伙伴图鉴/羁绊、引导、秘境、其余副本（神界/封印恶魔/SMJZ/金银塔）、
节日与运营活动、竞猜、夺宝、回归、充值活动、许愿、宴会、跨服、采矿、攻城、押镖、金银塔、跨服后台、
封印、修罗、首席、神灵、神龙、气球、丹药战（UNKNOWN）、运营入口 33/34/37/40/101/103（UNKNOWN）、染色（UNKNOWN）……

**判定纪律（INDEX.md §二，务必沿用）**：判"要不要做"先看 `server/logs/tcp.log` 的 `>> cmd=N` 次数
——**发 = 0 一律不实现**（已据此排除送花 13324/13326/13328/16300、聊天 127xx、好友扩展 133xx 一批、30503/30506、13369）。
判"回空"必须走 4 类判定法（真缺口 / 角色无数据 / 有意回空 / 配置侧未填），否则会得到"第二次假象"。

---

## K. UNKNOWN 系统清单（**禁止当事实使用**）

1. **11 个系统 `confidence=UNKNOWN`**：Dan War 丹药战、YunYing Ops 运营入口、Color 染色等（有配置文件名，语义未定）。
2. **1.4.11 的 item/task/partner/shop 逐条计数**：存在性 CONFIRMED，**计数未提取**（1.4.9 侧的 3535/846/53/142 为 VERIFIED）。
3. **战力公式 / 各成长族数值公式**：原版权威公式未知，`role_power()` 为 INFERENCE 兼容实现。
4. **战斗数值**：怪物 HP/攻防/EXP/掉落 —— APK 内无此数据（服务端公式算出），当前 `TEST_ONLY`/占位。
5. **宝石镶嵌加成**：`ItemJewel` 反构造失败，总属性表已接线，单宝石拆分 INFERENCE。
6. **修炼消耗/拥有 EXP 值**：进度条 35/50 正确，消耗/拥有栏空白，字段偏移待定位。
7. **巡逻按钮激活条件**：点击无 CS 命令，客户端本地 UI 态待证。
8. **`chengjiu_has.state` 子字段语义**：待 hook。
9. **`jingjie`/`xiulianhulu` 在 1.4.11 的存废**：待 1.4.11 全量配置确认。
10. **1.4.11 在 MuMu 中的实际运行态**：本次实测 adb 无设备、MuMu 未启动 ⇒ **当前不可验证**
    （10-02 审计记为"尚未装入"，HANDOFF 10-02 记为"已装并跑通登录/地图/NPC/任务"——**两处记载冲突，需一次实机确认**）。
11. **若干礼包/掉落 ID 指向、珍宝商城 45 件商品数据**：原版服务端数据不在 APK 内。

---

## L. 推荐实施路线（本次修订）

```
Phase 0  ✅ 完成（2026-10-02）+ 本次复核 #2（2026-10-14）
Phase 1  MuMu + mock_server 联调（唯一未闭合的前置）：
         启动 MuMu → adb connect 127.0.0.1:16384 → 确认 1.4.11 包在机 → 起 mock_server(9000/8080)
         → 抓 R1–R12 协议实值 + V1–V12 数值标定 → 产出"实现 vs 实机"差异清单
Phase 2  Server Core 下沉（19,383 行 if 链 → 按域 handler；wing/soulbone/fashion/amplification/
         artifact/destiny/formation/ranking 8 个缺目录补齐）——高风险，需回归保护
Phase 3–4  Account/Login/Role/Scene（已可用，保留）+ Level/EXP/Attribute/Power 服务化
Phase 5  Monster/Battle/Reward（数值取证优先，RewardService 统一）
Phase 6–8 Inventory/Item/Currency → Equipment/Enhancement/Gem → Skill
Phase 9–11 Partner → 外观成长族 → 神器/命格/阵法/增幅
Phase 12–13 Dungeon/AFK → Shop/Package/Activity
Phase 14 Social/Guild/Mail/Ranking
Phase 15 GM Manager（现为 `/DSH_ADMIN` 72 动作内嵌，需独立化 + 权限分级 SUPER_ADMIN/ADMIN/OPERATOR/VIEWER + 审计）
Phase 16–17 1.4.11 全量内容入库 + 全场景 Regression
```

**ReVa（本次已装）在证据链里的正确位置**（规划，非实现）：
- 它擅长的是 **native/ELF 层**（`libsupersdkjni.so`、Bangcle 保护、客户端 `.so` 逻辑）——
  对应本工程 K 节里的**客户端侧** UNKNOWN（宝石镶嵌反构造、修炼帧偏移、`chengjiu_has` 字段、
  巡逻按钮回调）：用 ReVa 的 Ghidra MCP 工具在反编译视图里定位字符串/交叉引用，比反复 luac 试错快。
- **不可**用它替代**服务端侧数值**取证（怪物 HP/ATK、伤害公式、掉落概率）——那些值不在客户端，
  必须靠 MuMu 实机抓包 / 真服流量。**别把 ReVa 当成 V1–V12 数值标定的替代品。**

---

## M. 预计每阶段工作量（相对，8h 日当量）

| Phase | 内容 | 预估 | 备注 |
|---|---|---|---|
| 1 | MuMu 联调 + 协议实值 + 数值标定 | **2–4 天** | 硬约束前置；出 V1–V12 标定表 |
| 2 | 拆 handler / 补 8 个缺目录 | 2–3 天 | 高风险高收益 |
| 3–4 | 核心/角色/属性/战力服务化 | 1–2 天 | 战力公式待替换 |
| 5 | 战斗 + 奖励 | **3–5 天** | 数值取证是硬骨头 |
| 6 | 背包/货币/装备/强化/宝石 | 3–4 天 | 复用现有 64 表 |
| 7–8 | 技能 / 伙伴 | 2–3 天 | |
| 9–11 | 外观成长 / 神器 / 命格 / 阵法 / 增幅 | 3–4 天 | 大量 config_* 待入库 |
| 12 | 副本 / 挂机 | 2–3 天 | |
| 13 | 商城 / 礼包 / 活动 | 2–3 天 | |
| 14 | 社交 / 公会 / 跨服 | 3–4 天 | 结婚/结拜等新系统 |
| 15 | GM Manager 独立化 | 2–3 天 | 复用 72 动作 |
| 16–17 | 内容填充 + 全量回归 | 3–4 天 | 1.4.11 全量 |

**合计：约 30–42 人日**（较 10-02 的 32–44 略降，因 Phase 2.11–2.17 已消化掉若干系统）。
最大不确定性 = **战斗数值与成长公式的 MuMu 取证难度**。

---

## N. 本次复核发现的「审计自身缺口」（Phase 0 未闭合项）

| # | 缺口 | 现状 | 建议处置 |
|---|---|---|---|
| 1 | 1.4.9 / 1.4.11 无 `extracted/` 逐条清单 | 只有 `inventory.md`；逐条计数 UNKNOWN | 解包两包（1.3.0 路径已有脚本 `_extract.py` 可复用）|
| 2 | 三版本"同维度逐条 diff"只做到 1.3.0 侧 | 24 维度矩阵已建，子项级 diff 不完整 | 承 #1 |
| 3 | ~~1.4.11 实机运行态记载冲突~~ | ✅ **2026-10-14 已闭合**：实机确认 `com.shiyue.dldl.ewan.baidu2` = **1.4.11（versionCode 46）已安装并运行**，base.apk 280,472,477 B = 本地 `patched/jstm_1411_fakelogin_aligned.apk` 同长 ⇒ 装的是**补丁包**。`PHASE0_AUDIT.md` §0.1「尚未装入」**已过期**，以 `analysis/extraction/phase1_runtime_restore.md` 为准 | — |
| 4 | `PHASE0_AUDIT.md` B/E/L 数字过期 | 19,383 行 / 72 动作 / 64 表 / 34 命令 | 以本文件为准，或在旧文件顶部加 superseded 标注 |
| 5 | `game.db` 为 0 B 空壳 | 易误判"库不存在" | 文档里明确唯一真实库 = `state/roles.db` |
| 6 | 审计期内无运行态证据 | 无 python 进程、无 adb 设备 | Phase 1 恢复运行态后重抓 |

---

## 结论

- **PHASE 0 交付物完整存在**（13/13 文件级交付；`analysis/` 内 A–M 全部可查），
  本次复核**独立验证了其中 A–K 的结论**，并修正了 3 处过期数字（B/E/L）。
- **项目真实进度已越过 PHASE 0**：`analysis/INDEX.md`（2026-10-06，PHASE 2.17 后）显示
  已注册 34 条命令、剩余缺口**全部阻塞在证据**（需实机 / 需真值），**无一属"工时不够"**。
- **当前阻塞点只有一个**：运行态未启动（MuMu 未开、mock_server 未跑、adb 无设备）。
  Phase 0 之后任何实现动作的第一步都是恢复这条链路。
- 本次复核**未修改任何核心代码**，未启停任何服务。

# [PHASE 0 AUDIT COMPLETE]
# [WAITING FOR IMPLEMENTATION]
