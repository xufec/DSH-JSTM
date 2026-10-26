# 1.4.9 掉落模型（drop_model）

> **目标 APK**：`anzbao\jstm.apk` — 绝世唐门 **1.4.9**，包名 `com.shiyue.dldl.ewan.qihoo`。
> **版本锁定声明**：本文全部证据仅来自上述 1.4.9 APK。`anzbao\jstm_142165.apk`（1.4.11）、
> `anzbao\dldlJl.apk`、`patched\*_142165*` **一律未读取**，不作为任何证据。
> 本文所有字段名、字段数、数值、CMD 号均可回溯到具体字节码位置；无法证实的部分一律标 `UNKNOWN`。

---

## 0. 结论速览

| 问题 | 结论 | 置信度 |
|---|---|---|
| 掉落表是否以 `mon_bid` 为键 | **是**，29 条记录的 `mon_bid` 字段与表键 100% 相同 | 已确认（字节码 + 数据一致） |
| 掉落表条目总数 | **29** 条 | 已确认 |
| 掉落池（Config.DropItem）组数 | **17** 组，`item_list` 终端条目 **39** 条 | 已确认 |
| 引用到的怪物 | 24 个（`Config.Mon` 内） + 5 个（`30001`–`30005`，**不在** `Config.Mon`） | 已确认 |
| 客户端是否读取 `Config.Drop` / `Config.DropItem` | **完全不读**。全 APK 2232 个 `.luac` 深字符串扫描，除两个文件自身的定义点外零引用 | 已确认 |
| 掉落池物品是否属于本作 | **全部不属于**。29 个 `item_bid` 全在 `51000`–`51066`，全是别家 IP 角色 | 已确认（名字）/ INFERRED（IP 归属） |
| 29 条中有物品内容的比例 | **17 / 29**（12 条三个掉落节全空） | 已确认 |
| 真实掉落判定算法 | **UNKNOWN** —— 在服务端，客户端包内不存在 | — |
| `pp` 的概率语义 | `pp / p_sum` 为命中概率 | **INFERRED**（算术关系 39/39 条成立，无代码可证） |

> ⚠️ **最重要的一条**：**掉落判定本身不在客户端里**。客户端只负责把服务器下发的
> 掉落物渲染成地面图标。因此"某个任务怪到底掉什么"在 1.4.9 客户端包内
> **不可恢复**，必须标 `UNKNOWN / TEST_ONLY`。
>
> ⚠️ **第二重要的一条（详见 §9）**：这两张表**很可能是模板残留，不是绝世唐门的内容**。
> 29 条里 **12 条完全没有物品内容**；掉落池里的 **29 个物品全部落在 `51xxx` 号段，
> 且全是其它游戏（仙剑/轩辕剑/古剑）的角色**（李逍遥、赵灵儿、南宫煌、柳梦璃…），
> 与绝世唐门自己的角色号段（`H30xxx`–`H35xxx`、`R01xxx`–`R11xxx`、`M40xxx` 等）
> **交集为空**。**不要直接把这张表搬进私服。**

---

## 1. 数据来源与提取方法

### 1.1 源文件

| 文件（APK 内路径） | 大小 | 全局表名 | 证据 |
|---|---|---|---|
| `assets/src/config/config_drop.luac` | 8195 B | `Config.Drop` | `proto#0` bc#4 `GSET 'Config'`；`proto#0` 内 `TSETS 'Drop'` |
| `assets/src/config/config_drop_item.luac` | 3939 B | `Config.DropItem` | `proto#0` bc#165 `TSETS 'DropItem'`；kgc#57=`'DropItem'`, kgc#58=`'Config'` |

两者都是 **LuaJIT 2.0 字节码**（dump version 1，flags `0x02` = STRIP），
由 `config_drop.luac` 的 `Config.Drop` 与 `config_drop_item.luac` 的 `Config.DropItem` 组成。

### 1.2 提取命令（可复现）

```powershell
python tools/apk_extract_luac.py "assets/src/config/config_drop.luac"      "analysis/1.4.9/item/_config_drop.luac"
python tools/apk_extract_luac.py "assets/src/config/config_drop_item.luac" "analysis/1.4.9/item/_config_drop_item.luac"
python tools/dump_drop_config.py analysis/1.4.9/item/_config_drop.luac      --json analysis/1.4.9/item/_config_drop.json
python tools/dump_drop_config.py analysis/1.4.9/item/_config_drop_item.luac --json analysis/1.4.9/item/_config_drop_item.json
python tools/analyze_drop.py --csv analysis/1.4.9/item/_drop_detail.csv
```

