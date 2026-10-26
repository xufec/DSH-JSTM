# Phase 5 完善记录（5C 突破 + 任务系统补强）

> 本轮目标：「完善任务系统」。
> **本轮三条实质进展**：
> ① 走通了**原版点击链路**并定位到事件监听者；
> ② 发现并**按协议修正了 NPC 的 `type` 字段**（0→2）；
> ③ 补上了**奖励的界面级验证**（面板显示金币 1888 / 经验 150）。

---

## 零、★★★ 新证据：奖励在角色面板上可见（5I 的界面级确认）

跑测时打开了角色面板（背包页），视觉逐字判读：

```
玄武 LV.7
金币 1,888            ← ★ 正是任务奖励发的 888（+ 初始 1000）
经验 150/100          ← ★ 正是任务奖励发的 150
综合战力：0
无报错、无 nil、无乱码
```

**⇒ 任务奖励（5I）此前只有**日志级**证据（`+150 exp, +888 gold`），
现在补上了**界面级**证据 —— 奖励确实进了角色数据并在面板上显示。**

---

## 零之二、★★★ `ObjType` 找到，NPC 的 `type` 字段**按协议修正**

从 `game/scene/element/type_state.luac` 读出：

```lua
ObjType = {
  NORMAL = 0, PLAYER = 1, NPC = 2, MONSTER = 3, DOOR = 4,
  COLLECT_1 = 5, COLLECT_2 = 51, QIXI_ELEM = 6, BEAST = 6, CONVOY = 7,
  ELE_Effect = 100, ELE_HANDLE_Effect = 101
}
```

**⇒ 我们下发的 25 个 NPC 原本全是 `type=0`（NORMAL），而**NPC 本应是 `2`**。**

**已修正：`config.json` 的 25 条 NPC 全部 `type=2`。**

| 项 | 修正前 | 修正后 |
|---|---|---|
| NPC `type` | **0（NORMAL）** | **2（NPC）** |

**⇒ 这是一处**有协议依据的修正**（不是猜）。
但实测：修正后点击链路的报错**没有变化**（仍是 `scene_model.luac: attempt to index a nil value`）
⇒ **nil 不是来自 type 判断**（handler 里只对 `ELE_Effect=100` 提前 return），
**而是来自 handler 的后段**。

---

## 一、★ 5C 的**真正卡点**：找到了 `SCENE_NPC_CLICK` 的监听者

### 1.1 链路全貌（全部有反汇编依据）

```
Npc:clickHandler()                              -- npc.luac proto[5]
   └─ GlobalEvent:Fire(SceneEvent.SCENE_NPC_CLICK, self.vo)
        └─ scene_model 的 child proto[5]        -- ★ 监听者就在这
             ├─ if not vo then return end                        (@0-2)
             ├─ if self:isOnTeamFollow() then return end         (@3-9)
             ├─ if SceneModel:getInstance():getIsOnXM() then return end (@10-19)
             ├─ if vo.type == ObjType.ELE_Effect then return end (@20-25)
             └─ …（寻路 / 打开对话）
```

**⇒ `SCENE_NPC_CLICK` 的监听者 = `game/scene/scene_model.luac` 的 child proto[5]（params=1，收 vo）。**
**⇒ 报错 `scene_model.luac: attempt to index a nil value` 正是发生在这个 handler 里 —— 位置吻合。**

### 1.2 事件绑定方式

```lua
-- scene_model proto[15]（事件绑定）@30-44
if self.npc_click_event == nil then
   self.npc_click_event = GlobalEvent:getInstance():Bind(
                             SceneEvent.SCENE_NPC_CLICK, <child proto[5]>)
end
```

**⇒ 是 `GlobalEvent:Bind(事件, 闭包)` 的注册方式**（不是 `addTouchEventListener`）。

---

## 一、★ 5C 的**真正卡点**找到了：`openNpc(x)` 的 `x` 是 **bid 数字**，不是 VO 表

反汇编 `game/npc/npc_dialogs.luac proto[8] = openNpc`：

```lua
function NpcDialogs:openNpc(x)
  self.ctrl:setOpenNpc(x)
  self.npc_cfg = Config.Npc[ x ]                                     -- ★ x 当 bid 用！
  self.npc_vo  = SceneModel:getInstance():getScene():getNpcByBid(x).vo
  if self.npc_vo then
     for k, v in pairs(self.npc_vo.misc) do ... end
  end
  ...
end
```

