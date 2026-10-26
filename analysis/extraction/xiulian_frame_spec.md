# 10621 skill_list 客户端解析偏移确认 + 修炼填值方案

> 日期：2026-10-02 | 纯静态分析（APK luac + proto_defs + 配置表）
> 约束：未修改 server/、未碰模拟器

---

## 1. SC_10621 帧结构（proto_defs 确认）

```
SC_10621 {
    world_lev: uint16,          // 世界等级
    skill_list: table {
        bid: uint32,            // 技能/修炼 bid
        exp: uint32             // 累计经验值
    }
}
```

**当前 mock_server 发送**（config.json skills）：
- bid=10000, exp=0
- bid=10001, exp=0
- bid=10002, exp=0

→ 仅 3 个基础技能，**无修炼技能条目**，这就是 UI 修炼面板消耗/拥有栏为空的根因。

---

## 2. 客户端解析逻辑推断

### 2.1 bid → 技能类型映射

客户端根据 bid 范围判断技能类型：

| bid 范围 | 类型 | 配置表 |
|---|---|---|
| 10000-10099 | 基础职业技能 | config_skill.json |
| 10101-10801+ | 修炼技能（链式） | config_skill_xiulian.json |

### 2.2 修炼技能链式结构

修炼技能为 **bid 链式递增**：
- 攻击修炼：10101(L1) → 10102(L2) → ... → 10123(L23)
- 物防修炼：10201(L1) → 10202(L2) → ...
- 法防修炼：10301 → ...
- 控制修炼：10401 → ...
- 伙伴攻/法/物防法防：10501-10701 → ...
- **抗控修炼：10801(L1) → 10802(L2) → ... → 10822(L22) → ...**

**客户端如何判定 LV**：
- 收到 bid=10822 → 在 SkillXiulianUp 表中查到 next_bid=10823
- 链式回推：10822 - 10801 = 21 → LV = 22（base=10801 对应 L1）

### 2.3 exp 字段含义

`exp:u32` = **当前修炼等级已积累的经验值**（向下一级进度）

**UI "修炼进度: 35/50" 含义**：
- 35 = 当前等级已积累 exp（= skill_list 中对应条目的 exp 字段值）
- 50 = 当前等级升级所需总 exp（从 SkillXiulianUp 配置查 exp 字段）

> ⚠️ 注意：配置中 SkillXiulianUp exp=402（L1→L2）与 UI 显示 50 不一致。可能原因：
> 1. 配置 exp 为"累计总经验"而非"本级增量"
> 2. UI 显示经过缩放计算
> 3. 需实机 hook 验证精确映射

### 2.4 消耗/拥有栏来源

UI 修炼面板的：
- **消耗栏**：升级到下一级所需 exp（= SkillXiulianUp[当前bid].exp）
- **拥有栏**：当前已积累 exp（= skill_list[对应bid].exp）

**当前为空的原因**：skill_list 中无修炼条目（无 bid=10822 等），客户端无数据可填。

---

## 3. 填值方案（供实施代理直接实现）

### 3.1 需在 config.json skills 列表中添加修炼条目

当前：
```json
"skills": [
  {"bid": 10000, "exp": 0},
  {"bid": 10001, "exp": 0},
  {"bid": 10002, "exp": 0}
]
```

**目标状态**（抗控修炼 LV.22，进度 35/50）：
```json
"skills": [
  {"bid": 10000, "exp": 0},
  {"bid": 10001, "exp": 0},
  {"bid": 10002, "exp": 0},
  {"bid": 10822, "exp": 35}
]
```

### 3.2 帧长变化

| 项 | 当前 | 修改后 |
|---|---|---|
| skill_list 条数 | 3 | 4 |
| 每条大小 | 8 bytes (u32 bid + u32 exp) | 8 bytes |
| 净增 | 0 | +8 bytes |
| SC_10621 总大小 | 34 bytes | 42 bytes |

### 3.3 完整修炼条目推荐配置

如需完整 8 项修炼：
```json
"skills": [
  {"bid": 10000, "exp": 0},
  {"bid": 10001, "exp": 0},
  {"bid": 10002, "exp": 0},
  {"bid": 10122, "exp": 0},   // 攻击修炼 L22
  {"bid": 10222, "exp": 0},   // 物防修炼 L22
  {"bid": 10322, "exp": 0},   // 法防修炼 L22
  {"bid": 10422, "exp": 0},   // 控制修炼 L22
  {"bid": 10822, "exp": 35}   // 抗控修炼 L22, exp=35
]
```

