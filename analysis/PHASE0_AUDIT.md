# 《绝世唐门》JSTM — PHASE 0 全量审计报告（2026-10-02 复核版）

> 范围：只读审计。本报告及本次全部子审计**未修改任何核心代码**（server/ 下所有 .py/.lua/.db 均未改动）。
> 本次复核在既有 PHASE 0 成果之上完成：①按用户最高优先级硬约束建立 **MuMu 运行时取证通道**并实测本机环境；
> ②将内容清单中 11 项 UNKNOWN 计数全部用 1.4.11 配置实算补齐；③对 mock_server / miniloop 做代码级能力核实（修正多处过时数字）；
> ④对 5 个参考项目做 zip 级许可复核（新增 pomelo MIT 发现）；⑤三版本差异矩阵受控词化 + 陈旧内容修正。
> 证据等级：**CONFIRMED / VERIFIED / STRONG_INFERENCE / INFERENCE / UNKNOWN**。禁止把 UNKNOWN 写成 CONFIRMED；数值/行为类结论只有 MuMu 实机运行后才可标 VERIFIED。

---

## 〇、MuMu 运行时取证通道（用户最高优先级硬约束，本次新增）

### 0.1 本机环境实测（CONFIRMED，2026-10-02 实际探测，非假设）

| 探测项 | 实测结果 |
|---|---|
| MuMu 安装 | ✅ 已安装（注册表 DisplayName=MuMu模拟器，Version=6.6.4.0，InstallLocation=`D:\MuMuPlayer`，引擎 `D:\MuMuPlayer\nx_main\MuMuNxMain.exe`） |
| 可启动 | ✅ 实例 0「MuMu安卓设备」（Android 12.0, hyperv_enabled）已实际启动成功（mumu-cli launch，errcode=0，player_state=start_finished） |
| adb | ✅ `D:\ADB\platform-tools\adb.exe`（在 PATH，v36.0.2）；`adb connect 127.0.0.1:16384` 成功 → 设备序列号 `127.0.0.1:16384`，product:rubens，model:22041211A，Android 12，transport_id 1 |
| 实例 1 | 「MuMu安卓设备-1」存在（未启动，Android 12，13.8GB 磁盘） |
| 已装入包 | `com.shiyue.dldl.ewan` = versionName **1.3.0**（versionCode 25，2026-09-29 装）；`com.shiyue.dldl.ewan.qihoo` = versionName **1.4.9**（versionCode 44，2026-10-01 更新） |
| **1.4.11** | ⚠ **尚未装入模拟器**（补丁包位于 `patched\jstm_1411_fakelogin_aligned.apk`）→ 列为 **Phase 1 第一项前置任务** |

> 旁证：装入的 1.3.0 包 versionName 即 "1.3.0"，与「1.3.0=工程代号」判断互证（内部 NOW_VERSION=35 仍为 CONFIRMED）。

### 0.2 证据通道定义（已写入 `systems_master.json` 的 `_meta.mumu_runtime_evidence_channel` 与 `systems_master.md` 头部）

- **VERIFIED 的唯一来源** = 原版/补丁客户端在 MuMu 中实际运行 + mock_server 联调。
- **采集流程**：启动 MuMu 实例 → adb 安装/启动 1.4.11 补丁包 → 客户端 URL 配置指向本机 mock_server（TCP 9000）→ 抓协议 dump（frida hook / 客户端日志 / 抓包）→ 记录 UI 显示值与回包字段 → 与服务器应答比对。
- 静态 APK 提取只能作 **CONFIRMED（存在性/结构）**；数值真实性一律需 MuMu 取证。已为 **45/124** 系统打标 `needs_mumu_runtime: true`。

### 0.3 等 MuMu 环境就绪后需补抓的运行时数据清单（Phase 1 前置，详见 `server_capability_verified.md` §十 与 `jstm_game_content_inventory_counts.md` 末节）

