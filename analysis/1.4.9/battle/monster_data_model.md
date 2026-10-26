# 1.4.9 怪物数据模型

> **目标 APK**：`anzbao/jstm.apk` / `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 1.4.11 未参与任何判定。
> 本文只写**APK 里实际存在**的字段；APK 里没有的，明确标 `UNKNOWN` 或
> 「原版服务端数据，APK 无取证途径」。

---

## 一、结论速览

| 问题 | 结论 | 证据 |
|---|---|---|
| 怪物的**外观/名字/等级类**数据来自哪？ | **客户端静态配置** `Config.Mon`（2645 条） | `assets/src/config/config_mon_data.luac` |
| 怪物的**摆位/坐标**来自哪？ | **服务端**下发 | `SC_10201.mons` / `SC_10212`；`Config.Map[*].mons` 实测**全表为空** |
| 怪物的 **HP / 攻击力 / 防御 / 经验 / 金币**来自哪？ | **不在客户端配置里** ⇒ 原版服务端数据，本阶段 `UNKNOWN` | `Config.Mon` 23 个字段**无一个是 HP/ATK/EXP/GOLD**（见 §三） |
| 怪物的**实例 id** 是什么？ | 服务端下发时指定的 `id`（≠ 配置 id `bid`） | `SC_10201.mons.id` / `CS_20002.mon_id` |
| 客户端点怪时发的是哪个 id？ | **`vo.id`（实例 id）** | `battle_ctrl.luac` proto#3 `csFightMon`：`proto.mon_id = vo.id` |

---

## 二、服务端下发的怪物结构（协议侧，权威）

`SC_10201.mons`（`cmd_resolve_102.luac` 内联 spec，经 `tools/proto_spec.py cmds 10201` 复核）：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | uint32 | **场景内实例 id** —— `CS_20002.mon_id` 用的就是它 |
| bid | uint32 | 配置 id（对应 `Config.Mon[bid]`） |
| type | uint8 | 类型（取值语义 `UNKNOWN`） |
| name | string | 显示名（服务端下发；客户端也可用 `Config.Mon` 覆盖） |
| realm | uint8 | 境界/等阶（语义 `UNKNOWN`） |
| mspd | uint16 | 移动速度 |
| x | uint16 | 坐标 x |
| y | uint16 | 坐标 y |
| dir | uint8 | 朝向 |
| res_id | string | **外观资源 id**（如 `H32000`） |
| status | uint8 | 状态（`SC_10214` 可单独改） |

单独推送（`cmd_resolve_102.luac`）：

| CMD | 用途 | 差异 |
|---|---|---|
| 10212 | 附近有 MON 进入场景 | 同 10201.mons，**多一个 `enter_effect:uint8`** |
| 10213 | MON 移动 | `id, x, y` |
| 10214 | MON 状态改变 | `id, status` |
| 10215 | 有 Mon 离开场景 | `id` |
| 10220 | 删除角色、MON | `mon_ids:table(id:uint32)`, `role_ids` |
| 10221 | 获取当前场景所有怪物坐标（挂机用） | 响应 `mons:table(id, bid, x, y)`；**CS 为空消息** |

---

## 三、客户端静态配置 `Config.Mon`（1.4.9 APK 实测）

**来源**：`assets/src/config/config_mon_data.luac`（857 KB），
由 `tools/extract_config_mon.py` 提取为 `analysis/1.4.9/task/config_mon.json`。
**条目数：2645。**

每条是一个 **23 元素数组**（索引 1..23；索引 0 为 `nil`）。字段分布实测如下
（对全部 2645 条做统计，`distinct` = 不同取值个数）：

| 索引 | 类型 | distinct | 取值范围示例 | 判断 |
|---|---|---|---|---|
| 0 | `nil` | 1 | — | 占位 |
| **1** | string | 601 | 蓝银圣女／圣灵教法师／冥雷斗罗 | **`name` 名字**（已确认） |
| 2 | int | 111 | 1..150 | **疑似 `level` 等级**（`INFERRED`，见 §四） |
| 3 | int | 3 | 0, 1, 4 | `UNKNOWN` |
| 4 | int | 24 | 0..255 | `UNKNOWN` |
| 5 | int | 5 | 0..4 | `UNKNOWN` |
| 6 | int | 5 | 0..254 | `UNKNOWN` |
| 7 | int | 1 | 0 | 恒 0 |
| **8** | string | 173 | H31510／R11000／M40003 | **`res_id` 外观资源**（已确认，见 §四） |
| 9 | int | 1 | 0 | 恒 0 |
| 10 | int | 1 | 0 | 恒 0 |
| 11 | int | 1 | 0 | 恒 0 |
| 12 | string | 2 | `"1"` 或 `""` | `UNKNOWN` |
| 13 | int | 2 | 0 或 90 | `UNKNOWN` |
| 14 | int | 3 | 0, 170, 200 | `UNKNOWN` |
| 15 | string | 1 | `""` | 恒空 |
| 16 | string | 2 | `E62931` 或 `""` | `UNKNOWN`（像特效资源） |
| 17 | `nil` | 1 | — | 占位 |
| 18 | int | 8 | 0..7 | `UNKNOWN`（像类型枚举） |
| 19 | int | 1 | 0 | 恒 0 |
| 20 | string | 6 | `E70003`／`E52565`／`""` | `UNKNOWN`（像特效资源） |
| 21 | int/float | 7 | 0, 1, 0.9, 1.1, 15 | `UNKNOWN`（含小数 ⇒ 像缩放比例） |
| 22 | string | 14 | 庄老／牛天／雪女／`""` | `UNKNOWN`（像关联人物名） |
| 23 | int | 5 | 0, 4, 6, 8 | `UNKNOWN` |

### 3.1 ★ 最关键的一条：**`Config.Mon` 里没有 HP / 攻击 / 经验 / 金币**

23 个字段中**没有任何一个**的取值分布像 HP 或攻击力
（若存在，应有几百到几万级的宽范围；实测所有数值字段的 distinct ≤ 111 且范围 ≤ 255）。

⇒ **结论（重要）**：怪物战斗数值**不在客户端 APK 里**，属于**原版服务端数据**。
本阶段实现战斗时，这些数值只能：
- 标 `UNKNOWN`，或
- 用明确标注的 **`IMPLEMENTATION_FALLBACK` / `TEST_ONLY`** 兼容值。

**不得声称是原版公式或原版数值。**

---

## 四、已确认字段的证据

| 字段 | 结论 | 证据 |
|---|---|---|
| 索引 1 = `name` | 已确认 | 取值即中文怪物名；且 `tools/extract_config_mon.py` 与客户端 `mon_tips.luac` 的 `mon_name` 用法一致 |
| 索引 8 = `res_id` | 已确认 | 与 `SC_10201.mons.res_id` 同域取值（`H32000` 等）；`monster_vo.luac` 的 `res_id` 直接用于取外观资源 |
| 索引 2 疑似 `level` | `INFERRED` | 范围 1..150 与游戏等级区间一致；**尚无字节码直证**，故只作参考 |

> 其余字段**一律 `UNKNOWN`**。本阶段**不**用它们做任何逻辑判断。

---

## 五、客户端的怪物对象（`MonsterVo`）

`assets/src/game/scene/element/monster_vo.luac`（继承 `RoleVo`）字段：
`id, res_id, enter_effect, bid, realm, type, type2, is_client, model_size, spine_type, dir`。

与 `SC_10201.mons` / `SC_10212` 的字段**一一对应**（`enter_effect` 正对应 10212 多出的那个字段）
⇒ 客户端就是按服务端下发的这份数据构造怪物对象的。

场景模型侧（`assets/src/game/scene/scene_model.luac`）：

| 方法 | 位置 | 行为 |
|---|---|---|
| `addMonster` | proto#25 | 加入 `monList` |
| `removeMonster` | proto#27 | 移出 |
| `getMonster(id)` | proto#28 | **`monList[id]`**（按实例 id） |
| `getMonsterByBid(bid)` | proto#29 | 按配置 id 查（内部用 `monList` 查找） |
| `getMaxMonsterId()` | proto#30 | 遍历 `monList` 取最大 `id` |
| `syncMonsters` | proto#31 | 用服务端数据更新 `monList[vo.id]` 的 `x/y` |
| `managerMonster` | proto#36 | 怪物点击的完整处理（含组队确认框，最终 `csFightMon`） |

⇒ **服务端下发的 `id` 就是客户端的键**；一击必中的关键就是保证
`SC_10201.mons[].id` 与后续 `CS_20002.mon_id` 对得上。

---

## 六、本阶段使用的测试怪物

见 `test_monster.md`。摘要：**bid 20001「戴浩」**，`res_id='H32000'`，
是**第一条 `fight_mon` 主线任务 10020 的目标怪物**（1/1 击杀），
来自 1.4.9 `Config.Mon` 原版条目。

---

## 七、未知项清单（不猜）

| 项 | 状态 |
|---|---|
| 怪物 HP / HP_MAX | `UNKNOWN`（非 APK 数据） |
| 怪物攻击 / 防御 / 暴击 | `UNKNOWN`（非 APK 数据） |
| 怪物经验 / 金币 | `UNKNOWN`（非 APK 数据） |
| 怪物掉落表 | 见 `../item/drop_model.md` |
| `Config.Mon` 索引 2 是否就是 `level` | `INFERRED`，需字节码直证 |
| `Config.Mon` 索引 3/4/5/6/18/23 的语义 | `UNKNOWN` |
| `SC_10201.mons.type` 的取值枚举 | `UNKNOWN` |
