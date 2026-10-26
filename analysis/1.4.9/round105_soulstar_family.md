# R105：`soulstar`（魂星/符文）家族全景 —— **结论是"现在不值得投入"，附证据**

> 上一轮做完 `21400` 后，我按计划继续做同系统的 `21410/21411/21412`。
> 深挖之后得出的结论是：**这几条现在做不出真实数据**，而且**原因有三条硬证据**。
> 把它写清楚，是为了**避免后续重复投入**。
> **时间**：2026-09-29 02:20 – 02:45。

---

## 一、家族全景（`213xx` + `214xx`，共 **15 条**）

`game/soulstar/soulstar_ctrl.luac` 的注册表一次列全：`21301-21304 / 21399 / 21400-21407 / 21410-21413`。

| cmd | 我们的状态 | **真机次数** | SC 字段摘要 | 归属配置 |
|---|---|---|---|---|
| **`21301`** | **专用** ✓ | **79** | `tower_id, floor, is_effect, clear_list, is_clear, daily_f…` | config_item |
| `21302` | 无 | 0 | `{code, msg}` | |
| `21303` | 无 | 0 | `dung_bid, tower_id, floor, BossList` | |
| `21304` | 无 | 0 | `tower_id, floor, round, reward_list, daily_floors` | config_partner_fetter |
| `21399` | 无 | 0 | `tower_id, clear_list` | |
| **`21400`** | **专用** ✓（R104）| **30** | `role_eqm, partner_eqm, eqm_grid, dung_bid, floor` | config_item |
| `21401` | 无 | 0 | `eqm_grid` | |
| `21402` / `21403` | 无 | 0 | 装备穿脱（`code,msg,bag_item_id,eqm_item_id,…`）| |
| `21405` | 无 | 0 | `{code,msg,id,num,price}` | ★ **config_rune_data** |
| `21406` | 无 | 0 | `{code,msg,bag_code,id,new_lev}` | |
| `21407` | 无 | 0 | `dung_bid, floor` | |
| **`21410`** | 默认响应 | **31** | `free_times, is_haft, free_end_time, rest_times, coin_count, record_server, show_vip, gold_count` | |
| **`21411`** | **未开放** | **15** | `{code,msg,coin_count,rest_times, Items:table(bid,num,exchange)}` | ★ **config_rune_data** |
| `21412` | 无 | 0 | `free_times, is_haft, free_end_time` | |
| `21413` | 无 | 0 | `record_server:table` | ★ config_rune_data |

**★ 真机只发过 4 条**：`21301`(79)、`21400`(30，**已做**)、`21410`(31)、`21411`(15)。
其余 **11 条真机 0 次** —— 客户端根本还没走到那些界面。

---

## 二、★ 三条硬证据（为什么现在不值得做）

### 证据 1：配置是 **20108 张表**的超大嵌套结构，现有解构器不适用

`config_rune_data.luac` 有 **1,229,514 字节**，反汇编出：

```
--- proto #0 bc=88937 ---
strings(16): 'RuneHeroDesc','RuneTarget','RuneExchange','attr','effect','item_list',
             'assets','RuneBase','RuneGridOpen','RuneOpenLimit','RuneBaseExp',
             'RuneOpenLimit1','sub','RuneContent','RuneStatic','Config'
tables(20108):
  TableConst(hash=[('id',35600),('content','推荐星魂：…'),('rune_type',2…)])
  …
```

⇒ **`RuneBase`/`RuneExchange`/`RuneContent`/`RuneStatic` 是顶层 `Config` 表的键**，
而反汇编把 **20108 张表平铺**了 ⇒ **要拿到 `RuneExchange`，必须先建立
"TDUP 顺序 ↔ 顶层键顺序"的对齐关系** —— 那是**独立的一件工程**（不是顺手能做的小事）。
**同一个形状问题**在 `config_invest`（3.2KB）上已经出现过（提取器输出 0 条）；
这里是它的 **1000 倍规模**。

### 证据 2：`21410`/`21412`/`21413` 回零 **与通用默认响应等价**（零增量）

通用默认响应的规则是"**第一个字段若名为 `code` 回 1，其余 string='' / table=空 / 数值=0**"。
而这三条的字段里**没有 `code`** ⇒ 默认响应本来就会给出**数值 0 + 空表**。
⇒ 我们专门实现一遍，**产出的字节完全一样** —— **没有增量**（同 `16500`/`17200` 投资系统的判断）。

### 证据 3：`21411` 是**动作**且需要 `RuneExchange` 的真实语义 —— 只能保持"未开放"

它是 `CS{count_type:u8, color:u8}` → `{code,msg,coin_count,rest_times, Items:table(bid,num,exchange)}`
—— **要发奖**。没有 `RuneExchange` 就**只能空发或假发**，两者都违反纪律。
⇒ 保持"未开放"（`code=0`）**本身就是诚实的**；将来解构了 `RuneExchange` 再实现。

---

## 三、结论与处置

| cmd | 处置 | 依据 |
|---|---|---|
| `21410` / `21412` / `21413` | **不做**（登记理由）| 回零与默认响应**字节等价** ⇒ 零增量；真实值需 `RuneStatic`/`RuneBase` 语义 |
| `21411` | **保持"未开放"** | 需要 `RuneExchange`；未解构前空发/假发都违规 |
| `21405` / `21406` / `21303` / `21403`（等 11 条） | **不做** | **真机 0 次**（客户端没走到）|
| `21301` / `21400` | **已做** ✓ | 真机 79 / 30 次，且各有真实数据源 |

### 下一步若要做 `soulstar`，正确的前置是：

> **写一个"TDUP 顺序 ↔ 顶层键顺序"对齐的解构器**（针对 `config_rune_data` 这种形状），
> 先把 `RuneBase` / `RuneExchange` / `RuneStatic` 落成 JSON，再回头做 `21405`/`21410`/`21411`。
> 在此之前，`soulstar` 家族**没有值得投入的命令**。

---

## 四、全量验证（本轮**未改服务端**，只加报告与探针）

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 194 / 默认 51 / 未开放 21）/ CS 2463-0 / SC 静态 72+1空-0 / SC 在线 **72-72** / 专用 **75-75** / 门禁 E **PASS** |
| 回归（12 项） | 全 PASS |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `tools/_probe_soulstar_cfg.py` | 探针：列 soulstar 家族相关配置 + 三条命令的集合状态 |
| `analysis/_cfg_rune.txt` | `config_rune_data` 反汇编（20108 张表）|
| `analysis/_soulstar_ctrl.txt` | `soulstar_ctrl` 完整注册表（15 条）|
| `analysis/1.4.9/round105_soulstar_family.md` | 本报告 |

---

## 六、一句话

> **`soulstar` 家族 15 条命令，真机只发过 4 条**（`21301`/`21400` 已做，`21410`/`21411` 是"兑换/抽奖"）。
> 深挖后**三条硬证据都指向"现在不值得做"**：
> ① 它依赖的 `config_rune_data` 是 **20108 张表**的超大嵌套配置，现有解构器不适用（要先写专用对齐器）；
> ② `21410/21412/21413` 回零与**通用默认响应字节等价**（零增量）；
> ③ `21411` 是**发奖动作**，没有 `RuneExchange` 只能空发或假发（都违规）。
> ⇒ **保持现状最诚实**，并把"下一步的前置条件"写清楚了。
