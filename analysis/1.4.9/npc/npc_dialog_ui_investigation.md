# NPC 对话 UI —— 原版链路解剖与探针实测

> **目标**：让"点 NPC → 出对话框 → 接/交任务"走**原版交互**，而不是探针直调 `MissionCtrl:submit`。
> **本轮结论**：**链路已完整解剖（有反汇编证据）**；探针已注入并运行，
> **但卡在"获取 NPC vo 对象"这一步**，**未真正调起对话框**（如实）。

---

## 一、★★ 原版对话链路（**已确认**，来自 `npc_ctrl.luac` 反汇编）

```
Npc:clickHandler()
   └─ Fire(SceneEvent.SCENE_NPC_CLICK, vo)
        ├─ scene_model.luac proto[5]   ← ★ **不是对话**！处理的是**传送门(DOOR)**
        └─ npc_ctrl.luac  proto[2]     ← ★ **真正的对话入口**（注册 clickNpcOpenDialog）
```

### 1.1 `scene_model.luac proto[5]` —— **传送门 handler，与对话无关**（69 条字节码全还原）

```lua
function(vo)
  if not vo then return end
  if vo:isOnTeamFollow() then return end
  if SceneModel:getInstance():getIsOnXM() then return end
  if vo.type == ObjType.ELE_Effect then return end
  vo:getScene():cancelWalk()
  vo:getScene():closeClickEffect()
  local ev = {}
  ev.findVoTarget = ...
  ev.sub_type = vo.sub_type
  ev.type     = FindType.DOOR          -- ★ DOOR（传送门）
  ev.pos      = cc.p(vo.x, vo.y)
  ev.sceneId  = vo.sceneId
  ev.doorId   = vo.id
  vo:getScene():gotoTarget(ev)
end
```

**⇒ 之前 `/Fire(SCENE_NPC_CLICK)` 报的 nil，极可能来自这里**（`vo:getScene()` 对我们的 NPC 为 nil）。
**⇒ 这也解释了为什么"点 NPC 出不来对话框"—— 罪魁可能不是对话代码，而是同事件上的这个 DOOR handler 先报错。**

### 1.2 `npc_ctrl.luac proto[26]` —— **真正的对话入口**（30 条字节码全还原）

```lua
function(self, vo)                                     -- params=2
  if Battle:getInstance():inFight() then return end    -- @0-9   战斗中不开
  if not vo:checkIsOpen() then return end              -- @10-15 ★★★ 门禁！
  if self.view == nil then
    self.view = NpcDialogs:New()                       -- @19-23
  end
  self.view:openNpc(vo)                                -- @24-29 ★ 传 **vo**（不是裸 bid）
end
```

**⇒ 三个关键点：**
1. **`vo:checkIsOpen()` 是门禁** —— 返回假就直接 return，对话框不出现
2. **`NpcDialogs` 需要**实例**（`NpcDialogs:New()`），不是直接调类方法**
3. **`openNpc` 收到的是 **vo 表**（含 `bid`），不是裸 bid 数字**
   ⇒ 与我此前"直调 `NpcDialogs:openNpc(10030)`"的做法**不一致** —— 那是推测用法，**现已否证**

---

## 二、探针实测（**已注入并运行，但未取到 vo**）

探针做的事：
1. `wrap Npc.checkIsOpen` —— 观察门禁返回什么
2. 取 NPC vo（依次尝试 `SceneModel:getInstance().npcList`、`getNpcList()`）
3. 拿 `NpcCtrl:getInstance()` 实例，调 `ctrl:clickNpcOpenDialog(vo)`
4. 上报 `npcui`

### 实测输出

```
t=npcui&v=vo_false
t=npcui&v=open_ok_true_err_nil
t=npcui&v=vo_false
t=npcui&v=open_ok_true_err_nil
```

| 观察 | 结论 |
|---|---|
| `open_ok_true` | 探针块本身执行正常（无语法/运行时崩溃） |
| **`vo_false`** | ❌ **没能取到 NPC vo** —— `SceneModel.npcList` / `getNpcList()` **都不是真实字段名** |
| **未见 `Npc.checkIsOpen_wrapped`** | ⚠️ 该时刻 `Npc` 类或其 `checkIsOpen` 尚不可用（**待验证**） |

