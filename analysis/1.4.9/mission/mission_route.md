# 任务路线提取 + A/B 判定 —— 结论与新的阻塞点

> 本轮做了 A/B 判定（原始配置 vs VO 的 `progress`），并按结论换了任务。
> **结果：`progress` 从 `n0` 变成 `n1` 了，但 `mis_content` 仍然是 nil ⇒ 阻塞点前移。**

---

## ★★ A/B 判定结果：**B**（任务本身 progress 为空，不是拷贝丢字段）

```
t=cfgCmp&v=bid_10010_rawType_table_rawProgress_table_n0_voProgress_table_n0_sameTable_true
```

| 读数 | 含义 |
|---|---|
| `rawProgress=table_n0` | **原始配置 `Config.Mission[10010].progress` 就是空表** |
| `voProgress=table_n0` | VO 里也是空表 |
| `sameTable=true` | **两者是同一个表** ⇒ **不存在"对象拷贝丢字段"** |

⇒ **候选 B 成立**，候选 A 否证。

## ★ 运行期全表扫描（`Config.Mission` 是活表，比静态解析可靠）

```
t=scanMis&v=total_846_withProg_531_sample_10070:1:t1,35013:1:t6,40008:1:t9,52031:1:t27,…
```

- `Config.Mission` 共 **846 条**
- 其中 **531 条有非空 `progress`**
- 样例里有 **`10070:1:t1`** —— **主线任务（type=1=MIS_ZHU）且带 1 条 progress**

## ★ 换任务实测：`progress` 有数据了，但 `mis_content` 仍为 nil

```json
"missions": [ { "mission_bid": 10070, ... } ]
```

```
t=misProg&v=progress_table_n1_type_1_status_1        ← progress 有 1 条 ✓
t=mcCall&v=bid_10070_mtype_1_lnum_1_tval_1_before_NIL_after_NIL   ← 仍 after_NIL
```

**⇒ 阻塞点**不只是** `progress` 为空。**

回顾分支④ 的代码（`mission_util proto[0]`）：

```lua
local roleVo = RoleCtrl:getInstance():getRoleVo()   -- @53-59
if roleVo == nil then return end                    -- @60-62
local prog = vo:getConfig().progress                -- @65-72   ← 现已通过（n1）
if prog == nil then return end                      -- @73-75
local step = prog[vo.mis_status]                    -- @76-80   ★ 下一个可能的门禁
if vo.mis_status == MissionStatus.STATUS_2
   and vo.mis_code == MissionCode.finish_flower then … end   -- @81-90
… MIS_COLLECT 分支 @92-111
… @113+ 按 commit_npc_id / accept_npc_id / mis_code 一大串分支拼正文
```

**⇒ 分支④ 后面还有若干分支/门禁（很可能与 `mis_status`、`mis_code`、
`commit_npc_id`/`accept_npc_id` 的取值有关），我们的值没命中任何一条会写 `mis_content` 的路径。**

---

## ★ 精确的下一步（一步就能看出卡在哪）

**在探针里量 `prog[vo.mis_status]` 到底是什么**（这是分支④ 里用 progress 的第一处）：

```lua
local p = vo.mis_config.progress
local s = vo.mis_status
report('progStep', 'p=' .. type(p[s]) .. '_keys=' .. <把 p 的键列出来> .. '_status=' .. s)
```

- 若 `p[s] == nil` ⇒ **键不匹配**（`progress` 的键不是 `mis_status`），
  需要搞清 `progress` 的键语义（可能是"步骤序号"从 1 开始，而 `mis_status` 不是序号）；
- 若 `p[s]` 有值 ⇒ 继续往 @81-@130 之后的**分支条件**查（`mis_status`/`mis_code`/
  `commit_npc_id`/`accept_npc_id`），用单变量调这些字段。

**这一步之后就能定位到确切的那一个条件。**

---

## ★ 继续取证：`progress` 的键 = 合法 `mis_status` 值

### 实测（`bid=10070`，主线「巫风挑战」）

```
t=progStep&v=status_1_p_status_table_keys_1:table      ← status=1 时 prog[1] 是 table ✓
```

### 对照实验：`mission_status = 2`

```json
{ "mission_bid": 10070, "mission_status": 2, ... }
```

```
t=progStep&v=status_2_p_status_nil_keys_1:table        ← status=2 时 prog[2] 是 nil ✗
t=mcCall&v=bid_10070_…_before_NIL_after_NIL
```

**⇒ `progress` 的键就是"合法的 `mis_status` 值集合"**（这里只有键 `1`）。
**所以 `mission_status = 1` 是正确取值**，status=2 反而查不到步骤。

### 结论：阻塞点定位到分支④ 的**后段**（@113 之后）

对照 `mission_util proto[0]` 分支④ 的判定链：

