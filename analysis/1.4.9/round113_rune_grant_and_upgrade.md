# R113：修 `21405` 的**假成功**缺陷 + 实现 `21406`（符文升级）

> 目标轮次 1/40。本轮先做了一件"补漏"的事：**R112 的 `21405` 只扣钱、没给东西** ——
> 那是假成功。修完后顺手把 `21406`（符文升级）也做了。
> **时间**：2026-09-30 00:25 – 00:40。

---

## 一、★★ 修 `21405` 的假成功（R112 留下的真缺陷）

R112 的实现：扣 `rune_chip` → 回 `code=1`。**但没有把符文加进背包** ⇒
玩家"钱花了、东西没到" —— 这正是项目纪律里最不能犯的那类错（**假装成功**）。

**依据**（确认 `rune_id` 是真实物品 bid）：

```
server/item_config.json:
  21403 牧夫 type=43    21413 贪狼 type=43    21423 仙女 type=43    21433 巨蛇 type=43
RuneExchange[2] = {name:"贪狼", rune_id:21413, …}   ← 名字对上了 ⇒ 映射成立
```

**修法**：兑换成功后 `db_bag_add(rid, rune_id, num)`（真的入库）。

---

## 二、`21406`（符文升级）实现

```
CS_21406{bag_code:u8, id:u32} → SC_21406{code:u8, msg:string}
```

| 步骤 | 做法 |
|---|---|
| 1 | `id` 是**背包实例 id**（`bag_items.item_id`）⇒ 先查出符文的 `bid` |
| 2 | 取 `RuneBase[bid][lev+1].assets`（本服是 `rune_exp`）作为升级消耗 |
| 3 | 扣 `rune_exp`（`db_add_assets` 负数）并把等级 +1 |
| 4 | 等级存 **`role_runes(rid, rune_bid, lev)`**（新表，列名对应语义；**没有行 ⇒ 等级 1**，与 `RuneBase[bid]['1']` 一致）|

判据（都指向出处）：
- 找不到背包物品 ⇒ `code=0 '背包里找不到该符文'`
- `RuneBase[bid][lev+1]` 不存在 ⇒ `code=0 '已满级或该符文无升级配置'`
- 材料不足 ⇒ `code=0 '材料不足(rune_exp)'`
- 否则 ⇒ 扣钱 + 升级 + `code=1`

---

## 三、实测（三条路径全通）

```
前置：rune_chip=50000  rune_exp=50000

== CS_21405{21403,1} ==
  code=1 msg=''  rune_chip 50000→45500  背包里 21403 数量: 4→5     ← ★ 真的给了
  扣 4500 且真的拿到符文（数量 +1）⇒ ✓

== CS_21406{bag_code=1, id=45} ==
  code=1 msg=''  等级 4→5  rune_exp 50000→49409                    ← ★ 真的升级 + 扣钱
  升级成功且扣了 rune_exp ⇒ ✓

== CS_21406（rune_exp=0）==
  code=0 msg='材料不足(rune_exp)'                                   ← ★ 诚实失败
  回 code=0 + 材料不足 ⇒ ✓
=== 结果: PASS ===
```

### ★ 这条判据我改了**三次**（都记下来）

| 版本 | 判据 | 为什么错 |
|---|---|---|
| v1 | `max(item_id)` 两次取值比较 | 背包里已有该物品时**两次相同** ⇒ 不幂等 |
| v2 | `COUNT(*)` 行数 | `db_bag_add(..., merge=True)` 对已有物品是**数量 +1、不新增行** ⇒ 假"没变化" |
| **v3** | **`SUM(quantity)`** | ✅ 正确 |

> **教训**：判"物品有没有真的到账"要数 **`quantity` 总和**，不是行数、也不是实例 id ——
> 因为背包有**合并**语义。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **199** / 默认 49 / 未开放 20）/ CS 2463-0 / SC 静态 **69+1空-0** / SC 在线 **69-69** / 专用 **76-76** / 门禁 E **PASS** |
| 回归（**14 项**） | **新增 `verify_rune_upgrade.py`** + `verify_mingge_rune` + 原 12 项 **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `21405` 补"真给符文"；新增 `db_rune_init/lev/set_lev`、`rune_up_cost` 与 `21406` 处理器 |
| `tools/_fix_r113_rune_grant_upgrade.py` | 插入脚本 |
| `tools/verify_rune_upgrade.py` | **新增回归第 14 项**（兑换给物 + 升级 + 材料不足）|
| `server/mock_server.py.bak_r113` | 改前备份 |
| `analysis/1.4.9/round113_rune_grant_and_upgrade.md` | 本报告 |

---

## 六、下一批（继续自主推进）

| 序 | 目标 | 现成数据 |
|---|---|---|
| 1 | **`21402`/`21403`（装备穿脱）** | `equip_items` 6 件真实数据 + `bag_items` 35 条 |
| 2 | **`13741`（建筑/庄园）** | `config_manor`（19 键）已解出 |
| 3 | **`15501`（坐骑）** | `config_ride` / `config_lingshou`（各 14 键）|
| 4 | **`15700`（神器）** | `config_shenqi`(7 键) / `config_partner_shenqi`(9 键) |
| 5 | **`21301`–`21304`（魂塔）** | `soulstar_ctrl` 家族，`config_dungeon_new` + `config_rune_data` |
| 6 | **"获得途径"** | 让玩家能获得命格/翅膀/座椅/坐骑 —— 那些"全 0"的命令才有真实数据 |