### 1.3 为什么不能用现成的 `tools/extract_config_table.py`

该工具的配键是启发式"最近一个数字常量"。`config_drop.luac` 的写法是
**KSHORT 出现在 TDUP 之后**（`TDUP` → `TNEW`×4 → `KSHORT 20001` → `TSETV`），
因此该工具会把键错配到 4 个空子表上，并丢失全部子表内容。

`tools/dump_drop_config.py` 改为**逐条执行一个极简 LuaJIT 解释器**，按键值对写入还原嵌套表。
为避免"读得对但写错"这类隐性错误，解释器的操作数编码用 `config_drop_item.luac`
的已知结构逐字节反推确认（见下）：

```
bc# 5  TSETB A=4  D=769   ; C=1, B=3 → reg4 是 TDUP 项结构, reg3 是 item_list
bc# 8  TSETS A=3  D=517   ; B=2, C=5 → reg2 有 p_sum（外层 TDUP）, C=5 是 'item_list'
bc# 9  KSHORT A=3 1001
bc#10  TSETV A=2  D=259   ; C=3 → 键在 r3=1001, 表在 r1, 值在 r2
```

由此确定 LuaJIT 2.0 的 `BC` 16 位字段是**小端**（`C = D&0xff`，`B = D>>8`），
且这些指令的统一规律是：

| 指令 | 值寄存器 | 表寄存器 | 键/下标 |
|---|---|---|---|
| `TSETS` | `A` | `B` | `kgc[C]` |
| `TSETB` | `A` | `B` | `C`（数组下标） |
| `TSETV` | `A` | `B` | `C`（寄存器，浮点键） |

**结果**：还原出 `Config.Drop` 29 条、`Config.DropItem` 17 组，全部字段数与名称一致。

---

## 2. Config.Drop 的表结构

### 2.1 逐条一致：每条记录 18 个字段

对全部 29 条记录做字段名集合的交集与并集，结果完全一致：**18 个字段**，无缺省、无变体。

| 字段 | 观测到的类型 | 语义 | 证据/置信度 |
|---|---|---|---|
| `mon_bid` | int | 怪物 bid，**与表键始终相同** | 已确认（29/29 `key == mon_bid`） |
| `drop_type` | int（0/1） | 掉落类型开关。29 条中 28 条为 1，仅 `30005` 为 0 | 值已确认；**语义 UNKNOWN**（无代码读取） |
| `over_type` | int（恒为 0） | 29 条全为 0 | 值已确认；**语义 UNKNOWN** |
| `first` | int（0 或 DropItem bid） | 首次击杀掉落的**掉落池 bid**。取值 1001/1002/1011，均存在于 `Config.DropItem` | 引用关系已确认；"首次"语义 **INFERRED** |
| `first_p` | table | 首次击杀的**权重池** | 结构已确认；语义 **INFERRED** |
| `first_p_sum` | int | `= Σ first_p[*].pp` | 已确认（算术 25/25 非空节一致） |
| `core` | int（0 或 DropItem bid） | 核心掉落的**掉落池 bid**。取值 2001/2002/2003/2004/2012 | 引用关系已确认 |
| `core_interval` | int（0/3/6） | 核心掉落间隔。取值：3 或 6，其余为 0 | 值已确认；**语义 UNKNOWN**（"每 N 次"为 INFERRED） |
| `core_p` | table | 核心掉落的权重池 | 结构已确认 |
| `core_p_sum` | int | `= Σ core_p[*].pp` | 已确认 |
| `normal` | table | 普通掉落，**三层**结构 | 已确认（见 §2.2） |
| `normal_sum` | table | `{item_bid: 该 item_bid 小节内 Σpp}` | 已确认 |
| `holiday` | int（0 或 3001） | 有掉落内容的条目为 3001，`30001`–`30005` 为 0 | 值已确认；**语义 UNKNOWN** |
| `holiday_key` | int（恒为 0） | 29 条全为 0 | 值已确认；**语义 UNKNOWN** |
| `holiday_p` | string | `'[{1,1000}]'` 或 `'[]'`，**是字符串不是表** | 已确认（`KSTR`，不是 `TDUP`） |
| `coin` | string | `'{1000}'` … `'{6000}'`，`30001`–`30005` 为 `'{0}'` | 已确认是字符串；**解析语义 UNKNOWN** |
| `wood` | string | `'{500}'` … `'{1000}'`，`30001`–`30005` 为 `'{0}'` | 已确认是字符串；**解析语义 UNKNOWN** |
| `morale` | string | 29 条全部为 `''` | 已确认 |

