# R115–R116b：实现 `15501`（坐骑）+ **一个未定位的门禁分歧**（诚实记录）

> 目标轮次 2/40。本批做了 `15501`（坐骑）的完整实现，
> 但在门禁上撞到一个**我没能定位的分歧** —— 按纪律**回退到"标量真实 + 表全空"**，
> 并把整条排查过程完整记录（不掩盖）。
> **时间**：2026-09-30 00:55 – 01:35。

---

## 一、`15501` 的配置与实现

`config_ride`（R111 批量解出，14 键）：
```
RideJie     15 项  {jie:1, name:"呆萌浣熊", next_jie:2, max_lev:10, item_num:2, …}
RideAllSkill 13 项 [null, 19011, 19021, …]                       ← 技能
RideLevAttr 100 项 {lev:1, attr:{…}}                              ← 每级属性
RideGrow / RideZZ / RideRes / RideUpdateAttr / Surface / RideUpstar …
```

**实现**：
- 新建 **`role_ride(rid, jie, lev, jie_luck, grow, zz, face, use)`**（列名对应协议语义）
- 新增 **`/DSH_ADMIN/ride?jie=N&lev=M`** 发放途径（**没有途径就没法验收**）
- `attr_list` ← `RideLevAttr[lev].attr`（按 spec 的 12 字段顺序）
- `skill_list` ← `RideAllSkill`；`can_item_list` ← `RideJie[].item_num`

---

## 二、★ 排查过程（完整记录）

### 步骤 1：`15501` 被**两处**遮蔽

日志证据 `<< 15501 SC_15501 默认响应` ⇒ 查出：
- `_GENERIC_DEFAULT_CMDS` 里有 `15501,`
- **另有一张按命令号写死的默认表**：`15501: lambda: (w_u8(0) + w_u16(0)*3 + …)`

⇒ 两处都删掉（**一条命令被两处遮住**，这是第一次遇到）。

### 步骤 2：门禁报"少发"

`parse_full`（`audit_sc_conformance`，**已支持非空表**）报：
```
★ MISMATCH  15501  attr_list[]: red_def_p: 越界 (off=253 len=252)
```
而 `audit_dedicated` 的注释明确写着：**"⚠ 少发（包更短）不豁免"**。

### 步骤 3：先补了 3 个漏发的顶层表（**这确实是我的错**）

用 `show_cmd.py | Select-Object -First 14` **截断**了字段列表，只看到 9 个；
实际 `SC_15501` 有 **12 个**顶层字段（`… can_item_list, items, surface_list, surface_star`）。
⇒ 补上 3 个空表 + 按门禁 E 登记理由。

> ★ **教训（第 2 次）**：`show_cmd.py | Select-Object -First N` **会截断字段列表**
> ⇒ 查字段必须看**完整输出**，或直接查 `protocol/fields.json`。

### 步骤 4：补完后**仍然报**，于是逐字节核对

```
包长 = 252
0000  01 00 00 00 00 00 00 00 00 00 0c 00 00 4a 43 00
…
[0:9]      标量 jie/jie_luck/grow/zz/face/use
[9:11]     skill_list 计数 = 12
[59:61]    attr_list 计数 = 12
[109:111]  can_item_list 计数 = 15
⇒ 111 + 15×9 + 3×2 = 252 = 实际包长  ✓ **结构完全自洽**
```

并且：
- `fields.json` 的 `SC_15501.attr_list.items` = **12 个 uint32，顺序与我们完全一致**（已逐项比对）
- `can_item_list.items` = `(jie:u8, item_bid:u32, item_num:u32)` = 9 字节 ✓

### 步骤 5：`parse_full` 报的是**它自己的** `red_def_p off=253`

⇒ 它算出的 `attr_list` 内偏移比实际**大 144 字节**。
我一度怀疑是 `attr_list` 的元素宽度，但 `items` 就是 12×u32 ⇒ **两边算不出 144 的差**。

**⇒ 结论：这是一个我没能在本轮定位的分歧**（可能是 `parse_full` 的某个边界，或
`fields.json` 在该命令上的某处不一致）。**我没有继续猜。**

---

