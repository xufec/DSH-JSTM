# R194（新目标④）：**解构器再进一步 —— `ISNEN`/`RET1`/`RET0` + 返回值合并，救回 10 个配置**

> 新目标第 4 批。★ 在 R193（`IST`/`JMP`）之后，**再救回 5 个**（累计 10 个）。
> **时间**：次日 03:30 – 05:30。

---

## 一、★ 本批发现的三个"未处理指令"

### ① `config_skill` 用 **`ISNEN`**（不是 `IST`）

```
指令直方图: TDUP=17727, TSETB=17400, **ISNEN=8700**, **JMP=8700**, **RET1=8700**, TNEW=8373, RET0=1
```
★ R193 只处理了 `IST` ⇒ **`ISNEN` 落空** ⇒ 流程乱。

**修**：**把所有"测试"指令**（`ISNEN`/`ISNE`/`ISEQN`/`ISEQ`/`ISLT`/`ISGE`/`ISLE`/`ISGT`/`ISF`/`ISTC`/`ISFC`）
在本工具的**线性模拟**里**统一按"不跳"处理** —— 目的不是"精确模拟控制流"，
而是**让 `pc` 不因未识别指令而乱跳**，从而让后续的 `TDUP`/`TSETB` **把数据全部塞进容器**。

### ② `config_skill` 的每个分支以 **`RET1`** 结尾（8700 个）

**修**：**跳过返回、继续线性执行**（配置 chunk 的语义是"建表"，不是"函数调用"）。
★ 安全性：外层 `while _pc < len(pt.bc)` 保证不会越界。

### ③ ★★ 有的 chunk **只建表到寄存器、最后 `RET1` 返回**（没有 `GSET`）

`config_skill` proto0 **没有任何 `GSET`** ⇒ 只看 `gvars` 永远是空表。

**修**：**`RET1`/`RET0` 时把返回值（`regs[a]`）也收进 `_rets`**，函数末尾**并进结果**。
★ 并**过滤以 `__` 开头的键**（`__index` 是**元表字段**，不是配置数据）。

---

## 二、★ 本批一处自纠（**一行之差**）

第一版写成：
```python
if not gvars and _rets:     # ★ 错！`config_skill` proto0 的 gvars 非空 ⇒ 跳过合并
```
⇒ **仍 2 字符**。改成 **`if _rets:`（总是合并）** ⇒ **`config_skill` 从 737 → 1462** ✓

> **★ 纪律第 36 条**：**"兜底式的条件"要问一句"这个条件会不会永远为假"** ——
> `if not gvars and _rets` 看起来"只在没有全局变量时才用返回值"，
> ★★ 但**实测 `gvars` 非空**（有 `Config={}`）⇒ **永远跳过** ⇒ **等于没写**。

---

## 三、★★ 结果：**救回 10 个**（本批新增 5 个）

```
③ ★ 救回 10 个（原来空、现在有数据）：
   config_common               1365 字符（proto0/1）
   config_fangyao               348 字符（proto0/1）   ← 本批新增
   config_fashion_constant      340 字符（proto0/1）   ← 本批新增
   config_guild_welcome_data    270 字符（proto0/1）   ← 本批新增
   config_item               659004 字符（proto1/2）   ← R193
   config_mission_treasure      254 字符（proto0/1）   ← 本批新增
   config_mon_data              311 字符（proto2/3）   ← R193
   config_skill                1462 字符（proto2/3）   ← 本批 737 → 1462
   config_skill_magic          1474 字符（proto2/3）   ← 本批 743 → 1474
   config_trap                  284 字符（proto0/1）   ← 本批新增
④ 非空的文件**一律未动**（保护已有数据）✓
```

**验证**：**66 项回归失败 0** ｜ 门禁全 PASS ✓

---

## 四、★ 仍未解决的（**如实记录**）

| 配置 | 状况 | 原因 |
|---|---|---|
| **`config_skill` proto0** | 仍 2 字符 | ★ 它的 **8700 条技能在"嵌套函数"里**（proto0 是个函数、由 proto2 调用）⇒ **线性模拟拿不到** |
| **`config_mon_data`** | 311（`Mon: 0`）| 同上（`proto0` 有 58359 条，数据在嵌套函数）|
| **`config_drop_item`/`config_client`/`config_role_attribute`** | 仍空 | 待逐个诊断 |
| 仍空配置 | **约 60 个** | 逐批诊断 |

★ **⇒ 结论**：**"线性模拟"能拿到"chunk 顶层建表"的数据**（如 `config_item` 的 3013 条），
   **但拿不到"嵌套函数返回"的数据** ⇒ **下一步要"识别函数并调用"**（或**直接扫描 `TableConst` 常量池**）。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| ★ **`tools/config_deconstruct.py`** | **`ISNEN` 等测试指令 + `RET1`/`RET0` + 返回值合并 + `__` 键过滤** |
| `tools/_diag_r194.py` | ★ **参数化诊断**（任意 cfg + proto ⇒ 规模/解构长度/末尾 20 条/指令直方图）|
| `server/cfg/config_{fangyao,fashion_constant,guild_welcome_data,mission_treasure,trap}.json` | ★ 本批救回 |
| `server/cfg/config_{skill,skill_magic}.json` | ★ 1462 / 1474 |

---

## 七、下一批

| 目标 | 依据 |
|---|---|
| ★★ **"嵌套函数返回"的数据** | 扫描 `TableConst` 常量池（**`config_skill` proto0 的 `KGC=17727`** 里全是技能表）|
| ★ **仍空约 60 个配置** | 用 `_diag_r194.py` 逐个看 |
| ★ **B 类 15 条 + 回执型复查**（目标②）| — |
