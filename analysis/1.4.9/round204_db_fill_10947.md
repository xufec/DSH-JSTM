# R204（新目标②）：★★★ **"DB 可填"的首个实质成果 —— `10947` 的属性面板用上 `role_attr` 真值**

> 新目标第 14 批。★★ **435 条空表分类后，找到了 85 条"DB 可填"的对象，并完成了第一条。**
> **时间**：次日 19:30 – 21:00。

---

## 一、★★★ 分类结果（新工具 `tools/classify_empty_tables.py`）

```
  DB 表: 45 张；有数据的: 34 张
  空表: 435 条 / 326 个命令
  ★ 分类统计:
     未知         339 条
     DB可填        85 条      ← ★★ 可动的对象
     无元素        11 条
```

### ★★ "DB 可填"的高价值对象

| 命令 | 空表 | ← **DB 表**（字段重合）|
|---|---|---|
| **`10947`** | `attr` | ★★ **`role_attr`（14）** |
| **`10949`/`10950`** | `attr_list` | ★★ `role_attr`（11/12）|
| **`11201`** | `partner_attr` | ★★ `role_attr`（14）|
| **`10601`** | `hero_list` | ★ `role_attr`（13）|
| **`11200`** | `partner_bag` | ★ `role_heros`（**18 行**）|
| **`12405`** | `update_mission_list` | ★ `missions`（**5 行**，重合 11）|
| **`10526`/`10954`/`10955`/`10957`** | `items` | ★ `bag_items`（**7 行**）|
| `129xx`（20+ 条）| `rank_list` | ⚠ `roles`（重合仅 3-4，**弱**）|

---

## 二、★★★ 完成第一条：**`10947`（看他人角色详情）的 `attr`**

### 取证（**全部来自本服 DB，逐名对应**）

```
role_attr 列: [rid, strength, intellect, armor, constiution, atk_s, atk_p, def_s, def_p,
               hp_max, atk_speed, hit, dodge, crit, tenacity, red_def_s, red_def_p, …]
role_attr 行: (1001, …, 789, 563, 672, 448, 4381, None, 337, 226, 113, 90, …)

SC_10947.attr 的元素字段: atk_s, atk_p, def_s, def_p, hp_max, atk_speed, hit, dodge, crit, …
   ⇒ ★★ 与 `role_attr` 的列**逐名对应** ✓
```

★ **原代码**（专用分支里）：
```python
w_u16(0) +                        # attr 空表      ← ★★ 就是这里
```

### 实现

```python
def db_role_attr(rid):            # ★ 读 role_attr 首行为 dict
def attr_row_bytes(cmd, field_name, row, rid):   # ★ 按 SC 的子表字段顺序生成 1 条
# 10947:
attr_row_bytes(10947, 'attr', db_role_attr(_rid64), _rid64) +  # ★ R204
```
★ **`None` ⇒ 0**（DB 里的 `None` 是"未设置"，**忠实呈现**，不编造）。
★ **`row` 为空 ⇒ 返回空表**（**不编造**）✓

### 实测

```
  10947: len=117 消耗=117 err=None
  ★ attr 子表: 1 条
     atk_s=789 atk_p=563 def_s=672 def_p=448 hp_max=4381 atk_speed=0 hit=337 dodge=226
  ⇒ PASS
```
★ **与 `role_attr` 表真值完全一致** ✓

---

## 三、★★ 本批建立的**可复用模式**（"DB 可填"三步）

1. **分类**（`classify_empty_tables.py`）⇒ 找"子表字段名 ∩ DB 列名 ≥ 3"的对象
2. **取证**（`_diag_r204b.py`）⇒ 看 DB 表的实际行 + SC 的子表字段，**确认逐名对应**
3. **实现**（`db_<表>()` + `attr_row_bytes/列表函数`）⇒ **DB 空 ⇒ 空表（不编造）**

> **★ 纪律第 45 条**：**"DB 可填"的空表要"逐名对应 + 空则不填"** ——
> `role_attr` 里的 `None` 是**真"未设置"** ⇒ **给 0 是忠实**；
> ★★ 但 **DB 里没有该行 ⇒ 必须发空表**（**不能编造一条全 0** —— R203 的教训）。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379**）|
| 门禁 E | **PASS**（顶层空表 **298** 条，**全部已登记理由**）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| ★ **`tools/classify_empty_tables.py`** | ★★ **435 条空表按"数据来源"分类**（DB可填 85 / 未知 339 / 无元素 11）|
| `analysis/1.4.9/_empty_class.txt` | 分类原始数据 |
| ★ **`server/mock_server.py`** | **`db_role_attr()` + `attr_row_bytes()`** + `10947` 的 `attr` 用真值 |
| `tools/_diag_r204b.py` | ★ DB 表 + SC 的取证诊断 |
| `tools/_fix_r204_10947_attr.py` | 插入脚本 |

---

## 六、下一批（**按"DB 可填"清单逐个做**）

| 目标 | ← DB 表 |
|---|---|
| ★★ **`10949`/`10950`/`11201` 的 `attr_list`/`partner_attr`** | `role_attr`（**同一个函数直接复用**）|
| ★★ **`11200` 的 `partner_bag`** | `role_heros`（**18 行**）|
| ★★ **`12405` 的 `update_mission_list`** | `missions`（**5 行**）|
| ★★ **`10526`/`10954`/`10955`/`10957` 的 `items`** | `bag_items`（**7 行**）|
| ★ **`10601` 的 `hero_list`** | `role_attr` + `role_heros` |
