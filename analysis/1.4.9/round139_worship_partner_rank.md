# R139：实现 `13580`（膜拜列表，**5 条逐字段一致**）+ `12903`（伙伴榜，"榜上有我"）

> 新目标第 16 批。**C 类再次清零**（44 条未实现全部有结论）。
> **时间**：2026-09-30 12:05 – 12:35。

---

## 一、`13580`（膜拜列表）—— 元素 4 个字段**全在配置里**

```
SC_13580{worship_list:table(type:u8, lev:u16, exp:u32, used:u8)}
```

`config_guild_tree_data.WorshipType`（**5 项**）的字段：
```
{type:1, lev:0, exp:0, use:1, type_name:"北斗", weight:0, desc:"提高角色攻击", skill_desc:"…"}
{type:2, …, type_name:"缘灭"}, {type:3, …, type_name:"血手"}, …
```

⇒ `type` / `lev` / `exp` / **`used ← use`** —— **逐个对得上** ⇒ **5 条真实条目** ✓

### 实测（**逐字段**核对）

```
== 13580 膜拜列表 ==
  len=42 消耗=42 err=None 条目=5（配置 5 项）
  ★ 每条逐字段与配置一致 ⇒ ✓
```

★ `verify_worship_rank.py` **遍历配置的每一条**，与回包的 `(type, lev, exp, used)` **逐元组比对**
—— 不是抽查一条。

---

## 二、`12903`（伙伴榜）—— "榜上有我"（R130 判据）

```
SC_12903{my_ord:u8, my_val:u32, partner_bid:u32, partner_color:u8,
         rank_list:table(ord:u8, rid:u32, srv_id:string, name:string,
                         sex:u8, hero_bid:u32, val:u32, color:u32)}
```

| 字段 | 来源 |
|---|---|
| `rank_list`（1 条）| ★ **本服唯一角色**（`self_rank_row`，R130）；`hero_bid` ← 玩家当前伙伴 |
| `partner_bid` / `partner_color` | ★ **真实伙伴**（`db_hero_list`，本服 18 个）|
| `val` / `my_val` | **0**（伙伴战力算法未取证 ⇒ 不猜）|

### 实测

```
== 12903 伙伴榜 ==
  len=37 消耗=37 err=None my_ord=1 partner_bid=30800
  ★ 榜上有我（my_ord=1）+ 结构精确 ⇒ ✓
```

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **252** / 默认 35 / **未开放 6**）/ 静态 PASS / conformance PASS / **SC 在线 41-41** / **专用 89-89** / 门禁 E **PASS** |
| 回归（**27 项**） | **新增 `verify_worship_rank.py`** + 前 26 项 **失败数 0** |
| 判定表 | **B 25 / C 0 / A 252**（★ **C 类再次清零**）|
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `worship_rows`/`first_hero` + `13580`/`12903` 处理器；从集合移出 2 条 |
| `tools/verify_worship_rank.py` | **新增回归第 27 项**（**逐条**与配置比对）|
| `tools/_fix_r139_worship_partner_rank.py` | 插入脚本 |
| `server/mock_server.py.bak_r139` | 改前备份 |

---

## 五、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **6** | **−13** |
| **真机发过的未实现** | 67 | **43** | **−24** |
| **专用分支** | 208 | **252** | **+44** |
| **B 类（有依据地不做）** | 57 | **25** | **−32** |
| **回归项** | 17 | **27**（失败 0）| **+10** |
| 六道门禁 | — | **全 PASS** | — |
| **C 类（需人工判定）** | 10 | **0** | ★ **清零** |

### 下一批

| 目标 | 依据 |
|---|---|
| `13806`（摆摊列表）| 可补 `role_market`（R121 建了开关）+ `config_market`(7 键) |
| `16706`（VIP 道具）| `config_vip`(5 键) |
| `13569`（祈福）| `info:table` 无配置源 ⇒ 结构正确的空表 + 登记 |
| `13741`（建筑技能）| `lev`/`learn_list` 玩家态 ⇒ 可补 `role_build` |
| `scan_growth_cmds.py` 剩余动作 | 座椅 `20803`–`20809`、翅膀 `11602`–`11607` |
