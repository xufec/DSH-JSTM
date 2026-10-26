# 反汇编 `sceneStart`（proto#68，bc=173）—— **找到了建视图/建地图的全部代码**，且它**无条件执行**

> 时间：2026-10-01 ｜ 文件：`assets/src/game/scene/scene_model.luac`

---

## 〇、一句话结论

> ★ `SceneModel:sceneStart`（proto#68）就是**建视图 + 建地图**的地方，而且**中段没有任何门禁**：
>
> ```lua
> function SceneModel:sceneStart(msg)
>   self:setSceneInfo(self.sceneId)
>   if self.scene ~= nil then  goto AFTER_VIEW_LAYERS  end      -- ★ 已存在则**跳过建视图**
>       self.scene = Scene:New()                                -- ★ 建 Scene（视图对象）
>       ViewMgr:getInstance():changeSceneLayer(self.scene.root, false, self.scene_info)
>       ViewMgr:getInstance():setLayerVisible(false, Scene_LAYER_TAG / EFFECT_TAG /
>                                                    TOP_TAG / UI_TAG / BUTTOM_TAG / DEBUG_TAG)
>   ::AFTER_VIEW_LAYERS::
>   GlobalEvent:getInstance():Fire(SceneEvent.SCENE_START, self.sceneId)
>   <X>:getInstance():start()
>   RenderMgr:getInstance():getData():readInDefaultXml()        -- 读地图 XML
>   self.scene:createMap()                                     -- ★ 建地图（**无条件**）
>   local roleVo = GameData:getInstance():getRoleVo()           -- 之后按 career 分支
>   …
> end
> ```
>
> **⇒ 推论（重要）**：既然 `createMap()` 是**无条件**调用的，
> 那么"地图不清晰 / 没有 NPC / 点不动"就不该发生在 `sceneStart` **跑到之后**。
> ⇒ 最可能的解释收敛为两种，**都能用同一个探针实验区分**：
> 1. **`sceneStart` 根本没被调用**（即 `changeScene` 没被调用 ⇒ **我发的 `10200` 没被客户端处理**）；
> 2. **建视图那段被跳过**（`self.scene ~= nil` 成立，于是 `Scene:New()`/`changeSceneLayer` **都没执行**）
>    —— 注意：**这 6 个 `setLayerVisible` 也在这段里**，跳过意味着**图层可见性从未被设置**。

---

## 一、本轮证据（逐段读法）

| 指令 | 内容 | 意义 |
|---|---|---|
| 0–3 | `self:setSceneInfo(self.sceneId)` | 把当前 sceneId 落进 scene_info |
| **4–6** | `if self.scene ~= nil then JMP` | ★ **已存在就跳过建视图**（含 6 个 `setLayerVisible`） |
| 7–10 | `self.scene = Scene:New()` | ★ **视图对象在此创建**（若 `Scene` 类不可用会抛错） |
| 11–21 | `ViewMgr:getInstance():changeSceneLayer(self.scene.root, false, self.scene_info)` | 把场景层挂到 ViewMgr |
| 22–81 | 6× `setLayerVisible(false, {Scene,EFFECT,TOP,UI,BUTTOM,DEBUG}_TAG)` | 图层可见性 |
| 82–91 | `GlobalEvent:Fire(SceneEvent.SCENE_START, self.sceneId)` | 广播"场景开始" |
| 92–98 | `<某管理器>:getInstance():start()` | 启动 |
| **99–108** | `RenderMgr:getInstance():getData():readInDefaultXml()` | **读地图 XML** |
| **109–112** | **`self.scene:createMap()`** | ★ **建地图（无条件）** |
| 113–123+ | `GameData:getInstance():getRoleVo()` + `career` 分支 | 与角色职业相关的后续 |

> 与既往探针观测的呼应：探针一直报 **`view=no_scene_view_instance`**；
> 而这里 `self.scene`（模型里的场景对象）**是 table**（探针 `getScene()` 返回 table）。
> ⇒ 说明 **`self.scene` 存在** ⇒ 上表第 4–6 行的 **"跳过"分支很可能一直成立**，
> 于是 **`Scene:New()` 与 `changeSceneLayer`/`setLayerVisible` 从未执行** ⇒ 视图层从未建立。

---

## 二、完成 / 未完成

### 2.1 完成
1. ★★ **定位建视图/建地图的全部代码**（`sceneStart` proto#68）：`Scene:New()` + `changeSceneLayer`
   + 6×`setLayerVisible`（在 `self.scene==nil` 分支内）+ **无条件** `readInDefaultXml()` / `createMap()`。
2. ★ **给出两种可区分的解释**（`sceneStart` 未被调用 / 建视图分支被跳过），并指出**后者与既往
   `view=no_scene_view_instance` + 探针 `getScene()` 是 table 的观测相互吻合**。
3. ★ 明确下一步的**一个实验即可分辨**（探针挂钩 `changeScene` / `sceneStart`）。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `sceneStart` 是否被调用 / 是否走了"跳过建视图"分支 | ❌ 下一轮探针（v52） |
| 2 | `Scene` 类是否可用（若不可用会在 `Scene:New()` 抛错并**静默中断**） | **UNKNOWN**（静态可查 `Scene` 全局） |
| 3 | 真机自然操作发 `10204` / 充值档位承载命令 | ❌ / **UNKNOWN** |

---

## 三、下一轮施工单

1. ★ **探针 v52（决定性）**：挂钩 `SceneModel.changeScene`、`SceneModel.sceneStart`，
   上报 ① 是否被调用 ② `self.scene` 在入口时为 nil 还是 table ③ 入参 `bid/line_id/x/y`
   ④ `Scene` 全局是否为 table（能否 `Scene:New()`）。
   - 若 `sceneStart` **被调用**且 `self.scene` **已是 table** ⇒ 命中"跳过建视图"分支 ⇒
     去查**为什么 `self.scene` 会是非 nil**（谁先赋的值）——这可能是**我重复推送 `10200`** 造成的：
     客户端在**首次**（正确）进场景前，可能已被我另一条 `10200` **提前**置了 `self.scene`。
   - 若 `sceneStart` **没被调用** ⇒ 回头查 `10200` 的到达/解析（形状、时机、`code`）。
2. ★ 同时验证 `Scene` 全局可用性（若 nil ⇒ `Scene:New()` 抛错，`sceneStart` 静默中断）。

---

## 四、产物

| 文件 | 说明 |
|---|---|
| `analysis/scene_model.luac` | 本轮反汇编对象（`sceneStart` = proto#68） |
| 本报告 | ★ 建视图/建地图的完整代码 + 两种可区分解释 + v52 设计 |
| 设备 `files/dsh_v50.txt`、`files/dsh_v51.txt` | `isLoadState=true` / `move()` 发包（对照） |
