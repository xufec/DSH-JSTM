# Phase A —— 1.4.9 任务系统模块审计清单

> 目标 APK：`anzbao/jstm.apk` = **1.4.9** / `com.shiyue.dldl.ewan.qihoo`
> SHA-256 `4919AF2D4DA54D654D8744C0DEAD20916A50872C24582EFCF4A5768A38C97B58`
> 方法：LuaJIT 字节码反汇编（`GSET` 类名 / `RegisterProtocal` 映射 / 字段表）
> + `protocol/manual.md` + 实机 TCP 日志。
> 状态只用：**已确认 / 已验证 / 待验证 / 未知**

---

## 一、任务模块清单（`assets/src/game/mission/`，**14 个文件，共 172,985 字节**）

> 自查核对：`namelist()` 中以 `assets/src/game/mission/` 开头且 `.luac` 结尾的文件共 **14** 个
> （顶层 12 个 + `ui/` 2 个），合计 **172,985 字节**。

| 文件 | 模块 | 功能 | 是否网络 | 是否 UI | 是否配置 | 证据 |
|---|---|---|---|---|---|---|
| `game/mission/mission_ctrl.luac` (39,923) | **MissionCtrl** | 任务总控：注册 **33 条**协议、任务状态管理、接取/提交/放弃处理 | **是** | 否 | 否 | `RegisterProtocal` 映射 + `receiveHandler`/`submitHandler`/`giveUpHandler` |
| `game/mission/mission_util.luac` (68,143) | **MissionUtil** | 任务工具：`missionContent`（文案）、**`missionGoto`（自动寻路 3,588 条字节码）**、`isEdit` | 否 | 否 | 否 | `GSET MissionUtil`；`proto[0]=missionContent`、`proto[7]=missionGoto` |
| `game/mission/mission_view2.luac` (13,230) | 任务视图 | 任务列表/详情 UI、奖励展示（读 `mis_config.award_assets`） | 否 | **是** | 否 | `proto[15]` 里 `pairs(award_assets)` + `AwardItem` |
| `game/mission/mission_vo.luac` (2,916) | **MissionVo** | 任务 VO；`getConfig()` 仅 `return self.mis_config` | 否 | 否 | 否 | `proto[4]` 仅 2 条字节码（Phase 4 已验证） |
| `game/mission/mission_data2.luac` (9,794) | 任务数据层 | 任务数据分发/索引 | 否 | 否 | 否 | 引用 `defaultMissionId` |
| `game/mission/mission_contants.luac` (1,141) | 任务常量 | 状态/类型等枚举 | 否 | 否 | **是** | 与 `mission_util` 共同给出 `MissionStatus`/`MissionType` |
| `game/mission/mission_panel.luac` (1,209) | 任务面板壳 | 面板容器 | 否 | 是 | 否 | — |
| `game/mission/mission_item2.luac` (1,384) | 任务条目 | 列表单元格 | 否 | 是 | 否 | — |
| `game/mission/mission_tree_node.luac` (3,772) | 任务树节点 | 任务链树形展示 | 否 | 是 | 否 | — |
| `game/mission/mission_help.luac` (4,381) | 任务帮助 | 引导/帮助 | 否 | 是 | 否 | — |
| `game/mission/mission_asset.luac` (1,601) | 任务资源 | 图标/资源 | 否 | 是 | 否 | — |
| `game/mission/submit_goods.luac` (4,425) | 提交物品 | 交任务时选物品 | 是? | 是 | 否 | — |
| `game/mission/ui/mission_lead_list.luac` (12,832) | 任务引导列表 | 引导任务列表 | 否 | 是 | 否 | 引用 `award_assets` |
| `game/mission/ui/mission_nycollect_panel.luac` (8,234) | 采集任务面板 | 采集类任务 | 否 | 是 | 否 | — |

### 相关（非 mission 目录）

| 文件 | 模块 | 功能 | 是否网络 | 是否 UI | 是否配置 | 证据 |
|---|---|---|---|---|---|---|
| `game/sidebar/sidebar_mis_item.luac` | 任务追踪栏 | 主界面右侧两行任务条 | 否 | **是** | 否 | Phase 4 已验证：两行 = `name_label` / `content_label`（读 `mis_content`） |
| `game/sidebar/sidebar_ui.luac` | 侧边栏 | 承载追踪栏 | 否 | 是 | 否 | 引用 `defaultMissionId` |
| `game/npc/npc_mission_manager.luac` (2,388) | **NPC↔任务 关联管理** | — | 否 | 否 | 否 | `GSET`；**职责待验证** |
| `game/npc/npc_mission_vo.luac` (912) | **MNpcVo** | NPC 任务 VO | 否 | 否 | 否 | `GSET MNpcVo`；**字段待验证** |
| `game/guild/union/mission/*`（3 个） | 宗门任务 | 公会任务 | 是 | 是 | 否 | **非主线，本阶段不涉及** |
| `game/hero/hero_view/mission/*`（2 个） | 伙伴任务 | 伙伴任务 | 是 | 是 | 否 | **非主线，本阶段不涉及** |

---

## 二、任务配置文件清单（`assets/src/config/`）

| 文件 | 大小 | 内容 | 状态 |
|---|---|---|---|
| **`config_mission.luac`** | **504,437** | **`Config.Mission` 全表** | **已验证**：846 条（主线 `type=1` **262** 条）已提取到 `server/mission_config.json` |
| `config_guild_mission.luac` | 8,109 | 宗门任务 | 未分析（非主线） |
| `config_guild_mission_data.luac` | 52,150 | 宗门任务数据 | 未分析（非主线） |
| `config_holiday_order_mission.luac` | 20,367 | 节日/活动任务 | 未分析（非主线） |
| `config_adventure_mission.luac` | 459 | 冒险任务 | 未分析 |
| `config_mission_help.luac` | 1,566 | 任务帮助 | 未分析 |
| `config_mission_escort.luac` | 1,142 | 护送任务 | 未分析 |
| `config_mission_treasure.luac` | 133 | 寻宝任务 | 未分析 |
| `config_mission_kill_demon.luac` | 225 | 击杀类任务 | 未分析 |
| `config_mission_buffy.luac` / `_loop` / `_marry` | 45 × 3 | 空占位（45 字节） | 已确认是空表 |

