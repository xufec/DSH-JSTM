# Phase 4 / Phase 5 接线实现计划

> 日期：2026-10-02
> 范围：**只读** `server/`；本文件是 Phase 4（Level/EXP/Attribute/Power 服务化）与 Phase 5（Monster/Battle/Reward）的接线蓝图。
> 依据：
> - `analysis/phase2_design.md` §四（统一服务接口草案）
> - `analysis/runtime_evidence/runtime_findings.md`（D1–D5 实机差异）
> - `analysis/runtime_evidence/calibration_R.md`（R1–R12 协议实值）
> - `analysis/runtime_evidence/calibration_V.md`（V1–V12 数值标定）
> - `analysis/server_capability_verified.md` §六 A 组（需 MuMu 取证系统）
> - `protocol/fields.json`（SC_10303 / SC_10304 / SC_10306 / SC_12901 字段规格）
>
> 纪律：不改 `server/` 任何文件；所有结论带行号锚点；数值类一律标 CONFIRMED / VERIFIED / INFERENCE / UNKNOWN。

---

## 〇、实机取证结论摘要（本计划的输入）

| # | 发现 | 等级 | 来源 | 对 Phase 4/5 的影响 |
|---|---|---|---|---|
| D1 | 综合战力 UI=0，但 10303 attr 数组有完整攻防血 | VERIFIED（差异） | `runtime_findings.md` §D1；`shots/20261002_003528_tap_attr2.png` | **Phase 4 头号修复项** |
| D3 | mon_hp=2400 / 伤害 784 / +30coin / 掉落 bid=33001 全是 mock_server TEST_ONLY 占位 | CONFIRMED（帧） | `calibration_V.md` V1/V3/V4/V5 | **Phase 5 核心**：数值替换路径 |
| D4 | gold=钻石(1799840) / coin=紫币(990万) / coupon=橙币(9999万) | VERIFIED | `calibration_V.md` §货币样本 | CurrencyService code↔名称映射定稿 |
| V9 | UI"综合战力: 0"，服务端 `role_power()` 算值从未下发到客户端 | VERIFIED（差异） | `calibration_V.md` §V9 | 战力回包缺口 |
| V10 | lv=70 经验条分母 exp_max=2,600,094（当前 exp=12,789） | VERIFIED（UI） | `calibration_V.md` §V10 | LevelService 经验表标定基准 |
| R5 | 10302 lev=70 exp=12789 gold=1799840 gold_acc=5000；10303 hp_max=4381 atk_s=789 | VERIFIED | `calibration_R.md` R5 | 四件套回归基线 |
| R9 | 20002→20010→20012/20013×4→20020→20023→20021 整场战斗链路通 | VERIFIED | `calibration_R.md` R9 | 战斗链路已验证，只换数值 |
| R8 | 12403 提交幂等 code=1（already committed） | CONFIRMED（帧） | `calibration_R.md` R8 | RewardService 幂等语义基线 |

---

## 一、Phase 4：Level / EXP / Attribute / Power 服务化

### 1.1 服务清单与落地任务分解

#### 1.1.1 `attribute/service.py`（AttributeService）

| 任务 | 文件/函数 | 数据源 | 依赖 | 验收 |
|---|---|---|---|---|
| A1. 建壳 | `server/attribute/service.py` `class AttributeService` | — | core/runtime | import 无错 |
| A2. 迁移 `role_attr_dict(cfg)` | L56–79 → `AttributeService.get_attr_dict(rid)` | ATTR_DEFAULTS(L45) + cfg['role_attrs'] + `db_role_attr(rid)`(L3447) | PersistenceService | 返回 dict 与 L56 逐键一致 |
| A3. 迁移 `attr_table_10304(ad)` | L99–106 → `get_attr_table_10304(rid)` | get_attr_dict | — | 字节与 L99 输出一致 |
| A4. 迁移 `attr_table_10306(ad)` | L109–120 → `get_attr_table_10306(rid)` | get_attr_dict | — | 字节与 L109 输出一致 |
| A5. 迁移 `db_get_attr/db_save_attr` | L4895–4932 → `AttributeService.load/save` | `role_attr` 表 (L4295) | PersistenceService | 读写一致 |
| A6. 新增 `apply_delta(rid, delta)` | **新函数**：成长系统（翅膀/时装/法宝…）追加属性加成写 `role_attr` | — | PersistenceService | 写后 get_attr_dict 可见 |
| A7. **修 D1 战力字段**（见 §1.2） | `build_10303` L5217 / `build_10304` / `build_10306` 改用 PowerService | — | PowerService | UI 综合战力 ≠ 0 |

