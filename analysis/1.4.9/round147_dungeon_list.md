# R147：`21306`（副本列表）+ `21312`（一键扫荡）—— **34 条真实配置**

> 新目标第 23 批。沿用 **R129（`16200`）的成功模式**：**用配置表产出真实列表**。
> 时间：2026-09-30 16:25 – 16:55。

---

## 一、先纠正一个误判：`scan_table_sources` 的"命中"是**偶然**的

`tools/scan_table_sources.py` 报 `21306` 的元素字段"能对上配置"：
```
bid        ← config_adventure_mission, config_black_market
time       ← config_dungeon_gods, config_dungeon_tower
is_finish  ← config_promote
```
★ 但 `bid`/`time`/`is_finish` **在很多配置里都有** ⇒ 那是**名字撞车**，不是真正的对应。

**真正的数据源**要从"命令的语义"找 ⇒ ★ **`config_dungeon_new.Dungeon`（34 项）**：

```
Dungeon = {20001: {name:"极地寻宝", type:3, type_team:1, count:1, desc:"英雄试炼", …},
           30001: {name:"斗兽场",   type:5, type_team:4, count:0, desc:"…", …}, … 共 34 项}
```

> ★ **工具的使用边界**：`scan_table_sources` 只是**线索生成器**，
> 命中后**必须用语义核对**（`bid`/`time` 这种通用字段名尤其容易误命中）。

---

## 二、两条实现

| cmd | SC | 逐字段 |
|---|---|---|
| **`21306`** | `list:table(bid:u32, enter_count:u16, buy_count:u16, time:u32, is_finish:u8)` | `bid` ← **`Dungeon` 的键**；`enter_count` ← **配置的 `count`**；`buy_count`/`time`/`is_finish` ⇒ 0（玩家态，无源）|
| **`21312`** | `one_key_sweep_list:table(bid:u32)` | 同源 ⇒ **34 条真实 bid** |

### 实测（**逐条**与配置比对）

```
== 21306 副本列表 ==
  len=444 消耗=444 err=None 条目=34（配置 34）
  ★ 条目数与配置一致 ⇒ ✓
  ★ 逐条 bid/count 与配置一致 ⇒ ✓
== 21312 一键扫荡列表 ==
  len=138 消耗=138 err=None 条目=34
  ★ 34 条 bid 与配置一致 ⇒ ✓
=== 结果: PASS ===
```

★ `verify_dungeon_list.py` **遍历 34 条**逐对比 `(bid, count)` —— 不是抽查。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **294** / 默认 29 / **未开放 6**）/ 静态 PASS / conformance PASS / **SC 在线 35-35** / **专用 97-97** / 门禁 E **PASS** |
| 回归（**33 项**） | **新增 `verify_dungeon_list.py`** + 前 32 项 **失败数 0** |
| 判定表 | **B 20 / C 0 / A 294** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `dungeon_cfg`/`dungeon_rows` + `21306`/`21312` |
| `tools/verify_dungeon_list.py` | **新增回归第 33 项**（逐条与配置比对）|
| `tools/_fix_r147_dungeon_list.py` | 插入脚本 |
| `server/mock_server.py.bak_r147` | 改前备份 |

---

## 五、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **6** | **−13** |
| **真机发过的未实现** | 67 | **32** | **−35** |
| **专用分支** | 208 | **294** | **+86** |
| **B 类（有依据地不做）** | 57 | **20** | **−37** |
| **回归项** | 17 | **33**（失败 0）| **+16** |
| 六道门禁 | — | **全 PASS** | — |
| **C 类** | 10 | **0** | ★ 清零 |

### 下一批

| 目标 | 依据 |
|---|---|
| **`13361`**（`zone_list`/`head_list` 空间+头像）| `config_sns`/`config_friend_zone_data` |
| **`18307`**（`a_name`/`b_name` 结拜/婚宴）| —— |
| 真机剩余 32 条 | 按 `gap_worklist` |
| ★ **启用全局兜底**（`global_default_sc`）| 让 1144 条潜在缺口都有安全应答 |
