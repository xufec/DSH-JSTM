# 任务协议矩阵（Phase 5A 建立 / Phase 5D 补齐字段）

> 来源：`assets/src/game/mission/mission_ctrl.luac` 的 `RegisterProtocal`（33 条）
> ＋`protocol/manual.md` 字段定义（`tools/show_cmd.py <cmd>` 可复核）＋ 实机 TCP 日志。
> 状态只用：**已确认 / 已实现 / 已验证 / 待验证 / 未知**

---

## 一、★ 核心任务协议（Phase 5D 已把字段全部查清）

| 功能 | CMD | 请求字段 | 响应字段 | 客户端模块 | 当前服务器 | 状态 |
|---|---|---|---|---|---|---|
| **获取任务列表（初始）** | **12400** | 空 | `mission_list:table(mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16, loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32, value:u32, show_lave_time:u8, lave_time:u32, accept_time:u32)` | `MissionCtrl` | **已实现**（`10300` 后主动推） | **已验证** |
| 获取任务列表（刷新/另一路） | **12401** | 空 | `missions:table(同上 13 字段)` | `MissionCtrl` | 未实现 | **已确认** |
| **接取任务** | **12402** | `mission_bid:uint32` | `code:uint8, msg:string, missions:table(同上 13 字段)` | `MissionCtrl` | 未实现 | **已确认** |
| **提交任务** | **12403** | `mission_bid:uint32` | `mission_bid:uint32, code:uint8, msg:string` | `MissionCtrl` | 未实现 | **已验证**（客户端曾请求） |
| **放弃任务** | **12404** | `mission_bid:uint32` | `code:uint8, msg:string, mission_bid:uint32` | `MissionCtrl` | 未实现 | **已确认** |
| 任务更新（增量） | **12405** | 空 | `update_mission_list:table(同上 13 字段)` | `MissionCtrl` | 未实现 | **已确认** |
| 任务删除（列表） | **12406** | 空 | `del_mission_list:table(mission_bid:uint32)` | `MissionCtrl` | 未实现 | **已确认** |
| 用途未知 | **12416** | 空 | `mission_bid:uint32` | `MissionCtrl` | 未实现 | **未知**（只知字段） |

**13 字段（各协议一致）**：

```
mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16,
loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32,
value:u32, show_lave_time:u8, lave_time:u32, accept_time:u32
```

---

## 二、其余任务族命令（**用途未知**，不猜）

`MissionCtrl` 还注册了：

```
12407 12408 12409 12412 12413 12414 12415 12417 12420 12421 12422
12440 12450 12451 12452 12460 12499
15405 15420 15421 15422
18500 18501 18505
19500
```

**⇒ 这些的请求/响应字段与用途本轮**未确认**，一律标【未知】，
**没有用经验填补**。**

---

## 三、实机验证情况

| CMD | 客户端是否发出过 | 服务端 | 结果 |
|---|---|---|---|
| `12400` | ❌（客户端**不请求**，靠服务端主动推） | ✅ 已实现 | **已验证** |
| `12403` | ✅ 历史日志里出现过（服务端未回） | ❌ | **已验证**（请求/字段） |
| 其余 | ❌ 历史日志里未出现 | ❌ | **未知** |

---

## 四、与 NPC 的任务关联（**已确认**）

**任务 ↔ NPC 的关联在本地配置**：`Config.Mission[bid].accept_npc_id` / `.commit_npc_id`
（**不在** NPC 条目里带 `task_id`）。

**实测印证**：`Config.Mission[10010].commit_npc_id = 10030`，
而 5A 里实测 `Npc.clickHandler` 被触发的正是 `vo.bid = 10030` ⇒ **两者对得上**。

`NpcCtrl` 另有 `add_mission_event` / `delete_mission_event`，
以及 `game/npc/npc_mission_manager.luac` / `npc_mission_vo.luac`（`MNpcVo`）——
**客户端侧存在 NPC↔任务的关联机制**，其**具体协议归属待验证**。

---

## 五、**禁止猜测**声明

- 本表中所有 `未知` **都是真的未知**；
- 已确认的字段**全部来自 `protocol/manual.md`（1.4.9）**，可用 `tools/show_cmd.py <cmd>` 复核；
- **没有**虚构任何 CMD、字段或含义。
