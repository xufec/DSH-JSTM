# JSTM 系统依赖图 system_dependency_graph.md（PHASE C0）

> 由 systems_master.json 的 dependencies/related_systems 程序化生成；强依赖在表中标注。

```mermaid
graph TD
  SYS_CORE_001 --> protocol
  SYS_CORE_001 --> network
  SYS_CORE_002 --> Account_Login
  SYS_CORE_003 --> Role_Login
  SYS_CORE_003 --> Scene
  SYS_CORE_004 --> Account_Login
  SYS_CORE_005 --> Role_Login
  SYS_CORE_005 --> Network
  SYS_CORE_005 --> pathfind
  SYS_ROLE_001 --> Role_Base_Init
  SYS_ROLE_002 --> Role_Creation
  SYS_ROLE_003 --> Role_Base_Init
  SYS_ROLE_003 --> Rank
  SYS_ROLE_004 --> Recharge
  SYS_ROLE_004 --> Economy
  SYS_ROLE_005 --> Role_Base_Init
  SYS_GROWTH_001 --> Partner
  SYS_GROWTH_001 --> Battle
  SYS_GROWTH_002 --> Skill
  SYS_GROWTH_003 --> Skill
  SYS_GROWTH_004 --> Battle
  SYS_GROWTH_005 --> Battle
  SYS_GROWTH_005 --> Partner
  SYS_BATTLE_001 --> Skill
  SYS_BATTLE_001 --> Buff
  SYS_BATTLE_001 --> Partner
  SYS_BATTLE_001 --> Equipment
  SYS_BATTLE_002 --> Battle
  SYS_BATTLE_003 --> Battle
  SYS_BATTLE_004 --> Battle
  SYS_BATTLE_004 --> Cross-server
  SYS_BATTLE_005 --> Battle
  SYS_EQUIP_001 --> Inventory
  SYS_EQUIP_001 --> Partner
  SYS_EQUIP_002 --> Equipment
  SYS_EQUIP_002 --> Inventory
  SYS_EQUIP_003 --> Equipment
  SYS_EQUIP_003 --> Dungeon
  SYS_EQUIP_004 --> Equipment
  SYS_FRIEND_001 --> Inventory
  SYS_FRIEND_001 --> Battle
  SYS_FRIEND_001 --> Skill
  SYS_FRIEND_002 --> Partner
  SYS_FRIEND_002 --> Battle
  SYS_FRIEND_003 --> Partner
  SYS_FRIEND_004 --> Partner
  SYS_FRIEND_004 --> Mall
  SYS_FRIEND_005 --> Partner
  SYS_APPEAR_001 --> Appearance
  SYS_APPEAR_001 --> Attribute
  SYS_APPEAR_002 --> Appearance
  SYS_APPEAR_003 --> Appearance
  SYS_APPEAR_003 --> Attribute
  SYS_APPEAR_004 --> Appearance
  SYS_APPEAR_005 --> Appearance
  SYS_APPEAR_005 --> Partner
  SYS_APPEAR_006 --> Appearance
  SYS_APPEAR_007 --> Battle
  SYS_APPEAR_007 --> Partner
  SYS_APPEAR_008 --> Appearance
  SYS_APPEAR_009 --> Appearance
  SYS_APPEAR_009 --> Attribute
  SYS_APPEAR_010 --> Appearance
  SYS_APPEAR_010 --> Attribute
  SYS_ECON_002 --> Economy
  SYS_ECON_003 --> Economy
  SYS_ECON_003 --> Recharge
  SYS_ECON_004 --> Inventory
  SYS_ECON_005 --> Economy
  SYS_ECON_005 --> Inventory
  SYS_ECON_006 --> Market
  SYS_ECON_006 --> Economy
  SYS_ECON_007 --> Mall
  SYS_ECON_007 --> Economy
  SYS_ECON_008 --> Economy
  SYS_ECON_008 --> Inventory
  SYS_ECON_009 --> Economy
  SYS_ECON_009 --> Rewards
  SYS_ECON_010 --> Economy
  SYS_ECON_010 --> VIP
  SYS_ECON_011 --> Inventory
  SYS_ECON_011 --> Rewards
  SYS_QUEST_001 --> Rewards
  SYS_QUEST_001 --> Economy
  SYS_QUEST_002 --> Mission
  SYS_QUEST_002 --> Rewards
  SYS_QUEST_003 --> Rewards
  SYS_QUEST_004 --> Achievement
  SYS_MAP_001 --> Scene
  SYS_MAP_002 --> Scene
  SYS_MAP_002 --> Social
  SYS_DUNGEON_001 --> Battle
  SYS_DUNGEON_001 --> Rewards
  SYS_DUNGEON_002 --> Dungeon
  SYS_DUNGEON_002 --> Battle
  SYS_DUNGEON_002 --> Formation
  SYS_DUNGEON_003 --> Dungeon
  SYS_DUNGEON_003 --> Battle
  SYS_DUNGEON_004 --> Dungeon
  SYS_DUNGEON_005 --> Dungeon
  SYS_ACT_001 --> Rewards
  SYS_ACT_001 --> Daily
  SYS_ACT_002 --> Sign-in
  SYS_ACT_003 --> Recharge
  SYS_ACT_003 --> Economy
  SYS_ACT_004 --> Mall
  SYS_ACT_004 --> Economy
  SYS_ACT_005 --> Lottery
  SYS_ACT_006 --> Activity_infra
  SYS_ACT_009 --> Economy
  SYS_ACT_009 --> Daily
  SYS_ACT_010 --> Economy
  SYS_ACT_010 --> Daily
  SYS_ACT_011 --> Economy
  SYS_ACT_011 --> Dungeon
  SYS_ACT_012 --> Activity
  SYS_ACT_013 --> Recharge
  SYS_SOCIAL_002 --> Chat
  SYS_SOCIAL_003 --> Friend
  SYS_SOCIAL_004 --> Social
  SYS_SOCIAL_004 --> Economy
  SYS_SOCIAL_005 --> Social
  SYS_SOCIAL_005 --> Team
  SYS_SOCIAL_006 --> Social
  SYS_SOCIAL_006 --> Team
  SYS_SOCIAL_007 --> Marriage
  SYS_SOCIAL_007 --> Social
  SYS_SOCIAL_008 --> Marriage
  SYS_SOCIAL_009 --> Guild
  SYS_SOCIAL_009 --> Battle
  SYS_SOCIAL_010 --> Guild
  SYS_COMM_001 --> Title
  SYS_COMM_002 --> Battle
  SYS_COMM_002 --> Rank
  SYS_COMM_003 --> Battle
  SYS_COMM_003 --> Rank
  SYS_COMM_004 --> Battle
  SYS_COMM_005 --> All_PvP
  SYS_COMM_006 --> Guild
  SYS_COMM_007 --> Economy
  SYS_COMM_008 --> Guild
  SYS_COMM_008 --> Battle
  SYS_COMM_009 --> Mission
  SYS_COMM_009 --> Battle
  SYS_COMM_010 --> Dungeon
  SYS_COMM_010 --> Economy
  SYS_HIDDEN_001 --> Dungeon
  SYS_HIDDEN_001 --> Boss
  SYS_HIDDEN_002 --> PvP
  SYS_HIDDEN_003 --> Rank
  SYS_HIDDEN_004 --> Rune
  SYS_HIDDEN_004 --> Wing
  SYS_HIDDEN_005 --> Partner
  SYS_HIDDEN_007 --> Activity
  SYS_UNKNOWN_002 --> Activity
  SYS_UNKNOWN_003 --> Skill
  SYS_UNKNOWN_004 --> Appearance
  SYS_EQUIP_005 --> Equipment
  SYS_EQUIP_006 --> Equipment
  SYS_GROWTH_006 --> Role
  SYS_GROWTH_006 --> Equipment
  SYS_GROWTH_007 --> Role_Attribute
  SYS_ECON_012 --> Battle
  SYS_ECON_012 --> Monster
  SYS_ECON_012 --> Item
  SYS_CORE_008 --> all_UI
  SYS_CORE_009 --> Protocol_Network
  SYS_ROLE_007 --> Role_Attribute
  SYS_FRIEND_006 --> Partner_Hero_System
  SYS_FRIEND_007 --> Partner_Hero_System
  SYS_FRIEND_007 --> Equipment
```

## 强依赖链（收敛到统一服务）

| 依赖链 | 说明 |
|---|---|
| 装备 → 背包 → 属性 → 战力 | 穿戴/强化改背包→属性→战力重算 |
| 商城/黑市/活动 → CurrencyService → RewardService | 扣费/发放统一走货币与奖励服务 |
| 任务 → ConditionService → RewardService | 条件判定后发奖，幂等 reference_id |
| 所有成长系统 → AttributeService → PowerService | 禁止自行算属性/战力 |

## 数据一致性纪律

- 状态变更必须经 Service 落盘并 ClientSync。
- 奖励必须带 reference_id 防重。
- 任何系统禁止绕过 CurrencyService/RewardService。
