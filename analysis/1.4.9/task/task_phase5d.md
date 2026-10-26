# Phase 5D —— 任务系统审计（深化）

> APK：**1.4.9** / `com.shiyue.dldl.ewan.qihoo`
> 方法：`mission_ctrl.luac` 的 `RegisterProtocal` + `protocol/manual.md` 字段定义
> + `config_mission.luac` 反汇编 + Phase 4 运行期实测。
> 状态只用：**已确认 / 已验证 / 待验证 / 未知**

---

## 一、★★ 本轮最大成果：任务协议族**字段全部查清**

5A 里大量标 **未知** 的命令，本轮逐个查清：

| 功能 | CMD | 请求（CS） | 响应（SC） | 状态 |
|---|---|---|---|---|
| **任务列表（初始）** | **12400** | 空 | `mission_list:table(13 字段)` | **已验证**（服务端已推） |
| 任务列表（刷新/另一路） | **12401** | 空 | `missions:table(13 字段)` | **已确认**（定义） |
| **接取任务** | **12402** | `mission_bid:uint32` | `code:uint8, msg:string, missions:table(13 字段)` | **已确认** |
| **提交任务** | **12403** | `mission_bid:uint32` | `mission_bid:uint32, code:uint8, msg:string` | **已验证**（客户端曾请求，服务端未回） |
| **放弃任务** | **12404** | `mission_bid:uint32` | `code:uint8, msg:string, mission_bid:uint32` | **已确认** |
| 任务更新（增量） | **12405** | 空 | `update_mission_list:table(13 字段)` | **已确认** |
| 任务删除（列表） | **12406** | 空 | `del_mission_list:table(mission_bid:uint32)` | **已确认** |
| 未知用途 | **12416** | 空 | `mission_bid:uint32` | **未知**（只知字段） |

**13 字段（各处一致）**：

```
mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16,
loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32,
value:u32, show_lave_time:u8, lave_time:u32, accept_time:u32
```

**⇒ 关键结论：**
- **`12402` = 接取**（CS 带 `mission_bid`，SC 回 `code/msg` **+ 更新后的完整任务列表**）
- **`12403` = 提交**（CS 带 `mission_bid`，SC 回 `mission_bid + code/msg`）
- **`12404` = 放弃**（CS 带 `mission_bid`，SC 回 `code/msg + mission_bid`）
- **`12405` / `12406` = 服务端主动增量**（新增/更新 与 删除）
- **`12400` / `12401` = 全量列表**（两路，结构相同）

**⇒ Phase 5F（接取）→ 5H（完成）→ 5I（领奖）的协议骨架已经完整。**

---

## 二、`MissionCtrl` 注册的 33 条协议（已确认）

```
12400 12401 12402 12403 12404 12405 12406 12407 12408 12409
12412 12413 12414 12415 12416 12417 12420 12421 12422
12440 12450 12451 12452 12460 12499
15405 15420 15421 15422
18500 18501 18505
19500
```

本轮查清的是 **12400–12406、12416**；其余（12407/12408/12409/12412–12422/12440/12450–12460/12499/15405/15420–15422/18500 系/19500）
**仍为未知用途** —— 不猜。

---

## 三、任务状态（**已确认**，原始值）

```
MissionStatus = { STATUS_0 = 0, STATUS_1 = 1, STATUS_2 = 2, STATUS_3 = 3 }
MissionType   = 28 项（MIS_ZHU=1 … MIS_JIEYI=29）
MissionCode.defaultMissionId = 10000
```

**⇒ 1.4.9 客户端里**没有**"未接取/可接取/进行中/已完成/可提交/已领取"这套六态命名**，
按阶段要求**不自行定义状态**，直接使用客户端的 4 个 `STATUS_*`。

**已验证的语义（Phase 4 实测）**：`progress` 表的键 = 合法 `mission_status`
（`bid=10070` 的 `progress` 只有键 `1`；把 `mission_status` 设成 2 时 `prog[2] == nil`）。

---

## 四、任务数据结构（**已确认**）

### 4.1 协议侧（13 字段）

见 §一。

### 4.2 本地配置侧 `Config.Mission[bid]`

已确认的字段（节选）：

```
bid, name, desc, type, lev, realm, progress, progress_edit, progress_edit_2,
award_assets, commit_item, commit_assets, commit_npc_id, accept_npc_id,
accept_talk, commit_talk, auto_accept, auto_commit, abandon_flag,
career, sex, lev_track, is_track, max_lev, time_limit, …
```