**⇒ 之前几轮我一直传 **VO 表** ⇒ `Config.Npc[表]` = `nil` ⇒ `npc_cfg` 为 nil
⇒ 报 `npc_dialogs.luac: attempt to index a nil value`。**

**⇒ 这解释了 5B/5C 反复失败的原因 —— 不是"UI 不可用"，而是"我传错了参数类型"。**

### 修正后的实测

```lua
local c = NpcCtrl:getInstance()
if c.view == nil then c.view = NpcDialogs:New() end
c.view:openNpc(10030)           -- 10030 = 周漪（Config.Mission[10010].commit_npc_id）
```

```
t=dlgOpen&v=tries_25_openNpc_10030__ok_true_err_nil      ← ★ 调用成功、无报错！
```

**⇒ 从"必然报错"变成"成功调用"（`ok=true`）。**

### 但界面**仍未**出现对话面板（如实说明）

视觉判读：仍是主城界面，**没有**对话框。
不过**确实看到了关键信息**：

```
画面中央：玩家「DSH」与 NPC「周漪」（红发）
周漪上方有蓝色悬浮标签「学院任务」          ← ★ 与任务 10010 的 commit_npc_id=10030 对应
无报错、无 nil、无乱码
```

**⇒ `openNpc(10030)` 执行成功但未渲染 UI**，说明还缺前置。已查到的候选：

| 候选前置 | 依据 | 实测结果 |
|---|---|---|
| 先 `openDefault()` / `createRootWnd()` 建根节点 | `NpcDialogs` 有这两个方法 | ❌ **反而更糟**：先调 `openDefault()` 后，`openNpc` 报 `attempt to index field 'npc_cfg' (a nil value)` ⇒ **它会把 `npc_cfg` 清掉**，**必须单独调 `openNpc`** |
| 需要在"真实点击"的上下文里 | `npc_ctrl proto[26]` 的调用链 | 未验证 |

**⇒ 已回退到"单独调 `openNpc(10030)`"（`ok=true`），并保留这条否定结论备查。**

**⇒ 结论：`openNpc` 这条路"能调用、不报错"，但 UI 不出画面。
下一步应换思路：从 `NpcCtrl.sceneClickEvt`（它是**表**）找出真实的点击事件注册方式，
用**合法事件**触发一次点击，让客户端走完整原版链路。**

### 补充：任务系统在回退后仍稳定

```
t=dlgOpen&v=tries_25_openNpc_10030__ok_true_err_nil
<< 12403 SC_12403 mission_bid=10010 code=0 (already committed, idempotent)
```

**⇒ 客户端重登后又发了一次 `12403`，服务端**正确识别为已提交、未再发奖**（幂等生效）。**

---

## 一之补：★ 走通**原版点击链路**（本轮重大进展）

放弃"直接调 UI 函数"，改为**调 NPC 实体自己的点击回调**（用闭包局部捕获实体）：

```lua
local npcEntity = nil                 -- 闭包局部（_G / 类表存储都失败过）
Npc['setVo'] = function(self, vo)
   npcEntity = self
   -- 第 25 个 NPC 时（场景基本就绪）
   npcEntity:clickHandler()           -- ★ 原版点击回调
end
```

### 实测结果

```
t=npcH&v=clickNpcOpenDialog_n_1                      ← ★ clickNpcOpenDialog 被调用（1 个参数）
t=dlgH&v=openNpc_type_nil_bid_false                  ← 它内部往 openNpc 传了 **nil**
t=dlgOpen&v=…entity:clickHandler()_ok_false_err=
           game/scene/scene_model.luac: attempt to index a nil value
[11:00:55]  >> cmd=15203 ? body(4)=00 00 03 e9        ← ★★ 由**原版链路**发出 CS_15203！
[11:00:55]  << 15203 SC_15203 code=0 (9 bytes)        ← 服务端应答
```

### 结论（四条，都有实测支撑）

| # | 结论 | 依据 |
|---|---|---|
| 1 | **原版点击链路已走通**：`clickHandler` → `Fire(SCENE_NPC_CLICK)` → 监听者 → `clickNpcOpenDialog` → `SendProtocal(15203)` | 日志里 `clickNpcOpenDialog_n_1` 与 `>> cmd=15203` **同时**出现（此前 `15203` 都是我硬发的） |
| 2 | **NPC 点击是"事件驱动"**：`Npc:clickHandler` 本身**只发事件**，不打开 UI | 反汇编 `npc.luac proto[5]`（见下） |
| 3 | 是**监听 `SCENE_NPC_CLICK` 的 handler** 在打开对话，且它把 **nil** 传给了 `openNpc` | `openNpc_type_nil` |
| 4 | 中断点在 **`scene_model.luac: attempt to index a nil value`**，UI 未渲染 | 报错原文 + 视觉判读 |