**关于 `coin` / `wood` / `holiday_p` 是字符串**：这不是提取误差，而是原始 `.luac` 里就是
`KSTR` 常量（如 `'coin', '{1000}'`）。**其内部语法（`{n}`、`[{a,b}]`）的解析器不在客户端里**
→ `UNKNOWN`。

### 2.2 `normal` 是三层结构（其余两节是两层）

这是最容易写错的地方，逐条核对后的结论：

```
normal[item_bid][中层键] = { num?, min, max, pp }     ← 三层
core_p[中层键]           = { num, min, max, pp }      ← 两层
first_p[中层键]          = { num, min, max, pp }      ← 两层
```

- **`normal` 外层键是 DropItem 的组 bid**（如 `4001`），中层键是自动编号（`'1'`, `'2'`, …）。
- **`core_p` / `first_p` 没有 item_bid 层**：本节对应的掉落池 bid 由同记录的
  `core` / `first` 字段给出。

实测 `30002` 的 `normal` 有两层切片，可清晰看到三层的两层含义：

```
normal = { "4012": { "1": {min:1,   max:500,  pp:500, num:1},
                     "2": {min:501, max:1000, pp:500, num:2} } }
normal_sum = { "4012.0": 1000 }
```

> `normal_sum` 的键在主表中是**浮点**（`4012.0`）——这是 LuaJIT `ktab` 把
> `4001` 与 `4001.0` 视为同一个 hash 槽而序列化成 `4001.0` 的结果，**不是两个不同的键**。
> 证据：`config_drop_item.json` 里同样出现 `'4001.0'`；而 TSETV 写入时用的是
> `KSHORT 4012`（整数）。

---

## 3. Config.DropItem 的表结构

- 全局名 `DropItem` 挂在 `Config` 下：`Config.DropItem`。
- 17 个组：`1001 1002 1011 2001 2002 2003 2004 2011 2012 3001 3002 4001 4002 4003 4004 4011 4012`
- 每组 2 个字段：`p_sum`（int）、`item_list`（数组表）
- `item_list` 共 39 条终端条目，每条 7 个字段：

| 字段 | 类型 | 语义 | 证据 |
|---|---|---|---|
| `bid` | int | **组 bid**，与组键相同（冗余回写） | 已确认 39/39 相同 |
| `item_bid` | int | **真实物品 id**（如 51000 小仙桃） | 已确认 |
| `item_name` | string | 物品名，客户端自带的中文名 | 已确认 |
| `item_num` | int | 数量 | 已确认 |
| `min` | int | 该条目 roll 区间下界 | 已确认 |
| `max` | int | 该条目 roll 区间上界 | 已确认 |
| `pp` | int | 权重/概率 | 已确认 |

### 3.1 关键算术关系（17/17 组成立）

对**全部 17 组**同时满足：

1. `p_sum == Σ item_list[*].pp`
2. 把 `item_list` 按 `min` 排序后，`max` **恰好等于 `pp` 的前缀累加**，
   `min == 前一 max + 1`（首条 `min == 1`）

实测抽样（全部 39 条成立，校验脚本 `tools/analyze_drop.py` 输出 `0 条不满足`）：

| 组 | p_sum | 条目 (pp, min, max) |
|---|---|---|
| 4001 | 100 | (50, 1, 50) (50, 51, 100) |
| 4002 | 60 | (30, 1, 30) (30, 31, 60) |
| 4003 | 150 | (50, 1, 50) (50, 51, 100) (50, 101, 150) |
| 2001 | 90 | (30, 1, 30) (30, 31, 60) (30, 61, 90) |
| 3001 | 36 | (12, 1, 12) (24, 13, 36) |
| 3002 | 144 | (36, 1, 36) (48, 37, 84) (60, 85, 144) |
| 4012 | 200 | (100, 1, 100) (100, 101, 200) |