#### 1.1.2 `power/service.py`（PowerService）

| 任务 | 文件/函数 | 数据源 | 依赖 | 验收 |
|---|---|---|---|---|
| P1. 建壳 | `server/power/service.py` `class PowerService` | — | AttributeService | import 无错 |
| P2. 包装 `power.py:calc_power` | `calc_power(attrs)` → `PowerService.calc_power(attrs)` | `server/power.py` L59（原版权重 `_attr_data.json`） | — | 返回 int，与 L82 `role_power()` 一致 |
| P3. 迁移 `role_power_of(rid)` | L2551–2561 → `PowerService.power_of(rid)` | AttributeService.get_attr_dict | AttributeService | 与 L2551 输出一致 |
| P4. 包装 `power_items(attrs, top_n)` | `server/power.py` L78 → `PowerService.power_items(rid, top_n)` | power.py | — | /DSH_ADMIN/power (L1067) 输出一致 |
| P5. **新增九维子战力**（见 §1.3） | `breakdown(rid)` → `{power_eqm_role, power_skill, power_xiulian, power_hero, power_ride, power_lingshou, power_shenqi, power_wing, power_fabao}` | SC_12901 规格 | 各成长 Service | 九维和 ≈ 总战力 |

#### 1.1.3 `level/service.py`（LevelService）

| 任务 | 文件/函数 | 数据源 | 依赖 | 验收 |
|---|---|---|---|---|
| L1. 建壳 | `server/level/service.py` | — | — | import 无错 |
| L2. 迁移 `level_table()` | L5661–5675 | `config.json` level 段 | ConfigService | 返回 dict 与 L5661 一致 |
| L3. 迁移 `level_need/level_next_total/level_attr_point` | L5685–5723 | level_table | — | 逐档返回一致 |
| L4. 迁移 `add_role_exp(cfg, rid, amount, apply_attr_growth=True)` | L5743–5784 | `roles.exp` / `roles.level` | PersistenceService, AttributeService | 加经验后 exp/level 正确；升级触发属性成长 |
| L5. 迁移 `apply_level_attr_growth(rid, ups)` | L5785–5804 | level_table | AttributeService | 升级后 role_attr 增长正确 |
| L6. **标定 exp_max**（V10） | lv=70 exp_max=2,600,094（VERIFIED UI） | `calibration_V.md` §V10 | ConfigService | `level_row(70)['exp_max']` = 2,600,094；10301 推送的 exp_max 与 UI 经验条分母一致 |

### 1.2 ★ D1 战力回包缺口的具体补法（Phase 4 头号修复）

#### 1.2.1 根因定位（CONFIRMED by code）

`build_10303(role, skills, attr)` 在 L5217–5220：

```python
for k in ('power', 'exp', 'gold', 'coin', 'gold_acc', 'sinew', 'experience',
          'coupon', 'vitality', 'guild_contrib', 'practice_exp',
          'tower_cent', 'arena_cent'):
    b += w_u32(role.get(k, 0))
```

- `power` 字段**确实在写**（spec 里 SC_10303 的第 17 个字段就是 `power:uint32`，见 `protocol/fields.json`）。
- **但值来自 `role.get('power', 0)`**，而 `role` 是 `cfg['role']`（config.json L60 `"power": 0`）——**永远是 0**。
- 对比：`role_power(cfg)` (L82) 和 `role_power_of(rid)` (L2551) 明明会调 `power_mod.calc_power(a)` 算出真实战力，但**这两个函数的结果从未被塞进 `role` dict 传给 `build_10303`**。

**结论（INFERENCE，高置信）**：客户端读 10303 的 `power` 字段就是 0，所以"综合战力"显示 0。修复 = 在 `build_10303` / `build_10304` / `build_10306` 里，把 `power` 从 `role.get('power', 0)` 改为 `PowerService.power_of(rid)`。

#### 1.2.2 客户端期待哪些字段才能显示战力

