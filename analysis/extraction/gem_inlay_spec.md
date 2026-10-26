# 宝石镶嵌（10521/10522/10530/10531）命令取证

> 用途：HANDOFF 下一步顺序第 2 项 —— **宝石镶嵌 CS 命令取证**，为
> 「镶嵌 → `ItemMiscAttrJewel` 总属性表 → AttributeService → PowerService → 客户端同步」闭环铺路。
> 本文件**只记录取证结论与现状**，尚未改任何代码。
> 日期：2026-10-06　取证方式：`protocol/`（源自 `cmd_resolve_*.luac`）+ `server/cfg/` 配置 + 源码静态核对。

---

## 一、CS / SC 规格（**CONFIRMED** —— 直接来自 `protocol/fields.json`）

| cmd | 名称 | CS | SC |
|---|---|---|---|
| **10521** | 宝石镶嵌 | `{bag_code:u8, eqm_item_id:u32, jewel_item_id:u32}` | `{code:u8, msg:string, bag_code:u8, eqm_item_id:u32, pos:u8}` |
| **10522** | 宝石摘除 | `{bag_code:u8, eqm_item_id:u32, pos:u8}` | `{code:u8, msg:string, bag_code:u8, eqm_item_id:u32}` |
| **10530** | 宝石升级 | `{bag_code:u8, eqm_item_id:u32, jewel_pos:u8, state:u8}` | `{code:u8, msg:string, bag_code:u8, eqm_item_id:u32, jewel_pos:u8, jewel_bid:u8}` |
| **10531** | 镶嵌/升级所需铜币 | `{item_list:table{item_bid:u32}}` | `{item_coin:table{item_bid:u32, coin:u32}}` |

要点：
- `10521` 的**两个 id 都是物品实例 id**（`eqm_item_id` 装备、`jewel_item_id` 宝石），不是 bid。
- `10521` 的 SC 回 **`pos`** ⇒ 服务端要决定宝石镶到**第几个孔** ⇒ 服务端**必须持有孔位状态**。
- `10531` 是**纯查询**（给一批 bid 问需要多少铜币），可直接由配置驱动，不涉及状态。

相关但**属另一系统**（符文 rune，勿混）：
`21402 镶嵌符文` / `21403 拆卸符文` / `21401 推送符文装备栏解锁`。
`19410 共鸣开孔/重置` 属命格（`mingge_id`+`hole`）。

---

## 二、`ItemMiscAttrJewel` 总属性表（**CONFIRMED** —— `server/cfg/config_item_misc_attr.json`）

结构：`ItemMiscAttrJewel[宝石等级][所需孔数档]["hash"] = {next:<下一级>, attr:{序号:[null,属性名,数值]}}`

实测全表（8 级）：

| 宝石等级 | 所需孔数档 | next | 属性条数 |
|---|---|---|---|
| 3 | **12** | 4 | 10 |
| 4 | **12** | 5 | 11 |
| 5 | **18** | 6 | 11 |
| 6 | **18** | 7 | 11 |
| 7 | **24** | 8 | 11 |
| 8 | **24** | 9 | 11 |
| 9 | **24** | 10 | 11 |
| 10 | **24** | 0（满级） | 11 |

样例（L3 / tier12）：`atk_abs 92, tenacity 31, crit 31, dodge 21, hit 21, hp_max 700, def_p 99, def_s 99, atk_p 140, atk_s 140`

⇒ **"12 / 18 / 24" 是孔数档位**：等级 3–4 需 12 孔、5–6 需 18 孔、7–10 需 24 孔。
`next=0` 表示满级。属性名与 `attribute/service.py` 的 `ATTR_KEYS` **同名** ⇒ 可直接并入属性字典。

同文件另有 `ItemMiscAttrLev`（装备精炼等级 → `next_lev` + attr）与 `ItemMiscAttrWash`（**空 `{}`**）。

---

## 三、服务端现状（**源码核对**，`server/mock_server.py`）

| cmd | 位置 | 现状 |
|---|---|---|
| 10521 | L12843 | **桩**：只校验 `equip_one(rid, eqm_item_id)` 存在 ⇒ 恒回 `pos=0`。**不消耗 `jewel_item_id`、不记录孔位、不碰 `ItemMiscAttrJewel`** |
| 10530 | L12848 | **桩**：回显 `jewel_pos` + `jewel_bid=0`。无升级逻辑 |
| 10522 | L12341 | 回执族 |
| 10531 | L12780 | 属子表组，未按 `item_coin` 真实计算 |

⇒ 结论：**"总属性表已提取"≠"已接线"**。`FINAL_REGRESSION.md` 缺口 #3 的"部分 CONFIRMED"指的是**配置已提取**；
**镶嵌闭环尚未接通**，与本文件第三节一致。