**INFERRED 模型**：在组内均匀 roll `1..p_sum`，命中 `min ≤ roll ≤ max` 的条目，
故该条目概率 `= pp / p_sum`。上表 4001 即各 50%；3001 为 12/36 = 33.3% 与 24/36 = 66.7%。

> **没有代码可以证明这个 roll 模型**——客户端从不读这两张表。这是从
> "`max` 恒等于 `pp` 前缀累加"这一 39/39 成立的结构性事实推出的，
> 因此标记为 **INFERRED**，不是"已确认"。

---

## 4. 完整引用链（怪物 → 掉落表 → 物品）

```
Config.Mon[mon_bid]                                  ← analysis/1.4.9/task/config_mon.json
        │  （客户端内无任何代码建立此映射，仅靠 bid 数值一致）
        ▼
Config.Drop[mon_bid]                                 ← config_drop.luac
        ├── first  ──► Config.DropItem[first].item_list ──► item_bid（物品 id）+ item_num
        ├── core   ──► Config.DropItem[core ].item_list ──► item_bid + item_num
        ├── first_p / core_p / normal  ──► 权重池（min/max/pp）
        └── normal[dropitem_bid][切片的 min/max/pp] ──► Config.DropItem[dropitem_bid].item_list
                                                        └──► item_bid + item_num
        plus: coin / wood / holiday_p（字符串，内部语法未知 → UNKNOWN）
```

- `first`、`core` 是**直接指向 DropItem 组 bid 的整数**。
- `normal` 的**外层键**也是 DropItem 组 bid。
- 也就是说 `Config.Drop` 与 `Config.DropItem` 之间**只有这一种引用方式**：
  用 DropItem 的组 bid 去索引。

`Config.Drop` 引用到的 DropItem 组（14 个）：
`1001 1002 1011 2001 2002 2003 2004 2012 4001 4002 4003 4004 4011 4012`

`Config.DropItem` 中**存在但无任何引用**的组（3 个）：
`2011`（柳梦璃灵魂玉）、`3001`（李逍遥灵魂玉）、`3002`（赵灵儿灵魂玉）

> 这 3 组很可能是其它系统（活动/宝箱）在用，但**在客户端包内找不到消费者**
> → 引用来源 `UNKNOWN`。

---

## 5. 数量与覆盖统计

| 指标 | 数值 |
|---|---|
| `Config.Drop` 条目总数 | **29** |
| 其中 `mon_bid` 命中 `Config.Mon` | **24**（`20001`–`20024`） |
| 其中 `mon_bid` 不在 `Config.Mon` | **5**（`30001`–`30005`） |
| `Config.Mon` 怪物总数（参考） | 2645 |
| **有掉落表覆盖的怪物比例** | **24 / 2645 ≈ 0.91 %** |
| `Config.DropItem` 组数 | **17** |
| `Config.DropItem` 终端条目数 | **39** |
| 展开后的"怪物→物品"终端行数 | **75** |

### 5.1 关键发现：只有 0.91% 的怪物有掉落配置

`Config.Mon` 有 2645 个怪物，但 `Config.Drop` 只覆盖 **24** 个，
且这 24 个**全部落在 `20001`–`20024` 这一段连续区间**。
`Config.Mon` 在 `20025`–`20029` 也存在同名类型的怪物却没有掉落记录。

**这意味着**：普通任务怪（如 `10000`、`10001`、`30201` 等占绝大多数的 bid）
的掉落物**不可能来自这两张配置表**。它们的掉落只能来自：
1. 服务端的另一套（未打包进客户端的）配置 —— **不可恢复**；
2. 服务端硬编码 —— **不可恢复**。

→ 必须记为 **`UNKNOWN` / `TEST_ONLY`**：私服实现普通怪掉落时，
只能自建掉落表，不能声称"还原了原版"。

### 5.2 `30001`–`30005` 是什么

这 5 个 bid **不在 `Config.Mon` 中**（最近邻为 `30201`）。
它们与 `20001`–`20024` 有三处不同：

