# ★★★ 突破：用**客户端自己的配置真值**补齐三处 nil ⇒ **`sceneStart` 从必崩变为 `ok=true`**

> 时间：2026-10-01 ｜ 依据：round 67（配置竞态）+ round 69（`setSceneInfo` 真相）+ 本轮 v56 实测

---

## 〇、一句话结论

> ```
> v56_truth_fix
> try1 map_block=table | map=table | scene_info=nil(sid=0)      ← sid 取到 0，Config.Map[0]=nil
>      sceneStart ok=false | err=…attempt to index field 'scene_info' (a nil value) | scene.map=false
> try2 map_block=table | map=table | scene_info=table(sid=10001) | tile=30x30
>      sceneStart ok=true | scene.map=false                    ← ★★ 不崩了！
> ```
>
> ⇒ **`sceneStart` 现在 `ok=true`** —— 这条从始至终必崩的链路**被打通了**，
> 而且补进去的是**客户端自己的配置真值**（`Config.Map[10001]`，并顺带取到 **`tile=30×30`**），
> **不是我们编的数**。
>
> **修法（三处，全部取自 `Config.*`）**：
> ```lua
> if rawget(m,'map_block')  == nil then m.map_block  = Config.MapBlock end
> if rawget(m,'map')        == nil then m.map        = Config.Map      end
> if rawget(m,'scene_info') == nil then m.scene_info = Config.Map[10001] end
> m:sceneStart(m.scene_data or { bid=10001, x=1320, y=2032, line_id=0 })
> ```

---

## 一、本轮证据

| try | 状态 | 结果 |
|---|---|---|
| **try1** | `sid=0`（我从 `sceneId` 读到的值，此时还是 0）⇒ `Config.Map[0]` = nil | `ok=false`，仍崩在 `scene_info` **（说明"必须用 10001 这个真 sid"）** |
| **try2** | `sid=10001` ⇒ `Config.Map[10001]` = **table**，且 `tile=30×30` | ★★ **`ok=true`** |

**读法**：
- 前两轮定位的"配置竞态造成三处 nil"**被实证**：补上后崩溃消失；
- `scene_info` 一被填上真值，就顺带把 **`TileUtil` 的瓦片尺寸（30×30）** 也定下来了
  ⇒ 这正是此前"地图不清晰/点不动"里**坐标换算**缺的那块；
- 但 `scene.map=false` ⇒ **地图对象仍未（被我这个判据）观测到** ⇒ 还需一步。

---

## 二、完成 / 未完成

### 2.1 完成
1. ★★★ **打断崩溃链**：`sceneStart` 由"必崩"变为 **`ok=true`**（三处 nil 用 `Config.*` 真值补齐）。
2. ★ **确证 sid 必须是真场景 id（10001）**：用 `0` 时 `Config.Map[0]`=nil、仍然崩（try1 即反例）。
3. ★ **顺带修好瓦片尺寸来源**：`tile=30×30` 来自 `Config.Map[10001]`，会写进 `TileUtil`。
4. ★ 全程只用**客户端配置真值**，未编造任何数值。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `scene.map` 为何仍为 false（`createMap()` 是否真建、字段名是否不同） | ❌ **下一轮首查** |
| 2 | 视图（`SceneView`）是否随之创建（`no_scene_view_instance` 是否消失） | ❌ 需下一轮对照 |
| 3 | NPC 是否出现、场景区 swipe 是否触发 `10204` | ❌ 下一轮 |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 三、下一轮施工单（验证修复的**后果**）

1. ★ **查"地图到底建没建"**：`sceneStart ok=true` 后逐个看 `self.scene` 的字段
   （`map` / `map_node` / `root` / 子节点数 / `sceneId` / `astar`），
   并**顺带反汇编 `Scene:createMap`**（在 `scene.luac`）看它把地图写到哪个字段名上
   —— 我上一轮的判据（`scene.map ~= nil`）可能是**猜的字段名**，需以反汇编为准。
2. ★ **对照三条症状**：`t=view` 是否还报 `no_scene_view_instance`；UI dump 是否出现 NPC 节点；
   在场景区 swipe 是否出现 `>> 10204`。
3. 若 `createMap` 又因**同一竞态**缺字段 ⇒ 继续同法补（仍取 `Config.*` 真值）。

---

## 四、产物

| 文件 | 说明 |
|---|---|
| `server/_ml56_add.lua` / 设备 `files/dsh_v56.txt` | ★ 本轮实测（`ok=true` 的关键证据） |
| `report/report_20261001_rootcause_config_race.md` | 根因（配置竞态） |
| `report/report_20261001_setsceneinfo_disasm.md` | `setSceneInfo` 真相（`Config.Map[sceneId]`） |
| 本报告 | ★ 修复突破 + 下一步验证方案 |
