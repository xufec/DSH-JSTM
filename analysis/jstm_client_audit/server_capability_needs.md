# 每系统服务端能力需求 server_capability_needs

> PHASE C0 只读审计。逐系统列出需要的服务端能力（接口 / 权威状态 / 持久化 / GM），标注【已具备】/【部分】/【缺失】+ 证据。
> 行号指 `server/mock_server.py`；模块指 `server/<mod>/`；145/145 为 minloop 自检基线。

## 通用底座（所有系统共享，已具备）

- 会话/账号：account/、session/（mock_server.py:9968 cmd==1110；:9922 心跳）。【已具备】
- 持久化：persistence/db.py（db_conn/db_release），roles.db 全表；奖励幂等 reward_log(transaction_id)。【已具备】
- 资产统一出口：currency/service（db_get/add/set_assets）。【已具备】
- 属性/战力：attribute/service、power/service（10304 战力 :17208；10306 :17189）。【已具备】
- 客户端同步：SessionRegistry.push_to_rid；SC_10301/2/3。【已具备】
- GM 面：HTTP /DSH_ADMIN/setlevel|setassets|setcharge|reward_log|ach_list|battle_replay。【已具备】
- 自检基线：server/minloop/min_loop_server.py + selftest.py → 145/145。【已具备】

## 逐系统服务端能力

### SYS_CORE_001 Account Login 账号登录 — 【已具备】

- **需要的能力**：接口 `CS_1110 AccountLogin, CS_1199 心跳, CS_10001 FirstPack`；权威状态（校验帐号、签发会话、返回角色列表；会话与会话锁在 server/session+account）；持久化（accounts/roles 表（persistence/db.py））；GM（/DSH_ADMIN 查号、踢线）。
- **现状证据**：mock_server.py:9968 cmd==1110 登录；:9922 cmd==1199 心跳；:9963 cmd==10001 FirstPack；account/ 模块
- **缺口/后续**：无（闭环）

### SYS_CORE_002 Role Creation 创建角色 — 【已具备】

- **需要的能力**：接口 `CS_10101 RoleCreate, CS_10102 RoleLogin, CS_10103 RoleReLogin`；权威状态（职业/性别/名字入库、分配 rid、初始化 role_attr/role_assets）；持久化（roles 表(career/sex/name/scene/x/y)）；GM（GM 建角/改名）。
- **现状证据**：mock_server.py:15929 cmd==10101 建角；:15851 cmd in(10102,10103) 登录/重登
- **缺口/后续**：无（闭环）

### SYS_CORE_003 Role Base/Init 角色基础 — 【已具备】

- **需要的能力**：接口 `SC_10300/10301/10302/10303（服务器主动推送为主）`；权威状态（权威角色行、属性行、资产行；进游戏下发全量）；持久化（roles, role_attr, role_assets）；GM（/DSH_ADMIN/setlevel setassets）。
- **现状证据**：mock_server.py:17260 cmd==10300；:17047 10301；:16109 10302；:16098 10303；role/storage+attribute/service
- **缺口/后续**：无（闭环）

### SYS_CORE_004 Role Login 进入游戏 — 【已具备】

- **需要的能力**：接口 `CS_10102 RoleLogin`；权威状态（校验 rid 属于本帐号、装载角色行、建立会话）；持久化（roles 表）；GM（—）。
- **现状证据**：mock_server.py:15851 cmd in(10102,10103)；与 SYS_CORE_001 同链
- **缺口/后续**：无（闭环）

### SYS_CORE_005 Scene & Movement 场景移动 — 【已具备】

- **需要的能力**：接口 `CS_10200 进场景, CS_10201, CS_10204 移动, CS_10205`；权威状态（权威 scene_id/x/y、NPC/怪物刷新、AOI 邻居广播）；持久化（roles.scene_id/x/y；scene_npcs/scene_mons(8件套)）；GM（GM 传送(set scene)）。
- **现状证据**：mock_server.py:15957 cmd==10200；:15973 10201；:15992 cmd in(10204,10205)；scene/service 8件套
- **缺口/后续**：AOI 邻居帧逐字节对比需第二在线客户端（FINAL_REGRESSION 附）

### SYS_CORE_006 Protocol/Network Layer 网络层 — 【已具备】

- **需要的能力**：接口 `all（承载全部 CS）`；权威状态（TCP 9000 收包分发、HTTP 8080 /DSH_ADMIN 管理面；封包规格 protocol/fields）；持久化（无（传输层））；GM（—）。
- **现状证据**：protocol/frame+fields；mock_server.py:39 注释(DISPATCH_TABLE 现走旧 if 链)；minloop 145/145 基线
- **缺口/后续**：无

### SYS_CORE_007 Version/Resource Update 版本更新 — 【部分】

- **需要的能力**：接口 `20100`；权威状态（服务器仅回版本公告/热更列表，无资源分发）；持久化（无）；GM（—）。
- **现状证据**：mock_server.py:17144 cmd==20100 有占位处理器；PHASE0 判 client-only（file_update_1411.luac）
- **缺口/后续**：真实热更资源分发/强更策略未接

### SYS_ROLE_001 Role Attribute 角色属性 — 【已具备】

- **需要的能力**：接口 `CS_10331, CS_10333`；权威状态（权威 role_attr 行；加点 CS_10331/10333 后重算并广播）；持久化（role_attr 表(_ATTR_ALIAS 别名映射)）；GM（/DSH_ADMIN/setlevel）。
- **现状证据**：mock_server.py:17047 10301；:16234 cmd==10331；:16121 cmd==10333；attribute/service db_role_attr
- **缺口/后续**：MuMu 实机标定具体数值(⏳需取证)

### SYS_ROLE_002 Career/Job 职业 — 【已具备】

- **需要的能力**：接口 `（随 10101 建角携带）`；权威状态（roles.career 列权威，不单独建表）；持久化（roles.career 列）；GM（—）。
- **现状证据**：mock_server.py:15929 cmd==10101 写入 career；config_role_career
- **缺口/后续**：无（基础闭环）

### SYS_ROLE_003 Title System 称号 — 【已具备】

- **需要的能力**：接口 `CS_14901（接 role_title）`；权威状态（权威 role_title 拥有记录(175项)；佩戴后随角色信息广播）；持久化（role_title 表(config_title.Title 175项)）；GM（GM 发称号）。
- **现状证据**：mock_server.py:16243 cmd==14901；:7403 称号拥有记录(config_title 175项)
- **缺口/后续**：称号获取/解锁任务链未完整

### SYS_ROLE_004 VIP System 贵族/VIP — 【部分】

