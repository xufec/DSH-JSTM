# NPC 对话：第十轮 — 定位到 `setSceneInfo` 与 `openNpc.ctrl`

> 承接九轮追查。本轮做了**静态精确反汇编** + **运行时绕过修复的真实部署测试**。

---

## 一、静态反汇编：报错点**精确到指令**

### `openNpc`（`npc_dialogs.luac` proto[8]，137 条）

```lua
  @0   TGETS 'ctrl'                    → R2 = self.ctrl            ★ 关键
  @2   TGETS 'setOpenNpc'
  @4   CALL                            → self.ctrl:setOpenNpc(...)
  @5   GGET 'Config' / TGETS 'Npc' / TGETV / TSETS 'npc_cfg'
  @9   GGET 'SceneModel' / getInstance() / **getScene()**          ← 返回 nil
  @17  TGETS 'getNpcByBid'             ← ★ 在 nil 上索引
  @20  TGETS 'vo' → npc_vo
```

### `setSceneInfo`（`scene_model.luac` proto[80]，21 条，**带 A/B/C 操作数**）

```lua
  @0-2  R2 = Config.Map[id]
  @3    TSETS A=2 'scene_info'    ⇒ R1['scene_info'] = R2    ← **写在 R1（参数 id）**
  @4    GGET  A=2 'TileUtil'
  @5    TGETS A=3 B=0 'scene_info' ⇒ R3 = **R0['scene_info']** ← **读的是 R0（self）**
  @6    TGETS A=3 B=3 'tile_w'     ⇒ R3 = R3['tile_w']        ← ★★ **R3 为 nil ⇒ 报错点**
```

**定标依据（已知语义构造，`npc_ctrl proto[84]`）：**
```
@7 GGET A=0 'NpcCtrl' / @8 FNEW A=1 / @9 TSETS A=1 'config'
⇒ 意图必然是 NpcCtrl.config = <函数>，表在 R0、值在 R1，而 A=1
⇒ **TSETS A, C ⇒ R(A-1)[K[C]] = R(A)**  ✓
```

**⇒ 即 `setSceneInfo` **写 R1、读 R0** ⇒ **`self.scene_info` 永为 nil** ⇒ @6 索引 nil ⇒
**这正是探针里 `attempt to index field 'scene_info'` 的来源。****

---

## 二、`changeScene` 链路（proto[66]，80 条）—— 逻辑本身是**对的**

```lua
changeScene(self, scene_data):
  @18-20 self:clear()
  @21-22 self.line_id = scene_data.line_id
  @23-24 self.sceneId = scene_data.bid          ← ★ 先设 sceneId
  @25    self.scene_data = scene_data
  @27-29 **self:sceneStart()**                   ← 无参数调用（与 sceneStart 读 self.sceneId 一致）
  @30-39 GlobalEvent:Fire(SceneEvent.TANCHAUNG, ...)
```

**⇒ 且 `on10200` **根本不检查 `code`**：**
```lua
on10200 (proto[8], 仅 6 条): @0 'model' / @2 'changeScene' / @4 CALL
```
**⇒ 所以之前怀疑的「`SC_10200` 回 `code=0` 导致 `changeScene` 不被调用」**不成立**。**

---

## 三、★ 运行时绕过修复（**已真实部署并测试**）

### 做法

在探针里包住 **`setSceneInfo`** 与 **`sceneStart`**，把 `self.scene_info` 与 `TileUtil.scene_info` **都补上**
（覆盖两种寄存器解释），并记录每次调用的实际参数。

### 实测结果

```
2 x setSceneInfo_id10001_mptable        ← ★ setSceneInfo 被调用，id=10001，Config.Map[10001] **是 table** ✓
1 x inst_setOpenNpc_function            ← 实例上**有** setOpenNpc
1 x NpcCtrl_getOpenNpc_function
1 x NpcCtrl_setOpenNpc_function
1 x okfalse__...attempt_to_call_method__setOpenNpc___a_nil_value   ← ★ self.ctrl 是 nil
3 x openNpc_okfalse_e_...attempt_to_index_a_nil_value
1 x openNpc_type_nil_bid_false          ← bid 也成了 nil
```

### ★ 两个**新的、更精确**的发现

| # | 发现 | 含义 |
|---|---|---|
| **1** | **`setSceneInfo` 确实被调用，`id=10001`，`Config.Map[10001]` 是 table** | **所以数据是齐的** —— 问题**不在数据缺失**，而在**赋值目标错位（写 R1 读 R0）** |
| **2** | **`attempt to call method 'setOpenNpc' (a nil value)`** | **`openNpc` 的 `self.ctrl` 是 nil** —— 这是**比 `getScene()` 更靠前**的失败点 |

**⇒ 即：`openNpc` 在第 @0-@4 条（`self.ctrl:setOpenNpc`）就已经失败了，
根本还没走到 `getScene()`（@9）。**

---

## 四、★ 诚实结论（第十轮）

### 已完成

| 项 | 状态 |
|---|---|
| 报错点精确到**指令级** | ✅ `setSceneInfo @6 R3.tile_w`（R3 = `self.scene_info` = nil） |
| `changeScene` 链路 | ✅ **逻辑正确**（先设 `sceneId` 再调 `sceneStart`）；`on10200` 不检查 `code` |
| `setSceneInfo` 运行期调用 | ✅ **确实被调用，id=10001，`Config.Map[10001]` 存在** |
| 绕过修复 | ⚠️ **已部署但未生效**（`self.ctrl` 仍为 nil） |

### 未解决

**⇒ `openNpc` 的 `self.ctrl` 为 nil —— 这比 `getScene()` 更靠前，是本轮**新暴露**的失败点。**

**⇒ 我**没有**解决 NPC 对话。十轮下来把范围从"报错行号为 0 的黑洞"缩到
**两条具体指令 + 两个具体对象（`self.ctrl` / `self.scene_info`）**，
但**仍未闭环** —— 如实记录，不假装解决。**

---

## 五、下一步（有依据，但本轮未做）

| 方向 | 依据 | 说明 |
|---|---|---|
| **1. 查 `self.ctrl` 的来源** | `openNpc @0 TGETS 'ctrl'` | 需查 `npc_dialogs` 的 `ctrl` 是谁赋值的、为何为 nil —— **比 `getScene()` 更靠前** |
| **2. 运行时包 `openNpc` 入口** | — | 打印 `self` 的全部字段 + `self.ctrl` 的 type，看 `ctrl` 到底有没有被赋过 |
| **3. `setSceneInfo` 的写读错位** | 静态已确认（写 R1 读 R0） | **若这是客户端 bug，服务端无法修**；只能靠探针在调用后补 `self.scene_info`（本轮已做，但被 @0-4 的失败挡住） |

---

## 六、自查

```
lua-check OK（120355 字节）｜ 探针已部署（含 setSceneInfo/sceneStart 包装）
服务端 8080/9000 正常 ｜ 服务端代码本轮**未修改**
```