按 `protocol/fields.json`：

| 命令 | power 字段位置 | 客户端用途 |
|---|---|---|
| **SC_10303** | 第 17 个字段（skill_list 之后、exp 之前），`uint32` | 角色属性面板"综合战力"主显示 |
| **SC_10304** | 同 10303 位置，`uint32` | 角色详情/战斗前展示的战力 |
| **SC_10306** | attr 表 + mspd 之后，`uint32` | 属性对比面板的战力 |
| **SC_12901** | `rank_role` 子表 9 个 `uint32`：`power_eqm_role / power_skill / power_xiulian / power_hero / power_ride / power_lingshou / power_shenqi / power_wing / power_fabao` | 战力榜分项展示 + 总和排序 |
| **SC_10301** | **无 power 字段**（spec 里没有） | — |
| **SC_10302** | **无 power 字段**（spec 里没有） | — |

> INFERENCE：客户端"综合战力"= 10303.power。九维子战力（12901.rank_role）是战力榜的分项明细，主面板只显示总和。

#### 1.2.3 修复任务（P0，最小改动）

```python
# 在 build_10303(role, skills, attr) 里，L5217 的循环之前插入：
_rid = role.get('rid', 1001)
_real_power = power_service.power_of(_rid)   # 新：调 PowerService
role = dict(role, power=_real_power)           # 覆盖 config 里的 0
# 然后原循环照常 w_u32(role.get(k, 0))
```

同样改动套用到 `build_10304`（L5162 附近）和 `build_10306`。

#### 1.2.4 验收

1. 改完重启 server，MuMu 实机进属性面板（`shots/20261002_003528_tap_attr2.png` 同屏），"综合战力"应显示**非 0 整数**。
2. 对比 `role_power(cfg)` 服务端日志值 vs UI 显示值，应一致（VERIFIED 目标）。
3. 脱一件装备（/DSH_ADMIN/unequip），UI 战力应下降；穿回去应回升（V6 单件差值反推）。
4. 12901 战力榜的 `my_val` 应等于 10303.power。

### 1.3 九维子战力（P5）落地

SC_12901 的 `rank_role` 子表要求 9 个分项战力。当前 mock_server 没有分项计算。Phase 4 接线策略：

| 分项 | 数据源（现状） | Phase 4 处理 |
|---|---|---|
| `power_eqm_role` | `equip_items` 表 + 装备属性 | 暂用 `PowerService.power_of(rid) * 0.5`（INFERENCE 占位） |
| `power_skill` | 技能系统（UNKNOWN，*Capability* #13） | 0（UNKNOWN 系统不编造） |
| `power_xiulian` | 修炼系统（UNKNOWN） | 0 |
| `power_hero` | `role_heros` 表 + `_partner_base.json` | 暂用伙伴数量 × 系数（INFERENCE） |
| `power_ride` | `role_ride` 表 | 暂用 ride jie×lev 系数（INFERENCE） |
| `power_lingshou` | `role_lingshou` 表 | 暂用 lingshou jie×lev 系数（INFERENCE） |
| `power_shenqi` | `role_shenqi` 表 | 暂用 shenqi lev×star 系数（INFERENCE） |
| `power_wing` | `role_wing` 表 | 暂用 wing star×color 系数（INFERENCE） |
| `power_fabao` | `role_fabao` 表 | 暂用 fabao level×stage 系数（INFERENCE） |

> **纪律**：九维分项标 INFERENCE，等 MuMu 取证 V8/V11（伙伴/翅膀每阶属性）后替换为真值。Phase 4 只要求"九维和 ≈ 总战力"且不报错。

---

## 二、Phase 5：Monster / Battle / Reward 接线

### 2.1 现状（D3 / V1–V5 实机确认）

