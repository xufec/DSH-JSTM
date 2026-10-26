# 未实现 / 未接入系统清单 unimplemented_systems

> PHASE 0 审计产物。判据：客户端存在入口（config 表 / Lua 模块 / function id / 协议），
> 但 mock_server 无对应数据库表或仅有通用/空响应、或完全没有服务端实现。
> 证据等级见各行。共 **42** 项（另有 partial 项已实现但未完整，见 systems_master.md）。

> **⏳「需 MuMu 运行时取证」含义**：该系统的数值/掉落/奖励/UI 行为只有在 1.4.11 客户端于 MuMu 实机运行 + mock_server 联调后，才能确认真实值与行为；APK 静态配置表存在性仍按 CONFIRMED 处理。详见 systems_master.md 顶部「MuMu 运行时取证通道」。

| 系统 | 分类 | 发现位置(客户端入口) | 版本 | 相关配置 | 关联协议 | 依赖 | 优先级 | 证据等级 | 运行时取证 |
|---|---|---|---|---|---|---|---|---|---|
| Version/Resource Update (版本更新, 资源下载) | A. 核心系统 | xiazai (function 25000) | 1.4.11 | config_client.luac, config_notice.luac | 20100 | — | P2 | VERIFIED | — |
| Morale 士气 (士气) | C. 成长系统 | ?? | 1.4.11 | config_morale.luac, config_hero_morale.luac |  | Battle, Partner | P1 | STRONG_INFERENCE | — |
| Battle Replay / Video (战报, 战斗回放) | D. 战斗系统 | battlevideo_ctrl.luac | 1.4.11 | config_battlevideo.luac |  | Battle | P2 | VERIFIED | — |
| God War Battle (神魔战) | D. 战斗系统 | godwar (function 52) | 1.4.11 | config_sm_war_data.luac, config_god_unite_data.luac |  | Battle, Cross-server | P2 | VERIFIED | ⏳需MuMu取证 |
| Partner Atlas/图鉴 (伙伴图鉴) | F. 伙伴系统 | hero | 1.4.11 | config_partner_score.luac, config_hero_attr_opp.luac |  | Partner | P2 | VERIFIED | — |
| Partner Fetter/羁绊 (伙伴羁绊) | F. 伙伴系统 | hero | 1.4.11 | config_partner_fetter.luac |  | Partner | P2 | STRONG_INFERENCE | — |
| Guide System 引导 (新手引导, 剧情) | I. 任务系统 | guide | 1.4.11 | config_guide.luac, config_guider_up.luac, config_drama_data.luac, config_function_notice.luac |  | all | P1 | VERIFIED | — |
| Mystic Realm 秘境/遗迹 (秘境, mijing) | K. 副本系统 | mijing (function 1011) | 1.4.11 | config_treasure_plane_data.luac, config_dungeon_jieyi.luac, config_dungeon_seal_demon_data.luac |  | Dungeon | P1 | VERIFIED | ⏳需MuMu取证 |
| Shadow/Palace dungeon other (其余副本) | K. 副本系统 | dungeon* | 1.4.11 | config_dungeon_gods.luac, config_dungeon_seal_demon_data.luac, config_smjz.luac, config_primus.luac, config_golden_tower.luac |  | Dungeon | P1 | STRONG_INFERENCE | — |
| Scratch Card 刮刮乐 (刮卡, scratch) | L. 活动系统 | scratcher (function 51) | 1.4.11 | config_scratch_card.luac |  | Lottery | P1 | STRONG_INFERENCE | — |
| Festival/Operation Activity 节日/运营活动 (节日活动, fest) | L. 活动系统 | fest* | 1.4.11 | config_fest_data.json, config_fest_data.luac, config_festival_goods.luac, config_friend_regress.luac, config_holiday_regress_data.luac, config_holiday_util.luac, config_holiday_balloon.luac, config_holiday_crowd_lottery.luac, config_holiday_order_mission.luac, config_helloween_data.luac, config_huaguo_mountain_data.luac, config_week_calendar.luac |  | Activity infra | P1 | VERIFIED | ⏳需MuMu取证 |
| Answer Quiz 答题 (答题, answer) | L. 活动系统 | answer (function 3) | 1.4.11 | config_answer.luac, config_lantern_answer.luac |  | — | P1 | VERIFIED | ⏳需MuMu取证 |
| Guess 竞猜 (竞猜, guess) | L. 活动系统 | guess (function 25) | 1.4.11 | config_fun.luac, config_player_guess? |  | — | P1 | VERIFIED | ⏳需MuMu取证 |
| Treasure Hunt 夺宝/探宝 (夺宝, duobao) | L. 活动系统 | duobao (function 1013) | 1.4.11 | config_duobao.luac, config_treasure.luac, config_treasure_plane_data.luac, config_mission_treasure.luac, config_rune_treasure_data.luac, config_chest? | CS_13810..13817? | Economy, Dungeon | P1 | VERIFIED | ⏳需MuMu取证 |
| Return/Back Flow 回归 (回归, 老玩家) | L. 活动系统 | regress | 1.4.11 | config_friend_regress.luac, config_holiday_regress_data.luac |  | Activity | P1 | VERIFIED | — |
| Gift Recharge events 充值活动 (累计充值, 天降壕礼) | L. 活动系统 | charge_double (62) / tianjianghaoli (117) | 1.4.11 | config_every_charge.luac, config_once_charge.luac, config_charge_double? |  | Recharge | P1 | VERIFIED | — |
| Global Wish 全球许愿 (许愿, global wish) | L. 活动系统 | 1008 julong? | 1.4.11 | config_global_wish_data.luac, config_fangyao.luac, config_party.luac |  | — | P1 | STRONG_INFERENCE | — |
| Flower/Gift 送花 (送花, 花) | M. 社交系统 | flower (function 23) | 1.4.11 | config_flower.luac |  | Marriage, Social | P1 | VERIFIED | — |
| Party 宴会/派对 (宴会, party) | M. 社交系统 | party? | 1.4.11 | config_party.luac, config_fangyao.luac |  | Marriage | P1 | STRONG_INFERENCE | — |
| Cross-server 跨服 (跨服, cross) | N. 商业系统 / 对抗 | crossrace (22) / kuafu_guildwars (24) | 1.4.11 | — | 30100~31299 cross? | All PvP | P2 | STRONG_INFERENCE | ⏳需MuMu取证 |
| Mining 采矿 (采矿, 矿脉) | N. 商业系统 / 对抗 | mining? | 1.4.11 | config_mining.luac, config_mine_new.luac, config_mine_guild_data.luac |  | Guild | P2 | VERIFIED | ⏳需MuMu取证 |
| Attack City 攻城/领土战 (攻城, 领地战) | N. 商业系统 / 对抗 | qiangdao (102)? | 1.4.11 | config_attack_city.luac |  | Guild, Battle | P2 | STRONG_INFERENCE | — |
| Freight/Escort 押镖 (押镖, 护送) | N. 商业系统 / 对抗 | escort? | 1.4.11 | config_freight.luac, config_mission_escort.luac |  | Mission, Battle | P2 | STRONG_INFERENCE | ⏳需MuMu取证 |
| Gold/JinYin Tower activities (金银塔, jinyinta) | N. 商业系统 / 对抗 | jinyinta (function 56) | 1.4.11 | config_golden_tower.luac, config_single_tower.luac |  | Dungeon, Economy | P2 | VERIFIED | ⏳需MuMu取证 |
| Cross-server backend (跨服后台) | P. 后台系统 | (server) | 1.4.11 | — | — | — | P2 | STRONG_INFERENCE | — |
| Seal System 封印 (封印) | Q. 隐藏/未归类系统 | seal? | 1.4.11 | config_seal.luac, config_dungeon_seal_demon_data.luac, config_fangyao.luac |  | Dungeon, Boss | P2 | STRONG_INFERENCE | — |
| XiuLuo 修罗 (修罗, xiuluo) | Q. 隐藏/未归类系统 | xiuluo? | 1.4.11 | config_xiuluo_data.luac |  | PvP | P2 | STRONG_INFERENCE | — |
| Chief 会长/百官 (会长, 首席) | Q. 隐藏/未归类系统 | chief (function 41) | 1.4.11 | config_chief_award_data.luac |  | Rank | P2 | VERIFIED | — |
| God Redemption 神位/神减免 (神灵, godredeem) | Q. 隐藏/未归类系统 | god? | 1.4.11 | config_dungeon_gods.luac, config_god_unite_data.luac |  | Partner | P2 | VERIFIED | — |
| Dragon 神龙/巨龙 (神龙, 巨龙) | Q. 隐藏/未归类系统 | julong (function 1008) | 1.4.11 | config_dragon.luac, config_golden_dragon? |  | — | P2 | VERIFIED | — |
| Balloon 气球/多种活动 (气球, action_balloon) | Q. 隐藏/未归类系统 | action_balloon (function 48) | 1.4.11 | config_holiday_balloon.luac |  | Activity | P2 | VERIFIED | — |
| Dan War / 丹药战 (丹药, dan_war) | R. 未知系统 | ?? | 1.4.11 | config_dan_war.luac |  | — | P2 | UNKNOWN | — |
| YunYing Ops systems (运营活动) | R. 未知系统 | 33/34/37/40/101/103 etc (unnamed function ids) | 1.4.11 | config_function.json ids 33,34,37,40,101,103... |  | Activity | P2 | UNKNOWN | — |
| Color/Head system (染色, color) | R. 未知系统 | color? | 1.4.11 | config_color.luac, config_color_code.luac |  | Appearance | P2 | UNKNOWN | — |
| Equip Refine 装备洗练 (洗练, xilian, refine) | E. 装备系统 | UNKNOWN | 1.4.11 | — | — | Equipment | P2 | UNKNOWN | — |
| Gem / Socket 宝石 (宝石, gem, baoshi) | E. 装备系统 | UNKNOWN | 1.4.11 | — | — | Equipment | P2 | UNKNOWN | — |
| Soul Bone 魂骨 (魂骨, hun_gu, soulbone) | C. 成长系统 | UNKNOWN | 1.4.11 | — | — | Role, Equipment | P1 | UNKNOWN | — |
| Augment / Amplify 增幅 (增幅, zengfu, augment) | C. 成长系统 | UNKNOWN | 1.4.11 | — | — | Role Attribute | P1 | UNKNOWN | — |
| Red Dot / Badge 红点 (红点, reddot, red_point, badge, notice) | A. 核心系统 | UNKNOWN | 1.4.11 | — | — | all UI | P2 | UNKNOWN | — |
| UI State Sync UI状态 (UI状态, uistate, ui_state, ui_status) | A. 核心系统 | UNKNOWN | 1.4.11 | — | — | Protocol/Network | P2 | UNKNOWN | — |
| Combat Power 战力 (战力, power, zhanli, fight_power) | B. 角色系统 | UNKNOWN | 1.4.11 | — | — | Role Attribute | P2 | UNKNOWN | ⏳需MuMu取证 |
| Partner Training 伙伴培养 (伙伴培养, partner_train, hero_peiyang) | F. 伙伴系统 | UNKNOWN | 1.4.11 | — | — | Partner/Hero System | P2 | UNKNOWN | — |

