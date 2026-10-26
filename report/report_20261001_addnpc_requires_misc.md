# ★ `addNpc` 反汇编定论：必须 **`Config.Npc[bid]` 存在** 且 **`e.misc` 是 table**

> 时间：2026-10-01 ｜ 依据：`SceneModel:addNpc`（proto#17，bc=137）+ v60 的报错

---

## 〇、一句话结论

> ```lua
> function SceneModel:addNpc(e)
>   0-2    if e == nil then return end
>   3-6    local cfg = Config.Npc[e.bid]              -- ★ 必须存在
>   7-15   if cfg == nil then
>             print('------------npc加载出问题，不存在-------------------'); return
>          end
>  16-18   local old = self.npcList[e.id]
>  19-21   <遍历 e.misc>                              -- ★★ 这里对 e.misc 直接做 next/pairs
>  22-23   if <结果> == nil then …                    -- ★ 这个 nil 判断在**调用之后**
>  …       （继续用 cfg/e 里的 res_id / lev / career / sex / isCareer 等，配合 PathTool:getCareerRes）
> end
> ```
>
> ⇒ 两个硬性前提：
> 1. **`Config.Npc[e.bid]` 必须存在**（否则打印"npc加载出问题，不存在"并直接 return）；
> 2. ★★ **`e.misc` 必须是 table** —— 代码在**做 nil 判断之前**就已经把它传给了 `next/pairs`
>    ⇒ 这正是 v60 的报错 **`bad argument #1 to 'next' (table expected, got nil)`** 的出处
>    （我给的扁平 dict 没带 `misc`）。
>
> ⇒ **修法极小**：给每个 NPC entry 带上 **`misc = {}`**（以及同样可能必填的 `animate_res = {}` / `member = {}`）。

---

## 一、本轮证据（proto#17 反汇编节选）

```
 0-2   if e == nil then RET0 end
 3    GGET  Config
 4    TGETS ['Npc']            → Config.Npc
 5    TGETS ['bid']            → e.bid
 6    TGETV                     → Config.Npc[e.bid]
 7-15  if cfg == nil then print('------------npc加载出问题，不存在-------------------', e.bid) ; RET0 end
16-18  self.npcList[e.id]
19-21  <next/pairs>(e.misc)     ← ★★ 报错点（e.misc 为 nil 时即 "table expected, got nil"）
22-23  对上面结果的 nil 判断（在调用之后）
…     kgc 里还有：'NpcVo','initAttributeData','ObjType','res_base','getCareerWeaponRes',
        'base_weapon_res','getCareerRes','PathTool','isMon','Mon','res_id','lev','career',
        'isCareer','sex','misc','id','npcList','bid','Config'
```

---

## 二、完成 / 未完成

### 2.1 完成
1. ★★ **定位 `addNpc` 的两条硬性前提**（`Config.Npc[bid]` 存在 + `e.misc` 必须是 table），
   并**用报错原文把第二条钉死**（`next` 的 "table expected, got nil"）。
2. ★ 给出**极小修法**：entry 补 `misc = {}`（及可能同样必填的 `animate_res`/`member`）。
3. ★ 与上一轮的成果接上：`addMonster` 已证明**实体注入可行**（`monList 0→1`），本轮补齐 NPC 侧的形状即可。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | v61：按新形状注入 **19 个真值 NPC** ⇒ `npcList` 是否 0→19 | ❌ 下一轮 |
| 2 | 注入后 UI 是否出现 NPC、场景区 swipe 是否触发 `15203`/`10204` | ❌ |
| 3 | 充值档位承载命令 | **UNKNOWN** |

---

## 三、下一轮施工单（v61）

```lua
-- 严格前置（v58 的三条）+ 三处真值补齐 + sceneStart（预期 ok=true）
-- 然后注入 19 个真值 NPC（bid 10010…10175，真坐标取自 analysis/1.4.9/task/map_npc.json，scene_id=10001）
for _, e in ipairs(npcs) do
  e.misc, e.animate_res, e.member = {}, {}, {}     -- ★ 本轮反汇编得出的必填子表
  pcall(function() return m:addNpc(e) end)
end
-- 判据：① npcList 是否 0→19 ② v49 UI dump 是否出现 NPC 节点
--       ③ 在 NPC 坐标处 swipe/tap 是否触发 15203（NPC 对话）或 10204（移动）
```
> ③ 是把玩法环往前推的关键：`task_autopath_investigation.md` §二 明确"**寻路需要目标在场**"。

---

## 四、产物

| 文件 | 说明 |
|---|---|
| `analysis/scene_model.luac` | `addNpc` proto#17（本轮反汇编对象） |
| 设备 `files/dsh_v60.txt` | 上一轮：`addMonster` 成功、`addNpc` 报错原文 |
| 本报告 | ★ `addNpc` 的两条硬前提 + v61 施工单 |
