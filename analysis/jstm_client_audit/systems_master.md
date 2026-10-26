# JSTM 系统总目录 systems_master（PHASE C0 审计）

> 机读版：`systems_master.json`（124 系统，每系统 22 字段）。
> present_in_* 由脚本 basename 精确匹配三版本扫描清单生成（CONFIRMED）。

| system_id | 名称 | 分类 | 首现 | 1.3.0 | 1.4.9 | 1.4.11 | 现状 | 置信 |
|---|---|---|---|---|---|---|---|---|
| SYS_CORE_001 | Account Login | A. 核心系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_CORE_002 | Role Creation | A. 核心系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_CORE_003 | Role Base/Init | A. 核心系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_CORE_004 | Role Login | A. 核心系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_CORE_005 | Scene & Movement | A. 核心系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_CORE_006 | Protocol/Network Layer | A. 核心系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_CORE_007 | Version/Resource Update | A. 核心系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ROLE_001 | Role Attribute | B. 角色系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ROLE_002 | Career/Job | B. 角色系统 | 1.3.0 | true | true | true | implemented | VERIFIED |
| SYS_ROLE_003 | Title System | B. 角色系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ROLE_004 | VIP System | B. 角色系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ROLE_005 | Experience/Level | B. 角色系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ROLE_006 | Avatar/Head & Chat Bubble | B. 角色系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_GROWTH_001 | Skill System | C. 成长系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_GROWTH_002 | Talent/天赋 | C. 成长系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_GROWTH_003 | Practice/修炼 (Buff) | C. 成长系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_GROWTH_004 | Buff System | C. 成长系统 | 1.3.0 | true | true | true | partial | CONFIRMED |
| SYS_GROWTH_005 | Morale 士气 | C. 成长系统 | 1.3.0 | true | true | true | partial | STRONG_INFERENCE |
| SYS_BATTLE_001 | Turn-based Battle | D. 战斗系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_BATTLE_002 | Auto-battle / AFK | D. 战斗系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_BATTLE_003 | Battle Replay / Video | D. 战斗系统 | 1.4.9 | false | true | true | partial | VERIFIED |
| SYS_BATTLE_004 | God War Battle | D. 战斗系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_BATTLE_005 | Boss System | D. 战斗系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_EQUIP_001 | Equipment System | E. 装备系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_EQUIP_002 | Smith / Forge / Fuse | E. 装备系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_EQUIP_003 | Rune System | E. 装备系统 | 1.4.9 | false | true | true | implemented | CONFIRMED |
| SYS_EQUIP_004 | Equip StarUp/强化 | E. 装备系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_FRIEND_001 | Partner/Hero System | F. 伙伴系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_FRIEND_002 | Formation / 阵法 | F. 伙伴系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_FRIEND_003 | Partner Atlas/图鉴 | F. 伙伴系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_FRIEND_004 | Partner Recruit/招募 | F. 伙伴系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_FRIEND_005 | Partner Fetter/羁绊 | F. 伙伴系统 | 1.4.9 | UNKNOWN | true | true | partial | STRONG_INFERENCE |
| SYS_APPEAR_001 | Wing System 翅膀 | G. 外观系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_APPEAR_002 | Mount 坐骑 | G. 外观系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_APPEAR_003 | Beast 灵兽 | G. 外观系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_APPEAR_004 | Soul 元神 | G. 外观系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_APPEAR_005 | Divine Artifact 神器 | G. 外观系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_APPEAR_006 | Fate/Natal 命格 | G. 外观系统 | 1.4.9 | false | true | true | implemented | CONFIRMED |
| SYS_APPEAR_007 | Magic Weapon 法宝 | G. 外观系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_APPEAR_008 | Vehicle/Chair 座驾 | G. 外观系统 | 1.4.9 | UNKNOWN | true | true | implemented | CONFIRMED |
| SYS_APPEAR_009 | Fashion/Skin 时装 | G. 外观系统 | 1.3.0 | true | true | true | implemented | VERIFIED |
| SYS_APPEAR_010 | Halo 光环 | G. 外观系统 | 1.4.9 | false | true | true | implemented | VERIFIED |
| SYS_ECON_001 | Assets/Currency System | H. 资源经济 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ECON_002 | Inventory/Bag 背包 | H. 资源经济 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ECON_003 | Mall/Shop 商城 | H. 资源经济 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ECON_004 | Storage/Warehouse 仓库 | H. 资源经济 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ECON_005 | Trade Market 市场/交易 | H. 资源经济 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ECON_006 | Black Market 黑市 | H. 资源经济 | 1.4.9 | false | true | true | partial | VERIFIED |
| SYS_ECON_007 | Exchange 兑换 | H. 资源经济 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ECON_008 | Auction/拍卖 | H. 资源经济 | 1.3.0 | true | true | true | implemented | VERIFIED |
| SYS_ECON_009 | Mail 邮件 | H. 资源经济 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ECON_010 | Recharge/Payment 充值 | H. 资源经济 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ECON_011 | Gift Item 礼包/道具 | H. 资源经济 | 1.3.0 | true | true | true | implemented | VERIFIED |
| SYS_QUEST_001 | Mission/Quest 任务 | I. 任务系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_QUEST_002 | Daily/Active 日常活跃 | I. 任务系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_QUEST_003 | Achievement 成就 | I. 任务系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_QUEST_004 | Growth Target 成长目标 | I. 任务系统 | 1.4.9 | false | true | true | partial | VERIFIED |
| SYS_QUEST_005 | Guide System 引导 | I. 任务系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_MAP_001 | World Map / Region | J. 地图系统 | 1.3.0 | true | true | true | implemented | VERIFIED |
| SYS_MAP_002 | Team Group 组队 | J. 地图系统 | 1.3.0 | true | true | true | implemented | VERIFIED |
| SYS_DUNGEON_001 | Dungeon 副本 | K. 副本系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_DUNGEON_002 | Endless Dungeon 无尽/深渊 | K. 副本系统 | 1.4.9 | UNKNOWN | true | true | partial | VERIFIED |
| SYS_DUNGEON_003 | Tower 塔 | K. 副本系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_DUNGEON_004 | Mystic Realm 秘境/遗迹 | K. 副本系统 | 1.4.9 | UNKNOWN | true | true | partial | VERIFIED |
| SYS_DUNGEON_005 | Shadow/Palace dungeon other | K. 副本系统 | 1.3.0 | true | true | true | partial | STRONG_INFERENCE |
| SYS_ACT_001 | Sign-in/Check-in 签到 | L. 活动系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ACT_002 | Seven-Day Login 七日签到 | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_003 | Invest 投资 | L. 活动系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ACT_004 | Turntable/Lucky Draw 转盘抽奖 | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_005 | Scratch Card 刮刮乐 | L. 活动系统 | 1.4.9 | UNKNOWN | true | true | partial | STRONG_INFERENCE |
| SYS_ACT_006 | Festival/Operation Activity 节日/运营活动 | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_007 | Answer Quiz 答题 | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_008 | Guess 竞猜 | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_009 | Money Tree 摇钱树 | L. 活动系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ACT_010 | Pray/QiFu 祈福 | L. 活动系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_ACT_011 | Treasure Hunt 夺宝/探宝 | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_012 | Return/Back Flow 回归 | L. 活动系统 | 1.4.9 | UNKNOWN | true | true | partial | VERIFIED |
| SYS_ACT_013 | Gift Recharge events 充值活动 | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_014 | Point/Qing Fu activities 点/dnf/live | L. 活动系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_ACT_015 | Global Wish 全球许愿 | L. 活动系统 | 1.3.0 | true | true | true | partial | STRONG_INFERENCE |
| SYS_SOCIAL_001 | Chat System | M. 社交系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_SOCIAL_002 | Friend System | M. 社交系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_SOCIAL_003 | Moments/朋友圈 | M. 社交系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_SOCIAL_004 | Guild 公会 | M. 社交系统 | 1.3.0 | true | true | true | partial | CONFIRMED |
| SYS_SOCIAL_005 | Marriage 结婚 | M. 社交系统 | 1.3.0 | true | true | true | implemented | VERIFIED |
| SYS_SOCIAL_006 | Jiebai Soulmate 结拜 | M. 社交系统 | 1.4.9 | false | true | true | implemented | VERIFIED |
| SYS_SOCIAL_007 | Flower/Gift 送花 | M. 社交系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_SOCIAL_008 | Party 宴会/派对 | M. 社交系统 | 1.3.0 | true | true | true | partial | STRONG_INFERENCE |
| SYS_SOCIAL_009 | Guild Wars 公会战 | M. 社交系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_SOCIAL_010 | Guild Tree/Animal/Skill sub | M. 社交系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_COMM_001 | Rank 排行榜 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_COMM_002 | Arena 竞技场 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_COMM_003 | Peakwar 巅峰战 | N. 商业系统 / 对抗 | 1.4.9 | false | true | true | implemented | CONFIRMED |
| SYS_COMM_004 | Race 竞速/种族战 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_COMM_005 | Cross-server 跨服 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | not_implemented | STRONG_INFERENCE |
| SYS_COMM_006 | Mining 采矿 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_COMM_007 | Manor/Oasis 庄园/领地 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_COMM_008 | Attack City 攻城/领土战 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | partial | STRONG_INFERENCE |
| SYS_COMM_009 | Freight/Escort 押镖 | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | partial | STRONG_INFERENCE |
| SYS_COMM_010 | Gold/JinYin Tower activities | N. 商业系统 / 对抗 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_GM_001 | GM Tools | O. GM 系统 | 1.3.0 | true | true | true | implemented | CONFIRMED |
| SYS_BACK_001 | Server Backend/DB | P. 后台系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | implemented | UNKNOWN |
| SYS_BACK_002 | Cross-server backend | P. 后台系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | STRONG_INFERENCE |
| SYS_HIDDEN_001 | Seal System 封印 | Q. 隐藏/未归类系统 | 1.3.0 | true | true | true | partial | STRONG_INFERENCE |
| SYS_HIDDEN_002 | XiuLuo 修罗 | Q. 隐藏/未归类系统 | 1.4.9 | UNKNOWN | true | true | partial | STRONG_INFERENCE |
| SYS_HIDDEN_003 | Chief 会长/百官 | Q. 隐藏/未归类系统 | 1.4.9 | UNKNOWN | true | true | partial | VERIFIED |
| SYS_HIDDEN_004 | Star Soul 星魂 | Q. 隐藏/未归类系统 | 1.4.9 | false | true | true | partial | VERIFIED |
| SYS_HIDDEN_005 | God Redemption 神位/神减免 | Q. 隐藏/未归类系统 | 1.3.0 | true | true | true | partial | VERIFIED |
| SYS_HIDDEN_006 | Dragon 神龙/巨龙 | Q. 隐藏/未归类系统 | 1.4.9 | false | true | true | partial | VERIFIED |
| SYS_HIDDEN_007 | Balloon 气球/多种活动 | Q. 隐藏/未归类系统 | 1.4.9 | UNKNOWN | true | true | partial | VERIFIED |
| SYS_UNKNOWN_001 | Dan War / 丹药战 | R. 未知系统 | 1.3.0 | true | true | true | partial | UNKNOWN |
| SYS_UNKNOWN_002 | YunYing Ops systems | R. 未知系统 | UNKNOWN | false | false | false | partial | UNKNOWN |
| SYS_UNKNOWN_003 | Insight 顿悟/洞察 | R. 未知系统 | 1.4.9 | UNKNOWN | true | true | partial | VERIFIED |
| SYS_UNKNOWN_004 | Color/Head system | R. 未知系统 | 1.3.0 | true | true | true | partial | UNKNOWN |
| SYS_EQUIP_005 | Equip Refine 装备洗练 | E. 装备系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_EQUIP_006 | Gem / Socket 宝石 | E. 装备系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_GROWTH_006 | Soul Bone 魂骨 | C. 成长系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_GROWTH_007 | Augment / Amplify 增幅 | C. 成长系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_ECON_012 | Drop / Loot Table 掉落 | H. 资源经济 | 1.3.0 | true | true | true | partial | INFERENCE |
| SYS_CORE_008 | Red Dot / Badge 红点 | A. 核心系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_CORE_009 | UI State Sync UI状态 | A. 核心系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_ROLE_007 | Combat Power 战力 | B. 角色系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_FRIEND_006 | Partner Training 伙伴培养 | F. 伙伴系统 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | not_implemented | UNKNOWN |
| SYS_FRIEND_007 | Partner Equipment 伙伴装备 | F. 伙伴系统 | 1.3.0 | true | true | true | partial | INFERENCE |

## present_in_* 一致性统计

| 版本 | true | false | UNKNOWN |
|---|---|---|---|
| 1.3.0 | 93 | 11 | 20 |
| 1.4.9 | 113 | 1 | 10 |
| 1.4.11 | 113 | 1 | 10 |