- **需要的能力**：接口 `CS_16701（vip_lev 上传）`；权威状态（仅 role_assets.vip_exp 与 role 字段；无独立 vip_* 表与特权结算）；持久化（role_assets.vip_exp（无 vip_* 表））；GM（/DSH_ADMIN/setcharge）。
- **现状证据**：mock_server.py:10344 cmd==16701(vip_lev=1)；FINAL_REGRESSION 附二: setcharge 端点
- **缺口/后续**：VIP 等级逻辑/每日礼包/特权结算缺失

### SYS_ROLE_005 Experience/Level 经验等级 — 【已具备】

- **需要的能力**：接口 `CS_14600, CS_14601 等级礼包`；权威状态（权威 level/exp；经验来源(战斗/任务/挂机)经 RewardService；等级礼包幂等领取）；持久化（roles.level/exp；levgift_got 表）；GM（/DSH_ADMIN/setlevel）。
- **现状证据**：mock_server.py:17732 cmd in(14600,14601) 等级礼包；attribute/service
- **缺口/后续**：经验曲线 MuMu 标定(⏳)

### SYS_ROLE_006 Avatar/Head & Chat Bubble 头像框气泡 — 【部分】

- **需要的能力**：接口 `UNKNOWN（随角色信息携带）`；权威状态（仅 role 头像/气泡字段；无专用表）；持久化（roles 头像/气泡列（无专用表））；GM（—）。
- **现状证据**：systems_master: roles 字段 only；mock_server 无独立 handler（无专属命令）
- **缺口/后续**：头像框/气泡获取与佩戴协议未接

### SYS_GROWTH_001 Skill System 技能 — 【已具备】

- **需要的能力**：接口 `CS_10401..10406, CS_20012 技能播放`；权威状态（权威已学技能；学习/升级扣金币并广播；战斗中 CS_10401..10406）；持久化（（随 role_skill，无独立表名））；GM（GM 学技能）。
- **现状证据**：mock_server.py:18262 cmd in(10401..10404)；:13167 cmd==10406；skill/service 学习/升级(P8 partner_feed/skill_learn)
- **缺口/后续**：技能消耗真值已 CONFIRMED(config_skill)；战斗数值 MuMu 标定

### SYS_GROWTH_002 Talent/天赋 — 【部分】

- **需要的能力**：接口 `CS_10601/10610/10651（面板）`；权威状态（天赋/修炼面板读取；仅配置，无独立天赋成长结算）；持久化（（无独立表））；GM（—）。
- **现状证据**：mock_server.py:13008 cmd in(10601,10610,10622,10651) 天赋/修炼面板
- **缺口/后续**：天赋加点/解锁逻辑缺失

### SYS_GROWTH_003 Practice/修炼 Buff — 【已具备】

- **需要的能力**：接口 `CS_10621 修炼帧`；权威状态（权威 role_buffs/practice_exp；10621 修炼帧动态读 practice_exp=35）；持久化（role_buffs 表(practice_exp)）；GM（GM 设置修炼）。
- **现状证据**：mock_server.py:16127 cmd==10621；FINAL_REGRESSION §三: practice_exp=35 CONFIRMED(50=本级满值)
- **缺口/后续**：消耗/拥有 EXP 客户端渲染空白(客户端侧,勿再加帧)

### SYS_GROWTH_004 Buff System Buff — 【已具备】

- **需要的能力**：接口 `（随战斗 CS_20012/20013）`；权威状态（权威 role_buffs；战斗 SC_20012/20013 透传 Buff）；持久化（role_buffs 表）；GM（—）。
- **现状证据**：systems_master: role_buffs present；SC_20012/20013 透传链
- **缺口/后续**：Buff 数值/叠加规则 MuMu 标定

### SYS_GROWTH_005 Morale 士气 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_morale/hero_morale 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented_systems SYS_GROWTH_005(config_morale+hero_morale only)
- **缺口/后续**：需建权威士气状态+协议

### SYS_BATTLE_001 Turn-based Battle 回合战斗 — 【已具备】

- **需要的能力**：接口 `CS_20002 开战, CS_20014`；权威状态（权威战斗实例(battle.py)；怪物 HP/ATK 由服务端公式(配置无显式值)；Timer kick）；持久化（（战斗临时态，结算写奖励/经验））；GM（/DSH_ADMIN/battle_replay?mon_id=20001）。
- **现状证据**：mock_server.py:17384 cmd==20002；:19274 cmd==20014；/DSH_ADMIN/battle_replay 确定性重放(两次hex一致)
- **缺口/后续**：怪物 HP/ATK 真值 UNKNOWN(需真服/MuMu 战斗抓包)；20002 最终裁定保留旧链

### SYS_BATTLE_002 Auto-battle/AFK 挂机 — 【已具备】

- **需要的能力**：接口 `CS_15400 族(挂机)`；权威状态（权威 guaji_state；挂机累积+幂等领取(afk_claim)；8 地图区域）；持久化（guaji_state 表；config_guaji 8区域）；GM（GM 触发挂机）。
- **现状证据**：mock_server.py:18736 cmd==15400；:18678 15402；:18698 15403；:18668 15405；FINAL_REGRESSION P10 afk_claim
- **缺口/后续**：巡逻按钮激活条件待实机观察；收益系数 INFERENCE

### SYS_BATTLE_003 Battle Replay/Video 战报回放 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无客户端战报存储/回放 SC；仅管理端 battle_replay 重放）；持久化（无）；GM（/DSH_ADMIN/battle_replay（调试用））。
- **现状证据**：mock_server 无战报 CS handler；unimplemented SYS_BATTLE_003(battlevideo modules; no DB)
- **缺口/后续**：需战报录制/存储/回放协议

### SYS_BATTLE_004 God War Battle 神魔战 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；client UI only）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_BATTLE_004(config_sm_war/godwar_battle_*)
- **缺口/后续**：需建权威玩法状态

### SYS_BATTLE_005 Boss System BOSS — 【已具备】

- **需要的能力**：接口 `CS_20002（击杀 BOSS）`；权威状态（权威 role_boss_kill 击杀记录；BOSS 战斗走 20002）；持久化（role_boss_kill 表；config_boss/demon）；GM（GM 刷新 BOSS）。
- **现状证据**：systems_master: role_boss_kill present；mock_server 20002 战斗链；config_boss/demon
- **缺口/后续**：BOSS 刷新时间表/伤害榜未完整

### SYS_EQUIP_001 Equipment System 装备 — 【已具备】

- **需要的能力**：接口 `CS_10500..10593, CS_11200~11205(伙伴装备)`；权威状态（权威 equip_items；穿戴/脱下(10574/10576)改槽位并重算属性+战力；伙伴装备走 11200 族）；持久化（equip_items, bag_items）；GM（GM 发装备）。
- **现状证据**：mock_server.py:13370 cmd==10593；:13383 cmd in(10573,10574,10575,10576,10578) 穿戴/脱下；:13404 10574穿戴；:13407 10576脱下；equipment/service
- **缺口/后续**：外观属性贡献已闭环；MuMu 标定具体数值