| 特征 | `20001`–`20024` | `30001`–`30005` |
|---|---|---|
| `holiday` | 3001 | **0** |
| `holiday_p` | `'[{1,1000}]'` | **`'[]'`** |
| `coin` / `wood` | `'{1000}'`…`'{6000}'` / `'{500}'`…`'{1000}'` | **`'{0}'` / `'{0}'`** |
| 掉落内容 | `normal` + 部分 `core` | 纯 `normal` / `core`，且为**副本型 boss 掉落** |

其物品池内容是"聂小倩召唤符 / 孙思邈召唤符 / 千叶禅师召唤符 / 星璇灵魂玉 / 唐雨柔灵魂玉 /
龙幽召唤符"—— 明显是**活动或副本 boss**，不是场景普通怪。

→ 这 5 条是**另一套 bid 空间（3xxxx）**的怪物/实体，但客户端没有对应定义。
具体身份 **`UNKNOWN`**；需要服务端数据或运行时抓包才能确认。

---

## 6. 客户端是否使用这两张表 —— 决定性证据

对 APK 内**全部 2234 个 `.luac`** 逐 proto 扫描字符串常量：

```powershell
python tools/find_luac_global.py Drop DropItem
```

```
=== 'Drop': 1 个 proto 命中 ===
   assets/src/config/config_drop.luac proto#0          ← 只有定义点自身
=== 'DropItem': 2 个 proto 命中 ===
   assets/src/config/config_drop_item.luac proto#0     ← 定义点自身
   assets/src/game/drop/drop_item.luac proto#17        ← 是类名 'DropItem'（场景掉落物 UI），非配置
```

补充扫描：`drop_type` / `drop_ratio` / `drop_bid` 作为字符串常量在整个 APK 中
**0 个 proto 命中**（连 `config_drop.luac` 之外的任何文件都不含）。

**结论**：`Config.Drop` / `Config.DropItem` 是**服务端下发逻辑的客户端副本，客户端从不读取**。

### 6.1 那客户端的 `assets/src/game/drop/**` 是做什么的

那里是**纯表现层**：

| 文件 | 作用 | 证据（字符串常量） |
|---|---|---|
| `drop_ctrl.luac` | 空控制器骨架，`registerProtocals`/`registerEvents` 均为空体 | 300 B，仅 5 proto，proto#4 定义 4 个空方法 |
| `drop_data.luac` | 空数据类 | 93 B，仅 2 proto，只有 `__init` |
| `drop_vo.luac` | 地面掉落物的 VO（坐标 `x`/`y`/`p`）+ `getName`/`getPosition`/`getSceneId` | 272 B |
| `drop_item.luac` | 地面掉落物的**图标/动画**：`item_icon`、`shadow`、`MoveBy`、`ScaleTo`、`FadeIn`、`openResultPanel` | 3461 B，无任何概率/物品表引用 |

`drop_item.luac` 的字段是 `setPosition`/`setScale`/`setOpacity`/`runAction`，
**完全没有读取任何配置表**。也就是说客户端拿到的是服务器已经算好的掉落结果。

---

## 7. UNKNOWN 清单（明确列出，不猜）

| 项 | 状态 | 需要什么证据才能确定 |
|---|---|---|
| 掉落判定算法（roll 时机、次数、保底、多件掉落上限） | **UNKNOWN** | 服务端代码，或对 1.4.9 官服抓包复现 |
| `drop_type` / `over_type` 的取值语义 | **UNKNOWN** | 服务端代码 |
| `core_interval` 的单位与语义（"每 N 次击杀"是 INFERRED） | **UNKNOWN** | 服务端代码 |
| `holiday` / `holiday_key` 的语义 | **UNKNOWN** | 服务端代码 |
| `coin` / `wood` 字符串 `'{1000}'` 的语法 | **UNKNOWN** | 需要找到解析 `{}` 的服务端/Lua 模块（客户端内不存在） |
| `holiday_p` 字符串 `'[{1,1000}]'` 的语法 | **UNKNOWN** | 同上 |
| `morale` 的用途 | **UNKNOWN** | 29 条全为 `''`，无区分度 |
| `first_p` / `core_p` / `normal` 三个节之间的优先级与互斥关系 | **UNKNOWN** | 服务端代码 |
| `30001`–`30005` 对应的实体身份 | **UNKNOWN** | 服务端数据 / 抓包 |
| `normal_sum` 的键为何以浮点 `4001.0` 存 | 已解释为 LuaJIT hash 归一化，但**未用代码证明** | `config_drop_item.luac` 同样出现 `'4001.0'`，可佐证 |
| 普通任务怪（2645 中的 2621 个）的掉落 | **UNKNOWN / TEST_ONLY** | 不可从客户端恢复；私服必须自建 |

