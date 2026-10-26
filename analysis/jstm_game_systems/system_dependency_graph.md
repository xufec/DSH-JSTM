# JSTM 系统依赖图 system_dependency_graph.md

> Phase 0 审计产物。依据 mock_server 现有实现（角色/等级/属性/战力/装备/伙伴/多维成长/任务/战斗/商城/活动）
> 与任务书"统一 AttributeService / PowerService / CurrencyService / RewardService"要求绘制。

## 顶层依赖链（收敛到四个统一服务）

```
                          ┌──────────────────────────────────────────────┐
                          │           PersistenceService (SQLite)         │
                          │   role_attr / role_assets / bag_items / ...   │
                          └───────────────▲──────────────────────────────┘
                                          │ 任意状态修改必须经 Service 落盘
       成长/外观/伙伴                               │                    │
角色─等级─经验                                        │                    │
  │  └─属性(LevelService)                            │           修改  保存
装备─强化/进阶/洗练/宝石/符文                          │                    │
伙伴─等级/品质/星级/装备/技能                          │                    ▼
翅膀/坐骑/法宝/元神/命格/神器/时装/图腾/椅子/五行   ──► AttributeService ─► ClientSync
阵法                                        │         (汇总 FinalAttribute)   │
增幅/进阶(promote/intensify)                     ▼                            │
任务/活动/BUFF奖励                       PowerService(计算战力+贡献拆分) ◄─────┘

                    CurrencyService (统一货币: 金币/铜币/钻石/礼券/...)
                          ▲
        商城 / 黑市 / 活动 / 礼包 / 充值 / 签到 ──► (扣费/发放)
                          │
                    RewardService (统一 EXP/货币/物品/装备/伙伴/材料/礼包)
                          ▲
        任务 / 战斗 / 副本 / 活动 / 签到 / 邮件 / 商城 ──► 全部走 RewardService
```

## 关键依赖关系（逐系统）

| 依赖链 | 说明 |
|---|---|
| 角色 → 等级 → 经验 → 属性 → 战力 | 升级触发属性成长 → 战力重算 → 客户端同步 |
| 装备 → 属性 → 战力 | 穿戴/强化/洗练均改属性 → 战力 |
| 伙伴 → 伙伴属性 → 战力 → 战斗 | 伙伴上阵进阵法参与战斗 |
| 翅膀/坐骑/法宝/命格/神器/元神/时装/图腾/椅子 → 属性 → 战力 | 每个成长系统只提供 AttributeSource |
| 阵法 → 伙伴 → 战斗 → 战力 | 阵位伙伴才是战斗单位与战力来源 |
| 任务 → 条件(ConditionService) → 奖励(RewardService) → 货币/物品/EXP | 条件：level/item/kill/complete/power |
| 战斗 → 奖励 → 任务进度 | 击杀推进任务进度 → 反哺战斗循环，形成 Gameplay Loop |
| 商城/活动 → 货币(CurrencyService) → 扣费 → RewardService → 发货 | 幂等（reference_id 防重复领取） |
| 所有系统 → Persistence → ClientSync | 状态变必须推送与落盘 |

## 依赖环（可玩循环 PLAY LOOP）

```
进入地图 → 接任务 → 自动寻路 → 遇怪 → 战斗 → 结算(EXP/货币/掉落) → 完成任务奖励
        → 升级/获得装备/强化/成长 → 战力↑ → 更高级怪/副本/活动 → 循环
              ↑__________________________|
```

## 纪律

- 任何成长系统 **禁止自己算属性/战力**，必须收敛到 `AttributeService → PowerService`。
- 任何资产变动 **禁止绕过 CurrencyService/RewardService** 直接改余额。
- 任何奖励必须带 `reference_id` 防重（幂等）。
- 战力/战斗公式若原版未知 → 标 `JSTMCompatiblePowerFormula`/`INFERENCE`，留替换点。

[PHASE 0 — 依赖图完成]