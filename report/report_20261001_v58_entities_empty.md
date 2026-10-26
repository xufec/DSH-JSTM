# v58（严格前置条件下）：`sceneStart ok=true` **复现成功**；`npcList/monList/elementList` **全为 0** ⇒ "没有NPC"的直接原因

> 时间：2026-10-01 ｜ 前置：round 67 配置竞态根因 + round 70 v56 的首次成功 + round 71 的方法教训

---

## 〇、一句话结论

> ```
> v58_strict_fix
> map_block=table | map=table | scene_info=table | sceneStartOk=true | scene=table
> | npcList=0 | monList=0 | elementList=0 | moveOk=nil
> ```
>
> ① ★★ **`sceneStart ok=true` 在严格前置条件下复现**（`Config.Map[10001]` 已就绪 + 已进场景 + 控制器有 model）
> ⇒ round 70 的成功**不是侥幸**，"补三处真值"这条修法**可重复**。
> ② ★★ **`npcList=0 / monList=0 / elementList=0`** ⇒ **模型里一个实体都没有**
> —— 这就是"**没有NPC**"的**直接原因**，且它在**模型层**（不是渲染层）：
> 我的服务端 `10201` 明明推了 **19 NPC + 1 怪**，但客户端的这些列表是空的。
> ③ `moveOk=nil` ⇒ `SceneController:move()` 返回 nil（仍被某处挡住；待查）。

---

## 一、本轮证据与读法

| 观测 | 值 | 读法 |
|---|---|---|
| `map_block` / `map` / `scene_info` | 均 **table** | 三处真值补齐**生效**（取自 `Config.*`） |
| `sceneStartOk` | **true** | ★ 崩溃链已断（与此前"必崩"形成对照） |
| `scene` | table | 场景对象已建 |
| **`npcList` / `monList` / `elementList`** | **0 / 0 / 0** | ★★ **模型里没有任何 NPC/怪/元素** |
| `moveOk` | nil | `move()` 未成功返回（门禁/内部 return，待查） |

**因果推断**：实体是在 `SceneController.on10201` 里由 `addNpc` / `addMonster` 等**填进这些列表**的
（`scene_model.luac` 里有 `addNpc`(proto#17) / `addMonster`(proto#25)，strings 里也有 `npcList`/`monList`/`elementList`）。
⇒ **`on10201` 很可能在"场景尚未建好/配置尚未就绪"时就跑过了**（**同一个竞态**），
于是那些 `add*` **没能填进去**（或填进了当时还不存在的对象）。

---

## 二、★ 由此得到的下一枪（很具体、可执行）

**在场景建好之后，用真值重新驱动一次客户端的实体添加**：

```lua
-- v59 计划
-- ① 用服务端 10201 的**原样载荷**重调客户端的处理器（最忠实）
local ctrl = SceneController:getInstance()
pcall(function() ctrl:on10201(saved_10201_msg) end)
-- ② 若拿不到原载荷 ⇒ 退一步：按真值直接调 addNpc / addMonster
--    （NPC/怪的 bid、坐标都来自我们已核对的真值：19 NPC + 1 怪）
for _, e in ipairs(real_npcs) do pcall(function() m:addNpc(e) end) end
for _, e in ipairs(real_mons) do pcall(function() m:addMonster(e) end) end
-- ③ 判据：npcList/monList 是否从 0 变为 19/1；UI dump 是否出现 NPC 节点；场景区 swipe 是否触发 10204
```

> 与既往文档的呼应：`task_autopath_investigation.md` §二 明确"**寻路需要目标在场**"，
> 而"在场"在这里落地为 **`npcList/monList` 非空** ⇒ 这一枪同时服务"没有NPC"与"点不动"。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★★ **严格条件下复现 `sceneStart ok=true`**（修法可重复，非侥幸）。
2. ★★ **定位"没有NPC"的直接原因**：模型层 `npcList/monList/elementList` **全为 0**（服务端其实推了 19+1）。
3. ★ 指出最可能的机制：**`on10201` 的实体添加跑在"场景/配置未就绪"时**（同一个竞态的另一处表现）。
4. ★ 给出**具体可执行的下一枪**（真值重驱动 `on10201` / `addNpc` / `addMonster`）与判据。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | v59：重驱动后 `npcList/monList` 是否非空、NPC 是否出现 | ❌ 下一轮 |
| 2 | `move()` 返回 nil 的原因（哪道门禁） | **UNKNOWN** |
| 3 | 地图字段名（`scene.map` 是否就是地图对象） | **UNKNOWN**（本轮未 dump 到） |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 四、下一轮施工单

1. ★ **v59**：按 §二 重驱动实体添加（优先用**原样 10201 载荷**调 `ctrl:on10201`），
   看 `npcList/monList` 是否变非空；随后测场景区 swipe → `10204`。
2. ★ 同时打印 `move()` 的返回与**门禁值**（`isLoadState` / `getIsOnFight` / `isOnTeamFollow`）。
3. 若 NPC 出现 ⇒ 立即用 v49 的 UI dump 找 NPC 节点坐标，**点 NPC 触发 `15203`**（任务对话），把玩法环往前推。

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml58_add.lua` / 设备 `files/dsh_v58.txt` | ★ 本轮关键证据（ok=true + 三个列表为 0） |
| `report/report_20261001_v56_scenestart_ok.md` | v56 首次成功 |
| `analysis/scene_model.luac` | `addNpc`(proto#17) / `addMonster`(proto#25) 所在文件 |
