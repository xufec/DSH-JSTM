# R193（新目标④）：★★★ **解构器工程的决定性突破 —— 实现 `IST`/`JMP`**

> 新目标第 3 批。★★★ **`config_item` 从 120 字符 → 659004 字符（×5492 倍）**，**3013 条物品数据全部解出**。
> **时间**：次日 01:30 – 03:30。

---

## 一、★★★ 根因链（**三步诊断，每步都有证据**）

### 第 1 步：`config_item` 解构出什么？（`_diag_r193.txt`）

```json
{"Config": {"ItemDecomList": {"18071": {...}}}}     ← ★ 只有 1 项，1117 个物品全丢
```

### 第 2 步：跟踪寄存器 `R1`（`_diag_r193b.txt`）

```
TNEW a=1（重建 R1）: [6, 65456, 65465]      ← ★ R1 被"重建"3 次
TSETB b=1（写 R1[key]）: 只 1 次 ⇒ R1[2] = R2
GSET: #4 Config=R0 ｜ #65457 Config=R1 ｜ #65466 Config=R1   ← ★ Config 被换成 R1
```

### 第 3 步：看末尾 30 条（`_diag_r193c.txt`）—— **真相**

```
#65438  TSETS   R0['ItemData'] = R1        ← ★★ 物品表已挂到 Config['ItemData']！
#65453  GGET    a=1                        ; R1 = Config
#65454  IST     a=0                        ; if R1 then
#65455  JMP     a=2  d=32769               ;   goto pc+1+(d-0x8000) = #65457
#65456  TNEW    a=1                        ; R1 = {}      ← 只在"Config 为空"时
#65457  GSET    a=1                        ; Config = R1
```

★ **⇒ 这是 Lua 的 `if not Config then Config = {} end` 惯用法**！
★★ **⇒ 而 `deconstruct` 不处理 `IST`/`JMP`** ⇒ 它**照直执行 `TNEW` + `GSET`**
   ⇒ **`Config` 被换成空表** ⇒ **`ItemData`（1117 物品）/`ItemJewel` 全丢** ❌

---

## 二、★ 修法：**实现 `IST` / `JMP`**（LuaJIT 语义）

```python
_pc = 0
_ist = False
while _pc < len(pt.bc):
    ins = pt.bc[_pc]
    ...
    elif name == 'IST':
        _ist = bool(regs.get(a))            # 测试寄存器（供紧随的 JMP 用）
    elif name == 'JMP':
        if _ist:                            # ★ 仅当 IST 为真时跳
            _pc = _pc + 1 + (d - 0x8000)
            continue
    _pc += 1
```

★ **⇒ `JMP` 目标 = `pc + 1 + (d - 0x8000)`**（`d` 为 `(ins>>16)&0xffff`）
★ **⇒ `IST` 为假 ⇒ 顺序执行**（正是 `if not X then` 的语义）✓

---

## 三、★★★ 结果

```
config_item  proto1 ⇒ **659004 字符**（原 120；×5492 倍）
   Config → [('ItemData', **3013**), ('Item', 0), ('ItemJewel', 17), ('ItemDecomList', 1)]
```

**安全版自动解构**（只补"原来就空"的）：
```
③ ★ 救回 5 个：
   config_common            1365 字符（proto0/1）
   config_item            659004 字符（proto1/2）    ← ★★ 决定性
   config_mon_data           311 字符（proto2/3）
   config_skill              737 字符（proto2/3）
   config_skill_magic        743 字符（proto2/3）
④ 非空的文件一律未动（保护已有数据）✓
```

**验证**：**66 项回归失败 0** ｜ 门禁全 PASS ✓（**659004 字符的新配置未破坏任何东西**）

> **★ 纪律第 35 条**：**"解构/反编译"类工具的"控制流指令"必须实现** ——
> `IST`/`JMP`（条件跳转）看起来"只影响控制流"，
> ★★ 但**配置脚本大量使用 `if not X then X = {} end` 惯用法** ⇒
>    **不实现跳转 ⇒ 会"无条件执行初始化"⇒ 把已挂好的数据覆盖成空表**。
> ★★★ **判据**：**"解构结果异常小" ⇒ 先查"未处理的控制流指令"**（本批的 `IST`/`JMP` 就是）。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| ★★ **`tools/config_deconstruct.py`** | **实现 `IST`/`JMP`**（循环 `for` → `while` + `_pc`）|
| `tools/_diag_r193{,b,c,d}.py` | ★ **三步诊断链**（寄存器跟踪 → 末尾指令 → 验证）|
| `server/cfg/config_item.json` | ★★ **659004 字符**（3013 条物品）|
| `server/cfg/config_{common,mon_data,skill,skill_magic}.json` | ★ 救回 |
| `tools/config_deconstruct.py.bak_r193` | 改前备份 |

---

## 六、下一批

| 目标 | 依据 |
|---|---|
| ★ **`config_skill` 仍只有 737**（`Skill: 0`）| 它的数据可能在**别的 proto 或更深层** ⇒ 用同一套诊断 |
| ★ **`config_mon_data` 仍 311**（`Mon: 0`）| 同上 |
| ★ **`config_drop_item`/`config_client`/`config_role_attribute` 仍空** | 同上 |
| ★ **B 类 15 条 + 回执型复查**（目标②）| — |