**⇒ 因此 `ctrl:clickNpcOpenDialog(vo)` 从未真正执行，对话框未调起。**

---

## 三、精确卡点（下一步唯一要解决的）

**「NPC 的 vo 对象存在哪里、怎么取？」**

候选途径（**下一轮逐个探**，不猜）：
1. 枚举 `SceneModel:getInstance()` 的**全部字段名**（找到 NPC 列表的真实字段）
2. `NpcCtrl:getInstance()` 上找列表（如 `npc_list` / `npcs` / `getNpcVo`）
3. 场景元素表（`element_list` / `vo_list`）里按 `ObjType.NPC(2)` 过滤
4. `Npc.registEvent` 的存在说明 NPC 是**对象**，可能在某个注册表里

**探针已就位**（`_G.__dsh_npcui` 块），只需把"取 vo"那两行换成正确的取法即可复测。

---

## 三之二、★★★ 第二轮：`SceneModel` 字段名扫描（**已取得决定性结果**）

### 做法

探针枚举 `SceneModel:getInstance()` 的**全部字段名**（每 tick 报 3 个，规避 URL 200 字符限制）。

### 结果 1：`SceneModel` 共 **44 个字段**（**已确认**）

```
astar_table | autoFight_boolean | beastList_table |
beast_change_event_table | clllecting_boolean | convoyList_table |
convoy_change_event_table | convoy_state_event_table | doorRange_number |
elementList_table | element_click_event_table | find_target_event_table |
getScene_function | guild_hide_boolean | hasCheckMapList_table |
isJoystick_boolean | isWalking_boolean | is_can_move_boolean |
loadState___boolean | map_table | map_block_table |
monList_table | monRange_number | mon_click_event_table |
move_event_table | move_next_event_table | ★ npcList_table ★ |
npcRange_number | npc_click_event_table | player_click_event_table |
pointRange_number | roleList_table | sceneId_number |
skip_story_event_table | teamList_table | teamRange_number |
walk_end_event_table | walk_to_point_table
```

**⇒ `npcList` 是**真实字段**（我上一轮 `vo_false` 不是字段名错）。**

### 结果 2：★ **`npcList` 是空的**

```
t=npc2&v=npcList_typetable_n0
```

**⇒ `SceneModel.npcList` 类型是 table，但 **条数 = 0**。**

**⇒ 而画面上**确实能看到 NPC**（周漪/唐舞桐等，多张截图已确认）**
**⇒ 结论：NPC **不在 `npcList` 里**，一定在**别的容器**里。**

### 最可能的容器（下一步，**不猜，去探**）

从同一份 44 字段清单看，候选：

| 字段 | 理由 |
|---|---|
| **`elementList`** | 场景元素**通用**表 —— NPC 很可能作为 `ObjType.NPC(2)` 的元素存在这里 |
| `monList` | 怪物表（已知，用于战斗） |
| `roleList` | 玩家表 |
| `npc_click_event_table` | 只是**事件表**，不是实体列表 |

**⇒ 下一轮只需把探针的取 vo 改为：遍历 `elementList`，筛 `type == ObjType.NPC(2)`。**

---

## 三之三、本轮自查修掉的一个 bug（如实）

第一次注入 `npc2` 块后**完全没有上报**。自查发现原因：
**标志名 `_G.__dsh_npc2` 与文件里**已存在的旧块**（第 903 行）冲突** ——
旧块先置位了该标志，导致我的新块**永远不执行**。改用 `__dsh_npc2b` 后即正常上报。

**⇒ 这类"标志名冲突导致探针静默失效"的坑，值得记下。**

---

## 三之四、★★★ 第三轮：`elementList` 探测（**已取得确定结果**）

### 做法

把探针从"读 `npcList`"改为"遍历 `SceneModel.elementList`，筛 `type == ObjType.NPC(2)`"，
并把该块**移到确实会执行的段落**（见下方"踩坑"）。

### 结果

```
t=el&v=elementList_ttable_n0_npc0
t=el&v=first_
t=el&v=no_npc_in_elementList
```

