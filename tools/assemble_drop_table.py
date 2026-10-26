#!/usr/bin/env python3
"""把 gen_drop_table_md.py 生成的表格片段组装成 analysis/1.4.9/item/drop_table.md。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ITEM = os.path.join(ROOT, 'analysis', '1.4.9', 'item')

pool = io.open(os.path.join(ITEM, '_drop_pool_table.md'), encoding='utf-8').read().strip()
detail = io.open(os.path.join(ITEM, '_drop_detail_table.md'), encoding='utf-8').read().strip()

HEADER = r'''# 1.4.9 掉落明细表（drop_table）

> **目标 APK**：`anzbao\jstm.apk` — 绝世唐门 **1.4.9**，包名 `com.shiyue.dldl.ewan.qihoo`。
> **版本锁定声明**：本文全部数值仅来自上述 1.4.9 APK。`anzbao\jstm_142165.apk`（1.4.11）、
> `anzbao\dldlJl.apk`、`patched\*_142165*` **一律未读取**，不作为任何证据。
> 概率单位解释（千分比）在 §3，该解释标记为 `INFERRED`。

---

## 0. 汇总

| 指标 | 数值 |
|---|---|
| `Config.Drop` 条目总数 | **29** |
| `Config.DropItem` 掉落池组数 | **17** |
| `Config.DropItem.item_list` 终端条目数 | **39** |
| 展开后"怪物 → 物品"明细行数 | **75** |
| 有掉落表的怪物（在 `Config.Mon` 内） | **24**（`20001`–`20024`） |
| 表键不在 `Config.Mon` 的条目 | **5**（`30001`–`30005`） |
| `Config.Mon` 怪物总数 | 2645（覆盖率 **0.91%**） |

- **表 1**（§1）= 17 个掉落池的组内定义，即"物品 → 数量 → 概率"。
- **表 2**（§2）= 29 条掉落记录展开后的"怪物 → 掉落池 → 物品 → 数量 → 概率"。

---

## 1. 表 1：17 个掉落池（`Config.DropItem`）

来源：`analysis/1.4.9/item/_config_drop_item.json`，由
`assets/src/config/config_drop_item.luac` 还原。
全局名 `Config.DropItem`，证据：`proto#0` bc#165 `TSETS 'DropItem'`；
kgc#57 = `'DropItem'`，kgc#58 = `'Config'`。

`p_sum` 与 `pp` 的关系经 **17/17 组**算术校验通过：
`p_sum == Σ item_list[*].pp`，且 `max` 恒等于 `pp` 的前缀累加、`min == 前一 max + 1`。

'''

MID = r'''

```
概率列含义：pp / p_sum，即该条在组内被命中的概率。
例如 4001 组：p_sum=100，两条 pp 各 50  → 各 50.00%
     3001 组：p_sum=36，  pp=12 与 24  → 33.33% 与 66.67%
     3002 组：p_sum=144， pp=36/48/60  → 25% / 33.33% / 41.67%
```

---

## 2. 表 2：29 条掉落记录展开明细（75 行）

来源：`analysis/1.4.9/item/_drop_detail.csv`，由 `tools/analyze_drop.py` 生成。
"节"列对应 `Config.Drop` 记录内的三个掉落节：

- **首次** = `first` / `first_p`：`first` 是直接指向 DropItem 组 bid 的整数
- **核心** = `core` / `core_p`：`core` 同样直接指向组 bid；间隔见该条目的 `core_interval`
- **普通** = `normal`：三层结构 `normal[组bid][切片]`，
  `normal_sum` 记录每个组 bid 的 Σpp

`组内概率` = `pp / p_sum`（`p_sum` 为该 DropItem 组的权重总和）。
`档位(pp/区间)` 只有"普通"节有值，表示 `normal` 中层的切片权重与区间。

'''

FOOTER = r'''

---

## 3. 概率单位说明（重要）

### 3.1 观测到的数值范围

| 字段 | 观测到的取值 | 出现位置 |
|---|---|---|
| `pp`（DropItem 组内） | 12, 24, 25, 30, 36, 48, 50, 60, 100 | `config_drop_item.luac` |
| `p_sum` | 36, 50, 60, 90, 100, 144, 150, 200 | `config_drop_item.luac` |
| `pp`（`Drop.normal` 中层切片） | **只有 500 与 1000** | `config_drop.luac` |
| `normal_sum` | **只有 500 与 1000** | `config_drop.luac` |
| `holiday_p`（字符串） | `'[{1,1000}]'` | `config_drop.luac` |

### 3.2 结论：`pp` 是千分比（per-mille，1000 = 100%）—— 标记 `INFERRED`

支持"千分比"的证据：

1. `normal` 中层切片的 `pp` **只取 500 与 1000 两个值**，且 `normal_sum` 的对应值
   同样只取 500 与 1000。`500/1000` 与 `1000/1000` 是"半概率 / 满概率"的自然表达；
   若按百分制则是 `500%`、`1000%`，自相矛盾。
2. `holiday_p` 是字符串 `'[{1,1000}]'`，其中 `1000` 与上述量级一致。
3. 若按百分比（100 = 100%）解释，`pp=1000` 无意义。

**→ `pp` 为千分比权重，`1000 = 100%`。此解释标记为 `INFERRED`**（客户端不读这两张表，
无代码可直接证明）。

### 3.3 不能确认的部分

DropItem 组内的 `p_sum` 是 **36 / 90 / 144 / 150 / 200** 这类非 1000 的值。
这说明**组内概率不是直接写千分比，而是 `pp / p_sum` 的相对权重**。
该结论由 39/39 条 `max == pp 前缀累加`的算术事实支持，但**无代码可证**。
`p_sum` 与 `normal_sum` 之间的换算关系 → **`UNKNOWN`**。

### 3.4 INFERRED / UNKNOWN 一览

| 结论 | 标记 | 依据 |
|---|---|---|
| `p_sum == Σpp` | **已确认** | 算术，17/17 |
| `max == pp 前缀累加`、`min == 前一 max + 1` | **已确认** | 算术，39/39 |
| `组内概率 = pp / p_sum` | **INFERRED** | 无代码，仅结构推出 |
| `normal` 切片按 `1..1000` roll、命中 `[min,max]` | **INFERRED** | 同上 |
| `pp` 为千分比、`1000 = 100%` | **INFERRED** | 取值集 + 量级一致性 |
| 保底 / 多件掉落上限 / roll 次数 | **UNKNOWN** | 服务端逻辑不在包内 |
| 普通任务怪（2621/2645）的掉落 | **UNKNOWN / TEST_ONLY** | 客户端内不存在 |

---

## 4. 数值可追溯性

本文每一个数字都来自下列命令链，无任何人工估计或补全：

```powershell
python tools/apk_extract_luac.py "assets/src/config/config_drop.luac"      "analysis/1.4.9/item/_config_drop.luac"
python tools/apk_extract_luac.py "assets/src/config/config_drop_item.luac" "analysis/1.4.9/item/_config_drop_item.luac"
python tools/dump_drop_config.py analysis/1.4.9/item/_config_drop.luac      --json analysis/1.4.9/item/_config_drop.json
python tools/dump_drop_config.py analysis/1.4.9/item/_config_drop_item.luac --json analysis/1.4.9/item/_config_drop_item.json
python tools/analyze_drop.py --csv analysis/1.4.9/item/_drop_detail.csv
python tools/gen_drop_table_md.py
```

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/item/_config_drop.luac` / `_config_drop_item.luac` | 从 1.4.9 APK 提取的原始字节码 |
| `analysis/1.4.9/item/_config_drop.json` | 还原出的 `Config.Drop`（29 条 × 18 字段） |
| `analysis/1.4.9/item/_config_drop_item.json` | 还原出的 `Config.DropItem`（17 组，39 条 item_list） |
| `analysis/1.4.9/item/_drop_detail.csv` | 展开后的 75 行明细（含 `src` 溯源列） |
| `tools/dump_drop_config.py` | 嵌套表还原器（含 LuaJIT 操作数编码推导） |
| `tools/analyze_drop.py` | 统计 / 校验 / 明细生成 |
| `tools/gen_drop_table_md.py` | 表格 Markdown 生成 |
'''

out = HEADER + pool + MID + detail + FOOTER
io.open(os.path.join(ITEM, 'drop_table.md'), 'w', encoding='utf-8').write(out)
print('written %d chars' % len(out))
