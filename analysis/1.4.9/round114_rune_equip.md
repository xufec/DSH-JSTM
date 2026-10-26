# R114：实现 `21401`/`21402`/`21403`（魂星装备：格子容量 / 穿上 / 卸下）

> 目标轮次 2/40。这一批让**魂星系统的装备链路完整**：
> 列表（`21400`，R104）→ 容量 → 穿 → 脱，外加购买（`21405`）与升级（`21406`，R113）。
> **时间**：2026-09-30 00:40 – 00:55。

---

## 一、为什么这三条能真做（不是空壳）

| 条件 | 事实 |
|---|---|
| **有真实数据** | DB `equip_items`（rid=1001 **6 件**）+ `bag_items`（**36 条**）|
| **辅助齐全** | `db_bag_get_one` / `db_bag_delete` / `db_equip_put` / `db_bag_add` / `BAG_MAIN=1` |
| **同一条 DB 路径** | 与既有 admin 路由 `setequip`/`unequip` **完全一致** ⇒ 不引入新语义 |

---

## 二、逐条实现

| cmd | 协议 | 做法 |
|---|---|---|
| **`21401`** | `SC{eqm_grid:u8}` | 取 `bag_volume` 里 **`bag_code=2`（`ROLE_EQUIP`）** 的容量；**取不到 ⇒ 0（诚实）** |
| **`21402`** | `CS{bag_item_id, eqm_item_id, eqm_pos, hero_id}` → `SC{code,msg}` | 校验背包物品存在 ⇒ `db_equip_put(slot=eqm_pos)` 写入 ⇒ `db_bag_delete` 移出 ⇒ `code=1` |
| **`21403`** | `CS{eqm_item_id, bag_item_id, bag_pos, hero_bid}` → `SC{code,msg}` | 校验装备存在 ⇒ `db_bag_add` 回背包 ⇒ 删装备行 ⇒ `code=1` |

**新增辅助**：`db_equip_get_one` / `db_equip_delete` / `equip_grid_size`。

★ `bag_code=2` 的依据写在代码注释里（R58 已取证的 `BackPackConst.Bag_Code`：
`BACKPACK=1 / ROLE_EQUIP=2 / HERO_EQUIP=3 / STORAGE=4 / HERO_STORAGE=5 …`）。

---

## 三、实测（**真的搬动物品**）

```
== SC_21401 ==
  eqm_grid=0                    ← bag_volume 里没有 bag_code=2 的行 ⇒ 诚实回 0

== CS_21402{bag_item_id=6, eqm_pos=7} ==
  code=1 msg=''  bag 36→35  equip 6→7        ← ★ 真的从背包搬到装备
  物品真的从背包搬到装备 ⇒ ✓

== CS_21403{eqm_item_id=6} ==
  code=1 msg=''  bag 35→36  equip 7→6        ← ★ 真的卸回背包
  装备真的卸回背包 ⇒ ✓

== CS_21402{bag_item_id=99999999} ==
  code=0 msg='背包里找不到该物品'              ← ★ 诚实失败
=== 结果: PASS ===
```

★ 判据用的是**行数变化 + bid 回到背包**（不是"看 `code` 就算过"）——
`21402` 要求 `bag -1 且 equip +1`，`21403` 要求 `equip -1 且该 bid 回到 bag`。

### 顺带记一笔：`eqm_grid` 的配置来源**确认不存在**

在 `config_game_data` / `config_equip` / `config_item` 里搜 `eqm_grid` / `EquipGrid` / `grid`
**都没有命中** ⇒ **回 0 是当前唯一诚实的选择**（不是没做，是没源）。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **202** / 默认 49 / 未开放 20）/ CS 2463-0 / SC 静态 **69+1空-0** / SC 在线 **69-69** / 专用 **76-76** / 门禁 E **PASS** |
| 回归（**15 项**） | **新增 `verify_rune_equip.py`** + 前 14 项 **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `db_equip_get_one` / `db_equip_delete` / `equip_grid_size` + `21401`/`21402`/`21403` 处理器 |
| `tools/_fix_r114_rune_equip.py` | 插入脚本 |
| `tools/verify_rune_equip.py` | **新增回归第 15 项**（穿上/卸下的**数据搬运断言**）|
| `server/mock_server.py.bak_r114` | 改前备份 |
| `analysis/1.4.9/round114_rune_equip.md` | 本报告 |

---

## 六、魂星系统现状（已闭环）

| cmd | 功能 | 状态 |
|---|---|---|
| `21400` | 装备列表（从 `equip_items` 取真实装备）| ✅ R104 |
| **`21401`** | 格子容量 | ✅ **本轮** |
| **`21402`** | 穿上 | ✅ **本轮** |
| **`21403`** | 卸下 | ✅ **本轮** |
| `21405` | 兑换（真扣 `rune_chip` + **真给符文**）| ✅ R112/R113 |
| `21406` | 升级（扣 `rune_exp` + 等级 +1）| ✅ R113 |
| `21411` | 兑换列表（`RuneExchange` 20 项）| ✅ R109 |

⇒ **`soulstar` 家族里"真机发过"的命令已全部实现**（`21301` 早先已做）。

## 七、下一批（继续自主推进）

| 序 | 目标 | 现成数据 |
|---|---|---|
| 1 | **`15501`（坐骑）** | `config_ride`(14键) / `config_lingshou`(14键) |
| 2 | **`15700`（神器）** | `config_shenqi`(7) / `config_partner_shenqi`(9) |
| 3 | **`13741`（建筑/庄园）** | `config_manor`(19键) |
| 4 | **`21301`–`21304`（魂塔）** | `config_dungeon_new` + `config_rune_data` |
| 5 | **"获得途径"** | 让玩家能获得命格/翅膀/座椅/坐骑 |