**⇒ `SceneModel.elementList` 类型是 table，但 **条数 = 0**；`first` 也是 nil。**

### ★ 汇总（三个容器都探过了）

| 容器 | 类型 | 条数 | 结论 |
|---|---|---|---|
| `SceneModel.npcList` | table | **0** | ❌ 空 |
| `SceneModel.elementList` | table | **0** | ❌ 空 |
| `SceneModel.monList` | table | （未测，已知用于战斗） | — |

**⇒ NPC 既不在 `npcList` 也不在 `elementList`，但**画面上 NPC 可见**（多张截图已确认）。**

**⇒ 推断（`INFERRED`）：NPC 实体不由 `SceneModel` 的这三个列表持有 ——**
**很可能是**场景节点层（view）**里的显示对象，或 `SC_10201` 的接收 handler **解析后直接建节点**、
**不放进 SceneModel 的列表。**

### ★ 下一步（精确、可执行）

1. **包住 `SC_10201` 的接收 handler**（`scene_controller` 的 `on10201` / `handle10201`），
   **看它把 `npcs` 存到哪里** —— 这是**最直接的取证方式**（同 F3 手法）
2. 或**枚举 `SceneModel.scene` 的节点树**（`getChildren()`），找带 NPC 特征的子节点
3. 参考线索：探针已上报过 `t=sceneInfo&v=...npcs_table_mons_table_elems_table...`
   —— 说明**存在一个 `npcs` 表**，只是不在我们探过的容器里

---

## 三之六、★★★★ 第四轮：包 `on10201`（**决定性突破**）

### 做法

依据 `scene_controller proto[7]` 的注册：`RegisterProtocal(10201, 'on10201')`，
包住 `SceneController.on10201`，**观察它收到什么、处理后 `SceneModel` 容器的变化**。

### 结果 1：★ **`npcList` 确实会被填充为 26 条**（前三轮的"空"是**时序问题**）

```
t=n10201&v=SceneController.on10201_wrapped
t=n10201&v=in_npcs26_mons1_elems0                    ← handler 收到 26 个 NPC + 1 只怪
t=n10201&v=after_npcList26_elemList0_monList1        ← ★★★ 处理后 npcList = 26 条！
```

**⇒ 我前三轮读 `npcList` 得到 0，**不是字段错，而是读得太早**（在 `10201` 到达之前）。
**⇒ 这是重要更正：`SceneModel.npcList` 是**有效容器**，只是要**等 `on10201` 之后**读。**

### 结果 2：★ **成功取到 NPC vo**

```
t=n10201&v=vo_bid10150_type2
t=n10201&v=first_bid_10150_id_10150_type_2_name_<中文名>_sub_type_nil
```

**⇒ vo 字段：`bid=10150`、`id=10150`、`type=2`（= `ObjType.NPC`）、`name` 有中文名、`sub_type=nil`。**
**⇒ `bid=10150` 正是我们 `10201` 下发的 25 个 NPC 之一 —— 数据链是对的。**

### 结果 3：调对话入口 ⇒ **新卡点**

```
t=n10201&v=click_okfalse_e_string__game/npc/npc_dialogs.luac__:0:_attempt_to_index_a_nil_value
```

### ★ 结果 4：反汇编 `npc_dialogs proto[9]`（openNpc，32 条字节码全还原）

```lua
function(self, x)                                  -- params=2
  self.npc_cfg = Config.Npc[x]                     -- @0-3  ★ x 必须是 **bid 数字**
  if not self.npc_cfg then return end              -- @4-6
  if self.ctrl.manager:getNpcVo(x) == ... then     -- @7-14 ★ self.ctrl 若为 nil ⇒ nil 索引
    if self.ctrl:getMissionList():GetSize() >= 0 then
      ... openNpc(x)
    end
  end
end
```

**⇒ 两个明确结论：**
1. **`openNpc(x)` 的 `x` 是 **bid 数字**（内部 `Config.Npc[x]`）—— 我传 **vo 表**是错的**
2. **`self.ctrl` 必须已设置**（`self.ctrl.manager`、`self.ctrl:getMissionList()`）
   ⇒ **`self.ctrl` 为 nil 就是那个 `attempt to index a nil value` 的来源**

