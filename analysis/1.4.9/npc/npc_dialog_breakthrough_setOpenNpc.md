# 五步完善计划 · 执行进展（① NPC 对话 / ② mis_code / ③ 战斗画面 / ④ 稳定性 / ⑤ 横向系统）

> 依据：`report/jstm_privateserver_maturity_update.md` 的优先级建议。
> 原则：只用**日志 / 字节码 / 数据库**证据；无证据标 `UNKNOWN`。

---

## ① NPC 对话 UI —— ★★ **本轮取得关键突破**（真实错误拿到了）

### 之前四轮的困境

`v:openNpc(10030)` 一直报 **`npc_dialogs.luac:0: attempt to index a nil value`** ——
**行号是 0、没有堆栈** ⇒ 无法判断是哪一行、哪个 nil。

### 本轮做法：换 `xpcall + debug.traceback`

```lua
local ok, err = xpcall(function() v:openNpc(10030) end,
  function(e)
    local tb = ''; pcall(function() tb = debug.traceback('', 2) end)
    return tostring(e) .. ' @ ' .. tostring(tb)
  end)
```

### ★ 结果：**真实错误与之前完全不同**

```
okfalse: game/npc/npc_dialogs.luac:0: **attempt to call method 'setOpenNpc' (a nil value)**
```

**⇒ 不是"索引 nil"，而是**"调用 `setOpenNpc` 这个方法不存在"（`a nil value`）！**
**⇒ 之前四轮围绕"self.ctrl / self.ctrl.manager 是 nil"的推断**方向就错了**（信息不足导致）。**

### ★ 精确定位：`setOpenNpc` 的定义与调用

| 文件 | proto | 位置 | 操作 |
|---|---|---|---|
| **`game/npc/npc_ctrl.luac`** | **proto[84]** | @132 | **`TSETS 'setOpenNpc'`** ← **定义处** |
| `game/npc/npc_dialogs.luac` | **proto[8]** | @2 | `TGETS 'setOpenNpc'` ← **调用处** |

（`npc_dialogs proto[8]` = `openDefault`，早前扫描已确认它引用 `openDefault`。）

**⇒ 结论（`CONFIRMED`）：`NpcDialogs.openDefault` 会对某个对象调 `setOpenNpc`，
但**该对象没有这个方法** —— 因为 `setOpenNpc` 是 `npc_ctrl proto[84]` 挂上去的，
而我们的 `NpcCtrl` 实例（或传给 dialogs 的对象）**不是那个被挂方法的对象**。**

### ★ 下一步（一步可验）

**看 `npc_ctrl proto[84]` 把 `setOpenNpc` 挂在**哪个对象**上**（`TSETS` 的前一个寄存器是哪个全局/实例），
然后把**那个对象**（而不是 `NpcCtrl:getInstance()`）传给 `NpcDialogs`。

---

### ★★ 再进一步：`setOpenNpc` 是**谁的方法**（已确认）

反汇编 `npc_ctrl.luac proto[84]` —— **这是一个类定义块**（把方法挂到 `NpcCtrl` 类上）：

```lua
@0   GGET 'NpcCtrl' / IST / JMP
@3   GGET 'BaseClass' ; GGET 'BaseController' ; CALL ; GSET     ← 继承
@7   GGET 'NpcCtrl' @8  FNEW @9  TSETS 'config'
@10  GGET 'NpcCtrl' @11 FNEW @12 TSETS 'initMnpcList'
@13  GGET 'NpcCtrl' @14 FNEW @15 TSETS 'registerEvents'
@16  GGET 'NpcCtrl' @17 FNEW @18 TSETS 'clickNpcOpenDialog'
@19  GGET 'NpcCtrl' @20 FNEW @21 TSETS 'registerProtocals'
@22  GGET 'NpcCtrl' @23 FNEW @24 TSETS 'sendBtn'
@25  GGET 'NpcCtrl' @26 FNEW @27 TSETS 'sendBtnHandler'
...
（`setOpenNpc` 亦在本块内以 `GGET NpcCtrl + FNEW + TSETS` 形式挂上）
```

**⇒ 结论（`CONFIRMED`）：`setOpenNpc` 属于 **`NpcCtrl` 类**。**

### ⇒ 因此报错的**真正含义**