---

## 8. 对私服实现的直接建议

1. **可以照搬**：`Config.Drop` 29 条 + `Config.DropItem` 17 组的**结构与数据**
   已完整还原（`analysis/1.4.9/item/_config_drop.json`、
   `_config_drop_item.json`），实现 `pp/p_sum` 的 roll 即可得到合理掉落。
2. **不要声称"还原了原版掉落"**：判定逻辑在服务端，客户端只证明了**数据表**，
   没有证明**算法**。
3. **普通任务怪掉落必须自建**，并明确标注为自定义内容。
4. 若要验证 roll 模型，最小实验：对 `20003`（`normal` 只有 `4001` 一组、
   `pp` 各 50、`p_sum` 100）击杀 N 次统计 51000 小仙桃的 `item_num` 分布，
   看是否为 1:1。这需要真实的服务端实现，属 `TEST_ONLY`。

---

## 9. ⚠️ 补充发现：这张掉落表很可能是**模板残留**，不是绝世唐门的内容

在完成 §1–§8 之后做的进一步核查，发现两个必须在实现前知道的事实。

### 9.1 29 条记录里，**12 条完全没有物品内容**

| 分类 | 数量 | mon_bid |
|---|---|---|
| **有物品内容**（含 `first`/`core`/`normal` 任一） | **17** | `20003 20004 20007 20008 20011 20012 20015 20016 20019 20020 20023 20024 30001 30002 30003 30004 30005` |
| **完全无物品内容**（只有 `coin`/`wood` 字符串） | **12** | `20001 20002 20005 20006 20009 20010 20013 20014 20017 20018 20021 20022` |

那 12 条的 `first_p` / `core_p` / `normal` 与 `normal_sum` **全为空表**，
`first=0`、`core=0`、`core_p_sum=0`，只有 `coin`（如 `'{1000}'`）与
`wood`（如 `'{500}'`）。也就是说这 12 条**只可能产出货币/木材**，
且 `coin`/`wood` 的字符串语法客户端不解析（§7）。

各节出现次数：

| 节 | 条目数 | mon_bid |
|---|---|---|
| `first`（首次） | 3 | `20012 20024 30005` |
| `core`（核心） | 8 | `20004 20008 20012 20016 20020 20024 30003 30004` |
| `normal`（普通） | 14 | `20003 20004 20007 20008 20011 20012 20015 20016 20019 20020 20023 20024 30001 30002` |

### 9.2 掉落池里的物品**全部是其它游戏的 IP**

`Config.DropItem` 的 39 条 `item_list` 只涉及 **29 个不同物品**，
`item_bid` **全部落在 `51000`–`51066` 这一个带内**。
这些物品名是：

| IP | 物品名（`item_bid`） |
|---|---|
| 《仙剑奇侠传》系列 | 李逍遥召唤符(`51007`)/灵魂玉(`51037`)、赵灵儿召唤符(`51009`)/灵魂玉(`51039`)、林月如召唤符(`51010`)/灵魂玉(`51040`)、酒剑仙召唤符(`51008`)/灵魂玉(`51038`)、龙葵召唤符(`51030`)、小蛮召唤符(`51031`)、**唐雨柔灵魂玉**(`51066`)、**龙幽召唤符**(`51029`) |
| 《轩辕剑》系列 | 南宫煌召唤符(`51011`)/灵魂玉(`51041`)、**魔翳召唤符**(`51028`)、**飞蓬召唤符**(`51027`)、**夕瑶召唤符**(`51032`) |
| 《古剑奇谭》 | **星璇灵魂玉**(`51065`)、**柳梦璃灵魂玉**(`51064`)、**孙思邈召唤符**(`51020`)、**千叶禅师召唤符**(`51024`) |
| 《聊斋》/其它 | **聂小倩召唤符**(`51013`)、**宁采臣召唤符**(`51026`) |
| 通用消耗品 | 小仙桃(`51000`)、大仙桃(`51001`)、铜·经验符(`51004`)、银·经验符(`51005`)、金·经验符(`51006`) |

