# 客户端与服务器需求矩阵 client_server_matrix（124 系统 × 10 字段）

> PHASE C0 只读审计产物。对齐 `analysis/jstm_game_systems/systems_master.json`（124 系统）。
> 证据基线：`server/mock_server.py`（19390 行，`if cmd==N` 旧链；DISPATCH_TABLE 兼容层在 L39）、`server/minloop/min_loop_server.py`（145/145 自检）、`analysis/extraction/phase1_cs_inventory.md`（实抓 316 CS）、`tests/1.4.11/FINAL_REGRESSION.md`。
> 行号一律指 `server/mock_server.py`；`L<n>` = 文件第 n 行。无法核验处标 UNKNOWN。

**覆盖统计**：共 124 系统；已实现 60 / 部分实现 29 / 未实现 35。

> 注：实测 mock_server.py 的 `if cmd==N` 旧链覆盖 801 个 opcode（远超 HANDOFF 所记"注册 19→34"，后者为 `@register` DISPATCH_TABLE 计数；旧链才是真实分发面）。答题(161xx)/刮刮乐(16651)/成长目标(305xx)/好友(133xx) 在 PHASE2.11 已由独立模块实现（mock_server.py:102-105 import 注册为证），比 PHASE0 unimplemented 清单更新，本表以源码为准。

## 总览表