| 项 | 实机值 | 来源 | 代码位置 | 状态 |
|---|---|---|---|---|
| 怪物 HP | mon=20001 戴浩 hp_max=2400 | tcp.log L1169 | `battle.py` L104 `MON_STATS` | TEST_ONLY 占位 |
| 怪物攻击 | 怪→玩家伤害=1/次 | tcp.log L1178–1214 | `battle.py` L127 `calc_damage` | TEST_ONLY |
| 玩家伤害 | 784/次（物攻 789 - 怪微量防御） | tcp.log L1178–1214 | `battle.py` L127 | INFERENCE 简化模型 |
| 击杀经验 | +50 exp（12789→12839） | tcp.log L1234 | `battle.py` L111 `KILL_REWARD` | TEST_ONLY |
| 击杀金币 | +30 coin | tcp.log L1234 | `battle.py` L111 | TEST_ONLY |
| 掉落 | bid=33001 VIP2每日礼包 x1 | tcp.log L1236 | `battle.py` L117 `FALLBACK_DROPS` | TEST_ONLY |
| 原版掉落 | bid=51037 李逍遥灵魂玉（物品不存在被丢弃） | tcp.log L1235 日志 | `drop_cfg()` L5805 | 配置引用了不存在的 bid |

### 2.2 配置源盘点（1.4.11 反构造）

| 配置文件 | 大小 | 内容 | 可用性 |
|---|---|---|---|
| `cfg/config_mon_data.json` | 311 B | `{"Config": {"Mon": {}, "MonData": {}, "data": {}, "Filter": {...}}}` | **几乎空**——Mon/MonData/data 都是空 dict；只有 Filter 有数组 |
| `cfg/config_battle.json` | 158 B | `FightType: {MISS:0, HIT:1, BAOJI:2}` | 只有结果枚举，无公式 |
| `cfg/config_fight.json` | 1,450 B | 未读 | 待查 |
| `cfg/config_demon.json` | 5,671 B | 未读（BOSS/爬塔怪） | 待查 |
| `cfg/config_dungeon_*.json` | 多个 | 副本怪配置 | 待查 |

**结论（CONFIRMED）**：原版怪物数值数据**尚未从 1.4.11 APK 反构造出来**。`config_mon_data.json` 的 `Mon`/`MonData`/`data` 三个核心 dict 都是空的，说明提取脚本只拿到了壳。

### 2.3 数值替换路径（从 TEST_ONLY 到配置驱动真值）

#### 2.3.1 三层数据模型

```
Layer 1: 配置真值（唯一来源）
  cfg/config_mon_data.json   ← Mon[mon_id] = {hp, atk, def, speed, ...}
  cfg/config_battle.json     ← 伤害公式系数（暴击率/抗暴/命中/躲闪）
  cfg/config_demon.json      ← BOSS/爬塔怪覆盖值

Layer 2: Service 读取层
  monster/service.py  MonsterService.get_mon(mon_id) -> dict
  battle/formula.py   BattleFormula.calc_damage(atk, def, crit, hit, ...)
  battle/reward.py    KillRewardService.roll(mon_id) -> {exp, coin, drops[]}

Layer 3: 调用层（现状）
  battle.py  MON_STATS / KILL_REWARD / FALLBACK_DROPS  ← Phase 5 改为从 Layer 2 读
```

#### 2.3.2 任务分解

##### `monster/service.py`（MonsterService）

| 任务 | 说明 | 数据源 | 验收 |
|---|---|---|---|
| M1. 建壳 | `class MonsterService` | — | import 无错 |
| M2. 迁移 `mon_cfg/mon_def/static_mons` | L4465–4515 | `config.json` mon 段 | 返回 dict 与 L4465 一致 |
| M3. **新增 `get_mon(mon_id)`** | 从 `config_mon_data.json` 的 `Mon` dict 读；未命中时 fallback 到 `MON_STATS` 占位 | `cfg/config_mon_data.json` M2 | 返回 `{hp_max, atk, def, speed, ...}` |
| M4. 迁移 `scene_mons(cfg, scene_id)` | L4585–4639 | M3 + `map_cfg()` | 场景怪列表与 L4585 一致 |
| M5. 迁移 `boss_cfg/boss_rows` | L7028–7073 | `config_demon.json` | BOSS 列表一致 |

##### `battle/formula.py`（BattleFormula）

| 任务 | 说明 | 数据源 | 验收 |
|---|---|---|---|
| F1. 建壳 | 包装 `battle.py` L127 `calc_damage` | — | 返回值与现状一致 |
| F2. **新增暴击/命中/躲闪判定** | V2 实机：面板暴击113/抗暴90/命中337/躲闪226；实战 4 击全 784 无暴击（样本不足） | `config_battle.json` FightType hash | 按属性百分比 roll，结果 ∈ {MISS, HIT, BAOJI} |
| F3. **替换 `calc_damage` 公式** | 现状 INFERENCE: `dmg = atk - def`；目标：从 `config_battle.json` 读系数（待提取） | `config_battle.json` | 多场战斗回归后 dmg 分布合理 |

