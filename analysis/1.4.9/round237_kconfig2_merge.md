# R237（新目标④）：★★★ **"散片合并"规则 —— `12601` 从"60 个残缺行"变成"9 个真实恶魔"**

> 新目标第 7 批。★★★ **核心突破：修正 R221 的转换规则，解锁"多 dict 各装一行"型的配置。**
> **时间**：次日 08:30 – 11:00。

---

## 一、★★★ 诊断：R221 的转换规则**在"多 dict 各装一行"型上失败**

`cfg_kconst/config_demon.json` 的 `kgc` 有 **118 项**：

```
[ 0] dict  hash={"action_power_kill":10, "balance_ratio":1}         ← ★ 全局参数（无关键键）
[ 1] 'DemonKeyValue'                                                ← ★ 分组标识（字符串）
[ 2] list  [null,3,5,7,9,11]                                        ← ★ 数组型（阶段序列）
…
[ 9] dict  hash={"lev_up_chip":130, "lev":5, "cost":400, "chip_sum":310}
```

**关键键频次**（**决定性证据**）：
```
bid                   9      ← ★★★ **只有 9 个恶魔！**（不是 60）
career/name/nature/star_lev/chip/res_id   各 9
action_power         45      ← ★ **数组型**（每个恶魔多阶段）
lev_up_chip/lev/cost/chip_sum   各 5
action_power_kill/balance_ratio 各 1
```

★★ **⇒ R221 的规则**（**"每个 dict 当一行"**）**把"散片"当成了行** ⇒
   **`cfg_kconfig/config_demon` 得到 60 个"残缺行"**（每行只有 2–4 个字段）❌

---

## 二、★★★ 修：**"按关键键分组合并散片"**（`tools/kconst_merge.py`）

```python
KEYCAND = ('bid', 'id', 'uid', 'index', 'type')

def merge_rows(kgc):
    """★ ① 含关键键的 dict ⇒ "一个实体的开头"
       ② 后续不含关键键的 dict ⇒ 合并进"当前实体"
       ③ 数组型（list）⇒ 归入 lists（不硬配）"""
```

### ★ 结果（**`server/cfg_kconfig2/`，245 个 / 10.1 MB**）

| 配置 | `cfg_kconfig`（旧）| ★ **`cfg_kconfig2`（新）** |
|---|---|---|
| **`config_demon`** | **60 个残缺行** | ★★ **9 个完整恶魔** + 1 个 `_global` ✓ |
| `config_mission` | 2462 | **849**（**更接近真实行数**）|
| `config_npc` | 707 | **592** |
| `config_chengjiu` | — | **343** |
| `config_title` | — | **175** |
| `config_map` | — | **124** |

### ★★★ `config_demon` 的实测（**完整行！**）

```
[90080] = {"nature":3, "name":"风辅助", "career":3, "star_lev":1, "chip":52008,
           "bid":90080, "res_id":"M26001", "action_power":50}
[90070] = {"nature":2, "name":"宁静之雨", "career":3, ...}
[90060] = {"nature":1, "name":"火辅助", "career":3, ...}
```

---

## 三、★★★ 服务端接入：`kcfg2()` + `12601` 接真值

```python
kcfg2(name)        # ★ 读 cfg_kconfig2/（"散片合并"版）
kcfg2_rows(name)   # ★ [(id, row), …]（跳过 _global）
```

### ★ 实测（**从"全 0"到"真值"**）

| 版本 | 输出 |
|---|---|
| R236（`kcfg`）| `demon_list=60`，**首条全 0** ❌ |
| ★ **R237（`kcfg2`）** | ★★ **`demon_list=9`**，`bid=90080 career=3 star_lev=1 nature=3 chip=52008 action_power=50` ✓ |

```
12601: len=175 消耗=175 err=None ｜ ★ demon_list=9（应 9）
   [0] bid=90080 career=3 star_lev=1 nature=3 chip=52008 action_power=50
   [1] bid=90070 career=3 star_lev=1 nature=2 chip=52005 action_power=50
   [2] bid=90060 career=3 star_lev=1 nature=1 chip=52002 action_power=50
⇒ PASS
```

> **★ 纪律第 77 条**：**"常量池 → 配置表"必须"按关键键合并散片"** ——
> ★★ **判据**：**"某关键键（`bid`/`id`/`uid`）在 `kgc` 里出现的次数 = 真实行数"**
> （`config_demon`：`bid` 9 次 ⇒ **9 个恶魔**，**不是 60**）。
> ★★★ **可靠做法**：**"含关键键的 dict 开一个新实体，后续无关键键的 dict 合并进去"**。

---

## 四、★ 四层目录的最终状态

| 目录 | 文件 | 体积 | 规则 |
|---|---|---|---|
| **`server/cfg/`** | 231 | 9.3 MB | **线性解构**（R192–R195）|
| **`server/cfg_kconst/`** | 285 | 15.3 MB | **原始常量池**（R195）|
| `server/cfg_kconfig/` | 245 | 13.6 MB | **每个 dict 当一行**（R221，**有残缺行**）|
| ★★ **`server/cfg_kconfig2/`** | **245** | **10.1 MB** | ★★ **按关键键分组合并**（**R237，完整行**）✓ |

★ **⇒ `cfg_kconfig2` 是**目前最好**的"从常量池还原的配置表"** ✓

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1546** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| ★ **`12601`** | **9 个真实恶魔**（**字段全有真值**）✓ |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| ★★★ **`tools/kconst_merge.py`** | ★★★ **"散片合并"转换器**（**按关键键分组**）|
| ★★★ **`server/cfg_kconfig2/*.json`** | ★★★ **245 个"完整行"配置**（10.1 MB）|
| ★★ **`server/mock_server.py`** | **`kcfg2()` / `kcfg2_rows()`** + `12601` 接真值 |
| `tools/_diag_r237.py` | ★ **`config_demon` 的原始 kgc 诊断**（**关键证据**）|

---

## 七、下一批（**用 `cfg_kconfig2` 解锁更多命令**）

| 方向 | 理由 |
|---|---|
| ★★★ **重跑 `scan_gap_sources.py`，用 `cfg_kconfig2` 当配置源** | **会有一批新候选**（**旧扫描用的是 `cfg`/`cfg_kconfig`**）|
| ★★ **`config_mission`（849 行）→ 任务族** | 已用 `missions` |
| ★★ **`config_chengjiu`（343 行）→ 成就族** | — |
| ★ **`config_title`（175 行）→ 称号族** | — |