### SYS_EQUIP_002 Smith/Forge/Fuse 锻造合成 — 【部分】

- **需要的能力**：接口 `CS_10523/10527/10528`；权威状态（部分；强化族 10523/10527/10528；合成 config_item_fuse(192条)）；持久化（bag_items（材料消耗））；GM（GM 发材料）。
- **现状证据**：mock_server.py:13236 cmd==10523；:16986 cmd==10527；:17631 cmd==10528；config_item_fuse 192条(CONFIRMED)
- **缺口/后续**：升阶/融合完整规则未闭环

### SYS_EQUIP_003 Rune System 符文 — 【已具备】

- **需要的能力**：接口 `CS_11240, CS_21400..21414`；权威状态（权威 role_runes；21406 升级；124 符文(1..50级)）；持久化（role_runes 表(config_rune_data RuneBase 124项)）；GM（GM 发符文）。
- **现状证据**：mock_server.py:13249 cmd==11240；:15254 cmd==21406 升级；:8667/:8796 config_rune(124项)
- **缺口/后续**：符文套装效果未完整

### SYS_EQUIP_004 Equip StarUp/强化 装备升星 — 【部分】

- **需要的能力**：接口 `CS_10527/10528`；权威状态（部分；10527/10528 强化族；config_intensify(L1=100%/L3=75%)）；持久化（equip_items(强化等级)）；GM（—）。
- **现状证据**：mock_server.py:16986 10527；:17631 10528；FINAL_REGRESSION: 强化成功率/消耗 CONFIRMED
- **缺口/后续**：强化保护/倍率规则未完整

### SYS_FRIEND_001 Partner/Hero System 伙伴 — 【已具备】

- **需要的能力**：接口 `CS_11215, CS_11216`；权威状态（权威 role_heros；11215 伙伴面板、11216 伙伴状态；培养 partner_feed(P8)）；持久化（role_heros 表）；GM（GM 发伙伴）。
- **现状证据**：mock_server.py:18173 cmd==11215 伙伴面板；:16292 cmd==11216 partner_bid/state；P8 partner_feed
- **缺口/后续**：伙伴喂养消耗 UNKNOWN(配置无显式值)

### SYS_FRIEND_002 Formation 阵法 — 【已具备】

- **需要的能力**：接口 `CS_11237(formation_type)`；权威状态（权威 role_form；11237 formation_type）；持久化（role_form 表）；GM（—）。
- **现状证据**：phase1_cs_inventory: CS_11237 formation_type=1；systems_master role_form present
- **缺口/后续**：阵型加成系数 MuMu 标定

### SYS_FRIEND_003 Partner Atlas 伙伴图鉴 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；仅 client UI）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_FRIEND_003(partner_atlas modules; partial)
- **缺口/后续**：需图鉴收集状态协议

### SYS_FRIEND_004 Partner Recruit 伙伴招募/抽卡 — 【部分】

- **需要的能力**：接口 `UNKNOWN`；权威状态（部分；无专用招募命令，config_lucky_box）；持久化（（无专属表））；GM（—）。
- **现状证据**：mock_server 无独立招募 handler；config_lucky_box_data；systems_master partial
- **缺口/后续**：抽卡概率/保底/招募协议未接

### SYS_FRIEND_005 Partner Fetter 伙伴羁绊 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_partner_fetter only）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_FRIEND_005
- **缺口/后续**：需羁绊权威状态

### SYS_APPEAR_001 Wing System 翅膀 — 【已具备】

- **需要的能力**：接口 `CS_11600..11607`；权威状态（权威 role_wing；11600 翅膀面板数据源；wing_up(P9)）；持久化（role_wing 表(config_wing_data WingUpstar)）；GM（GM 发翅膀）。
- **现状证据**：mock_server.py:14887 cmd==11600；:7666 role_wing 数据源；:101 import growth.handler 注册11600；P9 wing_up
- **缺口/后续**：MuMu 标定数值

### SYS_APPEAR_002 Mount 坐骑 — 【已具备】

- **需要的能力**：接口 `CS_10551.., CS_15501`；权威状态（权威 role_ride；15501 坐骑态、10551 族）；持久化（role_ride 表(config_ride RideAllSkill)）；GM（—）。
- **现状证据**：mock_server.py:15297 cmd==15501；:17621 cmd in(10551)；:8525 role_ride 数据源
- **缺口/后续**：坐骑技能效果未完整

### SYS_APPEAR_003 Beast 灵兽 — 【已具备】

- **需要的能力**：接口 `CS_15801`；权威状态（权威 role_lingshou；15801 魂兽状态）；持久化（role_lingshou 表(config_lingshou)）；GM（—）。
- **现状证据**：mock_server.py:14807 cmd==15801；:7476 role_lingshou 数据源
- **缺口/后续**：灵兽培养/技能未完整

### SYS_APPEAR_004 Soul 元神 — 【已具备】

- **需要的能力**：接口 `CS_19406`；权威状态（权威 role_yuanshen；19406 元神状态）；持久化（role_yuanshen 表）；GM（—）。
- **现状证据**：mock_server.py:14840 cmd==19406；:7510 role_yuanshen 数据源
- **缺口/后续**：元神进阶未完整

### SYS_APPEAR_005 Divine Artifact 神器 — 【已具备】

- **需要的能力**：接口 `CS_15700..15704`；权威状态（权威 role_shenqi；15700 神器持有；使用中唯一(status=1)）；持久化（role_shenqi 表(id/lev/star/status/mark)）；GM（GM 发神器）。
- **现状证据**：mock_server.py:14850 cmd==15700；:7546/:7556 role_shenqi 数据源；P9 shenqi_up
- **缺口/后续**：MuMu 标定数值

### SYS_APPEAR_006 Fate/Natal 命格 — 【已具备】

- **需要的能力**：接口 `CS_19400..19414`；权威状态（权威 role_mingge；19400.mingge_list；19404 删除命格）；持久化（role_mingge 表(config_mingge MinggeOther.stage_init)）；GM（—）。
- **现状证据**：mock_server.py:15232 cmd==19400；:7588 role_mingge 数据源；P9 mingge_activate
- **缺口/后续**：命格套装效果未完整

### SYS_APPEAR_007 Magic Weapon 法宝 — 【已具备】