## 逐项详述

### SYS_CORE_007 — Version/Resource Update
- **aliases**: 版本更新, 资源下载
- **version**: 1.4.11
- **client_entry**: xiazai (function 25000)
- **lua_modules**: file_update_1411.luac
- **protocols**: 20100
- **config_files**: config_client.luac, config_notice.luac
- **server_state**: not implemented (client-only)
- **evidence**: file_update_1411.luac + function id 25000
- **confidence**: VERIFIED
- **implementation_status**: client-only / not hooked

### SYS_GROWTH_005 — Morale 士气
- **aliases**: 士气
- **version**: 1.4.11
- **client_entry**: ??
- **protocols**: 
- **config_files**: config_morale.luac, config_hero_morale.luac
- **dependencies**: Battle, Partner
- **server_state**: not implemented
- **evidence**: config_morale + config_hero_morale only
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_BATTLE_003 — Battle Replay / Video
- **aliases**: 战报, 战斗回放
- **version**: 1.4.11
- **client_entry**: battlevideo_ctrl.luac
- **lua_modules**: battlevideo_ctrl.luac, battlevideo_data.luac, battlevideo_main_panel.luac, ownvideo_*.luac, peakvideo_*.luac
- **protocols**: 
- **config_files**: config_battlevideo.luac
- **dependencies**: Battle
- **server_state**: not implemented
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
- **dependencies**: Battle, Cross-server
- **server_state**: not implemented (client UI only)
- **evidence**: godwar_battle_* modules + config_sm_war
- **confidence**: VERIFIED
- **implementation_status**: client-only / not hooked
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_FRIEND_003 — Partner Atlas/图鉴
- **aliases**: 伙伴图鉴
- **version**: 1.4.11
- **client_entry**: hero
- **lua_modules**: partner_atlas_*.luac, partner_show_panel.luac, partner_pack_view.luac
- **protocols**: 
- **config_files**: config_partner_score.luac, config_hero_attr_opp.luac
- **dependencies**: Partner
- **server_state**: partial
- **evidence**: partner_atlas modules
- **confidence**: VERIFIED
- **implementation_status**: client UI / partial

