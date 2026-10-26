# JSTM 游戏系统百科 systems_master

> PHASE 0 审计产物。主目标版本 1.4.11（`_tmp_cfg` 配置表 + `_tmp_*` Lua 模块 + mock_server 实现）。
> 证据等级：CONFIRMED / VERIFIED / STRONG_INFERENCE / INFERENCE / UNKNOWN。UNKNOWN 不得当作事实。
> 机读版本：`systems_master.json`（124 个系统）。


## MuMu 运行时取证通道（mumu_runtime_evidence_channel）

> PHASE 0 审计新增硬约束，2026-10-02 写入。

**定位：** MuMu 运行时取证通道 = **VERIFIED 级证据的唯一来源**。APK 静态提取（配置表名/Lua 模块/协议号/DB 表结构）可作为 CONFIRMED；但数值字段、战斗行为、掉落结果、UI 显示值、回包内容必须经本机 MuMu 模拟器跑 1.4.11 客户端 + mock_server 联调后才能标 VERIFIED。

**采集流程：**
1. 启动 MuMu 12 实例（实例 0 `MuMu安卓设备`，Android 12 / hyperv）。
2. `adb connect 127.0.0.1:16384`（adb: `D:\ADB\platform-tools\adb.exe`，亦在 PATH）；设备序列号 `127.0.0.1:16384`，product `rubens` / model `22041211A`，transport_id 1。
3. 安装并启动 1.4.11 补丁包：`C:\Users\xu\Desktop\DSH\patched\jstm_1411_fakelogin_aligned.apk`（**当前尚未安装 → 待安装**）。
4. 客户端 URL/host 配置指向本机 mock_server（TCP 9000）。
5. 抓协议 dump：客户端日志 / frida hook send/recv / 网络抓包。
6. 记录 UI 显示值与回包字段，与服务器应答逐字段比对。

**实测环境（CONFIRMED 级探测记录）：**
- MuMu 12 已安装（注册表 `MuMu模拟器 6.6.4.0`，安装目录 `D:\MuMuPlayer`，引擎 `MuMuNxMain.exe`）。
- 实例 0 已启动；实例 1 `MuMu安卓设备-1` 存在但未启动。
- 已装包：`com.shiyue.dldl.ewan` = versionName **1.3.0** (versionCode 25, 2026-09-29)；`com.shiyue.dldl.ewan.qihoo` = versionName **1.4.9** (versionCode 44, 2026-10-01)。
- **1.4.11 尚未装入模拟器**；在装入并跑通联调前，所有数值/行为类结论不得从 INFERENCE/STRONG_INFERENCE 升级为 VERIFIED。

**标注规则：** 凡实现依赖真实运行数据（战斗数值、掉落表、装备属性、伙伴数值、怪物数值、战力公式、经验曲线、UI 显示值、商城价格等）的系统，在矩阵/未实现清单中标注 **「需 MuMu 运行时取证」**。

**Phase 1 前置：** 搭建 MuMu + mock_server 联调环境 = Phase 1 第一项任务。

---
| 分类 | 系统数 |
|---|---|
| A. 核心系统 | 9 |
| B. 角色系统 | 7 |
| C. 成长系统 | 7 |
| D. 战斗系统 | 5 |
| E. 装备系统 | 6 |
| F. 伙伴系统 | 7 |
| G. 外观系统 | 10 |
| H. 资源经济 | 12 |
| I. 任务系统 | 5 |
| J. 地图系统 | 2 |
| K. 副本系统 | 5 |
| L. 活动系统 | 15 |
| M. 社交系统 | 10 |
| N. 商业系统 / 对抗 | 10 |
| O. GM 系统 | 1 |
| P. 后台系统 | 2 |
| Q. 隐藏/未归类系统 | 7 |
| R. 未知系统 | 4 |
| **合计** | **124** |

---

## A. 核心系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_CORE_001 | Account Login | 帐号登录, 账号, 登录 | denglu_ctrl.luac | CS_1110 AccountLogin, CS_1199 heartbeat, CS_10001 FirstPack | config_login.luac, config_client.luac | implemented | CMD_NAMES + roles.db + verified context / CONFIRMED |
| SYS_CORE_002 | Role Creation | 创建角色 | role_ctrl.luac | CS_10101 RoleCreate, CS_10102 RoleLogin, CS_10103 RoleReLogin | config_role_career.luac, config_role_face.luac, config_role_stock.luac | implemented | CMD_NAMES + roles.db / CONFIRMED |
| SYS_CORE_003 | Role Base/Init | 角色基础信息, 角色初始化 | role_ctrl.luac | SC_10300, SC_10301, SC_10302, SC_10303 | config_game_data.luac, config_role_attr.luac, config_role_attribute.luac | implemented | ROLE_DEFAULTS + roles.db / CONFIRMED |
| SYS_CORE_004 | Role Login | 角色进入游戏, 登录角色 | denglu_ctrl.luac | CS_10102, SC_1110 account roles | config_login.luac | implemented | CMD_NAMES / CONFIRMED |
| SYS_CORE_005 | Scene & Movement | 场景, 移动, 寻路, 自动寻路 | scene_controller.luac | CS_10200 RoleEnter, CS_10201, CS_10204, CS_10205 | config_map.luac, config_map_block.luac, config_map_npc.luac, config_map_icon_pos.luac, config_world_map.luac, config_trap.luac | implemented | pathfind.py/map_block.json / CONFIRMED |
| SYS_CORE_006 | Protocol/Network Layer | 网络协议层, 封包解包 | protocalrulesmgr.luac | all | — | implemented | protocol registry present / CONFIRMED |
| SYS_CORE_007 | Version/Resource Update | 版本更新, 资源下载 | xiazai (function 25000) | 20100 | config_client.luac, config_notice.luac | client-only / not hooked | file_update_1411.luac + function id 25000 / VERIFIED |
| SYS_CORE_008 | Red Dot / Badge 红点 | 红点, reddot, red_point, badge, notice | UNKNOWN | — | — | not implemented (unknown) | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |
| SYS_CORE_009 | UI State Sync UI状态 | UI状态, uistate, ui_state, ui_status | UNKNOWN | — | — | not implemented (unknown) | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |

### SYS_CORE_001 — Account Login
- **aliases**: 帐号登录, 账号, 登录
- **version**: 1.4.11
- **client_entry**: denglu_ctrl.luac
- **lua_modules**: denglu_ctrl.luac, login.luac
- **protocols**: CS_1110 AccountLogin, CS_1199 heartbeat, CS_10001 FirstPack
- **config_files**: config_login.luac, config_client.luac
- **data_files**: accounts table, roles table
- **UI_files**: login panel
- **dependencies**: protocol, network
- **server_state**: implemented
- **database_state**: roles,accounts tables present
- **related_systems**: Role Creation, Role Login
- **evidence**: CMD_NAMES + roles.db + verified context
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_CORE_002 — Role Creation
- **aliases**: 创建角色
- **version**: 1.4.11
- **client_entry**: role_ctrl.luac
- **lua_modules**: role_ctrl.luac
- **protocols**: CS_10101 RoleCreate, CS_10102 RoleLogin, CS_10103 RoleReLogin
- **config_files**: config_role_career.luac, config_role_face.luac, config_role_stock.luac
- **data_files**: roles table
- **UI_files**: role create panel
- **dependencies**: Account Login
- **server_state**: implemented
- **database_state**: roles table present
- **related_systems**: Account Login
- **evidence**: CMD_NAMES + roles.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_CORE_003 — Role Base/Init
- **aliases**: 角色基础信息, 角色初始化
- **version**: 1.4.11
- **client_entry**: role_ctrl.luac
- **lua_modules**: role_ctrl.luac, denglu_ctrl.luac
- **protocols**: SC_10300, SC_10301, SC_10302, SC_10303
- **config_files**: config_game_data.luac, config_role_attr.luac, config_role_attribute.luac
- **data_files**: roles table, role_attr table, role_assets table
- **dependencies**: Role Login, Scene
- **server_state**: implemented
- **database_state**: roles,role_attr,role_assets present
- **currencies**: gold,coin,coupon,experience,sinew
- **related_systems**: Role Login, Assets/Economy, Role Attr
- **evidence**: ROLE_DEFAULTS + roles.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_CORE_004 — Role Login
- **aliases**: 角色进入游戏, 登录角色
- **version**: 1.4.11
- **client_entry**: denglu_ctrl.luac
- **lua_modules**: denglu_ctrl.luac
- **protocols**: CS_10102, SC_1110 account roles
- **config_files**: config_login.luac
- **data_files**: roles table
- **UI_files**: role select
- **dependencies**: Account Login
- **server_state**: implemented
- **database_state**: roles present
- **related_systems**: Account Login, Role Base/Init
- **evidence**: CMD_NAMES
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_CORE_005 — Scene & Movement
- **aliases**: 场景, 移动, 寻路, 自动寻路
- **version**: 1.4.11
- **client_entry**: scene_controller.luac
- **lua_modules**: scene_controller.luac
- **protocols**: CS_10200 RoleEnter, CS_10201, CS_10204, CS_10205
- **config_files**: config_map.luac, config_map_block.luac, config_map_npc.luac, config_map_icon_pos.luac, config_world_map.luac, config_trap.luac
- **data_files**: roles.scene_id/x/y, map_block.json
- **UI_files**: scene/UI, minimap
- **dependencies**: Role Login, Network, pathfind
- **server_state**: implemented
- **database_state**: roles scene/x/y persisted
- **related_systems**: Role Base/Init, Team
- **evidence**: pathfind.py/map_block.json
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_CORE_006 — Protocol/Network Layer
- **aliases**: 网络协议层, 封包解包
- **version**: 1.4.11
- **client_entry**: protocalrulesmgr.luac
- **lua_modules**: protocalrulesmgr.luac
- **protocols**: all
- **data_files**: cmd_table.json, cmd_classes.json, fields.json
- **server_state**: implemented
- **related_systems**: all
- **evidence**: protocol registry present
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_CORE_007 — Version/Resource Update
- **aliases**: 版本更新, 资源下载
- **version**: 1.4.11
- **client_entry**: xiazai (function 25000)
- **lua_modules**: file_update_1411.luac
- **protocols**: 20100
- **config_files**: config_client.luac, config_notice.luac
- **UI_files**: downloader
- **server_state**: not implemented (client-only)
- **related_systems**: Account Login
- **evidence**: file_update_1411.luac + function id 25000
- **confidence**: VERIFIED
- **implementation_status**: client-only / not hooked

### SYS_CORE_008 — Red Dot / Badge 红点
- **aliases**: 红点, reddot, red_point, badge, notice
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: all UI
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **notes**: PHASE0 audit-flagged item; no dedicated red-dot framework module located. config_function_notice referenced inside Guide system.

### SYS_CORE_009 — UI State Sync UI状态
- **aliases**: UI状态, uistate, ui_state, ui_status
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: Protocol/Network
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **notes**: PHASE0 audit-flagged item; no dedicated UI-state push/sync module located (generic SC pushes cover per-system state).

---

## B. 角色系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_ROLE_001 | Role Attribute | 角色属性, 属性加点 | role (function 5000) | SC_10301/10302/10303, CS_10331, CS_10333 | config_role_attr.luac, config_role_attribute.luac, config_attr.luac, _attr.json, _attr_meta.json, _role_attr.json | implemented ⏳需MuMu取证 | role_attr.db + _attr_data.json / CONFIRMED |
| SYS_ROLE_002 | Career/Job | 职业 | menpai (function 10) |  | config_role_career.luac, config_role_cost.luac | implemented (basic) | config_role_career / VERIFIED |
| SYS_ROLE_003 | Title System | 称号 | title? |  | config_title.luac | implemented | role_title.db / CONFIRMED |
| SYS_ROLE_004 | VIP System | VIP, 贵族 | super_vip (function 44) |  | config_vip.luac, config_vip_ernie_data.luac, config_charge_eyou.luac | partial (fields tracked, no full VIP logic) | vip fields in ROLE_DEFAULTS; no dedicated table / VERIFIED |
| SYS_ROLE_005 | Experience/Level | 经验, 升级, 等级礼包 | jitici? | CS_14600, CS_14601 level gift | config_role_cost.luac, config_guider_up.luac, config_fly_up.luac | implemented ⏳需MuMu取证 | levgift_got.db + CS_14600/14601 / CONFIRMED |
| SYS_ROLE_006 | Avatar/Head & Chat Bubble | 头像框, 聊天气泡 | set? |  | config_head_surface.luac, config_chat_bubble.luac, config_biaoqing.luac | partial | ROLE_DEFAULTS head_bid/chat_bubble / VERIFIED |
| SYS_ROLE_007 | Combat Power 战力 | 战力, power, zhanli, fight_power | UNKNOWN | — | — | not implemented (unknown) ⏳需MuMu取证 | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |

### SYS_ROLE_001 — Role Attribute
- **aliases**: 角色属性, 属性加点
- **version**: 1.4.11
- **client_entry**: role (function 5000)
- **lua_modules**: role_ctrl.luac
- **protocols**: SC_10301/10302/10303, CS_10331, CS_10333
- **config_files**: config_role_attr.luac, config_role_attribute.luac, config_attr.luac, _attr.json, _attr_meta.json, _role_attr.json
- **data_files**: role_attr table
- **UI_files**: attr assign panel
- **dependencies**: Role Base/Init
- **server_state**: implemented
- **database_state**: role_attr present
- **currencies**: attr_point
- **related_systems**: Role Base/Init, Skill
- **evidence**: role_attr.db + _attr_data.json
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 属性公式/加点收益

### SYS_ROLE_002 — Career/Job
- **aliases**: 职业
- **version**: 1.4.11
- **client_entry**: menpai (function 10)
- **lua_modules**: role_ctrl.luac, menpai?
- **protocols**: 
- **config_files**: config_role_career.luac, config_role_cost.luac
- **data_files**: roles.career
- **UI_files**: career select
- **dependencies**: Role Creation
- **server_state**: implemented
- **database_state**: roles.career col
- **related_systems**: Role Creation, Role Attribute
- **evidence**: config_role_career
- **confidence**: VERIFIED
- **implementation_status**: implemented (basic)