- **需要的能力**：接口 `CS_11200~11205`；权威状态（权威 role_fabao；11200/11205 族接入）；持久化（role_fabao 表）；GM（—）。
- **现状证据**：mock_server.py:18127 cmd==11200；:12105 cmd in(11205..)
- **缺口/后续**：法宝技能效果未完整

### SYS_APPEAR_008 Vehicle/Chair 座驾 — 【已具备】

- **需要的能力**：接口 `UNKNOWN（随外观族）`；权威状态（权威 role_chair 表；无独立 CS 命令(并入外观族)）；持久化（role_chair 表）；GM（—）。
- **现状证据**：systems_master: role_chair present；mock_server 无专属命令(并入 112xx/外观族)
- **缺口/后续**：座驾独立协议未取证

### SYS_APPEAR_009 Fashion/Skin 时装 — 【已具备】

- **需要的能力**：接口 `CS_10573,10574,10575,10576,10578`；权威状态（权威 role_fashion；10573 激活/10574 穿戴/10576 脱下/10578；属性贡献已接）；持久化（role_fashion 表(config_fashion)）；GM（GM 发时装）。
- **现状证据**：mock_server.py:13383 cmd in(10573..10578)；:13392 时装激活；:13404 穿戴；:13407 脱下
- **缺口/后续**：MuMu 标定数值

### SYS_APPEAR_010 Halo 光环 — 【部分】

- **需要的能力**：接口 `CS_19100,19103,19104`；权威状态（权威 role_halo/role_halo_equip；19100 info/19103 穿戴；升级未实现）；持久化（role_halo, role_halo_equip 表）；GM（—）。
- **现状证据**：mock_server.py:13427 cmd==19100；:13446 cmd==19103 光环穿戴；:13458 cmd==19104
- **缺口/后续**：光环升级未实现

### SYS_ECON_001 Assets/Currency 货币资产 — 【已具备】

- **需要的能力**：接口 `SC_10303 资产推送(服务器主动)`；权威状态（权威 role_assets；一切资产变动走 CurrencyService(db_add/set_assets)）；持久化（role_assets 表）；GM（/DSH_ADMIN/setassets）。
- **现状证据**：mock_server.py:16098 cmd==10303；currency/service db_get/add/set_assets
- **缺口/后续**：无（闭环）

### SYS_ECON_002 Inventory/Bag 背包 — 【已具备】

- **需要的能力**：接口 `CS_10500..10593`；权威状态（权威 bag_items/bag_volume；10502 同步/10505 双击使用/10504 出售；D2 不可渲染 bid 过滤）；持久化（bag_items, bag_volume 表）；GM（GM 发道具）。
- **现状证据**：mock_server.py:19229 cmd==10502 背包同步；:17647 cmd==10505 双击使用；:15054 cmd==10504 出售；P16 不可渲染bid过滤
- **缺口/后续**：D2 渲染根因部分 INFERENCE

### SYS_ECON_003 Mall/Shop 商城 — 【已具备】

- **需要的能力**：接口 `CS_12801..12856, CS_13401..13416`；权威状态（权威 mall_bought；12801 族购买扣币+限购；13401 族）；持久化（mall_bought 表(config_mall/shop)）；GM（GM 发商品）。
- **现状证据**：mock_server.py:16770 cmd in(12801..)；:16797 12801；:10215 cmd==13403；P11 mall_buy
- **缺口/后续**：MuMu 标定商品价格

### SYS_ECON_004 Storage/Warehouse 仓库 — 【已具备】

- **需要的能力**：接口 `CS_10714, CS_10621`；权威状态（权威 store_items；10714 仓库）；持久化（store_items 表(config_storage_data)）；GM（—）。
- **现状证据**：mock_server.py:17711 cmd==10714；:16127 cmd==10621
- **缺口/后续**：无（基础闭环）

### SYS_ECON_005 Trade Market 市场/交易 — 【已具备】

- **需要的能力**：接口 `CS_18909..`；权威状态（权威 role_market/role_market_goods；18909 族）；持久化（role_market, role_market_goods 表）；GM（—）。
- **现状证据**：mock_server.py:10180 cmd==18909
- **缺口/后续**：寄售上架/税费规则未完整

### SYS_ECON_006 Black Market 黑市 — 【部分】

- **需要的能力**：接口 `CS_18909(通用)`；权威状态（仅 18909 通用响应；无独立 DB/刷新）；持久化（无）；GM（—）。
- **现状证据**：mock_server.py:10180 cmd==18909(通用 stub)；systems_master partial(no DB)
- **缺口/后续**：黑市独立刷新/限购逻辑缺失

### SYS_ECON_007 Exchange 兑换 — 【部分】

- **需要的能力**：接口 `CS_13403, duihuan(20)/yunyingduihuan(21)`；权威状态（部分；13403 兑换）；持久化（（mall_exchange））；GM（—）。
- **现状证据**：mock_server.py:10215 cmd==13403
- **缺口/后续**：完整兑换表/币别未闭环

### SYS_ECON_008 Auction 拍卖 — 【部分】

- **需要的能力**：接口 `CS_18020,18021,18022`；权威状态（权威 list+一口价(18020/18021/18022)；竞价未实现）；持久化（role_assets, bag_items）；GM（—）。
- **现状证据**：mock_server.py:12140 cmd==18020 拍卖行；:12144 18021；:12162 18022 一口价
- **缺口/后续**：竞价/一口价邮件通知未实现

### SYS_ECON_009 Mail 邮件 — 【已具备】

- **需要的能力**：接口 `CS_10800`；权威状态（权威 role_mail；10800；mail_claim 幂等(reward_log transaction_id)）；持久化（role_mail 表(rid/from/subject/content/附件)）；GM（GM 发邮件）。
- **现状证据**：mock_server.py:18236 cmd==10800；:2708 role_mail 表；P12 mail_claim 幂等
- **缺口/后续**：无（闭环）

### SYS_ECON_010 Recharge/Payment 充值 — 【部分】

- **需要的能力**：接口 `CS_12831, CS_13401..`；权威状态（部分；12831/13401；无独立充值表(走 mall_bought/assets)）；持久化（无独立充值表(mall_bought/assets)）；GM（/DSH_ADMIN/setcharge）。
- **现状证据**：mock_server.py:16594 cmd==12831；:10204 cmd in(13401)；FINAL_REGRESSION: setcharge 端点
- **缺口/后续**：真实支付回调/累计充值档位未接

### SYS_ECON_011 Gift Item 礼包/宝箱 — 【已具备】

- **需要的能力**：接口 `CS_10505(使用)`；权威状态（权威礼包/掉落经 gift/item 路径；10505 使用；P16 掉落接线）；持久化（bag_items(礼包)）；GM（GM 发礼包）。
- **现状证据**：mock_server.py:17647 cmd==10505；P16 drop_test/build_bag_items
- **缺口/后续**：掉落概率 pp/1000 基准 INFERENCE

