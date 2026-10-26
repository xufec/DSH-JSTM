# R157：`105xx` 家族**收尾 15 条**（专用分支 339 → 354）—— ★ **一次就对**

> 新目标第 6 批。这批**没有再踩坑**：把纪律第 10 条（字段名+类型+顺序）**落实成动作**后，
> 15 条**一次验证通过**。
> **时间**：2026-09-30 23:05 – 23:40。

---

## 一、★ 为什么这次"一次就对"

R156 有 **4 条宽度写错**（凭印象用了 `u32`/`u8`）。本批的做法改成：

1. **先用 `tools/_show_specs.py` 把 15 条的 CS/SC `(名字, 类型)` 全打出来**
2. **在代码注释里逐条写清类型**（见下表），再照着写 `w_u8`/`w_u16`/`w_u32`
3. 锚点**含整行**（纪律第 17 条）、**串行执行**（纪律第 18 条）

⇒ **结果：15 条一次 PASS**（结构精确 + 3 个真实值断言全过）。

---

## 二、15 条（★ 注释里就带着类型）

| cmd | SC（逐个写清类型）|
|---|---|
| `10506` | `code:u8, msg:s, bag_item_id:u32, item_bid:u32, hero_bid:u32, eqm_new_pos:u8` |
| `10517` | `code:u8, msg:s` |
| `10523` | `code:u8, msg:s, item_bid:u32, bid_list:table` |
| `10524` | `code:u8, msg:s, fc_bid_list:table, bid_list:table` |
| `10525` | `uniq_id:u32, from_code:u8, item_id:u32` ← ★ **无 code/msg** |
| `10526` | `items:table` |
| `10531` | `item_coin:table` |
| `10533` | `val:u8` |
| `10536` | `code:u8, msg:s, bid_list:table` |
| `10537` | `code:u8, msg:s, item_id:u32` |
| `10561` | `key:**u16**, args:table` ← ★ `key` 是 **u16** |
| `10571` | `code:u8, msg:s, item_id:u32, star_lev:u8, star_grid:u8` |
| `10587` | `code:u8, msg:s, is_auto:u8, bag_item_id:u32, eqm_item_id:u32, eqm_new_pos:u8, hero_bid:u32` |
| `10588` | `code:u8, msg:s, eqm_item_id:u32, bag_item_id:u32, bag_pos:u8, hero_bid:u32` |
| `10592` | `end_time:u32, GiftList:table` |

### 实测

```
== 15 条结构精确性 ==  失败 0 条 ⇒ ✓
  10525 uniq_id=90001 from_code=1 item_id=90001 ⇒ ✓
  10561 key=7（请求 7，u16）⇒ ✓
  10537 回显 item_id=21903 ⇒ ✓
=== 结果: PASS ===
```

★ **`105xx` 家族至此收尾**：R155（13 条）+ R156（12 条）+ R157（15 条）= **40 条**，
而开始时这一族有 **40 条**未实现 ⇒ **全部做完**。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **354** / 默认 21 / 未开放 6）/ 静态 PASS / conformance PASS / **SC 在线 27-27** / **专用 105-105** / 门禁 E **PASS** |
| 回归（**41 项**） | **新增 `verify_equip_batch3.py`** + 前 40 项 **失败数 0** |
| 判定表 | **B 15 / C 0 / A 354** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `105xx` 收尾 15 条（注释里带类型）|
| `tools/verify_equip_batch3.py` | **新增回归第 41 项** |
| `tools/_fix_r157_equip_batch3.py` | 插入脚本（锚点含整行）|
| `tools/_emitted_empty_allow.json` | 新增 8 条理由（共 131 条）|
| `server/mock_server.py.bak_r157` | 改前备份 |

---

## 五、新目标进度

| 指标 | R152 | R153 | R154 | R155 | R156 | 现在 |
|---|---|---|---|---|---|---|
| **专用分支** | 306 | 311 | 314 | 327 | 339 | **354** |
| **回归项** | 36 | 37 | 38 | 39 | 40 | **41**（失败 0）|
| **累计实现** | 4 | 9 | 12 | 25 | 37 | **52 条** |
| 六道门禁 | 全 PASS | 全 PASS | 全 PASS | 全 PASS | 全 PASS | **全 PASS** |

### 下一批

| 目标 | 依据 |
|---|---|
| ★ **`10xxx` 家族下一条主线**：`102xx`（41 条）/ `103xx` / `104xx` | `classify_gap.py --family 10` |
| `16610`/`16634`/`16636`（活动/礼包）| `config_lucky_box_data` / `config_treasure_box_data` |
| `10947`（`power, flyup_lev`）| `config_eqm_ancient` |
| ★ 用"**先看家族共性 + 逐个核对类型**"推进 `13xxx`（**226 条**，最大族）| `classify_gap.py` |
