# 第一只测试怪物（1.4.9）

> **目标 APK**：`anzbao/jstm.apk` / `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 1.4.11 未参与任何判定。
> 原则（用户 §10 明确要求）：**怪物 id / 名字 / 位置 / 数据来源全部要有据，
> 不自己创造 monster_id、monster_name、HP、攻击力、经验、金币。**

---

## 一、选定结论

| 项 | 值 | 来源 / 证据 |
|---|---|---|
| **monster_id（配置 id，bid）** | **20001** | `Config.Mon`（`assets/src/config/config_mon_data.luac`，2645 条之一） |
| **monster_name** | **戴浩** | 同上，`Config.Mon[20001][1]` |
| **res_id（外观资源）** | **H32000** | 同上，`Config.Mon[20001][8]` |
| 疑似等级 | 70 | `Config.Mon[20001][2]`（**`INFERRED`**，非确认字段） |
| **scene_id** | **10001**（史莱克城） | 当前角色所在场景；也是任务 10020 所在的主线场景 |
| **位置 (x, y)** | **仿真摆位**（当前配置 `(34,34)`） | ⚠ **不是原版坐标** —— 见 §三 |
| **HP / 攻击力 / 经验 / 金币** | **`UNKNOWN`** | `Config.Mon` 不含这些字段；原版服务端数据，APK 无取证途径 |
| 关联任务 | **10020**，条件 `fight_mon`，目标 `20001`，需要 **1/1** | `server/mission_config.json`（提取自 `config_mission.luac`） |

### 为什么选它

1. **它是第一条 `fight_mon` 主线任务的目标怪物。** 任务 10020 的条件就是
   「击杀 20001 × 1」，所以用它能同时验证
   **战斗闭环** 与 **战斗↔任务联动**（Phase D §19 的核心验证项）。
2. **它在 `Config.Mon` 里真实存在**，`name` 与 `res_id` 都能直读原版配置。
3. 它是**普通对话/挑战类怪物**（不是 Boss、不是多人、不是 PVP），符合
   §9「只需要怪物存在 → 可点击 → 可攻击 → 可扣血 → 可死亡 → 产生战斗结果」。

### 备选（同一条主线链上，均已确认存在于 `Config.Mon`）

| bid | name | res_id | 对应任务 | 条件 |
|---|---|---|---|---|
| 20002 | 男白虎 | R11000 | 10070 | fight_mon ×1 |
| 20022 | 男玄武 | R10100 | 10071 | fight_mon ×1 |
| 20040 | 叶夕水 | H30900 | 10072 | fight_mon ×1 |
| 20003 | 宁天 | H31900 | 10100 | fight_mon ×1 |

> `fight_mon` 类主线任务共 **38 条**（上一次统计），目标怪物 bid 全部落在
> `Config.Mon` 内。选 20001 只是因为它排在最前、覆盖最典型的链路。

---

## 二、`Config.Mon[20001]` 原始条目（1.4.9 APK 直读）

```
20001  {"bid": 20001, "name": "戴浩", "res_id": "H32000",
        "fields": [null, "戴浩", 70, 1, 0, 1, 0, 0, "H32000", 0, 0, 0,
                   "1", 0, 170, "", "E62931", null, 0, 0, "", 1, "", 0]}
```

字段索引含义见 `monster_data_model.md` §三：
只有 **[1]=name** 与 **[8]=res_id** 是**已确认**的；
**[2]=70 疑似 level** 标 `INFERRED`；其余 `UNKNOWN`，本阶段不使用。

---

## 三、★ 关于坐标：**必须如实标注**

原版「怪物摆在哪」的布置表**不在客户端 APK 里**：

| 候选数据源 | 实测结果 |
|---|---|
| `Config.Map[*].mons` | **全表为空**（上一阶段结论，本阶段复核一致） |
| `Config.MapMon` | 不存在该表 |
| `Config.Mon` | 只有定义，**无坐标** |

⇒ 因此本阶段下发到 `SC_10201.mons` 的坐标是
**「以场景声明的进入点为锚的仿真摆位」**，
配置项里明确带 `"source": "emulated"`，**不得对外表述为原版坐标**。

当前测试摆位（`server/config.json` 的 `mons[0]`）：

```json
{"id": 20001, "bid": 20001, "type": 0, "x": 34, "y": 34, "dir": 0,
 "source": "emulated",
 "why": "Phase D 测试怪：bid 20001 取自 1.4.9 Config.Mon（name/res_id 为原版），坐标是仿真摆位"}
```

其 `name` 与 `res_id` **由服务端从 `Config.Mon` 自动补齐**（`mon_def()`），
所以**名字和外观仍是原版数据**，只有坐标是仿真的。

---

## 四、实例 id 与配置 id 的区分（**实现时最容易错的一点**）

| 概念 | 字段 | 值 | 用途 |
|---|---|---|---|
| 配置 id | `bid` | 20001 | 查 `Config.Mon` 取名字/外观；任务条件比对 |
| **实例 id** | `id` | 20001（当前配置两者相同） | **`CS_20002.mon_id` 用的就是这个** |

依据：`battle_ctrl.luac` proto#3 `csFightMon` 的字节码是

```
proto = GameNet:getInstance():GetPrototype(20002)
proto.mon_id = <怪物 vo 的 id>        ← vo.id，不是 vo.bid
self:SendProtocal(proto)
```

且 `scene_model.luac` proto#28 `getMonster(id)` 就是 `monList[id]`
⇒ 服务端必须**记住自己下发的 `id`**，收到 `CS_20002.mon_id` 时按 `id` 反查。

---

## 五、本阶段**没有**做的事（诚实交代）

| 项 | 原因 |
|---|---|
| 没有编造 HP / 攻击力 / 经验 / 金币 | `Config.Mon` 无此数据；原版服务端数据不可得（见 `monster_data_model.md` §3.1） |
| 没有编造原版坐标 | 摆位表不在 APK 里 |
| 没有选用 Boss / 副本怪 / PVP | §9 明确排除 |
| 没有实现怪物 AI / 巡逻 | §9 明确排除（本阶段只要"存在→可点→可打→可死"） |
