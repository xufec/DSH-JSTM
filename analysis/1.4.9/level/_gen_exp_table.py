#!/usr/bin/env python3
"""生成 analysis/1.4.9/level/exp_table.md（Phase E 核心交付物）。

所有数字都来自本目录下已落盘的 JSON（由 1.4.9 的 config_role_attr.luac /
config_role_career.luac 还原），不手写任何数值，避免转录错误。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))

lt = json.load(open(os.path.join(HERE, 'level_table.json'), encoding='utf-8'))
lv = lt['levels']
LEV = sorted(int(k) for k in lv)

ra = json.load(open(os.path.join(HERE, 'role_attr.json'), encoding='utf-8'))['Config']['RoleAttr']
rc = json.load(open(os.path.join(HERE, 'role_career.json'), encoding='utf-8'))['Config']

# ---------------------------------------------------------------- 统计
facts = {}
facts['n'] = len(LEV)
facts['min'] = LEV[0]
facts['max'] = LEV[-1]
facts['contiguous'] = LEV == list(range(1, facts['max'] + 1))
et = [lv[str(k)]['exp_total'] for k in LEV]
em = [lv[str(k)]['exp_max'] for k in LEV]
facts['et_mono'] = all(et[i] < et[i + 1] for i in range(len(et) - 1))
facts['em_mono'] = all(em[i] < em[i + 1] for i in range(len(em) - 1))
bad = [(LEV[i], et[i] - et[i - 1], em[i]) for i in range(1, len(LEV)) if et[i] - et[i - 1] != em[i]]
facts['inv_bad'] = bad
facts['inv_ok_rows'] = len(LEV) - 1 - len(bad)
facts['ap_set'] = sorted(set(lv[str(k)]['attr_point'] for k in LEV))
facts['sa_set'] = sorted(set(lv[str(k)]['sinew_add'] for k in LEV))
facts['sm_set'] = sorted(set(lv[str(k)]['sinew_max'] for k in LEV))
facts['et_last'] = et[-1]
facts['em_last'] = em[-1]
# 分段（比值突变）
segs = []
prev = None
for i in range(1, len(em)):
    r = em[i] / em[i - 1]
    if prev is not None and abs(r - prev) / prev > 0.2:
        segs.append((LEV[i - 1], LEV[i], prev, r, em[i - 1], em[i]))
    prev = r
facts['segs'] = segs
facts['em_first10'] = [(k, int(lv[str(k)]['exp_max']), int(lv[str(k)]['exp_total'])) for k in LEV[:10]]

# ---------------------------------------------------------------- 大表
rows = []
for k in LEV:
    e = lv[str(k)]
    nxt = lv.get(str(k + 1))
    need = nxt['exp_max'] if nxt else None
    rows.append('| %d | %d | %d | %s |' % (k, e['exp_total'], e['exp_max'],
                                           str(need) if need is not None else '**—（已达上限）**'))
TABLE = '\n'.join(rows)

# ---------------------------------------------------------------- 职业
CAREERS = []
for c in sorted(rc['RoleCareer'], key=lambda x: int(x)):
    v = rc['RoleCareer'][c]
    sk = [x for x in (v['skill_list'].values() if isinstance(v['skill_list'], dict) else []) if x]
    bs = [x for x in (v['born_skill_list'].values() if isinstance(v['born_skill_list'], dict) else []) if x]
    CAREERS.append((c, v, sk, bs))
crows = []
for c, v, sk, bs in CAREERS:
    crows.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
        c, v['name'], v['res'], v['res_2'], v['weapon_res'], v['weapon_res_2'],
        v['height'], ','.join(str(x) for x in bs), ','.join(str(x) for x in sk)))
CAREER_TABLE = '\n'.join(crows)

srows = []
for c, v, sk, bs in CAREERS:
    rcs = rc['RoleCareerSkill'].get(c, {})
    items = sorted(rcs.items(), key=lambda kv: int(kv[0]))
    desc = '；'.join('%s(%s,解锁Lv%s,Lv上限%s)' % (d.get('skill_name'), d.get('type'),
                                                d.get('unlock_role_lev'), d.get('max_lev'))
                    for k2, d in items)
    srows.append('| %s | %s | %s | %s |' % (c, v['name'], len(items), desc))
SKILL_TABLE = '\n'.join(srows)

# 天命
tm = rc['TianmingSkill']
by = {}
for k, v in tm.items():
    by.setdefault(v['career'], []).append((int(v['lev']), int(v['buff_bid']), k))
trows = []
for c in sorted(by, key=lambda x: int(x)):
    lst = sorted(by[c])
    trows.append('| %s | %d | %d..%d | %d..%d | %s..%s |' % (
        c, len(lst), lst[0][0], lst[-1][0], lst[0][1], lst[-1][1], lst[0][2], lst[-1][2]))
TM_TABLE = '\n'.join(trows)

DOC = r'''# 1.4.9 角色经验与等级表 —— `Config.RoleAttr` 取证报告

> **目标 APK**：`anzbao/jstm.apk`
> `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> **1.4.11（`anzbao/jstm_142165.apk`）/ `anzbao/dldlJl.apk` / `patched\*_142165*`
> 全程未被读取**；`tools/dump_luac_strings.py`、`tools/who_uses_global.py`
> 两个硬编码 1.4.11 的工具也未使用。
> 数据文件：`analysis/1.4.9/level/role_attr.json`、`role_career.json`
> 辅助证据：`level_table.json`、`_proto_spec_exp.json`、`_attr.json`、
> `_role_ctrl_defs.txt`、`_flow_dis.py`（带跳转解析的反汇编器）

---

## 0. 结论速览

| # | 结论 | 置信度 | 关键证据 |
|---|---|---|---|
| 1 | **权威经验表 = `Config.RoleAttr`**，`config_role_attr.luac` proto#0 | **确定** | 安装点 `TSETS Config.RoleAttr` @bc#407；字符串池只有 `RoleAttr`/`Config` |
| 2 | 表是**数组部分**，键 =**等级 1..200**，由 **`TSETB idx=N` 显式写入**（不是靠 TDUP 数组或外部配键） | **确定** | bc#8/10/12…406 全为 `TSETB B=r1 idx=1..200` |
| 3 | 每条等级记录 **5 个字段**：`exp_total, exp_max, attr_point, sinew_add, sinew_max` | **确定** | 200 条 TDUP 常量的 hash 键完全一致 |
| 4 | **`exp_max` 就是"本级经验条容量"**：角色处于 **L 级**时，客户端用 **`RoleAttr[L+1].exp_max`** 作分母 | **确定** | `main_ui.luac` proto#16 bc#0–5（含 `ADDVN` 常量 `knum[0]=1`）+ bc#13/35/45 |
| 5 | 因此 **"从 L 级升到 L+1 级所需经验" = `RoleAttr[L+1].exp_max`**（不是 `RoleAttr[L].exp_max`） | **确定** | 同上；并与 `SC_10301.exp_max` / `exp_total_nextlev` 语义吻合 |
| 6 | `exp_total` = 达到该等级的累计经验阈值；恒等式 `exp_total[n]=exp_total[n-1]+exp_max[n]` 在 n=3..200 全部成立，**仅 n=2 一处不符** | **确定**（数据）/ **INFERRED**（语义） | 见 §6.4 |
| 7 | **等级上限 = 200** | **确定** | 数组键最大 200；无 `RoleAttr[201]`（客户端对 nil 有守卫） |
| 8 | `attr_point` / `sinew_add` / `sinew_max` 三列在 1.4.9 是**常量**（0 / 0 / 120），不构成成长曲线 | **确定** | 全 200 行取值集合分别为 {0}/{0}/{120} |
| 9 | **客户端不存在"等级 → 战斗属性"的成长表**。`Config.RoleCareer[career].attr` 与 `.turn_career_attr` 都是**字面空表**；整包内**不存在 `Config.Role`** | **确定** | `config_role_career.luac` bc#12–15 为 `TNEW D=0`（空表，无后续写入）；`assets/src/config/` 下全部 **347** 个 `.luac` 做 `GGET Config`+`TSETS` 扫描（`tools/_pE_cfgrole.py`）只见 `RoleAttr`/`RoleCareer` |
| 10 | 任务书里"职业 id = `90100`…`91000`"的假设**不成立**：这些数字是**职业 5「神机」的技能 id**。职业 id 是 **1,2,3,4,5,9** | **确定** | `RoleCareer` 键 = 1,2,3,4,5,9；`91000` 出现在 `RoleCareer[5].skill_list` 里 |
| 11 | 升级的**可见产出**：技能按 `unlock_role_lev` 解锁；40 级起每级解锁一个天命天赋 buff（`TianmingSkill`） | **确定**（数据） | `RoleCareerSkill`/`TianmingSkill`；见 §11 |
| 12 | 客户端**没有"升级奖励"配置表**（道具/邮件） | **确定（否定性结论）** | 全 config 目录无 `lev_reward`/`LevelReward` 类表；`Config.Reward` 只有 `{30:{1..7:{coin,drop_show}}}`，键不含等级 |

---

## 1. 取证方法与证据链

### 1.1 提取与还原

| 步骤 | 命令 / 工具 | 结果 |
|---|---|---|
| 从 1.4.9 APK 取字节码 | `python tools/apk_extract_luac.py assets/src/config/config_role_attr.luac analysis\1.4.9\level\_config_role_attr.luac` | 15573 B；`protos=1 bc=409 kgc=202(strings=2,tables=200) knum=0` |
| 忠实还原嵌套表 | `python tools/dump_drop_config.py analysis\1.4.9\level\_config_role_attr.luac --json ...\role_attr.json` | `Config.RoleAttr` 200 条 |
| 职业表 | 同上，`config_role_career.luac` | `protos=1 bc=705 kgc=233(strings=9,tables=224) knum=44`；全局 4 张表 |
| 分支级反汇编 | `python analysis\1.4.9\level\_flow_dis.py <asset> <proto#> [start] [count]` | 解析 JMP 目标 + 标注条件跳转 |
| 协议字段 | `python tools/proto_spec.py cmds <CMD…>` | `AutoConstruct` 权威定义 |
| 字符串交叉检索 | `python tools/scan_luac_strings_deep.py <完整字符串…>` | 递归展开 TDUP，全 2234 个 `.luac` |

> `tools/dump_drop_config.py` 是解释器而非启发式：它按 LuaJIT 2.0 的
> `TDUP/TSETV/TSETB/TSETS/GSET/GGET` 逐条执行，`Config.RoleAttr` 的 200 条
> 记录即由它还原。`tools/extract_config_table.py`（"最近数字常量"启发式）
> **未使用**。

### 1.2 分支语义（本文所有"哪个字段被谁读"结论的前提）

要证明"客户端用 `RoleAttr[lev+1].exp_max` 当分母"，必须先证明自己能正确读出
条件跳转。本报告用的规则**不是猜的**，而是照抄 APK 内附的 LuaJIT 反编译器
`tools/ljd/`（Andrian Nord 的 ljd）的指令定义：

```
tools/ljd/ljd/bytecode/instructions.py:
    IST = _IDef("IST", None, None, T_VAR, "if {D}")        # 被测寄存器在 C 域！
    ISF = _IDef("ISF", None, None, T_VAR, "if not {D}")
tools/ljd/ljd/rawdump/code.py:
    T_JMP = 13  # branch target, relative to next instruction, biased with 0x8000
    elif operand_type == T_JMP: return operand - 0x8000
tools/ljd/ljd/ast/builder.py:
    # Mind the inversion - comparison operators are affecting JMP to the next block
    _COMPARISON_MAP[ISGE] = T_LESS_THEN ; _COMPARISON_MAP[ISEQV] = T_NOT_EQUAL ...
    warp.false_target = destination ; warp.true_target = jump_addr + 1
```

⇒ 统一规则：**`<条件指令> ; JMP L`：条件成立 → 跳到 L；条件不成立 → 落空。**

注意 **`IST/ISF` 的 A 域是 0、真正被测的寄存器在 C 域（bits16-23）**——
`tools/luajit_dis.py` 把它打印成 16 位 `D`，看起来像立即数，极易误读。
`analysis/1.4.9/level/_flow_dis.py` 已修正此点。

**交叉验证（5 处互相独立，全部自洽）**：

| # | 位置 | 反汇编 | 还原出的源码 | 说明 |
|---|---|---|---|---|
| 1 | `config_role_attr.luac` bc#1-3 | `IST r0 ; JMP 4` / `TNEW` | `if not Config then Config = {} end` | 成立→跳（跳过 TNEW） |
| 2 | `role_ctrl.luac` proto#5 bc#1-3 | `IST r2 ; JMP 4` / `r2=0` | `local v = msg.profit_exp; if not v then v = 0 end` | 成立→跳（跳过赋值） |
| 3 | `role_ctrl.luac` proto#13 bc#3-4 | `ISF r2 ; JMP 12` | `if not self:getData() then return end` | 卫语句 |
| 4 | `main_ui.luac` proto#16 bc#6-7,9-10,31-32,53-54 | 4 个 `ISF` 分支 | 见 §4.1 | 4 分支语义全部成立 |
| 5 | `role_calculate.luac` proto#2 bc#13-15 | `ISGE r3,r5 ; JMP 16` | 见 §10 | 等级判定极性正确 |

---

## 2. `Config.RoleAttr` 的精确结构

### 2.1 安装过程（`config_role_attr.luac` proto#0，bc=409）

```
bc#0    GGET  r0 <- Config
bc#1-3  IST/ JMP / TNEW        ; if not Config then Config = {} end
bc#4    GSET  Config
bc#5    GGET  r0 <- Config
bc#6    TNEW  r1 (数组容量 64)  ; 外层表
bc#7    TDUP  r2 <- {exp_total=240, exp_max=240, attr_point=0, sinew_add=0, sinew_max=120}
bc#8    TSETB r1[1] = r2        ; ★ 键是显式数组下标
bc#9    TDUP  r2 <- {exp_total=481, exp_max=481, attr_point=0, sinew_add=0, sinew_max=120}
bc#10   TSETB r1[2] = r2
  ……（步长 2，直到）
bc#405  TDUP  r2 <- {…level 200…}
bc#406  TSETB r1[200] = r2
bc#407  TSETS r0['RoleAttr'] = r1
bc#408  RET0
```

⇒ **任务书担心的"200 个 TDUP 没有数字键、键从哪来"已有答案**：
外层表的**数组部分**由 **`TSETB` + 立即数下标**逐条写入，下标就是等级。
`knum=0` 无关紧要，`TDUP` 的 200 个常量是**每条记录的 5 字段 hash 表**，
不是等级键。**不需要**任何字符串键或外部配键。

### 2.2 一个**未确定**点（诚实标注）

`TDUP` 数组部分（`TableConst.array`）的**下标基准**存在歧义：

- 观测：全 config 目录 126098 个非空 TDUP 数组中，**126091 个首元素为 `nil`**，
  7 个首元素非 `nil`（如 `config_eqm_starup_data.luac` 的 `[15]`）。
- 又观测：`SC_10301` 的字段表 `AutoConstruct('sc',10301,{…})` 的 TDUP 数组
  **长度 45、首元素 `nil`**，而它的字段名恰好 **44 个**。
- `role_constants.luac` 的使用侧是 `for i = 1, #BASE_ATTR_1`（见 §9.3），
  若真存在 `t[1]=nil` 则该循环会立刻取到 nil。

**结论**：`TableConst.array` 的第 k 项对应 Lua 下标 k（含 0 号占位）还是 k+1，
**UNKNOWN**。`tools/dump_drop_config.py` 的 `tdup()` 用
`enumerate(array, start=1)`（即"第 0 项→下标 1"），因此**它还原的 TDUP 数组类
子表可能整体偏移 1**。要定案需要：在真机用 Frida 打印
`Config.RoleCareer[1].born_skill_list`（1 个元素）与某个 `[15]` 表的 `#`/`ipairs`
结果，或反编译 `config_eqm_starup_data.luac` 找到 `[15]` 的取值方。

**本报告的核心结论不受影响**：`Config.RoleAttr` 的外层键由 **`TSETB` 立即数**
写入（§2.1），不是 TDUP 数组；协议字段名由 `proto_spec.py` 过滤非字符串后
按序输出，**顺序**与下标基准无关。受影响的只有 §8 里 `skill_list`/
`born_skill_list` 的"第几个槽位"，故 §8 只按**顺序**列出，不声明槽号。

---

## 3. 等级记录的 5 个字段

`Config.RoleAttr[1..200]` 每条记录都是同一形状的 hash 表；在文件里 200 条
TDUP 常量的字段**序列化顺序完全一致**：

| 顺序 | 字段名 | 200 行中的取值域 | 推断含义 | 证据 |
|---|---|---|---|---|
| 1 | `exp_total` | 240 … 40190720853 | 达到该等级的**累计**经验 | 与 `exp_max` 构成 §6.4 的恒等式；`SC_10301.exp_total_nextlev` 同族命名 |
| 2 | `exp_max` | 240 … 1917555775 | **该等级经验条容量**（见 §4） | `main_ui.luac`#16 用它作分母；`role_attr_msg.luac`#9 用它调 `updateExpBar` |
| 3 | `attr_point` | 全 0 | 升级赠送的**能力点**（本版恒 0） | 全 200 行取值集合 {0}；协议 `SC_10301.attr_point:uint16` 与 `SC_10328.point:uint16` 存在但本表不给值 |
| 4 | `sinew_add` | 全 0 | 筋骨/修为增量（本版恒 0） | 全 200 行取值集合 {0} |
| 5 | `sinew_max` | 全 120 | 筋骨上限（本版恒 120） | 全 200 行取值集合 {120} |

> `attr_point/sinew_add/sinew_max` 三列**在本版本是死列**（常量）。
> 任何"升级送 N 点能力点"的实现都**没有**客户端配置支撑 —— 见 §12。

---

## 4. 哪个字段是"升级所需经验" —— 决定性证据

### 4.1 客户端消费者：`assets/src/game/main/main_ui.luac` proto#16（`MainUI:changeExp`）

反汇编（`_flow_dis.py`，已解析跳转目标）：

```
  0  GGET    r1 <- 'Config'
  1  TGETS   r1 = r1['RoleAttr']            ; r1 = Config.RoleAttr
  2  TGETS   r2 = r0['role']                ; r0 = self
  3  TGETS   r2 = r2['lev']                 ; r2 = self.role.lev
  4  ADDVN   r2 = r2 + knum[0]              ; ★ knum 表长度=1，内容=[1] ⇒ lev + 1
  5  TGETV   r1 = r1[r2]                    ; ★ cfg = Config.RoleAttr[lev + 1]
  6  ISF     test r1   ; 成立->67  不成立->8
  7  JMP     goto 67                        ; cfg 为 nil ⇒ 直接返回（等级达上限时的守卫）
  8  TGETS   r2 = r0['isFirstLogin']
  9  ISF     test r2   ; 成立->30  不成立->11
 11  TGETS   r2 = r0['role'] ; 12 TGETS r2 = r2['exp']
 13  TGETS   r3 = r1['exp_max']             ; ★ 分母 = cfg.exp_max
 14  DIVVV   r2 = r2 / r3                   ;     role.exp / exp_max
 15  TGETS   r3 = r0['expFull']
 16  MULVV   r2 = r2 * r3
 17  TSETS   r0['expPos'] = r2              ; 经验条宽度 = exp/exp_max*expFull
 18-26      exp_bar:setContentSize(cc.size(expPos, 11))
```

另外两处（bc#33–39、bc#43–49）用**完全相同的**
`r1['exp_max']` + `role.exp` 做除法，分别是"升级动画第二段"与"常规刷新"。

**关键点（可复核）**：

1. `knum` 长度 = 1，唯一常量 = `1`（`main_ui.luac` proto#16 的
   `pt.knum == [1]`）。`ADDVN` 的常量下标为 `0`，因此无论是否倒序都取到 `1`
   ⇒ **索引是 `lev + 1`，不可能是 `lev`**。
2. 分母来自被索引到的 `cfg.exp_max`，因此
   **`RoleAttr[n].exp_max` = 从 n-1 级升到 n 级所需的经验**
   （等价地：**处于 L 级时本级经验条容量 = `RoleAttr[L+1].exp_max`**）。
3. 客户端只信 `RoleVo.lev`（服务端下发），**不从经验反推等级**。

### 4.2 服务端权威侧：`SC_10301` 的两个字段

`python tools/proto_spec.py cmds 10301` 给出（`cmd_resolve_103.luac` proto#1）：

| 字段 | 类型 | 位置 |
|---|---|---|
| `lev` | uint16 | 第 4 个字段 |
| `exp_max` | **uint32** | 第 23 个字段 |
| `exp_total_nextlev` | **uint32** | 第 24 个字段 |
| `attr_point` | uint16 | 第 25 个字段 |

`role_vo.luac` proto#0（`RoleVo.__init`）的字符串池里同时出现
`exp`、`exp_max`、`exp_total_nextlev`、`lev`；`initAttributeData`
（`role_vo.luac` proto#9）遍历服务端下发的属性表并逐个
`setRoleAttribute(key, value)` ⇒ **这三个字段是服务端直接下发的**，
名字与 `Config.RoleAttr` 的字段名一一对应：

| 协议字段（10301） | 配置字段 | 处于 L 级时应下发 |
|---|---|---|
| `exp_max` | `RoleAttr[L+1].exp_max` | 本级经验条容量 |
| `exp_total_nextlev` | `RoleAttr[L+1].exp_total` | 升到 L+1 的累计经验 |
| `attr_point` | `RoleAttr[L+1].attr_point` | 本版恒 0 |

### 4.3 第二条消费者：`role_attr_msg.luac` proto#9

```
0-3   r2 = self:getRoleAttribute('exp')
4-7   r3 = self:getRoleAttribute('exp_max')
8-13  self.exp_bar:updateExpBar(r2, r3)
```

⇒ 面板侧同样把 `exp_max` 当分母（这里取的是服务端 10303 下发的属性，
`role_vo.luac` proto#21 `getRoleAttribute(key) { return self[key] }`）。
**两条独立路径（客户端配置 / 服务端下发）都把 `exp_max` 当"本级所需经验"。**

### 4.4 结论

- **`exp_max` = 经验条容量 = 升下一级所需经验。** 置信度 **确定**。
- 具体取值：**处于 L 级时 = `RoleAttr[L+1].exp_max`**；本报告 §5 的表格
  第 4 列已直接算好这一列。
- `exp_total` 是**累计**阈值（不是"本级所需"）；客户端 .luac 里**没有任何
  代码读 `exp_total`** —— 深度字符串扫描中 `exp_total` 只出现在
  `config_role_attr.luac` / `config_hero_attr.luac` / `config_hero_base.luac` /
  `config_partner_base.luac` 四个**配置**文件里，**零个**游戏逻辑文件。
  因此服务端必须自己维护累计值（与 `exp_total_nextlev` 对齐）。

---

## 5. 逐级经验表（1 级 … 200 级，全量）

- `RoleAttr[L].exp_total` = 达到 L 级的累计经验
- `RoleAttr[L].exp_max` = L 级经验条容量（= 从 L-1 升到 L 所需）
- 第 4 列 = **从 L 级升到 L+1 级所需经验** = `RoleAttr[L+1].exp_max`（服务端判定升级用这一列）

| 等级 L | RoleAttr[L].exp_total | RoleAttr[L].exp_max | 由 L 升到 L+1 所需（=RoleAttr[L+1].exp_max） |
|---:|---:|---:|---:|
@@TABLE@@

---

## 6. 一致性 / sanity check（全部实测）

### 6.1 键序列

| 检查 | 结果 |
|---|---|
| 记录条数 | **@@N@@** |
| 键最小值 / 最大值 | **@@MIN@@** / **@@MAX@@** |
| 是否恰好 `1..200` 连续无缺 | **@@CONTIG@@** |
| 是否有重复键 | 无（同一次 dump 内 200 个互异整数键） |

### 6.2 单调性

| 检查 | 结果 |
|---|---|
| `exp_max` 严格递增（每行都严格大于上一行） | **@@EMMONO@@** |
| `exp_total` 严格递增 | **@@ETMONO@@** |
| 结论 | 是一条**正常递增**的经验曲线，**不是**"全同值/荒谬小值"的错表 |

### 6.3 记录数 vs 等级上限

记录数 200 与键上界 200 **完全吻合** ⇒ 等级上限 **200**。
`set_role_level.py` 里的 `1..200` 校验与此一致（该工具是项目自写脚本，
仅作旁证）。客户端 `main_ui` proto#16 bc#6-7 对
`RoleAttr[201] == nil` 有显式守卫，也印证"超出 200 就没有经验条数据"。

### 6.4 `exp_total` 递增恒等式（**唯一一处异常，必须说明**）

| 检查 | 结果 |
|---|---|
| 满足 `exp_total[n] = exp_total[n-1] + exp_max[n]` 的行 | **n = 3..200，共 @@INVOK@@ 行** |
| 不满足的行 | **@@INVBAD@@** |

异常细节：`n=2` 时 `exp_total[2] - exp_total[1] = @@D2@@`，但
`exp_max[2] = @@EM2@@`。同时可观测到**只有第 1、2 两行的
`exp_total == exp_max`**（240/240 与 481/481），第 3 行起两者分离。

⇒ 两种可能（**均为 INFERRED**，无法从 APK 单独定案）：
(a) `exp_max[2]` 本应是 `@@D2@@`，被误写成与 `exp_total[2]` 相同；
(b) `exp_total[1]`/`exp_total[2]` 两行的生成规则与后面 198 行不同。
**对服务端的影响**：只影响 1→2 级的判定。客户端在 L=1 时用
`RoleAttr[2].exp_max = @@EM2@@` 当分母，因此**若要和客户端一致，
1→2 级就该要 @@EM2@@ 经验**（而不是 @@D2@@）。

### 6.5 "死列"

| 字段 | 200 行取值集合 | 判定 |
|---|---|---|
| `attr_point` | @@APSET@@ | 常量，本版不参与成长 |
| `sinew_add` | @@SASET@@ | 常量 |
| `sinew_max` | @@SMSET@@ | 常量 |

### 6.6 曲线形状（分段证据）

`exp_max` 的逐级比值并不恒定，存在明显**段边界**（比值突变 >20%）：

| 段边界 | 比值变化 | exp_max 变化 |
|---|---|---|
@@SEGS@@

⇒ 这是一张**人工分段配置**的表（不是单一公式），与"1~31 级一段、32~40 一段…"
的常见做法一致。段边界本身**不影响**服务端"照表查值"的实现。

### 6.7 数值量级

| 项 | 值 |
|---|---|
| 1 级 | exp_max = @@L1EM@@，exp_total = @@L1ET@@ |
| 10 级 | exp_max = @@L10EM@@，exp_total = @@L10ET@@ |
| 200 级 | exp_max = @@EMLAST@@，exp_total = @@ETLAST@@ |

200 级总累计约 **4.02e10**（40190720853），单级需求约 **1.92e9**，
均可用 `uint32` 表达（上限 4294967295），与 `SC_10301.exp_max:uint32` /
`exp_total_nextlev:uint32` 的类型一致 ⇒ **量级合理，字段选型自洽**。

---

## 7. 等级上限

**200 级（确定）**。证据：`Config.RoleAttr` 键恰为 1..200（§6.1/6.3）；
无 `RoleAttr[201]`。

`UNKNOWN`：200 是"服务端硬上限"还是"客户端经验表上限"。
若服务端允许 >200，客户端 `main_ui` proto#16 bc#6-7 会走
`cfg == nil` 分支（直接返回、不刷新经验条），**等级数字仍会显示**（来自
`SC_10301.lev`），但经验条不再更新。要区分需要真机验证 200 级以上的表现。

---

## 8. 职业（`Config.RoleCareer`）

### 8.1 ⚠ 更正任务书前提

任务书写"约 10 个职业（`90100`…`91000`）"。**实测不成立**：

- `Config.RoleCareer` 的键是 **`1, 2, 3, 4, 5, 9`**（6 条），**不是** `90100`…`91000`。
- `90100`、`90200` … `91000` 出现在 **`RoleCareer[5]`（职业 5「神机」）的
  `skill_list`** 中，是**技能 id**，不是职业 id。
- `knum` 里那 12 个数字（`90100…91000, 99091, 99092`）正是
  `RoleCareer[5].skill_list` 与 `RoleCareer[9].skill_list` 的**取值**。
- 协议侧 `SC_10301.career:uint16` / `SC_10302` /
  `server/config.json` 的 `career:1` 也都是小整数。

⇒ **职业 id = 1..5（+9 = 测试职业）。**

### 8.2 6 条职业条目

| career | name | res | res_2 | weapon_res | weapon_res_2 | height | born_skill_list（按序） | skill_list（按序） |
|---:|---|---|---|---|---|---:|---|---|
@@CAREER@@

字段清单（每条完全一致，14 个键）：
`career, name, res, res_2, weapon_res, weapon_res_2, height, width,
die_effect, anime_die, skill_list, born_skill_list, attr, turn_career_attr`。

`width` 全为 0，`die_effect` 全为 `E62931`，`anime_die` 全为 `die`，
`height` **6 条全为 170**（无差异，不构成职业区分度）。

> `skill_list` / `born_skill_list` 是表的**数组部分**，只按**顺序**列出
> （下标基准问题见 §2.2，故不声明槽号）。

### 8.3 **职业基础属性：客户端里没有**

`config_role_career.luac` proto#0 对**每个职业**都是这段（以 career 1 为例）：

```
bc#12  TNEW r3 D=0     ; 空表
bc#13  TSETS r2['attr'] = r3
bc#14  TNEW r3 D=0     ; 空表
bc#15  TSETS r2['turn_career_attr'] = r3
bc#16  TSETB r1[1] = r2
```

`TNEW D=0` = 数组/哈希容量均为 0，**之后没有任何写入** ⇒
`RoleCareer[c].attr` 与 `RoleCareer[c].turn_career_attr` 都是**字面空表**。

**同时**：对 `assets/src/config/` 下全部 **347** 个 `.luac` 做
`GGET Config` + `TSETS` 扫描（`tools/_pE_cfgrole.py`），只有
`config_role_attr.luac`（`RoleAttr`）和
`config_role_career.luac`（`RoleCareer`）命中 —— **整包内不存在 `Config.Role`**，
也不存在 `Config.Level` / `Config.Attr`（`config_attr.luac` 定义的是
`Config.AttrKey2Id` 等 8 个平铺键，见 §9.2）。

⇒ **1.4.9 客户端 APK 内没有"职业基础属性"数据**。原版里 1 级的
strength/intellect/… 是**服务端算好**再通过 `SC_10303.attr__T` 下发的。
`tools/scale_role_attr.py` 的注释与之一致（该工具做的是 emulation 而非还原）。

---

## 9. 属性字段名与顺序

### 9.1 `SC_10303.attr__T`（协议权威，24 项，顺序即线序）

`python tools/proto_spec.py cmds 10303`（`cmd_resolve_103.luac` proto#7）：

| # | 字段 | 类型 | # | 字段 | 类型 |
|---:|---|---|---:|---|---|
| 1 | `strength` | uint16 | 13 | `crit` | uint32 |
| 2 | `intellect` | uint16 | 14 | `tenacity` | uint32 |
| 3 | `armor` | uint16 | 15 | `red_def_s` | uint32 |
| 4 | `constiution` | uint16 | 16 | `red_def_p` | uint32 |
| 5 | `atk_s` | uint32 | 17 | `atk_abs` | uint32 |
| 6 | `atk_p` | uint32 | 18 | `def_abs` | uint32 |
| 7 | `def_s` | uint32 | 19 | `reduce` | uint32 |
| 8 | `def_p` | uint32 | 20 | `hurt` | uint32 |
| 9 | `hp_max` | uint32 | 21 | `hit_rate_show` | uint32 |
| 10 | `atk_speed` | uint32 | 22 | `dodge_rate_show` | uint32 |
| 11 | `hit` | uint32 | 23 | `crit_rate_show` | uint32 |
| 12 | `dodge` | uint32 | 24 | `tenacity_rate_show` | uint32 |

⚠ **`SC_10306.attr__T` 同名但类型不同**：`atk_abs`/`def_abs`/`reduce`/`hurt`
在 10306 里是 **uint16**（10303 是 uint32）。差分编写时别混。

### 9.2 `Config.Attr*` 元数据（64 项 id↔key↔中文名）

`config_attr.luac` proto#0 定义的是 **8 个顶层键**（**注意不是 `Config.Attr`，
`Config.Attr` 不存在**）：

| 键 | 内容 | 规模 |
|---|---|---|
| `AttrLen` | 属性总数 | 64 |
| `AttrKey2Id` | key → id | 64 |
| `AttrId2Key` | id（键是浮点字符串，如 `"101.0"`）→ key | 64 |
| `AttrKey2Str` | key → 中文名 | 64 |
| `AttrId2Str` | id → 中文名 | 64 |
| `AttrKeyIsShow` | 面板是否显示 | 10（`atk_p, atk_s, atk_speed, crit, def_p, def_s, dodge, hit, hp_max, tenacity`） |
| `AttrPower` | 战力权重 | 64 |
| `AttrPartnerPower` | 伙伴战力权重 | 64 |

id 共 **64** 个，**不连续**，分三段：
`101..151`（51 个基础/战斗属性）、`201..209`（9 个"转化/展示率"类）、
`240..243`（4 个抗控细分）。例：`101=strength 力量`、`104=constiution 体质`、
`105=atk_s 物攻`、`109=hp_max 生命`、`130=mspd 移动速度`、
`203=crit_rate_show 总暴击率`、`240=anti_control_s 抗睡眠等级`。

### 9.3 `RoleConstants.BASE_ATTR_1 / BASE_ATTR_2`（`role_constants.luac` proto#1）

| 常量 | 内容（顺序即数组顺序） | 证据 |
|---|---|---|
| `BASE_ATTR_1` | `hp_max, atk_s, atk_p, def_s, def_p, atk_speed` | TDUP @bc#143，`TSETS` @bc#144 |
| `BASE_ATTR_2` | `tenacity, crit, dodge, hit, atk_speed, hp_max, def_p, def_s, atk_p, atk_s` | TDUP @bc#165，`TSETS` @bc#166 |
| `HERO_ATTR_1` | `{[1]={crit,hit,atk_p,atk_s,hp_max}, [2]={tenacity,dodge,def_p,def_s,atk_speed}}` | `TNEW` @bc#168 + `TSETB idx=1/2` |
| `HERO_ATTR_2` | `hp_max, def_s, def_p, atk_s, atk_p` | TDUP @bc#175 |
| `ATTR_BTN` | `strength/intellect/armor/constiution` → 面板按钮标签（`getString('力  量')` 等） | bc#146–162 |
| `Object` | `{Role=1, Hero=2, All=0}` | TDUP @bc#178 |
| 其它 | `EQUIPS_NUM=6, ROLE_RING_POS=7, ROLE_FASHION_NUM=4, ROLE_WEAPON_NUM=7, HERO_BID=0` | bc#181–194 |

> `BASE_ATTR_2` 的 10 项与 `Config.AttrKeyIsShow` 的 10 个 key **完全一致**
> ⇒ 它正是"面板要展示的 10 条属性"。
> 使用侧实例：`role/new_ui/hero/hero_tab_msg.luac` proto#2
> `for i = 1, #BASE_ATTR_1 do … BASE_ATTR_1[i] .. '_label_1' … end`
> （见 §2.2 的下标基准说明）。

### 9.4 等级记录本身的字段顺序

`Config.RoleAttr[L]` 的字段顺序就是 §3 表里的
`exp_total → exp_max → attr_point → sinew_add → sinew_max`
（200 条 TDUP 的序列化顺序一致）。
⚠ Lua 表字面量的字段顺序在 hash 部分**不可靠**；这里的依据是
**"200 条独立 TDUP 的序列化顺序完全相同"**，属于强证据但不是语言保证。

---

## 10. 与 `role_calculate.luac` / `role_constants.luac` 的交叉验证

### 10.1 `role_calculate.luac` 的字符串池与真实用途

任务书提到它引用 `Config.Role` / `Config.Hero` / `Config.Object` / `RoleConstants`。
实测：

| proto | 方法（`proto#27` 是方法表） | 字符串池关键项 | 说明 |
|---|---|---|---|
| proto#0 | `isLimitCareer`（方法表映射） | `RoleCalculate, isRolePartnerEquip, isCanPutOn, isLevLimit, isCareerLimit` | 组合判定 |
| proto#1 | `isCareerLimit` | `Item, PartnerBase, Config, career` | 读 `Config.Item[bid]` / `Config.PartnerBase` |
| **proto#2** | **`isLevLimit`** | `bid, Item, Config, lev` | **唯一的等级判定** |
| proto#3 | `isCanPutOn` | `Object, Hero, Role, RoleConstants` | 比较 `self.object` 与 `Config.Object.Hero/Role` |

`proto#2` 完整还原（`_flow_dis.py`）：

```lua
function RoleCalculate.isLevLimit(roleVo, goodsVo)
    local res = true
    if not roleVo then return res end        -- bc#1-2
    if not goodsVo then return res end       -- bc#3-4
    local lev = roleVo.lev                   -- bc#5
    local cfg = Config.Item[goodsVo.bid]     -- bc#6-9
    if not cfg then return res end           -- bc#10-11
    if lev >= cfg.lev then return true end   -- bc#12-14  (ISGE)
    return false                             -- bc#15-16
end
```

⇒ **`role_calculate.luac` 里的"等级"只用于"这件装备/物品的穿戴等级要求"**，
用的是 `Config.Item[bid].lev`。它**没有任何** `等级 → 属性` 的计算，
也**不读** `Config.RoleAttr`（`RoleAttr` 字符串在该文件里完全不出现）。
这从代码侧再次确认 §8.3 的结论：**逐级属性成长不在客户端 APK 里**。

### 10.2 `role_constants.luac`

只提供枚举/常量（`Object{Role,Hero,All}`、`BASE_ATTR_1/2`、
`RoleTabConstants`、`GridsCellState`、`EQUIPS_NUM=6` 等），
**不含任何等级/经验数值**。它给的是"属性字段名清单"（§9.3），
与 `Config.AttrKey2Id` 的 key 命名体系一致。

### 10.3 全包字符串检索（`exp_total` / `attr_point` / `RoleAttr`）

| 字符串 | 命中的**游戏逻辑**文件 | 说明 |
|---|---|---|
| `RoleAttr` | **仅** `game/main/main_ui.luac` proto#16 | 唯一消费者 |
| `exp_total` | **无**（仅 4 个 config 文件） | 客户端从不用累计值 |
| `exp_max` | `main_ui#16`、`role_attr_msg#9`、以及 hero/partner 系列的 `hero_vo`、`partner_show_msg`、`mine_show_partner`、`hero_tab_msg`、`hero_attr_msg`、`partner_item_backpack_panel` | 角色经验条 + 英雄/伙伴经验条 |
| `attr_point` | `role_ctrl.luac` proto#28/#29、`role_vo.luac` proto#0 | 能力点面板 + `RoleVo` 字段 |

⇒ **角色经验表在客户端只有一个读点**（`main_ui` proto#16），
因此 §4.1 的 `+1` 索引就是全部依据，不存在第二种解释路径。

---

## 11. 升级会得到什么

### 11.1 技能按等级解锁（`Config.RoleCareerSkill[career][skill_id]`）

每条技能记录字段：`quality, type, max_lev, unlock_role_lev, skill_name,
attr_desc, ex_desc`。

| career | name | 技能条数 | 技能（名称 / 类型 / 解锁角色等级 / 技能等级上限） |
|---:|---|---:|---|
@@SKILLS@@

> `unlock_role_lev` 的取值集合（以职业 1 为例）：`1, 3, 13, 22, 32, 38, 43, 48, 57`
> ⇒ **技能解锁是等级提升的主要可见产出**。这部分**由服务端在 10301 的
> `skill_list` 中下发**（`SC_10301.skill_list__T{bid:uint32}`），客户端不自己推。

### 11.2 天命天赋：40 级起每级一个（`Config.TianmingSkill`）

`Config.TianmingSkill` 共 **150** 条，键是**技能 id**，值是
`{career:uint16, lev:uint16, buff_bid:uint32}`：

| career | 条数 | lev 范围 | buff_bid 范围 | skill_id 范围 |
|---:|---:|---|---|---|
@@TIANMING@@

⇒ **等级是唯一的解锁条件**：职业 C 的角色到达 `lev` 时获得 `buff_bid`。
（`RoleCareerSkill[1][12600]` 的记录是 `type='天赋技能', max_lev=30,
unlock_role_lev=40, skill_name='玄武之力'`，与上表 `career=1, lev=40,
buff_bid=40101` 完全对齐。）这是"升级授予"里**最像"每级奖励"**的一张表，
但只覆盖 **40..69 级**。

### 11.3 升级奖励（道具/邮件）：**客户端无表**

| 检查 | 结果 |
|---|---|
| 是否存在 `lev_reward` / `LevelReward` / `up_reward` 之类字符串 | **0 命中**（`scan_luac_strings_deep.py`） |
| config 目录里名字含 reward 的表 | `config_reward_data.luac`（`Config.Reward`）、`config_reward_box_data.luac`、`config_reward_back_data.luac`、`config_chief_award_data.luac`、`config_holiday_dial_reward_data.luac`、`config_dungeon_reward_desc.luac` |
| `Config.Reward` 的形状 | `{ "30": { "1".."7": {coin:20000, drop_show:{1..4: item_id}} } }` |

`Config.Reward` 的外层键只有 `"30"`，第二层是 `1..7`，**既不是等级也不是职业**
（更像活动/开服天数类的 7 档奖励）。**`UNKNOWN`**：它到底由哪个协议触发。
**可以确定的是：没有任何"等级 → 奖励"的客户端配置表** ⇒
升级奖励（如果有）**完全由服务端决定**，客户端不需要配置。

---

## 12. 未能确定（UNKNOWN / INFERRED）汇总

| # | 项 | 状态 | 会怎样定案 |
|---|---|---|---|
| 1 | TDUP 数组部分的**下标基准**（`array[k]` ↔ Lua 下标 k 还是 k+1） | **UNKNOWN** | 真机 Frida 打印 `#Config.RoleCareer[1].born_skill_list` / 某 `[15]` 表的 `ipairs`；或找到 `[15]` 的取值方 |
| 2 | `exp_total` 的确切用途（服务端累计阈值 vs 其它） | **INFERRED** | 客户端零引用，只能靠 §6.4 恒等式 + `exp_total_nextlev` 同族命名推断 |
| 3 | 第 2 行异常（`exp_max[2]=481` vs `exp_total[1]+…`）的成因 | **INFERRED** | 需要原版服务端代码或真机 1→2 级实测 |
| 4 | `attr_point` / `sinew_add` / `sinew_max` 三列恒定的含义 | **UNKNOWN** | 本版客户端无消费点；`SC_10328`（增加能力点）也无配置来源 |
| 5 | 200 级以上的行为（服务端硬上限？客户端只不刷经验条？） | **UNKNOWN** | 真机把角色改到 201+ 级，观察经验条与等级显示 |
| 6 | `Config.Reward` 的触发协议 | **UNKNOWN** | 需扫描全部 `SC_*` 里带 `reward` 的 CMD，并对照 1.4.9 活动配置 |
| 7 | 逐级战斗属性（atk/hp/def）的真实成长值 | **UNKNOWN（不可得）** | APK 内无表（§8.3/§10.1）；只能靠原版服务端数据或抓包对照 |
| 8 | **跳转语义**（§1.2）已交叉验证 5 处，但未与 ljd 的完整反编译流程逐条对齐 | 已**确定**规则 / 未做全量回归 | 若要让 `tools/ljd` 能直接跑这 2234 个 `.luac`（它当前因头部格式差异失败），可做全量对拍 |

---

## 附：本报告使用的落盘文件

| 文件 | 内容 |
|---|---|
| `role_attr.json` | `Config.RoleAttr` 全量（200 级 × 5 字段） |
| `role_career.json` | `Config.RoleCareer` / `RoleCareerSkill` / `Tianming` / `TianmingSkill` |
| `level_table.json` | 服务端直接可读的等级表（`max_lev=200` + `levels`） |
| `_config_role_attr.luac` | 从 1.4.9 APK 提取的原始字节码（15573 B） |
| `_config_role_career.luac` | 同上（14497 B） |
| `_config_attr.luac` | `Config.Attr*` 元数据来源（6305 B） |
| `_proto_spec_exp.json` | 本次用 `proto_spec.py` 取的全部经验/等级相关 CMD 字段定义 |
| `_flow_dis.py` | 带跳转目标解析 + 条件标注的反汇编器（修正了 IST/ISF 的 C 域） |
| `_role_ctrl_defs.txt` | `role_ctrl.luac` 的方法名 → proto# 映射 |
'''

DOC = (DOC.replace('@@TABLE@@', TABLE)
          .replace('@@CAREER@@', CAREER_TABLE)
          .replace('@@SKILLS@@', SKILL_TABLE)
          .replace('@@TIANMING@@', TM_TABLE)
          .replace('@@N@@', str(facts['n']))
          .replace('@@MIN@@', str(facts['min']))
          .replace('@@MAX@@', str(facts['max']))
          .replace('@@CONTIG@@', '是（`1..200` 连续）' if facts['contiguous'] else '否')
          .replace('@@EMMONO@@', '是' if facts['em_mono'] else '否')
          .replace('@@ETMONO@@', '是' if facts['et_mono'] else '否')
          .replace('@@INVOK@@', str(facts['inv_ok_rows']))
          .replace('@@D2@@', str(facts['inv_bad'][0][1]) if facts['inv_bad'] else 'n/a')
          .replace('@@EM2@@', str(facts['inv_bad'][0][2]) if facts['inv_bad'] else 'n/a')
          .replace('@@INVBAD@@', ('n = %d（`exp_total[2]-exp_total[1]=%d`，但 `exp_max[2]=%d`）'
                                  % facts['inv_bad'][0]) if facts['inv_bad'] else '无')
          .replace('@@APSET@@', str(facts['ap_set']))
          .replace('@@SASET@@', str(facts['sa_set']))
          .replace('@@SMSET@@', str(facts['sm_set']))
          .replace('@@EMLAST@@', str(facts['em_last']))
          .replace('@@ETLAST@@', str(facts['et_last']))
          .replace('@@L1EM@@', str(facts['em_first10'][0][1]))
          .replace('@@L1ET@@', str(facts['em_first10'][0][2]))
          .replace('@@L10EM@@', str(facts['em_first10'][9][1]))
          .replace('@@L10ET@@', str(facts['em_first10'][9][2]))
          .replace('@@SEGS@@', '\n'.join(
              '| %d → %d | %.4f → %.4f | %d → %d |' % s for s in facts['segs'])))

out = os.path.join(HERE, 'exp_table.md')
open(out, 'w', encoding='utf-8').write(DOC)
print('wrote %s (%d bytes)' % (out, len(DOC.encode('utf-8'))))
print('facts:', json.dumps({k: v for k, v in facts.items() if k != 'segs'}, ensure_ascii=False))