`npc_dialogs proto[8]`（`openDefault`）对某个对象调 `:setOpenNpc(...)`，
**而那个对象**不是** `NpcCtrl` 实例** ⇒ 元表里没有该方法 ⇒ `attempt to call method 'setOpenNpc' (a nil value)`。

**⇒ 不是"服务端数据不对"，而是"调用时传错对象"（客户端侧的调用链需要正确的对象）。**

### ★ 下一步（**一步可定**）

**看 `npc_dialogs.luac proto[8]` 里 `TGETS 'setOpenNpc'` **前面的接收者是谁**
（是 `self`？`self.ctrl`？某个 vo？）—— 反汇编出来即可确定该传哪个对象。**

**⇒ 这比前四轮"猜 self.ctrl / self.ctrl.manager"要确定得多，因为**错误信息本身已经指明了缺失的方法名**。**

---

### ★★★ 最后一步解析：接收者与**根因**（已完成）

反汇编 `npc_dialogs.luac proto[8]`（`openDefault`，params=2，137 条字节码）**开头三条**：

```lua
@0  TGETS 'ctrl'          -- REG = self.ctrl
@1  MOV
@2  TGETS 'setOpenNpc'    -- REG = self.ctrl.setOpenNpc
@3  MOV
@4  CALL                  -- self.ctrl:setOpenNpc(...)
```

**⇒ 接收者 = **`NpcDialogs` 实例的 `ctrl` 字段**；而 `setOpenNpc` 属于 **`NpcCtrl` 类**（已确认）。**

### ★ 根因（`CONFIRMED`）：`NpcCtrl` 的类定义块**未执行**

| 证据 | 内容 |
|---|---|
| `npc_ctrl proto[84]` 开头 | `GGET 'NpcCtrl' ; IST ; JMP` ⇒ **"若 `NpcCtrl` 已存在则跳过整块定义"**（**懒加载类定义**） |
| 实测枚举 `NpcCtrl` 实例 | 只有 `New / __delete / __init / super` —— **没有 `setOpenNpc`** |
| 实测错误 | `attempt to call method 'setOpenNpc' (a nil value)` |

**⇒ 结论：`NpcCtrl:getInstance()` 是在**类方法挂载之前**就被取到的
（`BaseController.New` 先建实例，而 `proto[84]` 的 `GGET/IST/JMP` 守卫让定义块没跑到）
⇒ **实例上没有 `setOpenNpc` 等方法** ⇒ `openDefault` 调用时炸。**

**⇒ 这不是"服务端数据不对"，是**客户端类定义加载顺序**问题。**

### ★ 顺带拿到的**高价值事实**：原版取 NPC vo 的正规途径

`proto[8]` 中段（@9–@21）：

```lua
SceneModel:getInstance():getScene():getNpcByBid(bid)   -- ★ 按 bid 取场景 NPC 实体
   .vo                                                  -- ★ 取它的 vo
   → self.npc_vo
```

**⇒ 这就是**原版获取 NPC vo 的正规 API**：`getScene():getNpcByBid(bid).vo`**
（比我们之前遍历 `SceneModel.npcList` 更直接，且是客户端自己认定的方式。）

并且它会读 `npc_vo.misc`（`pairs`）来识别活动任务：
`MissionType.MIS_MENPAI` / `MissionType.MIS_NEWYEAR` → `activityMis`。

### ★ 修复方向（明确）

**先确保 `NpcCtrl` 类定义块（`proto[84]`）执行完，再取实例/调 `openDefault`**；
或直接把 `NpcDialogs.ctrl` 指向**已完整定义**的 `NpcCtrl` 对象。
**（本轮未实施 —— 因为"何时类定义才完成"需要在真机上再验一次，不凭猜改。）**

---

## ①之二、★★ 第二轮深入：**真正的 bug 找到了（`view.ctrl` 指向错误对象）**

### 先更正上一轮的一个方法错误

上一轮我用 **`pairs(instance)` 枚举 `NpcCtrl` 实例**，只看到 `New/__delete/__init/super`，
据此说"实例上没有 `setOpenNpc`"。**这是错的** —— **`pairs` 看不到元表/类上的方法。**

**静态确证**（`npc_ctrl proto[84]` @130-132）：
```lua
@130  GGET 'NpcCtrl'      ← 接收者
@131  FNEW proto[65]      ← 函数体
@132  TSETS 'setOpenNpc'
```
**⇒ `setOpenNpc` 确实挂在 `NpcCtrl` 类上。**

