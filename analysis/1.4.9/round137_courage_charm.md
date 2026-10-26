# R137：实现 `13331`（勇气值 / 魅力值 + 排名）—— 依据 `config_game_data` 的**权威资产定义**

> 新目标第 14 批。这批的价值在于：**找到了 `courage`/`charm` 的权威出处**，
> 从而把一个"只回默认响应"的命令变成**读真实资产 + 榜上有我**。
> **时间**：2026-09-30 11:05 – 11:35。

---

## 一、★ 依据：`config_game_data` 里的**标准资产表**

`tools/scan_table_sources.py` 的思路反过来用了一次：**从"字段名"去找配置**，
结果在 `server/cfg/config_game_data.json`（R111 批量解出）里找到**权威定义**：

```
CodeToAssets : [null, "gold", "coin", "coupon", "exp", "sinew", "experience",
                "vitality", "guild_contrib", "practice_exp", "tower_cent",
                "arena_cent", "shilian", "coral", "rmb", "hero_exp",
                ★"courage"(16), ★"charm"(17), "trophy"(18), "lingqi", …]
AssetsEnToCode: {gold:1, coin:2, coupon:3, …, courage:16, charm:17, trophy:18, …}
AtomToDesc    : {courage:"勇气值", charm:"魅力值", …}
AtomToSource  : {courage:0, charm:0, …}
```

⇒ `courage`/`charm` 是**标准资产**（与 `gold`/`coin` 同一张表）
⇒ 直接用现成的 `db_get_assets` / `db_add_assets`（`role_assets` 表），**无需新建表** ✓

---

## 二、实现

```
CS_13331（空） → SC_13331{courage:u32, charm:u32, courage_rank:u8, charm_rank:u8}
```

| 字段 | 来源 |
|---|---|
| `courage` / `charm` | ★ **真实 DB**（`role_assets`；没有行 ⇒ 0）|
| `courage_rank` / `charm_rank` | ★ **"榜上有我"**（R130 的判据）：值为 0 ⇒ 未上榜 ⇒ 0；> 0 ⇒ 本服唯一角色 ⇒ **rank 1** |

★ 发放入口**已存在**（通用资产接口）：`GET /DSH_ADMIN/setassets?courage=100&charm=50`

### 实测

```
== 13331（全 0）==
  len=10 消耗=10 err=None courage=0 charm=0 rank=(0,0)      ← 未上榜是真话
== 13331（courage=123 charm=456）==
  courage=123 charm=456 rank=(1,1)                          ← ★ 真实资产 + 榜上有我
=== 结果: PASS ===
```

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **249** / 默认 37 / **未开放 6**）/ 静态 PASS / conformance PASS / **SC 在线 43-43** / **专用 87-87** / 门禁 E **PASS** |
| 回归（**25 项**） | **新增 `verify_courage.py`** + 前 24 项 **失败数 0** |
| 判定表 | **B 27 / C 1 / A 249**（C 类新出现 1 条，待下批查）|
| 真机缺口 | **43 种**只回默认响应（`gap_worklist`）|
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `13331` 处理器；从 `_GENERIC_DEFAULT_CMDS` 移出 |
| `tools/verify_courage.py` | **新增回归第 25 项**（含 `/DSH_ADMIN/setassets` 精确置值）|
| `tools/_fix_r137_courage_charm.py` | 插入脚本 |
| `server/mock_server.py.bak_r137` | 改前备份 |

---

## 五、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **6** | **−13** |
| **真机发过的未实现** | 67 | **43** | **−24** |
| **专用分支** | 208 | **249** | **+41** |
| **B 类（有依据地不做）** | 57 | **27** | **−30** |
| **回归项** | 17 | **25**（失败 0）| **+8** |
| 六道门禁 | — | **全 PASS** | — |
| 潜在缺口兜底 | 无 | **开关已就绪**（1144 条，默认关，R136）| — |

### 下一批

1. **查 C 类那 1 条**（`gap_verdicts` 新出现）
2. 继续做真机 43 条里的可做项：`13579`（摇钱树/膜拜，有 `tree_lev`/`strength_*`）、
   `13569`（祈福）、`13806`（摆摊，可补 `role_market`）、`16706`（VIP 道具）|
3. `tools/scan_growth_cmds.py` 的剩余成长动作（座椅 `20803`–`20809`、翅膀 `11602`–`11607`）
