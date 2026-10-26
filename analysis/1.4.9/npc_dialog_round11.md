# NPC 对话 第十一轮：`self.ctrl` 存在，失败点回到 `getScene()`

> 承接第十轮。本轮包住 `NpcDialogs.openNpc` 入口，打印 `self` 全部字段。

---

## 一、运行时取数（真实部署）

```
openNpc_self_ttable_ctrltable_keys_
  is_auto:boolean  class_type:table  style:number  close_mode:number
  is_load_finish:boolean  view_tag:number
  **ctrl:table**        ← ★ 存在（不是 nil）
  **npc_cfg:table**     ← ★ 也存在
  assets:table  DeleteMe:function  popup_data:string ...
```

**错误：**
```
openNpc_ERR__string__game/npc/npc_dialogs.luac__:0:_attempt_to_index_a_nil_value
```

---

## 二、★ 两个结论

### 结论 1：`self.ctrl` **存在**（第十轮的怀疑被否证）

**第十轮看到 `attempt to call method 'setOpenNpc' (a nil value)`，我怀疑 `self.ctrl` 为 nil。**
**⇒ 本轮实测：`ctrl:table` —— **`self.ctrl` 是 table，存在**。**
**⇒ 所以那条 `call method` 的报错**不是** `self.ctrl` 为 nil 造成的（可能来自另一条调用路径）。**

**⇒ **这是我第十轮的推断被实测否证 —— 第 6 处自我更正。****

### 结论 2：失败点**回到了 `getScene()`**

**加上 wrapper 后，错误从 `call method 'setOpenNpc'` 变成 `attempt to index a nil value`。**
**⇒ 对应 `openNpc` 的 `@9-@17`：**
```lua
@9-16  SceneModel:getInstance():getScene()      ← 返回 nil
@17    TGETS 'getNpcByBid'                      ← ★ 在 nil 上索引
```

**⇒ **失败点从 `@0-@4` 移到了 `@9-@17`** —— 又回到九轮的老结论：`getScene() == nil`。**

---

## 三、★ 所以整条链最终收敛到**一个点**：`setSceneInfo` 的写读错位

**十一轮下来，所有证据都指向同一处：**

```lua
setSceneInfo(self, id):                        -- scene_model.luac proto[80]
  @0-2  R2 = Config.Map[id]                    -- ← 数据齐（实测 id=10001, mp 是 table）
  @3    TSETS A=2 'scene_info'   ⇒ R1['scene_info'] = R2    -- ★ 写在 **R1**
  @5    TGETS A=3 B=0 'scene_info' ⇒ R3 = R0['scene_info']   -- ★ 读 **R0**(self)
  @6    TGETS A=3 B=3 'tile_w'      ⇒ R3['tile_w']           -- ★★ nil ⇒ 报错
```

**⇒ `self.scene_info` **永远不会被赋值**（因为写在 R1 上）。**
**⇒ 这是**客户端自身的寄存器/对象错位**。**

**⇒ 而 `getScene()` 为 nil 的最终原因，就是 `sceneStart` 依赖 `self.scene_info`，
而后者从未被设置。**

---

## 四、★ 为什么我的绕过修复**没生效**（如实）

**我在第十轮包了 `setSceneInfo`，试图在调用后补 `me.scene_info = mp`。**

**但实测显示：**
```
2 x setSceneInfo_id10001_mptable      ← wrapper 生效（id/mp 都对）
openNpc 仍失败：index a nil value
```

**⇒ 可能原因（**未验证**）：**
1. **`setSceneInfo` 在 `sceneStart` 内部被调用，而 `sceneStart` 在 wrapper 之后才跑** ⇒ **时序上应该没问题**
2. **`me` 在 `setSceneInfo` 里可能不是 `SceneModel` 实例**（若它以 `TileUtil:setSceneInfo()` 之类调用）
3. **`getScene()` 返回的是 `self.scene`，而 loop 修复的是 `self.scene_info`** —— **两者是不同的字段！**
   **⇒ 我补了 `scene_info`，但 `sceneStart` 里的 `self.scene = SceneView:New()` 是否执行成功，**未被验证****

**⇒ ⇒ 第 3 点最可能：我的 wrapper 补了 `scene_info`，但**没有确认 `self.scene` 是否真被赋值**。**

---

## 五、诚实结论（第十一轮）

| 项 | 状态 |
|---|---|
| `self.ctrl` 是否存在 | ✅ **实测存在（table）** —— 第十轮的怀疑**被否证** |
| 失败点 | ⚠️ 回到 **`getScene()` 返回 nil** |
| 最终收敛点 | ✅ **`setSceneInfo` 写 R1 / 读 R0 的错位**（静态已确认，操作数级） |
| 我的绕过修复 | ⚠️ **wrapper 生效但未解决问题**；原因**未验证**（最可能是"补了 scene_info 但 scene 仍未赋值"） |
| **NPC 对话** | ❌ **十一轮仍未闭环** |

**⇒ 我**没有**解决 NPC 对话。十一轮把范围从"报错行号为 0"缩到
**一条具体指令（`setSceneInfo @6`）+ 一个具体字段（`self.scene_info` 写错目标）**，
但**仍未闭环 —— 如实记录，不假装解决。**

---

## 六、下一步（唯一有依据的方向）

**⇒ 直接验证 `self.scene` 到底有没有被赋值。**

**具体做法：包住 `sceneStart`，在**调用后**打印 `me.scene` 的 type（而不是 `me:getScene()` ——
后者内部就是 `self.scene`，但用 `me.scene` 更直接）；同时在 `SceneView:New()` 外面包一层，
看它是否被调用、是否抛异常。**

**⇒ 若 `SceneView:New()` 抛异常 ⇒ 真正的阻塞点在那里（而不是 `scene_info`）。**
**⇒ 若 `SceneView:New()` 正常但 `self.scene` 仍为 nil ⇒ 说明 `TSETS` 的目标寄存器确实是 R1，
则 `sceneStart` 的 `self.scene = ...` 也被写错了 —— **那是同一个客户端 bug 的第二处**。**

---

## 七、自查

```
lua-check OK（121513 字节）｜ 探针已部署（含 NpcDialogs.openNpc wrapper）
服务端 8080/9000 正常 ｜ 服务端代码**本轮未修改**
```
