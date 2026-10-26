# R108：修解构器残留 —— 根因是**容器可能是模板对象**

> 上一轮（R106）解构器只解出"静态挂载"的部分，深层全是空 `{}`。
> 本轮用 trace 定位到**一行根因**，修完后 `cost` / `AllFanhuan` / 符文 `assets`+`effect` 全部解出。
> **时间**：2026-09-29 03:40 – 04:05。

---

## 一、根因定位：写了 `tools/_trace_decode.py` 逐条打印

把 `config_invest` 前 20 条字节码逐步跑一遍、打印每步的 `regs` 与"是否写入"，立刻看到：

```
 8  TNEW  A=3         ; R3 = {}
 9  TDUP  A=4 D=3     ; R4 = {'gold',1000}
10  TSETB A=4 B=3 C=1 ; t[3][1] = t[4]              → 已写入（R3 是 dict）
11  TSETS A=3 B=2 C=4 ; t[2]['cost'] = t[3]
      | cont类型=TableConst → ★ 跳过（容器非 dict 或键非 str）
12  TSETB A=2 B=1 C=2 ; t[1][2] = t[2]              → 已写入
```

**⇒ 一行根因**：第 11 行的**容器 `R2` 是 `TableConst`（模板对象），不是 `dict`** ——
我第一版只认 `dict`，于是**凡是以模板为容器的写入全被静默丢弃**。

这不是个别现象：配置里的具名子表都是 `TDUP` 拿到模板后**直接往模板上挂键**
（`TSETS`/`TSETB`），所以**大部分深层内容都走了这条路径** ⇒ 全丢成空 `{}`。

---

## 二、修法（一个函数 `_set()`）

```python
def _set(cont, key, val):
    if isinstance(cont, dict):          # TNEW 出来的新表
        cont[key] = val
    elif isinstance(cont, TableConst):  # ★ TDUP 出来的模板对象
        (cont.hash if cont.hash is not None else []).append((key, val))
    ...
```

`TSETS` / `TSETB` / `TSETV` 三条写入指令**统一走 `_set`**。

---

## 三、成果（实测）

### `config_invest` —— `cost` 出来了

```
InvestType:
  "2" 登录基金  is_charge=0  cost = {"1": [null, "gold", 1000]}     ← ★ 1000 金币
  "3" 等级基金  is_charge=0  cost = {"1": [null, "gold", 1500]}     ← ★ 1500 金币
  "7" 豪华投资  is_charge=1  cost = {}
  "8" 至尊投资  is_charge=1  cost = {}

AllFanhuan:                       ← ★ 全返还，之前完全解不出
  "2" { normal: {"1": [null, "gold", 1500]}, … }
```

（`cost` 的 `[null,'gold',1000]` 是 Lua 的 `{"gold", 1000}` —— **金币 1000**。）

### `config_rune_data` —— 顶层键 7 → **8**，且**深层全出来了**

符文等级表的每一项现在含：

```
name / effect_desc / lev / rune_id / power / is_open
★ assets: {1: [null, "rune_exp", 443]}              ← 升级消耗（星魂经验 443）
★ effect: {1: [null, "attr", "atk_speed", 2160]}    ← 属性加成（攻速 +2160）
item_list / attr
```

★ 例：`风云(21595)` 1→50 级，`rune_exp` 从 443 递增，`atk_speed` 从 2160 到 10000 —— **整条曲线都在**。

---

## 四、★ 残留：`RuneExchange` 的**内容解出了，但键名丢了**

`RuneExchange` 现在**存在**（顶层第 8 个键），但它的键**是一个 `TableConst` 对象**
（`{'50': {1: {...level表...}}}`），而不是字符串 `'RuneExchange'`。

⇒ **它的内容可用**（就是那张 `{等级: {级数: {字段}}}` 的表），
但**顶层键名没还原出来**。原因：该键在字节码里是**运行时用表对象当键**（`TSETV`），
而 `_key_repr()` 对"没有 `id/bid/lev/rune_id/type` 字段的表"只能退化成 `TC#…`。

**这是明确的待修点**（不影响其他 7 个顶层键的数据）。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽** / CS 2463-0 / SC 静态 71+1空-0 / SC 在线 **71-71** / 专用 **76-76** / 门禁 E **PASS** |
| 回归（12 项） | 全 PASS（本轮**只改工具**，未动服务端）|
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `tools/config_deconstruct.py` | 新增 `_set()`（容器可以是 `TableConst`）；三条写入指令统一走它 |
| `tools/_trace_decode.py` | **新增**：逐步 trace，就是它定位到那一行根因 |
| `_tmp_cfg/config_invest_dec.json` | 现在含 `cost`/`AllFanhuan` |
| `_tmp_cfg/config_rune_dec.json` | 顶层键 7→8，`assets`/`effect` 深层全出 |
| `analysis/1.4.9/round108_deconstructor_fix.md` | 本报告 |

---

## 七、一句话

> **根因是一行**：配置里的具名子表都是"`TDUP` 拿模板 → 直接往**模板对象**上挂键"，
> 而我第一版只认 `dict` 容器 ⇒ **所有这类写入被静默丢弃**。
> 修完 `_set()` 后：`cost`（1000/1500 金币）、`AllFanhuan`、符文 `assets`（升级经验）与
> `effect`（属性加成曲线）**全部解出**。
> `RuneExchange` 的内容也已在，**只剩顶层键名**没还原（`TSETV` 用表对象作键）—— 记为待修点。
