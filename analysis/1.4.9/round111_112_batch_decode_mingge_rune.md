# R111–R112：批量解构 204 个配置 + 落地 `19400`（命格）与 `21405`（魂星兑换，**真扣材料**）

> 项目方指示「自行补完余下未实现的功能，不用再请示」。本轮先做了一件**乘法性**的事：
> 把 R106–R109 做出来的对齐解构器**批量**跑遍全部配置；然后立刻用它落地两条命令。
> **时间**：2026-09-30 00:10 – 00:25。

---

## 一、★ 批量解构：**204 个配置一次性解锁**

新增 `tools/batch_deconstruct.py`（复用 R106–R109 的对齐解构器），把 APK 里
**全部 `config_*.luac`** 解构成 JSON，落到 `server/cfg/`（**222 个文件**）。

```
=== 解构成功且有顶层键：204 个 ===
  config_manor             19 键    42.4 KB      config_lingshou      14 键   121.5 KB
  config_ride              14 键   142.9 KB      config_intensify     13 键    86.4 KB
  config_fabao             11 键   148.2 KB      config_guild         11 键    32.2 KB
  config_rune_data         10 键  1727.7 KB      config_mingge         9 键    96.6 KB
  config_partner_shenqi     9 键   386.1 KB      config_attr           8 键     8.1 KB
  config_shenqi             7 键   561.1 KB      config_arena_data     6 键    29.9 KB
  config_chair              6 键    61.8 KB      config_wing_data      6 键
  config_vip                5 键                 config_market         7 键    37.7 KB
  …
=== 解出但为空：18 个 ===（那些是纯数字键的平铺表，老提取器本来就能处理）
```

### 三个自己踩的坑（都记下来）

| # | 现象 | 真因 | 修法 |
|---|---|---|---|
| 1 | `ValueError: I/O operation on closed file` | `batch` 与 `config_deconstruct` **各包了一层 `sys.stdout`**，前一层被 gc 关闭 | batch **不再包** stdout |
| 2 | 同上（第二次，来自插桩） | R108 在 `_key_repr` 留的**调试插桩**还在 | 移除插桩 |
| 3 | ★ **`19400` 改了却仍回"默认响应"** | R111 脚本里的正则写成 `r'...\\s*='`（**双反斜杠**），在单引号 heredoc 里成了字面量 ⇒ **没匹配到集合** ⇒ 误报"不在通用集合里" ⇒ **`19400` 留在 `_GENERIC_DEFAULT_CMDS` 里遮蔽了新实现** | 用 `.py` 文件写正则（单反斜杠），**不经 shell 转义** |

---

## 二、`19400`（命格背包）

配置依据：`config_mingge`（9 键：`Mingge` / `MinggeOpen` / **`MinggeOther`** / `MinggeLevup` /
`MinggeStage` / `MinggeGongming` / `MinggeTuiJian` / `MinggeHandBook` / `MinggeTuiJianBook`）。

| 协议字段 | 来源 |
|---|---|
| `bag_code` | CS 的 `bagcode` 原样回 |
| **`mingge_stage`** | ★ **`MinggeOther.stage_init`（=1）** —— **配置有出处**，而默认响应只会给 0 |
| `mingge_list` | **空** —— 本服该角色没有任何命格 ⇒ **空是真话** |

**实测**：`SC_19400 len=4 bag_code=1 mingge_stage=1 ⇒ PASS`

---

## 三、★★ `21405`（魂星兑换）—— **真扣材料**，不是假装成功

数据源（R109 解出）：`RuneExchange[].assets = {"1": [null, "rune_chip", 4500]}` ⇒ **4500 符文碎片**。

**实现**（用现成的 `db_get_assets` / `db_add_assets`，后者支持负数=扣除）：

```
1. rune_bid 必须命中 RuneExchange（同时认 rune_id 与条目 id —— 客户端字段名叫 rune_bid，
   两种编号都可能，两个都认最稳）
2. 取该条 assets 的消耗，乘 num
3. 余额不够 ⇒ code=0 + 诚实 msg；够 ⇒ 扣掉 + code=1
```

**实测（三条路径）**：

| 场景 | 结果 |
|---|---|
| `rune_bid=99999`（无效） | `code=0, msg='无效星魂'` ✓ |
| 材料不足 | `code=0, msg='材料不足(rune_chip)'` ✓ |
| **有材料（20000 碎片）兑 21403** | **`code=1`，`rune_chip 15500 → 11000`（恰好扣 4500）** ✓ |

> ★ 这是**真功能**：有消耗、有校验、失败有明确提示 ——
> 比"通用默认响应"（什么都不做却回成功）强得多。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **198** / 默认 49 / 未开放 20）/ CS 2463-0 / SC 静态 **69+1空-0** / SC 在线 **69-69** / 专用 **76-76** / 门禁 E **PASS** |
| 回归 | 原 12 项 **全 PASS**；**新增第 13 项** `verify_mingge_rune.py` **PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `tools/batch_deconstruct.py` | **新增**：批量解构全部配置 → `server/cfg/*.json`（**222 个**）|
| `server/cfg/` | **204 个可用的配置 JSON**（乘法性成果）|
| `server/_mingge_cfg.json` | `19400` 用到的命格配置最小集 |
| `tools/_fix_r111_mingge.py` / `_fix_r111b_moveset.py` | `19400` 实现 + 修正集合移出 |
| `tools/_fix_r112_rune_buy.py` | `21405` 实现（`rune_exchange_cost` + 真扣费）|
| `tools/verify_mingge_rune.py` | **新增回归第 13 项** |
| `server/mock_server.py.bak_r111` / `.bak_r112` | 改前备份 |
| `analysis/1.4.9/round111_112_batch_decode_mingge_rune.md` | 本报告 |

---

## 六、★ 批次结论与下一步（不请示，按本清单继续）

**已完成**（本目标内）：`19400`（命格）、`21405`（魂星兑换真扣费）。

**审查过的"不值得做"**（都写清依据，避免重复投入）：

| cmd | 结论 |
|---|---|
| `20800`（座椅）/ `11600`（翅膀） | 玩家**没有**该物 ⇒ 全 0 **与默认响应等价** |
| `17001`（关卡） | `dungeon_progress` 只有副本**设置**、**没有关卡进度** ⇒ 无源 |
| `16706`（VIP 道具） | 只比默认响应多一个 `status` 位 ⇒ 增量极小 |
| 社交域（team/circle/friend/friendback/market/wedding/guild_race） | **1 个角色** ⇒ 空即真话 |

**下一步（按价值排序，将继续推进）**：
1. **`21406`（魂星升级）** —— `RuneBase` 的 `rune_exp` 曲线已解出（443→13884，50 级）
2. **`21402`/`21403`（装备穿脱）** —— `equip_items` 有真实数据（6 件）
3. **`13741`（建筑/庄园）** —— `config_manor`（19 键）已解出
4. **`15501`（坐骑）** —— `config_ride`/`config_lingshou`（14 键×2）已解出
5. **`15700`（神器）** —— `config_shenqi`（7 键）/`config_partner_shenqi`（9 键）已解出
6. **"获得途径"**：让玩家能获得命格/翅膀/座椅/坐骑 —— 这样那些"全 0"的命令才有真实数据
