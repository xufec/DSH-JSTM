# ★ `setSceneInfo` 反汇编定论：`self.scene_info = Config.Map[sceneId]` —— 仍是**同一个配置竞态**

> 时间：2026-10-01 ｜ 依据：`SceneModel:setSceneInfo`（proto#80，bc=21）反汇编 + v55 崩溃证据

---

## 〇、一句话结论

> ```lua
> function SceneModel:setSceneInfo(sceneId)
>   0-3   self.scene_info = Config.Map[sceneId]          -- ★★ 就是这一行（TGETV：按变量键取值）
>   4-19  if TileUtil.tileWidth  == nil then TileUtil.tileWidth  = self.scene_info.tile_w end
>         if TileUtil.tileHeight == nil then TileUtil.tileHeight = self.scene_info.tile_h end
> end
> ```
>
> ⇒ **`self.scene_info` 就是 `Config.Map[sceneId]`**，**不是**什么复杂结构 ⇒
> v55 里 `scene_info == nil` 的原因是 **`Config.Map[sceneId]` 当时取到 nil**
> （`Config.Map` 那时还没加载好，或该场景 id 的表项未就绪）——
> **与 round 67 查明的"配置加载竞态"是同一个根因**，只是发生在第二处。
>
> ⇒ **修法精确且不需猜**：等配置加载完后，**用真值补上**
> ```lua
> m.scene_info = Config.Map[m.sceneId]      -- 或 Config.Map[10001]
> ```
> **不要手工造结构**（我上一轮的计划可以作废）。
>
> 附带一条重要发现：`scene_info` 还提供 **`tile_w` / `tile_h`**（首次会被写进 `TileUtil.tileWidth/Height`）
> ⇒ 若 `scene_info` 为 nil，**瓦片尺寸也定不下来** ⇒ 地图/pathfinding 的坐标换算同样受影响
> （这与"地图不清晰 + 点不动"的现象一致）。

---

## 一、本轮证据（反汇编）

```
=== scene_model.luac proto #80（setSceneInfo，bc=21）===
  strings: 'tile_h', 'tileHeight', 'tile_w', 'tileWidth', 'TileUtil', 'Map', 'Config', 'scene_info'
   0  GGET   A=2 D=1     ; Config
   1  TGETS  A=2 B=2 C=2 ; ['Map']         → Config.Map
   2  TGETV  A=2 D=513   ; ★ 按变量键取值 → Config.Map[sceneId]
   3  TSETS  A=2 B=0 C=0 ; self.scene_info = 上面那个
   4-11  if TileUtil.tileWidth == nil then TileUtil.tileWidth = self.scene_info.tile_w end
  12-19  if TileUtil.tileHeight == nil then TileUtil.tileHeight = self.scene_info.tile_h end
```

**读法**：`Config.Map[sceneId]` **取不到只会把 `scene_info` 静默置 nil**（不会报错），
于是后面任何 `self.scene_info.xxx` 才崩 —— **这正好解释了 v55 的报错形态**。

---

## 二、完成 / 未完成

### 2.1 完成
1. ★★ **`setSceneInfo` 的真相**：`self.scene_info = Config.Map[sceneId]`（一行），并连带设置 `TileUtil` 的瓦片尺寸。
2. ★ **把第二道坎归因到同一根因**：`Config.Map[sceneId]` 当时为 nil ⇒ 仍是**配置加载竞态**。
3. ★ **修正上轮的修法**：不再手工构造 `scene_info`，而是 **`m.scene_info = Config.Map[m.sceneId]`**（真值）。
4. ★ 发现 `scene_info` 还承载 **瓦片尺寸**（`tile_w/tile_h`）⇒ 其缺失会同时影响地图坐标换算。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | v56：用真值补 `scene_info` 后能否建出地图 | ❌ 下一轮 |
| 2 | 是否还有第三道/更多同源字段 | **UNKNOWN**（v56 会继续暴露） |
| 3 | 真机自然操作发 `10204` / 充值档位承载命令 | ❌ / **UNKNOWN** |

---

## 三、下一轮施工单（v56，精确版）

```lua
-- v56：把"配置竞态造成的一份 null"按真值补齐，再重跑 sceneStart
local m = SceneModel:getInstance()
if rawget(m, 'map_block') == nil then m.map_block = Config.MapBlock end
if rawget(m, 'map')       == nil then m.map       = Config.Map     end
if rawget(m, 'scene_info')== nil then m.scene_info = Config.Map[m.sceneId or 10001] end
m:sceneStart(m.scene_data or { bid = 10001, x = 1320, y = 2032, line_id = 0 })
```
**验收判据（4 条，不变）**：① `ok=true` ② `scene.map ~= nil` ③ 不再 `no_scene_view_instance`
④ 界面出现 NPC 且**场景区 swipe/tap 能触发 `10204`**。

> 若再撞第三个 nil（预期可能：`Map`/`MapBlock` 相关的其它缓存、`astar` 的块数据）⇒
> **同一手法继续补**（都从 `Config.*` 取真值），一轮一个，直到 `ok=true`。
> 这条路线之所以可信：**每一处补的都是客户端自己的配置真值，不是我们编的数**。

---

## 四、产物

| 文件 | 说明 |
|---|---|
| `analysis/scene_model.luac` | 反汇编依据（`setSceneInfo` proto#80） |
| 设备 `files/dsh_v55.txt` | 上一轮：`map_block` 已补、崩在 `scene_info` |
| 本报告 | ★ `setSceneInfo` 真相 + v56 精确修法 |
