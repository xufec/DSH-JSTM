# v57：结果**不可比**（本轮客户端处于"未进场景"状态）—— 诚实标注 + 一条方法教训 + 一个新 nil

> 时间：2026-10-01 ｜ 上一轮：v56 已让 `sceneStart ok=true`（三处真值补齐）

---

## 〇、一句话结论

> v57 跑出来的是 **`sceneStart ok=false`（又崩在 `scene_info`）**，但**本轮结果不可比、不能当作 v56 的反例**：
>
> ```
> v57_scene_fields
> sceneStart ok=false err=…attempt to index field 'scene_info' (a nil value)
> scene 类型=nil                              ← ★ 本轮根本没有 scene 对象
> TileUtil tile_w=30 tile_h=30                ← 瓦片尺寸**是**有的（说明 Config.Map 存在）
> model.astar=table ; model.elementList=table
> move() ok=false err=…scene_controller.luac:0: attempt to index field 'model' (a nil value)   ← ★ 新 nil
> ```
>
> 三个信号说明**本轮客户端处于"未进场景"状态**（与 v56 那次不同）：
> ① `self.scene` **为 nil**（v56 时是 table）② **`SceneController.model` 为 nil**（控制器还没拿到模型）
> ③ 因而我在这个状态下调用 `sceneStart`，`Config.Map[10001]` 当时**仍不可用**（配置竞态尚未走完）。
>
> ⇒ **诚实结论**：v57 **没有**推翻 v56（v56 的 `ok=true` 是在"客户端已进场景、配置已加载完"的条件下取得的）；
> 本轮暴露的是**我的判据/触发条件不够严**（见 §二 的方法教训）。

---

## 一、本轮证据与读法

| 观测 | 读法 |
|---|---|
| `scene=nil` | 客户端**尚未**走到建场景那一步（或在别的画面）⇒ 此时补字段没有意义 |
| `move() err=…index field 'model' (a nil value)` | ★ **新 nil**：`SceneController.model` 为 nil ⇒ **同族问题**（`__init` 竞态）在**控制器**上也存在 |
| `TileUtil tile_w/h = 30/30` | `Config.Map` **是存在的**（瓦片尺寸已定）⇒ 说明"配置已经加载" |
| `model.astar=table` / `elementList=table` | 模型侧对象已在（与此前一致） |

---

## 二、★ 方法教训（本轮主要产出）

| # | 我上一版的问题 | 改进 |
|---|---|---|
| 1 | 我只检查 `type(cfg.Map)=='table'`，**没检查 `cfg.Map[10001] ~= nil`** | 补上该检查（否则 `scene_info` 仍会是 nil） |
| 2 | 我没检查**客户端是否已进场景**（`m.scene ~= nil` / `SceneController.model ~= nil`）就动手 | 加前置条件：**只在"已进场景"状态**下施补并重跑 |
| 3 | 我把"补字段"当成纯机械动作，忽略了**时机** | 记录并对照：v56 成功那次是**客户端 changeScene 已被调用多次之后** |

> 这说明：**同一条修法在不同状态下结果不同** ⇒ 必须在**同一状态**下比较（本会话反复出现的"比对基线"纪律）。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★ **如实标注 v57 结果不可比**（客户端未进场景：`scene=nil`、`controller.model=nil`），**不当作反例**。
2. ★ **发现同族新 nil**：**`SceneController.model` 也为 nil** ⇒ `__init` 竞态在控制器上同样存在（新的待补/待查项）。
3. ★ 记录**方法教训三条**（判据要查 `cfg.Map[sid]`、要等"已进场景"、要同状态比对）。
4. ★ 确认 `TileUtil` 的瓦片尺寸（30×30）**已定** ⇒ `Config.Map` 本身是加载到了的。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 在"已进场景"状态下复跑 v57（dump `scene` 字段，找地图落在哪个字段） | ❌ 下一轮 |
| 2 | `SceneController.model` 为何为 nil（同族竞态的影响面） | **UNKNOWN** |
| 3 | NPC 是否出现 / 场景区 swipe 是否触发 `10204` | ❌ 下一轮 |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 四、下一轮施工单（严格化后的 v58）

```lua
-- 前置条件（全满足才动手）
if cfg.Map[10001] == nil then return end              -- ★ 配置真的就绪
if rawget(m, 'scene') == nil then return end          -- ★ 客户端已进场景
if SceneController:getInstance().model == nil then return end

-- 补齐 + 重跑（同 v56）
... m.map_block/map/scene_info ...
m:sceneStart(m.scene_data or {bid=10001,x=1320,y=2032,line_id=0})
-- 成功则 dump scene 全部字段（找出地图字段名）+ 检查 view / NPC / swipe→10204
```

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml57_add.lua` / 设备 `files/dsh_v57.txt` | ★ 本轮证据（不可比的状态 + 新 nil） |
| `report/report_20261001_v56_scenestart_ok.md` | 上一轮：`ok=true` 的突破（仍成立，但条件已明确） |
| 本报告 | ★ 诚实标注 + 方法教训 + 下一轮严格化方案 |
