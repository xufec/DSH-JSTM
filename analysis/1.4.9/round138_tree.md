# R138：实现 `13579`（摇钱树 / 膜拜）—— 用了两个**真实的配置常量**

> 新目标第 15 批。这批的亮点：`strength_rest` 与 `strength_name` **都有配置出处**，
> 而且**随等级变化**（可验证）。
> **时间**：2026-09-30 11:35 – 12:05。

---

## 一、依据（`server/cfg/config_guild_tree_data.json`，R111 批量解出）

```
TreeLev     = {0: {tree_lev:0, exp_mult:0,  ui_source:"N50080", npc_bid:80000},
               1: {tree_lev:1, exp_mult:10, …}, …  共 6 档}
StaticData  = {attr_delay:      {val:48,  desc:"属性保留时间（小时）"},
               strengthen_cost: {val:100, desc:"强化消耗元宝"}, …}     ← ★ 常量
WorshipType = {1: {type:1, type_name:"北斗", desc:"提高角色攻击", …},
               2: {…}, … 共 5 种}                                     ← ★ 膜拜类型
```

---

## 二、规格与逐字段处置

```
SC_13579{tree_lev:u8, strength_rest:u32, strength_name:string,
         role_eff:u32, role_delay:u32, role_attrs:table(code:u8, value:int32),
         parter_eff:u32, parter_delay:u32, parter_attrs:table(code:u8, value:int32)}
```

| 字段 | 来源 |
|---|---|
| **`strength_rest`** | ★ **`StaticData.attr_delay.val`**（配置写死 **48**）|
| **`strength_name`** | ★ **`WorshipType[].type_name`**（随 `tree_lev` 取：**北斗 → 独灼**）|
| `tree_lev` | 玩家态（新建 `role_tree`；没有 ⇒ **0**，真话）|
| `role_eff` / `role_delay` / `parter_eff` / `parter_delay` | 无源 ⇒ **0**（不猜）|
| `role_attrs` / `parter_attrs` | 无源 ⇒ **空表**（按门禁 E 登记 2 条理由）|

★ 发放入口：`GET /DSH_ADMIN/tree?lev=3`

---

## 三、实测（★ 两个值都可**独立复核**）

```
== 13579（lev=0）==
  len=33 消耗=33 err=None tree_lev=0 strength_rest=48 name='北斗'
  ★ strength_rest 与配置 `attr_delay.val`(48) 一致 ⇒ ✓
== 13579（lev=4）==
  tree_lev=4 name='独灼'
  ★ 膜拜类型随等级变化（'北斗' → '独灼'）⇒ ✓
=== 结果: PASS ===
```

★ `verify_tree.py` 直接**从 `config_guild_tree_data.json` 读期望值**再比对
—— 不是"看 `code` 就算过"，也不是写死常量。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **250** / 默认 36 / **未开放 6**）/ 静态 PASS / conformance PASS / **SC 在线 42-42** / **专用 88-88** / 门禁 E **PASS** |
| 回归（**26 项**） | **新增 `verify_tree.py`** + 前 25 项 **失败数 0** |
| 判定表 | **B 26 / C 1 / A 250** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `tree_cfg`/`tree_static`/`tree_worship_name`/`db_tree_*` + `13579` + `/DSH_ADMIN/tree` |
| `tools/verify_tree.py` | **新增回归第 26 项**（期望值**从配置读**）|
| `tools/_fix_r138_tree.py` | 插入脚本 |
| `tools/_emitted_empty_allow.json` | 新增 2 条理由（`role_attrs`/`parter_attrs`）|
| `server/mock_server.py.bak_r138` | 改前备份 |

---

## 六、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **6** | **−13** |
| **真机发过的未实现** | 67 | **43** | **−24** |
| **专用分支** | 208 | **250** | **+42** |
| **B 类（有依据地不做）** | 57 | **26** | **−31** |
| **回归项** | 17 | **26**（失败 0）| **+9** |
| 六道门禁 | — | **全 PASS** | — |

### 下一批

1. **C 类剩 1 条**：`rank` 系统的 **`12903`**（`rank_list` 家族，可同"榜上有我"处理）
2. 真机剩余可做：**`13580`（膜拜列表）**、`13806`（摆摊，可补 `role_market`）、`16706`（VIP 道具）、
   `13569`（祈福）
3. `scan_growth_cmds.py` 剩余成长动作