**`Npc:clickHandler` 的反汇编（`npc.luac proto[5]`，params=1，仅 17 条字节码）：**

```lua
function Npc:clickHandler()
  SceneModel:getInstance().hasCheckMapList = {}                      -- @0-5
  GlobalEvent:getInstance():Fire(SceneEvent.SCENE_NPC_CLICK, self.vo) -- @6-15
end
```

**⇒ 下一步（明确的、可执行的）**：
**找到 `SCENE_NPC_CLICK` 的监听者**，看它为何把 `nil` 递给 `openNpc`
—— 大概率是它从某个上下文（如 `NpcCtrl.getOpenNpc()`）取 vo，而该上下文在我"人造点击"时为空。

---

## 一之补 2：`openNpc(10030)` 单独调用 `ok=true`（保留）

```lua
local c = NpcCtrl:getInstance()
if c.view == nil then c.view = NpcDialogs:New() end
c.view:openNpc(10030)     -- 10030 = 周漪 = Config.Mission[10010].commit_npc_id
```
```
t=dlgOpen&v=tries_25_openNpc_10030__ok_true_err_nil
```

**但先调 `openDefault()` 会让它报 `npc_cfg` 为 nil ⇒ 必须单独调 `openNpc`（否定结论，已回退）。**

---

| # | 改进 | 说明 |
|---|---|---|
| 1 | **任务列表以数据库为准** | `mission_rows()`：DB 优先，库里没有才用 `config` 播种 |
| 2 | **过滤已提交任务** | `mission_status==3` 不再出现在 `12400/12405` 列表里 |
| 3 | **幂等提交** | 已提交的任务再收到 `12403` 只回包、**不再发奖** |
| 4 | **提交后移出列表** | 发 `SC_12406{del_mission_list}` |
| 5 | **提交后刷新角色数据** | 推 `10301` / `10302` / `10303` |
| 6 | **两处 `12400` 推送统一走 DB** | 原先漏了"开局主动推"那一处（自查发现） |
| 7 | **`12403` 库空时先播种** | 避免 `12403` 早于 `12400` 到达时报 `no such mission`（自查发现） |

---

## 三、仍然待解（如实，不猜）

| # | 项 | 状态 |
|---|---|---|
| 1 | **对话 UI 前置**（`openDefault`/`createRootWnd`） | **待验证**（本轮把调用跑通了，UI 没渲染） |
| 2 | **`award_assets` 二元组含义** | **待验证**。已确认：`mission_view2 proto[15]` 用 `pairs(mis_config.award_assets)` 逐条 `table.insert`，上下文是 `AwardItem` / `item_bid` / `num` / `quantity` ⇒ **更像 `{物品bid, 数量}`**，但**没有确证**，故奖励仍用显式 `reward_exp`/`reward_gold` |
| 3 | 重登后客户端**再发一次 `12403`** | 已由幂等兜住；**根因待查** |
| 4 | "完成/可提交"界面标记 | 未复现（5G 已排除 `process_status`/`target`/`value`） |
| 5 | `12407–12460`/`154xx`/`185xx`/`19500` | **未知** |

---

## 四、本轮结论

| 项 | 结果 |
|---|---|
| 找到 5C 卡点真因 | ✅ **已确认**：`openNpc` 要 **bid 数字**，不是 VO 表 |
| `openNpc(10030)` 调用 | ✅ **成功无报错**（此前必报 nil） |
| 对话 UI 渲染 | ❌ 仍未出现（已列出候选前置） |
| 任务系统补强 | ✅ 7 项改进（DB 优先、过滤、幂等、移出列表、刷新、两处统一、播种兜底） |
| 改 APK 业务 / UI / 新增任务定义 | ✅ 未做（只改服务端与调试探针） |

**交付物**：本文件、`server/mock_server.py`、`server/dsh_fake_login.lua`、
`shots/p5c_dialog5.png`（周漪 + 「学院任务」标记，但无对话框）

---

**[WAITING FOR NEXT INSTRUCTION]**
