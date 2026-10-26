# NPC 对话 第十二轮：★ 真相大白 —— 阻塞是 `skill_ctrl.luac` 抛的异常

> 承接十一轮。本轮直接验证 `self.scene` 是否被赋值，**结果推翻了此前所有假设**。

---

## 一、决定性取数（真实部署）

```
SceneViewNew_oktrue_rtable                    ← ★ SceneView:New() **成功**，返回 table

sceneStart_before**nil**_after**table**_okfalse_e_string__game/skill/skill_ctrl.luac__:0:_attempt_to_index_a_nil_value
        ↑ me.scene 从 nil → **table**（赋值**成功**）
        ↑ 但 **抛了异常**，来自 **`skill_ctrl.luac`**

sceneStart_beforetable_aftertable_oktrue      ← 第二次调用成功
sceneStart_wrapped2 ｜ SceneViewNew_wrapped
```

---

## 二、★★★ 结论：此前十二轮的假设**大部分被推翻**

| 我此前的假设 | 本轮实测 | 判定 |
|---|---|---|
| `getScene()` 为 nil 是根因 | **`me.scene` 从 nil 变成了 **table**** | ❌ **部分推翻** |
| `sceneStart` 因缺 `scene_info` 而失败 | `SceneView:New()` **成功**，`scene` **被赋值** | ❌ **推翻** |
| `self.ctrl` 为 nil | 十一轮已实测为 **table** | ❌ 已推翻 |
| `setSceneInfo` 写 R1/读 R0 是根因 | 该错位**确实存在**，但**不是本轮阻塞点** | ⚠️ 降级 |

### ★★ 真正的阻塞（`CONFIRMED`）

**`sceneStart` 在把 `self.scene` 赋值成功**之后**，继续执行时在
**`game/skill/skill_ctrl.luac`** 里抛了 `attempt to index a nil value`。**

**⇒ 异常传播 ⇒ 调用者 `changeScene` 中断 ⇒ **场景初始化未完成** ⇒
后续 NPC 对话（`openNpc` → `getScene():getNpcByBid`）拿到不完整状态 ⇒ 失败。**

**⇒ 这是十二轮里**第一次**把阻塞点定位到一个**与场景/对话都无关的第三方模块 —— 技能控制器**。**

---

## 三、为什么这是**重大进展**

**此前所有轮次都在追 `getScene()` / `scene_info` / `ctrl` —— 全是**场景与对话自身**的字段。
而本轮的证据表明：**

```
场景对象创建成功（SceneView:New ✓）
self.scene 赋值成功（nil → table ✓）
⇒ 但 sceneStart 的**后续步骤**在 skill_ctrl.luac 崩了
```

**⇒ 阻塞点在**场景初始化的后段**，而且**不在场景模块里，在技能模块里**。**

**⇒ 这解释了"为什么场景能渲染、怪能打、任务能走，但 NPC 对话不行"** ——
因为**大部分初始化已完成**，只有**走到技能那一步**才崩，而 NPC 对话恰好依赖崩溃之后的状态。**

---

## 四、下一步（明确、可执行）

**⇒ 定位 `skill_ctrl.luac` 里那个 nil 索引：**

```bash
tools/luajit_dis.py 反汇编 assets/src/game/skill/skill_ctrl.luac
⇒ 找 sceneStart 调用链上会走到的、索引 nil 的那条指令
```

**或者更直接：在探针里包住 `sceneStart` 的调用，用 `debug.traceback` 抓到**精确行号**
（因为报错信息里行号是 `:0:` —— **LuaJIT 字节码没有行号信息**，需 traceback 或逐段包）。**

**具体做法（探针）：**
```lua
-- 逐段包 sceneStart 内部的 pcall，或用 xpcall + debug.traceback 拿调用栈
local ok, e = xpcall(function() return _s(me, ...) end, function(err)
  return tostring(err) .. '|' .. debug.traceback('', 2)
end)
```

**⇒ 拿到调用栈就能确定是 `skill_ctrl` 的哪个方法、在哪一步被调用的。**

---

## 五、诚实结论（第十二轮）

| 项 | 状态 |
|---|---|
| `SceneView:New()` | ✅ **成功** |
| `self.scene` 赋值 | ✅ **成功（nil → table）** |
| **真正的阻塞** | ✅ **`skill_ctrl.luac` 在 `sceneStart` 后续步骤里抛 `index a nil value`** |
| 我此前 3 个假设 | ❌ **均被推翻**（`getScene` 为 nil / `scene_info` 缺失 / `ctrl` 为 nil） |
| **NPC 对话** | ❌ 仍未闭环，但**目标已换**（从"场景字段"换成"技能模块的 nil 索引"） |

**⇒ 我**没有**解决 NPC 对话，但十二轮把根因**从场景/对话模块移到了技能模块** ——
这是**第一次有明确、可独立验证的新目标**。**如实记录。**

---

## 六、★ 本轮是第 7 次自我更正

**十二轮里，我被实测推翻的推断累计：**
1. 错误是 `index a nil value`（实为 `call setOpenNpc`）
2. "实例上没有 `setOpenNpc`"（`pairs` 看不到元表方法）
3. "NPC `10030` 不在场"（它在 25 个里）
4. "补 `sm.scene_info` 就能修"（补了仍失败）
5. "移动不通"（实测 53 个包，一直通）
6. "`self.ctrl` 为 nil"（实测是 table）
7. **"`getScene()` 为 nil / `scene_info` 缺失是根因"（实测 `scene` 赋值成功，真正阻塞在 `skill_ctrl`）**

**⇒ 每一处都保留在案，未删除。**

---

## 七、自查

```
lua-check OK（123168 字节）｜ 探针已部署（含 SceneView.New + sceneStart 前后取数）
服务端 8080/9000 正常 ｜ 服务端代码**本轮未修改**
```
