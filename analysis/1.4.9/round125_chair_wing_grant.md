# R125：给「玩家没有该物」的那批补上**获得途径**（座椅 / 翅膀）

> 新目标的 ② 项：那批"玩家没有该物 ⇒ 与默认响应等价"的命令，
> **真正的解法不是实现它自己，而是给它一个"能有的途径"**。
> **时间**：2026-09-30 04:20 – 04:50。

---

## 一、思路

`20800`（座椅）/`11600`（翅膀）此前判"与默认响应等价"，理由是"玩家没有"。
但那有个隐含前提：**玩家永远没有**。

⇒ 照 R115 的 `role_ride` 先例：**建真实状态表 + 发放入口** ⇒ 查询命令**立刻有真实数据**。

| cmd | 新建表 | 发放入口 | 读真实 DB 的字段 |
|---|---|---|---|
| **`20800`** | `role_chair(rid,stage,power,luck,res_stage,grow)` | `GET /DSH_ADMIN/chair?stage=3&power=12345&luck=7&res_stage=2&grow=99` | `stage`/`power`/`luck`/`res_stage`/`grow` |
| **`11600`** | `role_wing(rid,color,wing_id,power,star)` | `GET /DSH_ADMIN/wing?wing_id=8801&star=5&color=2&power=999` | `color`/`wing_id`/`power`/`star` |

---

## 二、实测（获得途径 → 立刻有真实数据）

```
20800 没座椅: len=12 stage=0 power=0
20800 有座椅: stage=3 power=12345 luck=7 res_stage=2 grow=99 技能表=0     ← ★ 真实
11600 没翅膀: len=15 wing_id=0 star=0
11600 有翅膀: color=2 wing_id=8801 power=999 技能表=0 属性表=0 star=5      ← ★ 真实
⇒ PASS
```

**门禁权威解析器复核**：
```
SC_20800 len=18 消耗=18 err=None ⇒ PASS
SC_11600 len=25 消耗=25 err=None ⇒ PASS
```

---

## 三、★★★ 同一个错误**第 3 次**：`Select-Object -First N` 截断字段列表

门禁**当场抓到**我刚写的两条：

```
★ MISMATCH  11600  lingxi_num: 越界 (off=19 len=15)
★ MISMATCH  20800  items: table 计数越界
```

根因：我用 `show_cmd.py | Select-Object -First 11` 看规格 ⇒ **只看到前 6 个字段**。
完整规格是：

```
SC_20800{stage, power, luck, res_stage, grow, skill_list, ★items, ★surface_list, ★surface_star}
SC_11600{color, wing_id, power, wing_skill, add_attr, star, ★lingxi_num, ★jiewing_id, ★surface_list}
```

### 本会话第 3 次（前两次：`15501`、`13741`）

| 次 | 命令 | 漏了什么 |
|---|---|---|
| 1 | `15501`（坐骑） | `items` / `surface_list` / `surface_star` |
| 2 | `13741`（建筑） | —— 忘了看完整规格就下判断 |
| **3** | **`20800`/`11600`** | `20800` 漏 3 张表；`11600` 漏 `lingxi_num`/`jiewing_id`/`surface_list` |

> ★ **纪律（写死）**：**查命令字段必须看完整输出**（`show_cmd.py` **不带** `Select-Object -First`），
> 或直接读 `protocol/fields.json`。**`Select-Object -First N` 是查字段时的禁招。**

**修**：补齐 6 个字段（本服无源的按门禁 E 登记理由后回空表）。

---

## 四、顺带修掉第 2 个验收幂等坑

`verify_rune_equip.py` 本轮 FAIL：`bag 26→27 equip 5→3`（**装备表里有前几次测试的残留**，
`eqm_pos` 覆盖了别的槽位 ⇒ 行数判据不成立）。
**修**：验收前**清空 `equip_items`**（自备前置）⇒ 幂等 ✓

| 幂等坑 | 命令 | 修法 |
|---|---|---|
| 第 1 次 | `verify_ride` | 表未建时默认等级 1 |
| 第 2 次 | `verify_unsupported4` | 自备金币（脚本会花钱）|
| **第 3 次** | **`verify_rune_equip`** | **清空 `equip_items`**（脚本会搬装备）|

> ★ 规律：**凡是有"消耗/搬运"的验收，必须先把自己依赖的状态重置或补足。**

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **223** / 默认 45 / **未开放 7**）/ 静态 PASS / conformance PASS / **SC 在线 52-52** / **专用 80-80** / 门禁 E **PASS**（长度不符 0）|
| 回归（**20 项**） | **失败数 0** |
| 判定表 | **B 46 → 31** / **C 0** / **A 223** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `db_chair_state/set`、`db_wing_state/set` + `20800`/`11600` 处理器 + `/DSH_ADMIN/chair`/`wing`；从 `_GENERIC_DEFAULT_CMDS` 移出 2 条 |
| `tools/_fix_r125_chair_wing.py` / `_fix_r125b_fields.py` | 实现 + 补漏字段 |
| `tools/gap_verdicts.py` | 15 条从 B 类移入 A 类（含 R120–R125 全部新实现）|
| `tools/verify_rune_equip.py` | 加幂等前置 |
| `server/mock_server.py.bak_r125` | 改前备份 |

---

## 七、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **7** | **−12** |
| **未实现命令** | 67 | **54** | **−13** |
| **专用分支** | 208 | **223** | **+15** |
| **B 类（有依据地不做）** | 57 | **31** | **−26** |
| **回归项** | 17 | **20**（失败 0）| **+3** |
| 六道门禁 | — | **全 PASS** | — |

### 下一批（继续做 ② 项"获得途径"）

| 系统 | 命令 | 需要的表 |
|---|---|---|
| **神器** | `15700` | `role_shenqi`（`config_shenqi` 7 键已解出）|
| **命格** | `19400` 的 `mingge_list` | `role_mingge`（`config_mingge` 9 键）|
| **魂兽** | `15801` | `role_beast` |
| **元神** | `19406` | `role_yuanshen` |
| **称号** | `11400` | `role_title` |