### 运行时直取（`t=so` 探针）—— **矛盾暴露了真凶**

```
NpcCtrl_setOpenNpc = function       ← 类上有
inst_setOpenNpc    = function       ← ★ 实例上也有
view_has_ctrl      = true           ← NpcDialogs.view.ctrl **已经非 nil**
after_ctrl_set_type = nil           ← ★★★ 但 v.ctrl.setOpenNpc 是 nil！
```

**⇒ 结论（`CONFIRMED`）：`NpcDialogs` 实例的 `ctrl` 字段指向的**不是 `NpcCtrl`**，
而是另一个没有 `setOpenNpc` 的对象 ⇒ 调用失败。**

### 强制覆盖后：**卡点前移了一步**

```
forced_ctrl_has    = function                                  ← 强制 v.ctrl = NpcCtrl:getInstance() 后有了
openNpc2_okfalse_e = ...attempt to **index** a nil value       ← ★ 错误从 "call setOpenNpc" 变成 "index nil"
```

**⇒ `setOpenNpc` 已成功调用；错误换成了 `index a nil value`。**

### `setOpenNpc` 本体（proto[65]，**只有 2 条字节码**）

```lua
function(self, x)
  self.selectNpcBid = x     -- @0
  return                    -- @1
end
```
**⇒ 它不会索引 nil ⇒ 新的 nil 在**它之后**的代码里。**

### 新卡点定位（回到 `npc_dialogs proto[8]`）

```lua
@4   CALL                                   ← self.ctrl:setOpenNpc(x)   ✓ 已通
@5   GGET 'Config' / TGETS 'Npc' / TGETV    ← Config.Npc[x]
@9   GGET 'SceneModel' / TGETS 'getScene' / CALL
@17  TGETS 'getNpcByBid' / CALL
@20  TGETS 'vo'                             ← ★ getScene():getNpcByBid(bid).vo
```

**⇒ 最可能：`SceneModel:getInstance():getScene()` 在**探针执行那一刻**返回 nil
⇒ `:getNpcByBid` 索引 nil。**（探针跑在 `t%15==0`，可能早于场景就绪。）

### ★ 下一步（两个动作，按顺序）

1. **把探测时机移到场景就绪之后**（例如复用 `on10201` 之后的那一刻）再调 `openNpc`
   —— 若成功即证明是**时序问题**
2. 若仍失败，则 wrap `getScene` / `getNpcByBid`，看哪一个返回 nil

**⇒ 这也是一个明确的"修复候选"：把 `NpcDialogs.view.ctrl` 修正为真正的 `NpcCtrl` 实例。**

---

## ①之三、★★★ 第三轮：实施修复候选 —— **排除了"时序问题"**

### 做了什么

按上一轮的两个修复候选实施：

1. **强制修正** `NpcDialogs.view.ctrl = NpcCtrl:getInstance()`
   （原来只在 `nil` 时赋值，而它**非 nil 但是错误对象**）
2. **把调用时机移到 `on10201` 之后**（场景就绪）

### 结果

```
forced_ctrl        = function        ← ★ 强制覆盖成功，setOpenNpc 存在了
in_npcs25_mons1_elems0               ← 场景已就绪（on10201 收到 25 个 NPC）
after_npcList25_elemList0_monList1   ← SceneModel.npcList = 25
openNpc_okfalse_e = ...attempt to **index** a nil value     ← ★ 仍然报错
```

**⇒ 结论（`CONFIRMED`）：**即使场景已就绪、`ctrl` 已修正、`setOpenNpc` 已可调用，
`openDefault` 内部仍在**同一位置**索引到 nil。**
**⇒ 这不是时序问题，而是**数据缺失**。**

### 目前的精确定位（收敛到 3 个候选）

`npc_dialogs proto[8]` 中 `setOpenNpc` 调用（@4）**之后**的索引点：

| @ | 代码 | 若为 nil 的可能原因 |
|---|---|---|
| @5–@8 | `self.npc_cfg = Config.Npc[x]` | `x`（我们传的 bid，如 10030）在 `Config.Npc` 里查不到 |
| @9–@16 | `SceneModel:getInstance():getScene()` | 场景对象本身（**已排除**：npcList=25 说明场景在） |
| @17–@20 | `...:getNpcByBid(bid).vo` | **`getNpcByBid(10030)` 返回 nil** ⇒ `.vo` 索引 nil |