| # | system_id | 系统 | 状态 | 证据级 | 请求协议 | 当前实现证据(摘) |
|---|---|---|---|---|---|---|
| 1 | SYS_CORE_001 | Account Login 账号登录 | 已实现 | CONFIRMED | CS_1110 AccountLogin, CS_119 | mock_server.py:9968 cmd==1110 登录 |
| 2 | SYS_CORE_002 | Role Creation 创建角色 | 已实现 | CONFIRMED | CS_10101 RoleCreate, CS_1010 | mock_server.py:15929 cmd==10101 建角 |
| 3 | SYS_CORE_003 | Role Base/Init 角色基础 | 已实现 | CONFIRMED | SC_10300/10301/10302/10303（服 | mock_server.py:17260 cmd==10300 |
| 4 | SYS_CORE_004 | Role Login 进入游戏 | 已实现 | CONFIRMED | CS_10102 RoleLogin | mock_server.py:15851 cmd in(10102,10103) |
| 5 | SYS_CORE_005 | Scene & Movement 场景移动 | 已实现 | VERIFIED | CS_10200 进场景, CS_10201, CS_1 | mock_server.py:15957 cmd==10200 |
| 6 | SYS_CORE_006 | Protocol/Network Layer 网络层 | 已实现 | CONFIRMED | all（承载全部 CS） | protocol/frame+fields |
| 7 | SYS_CORE_007 | Version/Resource Update 版本更新 | 部分实现 | STRONG_INFERENCE | 20100 | mock_server.py:17144 cmd==20100 有占位处理器 |
| 8 | SYS_ROLE_001 | Role Attribute 角色属性 | 已实现 | VERIFIED | CS_10331, CS_10333 | mock_server.py:17047 10301 |
| 9 | SYS_ROLE_002 | Career/Job 职业 | 已实现 | CONFIRMED | （随 10101 建角携带） | mock_server.py:15929 cmd==10101 写入 career |
| 10 | SYS_ROLE_003 | Title System 称号 | 已实现 | VERIFIED | CS_14901（接 role_title） | mock_server.py:16243 cmd==14901 |
| 11 | SYS_ROLE_004 | VIP System 贵族/VIP | 部分实现 | VERIFIED | CS_16701（vip_lev 上传） | mock_server.py:10344 cmd==16701(vip_lev=1) |
| 12 | SYS_ROLE_005 | Experience/Level 经验等级 | 已实现 | VERIFIED | CS_14600, CS_14601 等级礼包 | mock_server.py:17732 cmd in(14600,14601) 等级礼包 |
| 13 | SYS_ROLE_006 | Avatar/Head & Chat Bubble 头像框气泡 | 部分实现 | INFERENCE | UNKNOWN（随角色信息携带） | systems_master: roles 字段 only |
| 14 | SYS_GROWTH_001 | Skill System 技能 | 已实现 | VERIFIED | CS_10401..10406, CS_20012 技能 | mock_server.py:18262 cmd in(10401..10404) |
| 15 | SYS_GROWTH_002 | Talent/天赋 | 部分实现 | VERIFIED | CS_10601/10610/10651（面板） | mock_server.py:13008 cmd in(10601,10610,10622, |
| 16 | SYS_GROWTH_003 | Practice/修炼 Buff | 已实现 | CONFIRMED | CS_10621 修炼帧 | mock_server.py:16127 cmd==10621 |
| 17 | SYS_GROWTH_004 | Buff System Buff | 已实现 | VERIFIED | （随战斗 CS_20012/20013） | systems_master: role_buffs present |
| 18 | SYS_GROWTH_005 | Morale 士气 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 19 | SYS_BATTLE_001 | Turn-based Battle 回合战斗 | 已实现 | VERIFIED | CS_20002 开战, CS_20014 | mock_server.py:17384 cmd==20002 |
| 20 | SYS_BATTLE_002 | Auto-battle/AFK 挂机 | 已实现 | VERIFIED | CS_15400 族(挂机) | mock_server.py:18736 cmd==15400 |
| 21 | SYS_BATTLE_003 | Battle Replay/Video 战报回放 | 未实现 | VERIFIED | UNKNOWN | mock_server 无战报 CS handler |
| 22 | SYS_BATTLE_004 | God War Battle 神魔战 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 23 | SYS_BATTLE_005 | Boss System BOSS | 已实现 | VERIFIED | CS_20002（击杀 BOSS） | systems_master: role_boss_kill present |
| 24 | SYS_EQUIP_001 | Equipment System 装备 | 已实现 | VERIFIED | CS_10500..10593, CS_11200~11 | mock_server.py:13370 cmd==10593 |
| 25 | SYS_EQUIP_002 | Smith/Forge/Fuse 锻造合成 | 部分实现 | VERIFIED | CS_10523/10527/10528 | mock_server.py:13236 cmd==10523 |
| 26 | SYS_EQUIP_003 | Rune System 符文 | 已实现 | VERIFIED | CS_11240, CS_21400..21414 | mock_server.py:13249 cmd==11240 |
| 27 | SYS_EQUIP_004 | Equip StarUp/强化 装备升星 | 部分实现 | CONFIRMED | CS_10527/10528 | mock_server.py:16986 10527 |
| 28 | SYS_FRIEND_001 | Partner/Hero System 伙伴 | 已实现 | VERIFIED | CS_11215, CS_11216 | mock_server.py:18173 cmd==11215 伙伴面板 |
| 29 | SYS_FRIEND_002 | Formation 阵法 | 已实现 | VERIFIED | CS_11237(formation_type) | phase1_cs_inventory: CS_11237 formation_type=1 |
| 30 | SYS_FRIEND_003 | Partner Atlas 伙伴图鉴 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 31 | SYS_FRIEND_004 | Partner Recruit 伙伴招募/抽卡 | 部分实现 | INFERENCE | UNKNOWN | mock_server 无独立招募 handler |
| 32 | SYS_FRIEND_005 | Partner Fetter 伙伴羁绊 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 33 | SYS_APPEAR_001 | Wing System 翅膀 | 已实现 | VERIFIED | CS_11600..11607 | mock_server.py:14887 cmd==11600 |
| 34 | SYS_APPEAR_002 | Mount 坐骑 | 已实现 | VERIFIED | CS_10551.., CS_15501 | mock_server.py:15297 cmd==15501 |
| 35 | SYS_APPEAR_003 | Beast 灵兽 | 已实现 | VERIFIED | CS_15801 | mock_server.py:14807 cmd==15801 |
| 36 | SYS_APPEAR_004 | Soul 元神 | 已实现 | VERIFIED | CS_19406 | mock_server.py:14840 cmd==19406 |
| 37 | SYS_APPEAR_005 | Divine Artifact 神器 | 已实现 | VERIFIED | CS_15700..15704 | mock_server.py:14850 cmd==15700 |
| 38 | SYS_APPEAR_006 | Fate/Natal 命格 | 已实现 | VERIFIED | CS_19400..19414 | mock_server.py:15232 cmd==19400 |
| 39 | SYS_APPEAR_007 | Magic Weapon 法宝 | 已实现 | VERIFIED | CS_11200~11205 | mock_server.py:18127 cmd==11200 |
| 40 | SYS_APPEAR_008 | Vehicle/Chair 座驾 | 已实现 | INFERENCE | UNKNOWN（随外观族） | systems_master: role_chair present |
| 41 | SYS_APPEAR_009 | Fashion/Skin 时装 | 已实现 | VERIFIED | CS_10573,10574,10575,10576,1 | mock_server.py:13383 cmd in(10573..10578) |
| 42 | SYS_APPEAR_010 | Halo 光环 | 部分实现 | VERIFIED | CS_19100,19103,19104 | mock_server.py:13427 cmd==19100 |
| 43 | SYS_ECON_001 | Assets/Currency 货币资产 | 已实现 | CONFIRMED | SC_10303 资产推送(服务器主动) | mock_server.py:16098 cmd==10303 |
| 44 | SYS_ECON_002 | Inventory/Bag 背包 | 已实现 | VERIFIED | CS_10500..10593 | mock_server.py:19229 cmd==10502 背包同步 |
| 45 | SYS_ECON_003 | Mall/Shop 商城 | 已实现 | VERIFIED | CS_12801..12856, CS_13401..1 | mock_server.py:16770 cmd in(12801..) |
| 46 | SYS_ECON_004 | Storage/Warehouse 仓库 | 已实现 | VERIFIED | CS_10714, CS_10621 | mock_server.py:17711 cmd==10714 |
| 47 | SYS_ECON_005 | Trade Market 市场/交易 | 已实现 | VERIFIED | CS_18909.. | mock_server.py:10180 cmd==18909 |
| 48 | SYS_ECON_006 | Black Market 黑市 | 部分实现 | VERIFIED | CS_18909(通用) | mock_server.py:10180 cmd==18909(通用 stub) |
| 49 | SYS_ECON_007 | Exchange 兑换 | 部分实现 | INFERENCE | CS_13403, duihuan(20)/yunyin | mock_server.py:10215 cmd==13403 |
| 50 | SYS_ECON_008 | Auction 拍卖 | 部分实现 | VERIFIED | CS_18020,18021,18022 | mock_server.py:12140 cmd==18020 拍卖行 |
| 51 | SYS_ECON_009 | Mail 邮件 | 已实现 | VERIFIED | CS_10800 | mock_server.py:18236 cmd==10800 |
| 52 | SYS_ECON_010 | Recharge/Payment 充值 | 部分实现 | VERIFIED | CS_12831, CS_13401.. | mock_server.py:16594 cmd==12831 |
| 53 | SYS_ECON_011 | Gift Item 礼包/宝箱 | 已实现 | VERIFIED | CS_10505(使用) | mock_server.py:17647 cmd==10505 |
| 54 | SYS_QUEST_001 | Mission/Quest 任务 | 已实现 | CONFIRMED | CS_12400..12421, CS_12407/08 | mock_server.py:16084 cmd==12400 |
| 55 | SYS_QUEST_002 | Daily/Active 日常活跃 | 已实现 | VERIFIED | CS_10301(日常数据) | systems_master: daily_progress/daily_lingqu pr |
| 56 | SYS_QUEST_003 | Achievement 成就 | 已实现 | VERIFIED | CS_16400 | mock_server.py:18629 cmd==16400 |
| 57 | SYS_QUEST_004 | Growth Target 成长目标 | 部分实现 | VERIFIED | CS_30500,30501,30502 | mock_server.py:11751 cmd==30500 |
| 58 | SYS_QUEST_005 | Guide System 新手引导 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 59 | SYS_MAP_001 | World Map 世界地图 | 已实现 | INFERENCE | （随 CS_10200） | systems_master: implemented(basic) |
| 60 | SYS_MAP_002 | Team Group 组队 | 已实现 | VERIFIED | CS_13200,13201,13202,13204,1 | mock_server.py:10778 cmd in(13200..) |
| 61 | SYS_DUNGEON_001 | Dungeon 副本 | 已实现 | VERIFIED | CS_11700..11713, CS_12000, C | mock_server.py:17905 cmd==11700 |
| 62 | SYS_DUNGEON_002 | Endless Dungeon 无尽/深渊 | 部分实现 | INFERENCE | CS_13035/13038(共用塔族) | systems_master: dungeon_progress shared |
| 63 | SYS_DUNGEON_003 | Tower 塔/爬塔 | 部分实现 | VERIFIED | CS_13035,13038 | mock_server.py:15702 cmd==13035 |
| 64 | SYS_DUNGEON_004 | Mystic Realm 秘境/遗迹 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 65 | SYS_DUNGEON_005 | Shadow/Palace dungeon 其余副本 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 66 | SYS_ACT_001 | Sign-in/Check-in 签到 | 已实现 | CONFIRMED | CS_14100, CS_14101 | mock_server.py:16981 cmd in(14100,14101) |
| 67 | SYS_ACT_002 | Seven-Day Login 七日签到 | 部分实现 | INFERENCE | UNKNOWN(随签到) | systems_master: sign_got shared |
| 68 | SYS_ACT_003 | Invest 投资 | 已实现 | VERIFIED | CS_13901.. | mock_server.py:10354 cmd==13901 |
| 69 | SYS_ACT_004 | Turntable/Lucky Draw 转盘 | 部分实现 | INFERENCE | UNKNOWN | mock_server 无 DB |
| 70 | SYS_ACT_005 | Scratch Card 刮刮乐 | 已实现 | VERIFIED | CS_16651,16652 | mock_server.py:104 import scratch.handler 注册16 |
| 71 | SYS_ACT_006 | Festival/Operation 节日运营活动 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 72 | SYS_ACT_007 | Answer Quiz 答题 | 已实现 | VERIFIED | CS_16100,16101,16102,16103 | mock_server.py:102 import answer.handler 注册161 |
| 73 | SYS_ACT_008 | Guess 竞猜 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 74 | SYS_ACT_009 | Money Tree 摇钱树 | 已实现 | INFERENCE | UNKNOWN | mock_server.py:3104 role_tree 等级 |
| 75 | SYS_ACT_010 | Pray/QiFu 祈福 | 已实现 | INFERENCE | UNKNOWN | mock_server.py:3294 祈福次数 |
| 76 | SYS_ACT_011 | Treasure Hunt 夺宝探宝 | 部分实现 | STRONG_INFERENCE | CS_13810..13817 | mock_server.py:12429 cmd in(13810..13817) |
| 77 | SYS_ACT_012 | Return/Back Flow 回归 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 78 | SYS_ACT_013 | Gift Recharge 累计充值活动 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 79 | SYS_ACT_014 | Point/QingFu 点/dnf/live | 部分实现 | INFERENCE | UNKNOWN | systems_master: role_point present / activitie |
| 80 | SYS_ACT_015 | Global Wish 全球许愿 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 81 | SYS_SOCIAL_001 | Chat System 聊天 | 已实现 | VERIFIED | CS_10800.., CS_12721/12762 | mock_server.py:18236 cmd==10800 |
| 82 | SYS_SOCIAL_002 | Friend System 好友 | 已实现 | VERIFIED | CS_13300,13303,13305,13321 | mock_server.py:105 import friend.handler 注册133 |
| 83 | SYS_SOCIAL_003 | Moments 朋友圈 | 已实现 | INFERENCE | UNKNOWN(随好友/社交) | systems_master: role_moments present |
| 84 | SYS_SOCIAL_004 | Guild 公会 | 已实现 | VERIFIED | CS_17500..17519, CS_19509.. | mock_server.py:11854 cmd==17519 |
| 85 | SYS_SOCIAL_005 | Marriage 结婚 | 已实现 | VERIFIED | CS_18300,18302,18313,18314,1 | mock_server.py:11077 cmd==18300 求婚 |
| 86 | SYS_SOCIAL_006 | Jiebai 结拜 | 已实现 | VERIFIED | CS_19505,19512,19514,19524,1 | mock_server.py:10947 cmd==19505 |
| 87 | SYS_SOCIAL_007 | Flower/Gift 送花 | 未实现 | VERIFIED | CS_13324/13326/13328(死协议) | mock_server 无 handler |
| 88 | SYS_SOCIAL_008 | Party 宴会/派对 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 89 | SYS_SOCIAL_009 | Guild Wars 公会战 | 部分实现 | VERIFIED | CS_17501, CS_195?, CS_130? | mock_server.py:17895 cmd==17501(按 type 分发 stub |
| 90 | SYS_SOCIAL_010 | Guild Tree/Animal/Skill 公会科技神兽 | 部分实现 | INFERENCE | UNKNOWN(随公会) | mock_server.py:3294 公会祈福 |
| 91 | SYS_COMM_001 | Rank 排行榜 | 部分实现 | VERIFIED | CS_16900..16903 | mock_server.py:10396 cmd==16900 |
| 92 | SYS_COMM_002 | Arena 竞技场 | 已实现 | VERIFIED | CS_11300..11310, CS_11301 | mock_server.py:17804 cmd==11300 |
| 93 | SYS_COMM_003 | Peakwar 巅峰战 | 已实现 | VERIFIED | CS_18803 | mock_server.py:15528 cmd==18803 |
| 94 | SYS_COMM_004 | Race 竞速/魂师大赛 | 已实现 | VERIFIED | CS_17306,17308,17310,17312 | mock_server.py:10545 cmd==17306 |
| 95 | SYS_COMM_005 | Cross-server 跨服 | 未实现 | STRONG_INFERENCE | CS_30100~31299(未实现) | mock_server 无跨服 |
| 96 | SYS_COMM_006 | Mining 采矿 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 97 | SYS_COMM_007 | Manor/Oasis 庄园 | 已实现 | VERIFIED | CS_10701,10702..10762 | mock_server.py:12975 cmd==10701 建筑研究升级 |
| 98 | SYS_COMM_008 | Attack City 攻城/领土战 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 99 | SYS_COMM_009 | Freight/Escort 押镖 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 100 | SYS_COMM_010 | Gold/JinYin Tower 金银塔 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 101 | SYS_GM_001 | GM Tools GM 工具 | 已实现 | CONFIRMED | CS_10922,10932,10921..10950 | mock_server.py:17054 cmd==10922 |
| 102 | SYS_BACK_001 | Server Backend/DB 后台数据库 | 已实现 | CONFIRMED | （内部） | persistence/db.py |
| 103 | SYS_BACK_002 | Cross-server backend 跨服后台 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无跨服 |
| 104 | SYS_HIDDEN_001 | Seal System 封印 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 105 | SYS_HIDDEN_002 | XiuLuo 修罗 | 未实现 | STRONG_INFERENCE | UNKNOWN | mock_server 无 handler |
| 106 | SYS_HIDDEN_003 | Chief 会长/百官 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 107 | SYS_HIDDEN_004 | Star Soul 星魂 | 部分实现 | INFERENCE | UNKNOWN(随符文) | systems_master: role_runes? partial |
| 108 | SYS_HIDDEN_005 | God Redemption 神位/神减免 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 109 | SYS_HIDDEN_006 | Dragon 神龙/巨龙 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 110 | SYS_HIDDEN_007 | Balloon 气球/活动 | 未实现 | VERIFIED | UNKNOWN | mock_server 无 handler |
| 111 | SYS_UNKNOWN_001 | Dan War 丹药战 | 未实现 | UNKNOWN | UNKNOWN | mock_server 无 handler |
| 112 | SYS_UNKNOWN_002 | YunYing Ops 运营活动 | 未实现 | UNKNOWN | UNKNOWN | mock_server 无 handler |
| 113 | SYS_UNKNOWN_003 | Insight 顿悟/洞察 | 部分实现 | INFERENCE | UNKNOWN | systems_master: roles.insight_status field onl |
| 114 | SYS_UNKNOWN_004 | Color/Head 染色 | 未实现 | UNKNOWN | UNKNOWN | mock_server 无 handler |
| 115 | SYS_EQUIP_005 | Equip Refine 装备洗练 | 未实现 | UNKNOWN | UNKNOWN | unimplemented SYS_EQUIP_005: named in PHASE0 c |
| 116 | SYS_EQUIP_006 | Gem/Socket 宝石 | 部分实现 | INFERENCE | UNKNOWN（镶嵌协议未取证） | mock_server 合成族; FINAL_REGRESSION: 宝石40物品+总属性表 |
| 117 | SYS_GROWTH_006 | Soul Bone 魂骨 | 未实现 | UNKNOWN | UNKNOWN | HANDOFF 文件地图: server/soulbone/ |
| 118 | SYS_GROWTH_007 | Augment/Amplify 增幅 | 未实现 | UNKNOWN | UNKNOWN | HANDOFF 文件地图: server/amplification/ |
| 119 | SYS_ECON_012 | Drop/Loot Table 掉落 | 部分实现 | INFERENCE | （随战斗/副本 CS） | FINAL_REGRESSION P16: drop_test |
| 120 | SYS_CORE_008 | Red Dot/Badge 红点 | 未实现 | UNKNOWN | UNKNOWN | unimplemented SYS_CORE_008: 无 config/module/pr |
| 121 | SYS_CORE_009 | UI State Sync UI状态 | 未实现 | UNKNOWN | UNKNOWN | unimplemented SYS_CORE_009: 无 config/module/pr |
| 122 | SYS_ROLE_007 | Combat Power 战力 | 部分实现 | CONFIRMED | SC_10304, SC_10306(服务器推送) | mock_server.py:17208 cmd==10304 战力推送 |
| 123 | SYS_FRIEND_006 | Partner Training 伙伴培养 | 部分实现 | UNKNOWN | CS_11216 | mock_server.py:16292 cmd==11216 |
| 124 | SYS_FRIEND_007 | Partner Equipment 伙伴装备 | 部分实现 | STRONG_INFERENCE | CS_11200~11205 | mock_server.py:18127 cmd==11200 |

## 逐系统详表（10 字段）

### SYS_CORE_001 Account Login 账号登录（A. 核心系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 登录界面(帐号/密码/选服)，denglu_ctrl.luac |
| **客户端本地逻辑** | 本地缓存帐号、拼登录包、心跳定时器 |
| **服务器权威状态** | 校验帐号、签发会话、返回角色列表；会话与会话锁在 server/session+account |
| **请求协议(CS)** | CS_1110 AccountLogin, CS_1199 心跳, CS_10001 FirstPack |
| **响应/推送协议(SC)** | SC_1110 角色列表, SC 登录回包 |
| **需要持久化的数据** | accounts/roles 表（persistence/db.py） |
| **依赖的其他服务** | 角色、会话、网络层 |
| **需要的GM功能** | /DSH_ADMIN 查号、踢线 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:9968 cmd==1110 登录；:9922 cmd==1199 心跳；:9963 cmd==10001 FirstPack；account/ 模块 |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_CORE_002 Role Creation 创建角色（A. 核心系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 建角界面(性别/名字/职业)，role_ctrl.luac |
| **客户端本地逻辑** | 本地校验名字合法性、预填职业外观 |
| **服务器权威状态** | 职业/性别/名字入库、分配 rid、初始化 role_attr/role_assets |
| **请求协议(CS)** | CS_10101 RoleCreate, CS_10102 RoleLogin, CS_10103 RoleReLogin |
| **响应/推送协议(SC)** | SC_10101 建角回包, SC_10300 角色初始化 |
| **需要持久化的数据** | roles 表(career/sex/name/scene/x/y) |
| **依赖的其他服务** | 角色属性、资产、场景 |
| **需要的GM功能** | GM 建角/改名 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15929 cmd==10101 建角；:15851 cmd in(10102,10103) 登录/重登 |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_CORE_003 Role Base/Init 角色基础（A. 核心系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 角色主界面(头顶信息/属性面板) |
| **客户端本地逻辑** | 本地缓存 RoleVo、按 10301/2/3 增量刷新 UI |
| **服务器权威状态** | 权威角色行、属性行、资产行；进游戏下发全量 |
| **请求协议(CS)** | SC_10300/10301/10302/10303（服务器主动推送为主） |
| **响应/推送协议(SC)** | SC_10300 初始化, SC_10301 属性, SC_10302 角色, SC_10303 资产 |
| **需要持久化的数据** | roles, role_attr, role_assets |
| **依赖的其他服务** | 属性、资产、持久化 |
| **需要的GM功能** | /DSH_ADMIN/setlevel setassets |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17260 cmd==10300；:17047 10301；:16109 10302；:16098 10303；role/storage+attribute/service |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_CORE_004 Role Login 进入游戏（A. 核心系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 选角后加载条、进主城 |
| **客户端本地逻辑** | 本地按 SC_1110 渲染角色列表、选角后触发进场景 |
| **服务器权威状态** | 校验 rid 属于本帐号、装载角色行、建立会话 |
| **请求协议(CS)** | CS_10102 RoleLogin |
| **响应/推送协议(SC)** | SC_1110 帐号角色列表 |
| **需要持久化的数据** | roles 表 |
| **依赖的其他服务** | 建角、场景、会话 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15851 cmd in(10102,10103)；与 SYS_CORE_001 同链 |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_CORE_005 Scene & Movement 场景移动（A. 核心系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 2D 场景、NPC/怪物头顶条、小地图 |
| **客户端本地逻辑** | 本地寻路(pathfind)、插值移动、点击寻路 |
| **服务器权威状态** | 权威 scene_id/x/y、NPC/怪物刷新、AOI 邻居广播 |
| **请求协议(CS)** | CS_10200 进场景, CS_10201, CS_10204 移动, CS_10205 |
| **响应/推送协议(SC)** | SC_10200 场景实体, AOI push_to_rid |
| **需要持久化的数据** | roles.scene_id/x/y；scene_npcs/scene_mons(8件套) |
| **依赖的其他服务** | 角色、战斗、AOI |
| **需要的GM功能** | GM 传送(set scene) |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15957 cmd==10200；:15973 10201；:15992 cmd in(10204,10205)；scene/service 8件套 |
| **剩余工作(与unimplemented清单一致)** | AOI 邻居帧逐字节对比需第二在线客户端（FINAL_REGRESSION 附） |

### SYS_CORE_006 Protocol/Network Layer 网络层（A. 核心系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 无独立界面（全局封包） |
| **客户端本地逻辑** | 本地封包/解包、粘包处理、重连(约11s) |
| **服务器权威状态** | TCP 9000 收包分发、HTTP 8080 /DSH_ADMIN 管理面；封包规格 protocol/fields |
| **请求协议(CS)** | all（承载全部 CS） |
| **响应/推送协议(SC)** | all（承载全部 SC） |
| **需要持久化的数据** | 无（传输层） |
| **依赖的其他服务** | 全部业务 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | protocol/frame+fields；mock_server.py:39 注释(DISPATCH_TABLE 现走旧 if 链)；minloop 145/145 基线 |
| **剩余工作(与unimplemented清单一致)** | 无 |

### SYS_CORE_007 Version/Resource Update 版本更新（A. 核心系统 · 部分实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 启动下载/更新界面(xiazai function25000) |
| **客户端本地逻辑** | 本地下载补丁、版本比对、资源校验 |
| **服务器权威状态** | 服务器仅回版本公告/热更列表，无资源分发 |
| **请求协议(CS)** | 20100 |
| **响应/推送协议(SC)** | SC 版本回包 |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 网络层 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17144 cmd==20100 有占位处理器；PHASE0 判 client-only（file_update_1411.luac） |
| **剩余工作(与unimplemented清单一致)** | 真实热更资源分发/强更策略未接 |

### SYS_ROLE_001 Role Attribute 角色属性（B. 角色系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 属性面板(攻防血/暴击等31项) |
| **客户端本地逻辑** | 本地按 10301 渲染、属性加点预览 |
| **服务器权威状态** | 权威 role_attr 行；加点 CS_10331/10333 后重算并广播 |
| **请求协议(CS)** | CS_10331, CS_10333 |
| **响应/推送协议(SC)** | SC_10301/10302/10303 属性推送 |
| **需要持久化的数据** | role_attr 表(_ATTR_ALIAS 别名映射) |
| **依赖的其他服务** | 资产、战力、持久化 |
| **需要的GM功能** | /DSH_ADMIN/setlevel |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17047 10301；:16234 cmd==10331；:16121 cmd==10333；attribute/service db_role_attr |
| **剩余工作(与unimplemented清单一致)** | MuMu 实机标定具体数值(⏳需取证) |

### SYS_ROLE_002 Career/Job 职业（B. 角色系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 建角职业选择/职业标识 |
| **客户端本地逻辑** | 本地按 career 切换技能/外观 |
| **服务器权威状态** | roles.career 列权威，不单独建表 |
| **请求协议(CS)** | （随 10101 建角携带） |
| **响应/推送协议(SC)** | SC_10302 携带 career |
| **需要持久化的数据** | roles.career 列 |
| **依赖的其他服务** | 建角、属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15929 cmd==10101 写入 career；config_role_career |
| **剩余工作(与unimplemented清单一致)** | 无（基础闭环） |

### SYS_ROLE_003 Title System 称号（B. 角色系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 称号列表/佩戴、头顶称号显示 |
| **客户端本地逻辑** | 本地按 config_title 渲染、佩戴预览 |
| **服务器权威状态** | 权威 role_title 拥有记录(175项)；佩戴后随角色信息广播 |
| **请求协议(CS)** | CS_14901（接 role_title） |
| **响应/推送协议(SC)** | SC 角色信息携带称号 |
| **需要持久化的数据** | role_title 表(config_title.Title 175项) |
| **依赖的其他服务** | 角色、持久化 |
| **需要的GM功能** | GM 发称号 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16243 cmd==14901；:7403 称号拥有记录(config_title 175项) |
| **剩余工作(与unimplemented清单一致)** | 称号获取/解锁任务链未完整 |

### SYS_ROLE_004 VIP System 贵族/VIP（B. 角色系统 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | VIP 面板、特权标识 |
| **客户端本地逻辑** | 本地按 vip_lev 渲染特权红点 |
| **服务器权威状态** | 仅 role_assets.vip_exp 与 role 字段；无独立 vip_* 表与特权结算 |
| **请求协议(CS)** | CS_16701（vip_lev 上传） |
| **响应/推送协议(SC)** | SC 资产/角色携带 vip_lev |
| **需要持久化的数据** | role_assets.vip_exp（无 vip_* 表） |
| **依赖的其他服务** | 资产、充值 |
| **需要的GM功能** | /DSH_ADMIN/setcharge |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10344 cmd==16701(vip_lev=1)；FINAL_REGRESSION 附二: setcharge 端点 |
| **剩余工作(与unimplemented清单一致)** | VIP 等级逻辑/每日礼包/特权结算缺失 |

### SYS_ROLE_005 Experience/Level 经验等级（B. 角色系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 经验条、等级礼包弹窗 |
| **客户端本地逻辑** | 本地按经验条渲染、升级特效 |
| **服务器权威状态** | 权威 level/exp；经验来源(战斗/任务/挂机)经 RewardService；等级礼包幂等领取 |
| **请求协议(CS)** | CS_14600, CS_14601 等级礼包 |
| **响应/推送协议(SC)** | SC_10301 属性(level/exp) |
| **需要持久化的数据** | roles.level/exp；levgift_got 表 |
| **依赖的其他服务** | 属性、资产、奖励 |
| **需要的GM功能** | /DSH_ADMIN/setlevel |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17732 cmd in(14600,14601) 等级礼包；attribute/service |
| **剩余工作(与unimplemented清单一致)** | 经验曲线 MuMu 标定(⏳) |

### SYS_ROLE_006 Avatar/Head & Chat Bubble 头像框气泡（B. 角色系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 头像框、聊天气泡选择界面 |
| **客户端本地逻辑** | 本地按 config_head_surface/chat_bubble 渲染 |
| **服务器权威状态** | 仅 role 头像/气泡字段；无专用表 |
| **请求协议(CS)** | UNKNOWN（随角色信息携带） |
| **响应/推送协议(SC)** | SC_10302 携带 |
| **需要持久化的数据** | roles 头像/气泡列（无专用表） |
| **依赖的其他服务** | 角色、聊天 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: roles 字段 only；mock_server 无独立 handler（无专属命令） |
| **剩余工作(与unimplemented清单一致)** | 头像框/气泡获取与佩戴协议未接 |

### SYS_GROWTH_001 Skill System 技能（C. 成长系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 技能面板、拖快捷栏、战斗技能播放 |
| **客户端本地逻辑** | 本地技能 CD/冷却、特效播放、连招 |
| **服务器权威状态** | 权威已学技能；学习/升级扣金币并广播；战斗中 CS_10401..10406 |
| **请求协议(CS)** | CS_10401..10406, CS_20012 技能播放 |
| **响应/推送协议(SC)** | SC_10302 技能列表, SC_20012/20013 战斗技能 |
| **需要持久化的数据** | （随 role_skill，无独立表名） |
| **依赖的其他服务** | 属性、资产、战斗 |
| **需要的GM功能** | GM 学技能 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18262 cmd in(10401..10404)；:13167 cmd==10406；skill/service 学习/升级(P8 partner_feed/skill_learn) |
| **剩余工作(与unimplemented清单一致)** | 技能消耗真值已 CONFIRMED(config_skill)；战斗数值 MuMu 标定 |

### SYS_GROWTH_002 Talent/天赋（C. 成长系统 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 天赋树面板 |
| **客户端本地逻辑** | 本地天赋点预览、树状渲染 |
| **服务器权威状态** | 天赋/修炼面板读取；仅配置，无独立天赋成长结算 |
| **请求协议(CS)** | CS_10601/10610/10651（面板） |
| **响应/推送协议(SC)** | SC 天赋面板回包 |
| **需要持久化的数据** | （无独立表） |
| **依赖的其他服务** | 技能、属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:13008 cmd in(10601,10610,10622,10651) 天赋/修炼面板 |
| **剩余工作(与unimplemented清单一致)** | 天赋加点/解锁逻辑缺失 |

### SYS_GROWTH_003 Practice/修炼 Buff（C. 成长系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 修炼面板(进度条 35/50) |
| **客户端本地逻辑** | 本地渲染修炼经验条 |
| **服务器权威状态** | 权威 role_buffs/practice_exp；10621 修炼帧动态读 practice_exp=35 |
| **请求协议(CS)** | CS_10621 修炼帧 |
| **响应/推送协议(SC)** | SC_10302/10303/10304 含 practice_exp |
| **需要持久化的数据** | role_buffs 表(practice_exp) |
| **依赖的其他服务** | 属性、Buff |
| **需要的GM功能** | GM 设置修炼 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16127 cmd==10621；FINAL_REGRESSION §三: practice_exp=35 CONFIRMED(50=本级满值) |
| **剩余工作(与unimplemented清单一致)** | 消耗/拥有 EXP 客户端渲染空白(客户端侧,勿再加帧) |

### SYS_GROWTH_004 Buff System Buff（C. 成长系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | Buff 图标栏、倒计时 |
| **客户端本地逻辑** | 本地 Buff 倒计时/图标刷新 |
| **服务器权威状态** | 权威 role_buffs；战斗 SC_20012/20013 透传 Buff |
| **请求协议(CS)** | （随战斗 CS_20012/20013） |
| **响应/推送协议(SC)** | SC_20012/20013 Buff 透传 |
| **需要持久化的数据** | role_buffs 表 |
| **依赖的其他服务** | 战斗、属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: role_buffs present；SC_20012/20013 透传链 |
| **剩余工作(与unimplemented清单一致)** | Buff 数值/叠加规则 MuMu 标定 |

### SYS_GROWTH_005 Morale 士气（C. 成长系统 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 士气显示(战斗/伙伴相关) |
| **客户端本地逻辑** | 本地渲染士气 |
| **服务器权威状态** | 无；config_morale/hero_morale 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 战斗、伙伴 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented_systems SYS_GROWTH_005(config_morale+hero_morale only) |
| **剩余工作(与unimplemented清单一致)** | 需建权威士气状态+协议 |

### SYS_BATTLE_001 Turn-based Battle 回合战斗（D. 战斗系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 战斗场景、回合回合结算面板 |
| **客户端本地逻辑** | 本地播放战斗动画、技能演出 |
| **服务器权威状态** | 权威战斗实例(battle.py)；怪物 HP/ATK 由服务端公式(配置无显式值)；Timer kick |
| **请求协议(CS)** | CS_20002 开战, CS_20014 |
| **响应/推送协议(SC)** | SC_20010/20012/20013/20020 |
| **需要持久化的数据** | （战斗临时态，结算写奖励/经验） |
| **依赖的其他服务** | 技能、Buff、掉落、经验 |
| **需要的GM功能** | /DSH_ADMIN/battle_replay?mon_id=20001 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17384 cmd==20002；:19274 cmd==20014；/DSH_ADMIN/battle_replay 确定性重放(两次hex一致) |
| **剩余工作(与unimplemented清单一致)** | 怪物 HP/ATK 真值 UNKNOWN(需真服/MuMu 战斗抓包)；20002 最终裁定保留旧链 |

### SYS_BATTLE_002 Auto-battle/AFK 挂机（D. 战斗系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 挂机界面、收益预览、巡逻按钮 |
| **客户端本地逻辑** | 本地自动战斗循环、挂机 UI |
| **服务器权威状态** | 权威 guaji_state；挂机累积+幂等领取(afk_claim)；8 地图区域 |
| **请求协议(CS)** | CS_15400 族(挂机) |
| **响应/推送协议(SC)** | SC_154xx 挂机收益推送 |
| **需要持久化的数据** | guaji_state 表；config_guaji 8区域 |
| **依赖的其他服务** | 战斗、资产、任务 |
| **需要的GM功能** | GM 触发挂机 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18736 cmd==15400；:18678 15402；:18698 15403；:18668 15405；FINAL_REGRESSION P10 afk_claim |
| **剩余工作(与unimplemented清单一致)** | 巡逻按钮激活条件待实机观察；收益系数 INFERENCE |

### SYS_BATTLE_003 Battle Replay/Video 战报回放（D. 战斗系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 战报列表/回放播放器(battlevideo_ctrl.luac) |
| **客户端本地逻辑** | 本地回放动画播放 |
| **服务器权威状态** | 无客户端战报存储/回放 SC；仅管理端 battle_replay 重放 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 战斗 |
| **需要的GM功能** | /DSH_ADMIN/battle_replay（调试用） |
| **当前已实现部分(源码/测试证据)** | mock_server 无战报 CS handler；unimplemented SYS_BATTLE_003(battlevideo modules; no DB) |
| **剩余工作(与unimplemented清单一致)** | 需战报录制/存储/回放协议 |

### SYS_BATTLE_004 God War Battle 神魔战（D. 战斗系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 神魔战 UI(godwar function52) |
| **客户端本地逻辑** | 本地战斗界面 |
| **服务器权威状态** | 无；client UI only |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 战斗、跨服 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_BATTLE_004(config_sm_war/godwar_battle_*) |
| **剩余工作(与unimplemented清单一致)** | 需建权威玩法状态 |

### SYS_BATTLE_005 Boss System BOSS（D. 战斗系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | BOSS 刷新提示、伤害榜 |
| **客户端本地逻辑** | 本地 BOSS 血条/伤害统计 |
| **服务器权威状态** | 权威 role_boss_kill 击杀记录；BOSS 战斗走 20002 |
| **请求协议(CS)** | CS_20002（击杀 BOSS） |
| **响应/推送协议(SC)** | SC 战斗结算/BOSS 推送 |
| **需要持久化的数据** | role_boss_kill 表；config_boss/demon |
| **依赖的其他服务** | 战斗、掉落、排名 |
| **需要的GM功能** | GM 刷新 BOSS |
| **当前已实现部分(源码/测试证据)** | systems_master: role_boss_kill present；mock_server 20002 战斗链；config_boss/demon |
| **剩余工作(与unimplemented清单一致)** | BOSS 刷新时间表/伤害榜未完整 |

### SYS_EQUIP_001 Equipment System 装备（E. 装备系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 背包/穿戴界面、装备槽、属性对比 |
| **客户端本地逻辑** | 本地穿戴预览、属性差对比、拖拽穿戴 |
| **服务器权威状态** | 权威 equip_items；穿戴/脱下(10574/10576)改槽位并重算属性+战力；伙伴装备走 11200 族 |
| **请求协议(CS)** | CS_10500..10593, CS_11200~11205(伙伴装备) |
| **响应/推送协议(SC)** | SC_10502 背包同步, SC_10301 属性, 战力推送 |
| **需要持久化的数据** | equip_items, bag_items |
| **依赖的其他服务** | 背包、属性、战力、资产 |
| **需要的GM功能** | GM 发装备 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:13370 cmd==10593；:13383 cmd in(10573,10574,10575,10576,10578) 穿戴/脱下；:13404 10574穿戴；:13407 10576脱下；equipment/service |
| **剩余工作(与unimplemented清单一致)** | 外观属性贡献已闭环；MuMu 标定具体数值 |

### SYS_EQUIP_002 Smith/Forge/Fuse 锻造合成（E. 装备系统 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 合成/融合界面 |
| **客户端本地逻辑** | 本地材料预览、成功率展示 |
| **服务器权威状态** | 部分；强化族 10523/10527/10528；合成 config_item_fuse(192条) |
| **请求协议(CS)** | CS_10523/10527/10528 |
| **响应/推送协议(SC)** | SC_10502 背包, SC_10301 属性 |
| **需要持久化的数据** | bag_items（材料消耗） |
| **依赖的其他服务** | 背包、资产、装备 |
| **需要的GM功能** | GM 发材料 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:13236 cmd==10523；:16986 cmd==10527；:17631 cmd==10528；config_item_fuse 192条(CONFIRMED) |
| **剩余工作(与unimplemented清单一致)** | 升阶/融合完整规则未闭环 |

### SYS_EQUIP_003 Rune System 符文（E. 装备系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 符文面板、镶嵌槽、符文等级 |
| **客户端本地逻辑** | 本地符文搭配预览 |
| **服务器权威状态** | 权威 role_runes；21406 升级；124 符文(1..50级) |
| **请求协议(CS)** | CS_11240, CS_21400..21414 |
| **响应/推送协议(SC)** | SC 符文面板, SC_10301 属性 |
| **需要持久化的数据** | role_runes 表(config_rune_data RuneBase 124项) |
| **依赖的其他服务** | 装备、属性、背包 |
| **需要的GM功能** | GM 发符文 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:13249 cmd==11240；:15254 cmd==21406 升级；:8667/:8796 config_rune(124项) |
| **剩余工作(与unimplemented清单一致)** | 符文套装效果未完整 |

### SYS_EQUIP_004 Equip StarUp/强化 装备升星（E. 装备系统 · 部分实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 强化界面、成功率、属性增长 |
| **客户端本地逻辑** | 本地强化预览、消耗展示 |
| **服务器权威状态** | 部分；10527/10528 强化族；config_intensify(L1=100%/L3=75%) |
| **请求协议(CS)** | CS_10527/10528 |
| **响应/推送协议(SC)** | SC_10301 属性, SC_10502 |
| **需要持久化的数据** | equip_items(强化等级) |
| **依赖的其他服务** | 装备、资产、背包 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16986 10527；:17631 10528；FINAL_REGRESSION: 强化成功率/消耗 CONFIRMED |
| **剩余工作(与unimplemented清单一致)** | 强化保护/倍率规则未完整 |

### SYS_FRIEND_001 Partner/Hero System 伙伴（F. 伙伴系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 伙伴列表/详情/上阵/战力 |
| **客户端本地逻辑** | 本地伙伴立绘、属性面板、上阵位预览 |
| **服务器权威状态** | 权威 role_heros；11215 伙伴面板、11216 伙伴状态；培养 partner_feed(P8) |
| **请求协议(CS)** | CS_11215, CS_11216 |
| **响应/推送协议(SC)** | SC 伙伴面板, SC_10301 属性 |
| **需要持久化的数据** | role_heros 表 |
| **依赖的其他服务** | 阵型、属性、战力、背包 |
| **需要的GM功能** | GM 发伙伴 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18173 cmd==11215 伙伴面板；:16292 cmd==11216 partner_bid/state；P8 partner_feed |
| **剩余工作(与unimplemented清单一致)** | 伙伴喂养消耗 UNKNOWN(配置无显式值) |

### SYS_FRIEND_002 Formation 阵法（F. 伙伴系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 阵型布阵界面、伙伴上阵位 |
| **客户端本地逻辑** | 本地拖拽伙伴上阵、阵型预览 |
| **服务器权威状态** | 权威 role_form；11237 formation_type |
| **请求协议(CS)** | CS_11237(formation_type) |
| **响应/推送协议(SC)** | SC 阵型回包 |
| **需要持久化的数据** | role_form 表 |
| **依赖的其他服务** | 伙伴、属性、战斗 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | phase1_cs_inventory: CS_11237 formation_type=1；systems_master role_form present |
| **剩余工作(与unimplemented清单一致)** | 阵型加成系数 MuMu 标定 |

### SYS_FRIEND_003 Partner Atlas 伙伴图鉴（F. 伙伴系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 图鉴收集界面(partner_atlas modules) |
| **客户端本地逻辑** | 本地图鉴点亮/收集进度渲染 |
| **服务器权威状态** | 无；仅 client UI |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 伙伴 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_FRIEND_003(partner_atlas modules; partial) |
| **剩余工作(与unimplemented清单一致)** | 需图鉴收集状态协议 |

### SYS_FRIEND_004 Partner Recruit 伙伴招募/抽卡（F. 伙伴系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 招募/抽卡弹窗、保底 |
| **客户端本地逻辑** | 本地抽卡动画、概率预览 |
| **服务器权威状态** | 部分；无专用招募命令，config_lucky_box |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | （无专属表） |
| **依赖的其他服务** | 资产、伙伴 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无独立招募 handler；config_lucky_box_data；systems_master partial |
| **剩余工作(与unimplemented清单一致)** | 抽卡概率/保底/招募协议未接 |

### SYS_FRIEND_005 Partner Fetter 伙伴羁绊（F. 伙伴系统 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 羁绊界面、羁绊激活 |
| **客户端本地逻辑** | 本地羁绊条件预览 |
| **服务器权威状态** | 无；config_partner_fetter only |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 伙伴 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_FRIEND_005 |
| **剩余工作(与unimplemented清单一致)** | 需羁绊权威状态 |

### SYS_APPEAR_001 Wing System 翅膀（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 翅膀面板、穿戴/升星、外观展示 |
| **客户端本地逻辑** | 本地翅膀外观切换、升阶预览 |
| **服务器权威状态** | 权威 role_wing；11600 翅膀面板数据源；wing_up(P9) |
| **请求协议(CS)** | CS_11600..11607 |
| **响应/推送协议(SC)** | SC_116xx 翅膀面板, SC_10301 属性 |
| **需要持久化的数据** | role_wing 表(config_wing_data WingUpstar) |
| **依赖的其他服务** | 属性、战力、资产 |
| **需要的GM功能** | GM 发翅膀 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:14887 cmd==11600；:7666 role_wing 数据源；:101 import growth.handler 注册11600；P9 wing_up |
| **剩余工作(与unimplemented清单一致)** | MuMu 标定数值 |

### SYS_APPEAR_002 Mount 坐骑（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 坐骑面板、骑乘、坐骑技能 |
| **客户端本地逻辑** | 本地骑乘状态切换、外观预览 |
| **服务器权威状态** | 权威 role_ride；15501 坐骑态、10551 族 |
| **请求协议(CS)** | CS_10551.., CS_15501 |
| **响应/推送协议(SC)** | SC_15501 坐骑态 |
| **需要持久化的数据** | role_ride 表(config_ride RideAllSkill) |
| **依赖的其他服务** | 属性、战力、战斗 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15297 cmd==15501；:17621 cmd in(10551)；:8525 role_ride 数据源 |
| **剩余工作(与unimplemented清单一致)** | 坐骑技能效果未完整 |

### SYS_APPEAR_003 Beast 灵兽（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 灵兽面板、跟随、 speak |
| **客户端本地逻辑** | 本地灵兽跟随/对话渲染 |
| **服务器权威状态** | 权威 role_lingshou；15801 魂兽状态 |
| **请求协议(CS)** | CS_15801 |
| **响应/推送协议(SC)** | SC_15801 魂兽状态 |
| **需要持久化的数据** | role_lingshou 表(config_lingshou) |
| **依赖的其他服务** | 属性、战力 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:14807 cmd==15801；:7476 role_lingshou 数据源 |
| **剩余工作(与unimplemented清单一致)** | 灵兽培养/技能未完整 |

### SYS_APPEAR_004 Soul 元神（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 元神面板、元神形象 |
| **客户端本地逻辑** | 本地元神形象切换 |
| **服务器权威状态** | 权威 role_yuanshen；19406 元神状态 |
| **请求协议(CS)** | CS_19406 |
| **响应/推送协议(SC)** | SC_194xx 元神状态 |
| **需要持久化的数据** | role_yuanshen 表 |
| **依赖的其他服务** | 属性、战力 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:14840 cmd==19406；:7510 role_yuanshen 数据源 |
| **剩余工作(与unimplemented清单一致)** | 元神进阶未完整 |

### SYS_APPEAR_005 Divine Artifact 神器（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 神器面板、激活/使用中、升阶 |
| **客户端本地逻辑** | 本地神器切换、升阶预览 |
| **服务器权威状态** | 权威 role_shenqi；15700 神器持有；使用中唯一(status=1) |
| **请求协议(CS)** | CS_15700..15704 |
| **响应/推送协议(SC)** | SC_157xx 神器列表 |
| **需要持久化的数据** | role_shenqi 表(id/lev/star/status/mark) |
| **依赖的其他服务** | 属性、战力、资产 |
| **需要的GM功能** | GM 发神器 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:14850 cmd==15700；:7546/:7556 role_shenqi 数据源；P9 shenqi_up |
| **剩余工作(与unimplemented清单一致)** | MuMu 标定数值 |

### SYS_APPEAR_006 Fate/Natal 命格（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 命格面板、命格列表、装备命格 |
| **客户端本地逻辑** | 本地命格搭配预览 |
| **服务器权威状态** | 权威 role_mingge；19400.mingge_list；19404 删除命格 |
| **请求协议(CS)** | CS_19400..19414 |
| **响应/推送协议(SC)** | SC_194xx 命格面板 |
| **需要持久化的数据** | role_mingge 表(config_mingge MinggeOther.stage_init) |
| **依赖的其他服务** | 属性、战力 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15232 cmd==19400；:7588 role_mingge 数据源；P9 mingge_activate |
| **剩余工作(与unimplemented清单一致)** | 命格套装效果未完整 |

### SYS_APPEAR_007 Magic Weapon 法宝（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 法宝面板、法宝形象 |
| **客户端本地逻辑** | 本地法宝切换 |
| **服务器权威状态** | 权威 role_fabao；11200/11205 族接入 |
| **请求协议(CS)** | CS_11200~11205 |
| **响应/推送协议(SC)** | SC 法宝面板 |
| **需要持久化的数据** | role_fabao 表 |
| **依赖的其他服务** | 属性、战力 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18127 cmd==11200；:12105 cmd in(11205..) |
| **剩余工作(与unimplemented清单一致)** | 法宝技能效果未完整 |

### SYS_APPEAR_008 Vehicle/Chair 座驾（G. 外观系统 · 已实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 座驾/椅子面板、乘坐 |
| **客户端本地逻辑** | 本地座驾切换 |
| **服务器权威状态** | 权威 role_chair 表；无独立 CS 命令(并入外观族) |
| **请求协议(CS)** | UNKNOWN（随外观族） |
| **响应/推送协议(SC)** | SC 外观回包 |
| **需要持久化的数据** | role_chair 表 |
| **依赖的其他服务** | 属性、战力 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: role_chair present；mock_server 无专属命令(并入 112xx/外观族) |
| **剩余工作(与unimplemented清单一致)** | 座驾独立协议未取证 |

### SYS_APPEAR_009 Fashion/Skin 时装（G. 外观系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 时装衣柜、激活/穿戴/脱下/升星 |
| **客户端本地逻辑** | 本地时装试穿、外观预览 |
| **服务器权威状态** | 权威 role_fashion；10573 激活/10574 穿戴/10576 脱下/10578；属性贡献已接 |
| **请求协议(CS)** | CS_10573,10574,10575,10576,10578 |
| **响应/推送协议(SC)** | SC_10502, SC_10301 属性 |
| **需要持久化的数据** | role_fashion 表(config_fashion) |
| **依赖的其他服务** | 背包、属性、战力、资产 |
| **需要的GM功能** | GM 发时装 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:13383 cmd in(10573..10578)；:13392 时装激活；:13404 穿戴；:13407 脱下 |
| **剩余工作(与unimplemented清单一致)** | MuMu 标定数值 |

### SYS_APPEAR_010 Halo 光环（G. 外观系统 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 光环面板、光环装备槽 |
| **客户端本地逻辑** | 本地光环切换预览 |
| **服务器权威状态** | 权威 role_halo/role_halo_equip；19100 info/19103 穿戴；升级未实现 |
| **请求协议(CS)** | CS_19100,19103,19104 |
| **响应/推送协议(SC)** | SC_191xx 光环面板 |
| **需要持久化的数据** | role_halo, role_halo_equip 表 |
| **依赖的其他服务** | 属性、战力、背包 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:13427 cmd==19100；:13446 cmd==19103 光环穿戴；:13458 cmd==19104 |
| **剩余工作(与unimplemented清单一致)** | 光环升级未实现 |

### SYS_ECON_001 Assets/Currency 货币资产（H. 资源经济 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 顶栏货币显示(金币/元宝/绑元等) |
| **客户端本地逻辑** | 本地按 10303 刷新货币显示 |
| **服务器权威状态** | 权威 role_assets；一切资产变动走 CurrencyService(db_add/set_assets) |
| **请求协议(CS)** | SC_10303 资产推送(服务器主动) |
| **响应/推送协议(SC)** | SC_10303, SC_10306 |
| **需要持久化的数据** | role_assets 表 |
| **依赖的其他服务** | 全部消费/产出系统 |
| **需要的GM功能** | /DSH_ADMIN/setassets |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16098 cmd==10303；currency/service db_get/add/set_assets |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_ECON_002 Inventory/Bag 背包（H. 资源经济 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 背包格子、道具图标/数量、使用/出售 |
| **客户端本地逻辑** | 本地拖拽整理、道具使用预览、筛选 |
| **服务器权威状态** | 权威 bag_items/bag_volume；10502 同步/10505 双击使用/10504 出售；D2 不可渲染 bid 过滤 |
| **请求协议(CS)** | CS_10500..10593 |
| **响应/推送协议(SC)** | SC_10502 背包同步 |
| **需要持久化的数据** | bag_items, bag_volume 表 |
| **依赖的其他服务** | 资产、装备、道具 |
| **需要的GM功能** | GM 发道具 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:19229 cmd==10502 背包同步；:17647 cmd==10505 双击使用；:15054 cmd==10504 出售；P16 不可渲染bid过滤 |
| **剩余工作(与unimplemented清单一致)** | D2 渲染根因部分 INFERENCE |

### SYS_ECON_003 Mall/Shop 商城（H. 资源经济 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 商城页签、商品列表、购买/限购 |
| **客户端本地逻辑** | 本地商品页签、购买确认 |
| **服务器权威状态** | 权威 mall_bought；12801 族购买扣币+限购；13401 族 |
| **请求协议(CS)** | CS_12801..12856, CS_13401..13416 |
| **响应/推送协议(SC)** | SC 商城回包, SC_10502, SC_10303 |
| **需要持久化的数据** | mall_bought 表(config_mall/shop) |
| **依赖的其他服务** | 资产、背包、持久化 |
| **需要的GM功能** | GM 发商品 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16770 cmd in(12801..)；:16797 12801；:10215 cmd==13403；P11 mall_buy |
| **剩余工作(与unimplemented清单一致)** | MuMu 标定商品价格 |

### SYS_ECON_004 Storage/Warehouse 仓库（H. 资源经济 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 仓库界面、存取、背包扩展 |
| **客户端本地逻辑** | 本地存取拖拽、容量显示 |
| **服务器权威状态** | 权威 store_items；10714 仓库 |
| **请求协议(CS)** | CS_10714, CS_10621 |
| **响应/推送协议(SC)** | SC 仓库回包, SC_10502 |
| **需要持久化的数据** | store_items 表(config_storage_data) |
| **依赖的其他服务** | 背包、资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17711 cmd==10714；:16127 cmd==10621 |
| **剩余工作(与unimplemented清单一致)** | 无（基础闭环） |

### SYS_ECON_005 Trade Market 市场/交易（H. 资源经济 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 市场寄售/购买界面 |
| **客户端本地逻辑** | 本地商品列表/购买预览 |
| **服务器权威状态** | 权威 role_market/role_market_goods；18909 族 |
| **请求协议(CS)** | CS_18909.. |
| **响应/推送协议(SC)** | SC 市场回包 |
| **需要持久化的数据** | role_market, role_market_goods 表 |
| **依赖的其他服务** | 背包、资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10180 cmd==18909 |
| **剩余工作(与unimplemented清单一致)** | 寄售上架/税费规则未完整 |

### SYS_ECON_006 Black Market 黑市（H. 资源经济 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 黑市刷新/购买界面 |
| **客户端本地逻辑** | 本地黑市商品预览 |
| **服务器权威状态** | 仅 18909 通用响应；无独立 DB/刷新 |
| **请求协议(CS)** | CS_18909(通用) |
| **响应/推送协议(SC)** | SC 通用回包 |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 资产、背包 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10180 cmd==18909(通用 stub)；systems_master partial(no DB) |
| **剩余工作(与unimplemented清单一致)** | 黑市独立刷新/限购逻辑缺失 |

### SYS_ECON_007 Exchange 兑换（H. 资源经济 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 兑换商店界面 |
| **客户端本地逻辑** | 本地兑换预览 |
| **服务器权威状态** | 部分；13403 兑换 |
| **请求协议(CS)** | CS_13403, duihuan(20)/yunyingduihuan(21) |
| **响应/推送协议(SC)** | SC_10502, SC_10303 |
| **需要持久化的数据** | （mall_exchange） |
| **依赖的其他服务** | 资产、背包 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10215 cmd==13403 |
| **剩余工作(与unimplemented清单一致)** | 完整兑换表/币别未闭环 |

### SYS_ECON_008 Auction 拍卖（H. 资源经济 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 拍卖行列表/一口价/竞价 |
| **客户端本地逻辑** | 本地拍卖列表渲染、出价确认 |
| **服务器权威状态** | 权威 list+一口价(18020/18021/18022)；竞价未实现 |
| **请求协议(CS)** | CS_18020,18021,18022 |
| **响应/推送协议(SC)** | SC 拍卖回包(buy_list/notice_list/item_list) |
| **需要持久化的数据** | role_assets, bag_items |
| **依赖的其他服务** | 背包、资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:12140 cmd==18020 拍卖行；:12144 18021；:12162 18022 一口价 |
| **剩余工作(与unimplemented清单一致)** | 竞价/一口价邮件通知未实现 |

### SYS_ECON_009 Mail 邮件（H. 资源经济 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 邮件列表、附件领取、写信 |
| **客户端本地逻辑** | 本地未读红点、附件领取预览 |
| **服务器权威状态** | 权威 role_mail；10800；mail_claim 幂等(reward_log transaction_id) |
| **请求协议(CS)** | CS_10800 |
| **响应/推送协议(SC)** | SC 邮件列表, SC_10502, SC_10303 |
| **需要持久化的数据** | role_mail 表(rid/from/subject/content/附件) |
| **依赖的其他服务** | 资产、背包、奖励 |
| **需要的GM功能** | GM 发邮件 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18236 cmd==10800；:2708 role_mail 表；P12 mail_claim 幂等 |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_ECON_010 Recharge/Payment 充值（H. 资源经济 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 充值/首充/礼包界面 |
| **客户端本地逻辑** | 本地充值页、首充标识 |
| **服务器权威状态** | 部分；12831/13401；无独立充值表(走 mall_bought/assets) |
| **请求协议(CS)** | CS_12831, CS_13401.. |
| **响应/推送协议(SC)** | SC_10303 资产 |
| **需要持久化的数据** | 无独立充值表(mall_bought/assets) |
| **依赖的其他服务** | 资产、商城 |
| **需要的GM功能** | /DSH_ADMIN/setcharge |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16594 cmd==12831；:10204 cmd in(13401)；FINAL_REGRESSION: setcharge 端点 |
| **剩余工作(与unimplemented清单一致)** | 真实支付回调/累计充值档位未接 |

### SYS_ECON_011 Gift Item 礼包/宝箱（H. 资源经济 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 礼包/宝箱开启界面 |
| **客户端本地逻辑** | 本地开箱动画、奖励展示 |
| **服务器权威状态** | 权威礼包/掉落经 gift/item 路径；10505 使用；P16 掉落接线 |
| **请求协议(CS)** | CS_10505(使用) |
| **响应/推送协议(SC)** | SC_10502, SC_10303 |
| **需要持久化的数据** | bag_items(礼包) |
| **依赖的其他服务** | 背包、资产、掉落 |
| **需要的GM功能** | GM 发礼包 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17647 cmd==10505；P16 drop_test/build_bag_items |
| **剩余工作(与unimplemented清单一致)** | 掉落概率 pp/1000 基准 INFERENCE |

### SYS_QUEST_001 Mission/Quest 任务（I. 任务系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 任务列表/追踪/NPC 对话/领奖 |
| **客户端本地逻辑** | 本地任务追踪、自动寻路到 NPC、红点 |
| **服务器权威状态** | 权威 missions；12400 列表/12401/12408 NPC；task/service build_12400；线性剧情链唯一进行中 |
| **请求协议(CS)** | CS_12400..12421, CS_12407/08/09 |
| **响应/推送协议(SC)** | SC_124xx 任务列表, SC_10502, SC_10303 |
| **需要持久化的数据** | missions 表(config_mission/chapter) |
| **依赖的其他服务** | NPC、奖励、资产、持久化 |
| **需要的GM功能** | GM 完成任务 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16084 cmd==12400；:16091 12401；:16075 cmd==12408；task/service |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_QUEST_002 Daily/Active 日常活跃（I. 任务系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 日常任务/活跃度界面 |
| **客户端本地逻辑** | 本地活跃进度渲染、红点 |
| **服务器权威状态** | 权威 daily_progress/daily_lingqu；随 10301 推送 |
| **请求协议(CS)** | CS_10301(日常数据) |
| **响应/推送协议(SC)** | SC_10301 日常/活跃 |
| **需要持久化的数据** | daily_progress, daily_lingqu 表 |
| **依赖的其他服务** | 任务、奖励、签到 |
| **需要的GM功能** | GM 重置日常 |
| **当前已实现部分(源码/测试证据)** | systems_master: daily_progress/daily_lingqu present；mock_server 10301 推送链(:17047) |
| **剩余工作(与unimplemented清单一致)** | 活跃奖励档位未完整 |

### SYS_QUEST_003 Achievement 成就（I. 任务系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 成就列表/进度/领奖 |
| **客户端本地逻辑** | 本地成就进度条、红点 |
| **服务器权威状态** | 权威 chengjiu_progress；16400；server/achievement/service.py 342 条 |
| **请求协议(CS)** | CS_16400 |
| **响应/推送协议(SC)** | SC_164xx 成就列表 |
| **需要持久化的数据** | chengjiu_progress 表(config_chengjiu 342条) |
| **依赖的其他服务** | 任务、奖励、资产 |
| **需要的GM功能** | GM 发成就 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18629 cmd==16400；server/achievement/service.py 342条(CONFIRMED) |
| **剩余工作(与unimplemented清单一致)** | chengjiu_has.state 子字段偏移 UNKNOWN(需实机 hook) |

### SYS_QUEST_004 Growth Target 成长目标（I. 任务系统 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 开服成长计划/目标进度界面 |
| **客户端本地逻辑** | 本地目标进度渲染 |
| **服务器权威状态** | 权威 30500/30501/30502；server/growth_target/ 模块(PHASE2.11) |
| **请求协议(CS)** | CS_30500,30501,30502 |
| **响应/推送协议(SC)** | SC_305xx 目标回包 |
| **需要持久化的数据** | role_growth_target(schema) |
| **依赖的其他服务** | 任务、奖励、资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:11751 cmd==30500；:11713 30501；:11716 30502；:103 import growth_target.handler |
| **剩余工作(与unimplemented清单一致)** | PHASE0 清单标 partial，实际 P2.11 已建模块(以源码为准) |

### SYS_QUEST_005 Guide System 新手引导（I. 任务系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 引导箭头/剧情弹窗(guide/action_ctrl) |
| **客户端本地逻辑** | 本地引导步骤机、剧情播放 |
| **服务器权威状态** | 无；client-side 引导 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 全部 UI |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_QUEST_005(config_guide/action_ctrl) |
| **剩余工作(与unimplemented清单一致)** | 引导服务器态/进度同步未接 |

### SYS_MAP_001 World Map 世界地图（J. 地图系统 · 已实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 世界地图/区域传送界面 |
| **客户端本地逻辑** | 本地地图渲染、点选传送预览 |
| **服务器权威状态** | 无独立 CS；随场景 10200 进图；config_map/world_map |
| **请求协议(CS)** | （随 CS_10200） |
| **响应/推送协议(SC)** | SC_10200 场景 |
| **需要持久化的数据** | roles.scene_id |
| **依赖的其他服务** | 场景、任务 |
| **需要的GM功能** | GM 传送 |
| **当前已实现部分(源码/测试证据)** | systems_master: implemented(basic)；config_world_map/map；mock_server 并入场景链 |
| **剩余工作(与unimplemented清单一致)** | 区域解锁条件未完整 |

### SYS_MAP_002 Team Group 组队（J. 地图系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 队伍界面/邀请/组队大厅 |
| **客户端本地逻辑** | 本地队伍列表、邀请确认 UI |
| **服务器权威状态** | 权威 role_team/role_team_invite；13200 队伍信息/13201 建队/13202 邀请/13204 应答/13210 退出/13226 解散/13218 大厅 |
| **请求协议(CS)** | CS_13200,13201,13202,13204,13210,13218,13226 |
| **响应/推送协议(SC)** | SC_132xx 队伍信息/邀请推送 |
| **需要持久化的数据** | role_team, role_team_invite 表 |
| **依赖的其他服务** | 场景、社交、战斗 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10778 cmd in(13200..)；:10802 13201 建队；:10846 13202 邀请；:10875 13204 应答；:10807 13210 退出；:10811 13226 解散 |
| **剩余工作(与unimplemented清单一致)** | 多人副本组队匹配未完整 |

### SYS_DUNGEON_001 Dungeon 副本（K. 副本系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 副本列表/进入/结算/扫荡 |
| **客户端本地逻辑** | 本地副本解锁、首通标识、扫荡预览 |
| **服务器权威状态** | 权威 dungeon_progress；11700 族/12000 进本/13028；34 副本列表+首通 |
| **请求协议(CS)** | CS_11700..11713, CS_12000, CS_13028.. |
| **响应/推送协议(SC)** | SC 副本回包, SC_20012 战斗 |
| **需要持久化的数据** | dungeon_progress 表(config_dungeon_new) |
| **依赖的其他服务** | 战斗、奖励、资产、体力 |
| **需要的GM功能** | GM 重置副本 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17905 cmd==11700；:18402 cmd in(11710..11713)；:12372 cmd==13028；:12251 cmd==12000 进本；P10 dungeon_clear |
| **剩余工作(与unimplemented清单一致)** | MuMu 标定掉落/体力 |

### SYS_DUNGEON_002 Endless Dungeon 无尽/深渊（K. 副本系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 无尽塔/深渊进度界面 |
| **客户端本地逻辑** | 本地层数进度渲染 |
| **服务器权威状态** | 共用 dungeon_progress；无独立无尽逻辑 |
| **请求协议(CS)** | CS_13035/13038(共用塔族) |
| **响应/推送协议(SC)** | SC 副本回包 |
| **需要持久化的数据** | dungeon_progress(shared) |
| **依赖的其他服务** | 副本、战斗 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: dungeon_progress shared；mock_server 13035/13038 塔族 |
| **剩余工作(与unimplemented清单一致)** | 无尽独立层数/奖励未闭环 |

### SYS_DUNGEON_003 Tower 塔/爬塔（K. 副本系统 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 镇魂塔/恶魔塔爬层界面 |
| **客户端本地逻辑** | 本地层数、扫荡预览 |
| **服务器权威状态** | 部分；13035/13038；config_dungeon_tower/single_tower |
| **请求协议(CS)** | CS_13035,13038 |
| **响应/推送协议(SC)** | SC_13752.. 塔回包 |
| **需要持久化的数据** | dungeon_progress(shared) |
| **依赖的其他服务** | 副本、战斗、奖励 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15702 cmd==13035；:15725 cmd==13038；config_dungeon_tower |
| **剩余工作(与unimplemented清单一致)** | 恶魔塔/金塔规则未完整 |

### SYS_DUNGEON_004 Mystic Realm 秘境/遗迹（K. 副本系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 秘境入口界面(mijing function1011) |
| **客户端本地逻辑** | 本地秘境列表渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 副本、经济 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_DUNGEON_004(mijing function1011) |
| **剩余工作(与unimplemented清单一致)** | 需建秘境权威状态 |

### SYS_DUNGEON_005 Shadow/Palace dungeon 其余副本（K. 副本系统 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 神殿/封魔等其余副本入口 |
| **客户端本地逻辑** | 本地入口渲染 |
| **服务器权威状态** | 无；config_dungeon_gods/smjz 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 副本 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_DUNGEON_005 |
| **剩余工作(与unimplemented清单一致)** | 需逐个建副本逻辑 |

### SYS_ACT_001 Sign-in/Check-in 签到（L. 活动系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 每日签到弹窗/奖励 |
| **客户端本地逻辑** | 本地签到日历渲染 |
| **服务器权威状态** | 权威 sign_got；14100/14101 幂等；30 天逐日奖励 |
| **请求协议(CS)** | CS_14100, CS_14101 |
| **响应/推送协议(SC)** | SC_141xx 签到回包, SC_10502 |
| **需要持久化的数据** | sign_got 表(config_checkin 30天) |
| **依赖的其他服务** | 奖励、资产、背包 |
| **需要的GM功能** | GM 补签 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16981 cmd in(14100,14101)；:18956 14100；P11 sign_do；config_checkin Day1~Day7 CONFIRMED |
| **剩余工作(与unimplemented清单一致)** | 无（闭环） |

### SYS_ACT_002 Seven-Day Login 七日签到（L. 活动系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 七日登录奖励界面 |
| **客户端本地逻辑** | 本地七日进度渲染 |
| **服务器权威状态** | 共用 sign_got；无独立七日逻辑 |
| **请求协议(CS)** | UNKNOWN(随签到) |
| **响应/推送协议(SC)** | SC 签到回包 |
| **需要持久化的数据** | sign_got(shared) |
| **依赖的其他服务** | 签到、奖励 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: sign_got shared；config_seven_login |
| **剩余工作(与unimplemented清单一致)** | 七日独立档位未闭环 |

### SYS_ACT_003 Invest 投资（L. 活动系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 投资计划界面/返利领取 |
| **客户端本地逻辑** | 本地投资进度渲染 |
| **服务器权威状态** | 权威 role_invest；13901 |
| **请求协议(CS)** | CS_13901.. |
| **响应/推送协议(SC)** | SC 投资回包 |
| **需要持久化的数据** | role_invest 表(config_invest) |
| **依赖的其他服务** | 资产、奖励 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10354 cmd==13901 |
| **剩余工作(与unimplemented清单一致)** | 返利档位/时间未完整 |

### SYS_ACT_004 Turntable/Lucky Draw 转盘（L. 活动系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 转盘抽奖界面/动画 |
| **客户端本地逻辑** | 本地转盘动画、概率预览 |
| **服务器权威状态** | 仅 dial reward stub；无 DB |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 资产、背包 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 DB；systems_master partial(dial reward stub) |
| **剩余工作(与unimplemented清单一致)** | 转盘概率/次数/奖励未接 |

### SYS_ACT_005 Scratch Card 刮刮乐（L. 活动系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 刮刮乐界面 |
| **客户端本地逻辑** | 本地刮奖动画 |
| **服务器权威状态** | server/scratch/ 模块注册 16651/16652(PHASE2.11) |
| **请求协议(CS)** | CS_16651,16652 |
| **响应/推送协议(SC)** | SC_166xx 刮奖回包 |
| **需要持久化的数据** | role_scratch(schema) |
| **依赖的其他服务** | 资产、背包 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:104 import scratch.handler 注册16651/16652；server/scratch/ |
| **剩余工作(与unimplemented清单一致)** | PHASE0 清单标未实现，实际 P2.11 已建模块(以源码为准) |

### SYS_ACT_006 Festival/Operation 节日运营活动（L. 活动系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 节日活动入口/倒计时 |
| **客户端本地逻辑** | 本地活动页渲染 |
| **服务器权威状态** | 无；config_fest_data 仅事件数据 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 活动基础设施 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_ACT_006 |
| **剩余工作(与unimplemented清单一致)** | 需活动框架+各节日玩法 |

### SYS_ACT_007 Answer Quiz 答题（L. 活动系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 答题活动界面 |
| **客户端本地逻辑** | 本地题目渲染、倒计时 |
| **服务器权威状态** | server/answer/ 模块注册 16100-16103(PHASE2.11) |
| **请求协议(CS)** | CS_16100,16101,16102,16103 |
| **响应/推送协议(SC)** | SC_161xx 答题回包 |
| **需要持久化的数据** | role_answer(schema) |
| **依赖的其他服务** | 奖励 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:102 import answer.handler 注册16100/16101/16102/16103；:10604 cmd==16102；server/answer/ |
| **剩余工作(与unimplemented清单一致)** | PHASE0 清单标未实现，实际 P2.11 已建模块(以源码为准) |

### SYS_ACT_008 Guess 竞猜（L. 活动系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 竞猜界面(guess function25) |
| **客户端本地逻辑** | 本地竞猜下注渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_ACT_008 |
| **剩余工作(与unimplemented清单一致)** | 需建竞猜权威状态 |

### SYS_ACT_009 Money Tree 摇钱树（L. 活动系统 · 已实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 摇钱树/膜拜界面 |
| **客户端本地逻辑** | 本地摇钱动画 |
| **服务器权威状态** | 权威 role_tree；无独立 CS(并入公会树/107xx 配置) |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | SC 资产变化 |
| **需要持久化的数据** | role_tree 表 |
| **依赖的其他服务** | 资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:3104 role_tree 等级；config_guild_tree_data |
| **剩余工作(与unimplemented清单一致)** | 摇钱次数/产出规则未完整 |

### SYS_ACT_010 Pray/QiFu 祈福（L. 活动系统 · 已实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 祈福界面、档位 |
| **客户端本地逻辑** | 本地祈福档位渲染 |
| **服务器权威状态** | 权威 role_qifu；公会祈福 config_guild_pray |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | SC 祈福回包 |
| **需要持久化的数据** | role_qifu 表(server/cfg/config_guild_pray.json) |
| **依赖的其他服务** | 公会、资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:3294 祈福次数；:3271 祈福档位 |
| **剩余工作(与unimplemented清单一致)** | 祈福奖励/冷却未完整 |

### SYS_ACT_011 Treasure Hunt 夺宝探宝（L. 活动系统 · 部分实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 夺宝/探宝界面(duobao function1013) |
| **客户端本地逻辑** | 本地探宝渲染 |
| **服务器权威状态** | 13810..13817 有处理器；PHASE0 清单标 client-only（以源码 handler 为准 partial） |
| **请求协议(CS)** | CS_13810..13817 |
| **响应/推送协议(SC)** | SC_138xx 夺宝回包 |
| **需要持久化的数据** | （未确认独立表） |
| **依赖的其他服务** | 经济、副本、背包 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:12429 cmd in(13810..13817)；:12473 cmd==13810；unimplemented SYS_ACT_011 标 client-only（源码与清单不一致） |
| **剩余工作(与unimplemented清单一致)** | 需核实 13810 族是否真闭环/有持久化 |

### SYS_ACT_012 Return/Back Flow 回归（L. 活动系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 老玩家回归界面 |
| **客户端本地逻辑** | 本地回归任务渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 活动 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_ACT_012 |
| **剩余工作(与unimplemented清单一致)** | 需回归资格判定/奖励 |

### SYS_ACT_013 Gift Recharge 累计充值活动（L. 活动系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 累计充值/天降壕礼界面 |
| **客户端本地逻辑** | 本地充值进度渲染 |
| **服务器权威状态** | 无；charge_double/tianjianghaoli |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 充值、资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_ACT_013 |
| **剩余工作(与unimplemented清单一致)** | 需累计充值统计/档位 |

### SYS_ACT_014 Point/QingFu 点/dnf/live（L. 活动系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 点券/dnf/live 活动界面 |
| **客户端本地逻辑** | 本地活动渲染 |
| **服务器权威状态** | role_point 已持久化；活动未接 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | SC 资产(role_point) |
| **需要持久化的数据** | role_point 表 |
| **依赖的其他服务** | 资产 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: role_point present / activities not hooked |
| **剩余工作(与unimplemented清单一致)** | 各活动玩法未接 |

### SYS_ACT_015 Global Wish 全球许愿（L. 活动系统 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 许愿界面 |
| **客户端本地逻辑** | 本地许愿渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | — |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_ACT_015 |
| **剩余工作(与unimplemented清单一致)** | 需许愿广播/奖励 |

### SYS_SOCIAL_001 Chat System 聊天（M. 社交系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 聊天频道/输入/气泡 |
| **客户端本地逻辑** | 本地频道切换、消息滚动、敏感词 |
| **服务器权威状态** | 权威 role_chat；10800/127xx 族；死协议判据 127xx 部分发=0 |
| **请求协议(CS)** | CS_10800.., CS_12721/12762 |
| **响应/推送协议(SC)** | SC 聊天推送 |
| **需要持久化的数据** | role_chat 表 |
| **依赖的其他服务** | 好友、头像 |
| **需要的GM功能** | GM 广播 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18236 cmd==10800；:13668 cmd in(12721..) 聊天；FINAL_REGRESSION 附二: 127xx 部分死协议 |
| **剩余工作(与unimplemented清单一致)** | 部分聊天频道发=0 未接 |

### SYS_SOCIAL_002 Friend System 好友（M. 社交系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 好友列表/添加/删除/私聊 |
| **客户端本地逻辑** | 本地好友列表、在线态渲染 |
| **服务器权威状态** | server/friend/ 模块注册 13300/13321/13303/13305(PHASE2.11)；扩展 13306/13310 等死协议 |
| **请求协议(CS)** | CS_13300,13303,13305,13321 |
| **响应/推送协议(SC)** | SC_133xx 好友列表 |
| **需要持久化的数据** | role_friend(schema) |
| **依赖的其他服务** | 聊天、角色 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:105 import friend.handler 注册13300/13321/13303/13305；:17804? 见 friend 模块；server/friend/ |
| **剩余工作(与unimplemented清单一致)** | PHASE0 清单标 partial，P2.11 已建模块；扩展好友协议死协议待取证 |

### SYS_SOCIAL_003 Moments 朋友圈（M. 社交系统 · 已实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 朋友圈动态界面 |
| **客户端本地逻辑** | 本地动态流渲染 |
| **服务器权威状态** | 权威 role_moments；无独立 CS |
| **请求协议(CS)** | UNKNOWN(随好友/社交) |
| **响应/推送协议(SC)** | SC 社交回包 |
| **需要持久化的数据** | role_moments 表 |
| **依赖的其他服务** | 好友 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: role_moments present；mock_server 无专属命令 |
| **剩余工作(与unimplemented清单一致)** | 动态发布/点赞协议未接 |

### SYS_SOCIAL_004 Guild 公会（M. 社交系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 公会主界面/成员/福利/科技 |
| **客户端本地逻辑** | 本地公会信息渲染、申请/退出 |
| **服务器权威状态** | 权威 role_guild；17501 族/19509；核心闭环，子系统(科技/神兽/祈福)partial |
| **请求协议(CS)** | CS_17500..17519, CS_19509.. |
| **响应/推送协议(SC)** | SC_175xx 公会信息 |
| **需要持久化的数据** | role_guild 表 |
| **依赖的其他服务** | 社交、祈福、矿脉 |
| **需要的GM功能** | GM 建公会 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:11854 cmd==17519；:11431 cmd==19509；:17895 cmd==17501 |
| **剩余工作(与unimplemented清单一致)** | 公会科技/神兽/副本站未完整 |

### SYS_SOCIAL_005 Marriage 结婚（M. 社交系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 求婚/婚礼/离婚/婚戒界面 |
| **客户端本地逻辑** | 本地求婚流程、婚礼动画 |
| **服务器权威状态** | 权威 role_marry/propose；18300 求婚/18302 应答/18313 离婚检查/18314 发起/18316 应答/18318 状态/18321 婚戒进阶；目标经服务端 intent 表 |
| **请求协议(CS)** | CS_18300,18302,18313,18314,18316,18318,18321,18322 |
| **响应/推送协议(SC)** | SC_183xx 婚姻状态 |
| **需要持久化的数据** | role_marry, role_marry_propose 表 |
| **依赖的其他服务** | 社交、资产、装备(婚戒) |
| **需要的GM功能** | GM 结婚/离婚 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:11077 cmd==18300 求婚；:11104 18302 应答；:11128 18313 离婚检查；:11151 18318 状态；:11155 18321 婚戒进阶 |
| **剩余工作(与unimplemented清单一致)** | 婚礼场景/礼堂未完整 |

### SYS_SOCIAL_006 Jiebai 结拜（M. 社交系统 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 结拜流程/空间/成员列表 |
| **客户端本地逻辑** | 本地结拜邀请/确认 UI |
| **服务器权威状态** | 权威 role_jiebai；19505 发起/19512 确认/19524 邀请/19530 成员列表/19533 取消/19536 提升空间 |
| **请求协议(CS)** | CS_19505,19512,19514,19524,19530,19533,19536 |
| **响应/推送协议(SC)** | SC_195xx 结拜信息 |
| **需要持久化的数据** | role_jiebai 表 |
| **依赖的其他服务** | 社交、多人 |
| **需要的GM功能** | GM 结拜 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10947 cmd==19505；:10992 19512；:10956 19524；:11022 19536；:10952 19533 |
| **剩余工作(与unimplemented清单一致)** | 结义副本/技能未完整 |

### SYS_SOCIAL_007 Flower/Gift 送花（M. 社交系统 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 送花界面/排行榜 |
| **客户端本地逻辑** | 本地送花动画 |
| **服务器权威状态** | 无；13324/13326/13328/16300 死协议(发=0) |
| **请求协议(CS)** | CS_13324/13326/13328(死协议) |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 婚姻、社交 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；FINAL_REGRESSION 附二: 送花死协议；unimplemented SYS_SOCIAL_007 |
| **剩余工作(与unimplemented清单一致)** | 需建送花权威逻辑 |

### SYS_SOCIAL_008 Party 宴会/派对（M. 社交系统 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 宴会界面 |
| **客户端本地逻辑** | 本地宴会渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 婚姻 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_SOCIAL_008 |
| **剩余工作(与unimplemented清单一致)** | 需宴会状态/奖励 |

### SYS_SOCIAL_009 Guild Wars 公会战（M. 社交系统 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 公会战匹配/战场界面 |
| **客户端本地逻辑** | 本地战场渲染、匹配 UI |
| **服务器权威状态** | 17501 按 type 分发(stub)；无独立战场 |
| **请求协议(CS)** | CS_17501, CS_195?, CS_130? |
| **响应/推送协议(SC)** | SC_175xx 分发 |
| **需要持久化的数据** | role_guild |
| **依赖的其他服务** | 公会、PvP |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17895 cmd==17501(按 type 分发 stub) |
| **剩余工作(与unimplemented清单一致)** | 公会战战场/匹配/奖励缺失 |

### SYS_SOCIAL_010 Guild Tree/Animal/Skill 公会科技神兽（M. 社交系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 公会科技树/神兽/祈福界面 |
| **客户端本地逻辑** | 本地科技渲染 |
| **服务器权威状态** | 共用 role_guild；祈福/神兽 config 已解构；无独立成长结算 |
| **请求协议(CS)** | UNKNOWN(随公会) |
| **响应/推送协议(SC)** | SC 公会回包 |
| **需要持久化的数据** | role_guild |
| **依赖的其他服务** | 公会、祈福 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:3294 公会祈福；config_guild_tree/animal/skill |
| **剩余工作(与unimplemented清单一致)** | 科技/神兽成长结算未闭环 |

### SYS_COMM_001 Rank 排行榜（N. 商业/对抗 · 部分实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 各类排行榜界面/我的排名 |
| **客户端本地逻辑** | 本地榜单渲染、红点 |
| **服务器权威状态** | 派生榜：本服唯一角色作第1名；无独立 rank 表；16900/16903 |
| **请求协议(CS)** | CS_16900..16903 |
| **响应/推送协议(SC)** | SC_169xx 榜单 |
| **需要持久化的数据** | 无独立 rank 表(派生) |
| **依赖的其他服务** | 角色、战力 |
| **需要的GM功能** | GM 改榜 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10396 cmd==16900；:19112 cmd==16903；:7333 排行榜第1名(派生) |
| **剩余工作(与unimplemented清单一致)** | 多榜真实排序/跨服榜未接 |

### SYS_COMM_002 Arena 竞技场（N. 商业/对抗 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 竞技场界面/对手/挑战/奖励 |
| **客户端本地逻辑** | 本地对手列表、战斗预览 |
| **服务器权威状态** | 权威 arena_state/arena_record；11300/11301；对手=本服已有角色(R47) |
| **请求协议(CS)** | CS_11300..11310, CS_11301 |
| **响应/推送协议(SC)** | SC_113xx 竞技场 |
| **需要持久化的数据** | arena_state, arena_record 表 |
| **依赖的其他服务** | 战斗、奖励、资产 |
| **需要的GM功能** | GM 重置 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17804 cmd==11300；:17783 cmd==11301；:6780 arena_state |
| **剩余工作(与unimplemented清单一致)** | 竞技币兑换/段位未完整 |

### SYS_COMM_003 Peakwar 巅峰战（N. 商业/对抗 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 巅峰战/精英赛界面 |
| **客户端本地逻辑** | 本地赛程渲染 |
| **服务器权威状态** | 权威 peakwar_state；18803 |
| **请求协议(CS)** | CS_18803 |
| **响应/推送协议(SC)** | SC_188xx 巅峰战 |
| **需要持久化的数据** | peakwar_state 表 |
| **依赖的其他服务** | 战斗、PvP、奖励 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:15528 cmd==18803；:8898 peakwar_state |
| **剩余工作(与unimplemented清单一致)** | 赛程/报名/奖励未完整 |

### SYS_COMM_004 Race 竞速/魂师大赛（N. 商业/对抗 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 竞速界面/排名 |
| **客户端本地逻辑** | 本地排名渲染 |
| **服务器权威状态** | 权威 race_state；17306/17308/17310/17312；本服无竞速奖励配置(回空) |
| **请求协议(CS)** | CS_17306,17308,17310,17312 |
| **响应/推送协议(SC)** | SC_173xx 竞速 |
| **需要持久化的数据** | race_state 表 |
| **依赖的其他服务** | 战斗、PvP、奖励 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:10545 cmd==17306；:10551 17308；:10558 17310；:10533 17312；:8936 race_state |
| **剩余工作(与unimplemented清单一致)** | 竞速奖励配置为空(回空)，需真值 |

### SYS_COMM_005 Cross-server 跨服（N. 商业/对抗 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 跨服入口界面 |
| **客户端本地逻辑** | 本地跨服选择渲染 |
| **服务器权威状态** | 无；单体进程；30100~31299 未实现 |
| **请求协议(CS)** | CS_30100~31299(未实现) |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 所有 PvP |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无跨服；unimplemented SYS_COMM_005(single-process) |
| **剩余工作(与unimplemented清单一致)** | 需跨服网关/多服互联 |

### SYS_COMM_006 Mining 采矿（N. 商业/对抗 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 矿脉界面 |
| **客户端本地逻辑** | 本地矿点渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 公会 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_COMM_006 |
| **剩余工作(与unimplemented清单一致)** | 需矿脉采集/争夺 |

### SYS_COMM_007 Manor/Oasis 庄园（N. 商业/对抗 · 已实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 庄园建筑/研究界面 |
| **客户端本地逻辑** | 本地建筑升级渲染 |
| **服务器权威状态** | 权威 role_build/role_build_learn；10701 建筑研究升级 |
| **请求协议(CS)** | CS_10701,10702..10762 |
| **响应/推送协议(SC)** | SC_107xx 庄园 |
| **需要持久化的数据** | role_build, role_build_learn 表 |
| **依赖的其他服务** | 资产、产出 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:12975 cmd==10701 建筑研究升级；:12966 10702；config_manor/build |
| **剩余工作(与unimplemented清单一致)** | 庄园产出/互动未完整 |

### SYS_COMM_008 Attack City 攻城/领土战（N. 商业/对抗 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 攻城战界面 |
| **客户端本地逻辑** | 本地战场渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 公会、战斗 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_COMM_008 |
| **剩余工作(与unimplemented清单一致)** | 需领土战/占领逻辑 |

### SYS_COMM_009 Freight/Escort 押镖（N. 商业/对抗 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 押镖界面/护送路线 |
| **客户端本地逻辑** | 本地镖车渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 任务、战斗 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_COMM_009 |
| **剩余工作(与unimplemented清单一致)** | 需押镖/劫镖逻辑 |

### SYS_COMM_010 Gold/JinYin Tower 金银塔（N. 商业/对抗 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 金银塔界面(jinyinta function56) |
| **客户端本地逻辑** | 本地爬塔渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 副本、经济 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_COMM_010 |
| **剩余工作(与unimplemented清单一致)** | 需金银塔逻辑 |

### SYS_GM_001 GM Tools GM 工具（O. GM 系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | GM 命令面板/控制台 |
| **客户端本地逻辑** | 本地 GM 指令输入 |
| **服务器权威状态** | 权威：CS_10922/10932 + HTTP /DSH_ADMIN(setlevel/setassets/setcharge/reward_log/ach_list/battle_replay)；P13 走正式 Service 链路+gm.log |
| **请求协议(CS)** | CS_10922,10932,10921..10950 |
| **响应/推送协议(SC)** | SC GM 回包 |
| **需要持久化的数据** | reward_log(幂等), gm.log |
| **依赖的其他服务** | 全部 Service |
| **需要的GM功能** | GM 工具本身 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17054 cmd==10922；:10512 cmd==10932；HTTP /DSH_ADMIN/*；P13 setlevel/setassets 走 Service |
| **剩余工作(与unimplemented清单一致)** | 无（调试闭环） |

### SYS_BACK_001 Server Backend/DB 后台数据库（P. 后台系统 · 已实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 无客户端界面（服务端） |
| **客户端本地逻辑** | — |
| **服务器权威状态** | 权威持久化层 persistence/db.py；db_conn/db_release；roles.db 全部表 |
| **请求协议(CS)** | （内部） |
| **响应/推送协议(SC)** | （内部） |
| **需要持久化的数据** | roles.db 全部表 |
| **依赖的其他服务** | 全部业务 |
| **需要的GM功能** | DB 备份/查询 |
| **当前已实现部分(源码/测试证据)** | persistence/db.py；role/storage db_get/save_role；FINAL_REGRESSION 附: from-import 无损下沉 |
| **剩余工作(与unimplemented清单一致)** | 无（基础闭环） |

### SYS_BACK_002 Cross-server backend 跨服后台（P. 后台系统 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 无客户端界面 |
| **客户端本地逻辑** | — |
| **服务器权威状态** | 无；单体进程 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 跨服 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无跨服；unimplemented SYS_BACK_002(single-process) |
| **剩余工作(与unimplemented清单一致)** | 需跨服网关/状态同步 |

### SYS_HIDDEN_001 Seal System 封印（Q. 隐藏/未归类 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 封印界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；config_seal 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 副本、Boss |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_HIDDEN_001 |
| **剩余工作(与unimplemented清单一致)** | 需封印权威状态 |

### SYS_HIDDEN_002 XiuLuo 修罗（Q. 隐藏/未归类 · 未实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 修罗界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；config_xiuluo_data 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | PvP |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_HIDDEN_002 |
| **剩余工作(与unimplemented清单一致)** | 需修罗逻辑 |

### SYS_HIDDEN_003 Chief 会长/百官（Q. 隐藏/未归类 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 百官/首席界面(chief function41) |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | Rank |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_HIDDEN_003 |
| **剩余工作(与unimplemented清单一致)** | 需百官评选/奖励 |

### SYS_HIDDEN_004 Star Soul 星魂（Q. 隐藏/未归类 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 星魂界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 复用 role_runes；无独立逻辑 |
| **请求协议(CS)** | UNKNOWN(随符文) |
| **响应/推送协议(SC)** | SC_10301 |
| **需要持久化的数据** | role_runes(shared) |
| **依赖的其他服务** | 符文、属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: role_runes? partial；mock_server 214xx 符文族 |
| **剩余工作(与unimplemented清单一致)** | 星魂独立逻辑未取证 |

### SYS_HIDDEN_005 God Redemption 神位/神减免（Q. 隐藏/未归类 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 神位界面(godredeem modules) |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；client-only not hooked |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 伙伴 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_HIDDEN_005(godredeem_* modules) |
| **剩余工作(与unimplemented清单一致)** | 需神位权威状态 |

### SYS_HIDDEN_006 Dragon 神龙/巨龙（Q. 隐藏/未归类 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 巨龙界面(julong function1008) |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；config_dragon 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | — |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_HIDDEN_006 |
| **剩余工作(与unimplemented清单一致)** | 需巨龙逻辑 |

### SYS_HIDDEN_007 Balloon 气球/活动（Q. 隐藏/未归类 · 未实现 · VERIFIED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 气球界面(action_balloon function48) |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；config_holiday_balloon 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 活动 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_HIDDEN_007 |
| **剩余工作(与unimplemented清单一致)** | 需气球活动逻辑 |

### SYS_UNKNOWN_001 Dan War 丹药战（R. 未知系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 丹药战界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；config_dan_war 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | — |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_UNKNOWN_001 |
| **剩余工作(与unimplemented清单一致)** | 需取证入口/协议 |

### SYS_UNKNOWN_002 YunYing Ops 运营活动（R. 未知系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 未命名运营入口(function ids 33/34/37/40/101/103) |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；config_function.json 未命名 id |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 活动 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_UNKNOWN_002 |
| **剩余工作(与unimplemented清单一致)** | 需逐个识别功能 id |

### SYS_UNKNOWN_003 Insight 顿悟/洞察（R. 未知系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 顿悟界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 仅 roles.insight_status 字段；无逻辑 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | SC_10302 携带 |
| **需要持久化的数据** | roles.insight_status 列 |
| **依赖的其他服务** | 属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | systems_master: roles.insight_status field only |
| **剩余工作(与unimplemented清单一致)** | 顿悟逻辑/协议未接 |

### SYS_UNKNOWN_004 Color/Head 染色（R. 未知系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 染色界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | 无；config_color 仅配置 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | 无 |
| **依赖的其他服务** | 外观 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 无 handler；unimplemented SYS_UNKNOWN_004 |
| **剩余工作(与unimplemented清单一致)** | 需染色状态/协议 |

### SYS_EQUIP_005 Equip Refine 装备洗练（E. 装备系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 洗练界面 |
| **客户端本地逻辑** | 本地洗练属性预览 |
| **服务器权威状态** | 无；APK inventory 未发现专属 config/module/protocol |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | UNKNOWN |
| **依赖的其他服务** | 装备、属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | unimplemented SYS_EQUIP_005: named in PHASE0 checklist; 无 config/module/protocol；mock_server 无 handler |
| **剩余工作(与unimplemented清单一致)** | 需先取证客户端入口与协议 |

### SYS_EQUIP_006 Gem/Socket 宝石（E. 装备系统 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 宝石背包/镶嵌界面 |
| **客户端本地逻辑** | 本地镶嵌预览、孔位展示 |
| **服务器权威状态** | 合成 192 条已接(config_item_fuse)；镶嵌加成总表 EqmJewel 提取，单宝石语义 INFERENCE |
| **请求协议(CS)** | UNKNOWN（镶嵌协议未取证） |
| **响应/推送协议(SC)** | SC_10301 属性 |
| **需要持久化的数据** | bag_items(宝石); ItemMiscAttrJewel 总属性表 |
| **依赖的其他服务** | 装备、背包、属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server 合成族; FINAL_REGRESSION: 宝石40物品+总属性表 CONFIRMED, 单宝石镶嵌加成 INFERENCE(ItemJewel 反构造 null) |
| **剩余工作(与unimplemented清单一致)** | 镶嵌 CS 命令取证→接通 镶嵌→总表→Attribute→Power 闭环 |

### SYS_GROWTH_006 Soul Bone 魂骨（C. 成长系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 魂骨界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | server/soulbone/ 目录存在(HANDOFF 文件地图)；无接入命令 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | UNKNOWN |
| **依赖的其他服务** | 角色、装备 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | HANDOFF 文件地图: server/soulbone/；mock_server 无接入 handler；unimplemented SYS_GROWTH_006 |
| **剩余工作(与unimplemented清单一致)** | 需魂骨模块接线/协议取证 |

### SYS_GROWTH_007 Augment/Amplify 增幅（C. 成长系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 增幅界面 |
| **客户端本地逻辑** | 本地渲染 |
| **服务器权威状态** | server/amplification/ 目录存在；无接入命令 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | UNKNOWN |
| **依赖的其他服务** | 角色属性 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | HANDOFF 文件地图: server/amplification/；mock_server 无接入 handler；unimplemented SYS_GROWTH_007 |
| **剩余工作(与unimplemented清单一致)** | 需增幅模块接线 |

### SYS_ECON_012 Drop/Loot Table 掉落（H. 资源经济 · 部分实现 · INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 战斗/副本掉落展示 |
| **客户端本地逻辑** | 本地掉落物品列表渲染 |
| **服务器权威状态** | 掉落经 gift/battle 路径；config_drop 29组；无独立 drop 系统；概率 INFERENCE |
| **请求协议(CS)** | （随战斗/副本 CS） |
| **响应/推送协议(SC)** | SC_10502 入包 |
| **需要持久化的数据** | bag_items(reward_log 幂等) |
| **依赖的其他服务** | 战斗、副本、背包、资产 |
| **需要的GM功能** | GM 触发掉落 |
| **当前已实现部分(源码/测试证据)** | FINAL_REGRESSION P16: drop_test；config_drop 29组金币/首通池(20001~20029) CONFIRMED；reward/service |
| **剩余工作(与unimplemented清单一致)** | 掉落概率 pp/1000 基准需实机标定 |

### SYS_CORE_008 Red Dot/Badge 红点（A. 核心系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 全局红点/角标 |
| **客户端本地逻辑** | 本地红点聚合/清除 |
| **服务器权威状态** | 无；APK inventory 未发现专属 config/module/protocol |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | UNKNOWN |
| **依赖的其他服务** | 全部 UI |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | unimplemented SYS_CORE_008: 无 config/module/protocol；mock_server 无 handler |
| **剩余工作(与unimplemented清单一致)** | 需红点推送/聚合协议 |

### SYS_CORE_009 UI State Sync UI状态（A. 核心系统 · 未实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | UI 开启/关闭状态同步 |
| **客户端本地逻辑** | 本地 UI 状态机 |
| **服务器权威状态** | 无专属同步协议 |
| **请求协议(CS)** | UNKNOWN |
| **响应/推送协议(SC)** | UNKNOWN |
| **需要持久化的数据** | UNKNOWN |
| **依赖的其他服务** | Protocol/Network |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | unimplemented SYS_CORE_009: 无 config/module/protocol |
| **剩余工作(与unimplemented清单一致)** | 需 UI 状态同步帧 |

### SYS_ROLE_007 Combat Power 战力（B. 角色系统 · 部分实现 · CONFIRMED）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 战力数值展示/九维 breakdown |
| **客户端本地逻辑** | 本地战力数字、九维渲染 |
| **服务器权威状态** | 权威 power/service；10304 战力/10306 资产推送；AttrPower 31 属性系数 CONFIRMED |
| **请求协议(CS)** | SC_10304, SC_10306(服务器推送) |
| **响应/推送协议(SC)** | SC_10304 战力, SC_10306 |
| **需要持久化的数据** | role_attr(派生) |
| **依赖的其他服务** | 属性、装备、外观、伙伴 |
| **需要的GM功能** | /DSH_ADMIN 查战力 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:17208 cmd==10304 战力推送；:17189 cmd==10306；FINAL_REGRESSION P12 power.breakdown；AttrPower 31属性 CONFIRMED |
| **剩余工作(与unimplemented清单一致)** | 九维分项组合公式待实机验证 |

### SYS_FRIEND_006 Partner Training 伙伴培养（F. 伙伴系统 · 部分实现 · UNKNOWN）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 伙伴培养/升级/喂丹界面 |
| **客户端本地逻辑** | 本地培养预览 |
| **服务器权威状态** | 11216 伙伴状态+partner_feed(P8)；喂养消耗数值 UNKNOWN |
| **请求协议(CS)** | CS_11216 |
| **响应/推送协议(SC)** | SC 伙伴面板 |
| **需要持久化的数据** | role_heros(培养等级) |
| **依赖的其他服务** | 伙伴、资产、背包 |
| **需要的GM功能** | GM 养伙伴 |
| **当前已实现部分(源码/测试证据)** | mock_server.py:16292 cmd==11216；P8 partner_feed；FINAL_REGRESSION 缺口#2 喂养消耗 UNKNOWN |
| **剩余工作(与unimplemented清单一致)** | 喂养消耗真值需实机喂养取证 |

### SYS_FRIEND_007 Partner Equipment 伙伴装备（F. 伙伴系统 · 部分实现 · STRONG_INFERENCE）

| 字段 | 内容 |
|---|---|
| **客户端展示** | 伙伴装备槽/穿戴界面 |
| **客户端本地逻辑** | 本地伙伴装备预览 |
| **服务器权威状态** | 协议段 11200~11205 被引用并接入；无独立模块 |
| **请求协议(CS)** | CS_11200~11205 |
| **响应/推送协议(SC)** | SC 伙伴装备回包 |
| **需要持久化的数据** | （随 role_heros/equip_items） |
| **依赖的其他服务** | 伙伴、装备 |
| **需要的GM功能** | — |
| **当前已实现部分(源码/测试证据)** | mock_server.py:18127 cmd==11200；:12105 cmd in(11205..)；systems_master partial |
| **剩余工作(与unimplemented清单一致)** | 伙伴装备独立模块/属性贡献未闭环 |