### SYS_FRIEND_005 — Partner Fetter/羁绊
- **aliases**: 伙伴羁绊
- **version**: 1.4.11
- **client_entry**: hero
- **protocols**: 
- **config_files**: config_partner_fetter.luac
- **dependencies**: Partner
- **server_state**: not implemented
- **evidence**: config_partner_fetter only
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_QUEST_005 — Guide System 引导
- **aliases**: 新手引导, 剧情
- **version**: 1.4.11
- **client_entry**: guide
- **lua_modules**: action_ctrl.luac, action_panel.luac
- **protocols**: 
- **config_files**: config_guide.luac, config_guider_up.luac, config_drama_data.luac, config_function_notice.luac
- **dependencies**: all
- **server_state**: not implemented (client-side)
- **evidence**: config_guide + action_ctrl
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_DUNGEON_004 — Mystic Realm 秘境/遗迹
- **aliases**: 秘境, mijing
- **version**: 1.4.11
- **client_entry**: mijing (function 1011)
- **protocols**: 
- **config_files**: config_treasure_plane_data.luac, config_dungeon_jieyi.luac, config_dungeon_seal_demon_data.luac
- **dependencies**: Dungeon
- **server_state**: not implemented
- **evidence**: mijing function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_DUNGEON_005 — Shadow/Palace dungeon other
- **aliases**: 其余副本
- **version**: 1.4.11
- **client_entry**: dungeon*
- **lua_modules**: kunshentower_battleui.luac, smjz
- **protocols**: 
- **config_files**: config_dungeon_gods.luac, config_dungeon_seal_demon_data.luac, config_smjz.luac, config_primus.luac, config_golden_tower.luac
- **dependencies**: Dungeon
- **server_state**: not implemented
- **evidence**: config_dungeon_gods + smjz
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_ACT_005 — Scratch Card 刮刮乐
- **aliases**: 刮卡, scratch
- **version**: 1.4.11
- **client_entry**: scratcher (function 51)
- **protocols**: 
- **config_files**: config_scratch_card.luac
- **dependencies**: Lottery
- **server_state**: not implemented
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
- **dependencies**: Activity infra
- **server_state**: not implemented (event data only)
- **evidence**: config_fest_data.json + holiday_* configs
- **confidence**: VERIFIED
- **implementation_status**: client-event-data only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_ACT_007 — Answer Quiz 答题
- **aliases**: 答题, answer
- **version**: 1.4.11
- **client_entry**: answer (function 3)
- **protocols**: 
- **config_files**: config_answer.luac, config_lantern_answer.luac
- **server_state**: not implemented
- **evidence**: config_answer + answer function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_ACT_008 — Guess 竞猜
- **aliases**: 竞猜, guess
- **version**: 1.4.11
- **client_entry**: guess (function 25)
- **protocols**: 
- **config_files**: config_fun.luac, config_player_guess?
- **server_state**: not implemented
- **evidence**: guess function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_ACT_011 — Treasure Hunt 夺宝/探宝
- **aliases**: 夺宝, duobao
- **version**: 1.4.11
- **client_entry**: duobao (function 1013)
- **lua_modules**: duobao?
- **protocols**: CS_13810..13817?
- **config_files**: config_duobao.luac, config_treasure.luac, config_treasure_plane_data.luac, config_mission_treasure.luac, config_rune_treasure_data.luac, config_chest?
- **dependencies**: Economy, Dungeon
- **server_state**: not implemented
- **evidence**: config_duobao + duobao function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_ACT_012 — Return/Back Flow 回归
- **aliases**: 回归, 老玩家
- **version**: 1.4.11
- **client_entry**: regress
- **protocols**: 
- **config_files**: config_friend_regress.luac, config_holiday_regress_data.luac
- **dependencies**: Activity
- **server_state**: not implemented
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
- **evidence**: charge_double/tianjianghaoli function ids
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_ACT_015 — Global Wish 全球许愿
- **aliases**: 许愿, global wish
- **version**: 1.4.11
- **client_entry**: 1008 julong?
- **protocols**: 
- **config_files**: config_global_wish_data.luac, config_fangyao.luac, config_party.luac
- **server_state**: not implemented
- **evidence**: config_global_wish_data
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_SOCIAL_007 — Flower/Gift 送花
- **aliases**: 送花, 花
- **version**: 1.4.11
- **client_entry**: flower (function 23)
- **protocols**: 
- **config_files**: config_flower.luac
- **dependencies**: Marriage, Social
- **server_state**: not implemented
- **evidence**: config_flower + flower function id
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_SOCIAL_008 — Party 宴会/派对
- **aliases**: 宴会, party
- **version**: 1.4.11
- **client_entry**: party?
- **protocols**: 
- **config_files**: config_party.luac, config_fangyao.luac
- **dependencies**: Marriage
- **server_state**: not implemented
- **evidence**: config_party only
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only