**★ 关键**：**`accept_npc_id` / `commit_npc_id` 是"任务 ↔ NPC"的关联字段**
（在**本地配置**里，不在 NPC 条目里）—— 这直接回答 5A §十二 的疑问。

**实测样例**：

```lua
Config.Mission[10010] = { bid=10010, name='斗罗魂师', desc='去周漪老师处报到',
                          type=1, commit_npc_id=10030, commit_talk=50010, progress={} }
Config.Mission[10070] = { bid=10070, name='巫风挑战', desc='打败隔壁班的巫风', type=1 }
```

**⇒ `10010` 的 `commit_npc_id=10030`，而 5A 实测里 `Npc.clickHandler` 被触发的
正是 `vo.bid=10030`** ⇒ **两者对得上**（NPC 10030 就是「周漪」）。

---

## 五、任务数据来源（**已验证**，结论 C）

| 层 | 来源 |
|---|---|
| 任务**定义**（名字/描述/类型/等级/奖励/NPC/进度结构） | **本地** `config_mission.luac`（846 条，531 条 `progress` 非空） |
| 任务**状态**（已接/进度/目标值/接取时间） | **服务器** `SC_12400` 等（13 字段） |

**⇒ 服务端不必下发任务定义；只需下发状态，客户端自己按 `mission_bid` 查本地配置。**

---

## 六、第一条测试任务的候选（**已确认存在**）

| bid | 名字 | 描述 | type | `progress` | `accept_npc_id`/`commit_npc_id` |
|---|---|---|---|---|---|
| **10010** | 斗罗魂师 | 去周漪老师处报到 | 1 (MIS_ZHU) | 空（0 条） | `commit_npc_id=10030`（**待补 accept**） |
| 10070 | 巫风挑战 | 打败隔壁班的巫风 | 1 | 1 条 | 待查 |
| 35000 | 寻人 | 学院任务 | 6 (MIS_HUAN) | 1 条 | 待查 |

**⇒ 倾向 `10010`**：它是"去某 NPC 处报到"型，最接近"NPC→接→回 NPC→奖励"的最小闭环；
且它的 `commit_npc_id=10030` 已在实测里出现过（点了 `10030` 会触发 `clickHandler`）。

**⇒ 是否最终选它，留到 Phase 5E 定（本轮不新增、不实现）。**

---

## 七、新线索（对 5F 有用）

5B 截图里，**NPC「周漪」头顶显示「学院任务」标记** ——
说明客户端能按本地配置在 NPC 头顶绘制任务标记。
**⇒ 服务器一旦把任务状态推对了，NPC 头顶的标记应当会变（可提交等）**，这是 5F–5H 的天然验证点。

---

## 八、仍然未知（如实列出，不猜）

| 项 | 状态 |
|---|---|
| `12407/12408/12409/12412–12422/12440/12450–12460/12499/15405/15420–15422/18500 系/19500` 的用途 | **未知** |
| `12416` 的用途（`SC` 只有 `mission_bid`） | **未知** |
| `award_assets` 二元组（如 `{1=2, 2=1290}`）的含义 | **待验证** |
| `progress[status]` 内层结构 | **待验证** |
| 任务"完成"由服务端还是客户端判定 | **未知** |
| `10010` 的 `accept_npc_id` | **待验证** |

---

## 九、Phase 5D 结论

| 项 | 结果 |
|---|---|
| 任务协议的**请求/响应字段** | ✅ **本轮查清 8 条**（12400–12406、12416） |
| 接取/提交/放弃的 CMD 与字段 | ✅ **已确认**（12402 / 12403 / 12404） |
| 任务状态枚举 | ✅ 已确认（4 个 `STATUS_*`，无六态） |
| 任务数据结构 | ✅ 已确认（协议 13 字段 + 配置 36 字段） |
| 任务 ↔ NPC 关联 | ✅ **已确认在本地配置**（`accept_npc_id` / `commit_npc_id`） |
| 任务数据来源 | ✅ 已验证（结论 C） |
| 第一条测试任务 | ✅ 候选已定（`10010`，待 5E 确认） |
| **未实现任何任务协议** | ✅（本阶段只审计） |
| 改 APK / UI / 新增任务 | ✅ 未做 |

**⇒ 5D 完成。任务系统的协议骨架、数据结构、状态枚举、数据来源、NPC 关联全部查清，
为 5E–5I 提供了可直接落地的依据。**

---

**[WAITING FOR PHASE 5E]**