---

## 4. 证据等级与待确认项

| 结论 | 证据等级 | 说明 |
|---|---|---|
| SC_10621 帧结构 | CONFIRMED | proto_defs.py L8612-8618 |
| skill_list = table(bid:u32, exp:u32) | CONFIRMED | proto_defs + mock_server L15615 |
| 当前仅 3 基础技能无修炼条目 | CONFIRMED | config.json skills 列表 |
| 修炼 bid 链式递增（10801→10822=L22） | STRONG_INFERENCE | config_skill_xiulian SkillXiulianUp next_bid 链 |
| exp 字段 = 当前等级积累经验 | INFERENCE | 基于 UI 进度条 35/50 反推 |
| 消耗栏 = 下一级所需 exp | INFERENCE | 基于 UI 布局推断 |
| 35/50 中 50 的精确来源 | UNKNOWN | 配置 exp=402 与 UI=50 不一致，需实机 hook |

---

## 5. 未确认项与后续验证路径

1. **exp 字段精确语义**：需实机 hook 客户端解析函数，对比不同 exp 值下 UI 进度条变化
2. **消耗栏数据来源**：确认是客户端本地计算（从 SkillXiulianUp 查表）还是服务端下发
3. **world_lev 字段**：当前=1，是否影响修炼面板显示
4. **基础技能与修炼技能是否共用同一表**：bid 范围是否足够区分

---

## 6. 实施代理操作要点

1. 在 `config.json` 的 `skills` 数组中添加修炼条目（如 `{"bid": 10822, "exp": 35}`）
2. 重启 mock_server（或热重载 config）
3. 观察客户端修炼面板：
   - 抗控修炼等级应显示 LV.22
   - 进度条应显示 35/50（或配置对应的 exp 值）
   - 消耗栏/拥有栏应填充数值
4. 若 UI 显示不符，微调 exp 值或 bid 链偏移

---

## 追加：修炼消耗/拥有 EXP 偏移定位结论

> 日期：2026-10-02 | 方法：静态协议字段分析（proto_defs + mock_server）

### 问题回顾

修炼面板 UI 进度条 35/50 已正确（skill_list{bid:10822, exp:35}），但**消耗栏/拥有栏 EXP 数值空白**。需定位这两个值的数据来源字段。

---

### 定位结论

| UI 栏位 | 数据来源 | 字段位置 | 当前值 | 证据等级 |
|---|---|---|---|---|
| **拥有栏**（当前修炼经验货币） | `practice_exp` 字段 | SC_10304 第 27 个字段（uint32） | **0**（mock_server 发送 0） | **CONFIRMED** |
| **消耗栏**（下一级所需 EXP） | 客户端从 config 计算 | SkillXiulianUp.exp（如 bid=10822 exp=63096） | 客户端应自行计算 | **INFERENCE** |

---

### 详细依据

**1. 拥有栏 = `practice_exp`（修炼经验货币）**

- SC_10304 帧定义（proto_defs.py L7730）：
  ```
  ('practice_exp', 'uint32', ''),  # 修炼经验
  ```
- mock_server storage.py L53 初始化：`'practice_exp': 0`
- 当前发送值为 0 → 客户端显示空白（0 值不渲染）

**2. 消耗栏 = 客户端从配置计算**

- 配置表 `config_skill_xiulian.json` → `SkillXiulianUp` 每条有 `exp` 字段
- bid=10822（抗控修炼 L22）：exp=63096（升 L23 所需）
- 客户端应根据当前选中的修炼技能 bid，查 SkillXiulianUp.exp 显示消耗值
- **当前空白原因推测**：客户端可能需要先收到有效的 practice_exp 值才会渲染消耗/拥有栏 UI（UI 组件联动显示）

**3. 进度条 "50" 的来源（补充说明）**

- 进度条分母 = 50，但配置中 L22 对应 SkillXiulianUp.exp=63096，不匹配
- 可能来源：
  - SkillXiulianLev 表的世界等级要求（L8=[None,40,50]）— 但 L22=[None,100,110]，不匹配
  - 客户端显示缩放（按比例归一化到 50）
  - 其他未定位的字段