### SYS_QUEST_001 Mission/Quest 任务 — 【已具备】

- **需要的能力**：接口 `CS_12400..12421, CS_12407/08/09`；权威状态（权威 missions；12400 列表/12401/12408 NPC；task/service build_12400；线性剧情链唯一进行中）；持久化（missions 表(config_mission/chapter)）；GM（GM 完成任务）。
- **现状证据**：mock_server.py:16084 cmd==12400；:16091 12401；:16075 cmd==12408；task/service
- **缺口/后续**：无（闭环）

### SYS_QUEST_002 Daily/Active 日常活跃 — 【已具备】

- **需要的能力**：接口 `CS_10301(日常数据)`；权威状态（权威 daily_progress/daily_lingqu；随 10301 推送）；持久化（daily_progress, daily_lingqu 表）；GM（GM 重置日常）。
- **现状证据**：systems_master: daily_progress/daily_lingqu present；mock_server 10301 推送链(:17047)
- **缺口/后续**：活跃奖励档位未完整

### SYS_QUEST_003 Achievement 成就 — 【已具备】

- **需要的能力**：接口 `CS_16400`；权威状态（权威 chengjiu_progress；16400；server/achievement/service.py 342 条）；持久化（chengjiu_progress 表(config_chengjiu 342条)）；GM（GM 发成就）。
- **现状证据**：mock_server.py:18629 cmd==16400；server/achievement/service.py 342条(CONFIRMED)
- **缺口/后续**：chengjiu_has.state 子字段偏移 UNKNOWN(需实机 hook)

### SYS_QUEST_004 Growth Target 成长目标 — 【部分】

- **需要的能力**：接口 `CS_30500,30501,30502`；权威状态（权威 30500/30501/30502；server/growth_target/ 模块(PHASE2.11)）；持久化（role_growth_target(schema)）；GM（—）。
- **现状证据**：mock_server.py:11751 cmd==30500；:11713 30501；:11716 30502；:103 import growth_target.handler
- **缺口/后续**：PHASE0 清单标 partial，实际 P2.11 已建模块(以源码为准)

### SYS_QUEST_005 Guide System 新手引导 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；client-side 引导）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_QUEST_005(config_guide/action_ctrl)
- **缺口/后续**：引导服务器态/进度同步未接

### SYS_MAP_001 World Map 世界地图 — 【已具备】

- **需要的能力**：接口 `（随 CS_10200）`；权威状态（无独立 CS；随场景 10200 进图；config_map/world_map）；持久化（roles.scene_id）；GM（GM 传送）。
- **现状证据**：systems_master: implemented(basic)；config_world_map/map；mock_server 并入场景链
- **缺口/后续**：区域解锁条件未完整

### SYS_MAP_002 Team Group 组队 — 【已具备】

- **需要的能力**：接口 `CS_13200,13201,13202,13204,13210,13218,13226`；权威状态（权威 role_team/role_team_invite；13200 队伍信息/13201 建队/13202 邀请/13204 应答/13210 退出/13226 解散/13218 大厅）；持久化（role_team, role_team_invite 表）；GM（—）。
- **现状证据**：mock_server.py:10778 cmd in(13200..)；:10802 13201 建队；:10846 13202 邀请；:10875 13204 应答；:10807 13210 退出；:10811 13226 解散
- **缺口/后续**：多人副本组队匹配未完整

### SYS_DUNGEON_001 Dungeon 副本 — 【已具备】

- **需要的能力**：接口 `CS_11700..11713, CS_12000, CS_13028..`；权威状态（权威 dungeon_progress；11700 族/12000 进本/13028；34 副本列表+首通）；持久化（dungeon_progress 表(config_dungeon_new)）；GM（GM 重置副本）。
- **现状证据**：mock_server.py:17905 cmd==11700；:18402 cmd in(11710..11713)；:12372 cmd==13028；:12251 cmd==12000 进本；P10 dungeon_clear
- **缺口/后续**：MuMu 标定掉落/体力

### SYS_DUNGEON_002 Endless Dungeon 无尽/深渊 — 【部分】

- **需要的能力**：接口 `CS_13035/13038(共用塔族)`；权威状态（共用 dungeon_progress；无独立无尽逻辑）；持久化（dungeon_progress(shared)）；GM（—）。
- **现状证据**：systems_master: dungeon_progress shared；mock_server 13035/13038 塔族
- **缺口/后续**：无尽独立层数/奖励未闭环

### SYS_DUNGEON_003 Tower 塔/爬塔 — 【部分】

- **需要的能力**：接口 `CS_13035,13038`；权威状态（部分；13035/13038；config_dungeon_tower/single_tower）；持久化（dungeon_progress(shared)）；GM（—）。
- **现状证据**：mock_server.py:15702 cmd==13035；:15725 cmd==13038；config_dungeon_tower
- **缺口/后续**：恶魔塔/金塔规则未完整

### SYS_DUNGEON_004 Mystic Realm 秘境/遗迹 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_DUNGEON_004(mijing function1011)
- **缺口/后续**：需建秘境权威状态

### SYS_DUNGEON_005 Shadow/Palace dungeon 其余副本 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_dungeon_gods/smjz 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_DUNGEON_005
- **缺口/后续**：需逐个建副本逻辑

### SYS_ACT_001 Sign-in/Check-in 签到 — 【已具备】

- **需要的能力**：接口 `CS_14100, CS_14101`；权威状态（权威 sign_got；14100/14101 幂等；30 天逐日奖励）；持久化（sign_got 表(config_checkin 30天)）；GM（GM 补签）。
- **现状证据**：mock_server.py:16981 cmd in(14100,14101)；:18956 14100；P11 sign_do；config_checkin Day1~Day7 CONFIRMED
- **缺口/后续**：无（闭环）

### SYS_ACT_002 Seven-Day Login 七日签到 — 【部分】

- **需要的能力**：接口 `UNKNOWN(随签到)`；权威状态（共用 sign_got；无独立七日逻辑）；持久化（sign_got(shared)）；GM（—）。
- **现状证据**：systems_master: sign_got shared；config_seven_login
- **缺口/后续**：七日独立档位未闭环

### SYS_ACT_003 Invest 投资 — 【已具备】

- **需要的能力**：接口 `CS_13901..`；权威状态（权威 role_invest；13901）；持久化（role_invest 表(config_invest)）；GM（—）。
- **现状证据**：mock_server.py:10354 cmd==13901
- **缺口/后续**：返利档位/时间未完整

### SYS_ACT_004 Turntable/Lucky Draw 转盘 — 【部分】

