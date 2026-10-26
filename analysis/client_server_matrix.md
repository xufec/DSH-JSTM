# 客户端系统 → 服务端需求矩阵 client_server_matrix

> PHASE 0 审计产物。由 `analysis/jstm_game_systems/systems_master.json` 生成。
> 主目标版本 1.4.11。状态：✅ 已实现 / 🟡 部分实现 / ❌ 未实现。
> **⏳「需MuMu取证」= 该系统实现依赖真实运行数据（战斗数值/掉落表/装备属性/伙伴数值/怪物数值/战力公式/经验曲线/UI 显示值等），须在 MuMu 模拟器跑通 1.4.11 客户端 + mock_server 联调后才能确认真实值；详见 systems_master.md 顶部「MuMu 运行时取证通道」。**

| 系统 | APK 入口 | 协议 | 数据(config/DB) | 服务端 | 状态 |
|---|---|---|---|---|---|
| Account Login (帐号登录, 账号, 登录) | denglu_ctrl.luac | CS_1110 AccountLogin, CS_1199 heartbeat, CS_10001 FirstPack | config_login.luac, config_client.luac | roles,accounts tables present | implemented | ✅ 已实现 |
| Role Creation (创建角色) | role_ctrl.luac | CS_10101 RoleCreate, CS_10102 RoleLogin, CS_10103 RoleReL… | config_role_career.luac, config_role_face.luac, config_role_stock.luac | role… | implemented | ✅ 已实现 |
| Role Base/Init (角色基础信息, 角色初始化) | role_ctrl.luac | SC_10300, SC_10301, SC_10302, SC_10303 | config_game_data.luac, config_role_attr.luac, config_role_attribute.luac | ro… | implemented | ✅ 已实现 |
| Role Login (角色进入游戏, 登录角色) | denglu_ctrl.luac | CS_10102, SC_1110 account roles | config_login.luac | roles present | implemented | ✅ 已实现 |
| Scene & Movement (场景, 移动, 寻路, 自动寻路) | scene_controller.luac | CS_10200 RoleEnter, CS_10201, CS_10204, CS_10205 | config_map.luac, config_map_block.luac, config_map_npc.luac, config_map_icon_… | implemented | ✅ 已实现 |
| Protocol/Network Layer (网络协议层, 封包解包) | protocalrulesmgr.luac | all | — | — | implemented | ✅ 已实现 |
| Version/Resource Update (版本更新, 资源下载) | xiazai (function 25000) | 20100 | config_client.luac, config_notice.luac | — | not implemented (client-only) | ❌ 未实现 |
| Role Attribute (角色属性, 属性加点) | role (function 5000) | SC_10301/10302/10303, CS_10331, CS_10333 | config_role_attr.luac, config_role_attribute.luac, config_attr.luac, _attr.js… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Career/Job (职业) | menpai (function 10) | — | config_role_career.luac, config_role_cost.luac | roles.career col | implemented | ✅ 已实现 |
| Title System (称号) | title? | — | config_title.luac | role_title present | implemented | ✅ 已实现 |
| VIP System (VIP, 贵族) | super_vip (function 44) | — | config_vip.luac, config_vip_ernie_data.luac, config_charge_eyou.luac | role_a… | partial | 🟡 部分实现 |
| Experience/Level (经验, 升级, 等级礼包) | jitici? | CS_14600, CS_14601 level gift | config_role_cost.luac, config_guider_up.luac, config_fly_up.luac | levgift_go… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Avatar/Head & Chat Bubble (头像框, 聊天气泡) | set? | — | config_head_surface.luac, config_chat_bubble.luac, config_biaoqing.luac | rol… | partial | 🟡 部分实现 |
| Skill System (技能) | skill (function 1000) | CS_10401..10406, CS_20012 skill_play | config_skill.luac, config_skill_magic.luac, config_skill_scene.luac, config_s… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Talent/天赋 (天赋) | skill (function 1000) | — | config_skill_talent.luac, buff_tianfu_tips.luac | — | partial | 🟡 部分实现 |
| Practice/修炼 (Buff) (修炼, 修为) | cultivate | — | config_skill_xiulian.luac, config_buff_data.luac, config_insight.luac | role_… | implemented | ✅ 已实现 |
| Buff System (Buff) | battle buff | relay SC_20012/20013 buff | config_buff_data.luac | role_buffs present | implemented | ✅ 已实现 |
| Morale 士气 (士气) | ?? | — | config_morale.luac, config_hero_morale.luac | — | not implemented | ❌ 未实现 |
| Turn-based Battle (回合制战斗, 怪物) | battle_ctrl.luac | CS_20002, SC_20010, SC_20012, SC_20013, CS_20014, SC_20020 | config_battle.luac, config_combat.luac, config_fight.luac, config_mon_data.lu… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Auto-battle / AFK (挂机, 自动战斗) | automate (function 504) | — | config_guaji.luac, config_automate.luac, _guaji.json | guaji_state present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Battle Replay / Video (战报, 战斗回放) | battlevideo_ctrl.luac | — | config_battlevideo.luac | — | not implemented | ❌ 未实现 |
| God War Battle (神魔战) | godwar (function 52) | — | config_sm_war_data.luac, config_god_unite_data.luac | — | not implemented (client UI only) | ❌ 未实现 ⏳需MuMu取证 |
| Boss System (BOSS, 世界BOSS, 恶魔/魔王) | boss? | — | config_boss.luac, config_demon.luac | role_boss_kill present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Equipment System (装备) | equip? | CS_10500..10593, CS_11200~11205 partner equip | config_eqm_ancient.luac, config_eqm_starup_data.luac, config_marry_eqm_data.l… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Smith / Forge / Fuse (锻造, 合成, 融合, 装备升阶) | smith (function 11000) / hecheng (function 16000) | — | config_item_fuse.luac, config_intensify.luac, config_promote.luac, _promote.j… | partial | 🟡 部分实现 ⏳需MuMu取证 |
| Rune System (符文) | rune? | — | config_rune_data.luac, config_rune_dec.json, config_rune_treasure_data.luac, … | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Equip StarUp/强化 (装备升星, 强化, 装备强化) | smith | — | config_eqm_starup_data.luac, config_intensify.luac | — | partial | 🟡 部分实现 ⏳需MuMu取证 |
| Partner/Hero System (伙伴, 英雄, 随从) | hero (function 4000) | CS_10401..10406 | config_hero_base.luac, config_hero_info.luac, config_hero_attr.luac, config_h… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Formation / 阵法 (阵法, 阵型) | formation (function 3000) | — | config_formation.luac | role_form present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Partner Atlas/图鉴 (伙伴图鉴) | hero | — | config_partner_score.luac, config_hero_attr_opp.luac | — | partial | ❌ 未实现 |
| Partner Recruit/招募 (伙伴招募, 抽卡) | recruit (function 113) | — | config_partner_skill.luac, config_lucky_box_data.luac | — | partial | 🟡 部分实现 ⏳需MuMu取证 |
| Partner Fetter/羁绊 (伙伴羁绊) | hero | — | config_partner_fetter.luac | — | not implemented | ❌ 未实现 |
| Wing System 翅膀 (翅膀, wind) | wind (function 20000) | — | config_wing_data.luac | role_wing present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Mount 坐骑 (坐骑) | ride (function 18000) | CS_10551.. | config_ride.luac | role_ride present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Beast 灵兽 (灵兽, Lingshou) | lingshou (function 19000) | — | config_lingshou.luac, config_lingshou_speak.luac | role_lingshou present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Soul 元神 (元神) | yuanshen (function 22000) | — | config_yuanshen.luac | role_yuanshen present | implemented | ✅ 已实现 |
| Divine Artifact 神器 (神器) | shenqi (function 21000) | — | config_shenqi.luac, config_partner_shenqi.luac, config_artifact_image.luac | … | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Fate/Natal 命格 (命格) | mingge (function 24000) | — | config_mingge.luac, _mingge_cfg.json | role_mingge present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Magic Weapon 法宝 (法宝) | fabao? | CS_11200~11205? | config_fabao.luac | role_fabao present | implemented | ✅ 已实现 |
| Vehicle/Chair 座驾 (座驾, 椅子) | chair? | — | config_chair.luac | role_chair present | implemented | ✅ 已实现 |
| Fashion/Skin 时装 (时装) | fashion? | 10573, 10574, 10575, 10576, 10578 | config_fashion.luac, config_fashion_upgrade.luac, config_fashion_constant.lua… | implemented (activate/wear/star/unwear); attribute contribution not yet wired | ✅ 已实现 ⏳需MuMu取证 |
| Halo 光环 (光环) | halo (game/halo/*) | 19100, 19103, 19104 | config_halo.luac | role_halo, role_halo_equip | implemented (info + equip slots); upgrade not implemented | ✅ 已实现 |
| Assets/Currency System (货币, 资源, 资产) | all | SC_10303 assets | config_game_data.luac (AssetsEnToCode) | role_assets present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Inventory/Bag 背包 (背包, 道具, 物品) | bag (function 2000) | CS_10500..10593 | config_item.luac, config_item_misc.luac, config_item_gift.luac, item_config.j… | implemented | ✅ 已实现 |
| Mall/Shop 商城 (商城, 商店) | mall (function 501) | CS_12801..12856, CS_13401..13416 | config_mall.luac, config_shop.luac, config_exchange.luac, mall_config.json, m… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Storage/Warehouse 仓库 (仓库, 背包扩展) | bag (function 2000) | CS_10714, CS_10621 | config_storage_data.luac | store_items present | implemented | ✅ 已实现 |
| Trade Market 市场/交易 (市场, 寄售) | market (function 7000) | CS_18909.. | config_market.luac | role_market, role_market_goods present | implemented | ✅ 已实现 |
| Black Market 黑市 (黑市) | black market? | CS_18909? | config_black_market.luac | — | partial (generic response) | 🟡 部分实现 |
| Exchange 兑换 (兑换, duihuan) | duihuan (function 20) / yunyingduihuan (21) | — | config_exchange.luac, mall_exchange.json | — | partial | 🟡 部分实现 |
| Auction/拍卖 (拍卖, paimai) | paimai (function 43) | 18020, 18021, 18022 | config_auction_data.luac, server/cfg_kconfig/config_auction_data.json | role_… | implemented (list + one-price buy); bidding not implemented | ✅ 已实现 |
| Mail 邮件 (邮件) | mail? | CS_10800 mail | config_notice.luac | role_mail present | implemented | ✅ 已实现 |
| Recharge/Payment 充值 (充值, 首充) | recharge (function 27) | CS_12831, CS_13401.. | config_charge.luac, config_charge_eyou.luac, config_first_charge.luac, config… | partial | 🟡 部分实现 |
| Gift Item 礼包/道具 (礼包, 宝箱) | all | — | config_item_gift.luac, config_lucky_box_data.luac, config_reward_box_data.lua… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Mission/Quest 任务 (任务, 主线, 任务奖励) | mission (function 10000) | CS_12400..12421, CS_12407/08/09 | config_mission.luac, config_mission_buffy.luac, config_chapter.luac, mission_… | implemented | ✅ 已实现 |
| Daily/Active 日常活跃 (日常, 活跃度) | richang (function 503) / daily | CS_10301? | config_richang.luac, config_function.luac, _richang.json | daily_progress, da… | implemented | ✅ 已实现 |
| Achievement 成就 (成就) | chengjiu (function 17000) | — | config_chengjiu.luac, _chengjiu.json, _chengjiu_map.json | chengjiu_progress … | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Growth Target 成长目标 (目标, 成长目标) | target (function 505) | — | config_growth_target_data.luac, config_growth_target.json, config_fly_up.luac… | partial | 🟡 部分实现 |
| Guide System 引导 (新手引导, 剧情) | guide | — | config_guide.luac, config_guider_up.luac, config_drama_data.luac, config_func… | not implemented (client-side) | ❌ 未实现 |
| World Map / Region (世界地图, 区域) | world map | — | config_world_map.luac, config_map.luac, config_team_destination.luac | — | implemented | ✅ 已实现 |
| Team Group 组队 (组队, 团队) | team (function 12000) | 13200, 13201, 13202, 13203, 13204, 13210, 13218, 13226, 1… | config_team_destination.luac | role_team, role_team_invite | implemented (core + multi-member invite) | ✅ 已实现 |
| Dungeon 副本 (副本, 地牢) | dungeon? | CS_11700..11713?, CS_13028.. | config_dungeon_new.luac, config_dungeon_reward_desc.luac, config_dungeon_vip_… | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Endless Dungeon 无尽/深渊 (无尽, 深渊, endless) | endless | — | config_dungeon_endless_data.luac | dungeon_progress shared | partial | 🟡 部分实现 ⏳需MuMu取证 |
| Tower 塔 (爬塔, 镇魂塔, 恶魔塔) | tower / demontower | CS_13035, CS_13038, SC_13752.. | config_dungeon_tower.luac, config_single_tower.luac, config_golden_tower.luac… | partial | 🟡 部分实现 ⏳需MuMu取证 |
| Mystic Realm 秘境/遗迹 (秘境, mijing) | mijing (function 1011) | — | config_treasure_plane_data.luac, config_dungeon_jieyi.luac, config_dungeon_se… | not implemented | ❌ 未实现 ⏳需MuMu取证 |
| Shadow/Palace dungeon other (其余副本) | dungeon* | — | config_dungeon_gods.luac, config_dungeon_seal_demon_data.luac, config_smjz.lu… | not implemented | ❌ 未实现 |
| Sign-in/Check-in 签到 (签到, 每日签到) | sign? | CS_14100 签到, CS_14101 | config_checkin.luac, config_seven_login.luac | sign_got present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Seven-Day Login 七日签到 (七日登录, 七日活动) | seven login | — | config_seven_login.luac, config_fest_data.luac | sign_got shared | partial | 🟡 部分实现 |
| Invest 投资 (投资, invest) | invest_sec (function 106) | CS_13901.. | config_invest.json, config_invest.luac, config_invest_dec.json, _invest_cfg.j… | implemented | ✅ 已实现 |
| Turntable/Lucky Draw 转盘抽奖 (转盘, lucky_turntable, rotatetable, dial) | rotatetable (function 8) / lucky_turntable (47) | — | config_gold_ernie_data.luac, config_ernie_data.luac, config_holiday_lucky_tur… | partial (dial reward stub) | 🟡 部分实现 ⏳需MuMu取证 |
| Scratch Card 刮刮乐 (刮卡, scratch) | scratcher (function 51) | — | config_scratch_card.luac | — | not implemented | ❌ 未实现 |
| Festival/Operation Activity 节日/运营活动 (节日活动, fest) | fest* | — | config_fest_data.json, config_fest_data.luac, config_festival_goods.luac, con… | not implemented (event data only) | ❌ 未实现 ⏳需MuMu取证 |
| Answer Quiz 答题 (答题, answer) | answer (function 3) | — | config_answer.luac, config_lantern_answer.luac | — | not implemented | ❌ 未实现 ⏳需MuMu取证 |
| Guess 竞猜 (竞猜, guess) | guess (function 25) | — | config_fun.luac, config_player_guess? | — | not implemented | ❌ 未实现 ⏳需MuMu取证 |
| Money Tree 摇钱树 (摇钱树, moneytree) | moneytree (function 26) | — | config_money_tree.luac | role_tree present | implemented | ✅ 已实现 |
| Pray/QiFu 祈福 (祈福) | qifu? | — | config_qifu.luac, config_flying? | role_qifu present | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Treasure Hunt 夺宝/探宝 (夺宝, duobao) | duobao (function 1013) | CS_13810..13817? | config_duobao.luac, config_treasure.luac, config_treasure_plane_data.luac, co… | not implemented | ❌ 未实现 ⏳需MuMu取证 |
| Return/Back Flow 回归 (回归, 老玩家) | regress | — | config_friend_regress.luac, config_holiday_regress_data.luac | — | not implemented | ❌ 未实现 |
| Gift Recharge events 充值活动 (累计充值, 天降壕礼) | charge_double (62) / tianjianghaoli (117) | — | config_every_charge.luac, config_once_charge.luac, config_charge_double? | — | not implemented | ❌ 未实现 |
| Point/Qing Fu activities 点/dnf/live (点券活动, dnf活动, 直播) | live? | — | config_dnf_data.luac, config_live.luac, config_source_data.luac | role_point … | implemented (role_point) / activities not hooked | 🟡 部分实现 |
| Global Wish 全球许愿 (许愿, global wish) | 1008 julong? | — | config_global_wish_data.luac, config_fangyao.luac, config_party.luac | — | not implemented | ❌ 未实现 |
| Chat System (聊天, 社交) | chat? | CS_10800.. | config_chat_bubble.luac, config_sns.luac | role_chat present | implemented | ✅ 已实现 |
| Friend System (好友) | friend (function 6000) | — | config_friend_zone_data.luac, config_friend_regress.luac | no dedicated frien… | partial | 🟡 部分实现 |
| Moments/朋友圈 (朋友圈, 动态) | friend zone | — | config_friend_zone_data.luac | role_moments present | implemented | ✅ 已实现 |
| Guild 公会 (公会, 帮派) | guild (function 9000) | CS_17500..17519, CS_19509.. | config_guild.luac, config_guild_animal.luac, config_guild_exploit_data.luac, … | implemented (core) | ✅ 已实现 |
| Marriage 结婚 (婚姻, 结婚系统) | wedding (function 17) | 18300, 18301, 18302, 18303, 18313, 18314, 18316, 18318, 1… | config_marry_data.luac, config_marry_eqm_data.luac, config_spouse.luac, confi… | implemented (propose->accept->marry->divorce->ring); target via server-side intent table | ✅ 已实现 ⏳需MuMu取证 |
| Jiebai Soulmate 结拜 (结拜, 义结金兰) | jiebailiucheng (110) / jiebaitoupiao (506) | 19505, 19511, 19512, 19513, 19514, 19524, 19530, 19533, 1… | config_jiebai_data.luac, config_dungeon_jieyi.luac | role_jiebai | implemented (create/space/member list/invite/confirm/upgrade/cancel) | ✅ 已实现 ⏳需MuMu取证 |
| Flower/Gift 送花 (送花, 花) | flower (function 23) | — | config_flower.luac | — | not implemented | ❌ 未实现 |
| Party 宴会/派对 (宴会, party) | party? | — | config_party.luac, config_fangyao.luac | — | not implemented | ❌ 未实现 |
| Guild Wars 公会战 (公会战, 宗门战, guildwars) | gangwars (14) / guildwars (15) / kuafu_guildwars (24) / guildmatchwar (1012) | CS_17501, CS_195?, CS_130?... | config_guild_match_war_data.luac, config_guild_tree_data.luac, config_sm_war_… | partial (mock handles 17501 by type) | 🟡 部分实现 |
| Guild Tree/Animal/Skill sub (公会科技, 公会神兽, 公会技能) | guild | — | config_guild_tree_data.luac, config_guild_animal.luac, config_guild_skill_dat… | partial | 🟡 部分实现 |
| Rank 排行榜 (排行榜) | rank? / actionrank (16) | CS_16900..16903 | config_rank.luac, config_rank.full.json, config_rank.asm | no dedicated rank … | partial (derived) | 🟡 部分实现 ⏳需MuMu取证 |
| Arena 竞技场 (竞技场) | arena? | CS_11300..11310, CS_11301 | config_arena_data.luac, config_arena_msg.luac, config_trophy_arena_data.luac … | implemented | ✅ 已实现 ⏳需MuMu取证 |
| Peakwar 巅峰战 (巅峰战, 精英赛) | peakwar (function 28) | CS_130?.., CS_113?.. | config_peak_war_data.luac | peakwar_state present | implemented | ✅ 已实现 |
| Race 竞速/种族战 (竞速, race, 跨服竞速) | race (function 12) / crossrace (22) | CS_130?.. | config_race? | race_state present | implemented | ✅ 已实现 |
| Cross-server 跨服 (跨服, cross) | crossrace (22) / kuafu_guildwars (24) | 30100~31299 cross? | — | — | not implemented (single-process) | ❌ 未实现 ⏳需MuMu取证 |
| Mining 采矿 (采矿, 矿脉) | mining? | — | config_mining.luac, config_mine_new.luac, config_mine_guild_data.luac | — | not implemented | ❌ 未实现 ⏳需MuMu取证 |
| Manor/Oasis 庄园/领地 (庄园, manor) | manor? | — | config_manor.luac, config_garden_data.luac, config_build.luac | role_build, r… | implemented (build) | ✅ 已实现 |
| Attack City 攻城/领土战 (攻城, 领地战) | qiangdao (102)? | — | config_attack_city.luac | — | not implemented | ❌ 未实现 |
| Freight/Escort 押镖 (押镖, 护送) | escort? | — | config_freight.luac, config_mission_escort.luac | — | not implemented | ❌ 未实现 ⏳需MuMu取证 |
| Gold/JinYin Tower activities (金银塔, jinyinta) | jinyinta (function 56) | — | config_golden_tower.luac, config_single_tower.luac | — | not implemented | ❌ 未实现 ⏳需MuMu取证 |
| GM Tools (GM命令, 调试) | gm? | CS_10922..10932?, CS_11999? | config_gm_cmd.luac, config_client.luac | — | implemented (debug cmds) | ✅ 已实现 |
| Server Backend/DB (后台, 数据库) | (server) | — | — | all tables in roles.db | implemented | ✅ 已实现 |
| Cross-server backend (跨服后台) | (server) | — | — | — | not implemented | ❌ 未实现 |
| Seal System 封印 (封印) | seal? | — | config_seal.luac, config_dungeon_seal_demon_data.luac, config_fangyao.luac | — | not implemented | ❌ 未实现 |
| XiuLuo 修罗 (修罗, xiuluo) | xiuluo? | — | config_xiuluo_data.luac | — | not implemented | ❌ 未实现 |
| Chief 会长/百官 (会长, 首席) | chief (function 41) | — | config_chief_award_data.luac | — | not implemented | ❌ 未实现 |
| Star Soul 星魂 (星魂, xinghun, soulstar) | xinghun (function 28000) | — | config_rune_star? | role_runes? | partial | 🟡 部分实现 |
| God Redemption 神位/神减免 (神灵, godredeem) | god? | — | config_dungeon_gods.luac, config_god_unite_data.luac | — | not implemented | ❌ 未实现 |
| Dragon 神龙/巨龙 (神龙, 巨龙) | julong (function 1008) | — | config_dragon.luac, config_golden_dragon? | — | not implemented | ❌ 未实现 |
| Balloon 气球/多种活动 (气球, action_balloon) | action_balloon (function 48) | — | config_holiday_balloon.luac | — | not implemented | ❌ 未实现 |
| Dan War / 丹药战 (丹药, dan_war) | ?? | — | config_dan_war.luac | — | not implemented | ❌ 未实现 |
| YunYing Ops systems (运营活动) | 33/34/37/40/101/103 etc (unnamed function ids) | — | config_function.json ids 33,34,37,40,101,103... | — | not implemented | ❌ 未实现 |
| Insight 顿悟/洞察 (顿悟, 洞察) | insight? | — | config_insight.luac | roles.insight_status field only | partial | 🟡 部分实现 |
| Color/Head system (染色, color) | color? | — | config_color.luac, config_color_code.luac | — | not implemented | ❌ 未实现 |
| Equip Refine 装备洗练 (洗练, xilian, refine) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 |
| Gem / Socket 宝石 (宝石, gem, baoshi) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 |
| Soul Bone 魂骨 (魂骨, hun_gu, soulbone) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 |
| Augment / Amplify 增幅 (增幅, zengfu, augment) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 |
| Drop / Loot Table 掉落 (掉落, drop, loot) | UNKNOWN | — | config_mon_data.luac (drop refs), config_item_drop? | UNKNOWN | partial (drop resolved via gift/item path) | 🟡 部分实现 ⏳需MuMu取证 |
| Red Dot / Badge 红点 (红点, reddot, red_point, badge, notice) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 |
| UI State Sync UI状态 (UI状态, uistate, ui_state, ui_status) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 |
| Combat Power 战力 (战力, power, zhanli, fight_power) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 ⏳需MuMu取证 |
| Partner Training 伙伴培养 (伙伴培养, partner_train, hero_peiyang) | UNKNOWN | — | — | UNKNOWN | unknown | ❌ 未实现 |
| Partner Equipment 伙伴装备 (伙伴装备, partner_equip, hero_equip, partner_eqm) | UNKNOWN | CS_11200~11205 partner equip (referenced in SYS_EQUIP_001) | — | UNKNOWN | partial (protocol range referenced) | 🟡 部分实现 |
