# 4 个 UNKNOWN 真值缺口深度检索报告

> 日期：2026-10-02 | 第一阶段：配置/Lua 静态检索 | 未修改 server/，未碰模拟器

---

## 总览

| 缺口 | 结论 | 证据等级 | 找到真值？ |
|---|---|---|---|
| G1 技能学习/升级消耗 | ✅ 全套真值已提取 | CONFIRMED | 是 |
| G2 伙伴培养消耗 | ⚠️ 部分找到（神器/符咒/羁绊有，基础喂养无） | CONFIRMED (部分) | 部分 |
| G3 宝石属性加成 | ⚠️ 合成消耗有，属性加成无 | CONFIRMED (部分) | 部分 |
| G4 怪物 HP/ATK | ❌ 配置表中无基础属性值 | UNKNOWN | 否 |

---

## G1. 技能学习/升级消耗 ✅ CONFIRMED

### 数据源
- `config_skill.json` → Config.SkillPoint（技能点金币成本）
- `config_skill_xiulian.json` → SkillXiulianLearn + SkillXiulianUp + SkillXiulianLev（修炼技能）

### 提取到的真值

**技能点金币成本（SkillPoint）**

| 技能点等级 | 金币消耗 |
|---:|---:|
| L1 | 10 |
| L2 | 20 |
| L5 | 50 |
| L10 | 100 |

> 递增规律：每点 +10g，共 10 个技能点等级。

**修炼技能学习消耗（SkillXiulianLearn，8个技能）**

| 技能 | bid | 学习经验 | 金币 | 最大等级 |
|---|---:|---:|---:|---:|
| 攻击修炼 | 10101 | 86 | 0 | 23 |
| 物防修炼 | 10201 | 43 | 0 | 23 |
| 法防修炼 | 10301 | 43 | 0 | 23 |
| 其余5个 | 10401~10801 | 43~86 | 0 | 23 |

> 修炼技能学习消耗修炼经验，金币为 0。

**修炼技能升级消耗（SkillXiulianUp，192级）**

| 等级 | 经验消耗 | 下一级 bid |
|---:|---:|---:|
| L1→L2 | 402 | 10102 |
| L2→L3 | 852 | 10103 |

> 经验消耗呈增长曲线，192 条完整数据。

**等级解锁门槛（SkillXiulianLev）**

| 修炼等级 | 角色等级要求 |
|---:|---|
| 1~4 | Lv1+ |
| 5 | Lv22~32 |
| 6 | Lv30~40 |
| 7 | Lv35~45 |
| 8 | Lv40~50 |

### 替换计划
替换 mock_server 中技能消耗占位：
- 技能点金币 → config_skill.json SkillPoint
- 修炼经验消耗 → SkillXiulianLearn（学习）+ SkillXiulianUp（升级）

---

## G2. 伙伴培养消耗 ⚠️ 部分 CONFIRMED

### 找到的真值

**羁绊/洗练经验系数（FetterConst）**

| 参数 | 值 | 说明 |
|---|---:|---|
| exp_ratio | 600 | 经验比率 |
| default_exp1 | 20 | 默认经验1 |
| default_exp2 | 10 | 默认经验2 |
| upstar_exp | 5 | 升星经验 |

**伙伴符咒消耗（PartnerTalismanCost）**

| 等级 | hc_cost |
|---:|---:|
| L1 | 10,000 |
| L2 | 20,000 |
| L3 | 30,000 |
| L4 | 40,000 |

**伙伴神器消耗（PartnerShenqi）**

| 等级 | 金币 |
|---:|---:|
| L1 | 2,400 |
| L2 | 4,400 |
| L3 | 6,400 |
| L4 | 12,000 |
| L5 | 18,000 |

> 模式与装备强化一致（递增曲线）。

### 未找到

**基础伙伴喂养消耗（FEED_GOLD=1000 / FEED_EXP=500）**
- 配置表中无此单项数值
- 伙伴经验主要通过经验书、任务、练功房获得
- 单次喂养消耗可能在服务端硬编码

### 替换计划
- 伙伴神器/符咒/羁绊消耗 → 替换为配置真值
- 基础喂养消耗 → 保持 INFERENCE

---

## G3. 宝石属性加成 ⚠️ 部分 CONFIRMED

### 找到的真值

**宝石物品存在性**
- 80 个宝石类物品（type=11），分 5 个等级（一级~五级物攻石等）
- 物品 field[13] = "dazao|xiangqian"（打造|镶嵌）标记

**宝石合成消耗（ItemRoleFuse，192条）**

| 合成配方 | 金币消耗 | 成功率 | 产出 |
|---|---:|---:|---|
| 36546 合成 | 2,000 | 100% | 38005×4 |
| 36545 合成 | 3,000 | 100% | 38010×4 |
| 42041 合成 | 4,000 | 100% | 38015×4 |

### 未找到

**宝石镶嵌属性加成数值**
- 宝石物品表（config_item.json）中无 atk_s/def/hp 等属性字段
- ItemJewel 表 17 条均为 null（反构造不完整）
- 无独立的镶嵌属性配置表（config_inlay/config_jewel_attr 不存在）
- 属性加成可能由镶嵌系统公式计算，或在未提取的 luac 表中