##### `battle/reward.py`（KillRewardService）

| 任务 | 说明 | 数据源 | 验收 |
|---|---|---|---|
| R1. 建壳 | 包装 `battle.py` L111 `KILL_REWARD` | — | 返回值与现状一致 |
| R2. **迁移 `roll_drops(mon_bid)`** | L5821–5884 | `drop_cfg()` L5805 + `config_drop.json` | 掉落列表与 L5821 一致 |
| R3. **修"原版掉落 bid=51037 不存在"** | tcp.log L1235 日志：`原版掉落表引用不存在物品(51037 李逍遥灵魂玉)，已丢弃` | `item_config.json` 3535 件 | 掉落 roll 时过滤掉 `is_valid_item(bid)==False` 的 bid |
| R4. 幂等：`grant(rid, rewards, reference_id)` | 接 RewardService.grant（phase2_design §4.2） | `reward_log` 表 | 重发同 reference_id 不重复发奖 |

### 2.4 配置提取待办（Phase 5 前置阻塞项）

> ⚠ `config_mon_data.json` 现在是空壳。要拿到真值，必须先做配置提取：

| # | 待办 | 工具 | 产出 |
|---|---|---|---|
| E1 | 从 1.4.11 APK 的 `config_mon.luac` 提取 Mon/MonData 表 | `tools/extract_*.py` 系列 | 填充 `config_mon_data.json` 的 `Mon` / `MonData` / `data` dict |
| E2 | 从 `config_battle.luac` 提取伤害公式系数 | 同上 | 填充 `config_battle.json` 的公式段 |
| E3 | 读 `config_fight.json` (1450B) 确认内容 | 直接 Read | 记录是否为技能/战斗参数 |
| E4 | 读 `config_demon.json` (5671B) 确认 BOSS 数值 | 直接 Read | BOSS 数值标定 |

> **在 E1/E2 完成前，Phase 5 只能做到"链路接线 + TEST_ONLY 值替换为 Service 调用"，数值仍是占位**。E1/E2 完成后，单点替换 `MonsterService.get_mon` 的数据源即可切换真值，无需改 handler。

---

## 三、RewardService 接线（Phase 5 核心）

### 3.1 现状

- `decode_award_assets(award_assets)` (L4164)：解析任务奖励串。
- `db_add_assets(rid, delta)` (L4338)：加货币。
- `db_bag_add(rid, bid, quantity)` (L5911)：加物品。
- 三者**散落**，没有统一入口；重发 12403 会重复发奖（R8 实机观察到"already committed"但服务端是靠 mission_status=3 挡的，不是幂等键）。

### 3.2 RewardService.grant 接口

```python
class RewardService:
    def grant(self, rid: int, awards: list, reference_id: str, source: str = '') -> dict:
        """
        awards = [
            {'type': 'asset', 'code': 'gold', 'num': 100},
            {'type': 'item', 'bid': 33001, 'num': 1},
            {'type': 'exp', 'num': 50},
        ]
        reference_id = 幂等键（如 'mission-10020-rid1001'）
        返回 {'granted': [...], 'skipped': [...]}
        """
```

### 3.3 接入点

| 触发点 | 现函数 | 改后 |
|---|---|---|
| 任务提交 12403 | L15615 `if cmd == 12403` 里直接调 `db_add_assets` / `db_bag_add` | 改调 `RewardService.grant(rid, awards, reference_id=f'mission-{mission_bid}-{rid}')` |
| 击杀结算 20023 | `_battle_settle` (L9460) 里 `KILL_REWARD` 直接加 | 改调 `RewardService.grant(rid, kill_rewards, reference_id=f'battle-{battle_uuid}')` |
| 商城购买 12805 | `shop_try_buy` (L4070) | 改调 `RewardService.grant` 发货 |
| GM /DSH_ADMIN/giveitem | L1175 | 改调 `RewardService.grant`，reference_id 必须带 `gm-` 前缀 |

### 3.4 幂等表（新建）