- **环境（E1–E4）**：安装 1.4.11 补丁包到 MuMu；URL 指向 mock_server；启动客户端；打通抓包链路。
- **协议实值（R1–R12）**：登录/建角/登角/进场景/移动/战斗/背包/商城/邮件/排行/任务等关键命令的 CS/SC 报文与字段实值。
- **数值标定（V1–V12）**：怪物 HP/攻防/暴击、伤害公式、经验与金币产出、掉落结果与概率、装备属性与强化增量、伙伴属性、战力公式结果 vs UI、经验表、成长族每阶属性。
- **差异清单**：mock_server 当前实现 vs 实机回包逐项比对（当前为空，待 Phase 1 填充）。

---

## A. 当前项目结构（CONFIRMED，目录实测）

```
DSH/
├── anzbao/            3 个原版 APK：jstm_142165.apk=1.4.11(主) / jstm.apk=1.4.9 / dldlJl.apk=1.3.0
├── patched/           补丁 APK：jstm_1411_fakelogin_aligned.apk(1.4.11) / jstm_fakelogin* / jstm_minloop* / jstm_solo* …
├── server/            ★ mock_server.py(18,506 行) + minloop/ + cfg*(231/285/245/245) + world/ + state/roles.db + 各 *_config.json
├── analysis/          审计产物 ★（本报告 + version_compare/ + jstm_game_systems/ + client_server_matrix.md
│                      + server_capability_verified.md + reference_projects_verified.md + 1.4.9/ + jstm_1.4.9/ + server_reference/）
├── docs/              ARCHITECTURE / TECHNICAL / RESTORE / SUMMARY / HANDOVER / PLAN
├── protocol/          cmd_table.json(1643) / fields.json(3553) / cmd_classes.json / registry_classes.json / manual.md
├── tools/             600+ 审计/修复/验证脚本 + jadx/frida/ljd/dex/apktool 逆向工具链
├── tests/             1.4.9 回归文档 + 稳定性脚本
├── cankao/            5 个参考工程 zip（Survive / kongkongxiyou / CXEngine / MahatmaComeBack / ChivalrousMan）
├── _tmp_cfg/          1.4.11 config_*.luac 提取目录（305 文件）
├── _tmp_* 系列         按系统临时分析目录（fashion/halo/wedding/form/god/hero/battle/buff）
├── report/            100+ 轮次进展/验证报告；shots/(34) photo/(11) logs/ docs/
└── 根级 *.md          三包对比 / APK 鉴定 / 协议笔记 / 路线图
```

## B. 当前已实现的系统（服务端代码级核实，CONFIRMED by code）

依据 `analysis/server_capability_verified.md`（本轮从 mock_server.py 逐段核实的实测数字，替代先前过时口径）：

| 指标 | 实测值 | 先前声明 | 说明 |
|---|---|---|---|
| mock_server.py | **18,506 行** / 982KB | ~16k 行 | 实测 |
| 去重命令号 | **800 个**（if cmd==N 585 处 + 多分支展开） | ~1446 专用分支 | 计数口径差异，均属实 |
| `_UNSUPPORTED_ACTION_CMDS` | 空 frozenset | 0 | 一致 |
| `_GENERIC_DEFAULT_CMDS` | 空 frozenset | 0 | 一致 |
| SQLite 表 | **55 张**（54 用户表 + sqlite_sequence） | 47 张 | 实测修正 |
| /DSH_ADMIN 动作 | **44 个** | 17+ | 实测修正 |
| 端口 | TCP 9000 / HTTP 8080 | 同 | 一致 |
| 配置目录 | cfg=231 / cfg_kconst=285 / cfg_kconfig=245 / cfg_kconfig2=245 | — | 实测 |