| 指令 | 条件 | 我们的值 | 结果 |
|---|---|---|---|
| @73-75 | `getConfig().progress == nil` | 是 table(n1) | 过 |
| @76-80 | `prog[vo.mis_status]` | status=1 ⇒ **table** | 过 |
| @81-85 | `mis_status == MissionStatus.STATUS_2`(=2) | `1` | 跳过 |
| @86-90 | `mis_code == MissionCode.finish_flower` | `0` | 跳过 |
| @92-111 | `mis_type == MissionType.MIS_COLLECT` | `1`(MIS_ZHU) | 跳过 |
| **@113+** | 按 `commit_npc_id` / `accept_npc_id` / `mis_code` 等一大串分支拼正文 | — | **★ 落在这里，没写出内容** |

### 已提取的常量（本轮新增）

```
MissionStatus = { STATUS_0 = 0, STATUS_1 = 1, STATUS_2 = 2, STATUS_3 = 3 }
```

且 `Config.Mission[10070] = { bid=10070, name='巫风挑战', type=1, desc='打败隔壁班的巫风' }`
（真实主线任务）。

### 下一步（精确）

**反汇编 `mission_util proto[0]` 的 @113–@260 段**，找出各条"给 `mis_content` 赋值"的
分支分别要求什么。它现在的形态已知是：

```
@113-121  取 getConfig().commit_npc_id / accept_npc_id
@121+     与 RoleCtrl / mis_code / mis_status 组合判断
```

把那段读出来，就能知道我们该填哪个字段（很可能与 `commit_npc_id`/`accept_npc_id`
是否配套、或 `mis_code` 的取值有关）。**仍按"先取证再改"，下一步只读代码 + 量字段。**

---

## ★ 当前任务系统能力盘点

| 项 | 状态 |
|---|---|
| 任务通道（12400 推送） | ✅ |
| 任务名 + 分类显示 | ✅ |
| 无 `nil` 文案 | ✅ 仅 `defaultMissionId=10000`（分支①，不看 progress） |
| 任意真实任务文案 | ❌ **阻塞点已从"progress 空"前移到"分支④ 后面的条件"** |
| 任务路线数据 | ⚠️ 部分（102 条循环任务；主线可改用运行期全表扫描，**531 条有 progress**） |
| 任务真实可执行 | ❌ 未达成 |

**重要收获**：`Config.Mission` 在运行期可读，**531 条任务带 progress** ——
以后挑任务不必再静态猜，直接在探针里扫即可（本轮 `scanMis` 已实现）。

> 目标：读取 APK 内本来的任务路线，使任务**真实可执行**。
> 本轮产出：提取到 **102 条任务**（`server/_mission_route.json`）。
> **但"真实可执行"仍被上一轮发现的 `progress` 空表问题卡住。**

---

## 一、本轮提取结果

对 `assets/src/config/config_mission.luac`（504KB，18737 条指令）做解析，
按"TDUP 出含 `bid`+`name` 的条目表 → 紧随的 KSHORT/KNUM 为键 → TSETV 落表"的规律提取：

```
提取到任务条目: 102
唯一任务 id 数: 102
type 分布: {6: 98, 12: 1, 17: 1, 29: 1, 25: 1}
```

前 20 条（按 id 排序）：

```
id=35000 type=6 名『寻人』 描述『学院任务』
id=35001 type=6 名『寻人』 描述『学院任务』
…（35000–35060 一片，均为 type=6）
```

`type=6` 在 `MissionType` 里是 **`MIS_HUAN`**（循环任务）。
⇒ **这批 102 条是"学院/循环任务"家族**，不是主线。

产物：`server/_mission_route.json`

```json
{ "35000": {"name":"寻人","type":6,"realm":0,"lev":0,"desc":"学院任务"}, … }
```

---

## 二、已知缺口（如实说明）

**主线任务（`100xx` 家族）没被这次解析捕获。**

证据：我此前**手工逐指令**从同一文件读到过：

```lua
Config.Mission[10010] = { bid=10010, name='斗罗魂师', desc='去周漪老师处报到',
                          type=1, is_drama=1, commit_npc_id=10030, commit_talk=50010,
                          progress = { … } }
Config.Mission[10020] = { bid=10020, name='切磋魂技', desc='与班长霍雨浩切磋', lev=2 }
```

说明主线条目在字节码里的构造形式与循环任务不同（很可能 `progress` 是**外部挂上去**的，
而不是写在同一个 TableConst 里 —— 这也与上一轮"运行期 `progress` 是空表"吻合）。

**⇒ 要拿到完整主线路线，解析器需要按"条目表 + 后续 `TSETS progress` 补充"两段式来读。**

---

## 三、真正的阻塞：任务"可执行"需要 `progress` 有数据

上一轮的实测结论（`analysis/1.4.9/mission/mission_status.md`）：

```
t=misProg&v=progress_table_n0      ← mis_config.progress 是空表（0 条）
t=mcCall&v=bid_10010_…_before_NIL_after_NIL
```

`MissionUtil.missionContent` 分支④ 的门禁：