### 替换计划
- 宝石合成消耗 → 替换为 config_item_fuse.json 真值
- 宝石属性加成 → 保持 INFERENCE，需后续查镶嵌系统

---

## G4. 怪物 HP/ATK ❌ UNKNOWN

### 检索过程

| 检查项 | 结果 |
|---|---|
| config_mon_data.luac (1.4.11) | 857KB，反构造主表空（Mon/MonData 均为 {}） |
| config_role_attr.json (200级) | 仅含 exp_max/exp_total/attr_point/sinew，**无基础 HP/ATK** |
| config_attr.json | 仅含属性 ID 映射 + AttrPower 战力系数，**无等级基础值表** |
| config_mon_base / config_mon_attr | **不存在** |
| 1.4.9 config_mon.json (2645怪) | 确认无显式 HP/ATK 字段（仅有元数据+scale系数） |

### 结论

**怪物 HP/ATK 真值 UNKNOWN**：配置表中无等级基础属性值，战斗数值由服务端公式计算（公式不在配置中）。

公式模型（INFERENCE）：
```
实际HP = 等级基础值(level) × 类型倍率(type) × 缩放系数(scale[field_21])
```
- 系数 scale[field_21]：CONFIRMED（0.7x ~ 15x，每怪独立）
- 等级基础值表：UNKNOWN（配置中不存在）
- 类型倍率：UNKNOWN（配置中不存在）

### 替换计划
保持 INFERENCE 占位，标注"需 MuMu 运行时取证或服务端代码反编译"。

---

## 附带发现

| 项 | 内容 | 来源 |
|---|---|---|
| 修炼笔记经验 | 使用修炼笔记可获得 **600点** 修炼经验 | config_promote.json 文案确认 |
| 挂机双倍 | 野外挂机可领取双倍点数加速 | config_promote.json |
| 伙伴经验书 | 伙伴主要经验来源为经验书/任务 | config_promote.json |

---

## 证据等级分布

| 等级 | 数量 | 内容 |
|---|---:|---|
| **CONFIRMED** | 3项部分 | 技能消耗全套、伙伴神器/符咒消耗、宝石合成消耗 |
| **INFERENCE** | 2项 | 伙伴基础喂养消耗、宝石镶嵌属性加成 |
| **UNKNOWN** | 1项 | 怪物 HP/ATK 实际值 |

---

## 附：MuMu UI 运行时取证结论（第二阶段）

> 日期：2026-10-02 | 设备：MuMu adb 127.0.0.1:16384 | 详见 `ui_display_values.md`

### G1 技能消耗 — UI 交叉验证

| 项目 | 配置真值 | UI 显示 | 结论 |
|---|---|---|---|
| 技能列表状态 | — | 全部"可学习" | UI_DISPLAY ✅ |
| 技能点金币消耗 | L1=10g→L10=100g | 消耗栏显示"0" | ⚠️ UI未体现配置值（服务端未下发） |
| 修炼消耗栏 | L1=402exp起 | **空白空条** | ⚠️ mock_server 未下发修炼经验 |
| 修炼进度 | — | 抗控修炼 LV.22, 35/50 | UI_DISPLAY ✅ |

**结论**：技能面板框架正常，但修炼经验数值未从服务端下发到客户端。配置表的消耗真值保持 CONFIRMED，UI 差异记录为"数据下发缺失"。

### G2 伙伴培养 — UI 部分验证

| 项目 | UI 显示 | 结论 |
|---|---|---|
| 伙伴资质范围 | 物攻1010-1550 等 | UI_DISPLAY ✅ 与配置一致 |
| 伙伴技能 | 火龙吐息/火柱/保命 | UI_DISPLAY ✅ |
| 培养/喂养 UI | **不可见**（角色未拥有伙伴） | ❌ 需先获得伙伴 |

**结论**：伙伴面板数据正确，但培养消耗 UI 无法验证（无已拥有伙伴）。

### G3 宝石镶嵌 — UI 未访问

未导航到锻造面板，镶嵌 UI 显示值待后续采集。保持 INFERENCE。

### G4 怪物数值 — 战斗未触发

尝试主线任务点击、挂机自动巡逻均未进入战斗场景。怪物血条/伤害数字/击杀奖励 UI 证据**未能采集**。保持 UNKNOWN。

---

**server/ 目录未做任何修改。GM 基线完好（lv70/gold=1,799,840/coin=9,904,569）。**

---

## 第三批：配置侧静态深挖（2026-10-02）

### G2 伙伴基础喂养消耗 — 继续深挖结论

**检索范围**：config_partner_base.json（PartnerLevUp/PartnerModeAttr/PartnerBase/PartnerConstant/PartnerVolume/PartnerWash/PartnerBYRate）+ config_partner_misc.json（PartnerTalismanCost/PartnerFoster/PartnerGratis/PartnerStageCost/PartnerRebirthCost）

**结论：仍 UNKNOWN**