**⇒ 这也修正了我更早的一个判断**：之前记的"`openNpc` 的 x 是 bid 数字不是 VO 表"**本来是对的**，
后来又被我改成了传 vo —— **本轮把这个反复纠正回来了**（依据是字节码，不是推测）。

### ★ 下一步（精确）

用 **bid 数字** 调，并确保 `view` 的 `ctrl` 已设置：

```lua
local v = NpcCtrl:getInstance().view      -- 或 NpcDialogs:New()
v.ctrl = NpcCtrl:getInstance()            -- ★ 补上 ctrl（否则 nil 索引）
v:openNpc(10150)                          -- ★ 传 bid 数字
```

---

## 三之八、★★★★★ 第五轮：用 **bid 数字** + 注入 `ctrl`（**又推进一步**）

### 做法（依据第四轮反汇编）

按 `npc_dialogs proto[9]`：`x` 用 **bid 数字**；并确保 `view.ctrl` 已设置。

```lua
local v = ctrl.view or NpcDialogs:New()
if v.ctrl == nil then v.ctrl = ctrl end
v:openNpc(10030)          -- 周漪（10010 的提交 NPC）
```

### 结果

```
t=n10201&v=view_oktrue_ctrltrue_bid10030                              ← ★ view/ctrl/bid 都对
t=n10201&v=openNpc_okfalse_e_...npc_dialogs.luac:0:_attempt_to_index_a_nil_value
```

**⇒ `view` 有、`ctrl` 已注入、`bid=10030` 正确 —— 但 `openNpc` 仍报 nil 索引。**
**⇒ 说明 nil **不在** `self.ctrl`。**

### ★ 再定位：nil 在 `self.ctrl.manager`

`proto[9]` 在 `npc_cfg` 判空之后的**第一件事**就是：

```lua
if self.ctrl.manager:getNpcVo(x) == ... then     -- @7-14
```

**而 `NpcCtrl` 实例的字段扫描结果（第二轮实测）是：**

```
NpcCtrl_n4  ->  DeleteMe | __dsh_sm | __class | __type
CTRL_       ->  New_function | delete_boolean | __init_boolean | super_table
```

**⇒ `NpcCtrl` 实例上**没有 `manager` 字段** ⇒ `self.ctrl.manager` = nil ⇒ 正是那个 `attempt to index a nil value`。**

**⇒ 结论（`CONFIRMED`）：`NpcDialogs` 需要 `view.ctrl.manager` 指向一个**「NPC 任务管理器」**，**
**从文件名看应是 `game/npc/npc_mission_manager.luac`（`NpcMissionManager`）。**

### ★ 下一步（精确）

注入 `manager` 再试：

```lua
local v = ctrl.view or NpcDialogs:New()
v.ctrl = ctrl
if ctrl.manager == nil and type(NpcMissionManager) == 'table' then
  ctrl.manager = NpcMissionManager:getInstance()   -- 或 :New()
end
v:openNpc(10030)
```

**⇒ 若 `NpcMissionManager` 不存在/名字不同，就用**枚举 `_G` 里含 `Mission`/`Manager` 的全局名**来定位（不猜）。**

---

## 三之十、★★★★★★ 第六轮：注入前先验证 —— **上一轮判断被否证**

### 做法

在注入 `manager` **之前**先验证它到底是不是 nil，并枚举 `_G` 里含
`Mission` / `Manager` / `Npc` 的全局名（找正确的管理器）。

### 结果

```
t=n10201&v=G_n48                                    ← 48 个候选全局名
t=n10201&v=G2_BuffManager_table
t=n10201&v=G3_CCNetManager_table
t=n10201&v=G4_CDPlayManager_table
t=n10201&v=G5_CSManorNpcList_10706_table
t=n10201&v=G6_CommonTipsManager_table
t=n10201&v=G8_MNpcVo_table
t=n10201&v=G10_MissionCode_table
t=n10201&v=G12_MissionContants_table
t=n10201&v=ctrl_manager_true                        ← ★★★ ctrl.manager **不是 nil**！
t=n10201&v=openNpc_okfalse_e_...npc_dialogs.luac:0:_attempt_to_index_a_nil_value
```

