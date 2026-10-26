# v55 修复实验：**第一道坎过了**（`map_block` 补齐有效），撞上第二道坎 `scene_info` 为 nil

> 时间：2026-10-01 ｜ 依据：round 67 的根因（配置加载竞态）+ 本轮实测

---

## 〇、一句话结论

> ```
> v55_mapblock_fix
> 补字段: map_block nil -> table | map -> table          ← ★ 补齐成功，第一道坎过了
> sceneStart ok=false err=…scene_model.luac:0:
>     attempt to index field 'scene_info' (a nil value)   ← ★ 新的（第二道）崩溃点
> 结果: scene.map=false children=nil
> ```
>
> ⇒ **"补 `map_block`/`map`"这个修复方向是对的**（不再崩在 `map_block`），
> 但 `sceneStart` 立即撞上**第二道坎：`self.scene_info` 为 nil**。
> 而这个 nil **是本项目早前就记录过的客户端自身 bug**：
> **`setSceneInfo` 写 R1、读 R0 ⇒ `self.scene_info` 永为 nil**
> （历史探针一直报 `sceneInfo=…roles_nil…scene_id_nil`，与此完全一致）。

---

## 一、本轮证据

```
$ cat files/dsh_v55.txt
v55_mapblock_fix
补字段: map_block nil -> table | map -> table
sceneStart ok=false err=[string "game/scene/scene_model.luac"]:0: attempt to index field 'scene_info' (a nil value)
结果: scene.map=false children=nil

同期客户端: t=state → scene_table:_0xc4670378 role_table:_0xbf975518 recv_304
（本次窗口未见 >> 10204）
```

**读法**：
1. 补字段**生效**（`map_block: nil → table`、`map: nil → table`）；
2. 崩溃点**前移**到 `scene_info` ⇒ 说明 `map_block` 那一环**确实被修好了**；
3. `scene_info` 为 nil ⇒ 与**历史记录的客户端寄存器 bug** 吻合（`setSceneInfo` 写 R1 读 R0）。

---

## 二、★ 由此得到的下一枪（v56）

沿用同一手法**把 `scene_info` 也补齐**，再重跑 `sceneStart`：

```lua
-- v56（修复实验续）
local m = SceneModel:getInstance()
if rawget(m, 'map_block') == nil then m.map_block = Config.MapBlock end
if rawget(m, 'map') == nil then m.map = Config.Map end
if rawget(m, 'scene_info') == nil then
  -- scene_info 的字段来自服务端 10200/10201（本项目 `_role_10201`/`visible_missions` 同类来源）
  m.scene_info = { scene_id = 10001, srv_id = '1', bid = 10001,
                   roles = {}, npcs = {}, mons = {}, elems = {}, number = 0 }
end
m:sceneStart(m.scene_data or { bid = 10001, x = 1320, y = 2032, line_id = 0 })
```

**判据（沿用 4 条）**：① `ok=true` ② `scene.map ~= nil` ③ 不再 `no_scene_view_instance`
④ 出现 NPC + 场景区 swipe/tap 触发 `10204`。

> ★ 注意：`scene_info` 的**准确字段名**应以 `SC_10201`/`SC_10200` 的真实字段为准
> （`protocol/fields.json` 可查；`scene_info` 是客户端内部结构，字段名可能不同）
> ⇒ v56 里**先打印 `scene_info` 为 nil 时那个索引点用了哪个字段名**（若崩溃信息给不出，就先用
> `setSceneInfo(sceneId)` 试一次，看它自己会写入什么），**不猜字段名**。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★ **验证"补 `map_block`/`map`"有效**：崩溃点从 `map_block` **前移**到 `scene_info`。
2. ★ **定位第二道坎**：`self.scene_info == nil`，并把它与本项目**早前记录的客户端寄存器 bug**
   （`setSceneInfo` 写 R1 读 R0）**对上了**（历史探针的 `sceneInfo=…roles_nil…` 是同一现象）。
3. ★ 给出 v56 的具体做法与 4 条判据，并**明确不猜字段名**（先用 `setSceneInfo(sceneId)` 让客户端自己写）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | v56：补齐 `scene_info` 后能否建出地图 | ❌ 下一轮 |
| 2 | `scene_info` 的**准确字段结构**（客户端内部结构） | **UNKNOWN**（需 `setSceneInfo` 反汇编/自证） |
| 3 | 真机自然操作发 `10204` / 充值档位承载命令 | ❌ / **UNKNOWN** |

---

## 四、下一轮施工单

1. ★ **反汇编 `SceneModel:setSceneInfo`（proto#80，bc=21）**：
   - 看它**到底写哪个字段**（这能直接解释"写 R1 读 R0"的说法，并给出正确字段名/结构）；
   - 若它确实是"写了别的字段" ⇒ 探针直接**调用 `setSceneInfo`** 让客户端自己填，比我们手工构造更可靠。
2. ★ **v56 修复实验**：按 §二补齐后重跑 `sceneStart`，按 4 条判据验收。
3. 若 v56 后地图建起来 ⇒ **立刻测场景区 swipe → `10204`**，验证"不能点击移动"是否一并解决。

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml55_add.lua` / 设备 `files/dsh_v55.txt` | ★ 本轮证据（第一坎已过、第二坎浮现） |
| `report/report_20261001_rootcause_config_race.md` | 上一轮：配置竞态根因 |
| 本报告 | ★ 修复推进（崩溃点前移）+ v56 设计 |