```sql
CREATE TABLE IF NOT EXISTS reward_log (
    rid INTEGER,
    reference_id TEXT,
    reward_json TEXT,
    granted_at INTEGER,
    PRIMARY KEY (rid, reference_id)
);
```

---

## 四、验收标准（与 runtime_evidence 实值对齐）

### 4.1 Phase 4 验收

| # | 验收项 | 基线（实机值） | 通过标准 |
|---|---|---|---|
| A-V1 | 综合战力 UI | = 0（D1） | **≠ 0**，且 ≈ `role_power_of(1001)` 服务端日志值（VERIFIED） |
| A-V2 | 10303 attr 数组 | hp_max=4381 atk_s=789（R5） | 字节级 diff 为空（power 字段除外，从 0 变为真值） |
| A-V3 | 10302 货币 | gold=1799840 coin=9904599（D4） | 不变（CurrencyService 不改语义） |
| A-V4 | 经验条分母 | exp_max=2,600,094 @lv70（V10） | 10301.exp_max = 2,600,094 |
| A-V5 | 升级加属性 | /DSH_ADMIN/setlevel 后 | 10303 attr 数组按 level_table 增长 |
| A-V6 | miniloop 自检 | 145/145 PASS | 不回退 |

### 4.2 Phase 5 验收

| # | 验收项 | 基线（实机值） | 通过标准 |
|---|---|---|---|
| B-V1 | 战斗链路 | 20002→20010→20012/20013×4→20020→20023→20021（R9） | 帧序列不变 |
| B-V2 | 战斗数值 | mon_hp=2400 dmg=784 +30coin（D3） | **链路通但数值仍标 TEST_ONLY**（等 E1/E2 配置提取后替换） |
| B-V3 | 掉落 | bid=33001 x1（V5） | 链路通；bid=51037 不存在 bid 被过滤（R3 修复） |
| B-V4 | 任务提交幂等 | 12403 code=1 already committed（R8） | 重发同 reference_id 返回相同结果，不重复发奖 |
| B-V5 | reward_log 表 | 新建 | 每次 grant 落一行；重复 grant 命中主键冲突 |
| B-V6 | miniloop 自检 | 145/145 PASS | 不回退 |

---

## 五、风险与边界

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | `build_10303` 改 power 字段后，字节长度变化可能导致客户端解析错位 | 高 | power 是 uint32，位置不变，只是值变；长度不变。改完先跑 miniloop 145 自检，再实机 |
| 2 | 九维子战力用 INFERENCE 系数凑数，可能被误读为"已实现" | 中 | 九维字段在代码里标 `# INFERENCE: placeholder, see V8/V11`；GM /status 里注明 |
| 3 | `config_mon_data.json` 空壳，E1/E2 提取未做 | 高 | Phase 5 接线完成后，数值仍是 TEST_ONLY；文档明确标注"链路通，数值待提取" |
| 4 | 暴击/命中/躲闪公式从 INFERENCE 改为配置驱动时，V2 实机 4 击全 784 无暴击样本不足 | 中 | 多跑几场战斗统计；V2 标 INFERENCE（实战未触发暴击样本） |
| 5 | RewardService 幂等表 `reward_log` 新建，但老数据（已发奖的 mission_bid）没有 reference_id 记录 | 低 | 老任务重发仍靠 mission_status=3 挡；新任务提交才走幂等键 |

---

## 六、Phase 4/5 边界声明

**本轮做**：
- AttributeService / PowerService / LevelService / MonsterService / BattleFormula / KillRewardService / RewardService 的接线。
- 修 D1 战力 UI=0（改 `build_10303/10304/10306` 的 power 字段来源）。
- 建 `reward_log` 幂等表。

**本轮不做**：
- 不提取 `config_mon_data.json` 真值（E1/E2 是独立前置任务）。
- 不替换 TEST_ONLY 战斗数值（等配置提取完成）。
- 不实现技能学习/升级（UNKNOWN，*Capability* #13）。
- 不调整协议字段顺序、不改命令号。

---

*计划完。所有行号基于 2026-10-02 快照的 `server/mock_server.py`（18,506 行）；实机证据来自 `analysis/runtime_evidence/`（2026-10-02 00:25–00:39 MuMu 取证）。*