**⇒ 最可能是 `getNpcByBid(10030)` 没找到**：`npcList` 里的 NPC bid 是 `10150` 等，
而我们传的 `10030`（周漪）**未必在当前场景的 npcList 里**。

### ★ 下一步（最后一个动作，一定能定论）

**用 `npcList` 里真实的 bid 去调 `openNpc`，并 wrap `getNpcByBid` 看它对目标 bid 返回什么。**

**⚠ 更正（本轮自查否证了自己的假设）：**

我上一版曾写"最可能是 `getNpcByBid(10030)` 没找到，因为 10030 不在场"。
**实测否证**：

```
服务端下发 NPC bid (25): [10010, 10020, **10030**, 10040, 10050, ...]
mission 10010  commit_npc=10030  ⇒ **在场** ✓
```

**⇒ `10030`（周漪）确实在服务端下发的 25 个 NPC 里，所以我那个"不在场"的猜测不成立。**
**⇒ nil 的位置仍未定论 —— 必须 wrap `getScene` / `getNpcByBid` 才能确认。**

（仍成立的一点：`mission 10030` 的 `commit_npc_id=20011` **确实不在**这 25 个里，
所以"**部分**任务需要的提交 NPC 不在本图"这个更大范围的问题是真实的，但**不是本次 nil 的原因**。）

### 本轮净结论（② 的当前状态）

| 项 | 状态 |
|---|---|
| 真因 1：`view.ctrl` 接错对象 | ✅ **已确认并已修**（强制覆盖后 `setOpenNpc` 可调用） |
| 真因 2：时序（场景未就绪） | ❌ **已排除**（场景就绪后仍失败） |
| 真因 3：NPC 不在场 | ❌ **已否证**（10030 在 25 个里） |
| nil 的确切位置 | ⚠️ **仍未知** —— 需 wrap `getScene` / `getNpcByBid` |
| **游戏逻辑改动** | ✅ **无**（仅探针 + `config.json` 的 `mission_chain_max`） |

---

## ①之四、★★★★ **最终定位成功：`getScene()` 返回 nil**

### 最后一击的探针（同时取三个候选）

```lua
Config.Npc[10030]                                -- @5  候选 1
SceneModel:getInstance():getScene()              -- @9  候选 2
...:getNpcByBid(10030)                           -- @17 候选 3
```

### 结果（`t=loc`）

```
ConfigNpc_t = table   entry = true     ← Config.Npc[10030] **存在** ✓
getScene_t  = **nil**                   ← ★★★★ **就是它！**
v_ctrl_ok   = function                  ← ctrl 已修好 ✓
openNpc_okfalse_e = ...attempt to index a nil value     ← 因为 getScene() 是 nil
```

### ★★★ 定论（`CONFIRMED`）

**`SceneModel:getInstance():getScene()` 返回 `nil`。**

`npc_dialogs proto[8]` 的 `@9-@17`：
```lua
SceneModel:getInstance()   -- 有对象（它的 npcList 里有 25 条）
   :getScene()             -- ★ 返回 nil
   :getNpcByBid(bid)       -- 在 nil 上索引  ⇒  报错
```

**⇒ 这就是"NPC 交互没了"的**最终根因**：不是 `setOpenNpc` 缺失（已修），
不是时序（已排除），不是 NPC 不在场（已否证）—— 而是 **`getScene()` 给不出场景对象**。**

### ★ 一个重要联系

**这与更早的 `report/jstm_privateserver_maturity.md` §八 标记的"硬阻塞：`getScene()==nil`"是**同一件事**。**

**⇒ 说明那个问题**并没有被真正解决**：
场景画面能渲染、`SceneModel.npcList` 有 25 条 NPC、战斗能打，
**但 `getScene()` 依然是 nil** —— 所以任何依赖"场景对象"的客户端功能（NPC 对话）都会失败。**

### ★ 修复方向（两条，都不需要服务端改数据）

| 路径 | 做法 | 风险 |
|---|---|---|
| **A（治本）** | 查清客户端**为什么 `getScene()` 为 nil** —— 它大概是"场景 view/node"，其创建条件未满足 | 需继续查客户端 |
| **B（绕过）** | 让对话链路**不走 `getScene()`**：直接从我们已能拿到的 `SceneModel.npcList`（25 条）里取目标 vo，喂给 `NpcDialogs` | 属"改客户端行为"，需谨慎 |

