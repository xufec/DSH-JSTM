# R154：候选池第三批 3 条（伙伴详情 / 魂兽详情 / 阵法位）

> 新目标第 3 批。**专用分支 311 → 314**。
> **时间**：2026-09-30 21:00 – 21:35。

---

## 一、3 条实现（真实值都核对过）

| cmd | CS | SC | 真实源 |
|---|---|---|---|
| **`11201`** | `[]` | `{id,bid,type,color,lifttime,lev,exp,grow,score,stage,rebirth,acc,partner_attr,power,aptitude,innate_skill,skill,jindan_skill,talisman_skill,ext}`（**20 字段**）| ★ `role_heros`（**18 行**）+ `role_power` |
| **`12602`** | `{demon_bid:u32}` | `{bid,career,star_lev,nature,chip,action_power,power,skill}` | ★ `config_demon` + `role_heros.chip` |
| **`11412`** | `[]` | `{pos,realm,state,skill_list}` | `role_heros.state` |

### 实测

```
== 11201 伙伴详情 ==
  len=48 消耗=48 err=None id=30800 bid=30800 color=1 lev=1（DB bid=30800 color=1 lev=1）
  ★ bid/color/lev 与 role_heros 一致 ⇒ ✓
== 12602 魂兽详情 ==
  len=19 消耗=19 err=None bid=30800 chip=0（DB chip=0）  ★ 回真实 bid + chip ⇒ ✓
== 11412 阵法位 ==   len=5 消耗=5 err=None state=1（DB state=1）  ★ ⇒ ✓
=== 结果: PASS ===
```

★ **真实**：`bid`/`color`/`lev`/`exp`（伙伴）、`chip`（魂兽碎片）、`state`（出战态）、`power`。
★ **无源 ⇒ 0**（真话）：`grow`/`score`/`stage`/`rebirth`/`acc`/`star_lev`/`nature`。
★ **子表 ⇒ 空**（8 条已登记）：`partner_attr`/`aptitude`/`skill`/`jindan_skill`/`talisman_skill`/`ext`/`skill_list`。

---

## 二、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **314** / 默认 21 / 未开放 6）/ 静态 PASS / conformance PASS / **SC 在线 27-27** / **专用 102-102** / 门禁 E **PASS** |
| 回归（**38 项**） | **新增 `verify_gap_batch3.py`** + 前 37 项 **失败数 0** |
| 判定表 | **B 15 / C 0 / A 314** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 三、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `demon_cfg`/`demon_one` + `11201`/`12602`/`11412` |
| `tools/verify_gap_batch3.py` | **新增回归第 38 项**（三个真实值都核对）|
| `tools/_fix_r154_gap_batch3.py` | 插入脚本 |
| `tools/_emitted_empty_allow.json` | 新增 8 条理由（共 120 条）|
| `server/mock_server.py.bak_r154` | 改前备份 |

---

## 四、新目标进度

| 指标 | R152 | R153 | 现在 |
|---|---|---|---|
| **专用分支** | 306 | 311 | **314** |
| **回归项** | 36 | 37 | **38**（失败 0）|
| **真候选池** | 22（已做 4）| 22（已做 9）| **22（已做 12）** |
| 六道门禁 | 全 PASS | 全 PASS | **全 PASS** |

### 下一批（候选池还剩 10 条）

| 目标 | 依据 |
|---|---|
| `16610` / `16634` / `16636`（活动/礼包，`cost_item`/`cost_num`/`end_date`）| `config_lucky_box_data` / `config_treasure_box_data` |
| `10947`（`power, flyup_lev`）| `config_eqm_ancient` |
| `10541` 兄弟 `10542`–`10545`（同族）| 先看 `105xx` 全家 |
| ★ 把"字段独特性"筛法**推广到 `10xxx`（146 条）/ `13xxx`（226 条）大族** | `classify_gap.py` |
