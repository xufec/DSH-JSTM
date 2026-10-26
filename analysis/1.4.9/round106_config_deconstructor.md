# R106：**对齐解构器** —— 打开"超大嵌套配置"（此前提取器输出 0 条的那一类）

> 项目方要的是那个解构器。**它做出来了**，并且**用已知答案验证过**。
> 它一次性解锁了 `config_invest`（投资系统）与 `config_rune_data`（1.2MB / 20108 张表，魂星系统）。
> **时间**：2026-09-29 02:45 – 03:20。

---

## 一、为什么需要它

此前的 `tools/extract_config_table.py` 只能处理**平铺的数字键表**，
对下面这类**具名嵌套表**输出 **0 条**：

```lua
Config = {
    LuckyGoldConst = {...},
    LimitConstant  = { normal = {...}, eyou = {...} },
    LevDays        = { [3] = {25,35,45,55,65,75} },
}
```

`config_invest`（3.2KB）与 `config_rune_data`（**1.2MB / `tables(20108)`**）都是这种形状。

---

## 二、解构原理（**先用样本自洽验证，再动手**）

LuaJIT 对具名表构造发出 `TDUP`/`TNEW` + `TSETS`/`TSETB`，语义为：

| 指令 | 语义 | 说明 |
|---|---|---|
| `TDUP  A=r D=t` | `R[r] = 模板 #t` | 模板就是一个 `TableConst` |
| `TNEW  A=r` | `R[r] = {}` | |
| `GGET  A=r D=g` | `R[r] = 全局[g]` | ★ **按对象引用**（不是名字标记）|
| `TSETS A=x B=y C=k` | **`t[y][k] = t[x]`** | 值在 A、容器在 B、键在 C |
| `TSETB A=x B=y C=lit` | **`t[y][lit] = t[x]`** | 同上，键是**字面量** |
| `TSETV A=x B=y C=z` | `t[y][t[z]] = t[x]` | 键也来自寄存器 |

### 验证方式（关键）

用最小的具名配置 `config_holiday_util.luac`（1.1KB，已知 `strings(10)`）对齐：

```
5  GGET A=0 D=0        ; R0 = Config          ← 开头是 `if not Config then Config = {} end`
6  TNEW A=1            ; R1 = {}
7  TSETS A=1 B=0 C=1   ; Config['LuckyGoldConst'] = R1      ✓
9  TDUP A=1 D=3
10 TSETS A=1 B=0 C=2   ; Config['TipsConstant'] = tpl3       ✓
12 TDUP A=1 D=5 ／ 13 TDUP A=2 D=6 ／ 14 TSETS A=2 B=1 C=7
                       ; R1['charge_return_not_list'] = tpl6  ✓
15 TSETS A=1 B=0 C=4   ; Config['LimitConstant'] = tpl5       ✓
```

⇒ 解出来正好 **4 个顶层键**（`LuckyGoldConst`/`TipsConstant`/`LimitConstant`/`ChargeReturnGolds`）
—— 与 `strings(10)` 完全自洽（`en/tw/eyou/normal` 是 `LimitConstant` 的子键）✓

---

## 三、★★ 三个 bug 与修法（都是我自己踩的，记下来）

| # | 现象 | 真因 | 修法 |
|---|---|---|---|
| 1 | `顶层键 1 个：Config 0 项 []` | **`GGET` 我当成了"名字标记"**，实际是**同一对象的引用**（配置开头 `if not Config then Config = {} end`）⇒ 容器找不到、整棵树挂不上 | 维护 `gvars`（`GSET` 存、`GGET` 取**引用**）|
| 2 | `TypeError: Object of type TableConst is not JSON serializable` | `to_jsonable` **只对 `TableConst` 分支递归**，对 `dict`/`list` 直接透传 | `dict`/`list` 也递归 |
| 3 | **只解出静态挂载的部分**，`LevDays`/`LevInvest`/`RuneBase` 全是 `{}` | **缺 `TSETB`（数字字面量键）** —— `config_invest` 用了 **110 次**、`config_rune_data` **19953 次** | 补 `TSETB`/`TSETV`；语义按 `TSETS` 同族（容器在 B、值在 A）|