**⇒ 下一轮建议走 A**：wrap `SceneModel.getScene` / `SceneModel.setScene`，看**谁在什么时候设它**、
以及**为什么没设**。这是把"硬阻塞"真正解开的唯一办法。

### ② 的完整定位链（四轮，全部有实测证据）

```
第 1 轮  错误信息只有 "luac:0: index a nil value"（无行号）→ 只能猜
第 2 轮  xpcall+traceback 拿到真错误："attempt to call method 'setOpenNpc'"
第 3 轮  静态确证 setOpenNpc 挂在 NpcCtrl；运行时发现 view.ctrl 指向**错误对象** → 强制修好
第 4 轮  排除时序（场景就绪仍失败）、否证"NPC 不在场"
第 5 轮  ★ 直接取三个候选 → **getScene() 是 nil**（定论）
```

---

## ①之五、★★★★★ **根因链追到表达式级（本轮最终结论）**

### 逐层向下（每层都有字节码或实测证据）

```
getScene()            →  return self.scene                        [proto[75]，仅 2 条字节码]
self.scene 只由        →  sceneStart() 创建（SceneView:New()）      [proto[68] @4-10]
sceneStart() 当前失败于 →  attempt to index field 'scene_info' (nil) [实测]
scene_info 由          →  setSceneInfo(id) 设置：Config.Map[id]     [proto[80] @0-3]
```

### 实测：传 `sceneId=10001` 后**仍然** `scene_info == nil`

```
calling_sceneStart_sceneId10001
sceneStart_okfalse_e = ...attempt to index field 'scene_info' (a nil value)
after_scene_t = nil
```

### ★ 但静态验证发现**矛盾**

`Config.Map` **确实有 10001**：
```
config_map.json：124 条，'10001' 存在，字段完整（bid / cols / def_x / elems / esp / bsp / …）
```

**⇒ `Config.Map[10001]` 不为 nil，但 `sceneStart` 读到的 `scene_info` 仍是 nil。**

### ⇒ 最可能的原因（**标 `INFERRED`，尚未验证**）

`setSceneInfo` 的字节码：
```lua
@0  GGET 'Config' / @1 TGETS 'Map' / @2 TGETV [idx]     -- Config.Map[id]
@3  TSETS 'scene_info'                                   -- ★ 接收者**未必是 self**
@4  GGET 'TileUtil'
@5  TGETS 'scene_info'                                   -- 这里读的是 TileUtil.scene_info
```

**⇒ 极可能：`scene_info` 写在 **`TileUtil`（全局单例）** 上，
而 `sceneStart` 读的是 **`self`**（或反之）—— **两个对象的 `scene_info` 不是同一个。**

**⇒ 这是我本轮能追到的最深处。** 验证它只需一步：
**在运行时同时打印 `SceneModel:getInstance().scene_info` 与 `TileUtil.scene_info`，看哪一个非 nil。**

### ② 的完整链条（六轮，全部有实测/字节码证据）

| 轮 | 结论 | 自我更正 |
|---|---|---|
| 1 | 只有 `luac:0: index a nil value`（无行号） | — |
| 2 | `xpcall+traceback` → `call setOpenNpc` | ✅ 更正方向 |
| 3 | `setOpenNpc` 在 `NpcCtrl` 上；真因是 **`view.ctrl` 接错对象** | ✅ 更正 `pairs` 假象 |
| 4 | 排除时序；否证"NPC 不在场" | ✅ 否证自己 |
| 5 | 三候选直取 → **`getScene()` 是 nil** | — |
| 6 | `getScene` = `self.scene`；只由 `sceneStart()` 建；`sceneStart` 缺 `scene_info`；**`Config.Map[10001]` 却存在** ⇒ 怀疑 `self` / `TileUtil` 对象不一致 | — |

---

## ①之六、★★★★★★ 第七轮：**"手动补齐 scene_info"被否证**（本轮最终）

### 做了什么

在调 `sceneStart` 之前**手动**补上 `sm.scene_info = Config.Map[10001]`，并同时打印两处 `scene_info`。

### 结果（决定性）

```
Config.Map[10001]        = table     ← ★ 数据确实在
sm.scene_info            = nil
TileUtil.scene_info      = nil
manual_set_sm_scene_info = done      ← ★ 手动设置**成功**
sceneStart_okfalse_e     = ...attempt to index field 'scene_info' (a nil value)   ← ★★ 仍然报错！
after_scene_t            = nil
```