> 上表的"IP 归属"是**文字层面的常识判断（INFERRED）**，
> **不是**从 APK 里得到的字段——APK 只提供 `item_name` 字符串本身。
> 可以 100% 确认的是：**这 29 个名字里没有一个是绝世唐门的角色**
> （绝世唐门的角色名可对照 `config_mon.json`，如戴浩、贝贝、宁天、叶夕水、
>  男/女火凤、男/女玄武、女琉璃 等）。

对照绝世唐门自己的角色命名空间（`analysis/1.4.9/task/config_mon.json`，2645 条）：

| 对比项 | 掉落表物品 | 绝世唐门角色 |
|---|---|---|
| id 带 | **`51000`–`51066`** | `H30xxx`–`H35xxx`、`R01xxx`–`R11xxx`、`M40xxx`、`N10xxx`、`B40xxx` |
| res_id 数字段 | 51000 段 | 30000/31000/32000/33000/34000/35000/37000/40000 |
| 前缀 | 无（纯数字 bid） | `H`(1962) / `R`(156) / `M`(459) / `N`(55) / `B`(10) |
| 交集 | **空集** | — |

**没有任何一件掉落物品能对应到绝世唐门的角色资源。**
`item_bid` 段内还有大量空洞（`51002`、`51003`、`51014`–`51019`、`51021`–`51023`、
`51025`、`51033`–`51036`、`51042`–`51063` 均未出现），
说明这是一个**被多个游戏共用的 51000 段物品号池**，
本游戏只用到其中一部分（而且用到的部分也不是自己的角色）。

### 9.3 结论：这批数据不能当作"绝世唐门 1.4.9 的掉落表"使用

综合 §5.1（只覆盖 0.91% 的怪物）、§6（客户端从不读取）、§9.1（42% 条目无物品）、
§9.2（物品全是别家 IP），最合理的解释是：

> **`config_drop.luac` / `config_drop_item.luac` 是从引擎模板或同发行商的
> 姊妹项目继承下来的残留配置**，在绝世唐门 1.4.9 里**既不被客户端读取，
> 内容也与本作角色无关**。

因此：

- 这两张表**不能**作为"原版掉落"的依据，也**不能**直接搬进私服让玩家得到
  "仙剑/轩辕剑角色的召唤符"。
- 它们**唯一可靠的用途**是：作为**掉落算法的结构样例**
  （`mon_bid → {first, core, normal} → DropItem 组 → {min,max,pp}` 这套三层结构
   与 `pp/p_sum` 权重关系），以及作为 **1.4.9 物品 id 段（`51xxx`）** 的存在证明。
- 绝世唐门真正的掉落与物品配置**不在客户端包内** → `UNKNOWN / TEST_ONLY`。

### 9.4 一处需要注意的 id 规律

所有 `item_bid` 都是 `51000 + n` 的形式。其中
`51007`–`51013` 是仙剑主角，`51026`–`51032` 是仙剑/轩辕剑另一批角色，
`51037`–`51041` 与 `51064`–`51066` 是"灵魂玉"（`51064`–`51066` 与前面的
`51037`–`51041` 不在同一小段，疑为后期追加）。
这个分段属于 INFERRED 观察，**未用代码证明**。

---

## 附：证据文件清单

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/item/_config_drop.luac` | 从 1.4.9 APK 提取的原始字节码 |
| `analysis/1.4.9/item/_config_drop_item.luac` | 同上 |
| `analysis/1.4.9/item/_config_drop.json` | 还原出的 `Config.Drop`（29 条） |
| `analysis/1.4.9/item/_config_drop_item.json` | 还原出的 `Config.DropItem`（17 组） |
| `analysis/1.4.9/item/_drop_detail.csv` | 展开后的 75 行终端明细 |
| `analysis/1.4.9/item/_assets_config.json` | `assets/config.json`（证明包内无物品数据表） |
| `tools/dump_drop_config.py` | 嵌套表还原器（含操作数编码推导） |
| `tools/analyze_drop.py` | 统计/校验/明细生成 |
| `tools/find_luac_global.py` | 全包全局名引用扫描（仅顶层字符串） |
| `tools/scan_luac_strings_deep.py` | **深字符串扫描**（含 TableConst 键/值），修正了上者的假阴性 |
