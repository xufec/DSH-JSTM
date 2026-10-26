# R104：实现 `21400`（魂星 · 装备列表）—— 用 DB 的 `equip_items` 发**真实装备**

> 继续清地图。这一轮选 `21400` 的理由很直接：它的 `role_eqm` 与 DB 的 `equip_items`
> **语义完全一致**（都是"已穿戴装备"），不像 `14099`/`13579` 那样有"总属性 vs 加成"的口径问题。
> **时间**：2026-09-29 01:55 – 02:20。

---

## 一、选它的依据（对比另一个候选）

| 候选 | 规格要点 | 口径问题 |
|---|---|---|
| **`21400`**（`soulstar_ctrl`，真机 **30 次**）| `role_eqm` / `partner_eqm` = **装备列表**；`eqm_grid` / `dung_bid` / `floor` | ★ **无** —— `equip_items` 就是"已穿戴装备"，**语义一致** |
| `13579`（`tree_ctrl`）| `tree_lev / role_attrs / role_eff …` = **摇钱树带来的属性加成** | ⚠ 有 —— 我们只有**角色总属性**（`role_attr_dict`），"加成 vs 总属性"与 `14099` 同类问题 |

⇒ 先做语义干净的 `21400`。

---

## 二、逐字段映射（**没有对不上的地方就不猜**）

**规格**：

```
SC_21400{ role_eqm:table(id:u32, bid:u32, hero_bid:u32, bind:u8, intensify_lev:u8,
            pos:u16, quantity:u16, ctime:u32, expire_ts:u32, durable:u16, object:u8,
            attrs_ext:…, attrs_ext_list:…, attrs_ext_one_list:…, jewel_list:…, str_ext_list:…),
          partner_eqm:（同构）, eqm_grid:u8, dung_bid:u32, floor:u8 }
```

**DB**：`equip_items(rid, slot, item_id, bid, hero_bid, ctime)` —— rid=1001 **有 6 行**

| 协议字段 | 来源 | 说明 |
|---|---|---|
| `id` | `item_id` | 物品实例 id |
| `bid` | `bid` | |
| `hero_bid` | `hero_bid` | ★ **0 = 角色装备，非 0 = 伙伴装备** ⇒ **据此把同一张表拆成 `role_eqm`/`partner_eqm`**（有依据的划分，不是猜）|
| `pos` | `slot` | |
| `ctime` | `ctime` | |
| `bind / intensify_lev / quantity / expire_ts / durable / object` + **5 个子表** | **无数据源 ⇒ 0 / 空表** | 不编造 |

---

## 三、实测（用**门禁的权威解析器**，不手写）

```
SC_21400 len=244 消耗=244 err=None  ⇒ PASS（结构精确符合规格）
顶层空表: ['partner_eqm']
第一条 role_eqm = (id=9, bid=40003, hero_bid=0, pos=1, ctime=1789749993)
   ← 与 DB `equip_items` 第 1 行 (slot=1,item_id=9,bid=40003,hero_bid=0,ctime=1789749993) **完全一致**
```

空表 `partner_eqm` 按门禁纪律**登记理由**（白名单 90 条）：
> `equip_items` 的 6 行**全部 `hero_bid = 0`**（都穿在角色身上）⇒ 伙伴装备为空是**真话**；
> 一旦有装备穿到伙伴身上，`partner_eqm` 立即非空。

---

## 四、★ 第二次踩同一个坑：**我手写的验证解析器又错了**

第一次验证时我**手写**了一个解析器，输出：

```
role_eqm=6 [(9,40003,0,1,1789749993), (0,0,9728,19200,0), (0,0,0,0,41403), …]   ← 第 2 条起全乱
解析=202/244  FAIL
```

**前两个数是对的**（与 DB 一致），之后偏了 —— 因为我把元素固定部分算成 22 字节，
实际是 **29 字节**（`4+4+4+1+1+2+2+4+4+2+1`）+ 5 个 `u16` 计数。

⇒ **结论：验证一律用 `audit_emitted_fields` 的权威解析器**（`load_specs()` + `audit_body()`），
**不要手写** —— 这与 R99 的"`17312` msg 读偏 1 字节"、R85 的"`10402` bid 读成 u32"是**同一类**，
已经发生 **3 次**了。这条已写进本报告，作为后续的硬性操作规范。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **194** / 默认 **51** / 未开放 21）/ CS 2463-0 / SC 静态 **72+1空-0** / SC 在线 **72-72** / 专用 **75-75**（+1）/ 门禁 E **PASS**（空表告警 0）|
| 回归（12 项） | 全 PASS |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `db_equip_rows(rid)`（按 `hero_bid` 拆分）+ `21400` 处理器；从通用集合移出 |
| `tools/_fix_r104_soulstar_eqm.py` | 插入脚本 |
| `tools/_fix_r104_allow_empty.py` | `21400:partner_eqm` 的理由登记 |
| `server/mock_server.py.bak_r104` | 改前备份 |
| `analysis/1.4.9/round104_soulstar_21400.md` | 本报告 |

---

## 七、一句话

> **`21400` 现在发的是玩家背包里那 6 件真实装备**（`id/bid/hero_bid/pos/ctime` 逐个来自
> `equip_items`），并按 `hero_bid` 把同一张表拆成"角色装备 / 伙伴装备"两张表 —— **有依据的划分**；
> 没有数据源的字段一律 0/空表，空的那张表**登记了理由**。
> ★ 顺带记下一条硬性规范：**验证一律用门禁的权威解析器**，手写解析器已经错了 3 次。
