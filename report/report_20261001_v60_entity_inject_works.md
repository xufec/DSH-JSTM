# ★★★ v60：**实体注入成功** —— `addMonster` 让 `monList 0 → 1`；`addNpc` 报错给出确切入参线索

> 时间：2026-10-01 ｜ 目标：绕开"`on10201` 零调用"，用真值直接把实体塞进客户端模型

---

## 〇、一句话结论

> ```
> v60_direct_entities
> sceneStart ok=true | 前 npcList=0 monList=0                      ← 修复第 4 次复现
> addNpc  ok=false err=…:0: bad argument #1 to 'next' (table expected, got nil)
> 加 NPC 后 npcList=0
> addMonster ok=true err=nil                                        ← ★★ 成功！
> 加怪后 monList=1                                                  ← ★★ 0 → 1
> ```
>
> ① ★★ **`addMonster` 调用成功，`monList` 从 0 变成 1**
> ⇒ **这是本会话第一次把实体真正塞进客户端模型**（此前一直是 0）⇒ **"实体进模型"这条链路是通的、可行的**。
> ② `addNpc` 失败，但**报错信息极其有用**：
> `bad argument #1 to 'next' (table expected, got nil)`
> ⇒ 它内部对某个字段做了 `next(...)`，而**我给的扁平 dict 里那个字段是 nil** ——
> 即 `addNpc` 期望的入参**含一个必填的子表**（很可能是 `misc` / `animate_res` / `member` 之一，
> 与 `SCMapGird_10201.npcs` 的 item 字段（`id,bid,type,x,y,name,misc,animate_res,member`）对得上）。
> ⇒ **下一轮按反汇编 `SceneModel:addNpc`（proto#17，bc=137）确认形状即可修好**。
> ③ `sceneStart ok=true` **第 4 次复现**（v56/v58/v59/v60）⇒ 前面那条修法完全稳定。

---

## 一、本轮证据与意义

| 观测 | 值 | 意义 |
|---|---|---|
| `sceneStart` | ok=true（**第 4 次**） | 三处真值补齐稳定有效 |
| `addNpc` | **false** + `bad argument #1 to 'next' (table expected, got nil)` | ★ **形状线索**：缺一个必填子表 |
| `addMonster` | **true** | ★★ **实体注入可行** |
| `npcList` / `monList` | 0 → 0 / **0 → 1** | ★★ `monList` 真的被填了 |

**读法（重要）**：此前 `npcList/monList` 全为 0 时，我只能推断"实体没进模型"；
**本轮证明"进模型"是可行的**（怪已进去）⇒ 剩下的只是**把 NPC 的入参形状喂对**。

---

## 二、完成 / 未完成

### 2.1 完成
1. ★★★ **实体注入成功**：`addMonster` → `monList 0 → 1`（客户端模型第一次有实体）。
2. ★★ **拿到 `addNpc` 的确切报错**：`bad argument #1 to 'next' (table expected, got nil)`
   ⇒ 定位到"缺一个必填子表"，与 `SCMapGird_10201.npcs` 的 item 字段集合对照后**范围很小**。
3. ★ **`sceneStart ok=true` 第 4 次复现**（修法稳定）。
4. ★ 明确了"让客户端有实体"这条**可执行路线**（真值 + 正确形状），且**未编造任何数据**（怪用真名"戴浩"/真 res_id"H32000"）。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `addNpc` 的**正确入参形状** | ❌ 下一轮（反汇编 proto#17 即可） |
| 2 | **19 个 NPC 全部注入**后，UI 是否出现 NPC 节点 | ❌ |
| 3 | 实体在场后，场景区 swipe 是否触发 `10204`（"点不动"是否解决） | ❌ |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 三、下一轮施工单（很具体）

1. ★ **反汇编 `SceneModel:addNpc`（proto#17，bc=137）**：看它开头对哪个字段做 `next(...)`
   ⇒ 直接得出必填子表名（`misc` / `animate_res` / `member`？），按形状补上。
2. ★ **v61**：用**正确形状**注入 **19 个真值 NPC**（bid 10010…10175、真坐标取自 `map_npc.json`）
   + 已成功的怪；判据：
   - `npcList` 是否 0 → 19；
   - v49 UI dump 是否出现 NPC 节点（带名字/坐标）；
   - **在 NPC 坐标处 swipe/tap 是否触发 `15203`（NPC 对话）或 `10204`（移动）** ——
     这是把玩法环往前推的关键一步（`task_autopath_investigation.md` §二：寻路需要目标在场）。
3. 若 NPC 注入成功但界面仍不显示 ⇒ 查 `SceneView` 侧的渲染刷新（可能需要 `updateNpc`/刷新调用）。

---

## 四、产物

| 文件 | 说明 |
|---|---|
| `server/_ml60_add.lua` / 设备 `files/dsh_v60.txt` | ★ 本轮关键证据（`addMonster` 成功、`addNpc` 报错） |
| `analysis/scene_model.luac` | `addNpc` = proto#17 / `addMonster` = proto#25 |
| `report/report_20261001_v59_on10201_never_called.md` | 上一轮：`on10201` 零调用 |