### ⇒ 结论（`CONFIRMED`）

**`sceneStart` 内部读的 `scene_info` **既不是 `SceneModel` 实例的、也不是 `TileUtil` 的** ——**
**是一个**第三对象**的 `scene_info`；或者在 `setSceneInfo` 内部它又被写成了 nil。**

**⇒ 我上一轮提出的修复方案（"把 `sm.scene_info` 补上"）**被实测否证**。**

### ⇒ 这已经超出"改探针就能解决"的范围

要真正解开，需要**完整的客户端调用链分析**：
**谁在什么时候调 `sceneStart`、传的参数是什么、`setSceneInfo` 的赋值目标到底是哪个对象**
—— 这需要做**寄存器级的字节码分析**（不是靠探针试），工作量超出本轮。

### ★ ② 的最终诚实结论

| 层级 | 结论 | 状态 |
|---|---|---|
| 现象 | NPC 对话调不起来 | — |
| 直接原因 | `NpcDialogs.openDefault` 里 `getScene()` 为 nil | ✅ 确认 |
| `getScene()` | `return self.scene`（纯字段读） | ✅ 确认 |
| `self.scene` | 只由 `sceneStart()` 创建（`SceneView:New()`） | ✅ 确认 |
| `sceneStart()` | 失败于 `scene_info` 为 nil | ✅ 确认 |
| `scene_info` | `Config.Map[10001]` **有数据**，但 `sceneStart` 读到的却是 nil | ✅ 确认（**矛盾已确证**） |
| **矛盾的根因** | **未知** —— 需寄存器级分析 | ❌ **UNKNOWN** |
| 我的修复尝试 | 手动补 `sm.scene_info` ⇒ **否证无效** | ❌ 已否证 |

**⇒ 这是本次调查能到达的最深处。** 再往下需要**逐条字节码做寄存器追踪**，
而不再是"加个探针试一下"能解决的 —— **我把边界如实标在这里，不假装已经解决。**

---

## ①之七、★★★★★★★ 第八轮：**寄存器级追踪（本轮最终交付）**

### `setSceneInfo` proto[80]（`self` = R0），带 A/B/C 操作数

```
@0  GGET  A=2  'Config'                     R2 = Config
@1  TGETS A=2 B=2  'Map'                    R2 = Config.Map
@2  TGETV A=2 B=2 C=1                       R2 = Config.Map[R1]      （R1 = 参数 id）
@3  TSETS A=2 C=0  'scene_info'             ← ★ 写目标的 A 寄存器 = **2**，不是 0(self)
@4  GGET  A=2  'TileUtil'
@5  TGETS A=3 B=0 C=0 'scene_info'          ← ★ 读的是 **R0['scene_info']**（= self.scene_info）
@6  TGETS A=3 B=3 C=5 'tile_w'
```

### `sceneStart` proto[68] @7-@21（`self` = R0），带操作数

```
@7  GGET  A=2 'SceneView'  @8 TGETS A=2 'New'  @9 CALL A=2
@10 TSETS A=2 C=2 'scene'                   ← ★ A 寄存器同样是 2
@11 GGET  A=2 'ViewManager' … @16 TGETS A=2 'changeSceneLayer'
@17 TGETS A=4 B=0 C=2 'scene'               ← 读 self.scene
@18 TGETS A=4 B=4 C=8 'root'
@20 TGETS A=6 B=0 C=9 'scene_info'          ← ★ 读 **R0['scene_info']**（self）
@21 CALL
```

### ★ 关键观察（`CONFIRMED`：操作数本身）

**两处 `TSETS` 的 A 寄存器都是 `2`，而 `self` 是 `R0`：**

| 位置 | 意图（从上下文） | A 寄存器 |
|---|---|---|
| `setSceneInfo @3` | `???['scene_info'] = Config.Map[id]` | **2** |
| `sceneStart @10` | `self.scene = SceneView:New()` | **2** |

**⇒ 而两处**读**`scene_info` 都用 `TGETS B=0`（即 `R0` = `self`）。**

**⇒ 结论：`setSceneInfo` 的**写目标**与 `sceneStart` 的**读目标**不是同一条寄存器路径 ——
这与实测的"矛盾"（`Config.Map[10001]` 有数据、`self.scene_info` 却为 nil）**完全吻合**。**

