# ★ v52 决定性结果：`10200` **确实被处理**；建视图分支**应当**执行；但探针看到 **`Scene` 类 = nil**

> 时间：2026-10-01 ｜ 探针 v52 挂钩 `SceneModel.changeScene` / `sceneStart`（依据 round 63 的反汇编）

---

## 〇、一句话结论

> 1. ★ **`10200` 到达并被正确处理**：`changeScene` / `sceneStart` **被反复调用**，
>    入参完全正确：**`bid=10001  line_id=0  x=1320  y=2032`**
>    ⇒ **"我发的 10200 没被客户端处理"这条假设被否证**（此前一直无法确定）。
> 2. ★ **第一次调用时 `self.scene = nil`** ⇒ 按反汇编，**"跳过建视图"那条分支当时不该命中**
>    ⇒ `Scene:New()` 与 `changeSceneLayer`/`setLayerVisible` **本应执行**。
> 3. ★★ **但探针读到 `Scene` 类 = `nil`**（`_G.Scene` 每次采样与调用时都是 nil）：
>    若 `scene_model.luac` 看的是**同一张全局表**，那么 `self.scene = Scene:New()`
>    必然**抛错**（index nil）⇒ `sceneStart` **静默中断在建视图处**
>    ⇒ 后面的 `changeSceneLayer` / 6×`setLayerVisible` / `readInDefaultXml` / **`createMap()`** **全部没执行**
>    ⇒ **地图没建、NPC 没渲染、场景层没有触摸处理器** ⇒ **三条症状一次性全解释**。
>    ⚠️ **但这条还需排除一个替代解释**：某些热更方案会给**每个模块私有 env**，
>    那样"我的探针看到 `_G.Scene` 为 nil"就**不代表** `scene_model` 看到 nil ⇒ 标 **待验证**。

---

## 一、本轮原始证据（`files/dsh_v52.txt`）

```
v52_scenestart_probe
installed ok=true
-- tick 10 SceneModel.scene=nil Scene类=nil
-- tick 20 SceneModel.scene=nil Scene类=nil
changeScene 入口 scene=nil    Scene类=nil  bid=10001 line_id=0 x=1320 y=2032   ← ★ 首次：scene=nil
sceneStart 入口 scene=nil （nil ⇒ 会 Scene:New()；table ⇒ 跳过建视图）
changeScene 入口 scene=table  Scene类=nil  bid=10001 line_id=0 x=1320 y=2032
sceneStart 入口 scene=table （…跳过建视图）
-- tick 30 SceneModel.scene=table Scene类=nil
…（其后每 10 秒都有若干次 changeScene/sceneStart，全部 bid=10001 / x=1320 / y=2032）…
-- tick 60 SceneModel.scene=table Scene类=nil
```

**读法**：
- `bid/line_id/x/y` 与我服务端 `push_10200` 发的值**一致** ⇒ 链路无问题；
- 首次 `scene=nil` ⇒ **不是"跳过"分支**；
- **`Scene类=nil` 贯穿全程** ⇒ 高度可疑（`Scene:New()` 会失败）。

---

## 二、这次同时**否证/收窄**了三条旧判断

| 旧判断 | 现状 |
|---|---|
| "我发的 `10200` 可能没到/没被处理" | ❌ **否证**：`changeScene`/`sceneStart` 被反复调用，入参正确 |
| "`changeScene` 因缺字段提前 return"（round 62 已否证） | ✅ 保持否证 |
| "`self.scene ~= nil` 导致跳过建视图"（round 63 的候选 2） | ❌ **首次调用时 scene=nil** ⇒ 该分支当时不成立 |
| **新候选（本轮）**：`Scene:New()` 因 `Scene` 为 nil 而**抛错**，`sceneStart` **静默中断** | ⚠️ **高度可疑**，待排除"模块私有 env" |

---

## 三、完成 / 未完成

### 3.1 完成
1. ★★ **确认 `10200` 被正确处理**（挂钩实测，入参逐字段核对）。
2. ★ 确认**首次 `sceneStart` 时 `self.scene = nil`** ⇒ 不是"跳过建视图"。
3. ★★ **发现 `Scene` 类在探针视角恒为 nil** ⇒ 提出"`Scene:New()` 抛错 ⇒ `sceneStart` 静默中断 ⇒ 地图/NPC/触摸全没建"的**统一解释**。
4. ★ 明确该解释的**唯一替代解释**（模块私有 env）与**验证办法**（下一轮）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `Scene` 类到底是否为 nil（排除模块私有 env） | ❌ 下一轮（决定性） |
| 2 | `self.scene` 是否有 map/root/子节点（若空 ⇒ 地图确实没建） | ❌ 下一轮同批测 |
| 3 | 真机自然操作发 `10204` / 充值档位承载命令 | ❌ / **UNKNOWN** |

---

## 四、下一轮施工单（一次实验定论）

探针 v53，三件事一起测：
1. **`Scene` 的真身**：遍历 `_G`、`package.loaded`、以及 `scene_model` 模块的 env，
   找名字含 `Scene` 的表；并打印 `SceneModel` 自身 metatable 的 `__index` 里是否含 `Scene`。
   ⇒ 若**只有探针看不到** ⇒ 是**模块私有 env**，则 `Scene:New()` 正常，"统一解释"作废；
   若**到处都 nil** ⇒ `Scene:New()` 必错 ⇒ **根因确定**（接下来找"`Scene` 为何没注册"）。
2. **`self.scene` 的实际内容**：打印 `scene.map`、`scene.root`、`scene:getChildren()` 数量
   ⇒ 判断**地图到底建没建**（空 scene ⇒ 没建）。
3. **pcall 包住 `sceneStart` 调用**：直接调一次 `SceneModel:getInstance():sceneStart(msg)` 并打印
   **错误信息 + traceback** ⇒ 若真抛错，一步定位到**具体哪一行/哪个 nil**。

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml52_add.lua` | ★ v52 探针（挂钩 changeScene/sceneStart + Scene 类采样） |
| 设备 `files/dsh_v52.txt` | ★ 本轮原始证据 |
| `analysis/scene_model.luac` | 反汇编依据（`sceneStart` proto#68） |
| `report/report_20261001_disasm_scenestart.md` | 上一轮：建视图/建地图的代码位置 |