| 发现 | 说明 |
|---|---|
| PartnerFoster | 仅为可喂养伙伴 ID 列表（hash 映射 bid→bid），**无消耗数值** |
| PartnerVolume | 伙伴背包格子解锁费用（12→100金），非喂养消耗 |
| PartnerConstant | 含 lev_max=200/exp_max=1908497990/挂机寿命损耗等常量，**无单次喂养消耗字段** |
| PartnerStageCost | 伙伴进阶消耗道具（36572等），非喂养金币 |

**已检索全部 partner 配置表，未发现"单次喂养金币/经验消耗"字段。** 推测喂养消耗由客户端硬编码或在服务端逻辑中，配置表无显式值。

---

### G3 宝石镶嵌属性加成 — 继续深挖结论

**检索范围**：config_item.json（ItemJewel）+ config_item_misc.json（EqmJewel）+ config_item_misc_attr.json（ItemMiscAttrJewel）

**新发现：CONFIRMED 部分属性**

| 表 | 内容 | 证据等级 |
|---|---|---|
| config_item.json ItemJewel | 17 条全 None（反构造失败） | UNKNOWN |
| config_item_misc.json EqmJewel | 13 条：装备等级解锁宝石槽（eqm_lev/groove/jewel_lev） | CONFIRMED |
| config_item_misc_attr.json ItemMiscAttrJewel | 8 级宝石属性表（3-10级），含 atk_s/atk_p/hp_max/def/暴击等 | **CONFIRMED** |

**宝石物品清单（config_item.json type 11-20）**：
- 8 类宝石：物攻石(11)/法攻石(12)/物防石(13)/法防石(14)/气血石(15)/速度石(16)/暴击石(19)/抗暴石(20)
- 每类 5 级（1-5级），共 40 个宝石物品
- 功能字段：`dazao|xiangqian`（锻造+镶嵌）

**ItemMiscAttrJewel 属性表（摘要）**：

| 等级 | 槽位数 | atk_s | atk_p | hp_max | def_s | def_p | 暴击 | 速度 |
|---|---|---|---|---|---|---|---|---|
| 3 | 12 | 140 | 140 | 700 | 99 | 99 | 31 | — |
| 5 | 18 | 359 | 359 | 1,795 | 253 | 253 | 79 | 10 |
| 7 | 24 | 724 | 724 | 3,620 | 510 | 510 | 159 | 25 |
| 10 | 24 | 1,381 | 1,381 | 6,907 | 973 | 973 | 304 | 70 |

> 注：此为**整套宝石镶嵌后总属性**（24槽满），非单个宝石属性。单个宝石属性 = 总值 / 槽位数。

**结论**：
- 宝石物品存在（40个，8类×5级） ✅ CONFIRMED
- 镶嵌后总属性表存在（ItemMiscAttrJewel） ✅ CONFIRMED
- 单个宝石具体属性值（每级每类）：由总值推算 INFERENCE
- ItemJewel 表反构造失败：单个宝石→属性映射 UNKNOWN

---

### 证据等级更新

| 等级 | 数量 | 变化 |
|---|---:|---|
| CONFIRMED | 5项 | +宝石物品清单、+宝石总属性表 |
| INFERENCE | 2项 | 单个宝石属性值（由总值推算） |
| UNKNOWN | 2项 | 伙伴基础喂养消耗、怪物 HP/ATK |

---

## 追加：装备链静态配置定位

> 日期：2026-10-02 | 方法：config_intensify + config_item 交叉检索

### 1. 武器升级材料 bid

| 材料 | item bid | 来源表 | 证据等级 |
|---|---:|---|---|
| 30打造石 | **13001** | config_item.json ItemData | **CONFIRMED** |
| 30玄武图纸 | **46022** | config_item.json ItemData | **CONFIRMED** |

**UpgradeConfig 升级配置（武器 type=100）**：
- L20→L30：coin=58,850 + item_list1=[13001×1]
- L30→L40：coin=86,900 + item_list1=[13005×1] + item_list4=[36040×1]

---

### 2. 武器基础属性表

**结论：未找到独立的武器基础属性配置表**

已检索：
- config_eqm_ancient.json（古代装备，非基础武器）
- config_eqm_starup_data.json（装备升星）
- config_red_eqm.json（血红装备）
- config_item.json ItemData（物品表，无 atk/def/hit 字段）

UI 显示：
- 秘银长枪 L20：物攻0/法攻0/命中0
- 黄金长枪 L30：物攻213/法攻213/命中69

**推测**：武器属性由客户端从等级公式计算，或在未反构造成功的配置表中。标 UNKNOWN。

---

### 3. 伙伴配置速查

| 项 | 值 | 来源 |
|---|---|---|
| 首个伙伴 bid | **35700** | config_partner_base.json PartnerBase |
| 首个伙伴名 | 唐舞桐 | PartnerBase[35700].name |
| 伙伴总数 | 53 个 | PartnerBase 条目数 |

---

### 证据等级

| 项 | 等级 |
|---|---|
| 30打造石 bid=13001 | CONFIRMED |
| 30玄武图纸 bid=46022 | CONFIRMED |
| 武器基础属性表 | UNKNOWN（未找到独立表） |
| 首个伙伴 bid=35700 | CONFIRMED |