**逐系统状态（55 项核实，节选）**：
- **代码结构 CONFIRMED（B 组，纯结构）**：登录/建角/登角/进场景/移动/背包/仓库/装备/任务/商城/黑市/邮件/排行/副本/挂机/签到/日常/成就/结拜/结婚/拍卖/法宝/翅膀/坐骑/魂兽/元神/神器/命格/椅子/时装/光环/符文/投资/BOSS/称号/阵法书 等。
- **⚠ 需 MuMu 运行时取证（A 组，数值真实性待实机）**：战斗数值（MON_STATS/KILL_REWARD/FALLBACK_DROPS 全 TEST_ONLY）、伤害公式（IMPLEMENTATION_FALLBACK）、装备/强化/洗练/宝石数值、伙伴/翅膀/坐骑/魂兽/元神/神器/命格每阶属性、`role_power()` 战力值 vs 客户端 UI、经验表 exp_max、掉落 bid/数量、商城实付。
- **UNKNOWN（C 组）**：技能学习/升级、魂骨、增幅、聊天频道实时广播、公会本体（多表 0 行）、NPC 对话 UI（setOpenNpc 未定义，客户端侧问题）。

## C. 客户端发现的全部系统（124 系统 / 18 分类）

`analysis/jstm_game_systems/systems_master.md/json`（本轮验证并补全：124 系统，18 分类 A–R 全覆盖，每系统 19 字段 + `category` + `needs_mumu_runtime`；`UI_files` 字段名已合规）。

| 分类 | 数量 | 分类 | 数量 |
|---|---|---|---|
| A.核心 | 9 | J.地图 | 2 |
| B.角色 | 7 | K.副本 | 5 |
| C.成长 | 7 | L.活动 | 15 |
| D.战斗 | 5 | M.社交 | 10 |
| E.装备 | 6 | N.商业/对抗 | 10 |
| F.伙伴 | 7 | O.GM | 1 |
| G.外观 | 10 | P.后台 | 2 |
| H.资源经济 | 12 | Q.隐藏 | 7 |
| I.任务 | 5 | R.未知 | 4 |

confidence 分布：CONFIRMED 50 / VERIFIED 49 / STRONG_INFERENCE 12 / INFERENCE 2 / UNKNOWN 11。未发现把 UNKNOWN 写成 CONFIRMED 的违规项。

## D. 三个 APK 的差异（24 维度差异矩阵，已刷新）

`analysis/version_compare/version_diff_matrix.md/json`（本轮：版本列受控词化【存在/不存在/未知】、变化列受控词化【新增/删除/修改/重命名/未知】、删除陈旧文本、assets 1.4.11 修正为存在、补全 flyup 模块）。

| 项 | 1.3.0 = dldlJl.apk | 1.4.9 = jstm.apk | 1.4.11 = jstm_142165.apk |
|---|---|---|---|
| 渠道 / NOW_VERSION | ewan/91CW / 35 | 360(qihoo) / 186 | baidu2 / 208 |
| 总条目 / .luac | 10,670 / 1,557 | 16,379 / 2,234 | 19,106 / 2,297 |
| config_*.luac / cmd_resolve | 168 / 89 | 227 / 122 | 233 / 124 |
| game 模块目录 / assets | 92 / 135.1MB | 116 / 241.3MB | 119 / 276.2MB |

- **24 个维度在三版本中均存在**（无整维度新增/删除），差异为维度内子项级。
- **1.3.0 独有**（找回对象）：模块 garden(庄园)/jingjie(境界)/moneytree(摇钱树)/xiulianhulu(修炼葫芦) + 配置表 config_holiday.luac。moneytree/garden 在 1.4.11 以 config_money_tree/config_garden_data 形式存在（改名/合并）；jingjie/xiulianhulu 在 1.4.11 的存废 → UNKNOWN（待确认）。
- **1.4.11 新增**：31 个模块（auction/blackmarketeer/chair/chief/crossdungeon/endless/footmark/friendback/godwar/gradebreak/guildrace/guildsecretarea/guildtarget/halo/jewelvip/kunshentower/loadres/mine/peakwar/scratcher/script/soulstar/sworn/treasure_plane/yuangu/yuanshen/battlevideo/actionanswer/animaequip/contact/flyup）+ 66 张配置表。
- 1.3.0 解包声明核实属实：`extracted/` 293 文件 / 6.95MB（164 张 config_*.luac + 90 个 cmd_resolve/all_proto + 4 个独有模块目录）；唯一路径偏差（实际在 `config/protocal/`）已在文档注明。
- 1.4.11 的 item/task/partner/shop 逐条计数仍未提取 → 该四格存在性 CONFIRMED、计数 UNKNOWN（1.4.9 的 3535/846/53/142 为 VERIFIED）。