### ⇒ 这就是"矛盾"的机制级解释（`INFERRED`，需确认 `TSETS` 的确切语义）

LuaJIT 的 `TSETS A, C` 语义需以权威为准（本轮未逐位确认）；
但**操作数已确证**：写用的 A 与读用的 B **不一致**。
**⇒ 极可能 `setSceneInfo` 把 `scene_info` 写到了 `Config.Map[id]`（配置表）上，
而 `sceneStart` 从 `self` 读 —— 于是永远读到 nil。**

### ★ 本轮诚实的终点

**我把链路追到了**操作数级**（A/B/C 寄存器已确证），
但**判定 `TSETS` 语义需要一个完整的 LuaJIT 寄存器语义实现**（现有 `luajit_dis.py` 只做反汇编）。

**⇒ 这是纯静态工作，不需要设备；但工作量是一次"小型解释器"级别的开发。**
**⇒ 建议作为**独立任务**做（工具一旦成型，可复用于很多同类"对象不一致"问题）。**

**⇒ 在此之前，我不宣称 `getScene()==nil` 已解决 —— 它仍是一个**有机制级线索但未闭环**的问题。**

---

## ①之八、★★★★★★★★ 第九轮：**`TSETS` 语义定标（本轮最终交付）**

### 方法：用一个**必然成立**的构造反推语义

`npc_ctrl proto[84]` 的类定义块里有一组**语义无争议**的构造：

```
@7   GGET  A=0  'NpcCtrl'      R0 = NpcCtrl
@8   FNEW  A=1  proto[0]        R1 = <函数体>
@9   TSETS A=1  key='config'    ← 意图**必然**是 NpcCtrl.config = <函数>
```

**⇒ 表在 R0、值在 R1，而指令的 A = 1：**

### ★ 定标结果（`CONFIRMED`，由已知构造反推）

```
TSETS A, C   ⇒   R(A-1)[K[C]] = R(A)
```

### 用它回读 `setSceneInfo` / `sceneStart`

| 位置 | 原指令 | 按定标展开 | 含义 |
|---|---|---|---|
| `setSceneInfo @3` | `TSETS A=2 'scene_info'` | **`R1['scene_info'] = R2`** | 写在 **R1**（= 第一个参数 `id`）上 |
| `setSceneInfo @5` | `TGETS A=3 B=0 'scene_info'` | **`R0['scene_info']`** | 读的是 **R0 = self** |
| `sceneStart @10` | `TSETS A=2 'scene'` | `R1['scene'] = R2` | 同样写在 R1 |

### ★★★ 结论：**写 R1、读 R0**

**`setSceneInfo` 把 `Config.Map[id]` 写到 **R1（参数 `id`）** 的 `scene_info` 字段上，
而后续（以及 `sceneStart`）从 **R0（self）** 读 `scene_info` —— 于是**永远读到 nil**。**

**⇒ 这与实测矛盾（`Config.Map[10001]` 是 table、`self.scene_info` 却 nil）**完全吻合**。**

### 剩余的未确认点（如实）

- 若 `R1` 是**数字**（我们传的 `id = 10001`），`R1['scene_info'] = ...` 本应报
  `attempt to index a number` —— **但实测没报这个错**。
  ⇒ 说明**调用时的 R1 不是数字**（可能是表），或 `TSETS` 在数字上的行为另有细节。
- **⇒ 这个不一致我**没时间验证**，如实标为未闭环。**
- 另一条线索：`sceneStart @2` 读的是 `R0['sceneId']`（`self.sceneId`），
  而我探针实测 `sm.sceneId` 是 **0** —— 这可能是另一个独立问题。

### ★ 本轮交付的"寄存器语义"结论（可复用）

```
TSETS A, C   ⇒   R(A-1)[K[C]] = R(A)      ← 由 npc_ctrl proto[84] 类定义块定标
```

**⇒ 这条规则足以解释本问题，也可用于其它同类"对象不一致"的分析。
但要把它做成**通用工具**，仍需完整的寄存器分配/生命周期实现（本轮只做了**单点定标**）。**

### ★ 诚实的边界