### SYS_ROLE_003 — Title System
- **aliases**: 称号
- **version**: 1.4.11
- **client_entry**: title?
- **lua_modules**: rank_title.luac
- **protocols**: 
- **config_files**: config_title.luac
- **data_files**: role_title table
- **UI_files**: title list
- **dependencies**: Role Base/Init, Rank
- **server_state**: implemented
- **database_state**: role_title present
- **rewards**: 称号
- **related_systems**: Rank, Achievement
- **evidence**: role_title.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_ROLE_004 — VIP System
- **aliases**: VIP, 贵族
- **version**: 1.4.11
- **client_entry**: super_vip (function 44)
- **protocols**: 
- **config_files**: config_vip.luac, config_vip_ernie_data.luac, config_charge_eyou.luac
- **data_files**: roles.is_vip/vip_lev/vip_exp cols
- **UI_files**: VIP panel
- **dependencies**: Recharge, Economy
- **server_state**: partial
- **database_state**: role_assets.vip_exp + role fields only (no vip_* table)
- **rewards**: VIP礼包
- **currencies**: vip_exp
- **related_systems**: Recharge, Level Gift
- **evidence**: vip fields in ROLE_DEFAULTS; no dedicated table
- **confidence**: VERIFIED
- **implementation_status**: partial (fields tracked, no full VIP logic)

### SYS_ROLE_005 — Experience/Level
- **aliases**: 经验, 升级, 等级礼包
- **version**: 1.4.11
- **client_entry**: jitici?
- **protocols**: CS_14600, CS_14601 level gift
- **config_files**: config_role_cost.luac, config_guider_up.luac, config_fly_up.luac
- **data_files**: roles.lev/exp, levgift_got table
- **UI_files**: level up panel, gift panel
- **dependencies**: Role Base/Init
- **server_state**: implemented
- **database_state**: levgift_got present
- **rewards**: 等级礼包
- **currencies**: exp
- **related_systems**: Level Gift, Role Attribute, Growth
- **evidence**: levgift_got.db + CS_14600/14601
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 经验曲线/升级数值

### SYS_ROLE_006 — Avatar/Head & Chat Bubble
- **aliases**: 头像框, 聊天气泡
- **version**: 1.4.11
- **client_entry**: set?
- **protocols**: 
- **config_files**: config_head_surface.luac, config_chat_bubble.luac, config_biaoqing.luac
- **data_files**: roles.head_bid/chat_bubble cols
- **UI_files**: avatar/bubble select
- **server_state**: partial
- **database_state**: role fields only, no dedicated table
- **related_systems**: Chat, Appearance
- **evidence**: ROLE_DEFAULTS head_bid/chat_bubble
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_ROLE_007 — Combat Power 战力
- **aliases**: 战力, power, zhanli, fight_power
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: Role Attribute
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: PHASE0 audit-flagged item; no dedicated zhanli/power calc module located. Power likely derived from role_attr on fly. [需 MuMu 运行时取证] 战力计算公式

---

## C. 成长系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_GROWTH_001 | Skill System | 技能 | skill (function 1000) | CS_10401..10406, CS_20012 skill_play | config_skill.luac, config_skill_magic.luac, config_skill_scene.luac, config_skill_talent.luac, config_skill_trigger.luac, config_skill_xiulian.luac, config_skill_bullet.luac, skill_bids.json | implemented (battle integration) ⏳需MuMu取证 | skill_bids.json + battle chain verified / CONFIRMED |
| SYS_GROWTH_002 | Talent/天赋 | 天赋 | skill (function 1000) |  | config_skill_talent.luac, buff_tianfu_tips.luac | partial (config only) | config_skill_talent + buff_tianfu_tips / VERIFIED |
| SYS_GROWTH_003 | Practice/修炼 (Buff) | 修炼, 修为 | cultivate |  | config_skill_xiulian.luac, config_buff_data.luac, config_insight.luac | implemented (buff persistence) | role_buffs.db + config_skill_xiulian / CONFIRMED |
| SYS_GROWTH_004 | Buff System | Buff | battle buff | relay SC_20012/20013 buff | config_buff_data.luac | implemented | role_buffs.db + _tmp_buff modules / CONFIRMED |
| SYS_GROWTH_005 | Morale 士气 | 士气 | ?? |  | config_morale.luac, config_hero_morale.luac | client-config only | config_morale + config_hero_morale only / STRONG_INFERENCE |
| SYS_GROWTH_006 | Soul Bone 魂骨 | 魂骨, hun_gu, soulbone | UNKNOWN | — | — | not implemented (unknown) | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |
| SYS_GROWTH_007 | Augment / Amplify 增幅 | 增幅, zengfu, augment | UNKNOWN | — | — | not implemented (unknown) | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |

### SYS_GROWTH_001 — Skill System
- **aliases**: 技能
- **version**: 1.4.11
- **client_entry**: skill (function 1000)
- **lua_modules**: skill_act.luac
- **protocols**: CS_10401..10406, CS_20012 skill_play
- **config_files**: config_skill.luac, config_skill_magic.luac, config_skill_scene.luac, config_skill_talent.luac, config_skill_trigger.luac, config_skill_xiulian.luac, config_skill_bullet.luac, skill_bids.json
- **data_files**: role_form? / role_heros skill bind
- **UI_files**: skill panel
- **dependencies**: Partner, Battle
- **server_state**: implemented
- **related_systems**: Battle, Talent
- **evidence**: skill_bids.json + battle chain verified
- **confidence**: CONFIRMED
- **implementation_status**: implemented (battle integration)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 技能伤害系数/成长

### SYS_GROWTH_002 — Talent/天赋
- **aliases**: 天赋
- **version**: 1.4.11
- **client_entry**: skill (function 1000)
- **protocols**: 
- **config_files**: config_skill_talent.luac, buff_tianfu_tips.luac
- **UI_files**: talent panel
- **dependencies**: Skill
- **server_state**: partial
- **related_systems**: Skill, Buff
- **evidence**: config_skill_talent + buff_tianfu_tips
- **confidence**: VERIFIED
- **implementation_status**: partial (config only)

### SYS_GROWTH_003 — Practice/修炼 (Buff)
- **aliases**: 修炼, 修为
- **version**: 1.4.11
- **client_entry**: cultivate
- **lua_modules**: buff_manager.luac, _cfg_buff.luac
- **protocols**: 
- **config_files**: config_skill_xiulian.luac, config_buff_data.luac, config_insight.luac
- **data_files**: role_buffs table
- **UI_files**: cultivate panel
- **dependencies**: Skill
- **server_state**: implemented
- **database_state**: role_buffs present
- **related_systems**: Skill, Buff
- **evidence**: role_buffs.db + config_skill_xiulian
- **confidence**: CONFIRMED
- **implementation_status**: implemented (buff persistence)

### SYS_GROWTH_004 — Buff System
- **aliases**: Buff
- **version**: 1.4.11
- **client_entry**: battle buff
- **lua_modules**: buff_manager.luac, buff_item.luac, buff_vo.luac, buff_tips.luac, _cfg_buff.luac
- **protocols**: relay SC_20012/20013 buff
- **config_files**: config_buff_data.luac
- **data_files**: role_buffs table
- **UI_files**: buff bar
- **dependencies**: Battle
- **server_state**: implemented
- **database_state**: role_buffs present
- **related_systems**: Battle, Practise
- **evidence**: role_buffs.db + _tmp_buff modules
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_GROWTH_005 — Morale 士气
- **aliases**: 士气
- **version**: 1.4.11
- **client_entry**: ??
- **protocols**: 
- **config_files**: config_morale.luac, config_hero_morale.luac
- **dependencies**: Battle, Partner
- **server_state**: not implemented
- **related_systems**: Battle, Partner
- **evidence**: config_morale + config_hero_morale only
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_GROWTH_006 — Soul Bone 魂骨
- **aliases**: 魂骨, hun_gu, soulbone
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: Role, Equipment
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **notes**: PHASE0 audit-flagged item; no config_hungu / soulbone module located in JSTM 1.4.11 inventory.

### SYS_GROWTH_007 — Augment / Amplify 增幅
- **aliases**: 增幅, zengfu, augment
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: Role Attribute
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **notes**: PHASE0 audit-flagged item; no dedicated augment module located. Attribute growth may be folded into role_attr.

---

## D. 战斗系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_BATTLE_001 | Turn-based Battle | 回合制战斗, 怪物 | battle_ctrl.luac | CS_20002, SC_20010, SC_20012, SC_20013, CS_20014, SC_20020 | config_battle.luac, config_combat.luac, config_fight.luac, config_mon_data.luac | implemented ⏳需MuMu取证 | battle.py + protocol_index five-cmd chain verified on real device / CONFIRMED |
| SYS_BATTLE_002 | Auto-battle / AFK | 挂机, 自动战斗 | automate (function 504) |  | config_guaji.luac, config_automate.luac, _guaji.json | implemented ⏳需MuMu取证 | guaji_state.db + config_guaji / CONFIRMED |
| SYS_BATTLE_003 | Battle Replay / Video | 战报, 战斗回放 | battlevideo_ctrl.luac |  | config_battlevideo.luac | client-only / not hooked | _tmp_battle battlevideo modules; no DB / VERIFIED |
| SYS_BATTLE_004 | God War Battle | 神魔战 | godwar (function 52) |  | config_sm_war_data.luac, config_god_unite_data.luac | client-only / not hooked ⏳需MuMu取证 | godwar_battle_* modules + config_sm_war / VERIFIED |
| SYS_BATTLE_005 | Boss System | BOSS, 世界BOSS, 恶魔/魔王 | boss? |  | config_boss.luac, config_demon.luac | implemented (kill record) ⏳需MuMu取证 | role_boss_kill.db + config_boss / CONFIRMED |

### SYS_BATTLE_001 — Turn-based Battle
- **aliases**: 回合制战斗, 怪物
- **version**: 1.4.11
- **client_entry**: battle_ctrl.luac
- **lua_modules**: battle.luac, battle_ctrl.luac, battle_role.luac, battle_view.luac, battle_tips.luac, conf_test_battle.luac
- **protocols**: CS_20002, SC_20010, SC_20012, SC_20013, CS_20014, SC_20020
- **config_files**: config_battle.luac, config_combat.luac, config_fight.luac, config_mon_data.luac
- **data_files**: battle.py
- **UI_files**: battle UI
- **dependencies**: Skill, Buff, Partner, Equipment
- **server_state**: implemented
- **related_systems**: Skill, Buff, PvE Dungeon, Boss
- **evidence**: battle.py + protocol_index five-cmd chain verified on real device
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 战斗数值（回合伤害/命中/暴击公式）

### SYS_BATTLE_002 — Auto-battle / AFK
- **aliases**: 挂机, 自动战斗
- **version**: 1.4.11
- **client_entry**: automate (function 504)
- **lua_modules**: automate_ctrl.luac
- **protocols**: 
- **config_files**: config_guaji.luac, config_automate.luac, _guaji.json
- **data_files**: guaji_state table
- **UI_files**: auto battle toggles
- **dependencies**: Battle
- **server_state**: implemented
- **database_state**: guaji_state present
- **rewards**: 挂机奖励
- **currencies**: profit_exp
- **related_systems**: Battle, Daily/Active
- **evidence**: guaji_state.db + config_guaji
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 挂机战斗数值与自动战斗 AI 行为

### SYS_BATTLE_003 — Battle Replay / Video
- **aliases**: 战报, 战斗回放
- **version**: 1.4.11
- **client_entry**: battlevideo_ctrl.luac
- **lua_modules**: battlevideo_ctrl.luac, battlevideo_data.luac, battlevideo_main_panel.luac, ownvideo_*.luac, peakvideo_*.luac
- **protocols**: 
- **config_files**: config_battlevideo.luac
- **UI_files**: replay lists
- **dependencies**: Battle
- **server_state**: not implemented
- **related_systems**: Battle, Rank PvP
- **evidence**: _tmp_battle battlevideo modules; no DB
- **confidence**: VERIFIED
- **implementation_status**: client-only / not hooked

### SYS_BATTLE_004 — God War Battle
- **aliases**: 神魔战
- **version**: 1.4.11
- **client_entry**: godwar (function 52)
- **lua_modules**: godwar_battle_*.luac
- **protocols**: 
- **config_files**: config_sm_war_data.luac, config_god_unite_data.luac
- **UI_files**: godwar battle UI
- **dependencies**: Battle, Cross-server
- **server_state**: not implemented (client UI only)
- **related_systems**: Battle, Dungeon tower
- **evidence**: godwar_battle_* modules + config_sm_war
- **confidence**: VERIFIED
- **implementation_status**: client-only / not hooked
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 神魔战数值与胜负结算

### SYS_BATTLE_005 — Boss System
- **aliases**: BOSS, 世界BOSS, 恶魔/魔王
- **version**: 1.4.11
- **client_entry**: boss?
- **lua_modules**: ghost_ctrl.luac, ghost_mon.luac
- **protocols**: 
- **config_files**: config_boss.luac, config_demon.luac
- **data_files**: role_boss_kill table
- **UI_files**: boss scene
- **dependencies**: Battle
- **server_state**: implemented
- **database_state**: role_boss_kill present
- **currencies**: boss_point (37)
- **related_systems**: Battle
- **evidence**: role_boss_kill.db + config_boss
- **confidence**: CONFIRMED
- **implementation_status**: implemented (kill record)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 怪物血量/攻击

---

## E. 装备系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_EQUIP_001 | Equipment System | 装备 | equip? | CS_10500..10593, CS_11200~11205 partner equip | config_eqm_ancient.luac, config_eqm_starup_data.luac, config_marry_eqm_data.luac, config_red_eqm.luac, config_item_type_name.luac | implemented ⏳需MuMu取证 | equip_items.db / CONFIRMED |
| SYS_EQUIP_002 | Smith / Forge / Fuse | 锻造, 合成, 融合, 装备升阶 | smith (function 11000) / hecheng (function 16000) |  | config_item_fuse.luac, config_intensify.luac, config_promote.luac, _promote.json | partial ⏳需MuMu取证 | config_item_fuse + hecheng function id / VERIFIED |
| SYS_EQUIP_003 | Rune System | 符文 | rune? |  | config_rune_data.luac, config_rune_dec.json, config_rune_treasure_data.luac, config_dungeon_rune.luac, _rune_cfg.json | implemented ⏳需MuMu取证 | role_runes.db + config_rune_data / CONFIRMED |
| SYS_EQUIP_004 | Equip StarUp/强化 | 装备升星, 强化, 装备强化 | smith |  | config_eqm_starup_data.luac, config_intensify.luac | partial ⏳需MuMu取证 | config_eqm_starup_data / VERIFIED |
| SYS_EQUIP_005 | Equip Refine 装备洗练 | 洗练, xilian, refine | UNKNOWN | — | — | not implemented (unknown) | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |
| SYS_EQUIP_006 | Gem / Socket 宝石 | 宝石, gem, baoshi | UNKNOWN | — | — | not implemented (unknown) | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |

### SYS_EQUIP_001 — Equipment System
- **aliases**: 装备
- **version**: 1.4.11
- **client_entry**: equip?
- **lua_modules**: durable_item.luac, durable_panel.luac
- **protocols**: CS_10500..10593, CS_11200~11205 partner equip
- **config_files**: config_eqm_ancient.luac, config_eqm_starup_data.luac, config_marry_eqm_data.luac, config_red_eqm.luac, config_item_type_name.luac
- **data_files**: equip_items table
- **UI_files**: equip panel
- **dependencies**: Inventory, Partner
- **server_state**: implemented
- **database_state**: equip_items present
- **related_systems**: Inventory, Smith/Forge, Rune
- **evidence**: equip_items.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 装备基础属性/穿戴加成

### SYS_EQUIP_002 — Smith / Forge / Fuse
- **aliases**: 锻造, 合成, 融合, 装备升阶
- **version**: 1.4.11
- **client_entry**: smith (function 11000) / hecheng (function 16000)
- **protocols**: 
- **config_files**: config_item_fuse.luac, config_intensify.luac, config_promote.luac, _promote.json
- **UI_files**: forge panel
- **dependencies**: Equipment, Inventory
- **server_state**: partial
- **related_systems**: Equipment, Equip StarUp
- **evidence**: config_item_fuse + hecheng function id
- **confidence**: VERIFIED
- **implementation_status**: partial
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 锻造/合成/升阶数值成功率

### SYS_EQUIP_003 — Rune System
- **aliases**: 符文
- **version**: 1.4.11
- **client_entry**: rune?
- **protocols**: 
- **config_files**: config_rune_data.luac, config_rune_dec.json, config_rune_treasure_data.luac, config_dungeon_rune.luac, _rune_cfg.json
- **data_files**: role_runes table
- **UI_files**: rune panel — `shots/user_assist/skill_rune_panel.png`（4槽未激活，学习/一键升级按钮，UI_DISPLAY 级证据）
- **dependencies**: Equipment, Dungeon
- **server_state**: implemented
- **database_state**: role_runes present
- **currencies**: rune_exp(39),rune_chip(40)
- **related_systems**: Equipment, Dungeon Tower
- **evidence**: role_runes.db + config_rune_data
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 符文属性与套装效果

### SYS_EQUIP_004 — Equip StarUp/强化
- **aliases**: 装备升星, 强化, 装备强化
- **version**: 1.4.11
- **client_entry**: smith
- **protocols**: 
- **config_files**: config_eqm_starup_data.luac, config_intensify.luac
- **UI_files**: starup panel
- **dependencies**: Equipment
- **server_state**: partial
- **related_systems**: Equipment, Smith
- **evidence**: config_eqm_starup_data
- **confidence**: VERIFIED
- **implementation_status**: partial
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 强化概率/强化属性成长

### SYS_EQUIP_005 — Equip Refine 装备洗练
- **aliases**: 洗练, xilian, refine
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: Equipment
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **notes**: PHASE0 audit-flagged item; no config_eqm_refine / xilian module located.

### SYS_EQUIP_006 — Gem / Socket 宝石
- **aliases**: 宝石, gem, baoshi
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: Equipment
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **notes**: PHASE0 audit-flagged item; no config_gem / gem socket module located. Rune system (SYS_EQUIP_003) is distinct.

---

## F. 伙伴系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_FRIEND_001 | Partner/Hero System | 伙伴, 英雄, 随从 | hero (function 4000) | CS_10401..10406 | config_hero_base.luac, config_hero_info.luac, config_hero_attr.luac, config_hero_attr_opp.luac, config_hero_misc.luac, config_hero_morale.luac, config_hero_skill_order.luac, config_partner_base.luac, config_partner_fetter.luac, config_partner_misc.luac, config_partner_score.luac, config_partner_shenqi.luac, config_partner_skill.luac, partner_config.json | implemented ⏳需MuMu取证 | role_heros.db + partner_config.json / CONFIRMED |
| SYS_FRIEND_002 | Formation / 阵法 | 阵法, 阵型 | formation (function 3000) |  | config_formation.luac | implemented ⏳需MuMu取证 | role_form.db + form_ctrl.luac / CONFIRMED |
| SYS_FRIEND_003 | Partner Atlas/图鉴 | 伙伴图鉴 | hero |  | config_partner_score.luac, config_hero_attr_opp.luac | client UI / partial | partner_atlas modules / VERIFIED |
| SYS_FRIEND_004 | Partner Recruit/招募 | 伙伴招募, 抽卡 | recruit (function 113) |  | config_partner_skill.luac, config_lucky_box_data.luac | partial ⏳需MuMu取证 | recruit function id + shop_partner_view / VERIFIED |
| SYS_FRIEND_005 | Partner Fetter/羁绊 | 伙伴羁绊 | hero |  | config_partner_fetter.luac | client-config only | config_partner_fetter only / STRONG_INFERENCE |
| SYS_FRIEND_006 | Partner Training 伙伴培养 | 伙伴培养, partner_train, hero_peiyang | UNKNOWN | — | — | not implemented (unknown) | UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory / UNKNOWN |
| SYS_FRIEND_007 | Partner Equipment 伙伴装备 | 伙伴装备, partner_equip, hero_equip, partner_eqm | UNKNOWN | CS_11200~11205 partner equip (referenced in SYS_EQUIP_001) | — | partial (protocols referenced; no dedicated module) | CS_11200..11205 mentioned as partner equip range inside SYS_EQUIP_001; no dedicated partner-equip module inventoried / INFERENCE |

### SYS_FRIEND_001 — Partner/Hero System
- **aliases**: 伙伴, 英雄, 随从
- **version**: 1.4.11
- **client_entry**: hero (function 4000)
- **lua_modules**: hero_ctrl.luac, hero_data.luac, hero_vo.luac, partner_event.luac, partner_vo.luac, partner_atlas_*.luac, hero_constants.luac
- **protocols**: CS_10401..10406
- **config_files**: config_hero_base.luac, config_hero_info.luac, config_hero_attr.luac, config_hero_attr_opp.luac, config_hero_misc.luac, config_hero_morale.luac, config_hero_skill_order.luac, config_partner_base.luac, config_partner_fetter.luac, config_partner_misc.luac, config_partner_score.luac, config_partner_shenqi.luac, config_partner_skill.luac, partner_config.json
- **data_files**: role_heros table
- **UI_files**: hero list/atlas/pack
- **dependencies**: Inventory, Battle, Skill
- **server_state**: implemented
- **database_state**: role_heros present
- **currencies**: courage(16)
- **related_systems**: Formation, Partner Atlas, Partner Weapon
- **evidence**: role_heros.db + partner_config.json
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 伙伴属性/技能数值/招募概率

### SYS_FRIEND_002 — Formation / 阵法
- **aliases**: 阵法, 阵型
- **version**: 1.4.11
- **client_entry**: formation (function 3000)
- **lua_modules**: form_ctrl.luac, form_data.luac, form_view.luac, form_hero_list.luac, form_type_list.luac, form_partner_list.luac, endless_form_ctrl.luac
- **protocols**: 
- **config_files**: config_formation.luac
- **data_files**: role_form table
- **UI_files**: formation panel, endless form
- **dependencies**: Partner, Battle
- **server_state**: implemented
- **database_state**: role_form present
- **related_systems**: Partner, Battle
- **evidence**: role_form.db + form_ctrl.luac
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 阵法加成数值

### SYS_FRIEND_003 — Partner Atlas/图鉴
- **aliases**: 伙伴图鉴
- **version**: 1.4.11
- **client_entry**: hero
- **lua_modules**: partner_atlas_*.luac, partner_show_panel.luac, partner_pack_view.luac
- **protocols**: 
- **config_files**: config_partner_score.luac, config_hero_attr_opp.luac
- **UI_files**: atlas
- **dependencies**: Partner
- **server_state**: partial
- **related_systems**: Partner
- **evidence**: partner_atlas modules
- **confidence**: VERIFIED
- **implementation_status**: client UI / partial

### SYS_FRIEND_004 — Partner Recruit/招募
- **aliases**: 伙伴招募, 抽卡
- **version**: 1.4.11
- **client_entry**: recruit (function 113)
- **lua_modules**: shop_partner_view.luac
- **protocols**: 
- **config_files**: config_partner_skill.luac, config_lucky_box_data.luac
- **UI_files**: recruit panel
- **dependencies**: Partner, Mall
- **server_state**: partial
- **related_systems**: Partner, Mall, Activity
- **evidence**: recruit function id + shop_partner_view
- **confidence**: VERIFIED
- **implementation_status**: partial
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 伙伴招募概率/保底

### SYS_FRIEND_005 — Partner Fetter/羁绊
- **aliases**: 伙伴羁绊
- **version**: 1.4.11
- **client_entry**: hero
- **protocols**: 
- **config_files**: config_partner_fetter.luac
- **dependencies**: Partner
- **server_state**: not implemented
- **related_systems**: Partner
- **evidence**: config_partner_fetter only
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_FRIEND_006 — Partner Training 伙伴培养
- **aliases**: 伙伴培养, partner_train, hero_peiyang
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **dependencies**: Partner/Hero System
- **server_state**: unknown
- **database_state**: UNKNOWN
- **evidence**: UNKNOWN: named in PHASE0 audit checklist; no dedicated config/module/protocol found during APK inventory
- **confidence**: UNKNOWN
- **implementation_status**: not implemented (unknown)
- **notes**: PHASE0 audit-flagged item; partner level/star may be folded into SYS_FRIEND_001 but no dedicated train module located.

### SYS_FRIEND_007 — Partner Equipment 伙伴装备
- **aliases**: 伙伴装备, partner_equip, hero_equip, partner_eqm
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **protocols**: CS_11200~11205 partner equip (referenced in SYS_EQUIP_001)
- **dependencies**: Partner/Hero System, Equipment
- **server_state**: partial (protocol range referenced)
- **database_state**: UNKNOWN
- **evidence**: CS_11200..11205 mentioned as partner equip range inside SYS_EQUIP_001; no dedicated partner-equip module inventoried
- **confidence**: INFERENCE
- **implementation_status**: partial (protocols referenced; no dedicated module)

---