## E. mock_server 当前能力（详见 server_capability_verified.md）

- 单体 Python + SQLite（55 表），多线程 TcpHandler，TCP 9000 + HTTP 8080。
- 协议层：pack_frame/FrameParser + `_sc_fields` 规格缓存 + AutoConstruct 规范编码；CS 命令 800 个去重实现，`_UNSUPPORTED_ACTION_CMDS`/`_GENERIC_DEFAULT_CMDS` 均为空。
- 业务层：单文件 if 链分发（核心逻辑）+ 全局兜底开关（默认关）；配置读取器覆盖 cfg(231)/kconst(285)/kconfig(245)/kconfig2(245) 四套来源。
- 数据层：55 表覆盖角色/资产/属性/背包/装备/任务/伙伴/多维成长/活动/市场/邮件/公会/挂机/结拜/结婚/拍卖等；`state/roles.db` 实库。
- 工程层：aoi.py / pathfind.py / power.py / battle.py / quest_spawn.py + world/（area/entities/move/ticker/jstm_bridge）。
- 管理：/DSH_ADMIN/* 44 个动作（状态/改等级/资产/物品/装备/配置重载等）。
- 局限：战斗数值 TEST_ONLY、战力/成长公式 INFERENCE、单进程 GIL、数值真实性全部待 MuMu 取证。

## F. miniloop 可借鉴能力（server/minloop）

- `min_loop_server.py`：**17 条 LOOP 命令**（README 的 11 为过时）+ ROLE_QUERIES 4 条；独立最小回环：登录→角色→场景→任务→打怪→结算→掉落→提交→奖励→背包。
- `selftest.py`：**145/145 PASS**（README 的 44 为过时；本轮用临时 DB 实跑，未碰 minloop.db）。
- `replay_real_frames.py` / `replay_stateful.py`：真机帧回放回归。
- 价值：兼容性度量尺与回归基座；"不猜、宁可空但合法"纪律可复用。局限：不实现 AOI/多人在线/商城/邮件/活动等横向系统；自检只验结构不验数值（数值一律 MuMu 取证）。

## G. 参考项目可借鉴能力（cankao/ 实际 5 个 zip，非 4 份）

`analysis/reference_projects_verified.md`（本轮 zip 级复核，含许可文件头原文确证）：

| 项目 | 技术栈 | 可借鉴（仅设计） | 不可采用 | 许可（本轮实测） |
|---|---|---|---|---|
| Survive | Lua(distrilua)+C .so+PHP 后台 | 服务组拆分、单线程多场景、AOI/寻路思想、buff/skill 组织、GM 后台 | aoi/astar/wordfilter 的 C 实现、协议/数值 | 无顶层 LICENSE；aoi.h/astar.h/wordfilter.h 内嵌 GPLv3（已读原文） |
| kongkongxiyou | Node.js+Pomelo+Cocos2d-JS | 按域切 handler、connector 网关、area+domain、任务状态机、Excel→JSON 管线 | handler 数值/任务链/掉落、exceldata 数值、route 串 | ★ **pomelo/lordofpomelo 框架=MIT（已读原文，新发现）**；自有游戏内容无 LICENSE；ExtJS 管理台传染 |
| CXEngine/YZXY | C++(CMake,cxluax)+Lua | share 共享层+独立 combat、addon 插件化、战斗框架骨架 | 战斗状态机/技能/怪物/quest/协议字段 | 无 LICENSE，仅借鉴设计 |
| MahatmaComeBack | 客户端 Cocos C++；**服务端 C#/.NET** | 客/服分离、.sql 集中建表思路 | 全部代码/.sql/美术 | **GPLv3（已读 LICENSE 原文）** |
| ChivalrousMan | 仅 Cocos C++ 客户端 | 传统 MMORPG 客户端流程、业务字段语义 | 客户端随机生成任务（错误示范）、泄露的 MySQL 凭据 | 无 LICENSE |

> 纪律重申：5 项目全部只能借鉴架构/模块/数据模型/工程经验；任何协议/数值/任务/装备/技能/怪物/属性/战斗规则都不得当作 JSTM 数据。JSTM 唯一权威源 = 3 个原版 APK + 实机运行结果。

## H. 客户端系统 → 服务器需求矩阵（124 行）

`analysis/client_server_matrix.md`（本轮补全：用户点名约 50 系统全覆盖，含装备洗练/宝石/魂骨/增幅/掉落/红点/UI状态/战力/伙伴培养/伙伴装备等新增行；每行 APK入口/协议/数据/服务端归属/状态五列齐全；状态列对 45 个系统追加 `⏳需MuMu取证` 图例标注）。节选：

| 系统 | APK 入口 | 协议 | 数据 | 服务端 | 状态 |
|---|---|---|---|---|---|
| 登录 | denglu_* | 1110 | accounts | login | ✅ 已实现 |
| 角色 | role_ctrl/role_data | 10301-10306 | roles/role_attr | role | ✅ 已实现 |
| 任务 | mission_* | 12400-12421 | missions | task | ✅ 已实现 |
| 战斗 | battle_* | 20000 族 | (内存) | battle.py | ⚠ 已实现 ⏳需MuMu取证 |
| 背包 | backpack_* | 10500-10593 | bag_items | inventory | ✅ 已实现 |
| 装备/强化/洗练/宝石 | backpack/equip | 105xx/106xx | bag_items/equip | equipment | ⚠ 已实现 ⏳需MuMu取证 |
| 商城 | shop_* | 12801-12856 | mall_bought | shop | ✅ 已实现 ⏳需MuMu取证(实付) |
| 伙伴 | hero_ctrl | 11215/11210 | role_heros | partner | ⚠ 部分 ⏳需MuMu取证 |
| 翅膀/魂骨/神器/命格/阵法等 | 各自 ctrl | 各自 | 各 role_* 表 | 各成长系统 | ⚠ 部分 ⏳需MuMu取证 |
| 结婚/结拜/跨服 | marry/jiebai/race | 各 | 部分落表 | social | ⚠ 部分/未实现 ⏳需MuMu取证 |

## I. 系统依赖图

`analysis/jstm_game_systems/system_dependency_graph.md`（已存在，本轮确认仍成立）：

```
角色 → 等级 → 经验 → 属性(AttributeService) → 战力(PowerService) → 客户端同步
装备 → 属性 → 战力     伙伴 → 属性 → 战力
翅膀/坐骑/法宝/命格/神器/元神/时装/图腾/椅子/五行/强化/升级 → 属性 → 战力
阵法 → 伙伴 → 战斗    任务 → 条件(ConditionService) → 奖励(RewardService)
战斗 → 奖励(EXP/货币/掉落) → 任务进度 → 战斗循环
商城/活动 → 货币(CurrencyService) → 扣费 → RewardService → 发货（幂等 reference_id）
所有系统 → PersistenceService(SQLite) → ClientSync
```

红线：任一成长系统禁止自己算属性/战力，必须收敛 AttributeService → PowerService → Persistence → ClientSync；资产变动禁止绕过 CurrencyService/RewardService；奖励必须带 reference_id 防重；原版公式未知一律标 JSTMCompatiblePowerFormula/INFERENCE 留替换点。

## J. 未实现系统清单（42 项）

`analysis/jstm_game_systems/unimplemented_systems.md`（本轮 34→42 项，与 json `is_not_impl` 双向差集为空；表格新增"运行时取证"列并给涉及数值/掉落/奖励的条目标 `⏳需MuMu取证`）。节选：版本/资源更新、士气、战斗回放、神魔战、伙伴图鉴/羁绊、引导、秘境、其余副本（神界/封印恶魔/SMJZ/金银塔）、刮刮乐、节日/运营活动、答题、竞猜、夺宝、回归、充值活动、许愿、送花、宴会、跨服、采矿、攻城、押镖、金银塔、跨服后台、封印、修罗、首席、神灵、神龙、气球、丹药战（UNKNOWN）、运营入口 33/34/37/40/101/103（UNKNOWN）、染色（UNKNOWN）等。

## K. UNKNOWN 系统清单（无法确认，勿当事实）

- **11 个系统 confidence=UNKNOWN**（Dan War 丹药战、YunYing Ops 运营入口、Color 染色等）——有配置文件名但系统语义未确认。
- **1.4.11 item/task/partner/shop 逐条计数**：存在性 CONFIRMED，计数未提取。
- **战力公式 / 各成长系统数值公式**：原版权威公式未知，mock_server 为 INFERENCE 兼容实现（role_power()），需 MuMu 取证替换。
- **战斗数值（怪物 HP/攻防/EXP/掉落）**：APK 无此数据，当前 TEST_ONLY/占位。
- **jingjie/xiulianhulu 在 1.4.11 的存废**：1.3.0 独有模块的去向待 1.4.11 全量配置确认。
- **1.4.11 在 MuMu 中的实际运行状态**：尚未装入，属"待安装/未验证"。
- **若干礼包/掉落 ID 指向、珍宝商城 45 件商品数据**：原版服务端数据不在 APK。

## L. 推荐实施路线（Phase 1 第一项 = MuMu 联调前置，硬约束）

```
Phase 0   ✅ 已完成（本报告）
Phase 1   MuMu + mock_server 联调环境（第一项前置）：安装 1.4.11 补丁包 → 跑通 → 抓 R1-R12 协议实值 + V1-V12 数值标定
Phase 2   Server Core 拆分（18,506 行 if 链按域拆 handler，借鉴 kongkongxiyou 分层；不丢已验证协议）
Phase 3   Account/Login/Role/Scene（已完成，保留）
Phase 4   Level/EXP/Attribute/Power（服务化；INFERENCE 公式留替换点，MuMu 取证后替换）
Phase 5   Monster/Battle/Reward（战斗数值取证优先；RewardService 统一）
Phase 6   Inventory/Item/Currency（统一 currency/reward/item 服务）
Phase 7   Equipment/Enhancement/Gem/符文
Phase 8   Skill
Phase 9   Partner（完善上阵/装备/技能/培养）
Phase 10  Wing/Soulbone/Ride/Lingshou/Fashion 等外观成长
Phase 11  Artifact(神器)/Destiny(命格)/Formation(阵法)/Amplification(增幅)
Phase 12  Dungeon/AFK（副本/挂机完整闭环）
Phase 13  Shop/Package/Activity（统一 Shop/Package/ActivityService）
Phase 14  Social/Guild/Mail/Ranking（结婚/结拜/公会/跨服补全）
Phase 15  GM Manager（独立 gm_manager，调统一 Service，安全+审计；复用 /DSH_ADMIN 44 动作扩展）
Phase 16  内容填充（1.4.11 全量配置入库）
Phase 17  1.4.11 全场景 Regression
```

执行纪律（继承既有）：垂直闭环优先、每系统必建测试、1.4.11 为唯一验收、不伪装 INFERENCE 为 CONFIRMED、**数值类结论必须 MuMu 取证后才可 VERIFIED**。

## M. 预计每阶段工作量（相对，8h 日当量；含 MuMu 取证前置）

| Phase | 内容 | 预估 | 备注 |
|---|---|---|---|
| 1 | MuMu 联调环境 + 协议实值 + 数值标定 | **2-4 天** | 硬约束前置；出 V1-V12 标定表与差异清单 |
| 2 | 拆 handler/模块化 | 2-3 天 | 高风险高收益，需回归保护 |
| 3-4 | 核心/角色/属性/战力服务化 | 1-2 天 | 战力公式待 MuMu 替换 |
| 5 | 战斗+奖励 | **3-5 天** | 数值取证是硬骨头 |
| 6 | 背包/货币/装备/强化/宝石 | 3-4 天 | 复用现有表 |
| 7-8 | 技能/伙伴 | 2-3 天 | |
| 9-11 | 外观成长/神器/命格/阵法/增幅 | 3-4 天 | 大量 config_* 表 |
| 12 | 副本/挂机 | 2-3 天 | |
| 13 | 商城/礼包/活动 | 2-3 天 | |
| 14 | 社交/公会/跨服 | 3-4 天 | 结婚/结拜等新系统 |
| 15 | GM Manager | 2-3 天 | 复用 /DSH_ADMIN 扩展 |
| 16-17 | 内容填充+回归 | 3-4 天 | 1.4.11 全量 |

**合计：约 32-44 人日** 到"1.4.11 可完整体验"。最大不确定性 = 战斗数值与成长公式的 MuMu 取证难度（可能上升）。

---

## 结论

PHASE 0 复核完成：3 个 APK（含 1.3.0 全量解包）、mock_server（代码级）、miniloop（145 自检）、5 个参考工程（zip 级许可复核）、124 系统百科、42 项未实现、124 行需求矩阵、24 维度版本差异、11 项 UNKNOWN 计数全部补齐。**MuMu 运行时取证通道已建立并实测环境就绪**（adb 127.0.0.1:16384 可达），1.4.11 装入模拟器为 Phase 1 第一项任务。现有协议对接（1.4.9 100% CS/SC、1.4.11 已连通 mock_server）是最大资产，应保留并演进为多模块统一 Game Core。

### PHASE 0 交付物索引

| 文件 | 说明 |
|---|---|
| `analysis/PHASE0_AUDIT.md` | 本报告（A–M 全量审计 + MuMu 取证通道） |
| `analysis/version_compare/version_diff_matrix.md` / `.json` | 三版本 24 维度差异矩阵（受控词化） |
| `analysis/version_compare/1.3.0|1.4.9|1.4.11/inventory.md` | 三版本资源盘点（1.3.0 已解包核实） |
| `analysis/jstm_game_systems/systems_master.md` / `.json` | 系统百科（124 系统，18 分类，19 字段 + MuMu 取证通道 meta） |
| `analysis/jstm_game_systems/unimplemented_systems.md` | 未实现系统清单（42 项 + 运行时取证列） |
| `analysis/jstm_game_systems/system_dependency_graph.md` | 系统依赖图 |
| `analysis/client_server_matrix.md` | 客户端系统→服务端需求矩阵（124 行） |
| `analysis/jstm_game_content_inventory.json` / `_counts.md` | 完整内容清单（11 项 UNKNOWN 全补齐 + 计数明细 + MuMu 取证待办） |
| `analysis/server_capability_verified.md` | mock_server/miniloop 代码级能力核实（含 Phase 1 前置清单 E/R/V） |
| `analysis/reference_projects_verified.md` | 5 参考项目 zip 级许可与可借鉴复核 |

# [PHASE 0 AUDIT COMPLETE]
# [WAITING FOR IMPLEMENTATION]