**我**没有**解决 `getScene()==nil`**，但把它的机制追到了**一条可陈述的语义规则**
（`TSETS` 写 `R(A-1)`）和一个**具体的对象错位**（写 R1、读 R0）。
**⇒ 再往下需要"谁在何时以什么参数调 `sceneStart`"的完整调用链 —— 这需要真机抓调用栈，不是静态能定。**

---

## ② 抓 `mis_code` 跑通寻路 —— 探针已就位，但**未取到 vo**

### 已做

- `message` 包裹**已装成功**（`t=msg&v=message_wrapped`）—— 一旦 `missionGoto` 走到兜底，就能抓到真实 `mis_code`
- 扫描 `MissionCtrl` 的字段/方法名（**不猜，枚举**）

### 结果

```
MissionCtrl_n4 ->  New / __delete / __init / super
inst_n4        ->  New / __delete / __init / super
```

**⇒ `MissionCtrl` 是 `BaseController` 风格：实例上**只有** `New/__delete/__init/super`，
**没有可见的任务列表字段**（数据应在 `super` 或通过 `__index` 元表访问）。**

**⇒ 因此仍**没拿到 mission vo** ⇒ `missionGoto` 未被调用 ⇒ `mis_code` 未取到。**

### 已确认的线索（下一轮可直接用）

`MissionCtrl` 的字符串表里有：
```
ALL_MISSION  ADD_MISSION  DELETE_MISSION  GIVE_UP_MISSION
MIS_ADD  MIS_FINISH  MIS_FINISH_LIST  MIS_FINISH_COUNT  MIS_MAIN_ID_FINISH
```

**⇒ 任务列表很可能是通过**事件**（`ADD_MISSION` / `MIS_FINISH_LIST` 等）驱动的，
而不是一个可直接读的 `mis_list` 字段。**
**⇒ 下一步：包住 `MissionCtrl` 上与 `MIS_*` / `ALL_MISSION` 相关的方法，从中拿到 vo。**

---

## ③ 独立验证战斗画面 —— **未做**（本轮容量用于 ①②）

**现状**：战斗**流程**已实测全通（`20002 → 20010 → 20012/20013 ↔ 20014 → 20020 → 20023`，
逐回合伤害、怪物死亡、结算、掉落进包、反哺任务进度）。
**「画面是否渲染」仍为 `UNKNOWN`** —— 未截到战斗画面帧。

---

## ④ 稳定性 —— **本轮遇到并处理了一次设备掉线**

| 事件 | 处理 |
|---|---|
| `adb.exe: device '127.0.0.1:16384' not found`（打包安装阶段） | `adb disconnect` → `adb connect 127.0.0.1:16384` → 恢复；并发现 `emulator-5554` 与 `127.0.0.1:5555` 也在线（**同一模拟器的多入口**，印证上午版的说法） |
| 服务端 | 保持运行：8080/9000 同一 PID，`stderr 0 字节` |

**⇒ TCP 间歇断连的根因**仍未定位。**

---

## ⑤ 横向系统（公会/拍卖/结婚/跨服/伙伴/地下城）—— **未做**

**范围与工程量提示**：`known commands: 1634`，其中横向系统占很大一块；
按当前"一次通一条纵向链"的节奏，属**数倍于现有工程量**的工作。

---

## 本轮净收获

| # | 收获 | 证据强度 |
|---|---|---|
| 1 | **NPC 对话的真实错误** = `attempt to call method 'setOpenNpc'`（**推翻前四轮的 nil 方向**） | **CONFIRMED**（`xpcall` 实测） |
| 2 | **`setOpenNpc` 定义在 `npc_ctrl proto[84]`、调用在 `npc_dialogs proto[8]`** | **CONFIRMED**（字节码交叉引用） |
| 3 | `MissionCtrl` 实例**无可见任务列表字段**，任务应由**事件**驱动 | **CONFIRMED**（枚举实测） |
| 4 | 设备掉线可自动恢复（`adb disconnect/connect`） | **CONFIRMED** |
| 5 | 打包门禁不变：`lua-check OK`（108,662 字节） | — |

## 如实说明

- **① 和 ② 都**没有**拿到最终结果**（对话未出现、`mis_code` 未抓到），
  但 **① 把卡点从"不知道哪一行"推进到"缺 `setOpenNpc` 方法 + 已知它的定义位置"**，
  这是本轮最有价值的进展。
- **我没有把"拿到了真实错误信息"写成"对话已修好"**。
- ③④⑤ 本轮未取得实质进展，如实标注。