- **结论**：进度条"50"语义仍待 luac 字节码确认，标 UNKNOWN

---

### 补丁方案（供实施参考）

**修复"拥有栏空白"**：
- 在 SC_10304 帧中发送非零的 `practice_exp` 值
- 建议初始值：与进度条 exp 对齐（如 practice_exp = 35，对应 bid=10822 的 exp=35）
- 字段位置：SC_10304 第 27 个 uint32 字段（在 guild_contrib 之后、tower_cent 之前）

**修复"消耗栏空白"**：
- 客户端应从 config_skill_xiulian SkillXiulianUp.exp 读取下一级消耗
- 若客户端未自动计算，可能需要在 SC_10621 或 SC_10304 中追加消耗字段
- 需 luac 字节码确认客户端实际读取逻辑

---

### 证据等级总结

| 项 | 等级 | 说明 |
|---|---|---|
| practice_exp 字段存在性 | CONFIRMED | proto_defs.py L7730 权威定义 |
| practice_exp = 拥有栏 | INFERENCE | 字段名匹配"修炼经验"语义，但未经客户端渲染验证 |
| 消耗栏 = config 计算 | INFERENCE | 配置表有 exp 字段，客户端应自行查询 |
| 进度条"50"语义 | UNKNOWN | 不匹配任何已知配置值，待 luac 分析 |

---

## 追加：进度条"50"配置源分析

> 日期：2026-10-02 | 方法：全配置表交叉检索

### 问题

UI 进度条显示 **35/50**（用户截图 CONFIRMED）。我们发送 `skill_list{bid:10822, exp:35}`，分子 35 已匹配。但分母 50 的配置源未定位。

---

### 检索范围与结果

| 配置表 | 字段 | L22 值 | 是否匹配"50" |
|---|---|---|---|
| SkillXiulianUp | exp（升级消耗） | 63096 | ❌ 差 1262 倍 |
| SkillXiulianUp | power（战力） | 2494 | ❌ |
| SkillXiulianUp | attr.anti_control（属性） | 440 | ❌ |
| SkillXiulianLev | L22=[min_role, min_world] | [100, 110] | ❌ |
| SkillXiulianLearn | exp（学习消耗） | 43 | ❌（接近但不等） |
| SkillXiulianRoleLev | 角色等级要求 | — | ❌ |
| SkillXiulianWorldLev | 世界等级要求 | — | ❌ |

---

### 结论

**"50"配置源：UNKNOWN**

已检索 config_skill_xiulian.json 全部 5 张表（SkillXiulianLearn/Up/WorldLev/RoleLev/Lev），L22 级所有字段值均不匹配 50。

**可能的来源（待 luac 字节码确认）**：

1. **客户端显示缩放**：将实际 exp（63096）按比例归一化到 0-50 区间显示（如 63096 → 50 满条）
2. **客户端硬编码**：进度条分母固定为 50（UI 设计值），与配置无关
3. **其他帧字段**：SC_10304 或其他帧中有未被 proto_defs 记录的扩展字段
4. **SkillXiulianLev L8 的 world_lev=50**：巧合或显示逻辑关联（但 L22 world_lev=110，不匹配）

---

### 证据等级

| 项 | 等级 |
|---|---|
| 分子 35 = skill_list.exp | CONFIRMED |
| 分母 50 来自配置表 | UNKNOWN |
| 50 = SkillXiulianUp.exp 缩放 | INFERENCE（未证实） |
| 50 = 客户端硬编码 | INFERENCE（未证实） |

> 需 luac 字节码反编译修炼面板渲染函数才能最终定位。

---

## 追加：进度条"50"配置源续析（第二轮）

> 日期：2026-10-02 | 方法：全配置表交叉检索 + luac 目录排查

### 检索扩展