- **需要的能力**：接口 `UNKNOWN`；权威状态（仅 dial reward stub；无 DB）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 DB；systems_master partial(dial reward stub)
- **缺口/后续**：转盘概率/次数/奖励未接

### SYS_ACT_005 Scratch Card 刮刮乐 — 【已具备】

- **需要的能力**：接口 `CS_16651,16652`；权威状态（server/scratch/ 模块注册 16651/16652(PHASE2.11)）；持久化（role_scratch(schema)）；GM（—）。
- **现状证据**：mock_server.py:104 import scratch.handler 注册16651/16652；server/scratch/
- **缺口/后续**：PHASE0 清单标未实现，实际 P2.11 已建模块(以源码为准)

### SYS_ACT_006 Festival/Operation 节日运营活动 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_fest_data 仅事件数据）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_ACT_006
- **缺口/后续**：需活动框架+各节日玩法

### SYS_ACT_007 Answer Quiz 答题 — 【已具备】

- **需要的能力**：接口 `CS_16100,16101,16102,16103`；权威状态（server/answer/ 模块注册 16100-16103(PHASE2.11)）；持久化（role_answer(schema)）；GM（—）。
- **现状证据**：mock_server.py:102 import answer.handler 注册16100/16101/16102/16103；:10604 cmd==16102；server/answer/
- **缺口/后续**：PHASE0 清单标未实现，实际 P2.11 已建模块(以源码为准)

### SYS_ACT_008 Guess 竞猜 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_ACT_008
- **缺口/后续**：需建竞猜权威状态

### SYS_ACT_009 Money Tree 摇钱树 — 【已具备】

- **需要的能力**：接口 `UNKNOWN`；权威状态（权威 role_tree；无独立 CS(并入公会树/107xx 配置)）；持久化（role_tree 表）；GM（—）。
- **现状证据**：mock_server.py:3104 role_tree 等级；config_guild_tree_data
- **缺口/后续**：摇钱次数/产出规则未完整

### SYS_ACT_010 Pray/QiFu 祈福 — 【已具备】

- **需要的能力**：接口 `UNKNOWN`；权威状态（权威 role_qifu；公会祈福 config_guild_pray）；持久化（role_qifu 表(server/cfg/config_guild_pray.json)）；GM（—）。
- **现状证据**：mock_server.py:3294 祈福次数；:3271 祈福档位
- **缺口/后续**：祈福奖励/冷却未完整

### SYS_ACT_011 Treasure Hunt 夺宝探宝 — 【部分】

- **需要的能力**：接口 `CS_13810..13817`；权威状态（13810..13817 有处理器；PHASE0 清单标 client-only（以源码 handler 为准 partial））；持久化（（未确认独立表））；GM（—）。
- **现状证据**：mock_server.py:12429 cmd in(13810..13817)；:12473 cmd==13810；unimplemented SYS_ACT_011 标 client-only（源码与清单不一致）
- **缺口/后续**：需核实 13810 族是否真闭环/有持久化

### SYS_ACT_012 Return/Back Flow 回归 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_ACT_012
- **缺口/后续**：需回归资格判定/奖励

### SYS_ACT_013 Gift Recharge 累计充值活动 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；charge_double/tianjianghaoli）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_ACT_013
- **缺口/后续**：需累计充值统计/档位

### SYS_ACT_014 Point/QingFu 点/dnf/live — 【部分】

- **需要的能力**：接口 `UNKNOWN`；权威状态（role_point 已持久化；活动未接）；持久化（role_point 表）；GM（—）。
- **现状证据**：systems_master: role_point present / activities not hooked
- **缺口/后续**：各活动玩法未接

### SYS_ACT_015 Global Wish 全球许愿 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_ACT_015
- **缺口/后续**：需许愿广播/奖励

### SYS_SOCIAL_001 Chat System 聊天 — 【已具备】

- **需要的能力**：接口 `CS_10800.., CS_12721/12762`；权威状态（权威 role_chat；10800/127xx 族；死协议判据 127xx 部分发=0）；持久化（role_chat 表）；GM（GM 广播）。
- **现状证据**：mock_server.py:18236 cmd==10800；:13668 cmd in(12721..) 聊天；FINAL_REGRESSION 附二: 127xx 部分死协议
- **缺口/后续**：部分聊天频道发=0 未接

### SYS_SOCIAL_002 Friend System 好友 — 【已具备】

- **需要的能力**：接口 `CS_13300,13303,13305,13321`；权威状态（server/friend/ 模块注册 13300/13321/13303/13305(PHASE2.11)；扩展 13306/13310 等死协议）；持久化（role_friend(schema)）；GM（—）。
- **现状证据**：mock_server.py:105 import friend.handler 注册13300/13321/13303/13305；:17804? 见 friend 模块；server/friend/
- **缺口/后续**：PHASE0 清单标 partial，P2.11 已建模块；扩展好友协议死协议待取证

### SYS_SOCIAL_003 Moments 朋友圈 — 【已具备】

- **需要的能力**：接口 `UNKNOWN(随好友/社交)`；权威状态（权威 role_moments；无独立 CS）；持久化（role_moments 表）；GM（—）。
- **现状证据**：systems_master: role_moments present；mock_server 无专属命令
- **缺口/后续**：动态发布/点赞协议未接

### SYS_SOCIAL_004 Guild 公会 — 【已具备】

- **需要的能力**：接口 `CS_17500..17519, CS_19509..`；权威状态（权威 role_guild；17501 族/19509；核心闭环，子系统(科技/神兽/祈福)partial）；持久化（role_guild 表）；GM（GM 建公会）。
- **现状证据**：mock_server.py:11854 cmd==17519；:11431 cmd==19509；:17895 cmd==17501
- **缺口/后续**：公会科技/神兽/副本站未完整

### SYS_SOCIAL_005 Marriage 结婚 — 【已具备】

- **需要的能力**：接口 `CS_18300,18302,18313,18314,18316,18318,18321,18322`；权威状态（权威 role_marry/propose；18300 求婚/18302 应答/18313 离婚检查/18314 发起/18316 应答/18318 状态/18321 婚戒进阶；目标经服务端 intent 表）；持久化（role_marry, role_marry_propose 表）；GM（GM 结婚/离婚）。
- **现状证据**：mock_server.py:11077 cmd==18300 求婚；:11104 18302 应答；:11128 18313 离婚检查；:11151 18318 状态；:11155 18321 婚戒进阶
- **缺口/后续**：婚礼场景/礼堂未完整

### SYS_SOCIAL_006 Jiebai 结拜 — 【已具备】

