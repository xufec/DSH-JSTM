# 任务数据结构（Phase 5A 审计）

> 来源：`protocol/manual.md`（`tools/show_cmd.py`）+ `config_mission.luac` 反汇编
> + Phase 4 的运行期实测。状态只用：**已确认 / 已验证 / 待验证 / 未知**

---

## 一、协议里的任务条目（`SC_12400.mission_list` 元素，**已确认**）

13 个字段，**全部简单类型**（无未解出的动态子表）：

| 字段 | 类型 | 含义 |
|---|---|---|
| `mission_bid` | uint32 | 任务 id（对应 `Config.Mission[bid]`） |
| `mission_status` | uint8 | 任务状态（见 §三） |
| `commit_num` | uint16 | 已提交次数 |
| `loop_count` | uint16 | 循环计数 |
| `loop_num` | uint16 | 当前轮次/进度轮数 |
| `code` | uint8 | 任务码 |
| `process_status` | uint8 | 处理状态 |
| `target` | uint32 | 目标 id |
| `target_value` | uint32 | 目标数量 |
| `value` | uint32 | 当前值 |
| `show_lave_time` | uint8 | 是否显示剩余时间 |
| `lave_time` | uint32 | 剩余时间 |
| `accept_time` | uint32 | 接取时间 |

**⇒ 这是"服务端 → 客户端"的任务状态载体；也是 Phase 5 要填的数据结构。**

---

## 二、本地配置里的任务定义（`config_mission.luac`，**已确认**）

`Config.Mission[bid]` 的字段（从条目表 TableConst + 后续 `TSETS` 读出，节选）：

| 字段 | 类型 | 来源 | 状态 |
|---|---|---|---|
| `bid` | number | 配置 | **已确认** |
| `name` | string | 配置 | **已确认**（如「斗罗魂师」） |
| `desc` | string | 配置 | **已确认**（如「去周漪老师处报到」） |
| `type` | number | 配置 | **已确认**（对应 `MissionType`） |
| `lev` | number | 配置 | 已确认（如 `10020` 的 `lev=2`） |
| `realm` | number | 配置 | 已确认（字段存在） |
| `progress` | table | 配置 | **已确认**（**531/846 条非空**；键 = 合法 `mission_status`） |
| `progress_edit` / `progress_edit_2` | string | 配置 | 已确认（如 `'去{3周漪老师}处报告'`） |
| `award_assets` | table | 配置 | 已确认（如 `{1=2, 2=1290}`） |
| `commit_item` / `commit_assets` | table | 配置 | 已确认（字段存在） |
| `commit_npc_id` / `accept_npc_id` | number | 配置 | **已确认**（这是 NPC↔任务的关联点！） |
| `accept_talk` / `commit_talk` | number | 配置 | 已确认（对白 id） |
| `auto_accept` / `auto_commit` | number | 配置 | 已确认 |
| `abandon_flag` | number | 配置 | 已确认 |
| `career` / `sex` | number | 配置 | 已确认（接取限制） |
| `lev_track` / `is_track` | number | 配置 | 已确认 |
| `max_lev` / `time_limit` | number | 配置 | 已确认 |
| `loop_count` 等 | number | 配置 | 待验证 |

> **`accept_npc_id` / `commit_npc_id` 是"NPC → 任务"的关联字段**，
> 这直接回答任务书 §十二的问题：**任务与 NPC 的关联在本地配置里**
> （`Config.Mission[bid].accept_npc_id` / `.commit_npc_id`），
> 而**不是**由 NPC 条目携带 `task_id`。

---

## 三、任务状态枚举（**已确认**，原始值）

从 `mission_util.luac` 读出的 `MissionStatus`：

```
MissionStatus = { STATUS_0 = 0, STATUS_1 = 1, STATUS_2 = 2, STATUS_3 = 3 }
```

**⇒ 客户端里只有 4 个状态常量，没有"未接取/可接取/进行中/已完成/可提交/已领取"
这种六态命名。** ⇒ 任务书 §十五 要求的那套命名**在 1.4.9 客户端里不存在**，
不能自行定义（遵守"不要自己定义状态"）。

**已知的用法（Phase 4 实测）**：
- `progress` 的键 = 合法的 `mission_status`（`bid=10070` 的 `progress` 只有键 `1`；
  把 `mission_status` 设成 2 时 `prog[2] == nil`）⇒ **状态与进度表键一一对应**（**已验证**）。

`MissionType`（28 项，**已确认**）：

```
MIS_ZHU=1 MIS_FUN=2 MIS_RICHANG=3 MIS_CHENGJIU=4 MIS_ZHI=5 MIS_HUAN=6 MIS_XUAN=7
MIS_BANG=8 MIS_GUI=9 MIS_YIN=10 MIS_DAN=11 MIS_GUI_ALL=12 MIS_BAOTU=13
MIS_GUILD=14 MIS_YAO=15 MIS_TRIAL=16 MIS_HUSONG=17 MIS_MENPAI=18 MIS_YUEKA=19
MIS_NEWYEAR=20 MIS_FAVOUR=21 MIS_COUPLE=22 MIS_COLLECT=23 MIS_ZHIZUN=24
MIS_GUANGHUAN=25 MIS_HALO=26 MIS_SECRET=27 MIS_JIEYI=29
```

`MissionCode.defaultMissionId = 10000`（**已确认**）。

---

## 四、追踪栏显示用的字段（**已验证**）

```
name_label    ← sidebar_mis_item proto[12]，来自 missionContent 拼的"分类-任务名"
content_label ← vo.mis_content（由 MissionUtil.missionContent 填充）
```

---

## 五、**未确认**的字段（如实列出，不填猜测值）

| 任务书要求 | 状态 |
|---|---|
| `task_type` | 对应 `type`（**已确认**存在）；但"任务书所指的 task_type"未逐值核对 ⇒ 部分**未知** |
| `task_state` | 对应 `MissionStatus`（4 值，**已确认**）；无六态命名 ⇒ 任务书那套 **未知/不适用** |
| `target_id` / `target_count` / `current_count` / `need_count` | 协议侧对应 `target` / `target_value` / `value`（**已确认**）；配置侧 `progress` 内层结构**待验证** |
| `accept_level` | 配置侧 `lev`（**已确认**）；协议侧无 ⇒ **不适用** |
| `reward_exp` / `reward_gold` / `reward_item` | 配置侧 `award_assets`（**已确认**字段）；其**二元组含义（如 `{1=2,2=1290}` 中 2/1290 分别是什么）待验证** |