### ★ 结论：上一轮的判断**被否证**

**我上一轮写的是**："`NpcCtrl` 实例上没有 `manager` 字段 ⇒ `self.ctrl.manager` = nil ⇒ 就是那个 nil"。
**实测：`ctrl.manager` **存在**（`ctrl_manager_true`）。**

**⇒ 所以 nil **不在** `self.ctrl.manager`。**
**（按项目规则，被否证的假设保留记录 —— 见上一节，本轮给出更正。）**

### 当前确切的未知

`proto[9]` 里在这之后还有 `manager:getNpcVo(x)`、`ctrl:getMissionList():GetSize()` 等调用。
**但报错信息只有 `npc_dialogs.luac:0`（行号为 0，无堆栈）**，**无法据此断定是哪一处。**

### ★ 下一步（**能精确定位**的办法）

**用 `xpcall` + `debug.traceback` 取真实行号：**

```lua
local ok, err = xpcall(function() v:openNpc(10030) end,
                       function(e) return tostring(e) .. '|' .. debug.traceback('', 2) end)
report('npc2', 'trace_' .. tostring(err):sub(1, 150))
```

**⇒ 这能直接给出**文件名 + 行号 + 调用栈**，一步定位到具体语句，不必再猜。**
（LuaJIT 的 `debug.traceback` 在 `npc_dialogs.luac` 这种带调试信息的字节码上可用性**待验证**；
若不可用，退路是**逐行 wrap** `proto[9]` 里的几个被调用者，看哪个先被调用到。）

---

## 三之十一、本轮踩的坑（累计 3 个，如实记录）

1. **标志名冲突**：`_G.__dsh_npc2` 与文件里已存在的旧块（第 903 行）冲突 ⇒ 新块永不执行。
   改用 `__dsh_npc2b` 解决。
2. **探针块放错位置**：`el` 块最初插在 `-- ★ 连接` 之前，**该段实际不执行**
   ⇒ **连续两轮零上报**。移到 `-- 客观判据：场景 / 自身角色`（该段有 `loadState` 等上报可证实在跑）
   之后，**立即取得结果**。

**⇒ 教训：探针插入点必须选在"已被证明在运行"的段落**，否则会静默失效，
且**看起来像"没数据"而不是"没执行"** —— 这一步差点让我误判。

---

## 四、本轮的**净收获**（有价值的部分）

| # | 收获 | 证据 |
|---|---|---|
| 1 | **证明 `scene_model proto[5]` 不是对话入口，而是 DOOR 传送门 handler** | 69 条字节码全还原 |
| 2 | **找到真正的对话入口 `npc_ctrl proto[26]`** | 30 条字节码全还原 |
| 3 | **确认门禁是 `vo:checkIsOpen()`**（此前未知） | `proto[26] @10-15` |
| 4 | **否证了"直接 `NpcDialogs:openNpc(bid)` 可行"** —— 原版传的是 **vo**，且需 `NpcDialogs:New()` 实例 | `proto[26] @19-29` |
| 5 | 探针已注入并可运行（`open_ok_true`） | 上报 |

---

## 五、仍缺失 / 待验证（如实）

| 项 | 状态 |
|---|---|
| NPC vo 的获取途径 | ❌ **UNKNOWN**（本轮未找到） |
| `Npc.checkIsOpen` 是否存在、返回什么 | ⚠️ **待验证**（wrap 未生效） |
| 对话框能否真正渲染 | ❌ **未验证**（vo 没拿到，从未调用） |
| `SCENE_NPC_CLICK` 上是否还有其它监听者 | ⚠️ 未穷举 |
| **本轮是否改动了游戏逻辑** | ✅ **没有** —— 只改探针（调试注入），业务代码零改动 |

---

## 六、交付物

- 本文件：`analysis/1.4.9/npc/npc_dialog_ui_investigation.md`
- 探针：`server/dsh_fake_login.lua`（含 `npcui` 块，门禁检查已过）
- APK：`patched/jstm_fakelogin.apk`（已安装）