> **验证口径**：改完 `TSETB` 后**不是"看起来对就行"** —— 而是拿**反汇编里已知的
> `TableConst(array=[None,25,35,45,55,65,75])`** 去对：
> 解出来的是 **`LevDays = {"3": [null,25,35,45,55,65,75]}`** ⇒ **逐项吻合** ✓

---

## 四、成果（实测）

### `config_invest`（此前 **0 条**）

```
InvestType  4项  {"2":{"name":"登录基金","is_charge":0}, "3":{"name":"等级基金",...},
                  "7":{"name":"豪华投资","is_charge":1}, "8":{...}}
LevDays     1项  {"3": [null, 25, 35, 45, 55, 65, 75]}        ← ★ 与反汇编逐项一致
LevInvest   1项  {"3": {"25":…,"35":…,"45":…,"55":…,"65":…,"75":…}}
DayInvest   2项  {"7": {"1"…"7"}, "8": {"1"…"7"}}
AllFanhuan / TypeDays
```

### `config_rune_data`（1.2MB / 20108 张表）

```
RuneStatic   {"max_lev": 50, "low_exchange": 4500, "role_lev": 78}     ← ★ 真实数值
符文等级表    星移(21585) / 风云(21590–21595) / 丰饶(21390–21393)
             每级含 {name, effect_desc, lev, rune_id, power, is_open}
推荐星魂      6 项 {id, content, rune_type}
RuneContent / RuneOpenLimit / RuneOpenLimit1 / RuneBaseExp / RuneGridOpen / RuneBase
```

---

## 五、已知残留（诚实标注）

`config_rune_data` 里**部分键仍是 `TableConst(...)` 长串** ——
那些是**运行时用"表对象"作键**（`TSETV` 的键）的条目。
`_key_repr()` 已尝试取该表的 `id/bid/lev/rune_id/type` 作键，但**在这条路径上没生效**
（原因未定，可能 `TSETV` 的键寄存器在写入时还是"模板"而非"最终表"）。

⇒ **不影响主体数据**（`RuneStatic`/符文等级表/推荐星魂都已正确解出），
但**这是一个明确的待修点**，记在这里而不是假装没有。

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `tools/config_deconstruct.py` | **新增**：对齐解构器（`deconstruct()` + `to_jsonable()` + `_key_repr()`）|
| `tools/_diag_missing_ops.py` | **新增**：诊断"出现但解构器没处理"的 opcode（就是它定位到 `TSETB`）|
| `tools/_show_decoded.py` | 展示解构结果 |
| `_tmp_cfg/config_invest_dec.json` | **解构成果**（投资系统，此前 0 条）|
| `_tmp_cfg/config_rune_dec.json` | **解构成果**（魂星系统，1.2MB）|
| `analysis/1.4.9/round106_config_deconstructor.md` | 本报告 |

---

## 七、一句话

> **解构器做出来了，并且是用"已知答案"验证过的**：`LevDays` 解出 `[null,25,35,45,55,65,75]`，
> 与反汇编里的 `TableConst` **逐项吻合**。
> 三个 bug 都是我自己踩的（`GGET` 的引用语义、`to_jsonable` 不递归 dict、**缺 `TSETB`**），
> 其中 `TSETB` 是**真正卡住的那个**（`config_rune_data` 用了 19953 次）。
> ⇒ `config_invest`（投资）与 `config_rune_data`（1.2MB 魂星）**现已可解**，
> 之前判为"暂不做"的 `16500`/`17200`/`21410`/`21411` 等项目**解锁了**。
> 残留一处已标注：部分"表对象作键"的条目仍是长串。