- **需要的能力**：接口 `CS_19505,19512,19514,19524,19530,19533,19536`；权威状态（权威 role_jiebai；19505 发起/19512 确认/19524 邀请/19530 成员列表/19533 取消/19536 提升空间）；持久化（role_jiebai 表）；GM（GM 结拜）。
- **现状证据**：mock_server.py:10947 cmd==19505；:10992 19512；:10956 19524；:11022 19536；:10952 19533
- **缺口/后续**：结义副本/技能未完整

### SYS_SOCIAL_007 Flower/Gift 送花 — 【缺失】

- **需要的能力**：接口 `CS_13324/13326/13328(死协议)`；权威状态（无；13324/13326/13328/16300 死协议(发=0)）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；FINAL_REGRESSION 附二: 送花死协议；unimplemented SYS_SOCIAL_007
- **缺口/后续**：需建送花权威逻辑

### SYS_SOCIAL_008 Party 宴会/派对 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_SOCIAL_008
- **缺口/后续**：需宴会状态/奖励

### SYS_SOCIAL_009 Guild Wars 公会战 — 【部分】

- **需要的能力**：接口 `CS_17501, CS_195?, CS_130?`；权威状态（17501 按 type 分发(stub)；无独立战场）；持久化（role_guild）；GM（—）。
- **现状证据**：mock_server.py:17895 cmd==17501(按 type 分发 stub)
- **缺口/后续**：公会战战场/匹配/奖励缺失

### SYS_SOCIAL_010 Guild Tree/Animal/Skill 公会科技神兽 — 【部分】

- **需要的能力**：接口 `UNKNOWN(随公会)`；权威状态（共用 role_guild；祈福/神兽 config 已解构；无独立成长结算）；持久化（role_guild）；GM（—）。
- **现状证据**：mock_server.py:3294 公会祈福；config_guild_tree/animal/skill
- **缺口/后续**：科技/神兽成长结算未闭环

### SYS_COMM_001 Rank 排行榜 — 【部分】

- **需要的能力**：接口 `CS_16900..16903`；权威状态（派生榜：本服唯一角色作第1名；无独立 rank 表；16900/16903）；持久化（无独立 rank 表(派生)）；GM（GM 改榜）。
- **现状证据**：mock_server.py:10396 cmd==16900；:19112 cmd==16903；:7333 排行榜第1名(派生)
- **缺口/后续**：多榜真实排序/跨服榜未接

### SYS_COMM_002 Arena 竞技场 — 【已具备】

- **需要的能力**：接口 `CS_11300..11310, CS_11301`；权威状态（权威 arena_state/arena_record；11300/11301；对手=本服已有角色(R47)）；持久化（arena_state, arena_record 表）；GM（GM 重置）。
- **现状证据**：mock_server.py:17804 cmd==11300；:17783 cmd==11301；:6780 arena_state
- **缺口/后续**：竞技币兑换/段位未完整

### SYS_COMM_003 Peakwar 巅峰战 — 【已具备】

- **需要的能力**：接口 `CS_18803`；权威状态（权威 peakwar_state；18803）；持久化（peakwar_state 表）；GM（—）。
- **现状证据**：mock_server.py:15528 cmd==18803；:8898 peakwar_state
- **缺口/后续**：赛程/报名/奖励未完整

### SYS_COMM_004 Race 竞速/魂师大赛 — 【已具备】

- **需要的能力**：接口 `CS_17306,17308,17310,17312`；权威状态（权威 race_state；17306/17308/17310/17312；本服无竞速奖励配置(回空)）；持久化（race_state 表）；GM（—）。
- **现状证据**：mock_server.py:10545 cmd==17306；:10551 17308；:10558 17310；:10533 17312；:8936 race_state
- **缺口/后续**：竞速奖励配置为空(回空)，需真值

### SYS_COMM_005 Cross-server 跨服 — 【缺失】

- **需要的能力**：接口 `CS_30100~31299(未实现)`；权威状态（无；单体进程；30100~31299 未实现）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无跨服；unimplemented SYS_COMM_005(single-process)
- **缺口/后续**：需跨服网关/多服互联

### SYS_COMM_006 Mining 采矿 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_COMM_006
- **缺口/后续**：需矿脉采集/争夺

### SYS_COMM_007 Manor/Oasis 庄园 — 【已具备】

- **需要的能力**：接口 `CS_10701,10702..10762`；权威状态（权威 role_build/role_build_learn；10701 建筑研究升级）；持久化（role_build, role_build_learn 表）；GM（—）。
- **现状证据**：mock_server.py:12975 cmd==10701 建筑研究升级；:12966 10702；config_manor/build
- **缺口/后续**：庄园产出/互动未完整

### SYS_COMM_008 Attack City 攻城/领土战 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_COMM_008
- **缺口/后续**：需领土战/占领逻辑

### SYS_COMM_009 Freight/Escort 押镖 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_COMM_009
- **缺口/后续**：需押镖/劫镖逻辑

### SYS_COMM_010 Gold/JinYin Tower 金银塔 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_COMM_010
- **缺口/后续**：需金银塔逻辑

### SYS_GM_001 GM Tools GM 工具 — 【已具备】