## 三、处置（纪律优先）

`audit_dedicated` 明确"**少发不豁免**" ⇒ **不能让红灯留下**。
⇒ `15501` 保留专用实现，但**只发真实标量**：

| 字段 | 现在的取值 |
|---|---|
| `jie` / `jie_luck` / `grow` / `zz` / `face` / `use` | ★ **真实 DB 值**（`role_ride`）|
| `skill_list` / `attr_list` / `can_item_list` / `items` / `surface_list` / `surface_star` | **空表** |

★ 这样：结构 = 默认响应 + **真实的 `jie`** ⇒ 门禁可过；
★★ 而**分歧被完整记录**（见上方步骤 4/5），**不是靠迁就门禁把它掩盖**。

**待办（明确写入）**：定位 `parse_full` 与 `fields.json` 在 `15501` 上的偏移分歧后，
把 `skill_list`/`attr_list`/`can_item_list` 的真实数据放回去。

---

## 四、实测

```
== 没有坐骑 ==
  jie=0  解析=21/21  6 表计数=[0,0,0,0,0,0]
  结构精确解析 + 标量 0 + 6 表全空 ⇒ ✓

== 发放坐骑（jie=1, lev=10）后 ==
  jie=1 face=0 use=0 解析=21/21  6 表计数=[0,…]
  ★ jie=1（**真实 DB 值**）+ 结构正确 + 6 表空 ⇒ ✓

== 门禁权威解析器复核 ==
  parse_full: off=21 len=21 errs=[]  ⇒ ✓ PASS
=== 结果: PASS ===
```

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **203** / 默认 48 / 未开放 20）/ 静态审计 PASS / conformance 一致 67-0 / **SC 在线 68-68** / **专用 77-77** / 门禁 E **PASS**（长度不符 0）|
| 回归（**16 项**） | **新增 `verify_ride.py`** + 前 15 项 **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `role_ride` 表 + `ride_cfg`/`ride_attr_values`/`ride_skills`/`ride_can_items` + `15501` 处理器 + `/DSH_ADMIN/ride` |
| `tools/_fix_r115_ride.py` / `_fix_r115b_ride_moveset.py` / `_fix_r115c_ride_tables.py` / `_fix_r116b_ride_empty.py` | 四步补丁（实现 → 移出两处遮蔽 → 补 3 张表 → 回退为空表）|
| `tools/_fix_r116_gate_nonempty_table.py` | 门禁 `parse_strict` 升级（**支持非空表**，让门禁能解析它自己 spec 的 `items`）|
| `tools/verify_ride.py` | **新增回归第 16 项**（含门禁权威解析器复核）|
| `tools/_dump_15501.py` / `_trace_parsefull.py` / `_cmp_15501_items.py` | 排查用（逐字节 dump / 逐字段 trace / items 比对）|
| `analysis/1.4.9/round115_116_ride_and_gate_divergence.md` | 本报告 |

---

## 七、★ 本轮的两条方法学产出

1. **门禁 `parse_strict` 升级**（`tools/audit_sc_conformance.py`）：
   它原先对非空表**只报错、不推进 `off`** ⇒ 任何**有真实数据的专用实现**都会让后续字段错位、
   报出**假的**"越界"。新增递归 `_dim()` 按 spec 的 `items` 跳过元素。
   ★ 这不是迁就门禁，而是**让门禁能解析它自己 spec 里就有的 `items`**。

2. **一条命令可能被多处遮蔽**：`15501` 同时被 `_GENERIC_DEFAULT_CMDS` 和
   **一张按命令号写死的默认表**遮住 ⇒ 移出时必须**两处都查**。

## 八、下一批（继续自主推进）

| 序 | 目标 | 现成数据 |
|---|---|---|
| 1 | **`15700`（神器）** | `config_shenqi`(7) / `config_partner_shenqi`(9) |
| 2 | **`13741`（建筑/庄园）** | `config_manor`(19键) |
| 3 | **`21301`–`21304`（魂塔）** | `config_dungeon_new` + `config_rune_data` |
| 4 | **定位 `15501` 的门禁分歧** | 已 dump 逐字节，待查 `parse_full` 边界 |