### SYS_COMM_005 — Cross-server 跨服
- **aliases**: 跨服, cross
- **version**: 1.4.11
- **client_entry**: crossrace (22) / kuafu_guildwars (24)
- **lua_modules**: cross_ctrl.luac
- **protocols**: 30100~31299 cross?
- **dependencies**: All PvP
- **server_state**: not implemented (single-process)
- **evidence**: cross_ctrl.luac; mock_server single-process
- **confidence**: STRONG_INFERENCE
- **implementation_status**: not implemented
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_COMM_006 — Mining 采矿
- **aliases**: 采矿, 矿脉
- **version**: 1.4.11
- **client_entry**: mining?
- **protocols**: 
- **config_files**: config_mining.luac, config_mine_new.luac, config_mine_guild_data.luac
- **dependencies**: Guild
- **server_state**: not implemented
- **evidence**: config_mining + config_mine_guild_data
- **confidence**: VERIFIED
- **implementation_status**: client-config only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_COMM_008 — Attack City 攻城/领土战
- **aliases**: 攻城, 领地战
- **version**: 1.4.11
- **client_entry**: qiangdao (102)?
- **protocols**: 
- **config_files**: config_attack_city.luac
- **dependencies**: Guild, Battle
- **server_state**: not implemented
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
- **evidence**: config_freight
- **confidence**: STRONG_INFERENCE
- **implementation_status**: client-config only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_COMM_010 — Gold/JinYin Tower activities
- **aliases**: 金银塔, jinyinta
- **version**: 1.4.11
- **client_entry**: jinyinta (function 56)
- **protocols**: 
- **config_files**: config_golden_tower.luac, config_single_tower.luac
- **dependencies**: Dungeon, Economy
- **server_state**: not implemented
- **evidence**: jinyinta function id
- **confidence**: VERIFIED
- **implementation_status**: client-only
- **needs_mumu_runtime**: true （需 MuMu 运行时取证）