- **需要的能力**：接口 `CS_10922,10932,10921..10950`；权威状态（权威：CS_10922/10932 + HTTP /DSH_ADMIN(setlevel/setassets/setcharge/reward_log/ach_list/battle_replay)；P13 走正式 Service 链路+gm.log）；持久化（reward_log(幂等), gm.log）；GM（GM 工具本身）。
- **现状证据**：mock_server.py:17054 cmd==10922；:10512 cmd==10932；HTTP /DSH_ADMIN/*；P13 setlevel/setassets 走 Service
- **缺口/后续**：无（调试闭环）

### SYS_BACK_001 Server Backend/DB 后台数据库 — 【已具备】

- **需要的能力**：接口 `（内部）`；权威状态（权威持久化层 persistence/db.py；db_conn/db_release；roles.db 全部表）；持久化（roles.db 全部表）；GM（DB 备份/查询）。
- **现状证据**：persistence/db.py；role/storage db_get/save_role；FINAL_REGRESSION 附: from-import 无损下沉
- **缺口/后续**：无（基础闭环）

### SYS_BACK_002 Cross-server backend 跨服后台 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；单体进程）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无跨服；unimplemented SYS_BACK_002(single-process)
- **缺口/后续**：需跨服网关/状态同步

### SYS_HIDDEN_001 Seal System 封印 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_seal 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_HIDDEN_001
- **缺口/后续**：需封印权威状态

### SYS_HIDDEN_002 XiuLuo 修罗 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_xiuluo_data 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_HIDDEN_002
- **缺口/后续**：需修罗逻辑

### SYS_HIDDEN_003 Chief 会长/百官 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_HIDDEN_003
- **缺口/后续**：需百官评选/奖励

### SYS_HIDDEN_004 Star Soul 星魂 — 【部分】

- **需要的能力**：接口 `UNKNOWN(随符文)`；权威状态（复用 role_runes；无独立逻辑）；持久化（role_runes(shared)）；GM（—）。
- **现状证据**：systems_master: role_runes? partial；mock_server 214xx 符文族
- **缺口/后续**：星魂独立逻辑未取证

### SYS_HIDDEN_005 God Redemption 神位/神减免 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；client-only not hooked）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_HIDDEN_005(godredeem_* modules)
- **缺口/后续**：需神位权威状态

### SYS_HIDDEN_006 Dragon 神龙/巨龙 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_dragon 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_HIDDEN_006
- **缺口/后续**：需巨龙逻辑

### SYS_HIDDEN_007 Balloon 气球/活动 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_holiday_balloon 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_HIDDEN_007
- **缺口/后续**：需气球活动逻辑

### SYS_UNKNOWN_001 Dan War 丹药战 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_dan_war 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_UNKNOWN_001
- **缺口/后续**：需取证入口/协议

### SYS_UNKNOWN_002 YunYing Ops 运营活动 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_function.json 未命名 id）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_UNKNOWN_002
- **缺口/后续**：需逐个识别功能 id

### SYS_UNKNOWN_003 Insight 顿悟/洞察 — 【部分】

- **需要的能力**：接口 `UNKNOWN`；权威状态（仅 roles.insight_status 字段；无逻辑）；持久化（roles.insight_status 列）；GM（—）。
- **现状证据**：systems_master: roles.insight_status field only
- **缺口/后续**：顿悟逻辑/协议未接

### SYS_UNKNOWN_004 Color/Head 染色 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；config_color 仅配置）；持久化（无）；GM（—）。
- **现状证据**：mock_server 无 handler；unimplemented SYS_UNKNOWN_004
- **缺口/后续**：需染色状态/协议

### SYS_EQUIP_005 Equip Refine 装备洗练 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；APK inventory 未发现专属 config/module/protocol）；持久化（UNKNOWN）；GM（—）。
- **现状证据**：unimplemented SYS_EQUIP_005: named in PHASE0 checklist; 无 config/module/protocol；mock_server 无 handler
- **缺口/后续**：需先取证客户端入口与协议

### SYS_EQUIP_006 Gem/Socket 宝石 — 【部分】

- **需要的能力**：接口 `UNKNOWN（镶嵌协议未取证）`；权威状态（合成 192 条已接(config_item_fuse)；镶嵌加成总表 EqmJewel 提取，单宝石语义 INFERENCE）；持久化（bag_items(宝石); ItemMiscAttrJewel 总属性表）；GM（—）。
- **现状证据**：mock_server 合成族; FINAL_REGRESSION: 宝石40物品+总属性表 CONFIRMED, 单宝石镶嵌加成 INFERENCE(ItemJewel 反构造 null)
- **缺口/后续**：镶嵌 CS 命令取证→接通 镶嵌→总表→Attribute→Power 闭环

### SYS_GROWTH_006 Soul Bone 魂骨 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（server/soulbone/ 目录存在(HANDOFF 文件地图)；无接入命令）；持久化（UNKNOWN）；GM（—）。
- **现状证据**：HANDOFF 文件地图: server/soulbone/；mock_server 无接入 handler；unimplemented SYS_GROWTH_006
- **缺口/后续**：需魂骨模块接线/协议取证

### SYS_GROWTH_007 Augment/Amplify 增幅 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（server/amplification/ 目录存在；无接入命令）；持久化（UNKNOWN）；GM（—）。
- **现状证据**：HANDOFF 文件地图: server/amplification/；mock_server 无接入 handler；unimplemented SYS_GROWTH_007
- **缺口/后续**：需增幅模块接线

### SYS_ECON_012 Drop/Loot Table 掉落 — 【部分】

- **需要的能力**：接口 `（随战斗/副本 CS）`；权威状态（掉落经 gift/battle 路径；config_drop 29组；无独立 drop 系统；概率 INFERENCE）；持久化（bag_items(reward_log 幂等)）；GM（GM 触发掉落）。
- **现状证据**：FINAL_REGRESSION P16: drop_test；config_drop 29组金币/首通池(20001~20029) CONFIRMED；reward/service
- **缺口/后续**：掉落概率 pp/1000 基准需实机标定

### SYS_CORE_008 Red Dot/Badge 红点 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无；APK inventory 未发现专属 config/module/protocol）；持久化（UNKNOWN）；GM（—）。
- **现状证据**：unimplemented SYS_CORE_008: 无 config/module/protocol；mock_server 无 handler
- **缺口/后续**：需红点推送/聚合协议

### SYS_CORE_009 UI State Sync UI状态 — 【缺失】

- **需要的能力**：接口 `UNKNOWN`；权威状态（无专属同步协议）；持久化（UNKNOWN）；GM（—）。
- **现状证据**：unimplemented SYS_CORE_009: 无 config/module/protocol
- **缺口/后续**：需 UI 状态同步帧

### SYS_ROLE_007 Combat Power 战力 — 【部分】

- **需要的能力**：接口 `SC_10304, SC_10306(服务器推送)`；权威状态（权威 power/service；10304 战力/10306 资产推送；AttrPower 31 属性系数 CONFIRMED）；持久化（role_attr(派生)）；GM（/DSH_ADMIN 查战力）。
- **现状证据**：mock_server.py:17208 cmd==10304 战力推送；:17189 cmd==10306；FINAL_REGRESSION P12 power.breakdown；AttrPower 31属性 CONFIRMED
- **缺口/后续**：九维分项组合公式待实机验证

### SYS_FRIEND_006 Partner Training 伙伴培养 — 【部分】

- **需要的能力**：接口 `CS_11216`；权威状态（11216 伙伴状态+partner_feed(P8)；喂养消耗数值 UNKNOWN）；持久化（role_heros(培养等级)）；GM（GM 养伙伴）。
- **现状证据**：mock_server.py:16292 cmd==11216；P8 partner_feed；FINAL_REGRESSION 缺口#2 喂养消耗 UNKNOWN
- **缺口/后续**：喂养消耗真值需实机喂养取证

### SYS_FRIEND_007 Partner Equipment 伙伴装备 — 【部分】

- **需要的能力**：接口 `CS_11200~11205`；权威状态（协议段 11200~11205 被引用并接入；无独立模块）；持久化（（随 role_heros/equip_items））；GM（—）。
- **现状证据**：mock_server.py:18127 cmd==11200；:12105 cmd in(11205..)；systems_master partial
- **缺口/后续**：伙伴装备独立模块/属性贡献未闭环