---

## 四、★ 装备孔位与宝石等级上限：**已找到**（`EqmJewel`）

> ⚠ 关键更正：此前 `FINAL_REGRESSION.md` 缺口 #3 记「`ItemJewel` 反构造失败 / 全 null」——
> 那是**找错了位置**：`config_item.Config` 下确有 `ItemJewel` 且为 **null**，
> 但真正的表是 **`config_item_misc.EqmJewel`**（13 行，**非 null**）。

**`server/cfg/config_item_misc.json` → `EqmJewel`（CONFIRMED）**
`EqmJewel[装备等级] = {eqm_lev, groove, jewel_lev}`

| 装备等级 | `groove`（孔数） | `jewel_lev`（可镶宝石等级上限） |
|---|---|---|
| 1 / 5 / 10 / 20 | 0 | 0 |
| 30 | 1 | 3 |
| 40 | 2 | 4 |
| 50 | 3 | 5 |
| 60 | 4 | 6 |
| 70 | 4 | **7** ← DSH 当前 70 级 |
| 80 | 4 | 8 |
| 90 | 4 | 9 |
| 100 / 110 | 4 | 10 |

⇒ **`groove` = 该等级装备的孔位数**；**`jewel_lev` = 该等级可镶的最高宝石等级**。
与 `ItemMiscAttrJewel` 的 `next` 链（…→10→0 满级）**自洽**。

`config_item_misc` 另有 `EqmPos`(15 行，装备位类型) / `EqmPos_2`(15 行，server_pos 映射)。

---

## 五、✗ 已**否证**的假设（记录以免重踩）

**假设**：`ItemMiscAttrJewel` 的孔数档 `12/18/24` = `装备位数 × groove`。

**检验**：`EqmPos` 实测 **15** 行（不是 6）⇒
- eqm_lev 40（groove=2）→ 15×2 = **30** ≠ 12
- eqm_lev 50（groove=3）→ 15×3 = **45** ≠ 18
- eqm_lev 60（groove=4）→ 15×4 = **60** ≠ 24

⇒ **该假设不成立**。`12/18/24` 的真实语义**仍为 UNKNOWN**（可能是"全身累计孔数档"或"共鸣档"，但未取证）。

---

## 六、仍未取证（明确列出，未猜）

| # | 缺口 | 状态 |
|---|---|---|
| 1 | `ItemMiscAttrJewel` 的 `12/18/24` 档位语义 | **UNKNOWN**（"位×孔"假设已否证） |
| 2 | 宝石物品 → 宝石**等级**的判定 | **UNKNOWN**：`10521` 只给物品实例 id；等级可能编码在 bid 段，待证 |
| 3 | 多颗宝石 → 总属性的**合成规则** | **UNKNOWN**（摘 1 颗是否降档？） |
| 4 | `10530` 升级的**成功率/消耗** | 装备宝石**未找到**；但 `config_intensify` 有 **`partner_jewel_inlay_rate` / `partner_jewel_up_rate`**（**伙伴**宝石的镶嵌/升级成功率）⇒ 属**伙伴**系统，勿与装备宝石混用 |
| 5 | `10531` 铜币算法 | **UNKNOWN** |

> 纪律：以上全部标 UNKNOWN，**未在代码中填任何猜测值**；`10521` 返回结构在取证完成前**不改**。

---

## 七、下一步（收敛后的取证顺序）

1. 在 `config_item` 的**宝石物品行**里找 `jewel_lev`（`config_yuanshen`/`config_item_misc` 亦有 `jewel_lev` 字段名，可对照）。
2. 找 `12/18/24` 的第三种可能来源：`config_common.INLAY` / `config_intensify` / `config_item_fuse`（192 条宝石合成）。
3. 取证齐再设计 `role_equip_jewel` 兼容表并接线（`ItemMiscAttrJewel.attr` → 属性字典 → 战力 → SC_10304/10306）。
4. 每步：miniloop 145/145 + `/DSH_ADMIN/status` + `lint_dispatch_shadow` + 实机冒烟。

---

## 附：证据出处

- 命令名/规格：`protocol/cmd_table.json`、`protocol/fields.json`（生成自 `cmd_resolve_105.luac` 等）
- 总属性表：`server/cfg/config_item_misc_attr.json`（5219 B，含 `ItemMiscAttrJewel`）
  - 注：`server/cfg_kconfig/config_item_misc_attr.json`（3789 B）**不含** `ItemMiscAttrJewel` ⇒ 取数须用 `server/cfg/`
- 现状源码：`server/mock_server.py` L12341 / L12780 / L12843 / L12848