### SYS_BACK_002 — Cross-server backend
- **aliases**: 跨服后台
- **version**: 1.4.11
- **client_entry**: (server)
- **server_state**: not implemented
- **evidence**: single-process server
- **confidence**: STRONG_INFERENCE
- **implementation_status**: not implemented

### SYS_HIDDEN_001 — Seal System 封印
- **aliases**: 封印
- **version**: 1.4.11
- **client_entry**: seal?
- **protocols**: 
- **config_files**: config_seal.luac, config_dungeon_seal_demon_data.luac, config_fangyao.luac
- **dependencies**: Dungeon, Boss
- **server_state**: not implemented
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
- **evidence**: chief function id + config_chief_award
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_HIDDEN_005 — God Redemption 神位/神减免
- **aliases**: 神灵, godredeem
- **version**: 1.4.11
- **client_entry**: god?
- **lua_modules**: godredeem_ctrl.luac, godredeem_data.luac, godredeem_view.luac, godredeem_panel.luac, godredeem_item.luac, godredeem_aptitude*.luac
- **protocols**: 
- **config_files**: config_dungeon_gods.luac, config_god_unite_data.luac
- **dependencies**: Partner
- **server_state**: not implemented
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
- **evidence**: action_balloon function id
- **confidence**: VERIFIED
- **implementation_status**: client-only

### SYS_UNKNOWN_001 — Dan War / 丹药战
- **aliases**: 丹药, dan_war
- **version**: 1.4.11
- **client_entry**: ??
- **protocols**: 
- **config_files**: config_dan_war.luac
- **server_state**: not implemented
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
- **evidence**: config_function.json unnamed ids
- **confidence**: UNKNOWN
- **implementation_status**: unidentified ops entries

### SYS_UNKNOWN_004 — Color/Head system
- **aliases**: 染色, color
- **version**: 1.4.11
- **client_entry**: color?
- **protocols**: 
- **config_files**: config_color.luac, config_color_code.luac
- **dependencies**: Appearance
- **server_state**: not implemented
- **evidence**: config_color*
- **confidence**: UNKNOWN
- **implementation_status**: client-config only

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