---

## 三、`MissionCtrl` 注册的 33 条协议（**已确认**）

```
12400 12401 12402 12403 12404 12405 12406 12407 12408 12409
12412 12413 12414 12415 12416 12417 12420 12421 12422
12440 12450 12451 12452 12460 12499
15405 15420 15421 15422
18500 18501 18505
19500
```

**已查清字段的 8 条**（Phase 5D）：`12400 / 12401 / 12402 / 12403 / 12404 / 12405 / 12406 / 12416`
**其余 25 条用途 = 【未知】**（未猜）。

**处理函数名（来自 RegisterProtocal）**：
`handle12400/12401/12405`、`receiveHandler(12402)`、`submitHandler(12403)`、
`giveUpHandler(12404)`、`deleteAccessHandler(12406)`、`addAccessHandler(12407)`、
`deleteCanHandler(12408)`、`addCanHandler(12409)`

---

## 四、关键枚举与映射（均**已确认**，逐项从字节码读出）

| 名称 | 内容 | 出处 |
|---|---|---|
| `MissionStatus` | `{STATUS_0=0, STATUS_1=1, STATUS_2=2, STATUS_3=3}`（**仅 4 值，无六态命名**） | `mission_util.luac` |
| `MissionType` | 28 项（`MIS_ZHU=1` … `MIS_JIEYI=29`） | `mission_util.luac` |
| `MissionCode` | 条件码表（`fight_mon=75`、`answer=125`、`collect_elem=…` …）+ `defaultMissionId=10000` | `mission_util.luac` |
| **`AssetsEnToCode`** | **38 项** 资产名→code（`gold=1`、**`coin=2`**、`exp=4`、`gold_acc=21` …） | `config_game_data.luac` |
| `ObjType` | `{NORMAL=0, PLAYER=1, NPC=2, MONSTER=3, DOOR=4, …, ELE_Effect=100}` | `scene/element/type_state.luac` |
| **`TRUE == 1`** | **协议 `code` 语义：`==TRUE(1)` 才是成功**（否则 `message(msg)`） | `common_define.luac proto[7]` + `submitHandler` 反汇编 |

---

## 五、任务数据结构（**已确认**）

### 5.1 协议条目（`SC_12400/12401/12402/12405` 元素，**34 字节/项**）

```
mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16,
loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32,
value:u32, show_lave_time:u8, lave_time:u32, accept_time:u32
```

### 5.2 本地配置条目（`Config.Mission[bid]`，**30+ 字段**）

```
bid, name, desc, type, type2, show_type, lev, realm, career, sex,
accept_npc_id, accept_talk, commit_npc_id, commit_talk,
auto_accept, auto_commit, abandon_flag, is_drama, is_track, lev_track,
max_lev, time_limit, times_type, times_arg, team, process_talk,
commit_ty, guider_res_id, progress_edit, progress_edit_2,
progress, award_assets, commit_item, commit_career_item, commit_assets, ext
```

**★ `progress` 结构（**已确认**）**：两行 ——
`[条件名, 目标id, 数量]`（第 1 行，**这就是完成条件**）+ `[?,?,?,?]`（第 2 行，**含义未知**）。

---

## 六、本阶段（剧情任务恢复）需要补齐的（据本审计）

| # | 缺口 | 影响 | 对应 Phase |
|---|---|---|---|
| 1 | **任务前置/后继关系**（谁解锁谁） | 无法建立完整剧情路线图 | **B** |
| 2 | 任务 ↔ NPC / 地图 / 坐标 对应 | 无法自动寻路、不知去何处 | **B / F** |
| 3 | `missionGoto`（自动寻路入口）未接 | **自动寻路不工作** | **F** |
| 4 | `progress` 第 2 行含义未知 | 部分任务的提交参数不明 | B |
| 5 | `MissionCode` 条件码含义（用于判定） | 条件判定仍是替身 | E |
| 6 | 25 条未查清的协议 | 功能可能缺失 | C |
| 7 | NPC 对话 UI 未打通 | 无法从 NPC 接取 | D |
| 8 | `npc_mission_manager` / `MNpcVo` 职责未查 | NPC↔任务 关联不明 | B / D |

---

## 七、审计结论

| 项 | 结果 |
|---|---|
| 任务模块定位 | ✅ **14 个 game 文件**（172,985 字节）+ 12 个配置文件（`config_mission.luac` 504,437 字节为主） |
| 任务协议 | ✅ 33 条编号已确认；**8 条字段查清**，25 条未知 |
| 任务配置 | ✅ **846 条已提取**（主线 262），字段 30+ 全部列出 |
| 关键枚举 | ✅ 6 张表逐项读出（含 `AssetsEnToCode` 38 项、`ObjType`、`TRUE==1`） |
| 数据结构 | ✅ 协议 34 字节条目 + 配置 30+ 字段 + `progress` 两行结构 |
| **未做** | ❌ 未修改任何代码；未编造任何 ID/字段/路线 |

**⇒ Phase A 完成。下一步 Phase B（剧情任务路线图）所需的数据已基本齐备，
关键缺口是"前置/后继关系"与"任务↔NPC/地图/坐标"对应，将在 Phase B 补齐。**