```lua
local prog = vo:getConfig().progress
if prog == nil then return end          -- 空表也能过
local step = prog[vo.mis_status]        -- ★ 空表 ⇒ nil ⇒ 后面全拼不出来
```

### ★ 本轮新增的关键否定结果

**全仓搜 `TSETS progress` 的写入点，结果只有配置文件自己：**

```
config/config_mission.luac proto[0] @9 @38 @59 @80 @105 @134 @163 @192 @221 @246 …
（其余文件没有任何一处写 progress）
```

⇒ **上一轮"`progress` 很可能由某条服务端消息填充"的假设被否证** ——
**没有任何消息处理器写 `progress`**。

那么运行期 `mis_config.progress` 为空，只可能是下面两种之一：

| 候选 | 说明 |
|---|---|
| A. 该任务的配置里 `progress` 本来就是空的 | 我们挑的 `bid=10010` 可能恰好没有 progress 条目 |
| B. `vo.mis_config` 不是 `Config.Mission[bid]` 本身，而是客户端另建的（拷贝/合并）对象 | 拷贝时只取了部分字段，`progress` 落成空表默认值 |

**⇒ 下一步（一步就能区分 A/B）**：在探针里直接读 **`Config.Mission[10010].progress`**
（原始配置表），与 `vo.mis_config.progress` 对比：

- 若**原始配置里 `progress` 非空**、而 VO 里为空 ⇒ **B**（拷贝丢字段）；
- 若**两者都为空** ⇒ **A**（该任务本就没 progress）⇒ 那就**换一条配置里 `progress` 非空的任务**
  来做文案验证（可用脚本扫 `config_mission.luac`，找 `progress` 其数组非空的条目）。

### 关于"任务真实可执行"的整体判断

| 需要什么 | 现状 |
|---|---|
| 任务路线数据 | ⚠️ 已提取 102 条循环任务；主线需两段式解析补齐 |
| 任务下发通道（12400） | ✅ 通 |
| 任务名/分类显示 | ✅ 通 |
| 任务正文（`mis_content`） | ❌ 卡在 `progress` 空表 |
| 接/做/交任务（12402/12403/12404） | ❌ 未开始（需正文通了才有意义） |

**⇒ 距离"任务真实可执行"仍差 `progress` 这一环，而这一环已确认**不是**服务端消息问题，
而是配置/对象层面的问题 —— 这一轮把它缩小到了 A/B 两个候选。**

---

### ★ 进一步：把 `progress` 赋值对回任务 id

扫 `config_mission.luac` 里所有 `TSETS progress`，并往前回溯最近的"含 `bid` 的条目表"：

```
TSETS progress 出现次数: 846
能对到任务 id 的次数: 846
样例 (指令位置, bid): [(9,10010), (38,10020), (59,10030), (80,10040),
                      (105,10051), (134,10052), (163,10053), (192,10054), …]
```

⇒ **配置里确实为 `10010` 等任务赋了 `progress`（@9）**，共 846 处。

但反汇编看 `10010` 那一处：

```
8  TNEW  A=3 D=0        ; r3 = {}          ← 空的
9  TSETS A=3 B=2 C=3    ; ['progress']     ← progress 拿到的是这个空表
10 TNEW  A=3 D=4096     ; 又新建一个表，随后装 {1=2,2=1290} 等条目
17 TSETS A=3 B=2 C=7    ; ['award_assets'] ← 那些条目其实落到了 award_assets
```

**⇒ 与运行期实测 `progress = table_n0`（0 条）完全吻合 ⇒ 倾向候选 A：
`10010` 这条任务的 `progress` 在配置里本来就是空的。**

**⇒ 因此下一步是：在 846 处赋值里找一处"`progress` 拿到的是非空表"的任务，
用它来验证 `mis_content` 能否写出真实文案。**（需要按寄存器追踪每处 `progress`
的源表是否被填过条目。）

---

## 四、当前任务系统能力盘点

| 项 | 状态 | 依据 |
|---|---|---|
| 推送任务列表（12400） | ✅ | 客户端不主动请求，服务端推 |
| 任务名 + 分类显示 | ✅ | 面板出「主线-斗罗魂师」/「学院-寻人」 |
| 无 `nil` 的任务文案 | ✅（仅 `defaultMissionId=10000` 这条） | `before_NIL → after_19`，面板两行真实文案 |
| 任意真实任务的文案 | ❌ | 卡在 `mis_config.progress` 为空表 |
| 任务路线数据 | ⚠️ 部分 | 已提取 102 条循环任务；主线待用两段式解析补齐 |
| 任务"可执行"（接/做/交） | ❌ 未开始 | 需要 `progress` 通路打通后，再接 12402/12403/12404 |

**结论：距离"任务真实可执行"还差 `progress` 这一条通路。**
本轮把"路线数据"提取了一部分，但**没有**解决可执行性 —— 如实记录，不夸大。