| 检索项 | 结果 |
|---|---|
| config_role_attr.json RoleAttr.exp_max | 角色等级经验表（200级），非修炼 |
| config_skill.json 全部表 | SkillPoint(10) / Skill(0) / data(0)，无修炼经验表 |
| 全 cfg 目录搜索 exp_max/level_exp/xiulian_exp | 无匹配表 |
| anzbao/ 反构造目录 | 仅 APK 文件，无解压 lua 源码 |
| _tmp_cfg/*.luac | 仅 config_skill_xiulian.luac (115KB)，已反构造为 JSON |

---

### 结论

**"50"配置源：UNKNOWN（第二轮仍无突破）**

已穷尽静态配置检索：
- config_skill_xiulian.json 全部 5 表（Learn/Up/WorldLev/RoleLev/Lev）
- config_role_attr.json RoleAttr 经验表
- config_skill.json 基础技能表
- 全 cfg 目录关键字搜索

L22 级所有已知字段值均不匹配 50（63096 / [100,110] / 43）。

---

### 可能解释（待 luac 字节码反编译确认）

1. **客户端显示归一化**：将实际 exp（63096）按比例缩放至 0-50 区间显示（如 progress = floor(35 / 63096 * 50) ≈ 0.03，不匹配）
2. **客户端硬编码分母**：进度条 UI 设计为固定 50 格，与配置无关
3. **其他帧扩展字段**：SC_10304 / SC_10621 有未被 proto_defs 记录的隐藏字段
4. **SkillXiulianLev 语义误判**：[None, min, max] 可能不是等级要求而是经验区间，但 L22=[100,110] 不匹配 50

---

### 证据等级

| 项 | 等级 |
|---|---|
| 分子 35 = skill_list.exp | CONFIRMED |
| 分母 50 来自配置表 | UNKNOWN |
| 50 = 客户端归一化缩放 | INFERENCE（未证实） |
| 50 = 客户端硬编码 UI 设计值 | INFERENCE（未证实） |

> 需反编译 config_skill_xiulian.luac 或客户端修炼面板 lua 渲染函数才能最终定位。

---

## 追加：消耗/拥有栏数字来源定位（第三轮）

> 日期：2026-10-02 | 方法：UI 截图分析 + 资产表交叉验证

### UI 实锤（用户截图）

修炼面板结构：
- **修炼进度**: 35/50（绿色进度条，✅ 正确渲染，来自 skill_list exp=35）
- **消耗**: [EXP 蓝色火焰图标] + [空白条] + [!按钮]
- **拥有**: [EXP 蓝色火焰图标] + [空白条]

**关键事实**：我们已下发 `practice_exp=35`（SC_10304），但消耗/拥有栏仍空白 → **证实两栏数字不是从 SC_10304.practice_exp 读取**。

---

### 资产表交叉验证

`config_game_data.json` → `CodeToAssets` 资产类型列表：

| 索引 | 资产名 | 说明 |
|---:|---|---|
| 9 | **practice_exp** | 修炼经验（即 EXP 蓝色火焰图标对应货币） |
| 4 | exp | 角色经验 |
| 6 | experience | 经验（道具） |

**结论**：消耗/拥有栏的 EXP 图标 = `practice_exp`（资产类型 9）。

---

### 数据来源定位

| 栏位 | 可能来源 | 证据等级 | 说明 |
|---|---|---|---|
| **拥有栏** | SC_10305 assets 表（label=9） | **INFERENCE** | SC_10304 已下发仍空白，客户端可能从 SC_10305 资产表读取 |
| **消耗栏** | 客户端从 config 计算（SkillXiulianUp.exp） | **INFERENCE** | 应从配置表读取下一级消耗值 |
| 拥有栏 | SC_10304.practice_exp | ❌ 已排除 | 用户证实下发后仍空白 |

---

### 补丁方案（供实施代理）

**修复"拥有栏空白"**：
- 在 SC_10305（assets 表帧）中追加 `{label: 9, val: practice_exp值}`
- 当前 SC_10305 仅在 proto_defs 中定义，未实际发送
- 需在角色数据同步时推送完整资产表

**修复"消耗栏空白"**：
- 客户端应从 config_skill_xiulian SkillXiulianUp.exp 读取下一级消耗
- 若客户端未自动计算，需确认是否需要额外帧下发

---

### 证据等级

| 项 | 等级 |
|---|---|
| EXP 图标 = practice_exp（资产类型 9） | CONFIRMED |
| 拥有栏 ≠ SC_10304.practice_exp | CONFIRMED（用户实锤） |
| 拥有栏 = SC_10305 assets(label=9) | INFERENCE |
| 消耗栏 = config SkillXiulianUp.exp | INFERENCE |

---

## 追加：第四轮 —— ★ **SC_10305 是死代码**（实证）+ 10302/10304 均带 35

> 日期：2026-10-06 | 方法：抓帧（自写客户端）+ 服务端 tcp.log 全量统计 + 源码核对
> 背景：上一次改动为 `mock_server_r10305_20261002_112209.py`（11:22，即当前 `mock_server.py` 的最后修改）

### ① 抓帧实测：10302 / 10304 **都带 practice_exp=35**

`python tools/verify_practice_exp.py --port 9000`（新写工具，按 `attribute/handler.py` 逐字段解析）：

| 帧 | practice_exp | 备注 |
|---|---|---|
| **SC_10304** | **35** | 第 9 号资产位（body=182B，power=724112） |
| **SC_10302** | **35** | `SC_10302` **本身就有 `practice_exp` 字段**（proto_defs，第 11 项），实测同为 35 |

⇒ 服务端**两条客户端会请求的帧**都已携带 35。来源：`server/role/storage.py` L153-159 动态读 `skill{bid:10822}.exp`。

### ② ★ SC_10305 **从未被客户端请求过** ⇒ r10305 改动是**死代码**

`server/logs/tcp.log` 全量统计：

| 方向 | cmd | 次数 |
|---|---|---|
| 客户端 `>>` | 10305 | **0** |
| 服务端 `<<` | 10305 | **0** |
| 客户端 `>>` | 10302 | 11 |
| 客户端 `>>` | 10303 | 11 |
| 客户端 `>>` | 10301 | 50 |

而当前 `mock_server.py` L12621 的 `10305` 分支**确实**会把 `(label=9, exp=35)` 追加进 assets 表
（即第三轮的"补丁方案"已实现）—— **但客户端从不请求 10305，该分支永不执行**。

> ⇒ **结论**：第三轮提出的"拥有栏 = SC_10305 assets(label=9)"这条路径，
> **即便实现了也不会送达客户端**。该假设**无法**通过 10305 验证；
> 若拥有栏仍空白，真正要查的是 **10302 / 10304 之外的第三方来源**（或客户端渲染条件）。

### ③ 证据等级

| 项 | 等级 | 依据 |
|---|---|---|
| SC_10302 / SC_10304 均携带 practice_exp=35 | **CONFIRMED** | 抓帧实测 |
| 客户端从不请求 10305（r10305 为死代码） | **CONFIRMED** | tcp.log 全量统计 0 次 |
| 拥有栏的数据来源 | **UNKNOWN** | 10304 已排除（第三轮）；10305 路径不可达；10302 待实机判读 |
| 消耗栏来源 | **UNKNOWN** | 同上 |

### ④ 下一步（按证据收敛）

1. **实机判读**：`10302` 已带 35，若拥有栏**仍**空白 ⇒ 排除 10302，转向
   `10303`（技能推送，client 请求 11 次）或客户端本地渲染条件。
2. 若拥有栏**上屏** ⇒ gap #5 记 CONFIRMED。
3. 建议**清理 10305 死分支**（或改为在收到 10301/10302 时**主动 push** 10305），
   避免后续 agent 误以为"已接线"。

---

## 追加：第五轮 —— ★★ **穷尽性证明：服务端侧已完备，缺口在客户端**

> 日期：2026-10-06 | 方法：客户端面板反汇编 + 协议穷举 + 逐帧实测 + 用户实机回证
> 本轮结论**推翻了第三轮的"另有独立帧"假设**。

### ① 客户端面板反汇编：`拥有` 栏确实读 `RoleVo.practice_exp`

定位到真正的修炼面板：**`assets/src/game/skill/train/skill_train.luac`**
（全 APK 中唯一同时含「修炼 + 拥有 + 消耗」的 `game/` 模块；已提取到 `_tmp_train/`）。

`skill_train.luac` proto#10（`requestTrainSkill`，点"修炼"按钮）关键字节码：

```
Config.SkillXiulianUp[ cur_skill_data.bid ].exp   → need
GameData:getInstance():getRoleVo().practice_exp   → own      ← ★ 拥有栏数据源
cur_skill_data.current_exp                        → cur
per_to = floor((own + cur) / need * 100)，上限 100
```

⇒ 面板读的就是 **`RoleVo.practice_exp`**，与文档第三轮判断一致；
差异在于**本轮证明了该字段在服务端已被送到**。

### ② 协议穷举：全协议中**只有 3 条** SC 帧含 `practice_exp`

对 `protocol/fields.json` 全量递归扫描（含嵌套子表）：

| SC 帧 | 含 practice_exp | 服务端实测值 |
|---|---|---|
| **SC_10302** | ✓ | **35** |
| **SC_10303** | ✓ | **35** |
| **SC_10304** | ✓ | **35** |
| （SC_10305） | 否（是 `assets{label,val}` 表） | label 9 = **35**（本轮新推） |

⇒ **不存在"第四条未知帧"**（第三轮提出的候选路径已被穷举排除）。

### ③ 本轮新写/复用的实测工具

| 工具 | 作用 |
|---|---|
| `tools/verify_practice_exp.py` | 抓帧解析 SC_10304 **与** SC_10302 的 practice_exp |
| `tools/verify_10305_push.py` | 走完整登录序列，验证服务端是否**主动推** 10305 及其 `label 9` |

实测输出（本轮）：
```
SC_10304 practice_exp = 35   SC_10302 practice_exp = 35
SC_10303 practice_exp = 35
after 10102: cmds = [10102, 10200, 10201, 10305]
SC_10305 PUSHED: {1:1800140, 2:9904629, 3:99999999, 4:13239, 9:35, 15:3200, ...}
```

### ④ ★ 本轮代码改动（留档，**已通过全部 gate**）

上一版的 10305 分支是**死代码**（客户端从不请求，`tcp.log` 0 次）。
本轮改为**服务端主动推送**：

| 改动 | 位置 |
|---|---|
| 新增 `build_10305(cfg)`（资产 label 表 + `practice_exp` label=9） | `server/mock_server.py`（`build_10302` 之后） |
| 登录（10102/10103）后**主动 push** 10305 | 同文件登录分支 |
| `live_push()` 顺带推 10305 | 同文件 |

备份：**`server/backup/mock_server_10305push_20261006_143300.py`**（失败可回滚）。

**gate 结果**：`miniloop 145/145` ✓ ｜ `lint_dispatch_shadow ✓ 无分发遮蔽` ｜
`py_compile OK` ｜ `/DSH_ADMIN/status` lv70/scene=10001 ✓ ｜ 真实客户端已收到 10305（日志实证）。

### ⑤ ★★ 用户实机回证：**拥有栏仍空白**

⇒ 综合 ① ② ⑤：

> **服务端已把所有可能的载体都填成 35**（10302 / 10303 / 10304 命名字段 + 10305 的 label 9），
> 客户端面板也确认读 `RoleVo.practice_exp` —— **仍然空白**。
>
> ⇒ **缺口 #5 的前半（服务端下发）已 CONFIRMED；后半不是"缺帧"，而是客户端渲染条件问题。**

### ⑥ 证据等级（终版）

| 项 | 等级 | 依据 |
|---|---|---|
| 面板读 `RoleVo.practice_exp` | **CONFIRMED** | `skill_train.luac` proto#10 反汇编 |
| 全协议只有 10302/10303/10304 含该字段 | **CONFIRMED** | `fields.json` 全量递归扫描 |
| 三帧 + 10305 实测均为 35 | **CONFIRMED** | 抓帧实测 |
| 下发到客户端仍空白 | **CONFIRMED** | 用户实机回证（本轮） |
| "另有独立帧" 假设 | **✗ 已否证** | ② 穷举 |
| 拥有栏空白的**真实原因** | **UNKNOWN** | 属客户端渲染；需 frida/hook `rgp_hander10302/3/4` 与 `updateOwnExp` |

### ⑦ 下一步（方向已收敛，不再加服务端帧）

1. **停止在服务端加帧**——已穷举，加了也不会变。
2. 客户端 hook 三选一：
   a. hook `rgp_hander10302/10303/10304`，看 `practice_exp` 是否真写进 `RoleVo`；
   b. hook `skill_train.updateOwnExp`，看入参 `practice_exp` 与控件可见性；
   c. 检查 `cur_skill_data.current_exp` 是否为 nil（面板可能因该项为空而**整体不渲染数值**）
      —— ⚠ 本轮发现 `role_skills` **无 10822**（只有 `10020`），
      即"抗控修炼"**未在已学表**中；这可能是真正的渲染前提。
3. 若走 (2c)：需确认修炼技能是否必须先进 `role_skills`（10622 通道，
   但**客户端从不请求 10622**，0 次 ⇒ 同样不可达）。