## G. 外观系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_APPEAR_001 | Wing System 翅膀 | 翅膀, wind | wind (function 20000) |  | config_wing_data.luac | implemented ⏳需MuMu取证 | role_wing.db + config_wing_data / CONFIRMED |
| SYS_APPEAR_002 | Mount 坐骑 | 坐骑 | ride (function 18000) | CS_10551.. | config_ride.luac | implemented ⏳需MuMu取证 | role_ride.db + config_ride / CONFIRMED |
| SYS_APPEAR_003 | Beast 灵兽 | 灵兽, Lingshou | lingshou (function 19000) |  | config_lingshou.luac, config_lingshou_speak.luac | implemented ⏳需MuMu取证 | role_lingshou.db / CONFIRMED |
| SYS_APPEAR_004 | Soul 元神 | 元神 | yuanshen (function 22000) |  | config_yuanshen.luac | implemented | role_yuanshen.db + yuanshen_ctrl.luac / CONFIRMED |
| SYS_APPEAR_005 | Divine Artifact 神器 | 神器 | shenqi (function 21000) |  | config_shenqi.luac, config_partner_shenqi.luac, config_artifact_image.luac | implemented ⏳需MuMu取证 | role_shenqi.db + config_shenqi / CONFIRMED |
| SYS_APPEAR_006 | Fate/Natal 命格 | 命格 | mingge (function 24000) |  | config_mingge.luac, _mingge_cfg.json | implemented ⏳需MuMu取证 | role_mingge.db + _mingge_cfg.json / CONFIRMED |
| SYS_APPEAR_007 | Magic Weapon 法宝 | 法宝 | fabao? | CS_11200~11205? | config_fabao.luac | implemented | role_fabao.db / CONFIRMED |
| SYS_APPEAR_008 | Vehicle/Chair 座驾 | 座驾, 椅子 | chair? |  | config_chair.luac | implemented | role_chair.db + config_chair / CONFIRMED |
| SYS_APPEAR_009 | Fashion/Skin 时装 | 时装 | fashion? | 10573, 10574, 10575, 10576, 10578 | config_fashion.luac, config_fashion_upgrade.luac, config_fashion_constant.luac | implemented (persistence) ⏳需MuMu取证 | role_fashion + config_fashion validation + tools/test_fashion.py ALL PASS / VERIFIED |
| SYS_APPEAR_010 | Halo 光环 | 光环 | halo (game/halo/*) | 19100, 19103, 19104 | config_halo.luac | implemented (persistence) | role_halo + halo_model disassembly + tools/test_halo.py ALL PASS / VERIFIED |

### SYS_APPEAR_001 — Wing System 翅膀
- **aliases**: 翅膀, wind
- **version**: 1.4.11
- **client_entry**: wind (function 20000)
- **protocols**: 
- **config_files**: config_wing_data.luac
- **data_files**: role_wing table
- **UI_files**: wing panel
- **dependencies**: Appearance, Attribute
- **server_state**: implemented
- **database_state**: role_wing present
- **related_systems**: Appearance Suite, Ride
- **evidence**: role_wing.db + config_wing_data
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 翅膀成长数值

### SYS_APPEAR_002 — Mount 坐骑
- **aliases**: 坐骑
- **version**: 1.4.11
- **client_entry**: ride (function 18000)
- **protocols**: CS_10551..
- **config_files**: config_ride.luac
- **data_files**: role_ride table
- **UI_files**: mount panel
- **dependencies**: Appearance
- **server_state**: implemented
- **database_state**: role_ride present
- **related_systems**: Wing
- **evidence**: role_ride.db + config_ride
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 坐骑成长数值

### SYS_APPEAR_003 — Beast 灵兽
- **aliases**: 灵兽, Lingshou
- **version**: 1.4.11
- **client_entry**: lingshou (function 19000)
- **protocols**: 
- **config_files**: config_lingshou.luac, config_lingshou_speak.luac
- **data_files**: role_lingshou table
- **UI_files**: beast panel
- **dependencies**: Appearance, Attribute
- **server_state**: implemented
- **database_state**: role_lingshou present
- **related_systems**: Wing, Ride
- **evidence**: role_lingshou.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 灵兽成长数值

### SYS_APPEAR_004 — Soul 元神
- **aliases**: 元神
- **version**: 1.4.11
- **client_entry**: yuanshen (function 22000)
- **lua_modules**: yuanshen_ctrl.luac
- **protocols**: 
- **config_files**: config_yuanshen.luac
- **data_files**: role_yuanshen table
- **UI_files**: soul panel
- **dependencies**: Appearance
- **server_state**: implemented
- **database_state**: role_yuanshen present
- **related_systems**: Wing, Divine Artifact
- **evidence**: role_yuanshen.db + yuanshen_ctrl.luac
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_APPEAR_005 — Divine Artifact 神器
- **aliases**: 神器
- **version**: 1.4.11
- **client_entry**: shenqi (function 21000)
- **protocols**: 
- **config_files**: config_shenqi.luac, config_partner_shenqi.luac, config_artifact_image.luac
- **data_files**: role_shenqi table
- **UI_files**: artifact panel
- **dependencies**: Appearance, Partner
- **server_state**: implemented
- **database_state**: role_shenqi present
- **currencies**: partner_shenqi_point(38)
- **related_systems**: Partner, Wing
- **evidence**: role_shenqi.db + config_shenqi
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 神器属性数值

### SYS_APPEAR_006 — Fate/Natal 命格
- **aliases**: 命格
- **version**: 1.4.11
- **client_entry**: mingge (function 24000)
- **protocols**: 
- **config_files**: config_mingge.luac, _mingge_cfg.json
- **data_files**: role_mingge table
- **UI_files**: fate panel
- **dependencies**: Appearance
- **server_state**: implemented
- **database_state**: role_mingge present
- **related_systems**: Wing
- **evidence**: role_mingge.db + _mingge_cfg.json
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 命格属性数值

### SYS_APPEAR_007 — Magic Weapon 法宝
- **aliases**: 法宝
- **version**: 1.4.11
- **client_entry**: fabao?
- **lua_modules**: fabao_select.luac
- **protocols**: CS_11200~11205?
- **config_files**: config_fabao.luac
- **data_files**: role_fabao table
- **UI_files**: weapon select
- **dependencies**: Battle, Partner
- **server_state**: implemented
- **database_state**: role_fabao present
- **related_systems**: Battle, Partner
- **evidence**: role_fabao.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_APPEAR_008 — Vehicle/Chair 座驾
- **aliases**: 座驾, 椅子
- **version**: 1.4.11
- **client_entry**: chair?
- **protocols**: 
- **config_files**: config_chair.luac
- **data_files**: role_chair table
- **UI_files**: vehicle panel
- **dependencies**: Appearance
- **server_state**: implemented
- **database_state**: role_chair present
- **related_systems**: Ride
- **evidence**: role_chair.db + config_chair
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_APPEAR_009 — Fashion/Skin 时装
- **aliases**: 时装
- **version**: 1.4.11
- **client_entry**: fashion?
- **protocols**: 10573, 10574, 10575, 10576, 10578
- **config_files**: config_fashion.luac, config_fashion_upgrade.luac, config_fashion_constant.luac
- **data_files**: role_fashion (SQLite), server/cfg_kconfig/config_fashion.json
- **UI_files**: skin panel
- **dependencies**: Appearance, Attribute
- **server_state**: implemented (activate/wear/star/unwear); attribute contribution not yet wired
- **database_state**: role_fashion
- **related_systems**: Wing, Halo
- **evidence**: role_fashion + config_fashion validation + tools/test_fashion.py ALL PASS
- **confidence**: VERIFIED
- **implementation_status**: implemented (persistence)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: PHASE2.7：10573/10574/10575/10576/10578 真实落库并**按 config_fashion 校验 bid**。CS id 即 bid(无实例概念)。10577 过期推送未做；属性/战力贡献未接。 [需 MuMu 运行时取证] 时装属性数值

### SYS_APPEAR_010 — Halo 光环
- **aliases**: 光环
- **version**: 1.4.11
- **client_entry**: halo (game/halo/*)
- **lua_modules**: halo_ctrl, halo_model, halo_view, halo_info_view
- **protocols**: 19100, 19103, 19104
- **config_files**: config_halo.luac
- **data_files**: role_halo (SQLite), role_halo_equip (SQLite)
- **UI_files**: halo_view
- **dependencies**: Appearance, Attribute
- **server_state**: implemented (info + equip slots); upgrade not implemented
- **database_state**: role_halo, role_halo_equip
- **related_systems**: Fashion, Wing
- **evidence**: role_halo + halo_model disassembly + tools/test_halo.py ALL PASS
- **confidence**: VERIFIED
- **implementation_status**: implemented (persistence)
- **notes**: PHASE2.8：19100 真实状态(items 用 bag_items_bytes 编码装备位)+19103/19104 落库。halo_model 只读 stage/luck/grow(已反汇编证实)。升阶/属性贡献未做。

---

## H. 资源经济

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_ECON_001 | Assets/Currency System | 货币, 资源, 资产 | all | SC_10303 assets | config_game_data.luac (AssetsEnToCode) | implemented ⏳需MuMu取证 | ASSETS_EN_TO_CODE 38 items verified vs client config / CONFIRMED |
| SYS_ECON_002 | Inventory/Bag 背包 | 背包, 道具, 物品 | bag (function 2000) | CS_10500..10593 | config_item.luac, config_item_misc.luac, config_item_gift.luac, item_config.json, item_gift.json | implemented | bag_items.db + item_config.json (3535 items) / CONFIRMED |
| SYS_ECON_003 | Mall/Shop 商城 | 商城, 商店 | mall (function 501) | CS_12801..12856, CS_13401..13416 | config_mall.luac, config_shop.luac, config_exchange.luac, mall_config.json, mall_exchange.json, mall_zhenbao.json | implemented ⏳需MuMu取证 | mall_bought.db + mall_config.json / CONFIRMED |
| SYS_ECON_004 | Storage/Warehouse 仓库 | 仓库, 背包扩展 | bag (function 2000) | CS_10714, CS_10621 | config_storage_data.luac | implemented | store_items.db + config_storage_data / CONFIRMED |
| SYS_ECON_005 | Trade Market 市场/交易 | 市场, 寄售 | market (function 7000) | CS_18909.. | config_market.luac | implemented | role_market,role_market_goods.db + market_ctrl.luac / CONFIRMED |
| SYS_ECON_006 | Black Market 黑市 | 黑市 | black market? | CS_18909? | config_black_market.luac | partial (generic stub, no DB) | mock_server handler 17128 loads config_black_market generic / VERIFIED |
| SYS_ECON_007 | Exchange 兑换 | 兑换, duihuan | duihuan (function 20) / yunyingduihuan (21) |  | config_exchange.luac, mall_exchange.json | partial | mall_exchange.json / VERIFIED |
| SYS_ECON_008 | Auction/拍卖 | 拍卖, paimai | paimai (function 43) | 18020, 18021, 18022 | config_auction_data.luac, server/cfg_kconfig/config_auction_data.json | implemented (list + buy) | tools/test_auction.py ALL PASS (real 50 goods, real deduct+deliver) / VERIFIED |
| SYS_ECON_009 | Mail 邮件 | 邮件 | mail? | CS_10800 mail | config_notice.luac | implemented | role_mail.db + CS_10800 / CONFIRMED |
| SYS_ECON_010 | Recharge/Payment 充值 | 充值, 首充 | recharge (function 27) | CS_12831, CS_13401.. | config_charge.luac, config_charge_eyou.luac, config_first_charge.luac, config_once_charge.luac, config_every_charge.luac, config_lucky_box_data.luac | partial | recharge function id + config_charge* / VERIFIED |
| SYS_ECON_011 | Gift Item 礼包/道具 | 礼包, 宝箱 | all |  | config_item_gift.luac, config_lucky_box_data.luac, config_reward_box_data.luac, config_treasure_box_data.luac, item_gift.json, config_drop.luac, config_drop_item.luac, config_reward_data.luac | implemented (gift/drop resolve) ⏳需MuMu取证 | item_gift.json + config_drop / VERIFIED |
| SYS_ECON_012 | Drop / Loot Table 掉落 | 掉落, drop, loot | UNKNOWN | — | config_mon_data.luac (drop refs), config_item_drop? | partial (drop resolve inside gift/battle; no dedicated drop system) ⏳需MuMu取证 | config_mon_data referenced inside SYS_BATTLE_001; no dedicated drop-table module inventoried / INFERENCE |

### SYS_ECON_001 — Assets/Currency System
- **aliases**: 货币, 资源, 资产
- **version**: 1.4.11
- **client_entry**: all
- **protocols**: SC_10303 assets
- **config_files**: config_game_data.luac (AssetsEnToCode)
- **data_files**: role_assets table
- **UI_files**: top bar
- **server_state**: implemented
- **database_state**: role_assets present
- **currencies**: gold,coin,coupon,experience,diamond,sinew,vitality,guild_contrib,practice_exp,tower_cent,arena_cent,coral,rmb,lingshi,gouyu,cash_coupon,dan_point,marriage,course,peak_point,arena_soul,black_soul,jiebai_cent,lottery_point,boss_point,...
- **related_systems**: all
- **evidence**: ASSETS_EN_TO_CODE 38 items verified vs client config
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 货币汇率/资产数值

### SYS_ECON_002 — Inventory/Bag 背包
- **aliases**: 背包, 道具, 物品
- **version**: 1.4.11
- **client_entry**: bag (function 2000)
- **lua_modules**: backpack_const.luac
- **protocols**: CS_10500..10593
- **config_files**: config_item.luac, config_item_misc.luac, config_item_gift.luac, item_config.json, item_gift.json
- **data_files**: bag_items table, bag_volume table
- **UI_files**: bag panel
- **dependencies**: Economy, All
- **server_state**: implemented
- **database_state**: bag_items, bag_volume present
- **related_systems**: all reward paths
- **evidence**: bag_items.db + item_config.json (3535 items)
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_ECON_003 — Mall/Shop 商城
- **aliases**: 商城, 商店
- **version**: 1.4.11
- **client_entry**: mall (function 501)
- **lua_modules**: shop_ctrl.luac, shop_cell.luac, shop_model.luac, shop_exchange_view.luac, shop_new_exchange_view.luac
- **protocols**: CS_12801..12856, CS_13401..13416
- **config_files**: config_mall.luac, config_shop.luac, config_exchange.luac, mall_config.json, mall_exchange.json, mall_zhenbao.json
- **data_files**: mall_bought table
- **UI_files**: mall/shop UI
- **dependencies**: Economy, Recharge
- **server_state**: implemented
- **database_state**: mall_bought present
- **related_systems**: Recharge, Exchange
- **evidence**: mall_bought.db + mall_config.json
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 商品价格/限购

### SYS_ECON_004 — Storage/Warehouse 仓库
- **aliases**: 仓库, 背包扩展
- **version**: 1.4.11
- **client_entry**: bag (function 2000)
- **protocols**: CS_10714, CS_10621
- **config_files**: config_storage_data.luac
- **data_files**: store_items table
- **UI_files**: warehouse panel
- **dependencies**: Inventory
- **server_state**: implemented
- **database_state**: store_items present
- **related_systems**: Inventory
- **evidence**: store_items.db + config_storage_data
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_ECON_005 — Trade Market 市场/交易
- **aliases**: 市场, 寄售
- **version**: 1.4.11
- **client_entry**: market (function 7000)
- **lua_modules**: market_ctrl.luac
- **protocols**: CS_18909..
- **config_files**: config_market.luac
- **data_files**: role_market table, role_market_goods table
- **UI_files**: market UI
- **dependencies**: Economy, Inventory
- **server_state**: implemented
- **database_state**: role_market, role_market_goods present
- **related_systems**: Black Market, Auction
- **evidence**: role_market,role_market_goods.db + market_ctrl.luac
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_ECON_006 — Black Market 黑市
- **aliases**: 黑市
- **version**: 1.4.11
- **client_entry**: black market?
- **protocols**: CS_18909?
- **config_files**: config_black_market.luac
- **UI_files**: black market
- **dependencies**: Market, Economy
- **server_state**: partial (generic response)
- **currencies**: black_soul(32)
- **related_systems**: Market, Auction
- **evidence**: mock_server handler 17128 loads config_black_market generic
- **confidence**: VERIFIED
- **implementation_status**: partial (generic stub, no DB)

### SYS_ECON_007 — Exchange 兑换
- **aliases**: 兑换, duihuan
- **version**: 1.4.11
- **client_entry**: duihuan (function 20) / yunyingduihuan (21)
- **lua_modules**: shop_exchange_view.luac, shop_new_exchange_view.luac
- **protocols**: 
- **config_files**: config_exchange.luac, mall_exchange.json
- **UI_files**: exchange UI
- **dependencies**: Mall, Economy
- **server_state**: partial
- **related_systems**: Mall
- **evidence**: mall_exchange.json
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_ECON_008 — Auction/拍卖
- **aliases**: 拍卖, paimai
- **version**: 1.4.11
- **client_entry**: paimai (function 43)
- **protocols**: 18020, 18021, 18022
- **config_files**: config_auction_data.luac, server/cfg_kconfig/config_auction_data.json
- **data_files**: role_assets (扣费), bag_items (发货)
- **UI_files**: auction
- **dependencies**: Economy, Inventory
- **server_state**: implemented (list + one-price buy); bidding not implemented
- **database_state**: role_assets, bag_items
- **rewards**: item
- **currencies**: guild_contrib, coupon, coin
- **related_systems**: Market, Shop
- **evidence**: tools/test_auction.py ALL PASS (real 50 goods, real deduct+deliver)
- **confidence**: VERIFIED
- **implementation_status**: implemented (list + buy)
- **notes**: PHASE2.9：18020/18021 真实 50 商品(按 item_bid 过滤掉 2 条配置行)；18022 一口价真扣费+真入包。price_assets 由 assets 名经 asset_label_map 转 code。item_number 配置无⇒取1(INFERENCE)。竞拍/记录/关注未做。

### SYS_ECON_009 — Mail 邮件
- **aliases**: 邮件
- **version**: 1.4.11
- **client_entry**: mail?
- **protocols**: CS_10800 mail
- **config_files**: config_notice.luac
- **data_files**: role_mail table
- **UI_files**: mail UI
- **dependencies**: Economy, Rewards
- **server_state**: implemented
- **database_state**: role_mail present
- **rewards**: 附件奖励
- **related_systems**: all reward paths
- **evidence**: role_mail.db + CS_10800
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_ECON_010 — Recharge/Payment 充值
- **aliases**: 充值, 首充
- **version**: 1.4.11
- **client_entry**: recharge (function 27)
- **lua_modules**: first_recharge_ui.luac
- **protocols**: CS_12831, CS_13401..
- **config_files**: config_charge.luac, config_charge_eyou.luac, config_first_charge.luac, config_once_charge.luac, config_every_charge.luac, config_lucky_box_data.luac
- **data_files**: mall_bought table, role_assets
- **UI_files**: recharge UI, first charge
- **dependencies**: Economy, VIP
- **server_state**: partial
- **database_state**: no dedicated recharge table (uses mall_bought/assets)
- **rewards**: 首充礼包
- **currencies**: rmb(14),cash_coupon(22)
- **related_systems**: VIP, First Charge, Daily Login
- **evidence**: recharge function id + config_charge*
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_ECON_011 — Gift Item 礼包/道具
- **aliases**: 礼包, 宝箱
- **version**: 1.4.11
- **client_entry**: all
- **protocols**: 
- **config_files**: config_item_gift.luac, config_lucky_box_data.luac, config_reward_box_data.luac, config_treasure_box_data.luac, item_gift.json, config_drop.luac, config_drop_item.luac, config_reward_data.luac
- **UI_files**: gift open
- **dependencies**: Inventory, Rewards
- **server_state**: implemented
- **related_systems**: Inventory, Activity rewards
- **evidence**: item_gift.json + config_drop
- **confidence**: VERIFIED
- **implementation_status**: implemented (gift/drop resolve)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 礼包/宝箱实际开出内容

### SYS_ECON_012 — Drop / Loot Table 掉落
- **aliases**: 掉落, drop, loot
- **version**: 1.4.11
- **client_entry**: UNKNOWN
- **config_files**: config_mon_data.luac (drop refs), config_item_drop?
- **data_files**: UNKNOWN
- **dependencies**: Battle, Monster, Item
- **server_state**: partial (drop resolved via gift/item path)
- **database_state**: UNKNOWN
- **evidence**: config_mon_data referenced inside SYS_BATTLE_001; no dedicated drop-table module inventoried
- **confidence**: INFERENCE
- **implementation_status**: partial (drop resolve inside gift/battle; no dedicated drop system)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 掉落表真实产出

---

## I. 任务系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_QUEST_001 | Mission/Quest 任务 | 任务, 主线, 任务奖励 | mission (function 10000) | CS_12400..12421, CS_12407/08/09 | config_mission.luac, config_mission_buffy.luac, config_chapter.luac, mission_config.json, _mission_route.json | implemented | missions.db + mission_config.json (846 tasks) + protocol_index / CONFIRMED |
| SYS_QUEST_002 | Daily/Active 日常活跃 | 日常, 活跃度 | richang (function 503) / daily | CS_10301? | config_richang.luac, config_function.luac, _richang.json | implemented | daily_progress.db / CONFIRMED |
| SYS_QUEST_003 | Achievement 成就 | 成就 | chengjiu (function 17000) |  | config_chengjiu.luac, _chengjiu.json, _chengjiu_map.json | implemented ⏳需MuMu取证 | chengjiu_progress.db / CONFIRMED |
| SYS_QUEST_004 | Growth Target 成长目标 | 目标, 成长目标 | target (function 505) |  | config_growth_target_data.luac, config_growth_target.json, config_fly_up.luac | partial | config_growth_target / VERIFIED |
| SYS_QUEST_005 | Guide System 引导 | 新手引导, 剧情 | guide |  | config_guide.luac, config_guider_up.luac, config_drama_data.luac, config_function_notice.luac | client-only | config_guide + action_ctrl / VERIFIED |

### SYS_QUEST_001 — Mission/Quest 任务
- **aliases**: 任务, 主线, 任务奖励
- **version**: 1.4.11
- **client_entry**: mission (function 10000)
- **lua_modules**: mission_util.luac
- **protocols**: CS_12400..12421, CS_12407/08/09
- **config_files**: config_mission.luac, config_mission_buffy.luac, config_chapter.luac, mission_config.json, _mission_route.json
- **data_files**: missions table
- **UI_files**: quest log/track
- **dependencies**: Rewards, Economy
- **server_state**: implemented
- **database_state**: missions present
- **rewards**: 任务奖励(assets+items)
- **currencies**: gold,coin,coupon,exp...
- **related_systems**: Daily, Achievement, Guide
- **evidence**: missions.db + mission_config.json (846 tasks) + protocol_index
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_QUEST_002 — Daily/Active 日常活跃
- **aliases**: 日常, 活跃度
- **version**: 1.4.11
- **client_entry**: richang (function 503) / daily
- **lua_modules**: daily_ctrl.luac, daily_cell.luac, daily_panel.luac
- **protocols**: CS_10301?
- **config_files**: config_richang.luac, config_function.luac, _richang.json
- **data_files**: daily_progress table, daily_lingqu table
- **UI_files**: daily/active UI
- **dependencies**: Mission, Rewards
- **server_state**: implemented
- **database_state**: daily_progress, daily_lingqu present
- **rewards**: 活跃宝箱
- **currencies**: guild_active(24)
- **related_systems**: Mission, Target
- **evidence**: daily_progress.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_QUEST_003 — Achievement 成就
- **aliases**: 成就
- **version**: 1.4.11
- **client_entry**: chengjiu (function 17000)
- **protocols**: 
- **config_files**: config_chengjiu.luac, _chengjiu.json, _chengjiu_map.json
- **data_files**: chengjiu_progress table
- **UI_files**: achievement panel
- **dependencies**: Rewards
- **server_state**: implemented
- **database_state**: chengjiu_progress present
- **related_systems**: Title, Daily
- **evidence**: chengjiu_progress.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 成就奖励

### SYS_QUEST_004 — Growth Target 成长目标
- **aliases**: 目标, 成长目标
- **version**: 1.4.11
- **client_entry**: target (function 505)
- **protocols**: 
- **config_files**: config_growth_target_data.luac, config_growth_target.json, config_fly_up.luac
- **UI_files**: target panel
- **dependencies**: Achievement
- **server_state**: partial
- **related_systems**: Achievement, Level
- **evidence**: config_growth_target
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_QUEST_005 — Guide System 引导
- **aliases**: 新手引导, 剧情
- **version**: 1.4.11
- **client_entry**: guide
- **lua_modules**: action_ctrl.luac, action_panel.luac
- **protocols**: 
- **config_files**: config_guide.luac, config_guider_up.luac, config_drama_data.luac, config_function_notice.luac
- **UI_files**: guide overlay
- **dependencies**: all
- **server_state**: not implemented (client-side)
- **related_systems**: Mission
- **evidence**: config_guide + action_ctrl
- **confidence**: VERIFIED
- **implementation_status**: client-only

---

## J. 地图系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_MAP_001 | World Map / Region | 世界地图, 区域 | world map |  | config_world_map.luac, config_map.luac, config_team_destination.luac | implemented (basic) | map_block.json + config_map* / VERIFIED |
| SYS_MAP_002 | Team Group 组队 | 组队, 团队 | team (function 12000) | 13200, 13201, 13202, 13203, 13204, 13210, 13218, 13226, 13237 | config_team_destination.luac | implemented (core + invite) | tools/test_multi_session.py ALL PASS (2 roles, real invite->accept->2-member team) / VERIFIED |

### SYS_MAP_001 — World Map / Region
- **aliases**: 世界地图, 区域
- **version**: 1.4.11
- **client_entry**: world map
- **protocols**: 
- **config_files**: config_world_map.luac, config_map.luac, config_team_destination.luac
- **data_files**: map_block.json
- **UI_files**: world map
- **dependencies**: Scene
- **server_state**: implemented
- **related_systems**: Scene, Teleport
- **evidence**: map_block.json + config_map*
- **confidence**: VERIFIED
- **implementation_status**: implemented (basic)

### SYS_MAP_002 — Team Group 组队
- **aliases**: 组队, 团队
- **version**: 1.4.11
- **client_entry**: team (function 12000)
- **protocols**: 13200, 13201, 13202, 13203, 13204, 13210, 13218, 13226, 13237
- **config_files**: config_team_destination.luac
- **data_files**: role_team (SQLite), role_team_invite (SQLite)
- **UI_files**: team panel
- **dependencies**: Scene, Social
- **server_state**: implemented (core + multi-member invite)
- **database_state**: role_team, role_team_invite
- **related_systems**: Social, Dungeon, Marriage, Jiebai
- **evidence**: tools/test_multi_session.py ALL PASS (2 roles, real invite->accept->2-member team)
- **confidence**: VERIFIED
- **implementation_status**: implemented (core + invite)
- **notes**: PHASE2/2.4：13200/13201/13202/13204/13210/13218/13226/13237；13203=服务端推送。多人(2角色)已实测。role_team/role_team_invite 为兼容层(INFERENCE)，协议字段来自 fields.json(CONFIRMED)。其余 132xx(13219/13224/13250 等)仍为通用回执。

---

## K. 副本系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_DUNGEON_001 | Dungeon 副本 | 副本, 地牢 | dungeon? | CS_11700..11713?, CS_13028.. | config_dungeon_new.luac, config_dungeon_reward_desc.luac, config_dungeon_vip_single.luac, config_dungeon_vip_single2.luac, config_dungeon_research? | implemented ⏳需MuMu取证 | dungeon_progress.db / CONFIRMED |
| SYS_DUNGEON_002 | Endless Dungeon 无尽/深渊 | 无尽, 深渊, endless | endless |  | config_dungeon_endless_data.luac | partial ⏳需MuMu取证 | config_dungeon_endless_data / VERIFIED |
| SYS_DUNGEON_003 | Tower 塔 | 爬塔, 镇魂塔, 恶魔塔 | tower / demontower | CS_13035, CS_13038, SC_13752.. | config_dungeon_tower.luac, config_single_tower.luac, config_golden_tower.luac, config_treasure_data.luac, cfg_config_dungeon_tower.json, cfg_config_single_tower.json | partial (tower stub, demontower config) ⏳需MuMu取证 | mock_server round44 demontower fix + cfg_config_dungeon_tower.json / VERIFIED |
| SYS_DUNGEON_004 | Mystic Realm 秘境/遗迹 | 秘境, mijing | mijing (function 1011) |  | config_treasure_plane_data.luac, config_dungeon_jieyi.luac, config_dungeon_seal_demon_data.luac | client-only ⏳需MuMu取证 | mijing function id / VERIFIED |
| SYS_DUNGEON_005 | Shadow/Palace dungeon other | 其余副本 | dungeon* |  | config_dungeon_gods.luac, config_dungeon_seal_demon_data.luac, config_smjz.luac, config_primus.luac, config_golden_tower.luac | client-config only | config_dungeon_gods + smjz / STRONG_INFERENCE |

### SYS_DUNGEON_001 — Dungeon 副本
- **aliases**: 副本, 地牢
- **version**: 1.4.11
- **client_entry**: dungeon?
- **lua_modules**: tower_ctrl.luac
- **protocols**: CS_11700..11713?, CS_13028..
- **config_files**: config_dungeon_new.luac, config_dungeon_reward_desc.luac, config_dungeon_vip_single.luac, config_dungeon_vip_single2.luac, config_dungeon_research?
- **data_files**: dungeon_progress table
- **UI_files**: dungeon select
- **dependencies**: Battle, Rewards
- **server_state**: implemented
- **database_state**: dungeon_progress present
- **related_systems**: Battle, Endless, Tower
- **evidence**: dungeon_progress.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 副本难度/怪物数值/通关奖励

### SYS_DUNGEON_002 — Endless Dungeon 无尽/深渊
- **aliases**: 无尽, 深渊, endless
- **version**: 1.4.11
- **client_entry**: endless
- **lua_modules**: endless_form_ctrl.luac, endless_battle_ui.luac
- **protocols**: 
- **config_files**: config_dungeon_endless_data.luac
- **data_files**: dungeon_progress table
- **UI_files**: endless UI
- **dependencies**: Dungeon, Battle, Formation
- **server_state**: partial
- **database_state**: dungeon_progress shared
- **related_systems**: Dungeon, Tower
- **evidence**: config_dungeon_endless_data
- **confidence**: VERIFIED
- **implementation_status**: partial
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 无尽深渊数值/奖励

### SYS_DUNGEON_003 — Tower 塔
- **aliases**: 爬塔, 镇魂塔, 恶魔塔
- **version**: 1.4.11
- **client_entry**: tower / demontower
- **lua_modules**: tower_ctrl.luac, demontower_ctrl.luac, kunshentower_battleui.luac
- **protocols**: CS_13035, CS_13038, SC_13752..
- **config_files**: config_dungeon_tower.luac, config_single_tower.luac, config_golden_tower.luac, config_treasure_data.luac, cfg_config_dungeon_tower.json, cfg_config_single_tower.json
- **data_files**: dungeon_progress table
- **UI_files**: tower UI
- **dependencies**: Dungeon, Battle
- **server_state**: partial
- **database_state**: dungeon_progress shared
- **currencies**: tower_cent(10)
- **related_systems**: Dungeon, Endless
- **evidence**: mock_server round44 demontower fix + cfg_config_dungeon_tower.json
- **confidence**: VERIFIED
- **implementation_status**: partial (tower stub, demontower config)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 爬塔数值/奖励

### SYS_DUNGEON_004 — Mystic Realm 秘境/遗迹
- **aliases**: 秘境, mijing
- **version**: 1.4.11
- **client_entry**: mijing (function 1011)
- **protocols**: 
- **config_files**: config_treasure_plane_data.luac, config_dungeon_jieyi.luac, config_dungeon_seal_demon_data.luac
- **dependencies**: Dungeon
- **server_state**: not implemented
- **related_systems**: Dungeon, Treasure
- **evidence**: mijing function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 秘境数值/奖励

### SYS_DUNGEON_005 — Shadow/Palace dungeon other
- **aliases**: 其余副本
- **version**: 1.4.11
- **client_entry**: dungeon*
- **lua_modules**: kunshentower_battleui.luac, smjz
- **protocols**: 
- **config_files**: config_dungeon_gods.luac, config_dungeon_seal_demon_data.luac, config_smjz.luac, config_primus.luac, config_golden_tower.luac
- **dependencies**: Dungeon
- **server_state**: not implemented
- **related_systems**: Dungeon, God
- **evidence**: config_dungeon_gods + smjz
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

---

## L. 活动系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_ACT_001 | Sign-in/Check-in 签到 | 签到, 每日签到 | sign? | CS_14100 签到, CS_14101 | config_checkin.luac, config_seven_login.luac | implemented ⏳需MuMu取证 | sign_got.db + CS_14100/14101 / CONFIRMED |
| SYS_ACT_002 | Seven-Day Login 七日签到 | 七日登录, 七日活动 | seven login |  | config_seven_login.luac, config_fest_data.luac | partial | notice7day.luac + config_seven_login / VERIFIED |
| SYS_ACT_003 | Invest 投资 | 投资, invest | invest_sec (function 106) | CS_13901.. | config_invest.json, config_invest.luac, config_invest_dec.json, _invest_cfg.json | implemented | role_invest.db + invest_ctrl.luac / CONFIRMED |
| SYS_ACT_004 | Turntable/Lucky Draw 转盘抽奖 | 转盘, lucky_turntable, rotatetable, dial | rotatetable (function 8) / lucky_turntable (47) |  | config_gold_ernie_data.luac, config_ernie_data.luac, config_holiday_lucky_turntable_data.luac, config_holiday_dial_reward_data.luac, config_vip_ernie_data.luac, _dial_reward.json | partial (config+stub, no DB) ⏳需MuMu取证 | _dial_reward.json + config_ernie / VERIFIED |
| SYS_ACT_005 | Scratch Card 刮刮乐 | 刮卡, scratch | scratcher (function 51) |  | config_scratch_card.luac | client-config only | config_scratch_card only / STRONG_INFERENCE |
| SYS_ACT_006 | Festival/Operation Activity 节日/运营活动 | 节日活动, fest | fest* |  | config_fest_data.json, config_fest_data.luac, config_festival_goods.luac, config_friend_regress.luac, config_holiday_regress_data.luac, config_holiday_util.luac, config_holiday_balloon.luac, config_holiday_crowd_lottery.luac, config_holiday_order_mission.luac, config_helloween_data.luac, config_huaguo_mountain_data.luac, config_week_calendar.luac | client-event-data only ⏳需MuMu取证 | config_fest_data.json + holiday_* configs / VERIFIED |
| SYS_ACT_007 | Answer Quiz 答题 | 答题, answer | answer (function 3) |  | config_answer.luac, config_lantern_answer.luac | client-only ⏳需MuMu取证 | config_answer + answer function id / VERIFIED |
| SYS_ACT_008 | Guess 竞猜 | 竞猜, guess | guess (function 25) |  | config_fun.luac, config_player_guess? | client-only ⏳需MuMu取证 | guess function id / VERIFIED |
| SYS_ACT_009 | Money Tree 摇钱树 | 摇钱树, moneytree | moneytree (function 26) |  | config_money_tree.luac | implemented | role_tree.db + config_money_tree / CONFIRMED |
| SYS_ACT_010 | Pray/QiFu 祈福 | 祈福 | qifu? |  | config_qifu.luac, config_flying? | implemented ⏳需MuMu取证 | role_qifu.db + qifu_ctrl.luac / CONFIRMED |
| SYS_ACT_011 | Treasure Hunt 夺宝/探宝 | 夺宝, duobao | duobao (function 1013) | CS_13810..13817? | config_duobao.luac, config_treasure.luac, config_treasure_plane_data.luac, config_mission_treasure.luac, config_rune_treasure_data.luac, config_chest? | client-only ⏳需MuMu取证 | config_duobao + duobao function id / VERIFIED |
| SYS_ACT_012 | Return/Back Flow 回归 | 回归, 老玩家 | regress |  | config_friend_regress.luac, config_holiday_regress_data.luac | client-only | config_friend_regress / VERIFIED |
| SYS_ACT_013 | Gift Recharge events 充值活动 | 累计充值, 天降壕礼 | charge_double (62) / tianjianghaoli (117) |  | config_every_charge.luac, config_once_charge.luac, config_charge_double? | client-only | charge_double/tianjianghaoli function ids / VERIFIED |
| SYS_ACT_014 | Point/Qing Fu activities 点/dnf/live | 点券活动, dnf活动, 直播 | live? |  | config_dnf_data.luac, config_live.luac, config_source_data.luac | partial (point persisted) | role_point.db / VERIFIED |
| SYS_ACT_015 | Global Wish 全球许愿 | 许愿, global wish | 1008 julong? |  | config_global_wish_data.luac, config_fangyao.luac, config_party.luac | client-config only | config_global_wish_data / STRONG_INFERENCE |

### SYS_ACT_001 — Sign-in/Check-in 签到
- **aliases**: 签到, 每日签到
- **version**: 1.4.11
- **client_entry**: sign?
- **lua_modules**: dailysign_ctrl.luac
- **protocols**: CS_14100 签到, CS_14101
- **config_files**: config_checkin.luac, config_seven_login.luac
- **data_files**: sign_got table
- **UI_files**: sign-in panel
- **dependencies**: Rewards, Daily
- **server_state**: implemented
- **database_state**: sign_got present
- **rewards**: 签到礼
- **related_systems**: Daily, Seven Login
- **evidence**: sign_got.db + CS_14100/14101
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 签到奖励

### SYS_ACT_002 — Seven-Day Login 七日签到
- **aliases**: 七日登录, 七日活动
- **version**: 1.4.11
- **client_entry**: seven login
- **lua_modules**: notice7day.luac
- **protocols**: 
- **config_files**: config_seven_login.luac, config_fest_data.luac
- **data_files**: sign_got table
- **UI_files**: 7day panel
- **dependencies**: Sign-in
- **server_state**: partial
- **database_state**: sign_got shared
- **rewards**: 7天奖励
- **related_systems**: Sign-in, Festival
- **evidence**: notice7day.luac + config_seven_login
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_ACT_003 — Invest 投资
- **aliases**: 投资, invest
- **version**: 1.4.11
- **client_entry**: invest_sec (function 106)
- **lua_modules**: invest_ctrl.luac, invest_const.luac, invest_cost_ui.luac, invest_level_ui.luac, invest_model.luac, invest_panel.luac, invest_sec_panel.luac, invest_vip_ui.luac
- **protocols**: CS_13901..
- **config_files**: config_invest.json, config_invest.luac, config_invest_dec.json, _invest_cfg.json
- **data_files**: role_invest table
- **UI_files**: invest panel
- **dependencies**: Recharge, Economy
- **server_state**: implemented
- **database_state**: role_invest present
- **related_systems**: Recharge, VIP
- **evidence**: role_invest.db + invest_ctrl.luac
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_ACT_004 — Turntable/Lucky Draw 转盘抽奖
- **aliases**: 转盘, lucky_turntable, rotatetable, dial
- **version**: 1.4.11
- **client_entry**: rotatetable (function 8) / lucky_turntable (47)
- **protocols**: 
- **config_files**: config_gold_ernie_data.luac, config_ernie_data.luac, config_holiday_lucky_turntable_data.luac, config_holiday_dial_reward_data.luac, config_vip_ernie_data.luac, _dial_reward.json
- **UI_files**: turntable
- **dependencies**: Mall, Economy
- **server_state**: partial (dial reward stub)
- **related_systems**: Activity Suite, Scratcher
- **evidence**: _dial_reward.json + config_ernie
- **confidence**: VERIFIED
- **implementation_status**: partial (config+stub, no DB)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 转盘概率/奖励

### SYS_ACT_005 — Scratch Card 刮刮乐
- **aliases**: 刮卡, scratch
- **version**: 1.4.11
- **client_entry**: scratcher (function 51)
- **protocols**: 
- **config_files**: config_scratch_card.luac
- **UI_files**: scratch UI
- **dependencies**: Lottery
- **server_state**: not implemented
- **related_systems**: Turntable
- **evidence**: config_scratch_card only
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_ACT_006 — Festival/Operation Activity 节日/运营活动
- **aliases**: 节日活动, fest
- **version**: 1.4.11
- **client_entry**: fest*
- **lua_modules**: activity_ctrl.luac, festival? (activity_ctrl.luac in form2)
- **protocols**: 
- **config_files**: config_fest_data.json, config_fest_data.luac, config_festival_goods.luac, config_friend_regress.luac, config_holiday_regress_data.luac, config_holiday_util.luac, config_holiday_balloon.luac, config_holiday_crowd_lottery.luac, config_holiday_order_mission.luac, config_helloween_data.luac, config_huaguo_mountain_data.luac, config_week_calendar.luac
- **UI_files**: festival panels
- **dependencies**: Activity infra
- **server_state**: not implemented (event data only)
- **related_systems**: Activity Suite
- **evidence**: config_fest_data.json + holiday_* configs
- **confidence**: VERIFIED
- **implementation_status**: client-event-data only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 节日/运营活动奖励

### SYS_ACT_007 — Answer Quiz 答题
- **aliases**: 答题, answer
- **version**: 1.4.11
- **client_entry**: answer (function 3)
- **protocols**: 
- **config_files**: config_answer.luac, config_lantern_answer.luac
- **UI_files**: quiz
- **server_state**: not implemented
- **related_systems**: Guess, Activity
- **evidence**: config_answer + answer function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 答题题库/奖励

### SYS_ACT_008 — Guess 竞猜
- **aliases**: 竞猜, guess
- **version**: 1.4.11
- **client_entry**: guess (function 25)
- **protocols**: 
- **config_files**: config_fun.luac, config_player_guess?
- **server_state**: not implemented
- **related_systems**: Answer
- **evidence**: guess function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 竞猜赔率/奖励

### SYS_ACT_009 — Money Tree 摇钱树
- **aliases**: 摇钱树, moneytree
- **version**: 1.4.11
- **client_entry**: moneytree (function 26)
- **protocols**: 
- **config_files**: config_money_tree.luac
- **data_files**: role_tree table
- **UI_files**: money tree
- **dependencies**: Economy, Daily
- **server_state**: implemented
- **database_state**: role_tree present
- **rewards**: 金币
- **currencies**: gold
- **related_systems**: Daily, Qifu
- **evidence**: role_tree.db + config_money_tree
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_ACT_010 — Pray/QiFu 祈福
- **aliases**: 祈福
- **version**: 1.4.11
- **client_entry**: qifu?
- **lua_modules**: qifu_ctrl.luac, qifu_model.luac, qifu_view.luac, qifu_cell.luac, qifu_redpaper_item.luac, qifu_redpaper.luac
- **protocols**: 
- **config_files**: config_qifu.luac, config_flying?
- **data_files**: role_qifu table
- **UI_files**: qifu/redpacket
- **dependencies**: Economy, Daily
- **server_state**: implemented
- **database_state**: role_qifu present
- **related_systems**: Money Tree, Red Packet
- **evidence**: role_qifu.db + qifu_ctrl.luac
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 祈福数值/产出

### SYS_ACT_011 — Treasure Hunt 夺宝/探宝
- **aliases**: 夺宝, duobao
- **version**: 1.4.11
- **client_entry**: duobao (function 1013)
- **lua_modules**: duobao?
- **protocols**: CS_13810..13817?
- **config_files**: config_duobao.luac, config_treasure.luac, config_treasure_plane_data.luac, config_mission_treasure.luac, config_rune_treasure_data.luac, config_chest?
- **UI_files**: duobao UI
- **dependencies**: Economy, Dungeon
- **server_state**: not implemented
- **related_systems**: Treasure, Secret Realm
- **evidence**: config_duobao + duobao function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 夺宝概率/奖励

### SYS_ACT_012 — Return/Back Flow 回归
- **aliases**: 回归, 老玩家
- **version**: 1.4.11
- **client_entry**: regress
- **protocols**: 
- **config_files**: config_friend_regress.luac, config_holiday_regress_data.luac
- **UI_files**: regress panel
- **dependencies**: Activity
- **server_state**: not implemented
- **related_systems**: Activity Suite
- **evidence**: config_friend_regress
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_ACT_013 — Gift Recharge events 充值活动
- **aliases**: 累计充值, 天降壕礼
- **version**: 1.4.11
- **client_entry**: charge_double (62) / tianjianghaoli (117)
- **protocols**: 
- **config_files**: config_every_charge.luac, config_once_charge.luac, config_charge_double?
- **dependencies**: Recharge
- **server_state**: not implemented
- **related_systems**: Recharge, Level
- **evidence**: charge_double/tianjianghaoli function ids
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_ACT_014 — Point/Qing Fu activities 点/dnf/live
- **aliases**: 点券活动, dnf活动, 直播
- **version**: 1.4.11
- **client_entry**: live?
- **protocols**: 
- **config_files**: config_dnf_data.luac, config_live.luac, config_source_data.luac
- **data_files**: role_point table
- **server_state**: implemented (role_point) / activities not hooked
- **database_state**: role_point present
- **related_systems**: Activity
- **evidence**: role_point.db
- **confidence**: VERIFIED
- **implementation_status**: partial (point persisted)

### SYS_ACT_015 — Global Wish 全球许愿
- **aliases**: 许愿, global wish
- **version**: 1.4.11
- **client_entry**: 1008 julong?
- **protocols**: 
- **config_files**: config_global_wish_data.luac, config_fangyao.luac, config_party.luac
- **server_state**: not implemented
- **related_systems**: Festival
- **evidence**: config_global_wish_data
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

---

## M. 社交系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_SOCIAL_001 | Chat System | 聊天, 社交 | chat? | CS_10800.. | config_chat_bubble.luac, config_sns.luac | implemented | role_chat.db / CONFIRMED |
| SYS_SOCIAL_002 | Friend System | 好友 | friend (function 6000) |  | config_friend_zone_data.luac, config_friend_regress.luac | partial | friend function id / VERIFIED |
| SYS_SOCIAL_003 | Moments/朋友圈 | 朋友圈, 动态 | friend zone |  | config_friend_zone_data.luac | implemented | role_moments.db / CONFIRMED |
| SYS_SOCIAL_004 | Guild 公会 | 公会, 帮派 | guild (function 9000) | CS_17500..17519, CS_19509.. | config_guild.luac, config_guild_animal.luac, config_guild_exploit_data.luac, config_guild_lucky_data.luac, config_guild_mission.luac, config_guild_mission_data.luac, config_guild_pray.luac, config_guild_skill_data.luac, config_guild_task_data.luac, config_guild_tree_data.luac, config_guild_union.luac, config_guild_welcome_data.luac, config_guild_match_war_data.luac | implemented (core guild, sub-systems partial) | role_guild.db / CONFIRMED |
| SYS_SOCIAL_005 | Marriage 结婚 | 婚姻, 结婚系统 | wedding (function 17) | 18300, 18301, 18302, 18303, 18313, 18314, 18316, 18318, 18321, 18322 | config_marry_data.luac, config_marry_eqm_data.luac, config_spouse.luac, config_mission_marry.luac | implemented (core loop) ⏳需MuMu取证 | tools/test_marry_propose.py ALL PASS (2 roles full proposal loop) / VERIFIED |
| SYS_SOCIAL_006 | Jiebai Soulmate 结拜 | 结拜, 义结金兰 | jiebailiucheng (110) / jiebaitoupiao (506) | 19505, 19511, 19512, 19513, 19514, 19524, 19530, 19533, 19536 | config_jiebai_data.luac, config_dungeon_jieyi.luac | implemented (core + multi-member) ⏳需MuMu取证 | tools/test_jiebai_multi.py ALL PASS (2 roles invite->confirm->2 members) / VERIFIED |
| SYS_SOCIAL_007 | Flower/Gift 送花 | 送花, 花 | flower (function 23) |  | config_flower.luac | client-only | config_flower + flower function id / VERIFIED |
| SYS_SOCIAL_008 | Party 宴会/派对 | 宴会, party | party? |  | config_party.luac, config_fangyao.luac | client-config only | config_party only / STRONG_INFERENCE |
| SYS_SOCIAL_009 | Guild Wars 公会战 | 公会战, 宗门战, guildwars | gangwars (14) / guildwars (15) / kuafu_guildwars (24) / guildmatchwar (1012) | CS_17501, CS_195?, CS_130?... | config_guild_match_war_data.luac, config_guild_tree_data.luac, config_sm_war_data.luac | partial (dispatch stub) | mock_server line 15953 handles guildwars_ctrl type branch / VERIFIED |
| SYS_SOCIAL_010 | Guild Tree/Animal/Skill sub | 公会科技, 公会神兽, 公会技能 | guild |  | config_guild_tree_data.luac, config_guild_animal.luac, config_guild_skill_data.luac, config_guild_pray.luac, config_guild_welcome_data.luac, config_guild_exploit_data.luac, config_guild_lucky_data.luac | partial | guild sub configs present / VERIFIED |

### SYS_SOCIAL_001 — Chat System
- **aliases**: 聊天, 社交
- **version**: 1.4.11
- **client_entry**: chat?
- **protocols**: CS_10800..
- **config_files**: config_chat_bubble.luac, config_sns.luac
- **data_files**: role_chat table
- **UI_files**: chat window
- **server_state**: implemented
- **database_state**: role_chat present
- **related_systems**: Friend, Social
- **evidence**: role_chat.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_SOCIAL_002 — Friend System
- **aliases**: 好友
- **version**: 1.4.11
- **client_entry**: friend (function 6000)
- **lua_modules**: friend_zone?
- **protocols**: 
- **config_files**: config_friend_zone_data.luac, config_friend_regress.luac
- **data_files**: role_moments? / friends via chat?
- **UI_files**: friend list
- **dependencies**: Chat
- **server_state**: partial
- **database_state**: no dedicated friend table
- **related_systems**: Chat, Moments
- **evidence**: friend function id
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_SOCIAL_003 — Moments/朋友圈
- **aliases**: 朋友圈, 动态
- **version**: 1.4.11
- **client_entry**: friend zone
- **protocols**: 
- **config_files**: config_friend_zone_data.luac
- **data_files**: role_moments table
- **UI_files**: moments
- **dependencies**: Friend
- **server_state**: implemented
- **database_state**: role_moments present
- **related_systems**: Friend, Chat
- **evidence**: role_moments.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_SOCIAL_004 — Guild 公会
- **aliases**: 公会, 帮派
- **version**: 1.4.11
- **client_entry**: guild (function 9000)
- **lua_modules**: guild_constants.luac, guild_action_item.luac, guild_race_const.luac, guild_race_data.luac, guild_race_ctrl.luac, guildwars_ctrl.luac
- **protocols**: CS_17500..17519, CS_19509..
- **config_files**: config_guild.luac, config_guild_animal.luac, config_guild_exploit_data.luac, config_guild_lucky_data.luac, config_guild_mission.luac, config_guild_mission_data.luac, config_guild_pray.luac, config_guild_skill_data.luac, config_guild_task_data.luac, config_guild_tree_data.luac, config_guild_union.luac, config_guild_welcome_data.luac, config_guild_match_war_data.luac
- **data_files**: role_guild table
- **UI_files**: guild UI
- **dependencies**: Social, Economy
- **server_state**: implemented (core)
- **database_state**: role_guild present
- **currencies**: guild_contrib(8),guild_active(24)
- **related_systems**: Guild Wars, Guild Party, Guild Mission
- **evidence**: role_guild.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented (core guild, sub-systems partial)

### SYS_SOCIAL_005 — Marriage 结婚
- **aliases**: 婚姻, 结婚系统
- **version**: 1.4.11
- **client_entry**: wedding (function 17)
- **protocols**: 18300, 18301, 18302, 18303, 18313, 18314, 18316, 18318, 18321, 18322
- **config_files**: config_marry_data.luac, config_marry_eqm_data.luac, config_spouse.luac, config_mission_marry.luac
- **data_files**: role_marry (SQLite), role_marry_propose (SQLite)
- **UI_files**: wedding panel
- **dependencies**: Social, Team
- **server_state**: implemented (propose->accept->marry->divorce->ring); target via server-side intent table
- **database_state**: role_marry, role_marry_propose
- **currencies**: marriage(25)
- **related_systems**: Jiebai, Team
- **evidence**: tools/test_marry_propose.py ALL PASS (2 roles full proposal loop)
- **confidence**: VERIFIED
- **implementation_status**: implemented (core loop)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: PHASE2.5：18300/18301/18302/18303 双角色实测。★CS_18300 为空消息，客户端不上传对象(反汇编 wedding_ctrl 证实)⇒目标由服务端意向表 role_marry_propose 承载(机制本身 UNKNOWN，不冒充原版)。婚宴 18304-18309 未实现。 [需 MuMu 运行时取证] 结婚消耗/奖励数值 [需 MuMu 运行时取证] 结婚数值/消耗

### SYS_SOCIAL_006 — Jiebai Soulmate 结拜
- **aliases**: 结拜, 义结金兰
- **version**: 1.4.11
- **client_entry**: jiebailiucheng (110) / jiebaitoupiao (506)
- **protocols**: 19505, 19511, 19512, 19513, 19514, 19524, 19530, 19533, 19536
- **config_files**: config_jiebai_data.luac, config_dungeon_jieyi.luac
- **data_files**: role_jiebai (SQLite)
- **UI_files**: jieyi panel
- **dependencies**: Social, Team
- **server_state**: implemented (create/space/member list/invite/confirm/upgrade/cancel)
- **database_state**: role_jiebai
- **currencies**: jiebai_cent(33)
- **related_systems**: Marriage, Friend, Team
- **evidence**: tools/test_jiebai_multi.py ALL PASS (2 roles invite->confirm->2 members)
- **confidence**: VERIFIED
- **implementation_status**: implemented (core + multi-member)
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: PHASE2.6：19505/19511/19512/19513/19514/19524/19530/19533/19536；19511/19513=推送。多人(2角色)已实测。注意 SC_19514/19530 无 code/msg。其余 195xx(投票/技能/称号) 仍为通用回执。 [需 MuMu 运行时取证] 结拜数值/属性加成 [需 MuMu 运行时取证] 结拜数值/加成

### SYS_SOCIAL_007 — Flower/Gift 送花
- **aliases**: 送花, 花
- **version**: 1.4.11
- **client_entry**: flower (function 23)
- **protocols**: 
- **config_files**: config_flower.luac
- **dependencies**: Marriage, Social
- **server_state**: not implemented
- **currencies**: charm(17)
- **related_systems**: Marriage, Rank
- **evidence**: config_flower + flower function id
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_SOCIAL_008 — Party 宴会/派对
- **aliases**: 宴会, party
- **version**: 1.4.11
- **client_entry**: party?
- **protocols**: 
- **config_files**: config_party.luac, config_fangyao.luac
- **UI_files**: party
- **dependencies**: Marriage
- **server_state**: not implemented
- **related_systems**: Marriage
- **evidence**: config_party only
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_SOCIAL_009 — Guild Wars 公会战
- **aliases**: 公会战, 宗门战, guildwars
- **version**: 1.4.11
- **client_entry**: gangwars (14) / guildwars (15) / kuafu_guildwars (24) / guildmatchwar (1012)
- **lua_modules**: guildwars_ctrl.luac, guild_race_ctrl.luac
- **protocols**: CS_17501, CS_195?, CS_130?...
- **config_files**: config_guild_match_war_data.luac, config_guild_tree_data.luac, config_sm_war_data.luac
- **data_files**: role_guild table
- **UI_files**: war UI
- **dependencies**: Guild, Battle
- **server_state**: partial (mock handles 17501 by type)
- **database_state**: role_guild
- **related_systems**: Guild, Cross-server, Peakwar
- **evidence**: mock_server line 15953 handles guildwars_ctrl type branch
- **confidence**: VERIFIED
- **implementation_status**: partial (dispatch stub)

### SYS_SOCIAL_010 — Guild Tree/Animal/Skill sub
- **aliases**: 公会科技, 公会神兽, 公会技能
- **version**: 1.4.11
- **client_entry**: guild
- **protocols**: 
- **config_files**: config_guild_tree_data.luac, config_guild_animal.luac, config_guild_skill_data.luac, config_guild_pray.luac, config_guild_welcome_data.luac, config_guild_exploit_data.luac, config_guild_lucky_data.luac
- **data_files**: role_guild table
- **dependencies**: Guild
- **server_state**: partial
- **database_state**: role_guild
- **related_systems**: Guild
- **evidence**: guild sub configs present
- **confidence**: VERIFIED
- **implementation_status**: partial

---

## N. 商业系统 / 对抗

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_COMM_001 | Rank 排行榜 | 排行榜 | rank? / actionrank (16) | CS_16900..16903 | config_rank.luac, config_rank.full.json, config_rank.asm | partial ⏳需MuMu取证 | rank_ctrl.luac + config_rank / VERIFIED |
| SYS_COMM_002 | Arena 竞技场 | 竞技场 | arena? | CS_11300..11310, CS_11301 | config_arena_data.luac, config_arena_msg.luac, config_trophy_arena_data.luac | implemented ⏳需MuMu取证 | arena_state/arena_record.db / CONFIRMED |
| SYS_COMM_003 | Peakwar 巅峰战 | 巅峰战, 精英赛 | peakwar (function 28) | CS_130?.., CS_113?.. | config_peak_war_data.luac | implemented | peakwar_state.db + config_peak_war_data / CONFIRMED |
| SYS_COMM_004 | Race 竞速/种族战 | 竞速, race, 跨服竞速 | race (function 12) / crossrace (22) | CS_130?.. | config_race? | implemented | race_state.db + race_ctrl.luac / CONFIRMED |
| SYS_COMM_005 | Cross-server 跨服 | 跨服, cross | crossrace (22) / kuafu_guildwars (24) | 30100~31299 cross? | — | not implemented ⏳需MuMu取证 | cross_ctrl.luac; mock_server single-process / STRONG_INFERENCE |
| SYS_COMM_006 | Mining 采矿 | 采矿, 矿脉 | mining? |  | config_mining.luac, config_mine_new.luac, config_mine_guild_data.luac | client-config only ⏳需MuMu取证 | config_mining + config_mine_guild_data / VERIFIED |
| SYS_COMM_007 | Manor/Oasis 庄园/领地 | 庄园, manor | manor? |  | config_manor.luac, config_garden_data.luac, config_build.luac | implemented (build persistent) | role_build.db + build_ctrl.luac + config_manor / CONFIRMED |
| SYS_COMM_008 | Attack City 攻城/领土战 | 攻城, 领地战 | qiangdao (102)? |  | config_attack_city.luac | client-config only | config_attack_city / STRONG_INFERENCE |
| SYS_COMM_009 | Freight/Escort 押镖 | 押镖, 护送 | escort? |  | config_freight.luac, config_mission_escort.luac | client-config only ⏳需MuMu取证 | config_freight / STRONG_INFERENCE |
| SYS_COMM_010 | Gold/JinYin Tower activities | 金银塔, jinyinta | jinyinta (function 56) |  | config_golden_tower.luac, config_single_tower.luac | client-only ⏳需MuMu取证 | jinyinta function id / VERIFIED |

### SYS_COMM_001 — Rank 排行榜
- **aliases**: 排行榜
- **version**: 1.4.11
- **client_entry**: rank? / actionrank (16)
- **lua_modules**: rank_ctrl.luac, rank_data.luac, rank_data_vo.luac, rank_title.luac
- **protocols**: CS_16900..16903
- **config_files**: config_rank.luac, config_rank.full.json, config_rank.asm
- **data_files**: derived from other tables
- **UI_files**: rank UI
- **dependencies**: Title
- **server_state**: partial (derived)
- **database_state**: no dedicated rank table
- **related_systems**: Title, Arena, Power
- **evidence**: rank_ctrl.luac + config_rank
- **confidence**: VERIFIED
- **implementation_status**: partial
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 排行榜排序字段/实时值

### SYS_COMM_002 — Arena 竞技场
- **aliases**: 竞技场
- **version**: 1.4.11
- **client_entry**: arena?
- **lua_modules**: trophy_arena_ctrl.luac
- **protocols**: CS_11300..11310, CS_11301
- **config_files**: config_arena_data.luac, config_arena_msg.luac, config_trophy_arena_data.luac
- **data_files**: arena_state table, arena_record table
- **UI_files**: arena UI
- **dependencies**: Battle, Rank
- **server_state**: implemented
- **database_state**: arena_state, arena_record present
- **currencies**: arena_cent(11),arena_soul(31),trophy(18)
- **related_systems**: Rank, PvP
- **evidence**: arena_state/arena_record.db
- **confidence**: CONFIRMED
- **implementation_status**: implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 竞技场匹配/战斗数值/积分

### SYS_COMM_003 — Peakwar 巅峰战
- **aliases**: 巅峰战, 精英赛
- **version**: 1.4.11
- **client_entry**: peakwar (function 28)
- **lua_modules**: peakvideo_*.luac
- **protocols**: CS_130?.., CS_113?..
- **config_files**: config_peak_war_data.luac
- **data_files**: peakwar_state table
- **UI_files**: peakwar UI
- **dependencies**: Battle, Rank
- **server_state**: implemented
- **database_state**: peakwar_state present
- **currencies**: peak_point(30)
- **related_systems**: Arena, Godwar
- **evidence**: peakwar_state.db + config_peak_war_data
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_COMM_004 — Race 竞速/种族战
- **aliases**: 竞速, race, 跨服竞速
- **version**: 1.4.11
- **client_entry**: race (function 12) / crossrace (22)
- **lua_modules**: race_ctrl.luac, race_ui_*.luac, guild_race_ctrl.luac, cross_ctrl.luac
- **protocols**: CS_130?..
- **config_files**: config_race?
- **data_files**: race_state table
- **UI_files**: race UI
- **dependencies**: Battle
- **server_state**: implemented
- **database_state**: race_state present
- **related_systems**: Guild Wars, Peakwar
- **evidence**: race_state.db + race_ctrl.luac
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_COMM_005 — Cross-server 跨服
- **aliases**: 跨服, cross
- **version**: 1.4.11
- **client_entry**: crossrace (22) / kuafu_guildwars (24)
- **lua_modules**: cross_ctrl.luac
- **protocols**: 30100~31299 cross?
- **dependencies**: All PvP
- **server_state**: not implemented (single-process)
- **related_systems**: Race, Guild Wars, Godwar
- **evidence**: cross_ctrl.luac; mock_server single-process
- **confidence**: STRONG_INFERENCE
- **implementation_status**: not implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 跨服匹配/数值

### SYS_COMM_006 — Mining 采矿
- **aliases**: 采矿, 矿脉
- **version**: 1.4.11
- **client_entry**: mining?
- **protocols**: 
- **config_files**: config_mining.luac, config_mine_new.luac, config_mine_guild_data.luac
- **dependencies**: Guild
- **server_state**: not implemented
- **related_systems**: Guild
- **evidence**: config_mining + config_mine_guild_data
- **confidence**: VERIFIED
- **implementation_status**: client-config only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 采矿产出

### SYS_COMM_007 — Manor/Oasis 庄园/领地
- **aliases**: 庄园, manor
- **version**: 1.4.11
- **client_entry**: manor?
- **lua_modules**: build_ctrl.luac, hunger.luac
- **protocols**: 
- **config_files**: config_manor.luac, config_garden_data.luac, config_build.luac
- **data_files**: role_build table, role_build_learn table
- **UI_files**: manor/build UI
- **dependencies**: Economy
- **server_state**: implemented (build)
- **database_state**: role_build, role_build_learn present
- **related_systems**: Guild, Tree
- **evidence**: role_build.db + build_ctrl.luac + config_manor
- **confidence**: CONFIRMED
- **implementation_status**: implemented (build persistent)

### SYS_COMM_008 — Attack City 攻城/领土战
- **aliases**: 攻城, 领地战
- **version**: 1.4.11
- **client_entry**: qiangdao (102)?
- **protocols**: 
- **config_files**: config_attack_city.luac
- **dependencies**: Guild, Battle
- **server_state**: not implemented
- **related_systems**: Guild Wars
- **evidence**: config_attack_city
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_COMM_009 — Freight/Escort 押镖
- **aliases**: 押镖, 护送
- **version**: 1.4.11
- **client_entry**: escort?
- **protocols**: 
- **config_files**: config_freight.luac, config_mission_escort.luac
- **dependencies**: Mission, Battle
- **server_state**: not implemented
- **related_systems**: Mission
- **evidence**: config_freight
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 押镖奖励/劫镖

### SYS_COMM_010 — Gold/JinYin Tower activities
- **aliases**: 金银塔, jinyinta
- **version**: 1.4.11
- **client_entry**: jinyinta (function 56)
- **protocols**: 
- **config_files**: config_golden_tower.luac, config_single_tower.luac
- **dependencies**: Dungeon, Economy
- **server_state**: not implemented
- **currencies**: gold,coral(13)
- **related_systems**: Tower
- **evidence**: jinyinta function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）
- **notes**: [需 MuMu 运行时取证] 金银塔奖励

---

## O. GM 系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_GM_001 | GM Tools | GM命令, 调试 | gm? | CS_10922..10932?, CS_11999? | config_gm_cmd.luac, config_client.luac | implemented | config_gm_cmd + battle_debug + protocol gm_protocol.md / CONFIRMED |

### SYS_GM_001 — GM Tools
- **aliases**: GM命令, 调试
- **version**: 1.4.11
- **client_entry**: gm?
- **lua_modules**: battle_debug.luac, gm? (config_gm_cmd)
- **protocols**: CS_10922..10932?, CS_11999?
- **config_files**: config_gm_cmd.luac, config_client.luac
- **UI_files**: GM panel
- **dependencies**: all
- **server_state**: implemented (debug cmds)
- **related_systems**: all
- **evidence**: config_gm_cmd + battle_debug + protocol gm_protocol.md
- **confidence**: CONFIRMED
- **implementation_status**: implemented

---

## P. 后台系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_BACK_001 | Server Backend/DB | 后台, 数据库 | (server) | — | — | implemented | server/state/roles.db 48 tables / CONFIRMED |
| SYS_BACK_002 | Cross-server backend | 跨服后台 | (server) | — | — | not implemented | single-process server / STRONG_INFERENCE |

### SYS_BACK_001 — Server Backend/DB
- **aliases**: 后台, 数据库
- **version**: 1.4.11
- **client_entry**: (server)
- **data_files**: roles.db / jstm.db
- **UI_files**: (admin)
- **server_state**: implemented
- **database_state**: all tables in roles.db
- **related_systems**: all
- **evidence**: server/state/roles.db 48 tables
- **confidence**: CONFIRMED
- **implementation_status**: implemented

### SYS_BACK_002 — Cross-server backend
- **aliases**: 跨服后台
- **version**: 1.4.11
- **client_entry**: (server)
- **server_state**: not implemented
- **evidence**: single-process server
- **confidence**: STRONG_INFERENCE
- **implementation_status**: not implemented

---

## Q. 隐藏/未归类系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_HIDDEN_001 | Seal System 封印 | 封印 | seal? |  | config_seal.luac, config_dungeon_seal_demon_data.luac, config_fangyao.luac | client-config only | config_seal / STRONG_INFERENCE |
| SYS_HIDDEN_002 | XiuLuo 修罗 | 修罗, xiuluo | xiuluo? |  | config_xiuluo_data.luac | client-config only | config_xiuluo_data / STRONG_INFERENCE |
| SYS_HIDDEN_003 | Chief 会长/百官 | 会长, 首席 | chief (function 41) |  | config_chief_award_data.luac | client-only | chief function id + config_chief_award / VERIFIED |
| SYS_HIDDEN_004 | Star Soul 星魂 | 星魂, xinghun, soulstar | xinghun (function 28000) |  | config_rune_star? | partial | soulstar_ctrl.luac + xinghun function id / VERIFIED |
| SYS_HIDDEN_005 | God Redemption 神位/神减免 | 神灵, godredeem | god? |  | config_dungeon_gods.luac, config_god_unite_data.luac | client-only / not hooked | _tmp_god godredeem_ctrl.modules / VERIFIED |
| SYS_HIDDEN_006 | Dragon 神龙/巨龙 | 神龙, 巨龙 | julong (function 1008) |  | config_dragon.luac, config_golden_dragon? | client-only | config_dragon + julong function id / VERIFIED |
| SYS_HIDDEN_007 | Balloon 气球/多种活动 | 气球, action_balloon | action_balloon (function 48) |  | config_holiday_balloon.luac | client-only | action_balloon function id / VERIFIED |

### SYS_HIDDEN_001 — Seal System 封印
- **aliases**: 封印
- **version**: 1.4.11
- **client_entry**: seal?
- **protocols**: 
- **config_files**: config_seal.luac, config_dungeon_seal_demon_data.luac, config_fangyao.luac
- **dependencies**: Dungeon, Boss
- **server_state**: not implemented
- **related_systems**: Boss, Demon
- **evidence**: config_seal
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_HIDDEN_002 — XiuLuo 修罗
- **aliases**: 修罗, xiuluo
- **version**: 1.4.11
- **client_entry**: xiuluo?
- **protocols**: 
- **config_files**: config_xiuluo_data.luac
- **dependencies**: PvP
- **server_state**: not implemented
- **related_systems**: Arena
- **evidence**: config_xiuluo_data
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_HIDDEN_003 — Chief 会长/百官
- **aliases**: 会长, 首席
- **version**: 1.4.11
- **client_entry**: chief (function 41)
- **protocols**: 
- **config_files**: config_chief_award_data.luac
- **dependencies**: Rank
- **server_state**: not implemented
- **related_systems**: Rank
- **evidence**: chief function id + config_chief_award
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_HIDDEN_004 — Star Soul 星魂
- **aliases**: 星魂, xinghun, soulstar
- **version**: 1.4.11
- **client_entry**: xinghun (function 28000)
- **lua_modules**: soulstar_ctrl.luac
- **protocols**: 
- **config_files**: config_rune_star?
- **data_files**: role_runes table?
- **UI_files**: soul star
- **dependencies**: Rune, Wing
- **server_state**: partial
- **database_state**: role_runes?
- **related_systems**: Rune, Fate
- **evidence**: soulstar_ctrl.luac + xinghun function id
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_HIDDEN_005 — God Redemption 神位/神减免
- **aliases**: 神灵, godredeem
- **version**: 1.4.11
- **client_entry**: god?
- **lua_modules**: godredeem_ctrl.luac, godredeem_data.luac, godredeem_view.luac, godredeem_panel.luac, godredeem_item.luac, godredeem_aptitude*.luac
- **protocols**: 
- **config_files**: config_dungeon_gods.luac, config_god_unite_data.luac
- **UI_files**: god redeem UI
- **dependencies**: Partner
- **server_state**: not implemented
- **related_systems**: Partner, Dungeon gods
- **evidence**: _tmp_god godredeem_ctrl.modules
- **confidence**: VERIFIED
- **implementation_status**: client-only / not hooked

### SYS_HIDDEN_006 — Dragon 神龙/巨龙
- **aliases**: 神龙, 巨龙
- **version**: 1.4.11
- **client_entry**: julong (function 1008)
- **protocols**: 
- **config_files**: config_dragon.luac, config_golden_dragon?
- **server_state**: not implemented
- **evidence**: config_dragon + julong function id
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_HIDDEN_007 — Balloon 气球/多种活动
- **aliases**: 气球, action_balloon
- **version**: 1.4.11
- **client_entry**: action_balloon (function 48)
- **protocols**: 
- **config_files**: config_holiday_balloon.luac
- **dependencies**: Activity
- **server_state**: not implemented
- **related_systems**: Festival
- **evidence**: action_balloon function id
- **confidence**: VERIFIED
- **implementation_status**: client-only

---

## R. 未知系统

| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |
|---|---|---|---|---|---|---|---|
| SYS_UNKNOWN_001 | Dan War / 丹药战 | 丹药, dan_war | ?? |  | config_dan_war.luac | client-config only | config_dan_war + dan_point currency / UNKNOWN |
| SYS_UNKNOWN_002 | YunYing Ops systems | 运营活动 | 33/34/37/40/101/103 etc (unnamed function ids) |  | config_function.json ids 33,34,37,40,101,103... | unidentified ops entries | config_function.json unnamed ids / UNKNOWN |
| SYS_UNKNOWN_003 | Insight 顿悟/洞察 | 顿悟, 洞察 | insight? |  | config_insight.luac | partial | config_insight + ROLE_DEFAULTS insight_status / VERIFIED |
| SYS_UNKNOWN_004 | Color/Head system | 染色, color | color? |  | config_color.luac, config_color_code.luac | client-config only | config_color* / UNKNOWN |

### SYS_UNKNOWN_001 — Dan War / 丹药战
- **aliases**: 丹药, dan_war
- **version**: 1.4.11
- **client_entry**: ??
- **protocols**: 
- **config_files**: config_dan_war.luac
- **server_state**: not implemented
- **currencies**: dan_point(23)
- **evidence**: config_dan_war + dan_point currency
- **confidence**: UNKNOWN
- **implementation_status**: client-config only

### SYS_UNKNOWN_002 — YunYing Ops systems
- **aliases**: 运营活动
- **version**: 1.4.11
- **client_entry**: 33/34/37/40/101/103 etc (unnamed function ids)
- **protocols**: 
- **config_files**: config_function.json ids 33,34,37,40,101,103...
- **dependencies**: Activity
- **server_state**: not implemented
- **related_systems**: Activity
- **evidence**: config_function.json unnamed ids
- **confidence**: UNKNOWN
- **implementation_status**: unidentified ops entries

### SYS_UNKNOWN_003 — Insight 顿悟/洞察
- **aliases**: 顿悟, 洞察
- **version**: 1.4.11
- **client_entry**: insight?
- **protocols**: 
- **config_files**: config_insight.luac
- **data_files**: roles.insight_status field
- **dependencies**: Skill
- **server_state**: partial
- **database_state**: roles.insight_status field only
- **related_systems**: Skill, Practice
- **evidence**: config_insight + ROLE_DEFAULTS insight_status
- **confidence**: VERIFIED
- **implementation_status**: partial

### SYS_UNKNOWN_004 — Color/Head system
- **aliases**: 染色, color
- **version**: 1.4.11
- **client_entry**: color?
- **protocols**: 
- **config_files**: config_color.luac, config_color_code.luac
- **dependencies**: Appearance
- **server_state**: not implemented
- **related_systems**: Fashion
- **evidence**: config_color*
- **confidence**: UNKNOWN
- **implementation_status**: client-config only

---

