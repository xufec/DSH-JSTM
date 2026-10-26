# NPC 交互 → 任务完成 → 领奖：链路进展与精确定位

> 本轮目标：**完善任务流程 —— 配置 NPC 交互、任务完成、奖励接受**。
> 全部结论以 1.4.9 APK 反汇编 + 实机探针 + 服务端日志为证据，未编造。

---

## 一、★ 本轮最重要的发现：`MissionStatus` 的真实语义

`mission_util.luac` **proto#68** 里的常量表（`tools/find_enum_table.py STATUS_`）：

```
MissionStatus = { STATUS_0 = 0, STATUS_1 = 1, STATUS_2 = 2, STATUS_3 = 3 }
```

语义由**客户端两处消费点**反推（两处互相印证）：

| 消费点 | 文件 / proto | 分桶规则 |
|---|---|---|
| `MissionData:add` | `mission_data2.luac` proto#3 | `0→can_list`（可接）、`3→finish_list`、**else(1,2)→receive_list**（追踪栏） |
| `NpcMissionManager:addNpc` | `npc_mission_manager.luac` proto#5 | `0→can_list`、`1→access_list`、**`2→finish_list`** |

⇒ **`STATUS_2 = 可提交`**。

而 NPC 对话里"任务项"的来源正是（`npc_dialogs.luac` proto#8 `openNpc`）：

```lua
local mis_list = self.ctrl.manager:getNpcVo(npc_bid):getMissionList()
if mis_list:GetSize() > 0 then self:openMis(mis_list:Get(0))
else                            self:openDefault() end
```

`MNpcVo:getMissionList`（`npc_mission_vo.luac` proto#5）把
`can_list + access_list + **finish_list**` 拼成一个数组并按 `mis_type_sort / mis_status_sort / mis_bid` 排序。

⇒ **服务端不送 `STATUS_2`，NPC 对话里就永远没有"完成/提交"项。**
这就是"任务无法完成/无法领奖"在**客户端一侧**的根因。

---

## 二、本轮已完成的服务端改动（`server/mock_server.py`）

| # | 改动 | 依据 |
|---|---|---|
| 1 | **播种**：无条件任务（"去某 NPC 处报到"类，如 10010/10030/10040）直接置 `STATUS_2` | `progress` 为空 |
| 2 | **进度达成**：`mission_progress_advance` 在 `value >= target_value` 时置 `STATUS_2`（原来只置 `process_status=1`） | 同 §一 |
| 3 | **状态归一（幂等）**：`mission_rows()` 里把"无条件/条件已满足"的在途任务提升到 `STATUS_2`，修好**旧存档** | 同 §一 |
| 4 | **补推 12405**：任务变为可提交后立即推一次 `SC_12405`，促使客户端重建该 NPC 的 `finish_list` | `mission_ctrl` proto#28 `handle12405` 会 Fire `NpcContants.ADD_MISSION` |

### 实测效果（**已验证**）

```
DB:  10010 status=2 / 10030 status=2 / 10040 status=2 / 10051..10054 status=2
客户端任务追踪栏（截图逐字判读）：
   主线-斗罗魂师   去周漪老师处报告
   主线-武魂觉醒   了解武魂觉醒
   主线-武魂觉醒   了解武魂觉醒
   主线-武魂觉醒 **完成**   老师传授你群攻技能     ← ★ 出现了「完成」标记
```

---

## 三、仍差最后一环：`NpcMissionManager` 是空的（**已精确定位**）

探针在点 NPC 后直接读实例状态：

```
dlgS enter_bid:10070
dlgS manager_npc_n:0_has:no          ← ★ NPC 任务管理器**完全为空**
dlgS after_rootwnd:userdata_vis:true_size:960x540_mis_vo:nil_btns:2:1_2
```

| 读数 | 含义 |
|---|---|
| `manager_npc_n:0` | `NpcCtrl:getInstance().manager.npc_list` 里**一个 NPC 都没有** |
| `after_rootwnd:userdata_vis:true_size:960x540` | 对话窗口**确实创建了且 visible**（960x540 = 全屏设计分辨率） |
| `mis_vo:nil` | 走的是"无任务"分支 ⇒ **`openDefault`**（只有闲聊/默认按钮） |

⇒ **面板本身没问题，问题是"这个 NPC 名下没有任务"。**

### 喂数据的链路（**已还原**）

```
mission_ctrl.luac proto#31 (`handle12400`) / proto#28 (`handle12405`)
    └─ GlobalEvent:Fire(NpcContants.ADD_MISSION, commitNpc, missionVo)
            │
            ▼
npc_ctrl.luac proto#16 (`registerEvents`)
    └─ Bind(NpcContants.ADD_MISSION) → proto#5 = NpcCtrl:addNpc(bid, m)
            │
            ▼
npc_ctrl.luac proto#5 → self.manager:addNpc(bid, m)   → NpcMissionManager 分桶
```

### 实测到的**异常现象**（已查明，**不是服务端问题**）

```
18:37:23  rq handle12400_in_list:4      ← 第一次收到 4 条
18:37:23  rq handle12400_in_list:nil    ← 第二次，resp 为 nil
```

#### 「服务端发了空体 12400」这个假设 —— **已被证伪**

| 查证 | 结果 |
|---|---|
| 服务端 `12400` 的**全部发送点**（源码审计） | 只有 2 处：`mock_server.py:1582`（应答 `CS_12400`）、`:1965`（`10300` 后的主动推送）；**两处都用 `build_12400(_ms)` 封装**，且推送处有 `if _ms:` 守卫 ⇒ **不可能发出空体** |
| 线上实际帧（`tcp.log` 全部 `<< 12400`） | `mission_list=4 (144 bytes)`、`mission_list=8 (280 bytes)` —— **没有**任何小包/空包，也**没有** `12400 skipped` |
| 客户端注册表（`mission_ctrl.luac` proto#11 逐指令读出） | **12400 只注册一次** → `handle12400`，不存在重复注册 |

#### ★ nil 调用的真正来源：**客户端事件系统**

在包装里加了 `debug.traceback()`，在 `resp == nil` 时打印调用栈，实测得到：

```
18:49:18  NIL_CALLER_ stack traceback:
            C: in function 'pcall'
            string 'config.luac':1303: in function 'handle12400'   ← 探针包装
            string 'game/mission/mission_ctrl.luac': in main chunk
            string 'sys/event.luac': in ...                        ← ★★ 事件系统
```

⇒ **`handle12400` 被 `GlobalEvent`（`sys/event.luac`）当成"事件监听器"又调了一次**，
这次没有协议参数，所以 `resp == nil`。

⇒ **结论：让 NPC 任务列表为空的那颗螺丝不在服务端**，而是
**客户端把 `handle12400` 也挂到了事件上**（同一个函数身兼"协议处理器"与"事件监听器"）。

#### 对 §三结论的修正

`handle12400` 的 nil 调用本身是**无害**的（proto#31 开头即对 nil 早退）。
因此 `manager_npc_n:0` 的原因需要改判为下述之一（**尚未定论**）：

1. `handle12400` 在真正处理列表时，**proto#31 会把 `resp` 换成自建表**
   （反汇编 23–28 行：`r2={mission_list={self.emptyMission}}`，随后 `MOV r1,r2`），
   若该分支被走到，就把服务端下发的列表**覆盖成占位任务**，`createMis`/`Fire(ADD_MISSION)`
   便只会处理占位项 ⇒ **NPC 管理器自然为空**；
2. 或 `NpcContants.ADD_MISSION` 触发时 `NpcCtrl` 尚未注册监听。

⇒ **下一步（唯一待办）**：确认 proto#31 的 `resp = 自建表` 分支是**正常路径**还是
"空列表兜底分支"（即它是否只在 `resp.mission_list` 为空/缺失时才走）。这决定修法：
若属兜底分支被误走，则问题在字段名/结构解析；若属正常路径，则需另行定位。


---

## 四、如实标注（未完成/未验证）

| 项 | 状态 |
|---|---|
| 服务端 `STATUS_2` 状态机 | ✅ 已实现并实测（DB + 追踪栏） |
| NPC 对话面板创建 | ✅ 已实测存在且 visible |
| NPC 对话**列出任务项** | ❌ 未达成 —— `NpcMissionManager` 为空 |
| 空体 `12400` 的确切来源 | ⚠️ **已缩小到服务端推送路径，未最终确认** |
| 通过对话**点击完成并领奖** | ❌ 未验证（依赖上一项） |

---

## 五、本轮新增/修改的文件

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | STATUS_2 状态机（播种 / 进度 / 归一 / 补推 12405） |
| `server/dsh_fake_login.lua` | 新增 `dlgS`（对话实例诊断）、`rq`（12400 重放实验）探针段 |
| `analysis/1.4.9/task/npc_quest_flow.md` | 本文件 |
| `analysis/1.4.9/task/_npc_ctrl_regEvents.txt` 等 | 本轮反汇编证据 |
| `tools/find_enum_table.py` / `tools/find_proto_with.py` | 定位枚举与 proto 的工具 |
