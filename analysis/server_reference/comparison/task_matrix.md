# 任务矩阵（R5）—— 五参考项目 × JSTM 任务系统对照

> **本文档闭环 `R1_SUPPLEMENT.md` §六 未做项 ②「`comparison/` 其余矩阵未单独出文件 → `task_matrix`」。**
> 依据：`jstm_1.4.9/task_protocol.md`（39 条 CMD，源自 `protocol/fields.json`）+ `analysis/1.4.9/task/task_data_model.md`（`MissionStatus`/`MissionType` 原始值）
> + **`server/mock_server.py` 实测**（29 处 `mission_status` 使用点）+ 各项目逐文件报告。
> 标注：【已确认】/【待验证】/【未知】；未读到的一律写「未读到」。
> **本文件只读，未修改 `server/` 任何文件。**
>
> ⚠ **时效声明**：JSTM 侧**行号**取自本次读取快照（`mock_server.py` 当时正被其他 agent 活跃开发）。
> 引用请以"表名 / 函数名 / SQL 原文"二次定位；**结论级事实（4 态语义、13 列、39 CMD）不受行号漂移影响**。

---

## 一、结论速览（6 方对照）

| 维度 | **Survive** | **YZXY / CXEngine** | **大圣归来** | **侠客行** | **空空西游** | **JSTM 现状** |
|---|---|---|---|---|---|---|
| 任务系统存在性 | ⚠ 有 `everydaytask.lua`（**仅日常任务**） | ❓ **`addon/quest.lua` 从未被读过**（见 §七） | ❌ **完全没有** | ✅ 完整（4 态 + 3 类 + 11 模板） | ✅ **完整**（`domain/task/*.js` 4 文件） | ✅ **已实现**（`missions` 表 + 8/39 CMD） |
| 状态机 | ❌ 无显式状态（`{lastreset,tasks}`） | ❓ 未读到 | ❌ 无 | ✅ **4 态** `NS_FREE/NS_HTASK/NS_WSTASK/NS_STASK` | ✅ **4 态** `NOT_START/NOT_COMPLETED/NOT_DELIVERY/COMPLETED` | ✅ **4 值** `mission_status 0/1/2/3` |
| 任务类型 | `{type,counter,awarded}`（无枚举） | ❓ 未读到 | ❌ 无 | ✅ **3 类** `T_KILL 2001/T_COLLECT 2002/T_ACCESS 2003` | ✅ **3 类** `KILL_MOB/COLLECT/TALK_NPC` | ⚠ **28 类** `MissionType`（业务分类，**不同维度**） |
| 进度模型 | 计数器 `counter` | ❓ 未读到 | ❌ 无 | `curschedule/allschedule` | `updateTaskData`/`updateCollectTaskData` | `target/target_value/value` + `loop_count/loop_num` |
| 任务定义来源 | **硬编码在 lua** | ❓ 未读到 | ❌ 无 | **客户端本地 `Task<N>.tsk`** | `config/data/*.json` 策划表 | **配置表 `Config.Mission`**（846 条） |
| 定义是否落库 | ❌ 否 | ❓ | — | ❌ 否 | ✅ **是**（DAO+策划表） | ❌ 否（配置 = `mission_config.json`，**正确**） |
| 进度是否落库 | ✅ 是（JSON in hash） | ❓ | — | ❌ **否**（纯内存） | ✅ 是（`taskDao.tasksUpdate`） | ✅ **是**（`missions` 表） |
| 权威方 | 服务端 | ❓ | — | ⛔ **客户端**（随机生成 + 本地发奖） | **服务端** | **服务端** |
| 是否有任务链 | ❌ | ❓ | — | ❌（随机独立任务） | ✅ 主线/支线（`taskMain`） | ✅ **有**（`mission_chain` + `mission_chain_max`） |
| 限时任务 | ❌ | ❓ | — | ❌ | ❓ | ⚠ **协议有 2 字段，表里未存**（见 §六 G3） |

---

## 二、JSTM 任务模型（★ 权威定义，全部【已确认】）

### 2.1 `missions` 表（13 列）↔ `SC_12400.mission_list`（13 字段）逐列对照

| # | `missions` 表列（`mock_server.py:1573-1579`） | `SC_12400` 协议字段（`task_data_model.md` §一） | 语义 | 是否对齐 |
|---|---|---|---|---|
| 1 | `rid` | — | 角色主键（**DB 内部列**） | ✅ 合理新增 |
| 2 | `mission_bid` | `mission_bid` u32 | 任务 id（`Config.Mission[bid]`） | ✅ |
| 3 | `mission_status` | `mission_status` u8 | **任务状态 0/1/2/3** | ✅ |
| 4 | `process_status` | `process_status` u8 | 处理状态（0 进行中 / 1 已完成） | ✅ |
| 5 | `target` | `target` u32 | 目标 id | ✅ |
| 6 | `target_value` | `target_value` u32 | 目标数量 | ✅ |
| 7 | `value` | `value` u32 | 当前值 | ✅ |
| 8 | `commit_num` | `commit_num` u16 | 已提交次数 | ✅ |
| 9 | `loop_count` | `loop_count` u16 | 循环计数 | ✅ |
| 10 | `loop_num` | `loop_num` u16 | 当前轮次 | ✅ |
| 11 | `code` | `code` u8 | 任务码 | ✅ |
| 12 | `accept_time` | `accept_time` u32 | 接取时间 | ✅ |
| 13 | `updated_at` | — | 落库时间（**DB 内部列**） | ✅ 合理新增 |
| — | **（缺）** | `show_lave_time` u8 | 是否显示剩余时间 | ❌ **未存** |
| — | **（缺）** | `lave_time` u32 | 剩余时间 | ❌ **未存** |

**⇒ 【已确认】11/13 协议字段已落库；`show_lave_time` / `lave_time` 两个限时字段缺失** ⇒ **限时任务（`Config.Mission.time_limit`）无法支撑**（见 §六 G3）。

### 2.2 `mission_status` 的实际语义（★ 由 `mock_server.py` 29 处使用点反推）

| 值 | 语义 | 代码证据 | 对应参考项目命名 |
|---|---|---|---|
| **0** | **已下发但未开始**（玩家可见、未进行） | `:1906` `{'mission_bid':b, 'mission_status':0, ...}` 插入可接取任务 | 空空西游 `NOT_START`；侠客行"可接取" |
| **1** | **进行中** | `:760` 创建时默认 `1`；`:2021` `db_save_mission(..., {'mission_status':1})`；`:1862/1864` 未完成时保持 `1` | 空空西游 `NOT_COMPLETED`；侠客行 `NS_WSTASK`（已接未完成） |
| **2** | **进行中且条件已满足（可提交）** | `:1864` `'mission_status': 2 if done else ...`；`:2011/2017/4233` `db_save_mission(..., {'mission_status':2})` | 空空西游 `NOT_DELIVERY`；**侠客行 `NS_STASK`（可提交）** |
| **3** | **已提交/完成** | `:1684` `if int(m.get('mission_status') or 0) == 3` 收集已完成集合；`:1916-1919` `mission_rows(include_done=False)` **默认排除 `status=3`** | 空空西游 `COMPLETED`；侠客行"提交即从 `m_pickedupTask` erase" |

**★ 任务链推进（【已确认】）**：
`mission_chain(cfg, rid)`（`:1667-1684`）的注释写得很清楚：
> 「**解锁指针** = 链上第一个"未完成（`mission_status != 3`）"的位置；只从指针处**往下发 `mission_chain_max` 条**」

`mission_chain_max` 默认 `8`（`:1678`），而 `server/config.json` 设为 **`1`**，并附注：
> 「`=1` 只下发链头：剧情链是**线性**的，同名任务（如「武魂觉醒」×6）同时下发会导致任务栏重复。
> 依据：实测 7 条里 6 条同名。若要展示更多，应走 12407/12408/12409 的「可接取列表」而不是塞进 12400 的「已接取列表」。」
⇒ **【已确认】JSTM 已有"链头指针 + 线性链"的推进模型**，且**已用实测数据（7 条里 6 条同名）驱动过决策**。

### 2.3 `MissionType`：JSTM 的 28 类**不是**参考项目的"3 类"

```lua
MIS_ZHU=1 MIS_FUN=2 MIS_RICHANG=3 MIS_CHENGJIU=4 MIS_ZHI=5 MIS_HUAN=6 MIS_XUAN=7
MIS_BANG=8 MIS_GUI=9 MIS_YIN=10 MIS_DAN=11 MIS_GUI_ALL=12 MIS_BAOTU=13 MIS_GUILD=14
MIS_YAO=15 MIS_TRIAL=16 MIS_HUSONG=17 MIS_MENPAI=18 MIS_YUEKA=19 MIS_NEWYEAR=20
MIS_FAVOUR=21 MIS_COUPLE=22 MIS_COLLECT=23 MIS_ZHIZUN=24 MIS_GUANGHUAN=25
MIS_HALO=26 MIS_SECRET=27 MIS_JIEYI=29        -- 共 28 项，无 28
```

**⇒ ★ 关键区分（本矩阵最重要的判断）**：

| 概念 | JSTM | 参考项目 | 关系 |
|---|---|---|---|
| `MissionType`（28 类） | **业务分类**：主线/支线/日常/成就/帮派/宝图/公会/试炼/护送/门派/月卡/新年/情缘/夫妻/收集/至尊/光环/魂环/秘境/结义… | —— 参考项目**没有**这个维度 | **JSTM 独有，参考项目帮不上忙** |
| 参考项目的 `TaskType`（3 类） | **完全不存在此维度**；其职责被 `process_status` + `progress` 表承担 | 侠客行 `T_KILL/T_COLLECT/T_ACCESS`；空空西游 `KILL_MOB/COLLECT/TALK_NPC` | **⇒ 3 类 ≈ JSTM 的"进度计算方式"**，应映射到 `Config.Mission[bid].progress` 的结构，而**不是** `MissionType` |

> **⇒ 纠正一处可能的误用**：`FINAL_SERVER_ARCHITECTURE.md` / `architecture_matrix.md` 把"任务参考"指向
> 「**CXEngine `addon/quest`** 的**目标类型**」—— 但（a）`quest.lua` **从未被读过**（§七），
> （b）"目标类型（击杀/收集/对话）"这个维度在 JSTM 里由 **`progress` 表**承担，**与 `MissionType` 无关**。
> ⇒ **该指引引用了一个未读文件，且维度对错位**，应改为指向 **空空西游 `domain/task/*.js`**（已读、已确认同构，见 §三）。

---

## 三、★★ 4 态收敛：三个独立项目得出同一模型

| 项目 | 状态常量（原文） | 值 | 与 JSTM `mission_status` 的对应 |
|---|---|---|---|
| **JSTM 1.4.9**（客户端原始值） | `MissionStatus = { STATUS_0=0, STATUS_1=1, STATUS_2=2, STATUS_3=3 }`（`mission_util.luac`） | 0/1/2/3 | **基准**（客户端只认这 4 个，无六态命名） |
| **空空西游** | `TaskState{ NOT_START, NOT_COMPLETED, NOT_DELIVERY, COMPLETED }`（`app/domain/task/task.js`） | 0/1/2/3 | **★ 1:1 同名同构** |
| **侠客行** | `NS_FREE 3001` / `NS_HTASK 3002` / `NS_WSTASK 3003` / `NS_STASK 3004` | 4 值 | 3002↔0（可接取）、3003↔1（已接未完成）、3004↔2（可提交）；3001 = 无任务（**不在 `mission_status` 域内**） |
| Survive | 无显式状态（`{type,counter,awarded}`） | — | 无法对应 |

**★ 结论（本矩阵最高价值的一条）**：
**三个互相独立的项目（JSTM 原客户端、空空西游、侠客行）都收敛到"4 态"**，
且**空空西游的 `TaskState` 与 JSTM 的 `mission_status 0/1/2/3` 是 1:1 同构**。
⇒ **JSTM 不需要自行发明状态命名**（`task_data_model.md` §三 已明确"客户端只有 4 个状态常量，不能自行定义"），
**可直接借用空空西游的 4 个语义名（未开始 / 未完成 / 未交付 / 已完成）作为服务端内部的文档化命名**，
再用 `analysis/1.4.9/task/` 的实测把每个值的**触发条件**钉死。

**⚠ 侠客行的差异（必须注意）**：它的 `NS_FREE`（无任务）是**第 5 个位置**，
对应 JSTM 的**"行不存在"**而非 `mission_status=0`。
⇒ 若照搬侠客行做映射，会把"无任务"与"可接取"混为一谈 ⇒ **JSTM 应保持"行不存在 = 无任务、`status=0` = 已下发可接取"的二分**。

---

## 四、★★ 3 类型收敛

| 项目 | 类型枚举（原文） | 进度更新入口 | 是否有服务端权威 |
|---|---|---|---|
| **空空西游** | `TaskType{ KILL_MOB, COLLECT, TALK_NPC }` | `updateTaskData`（击杀）/ `updateCollectTaskData`（收集）；`mob.js` 也有 `updateTaskData` | ✅ 服务端（`taskDao.tasksUpdate`） |
| **侠客行** | `T_KILL 2001` / `T_COLLECT 2002` / `T_ACCESS 2003`；**`T_COLLECT` 在 11 个模板中使用 0 次** | `checkKillMonster`（**唯一入口**，由 `Monster.cpp:114` 触发）；`T_ACCESS` 靠 `.tsk` 自带 `curschedule 1 / allschedule 1` **接即完成** | ⛔ **客户端** |
| 大圣归来 | ❌ 无任务系统 | — | — |
| Survive | ❌ 无枚举（`{type,counter,awarded}`） | `OnEvent` 里直接 `counter++` | 服务端 |

**★ 结论**：
1. **两个独立项目同样收敛到"击杀 / 收集 / 对话（访问）"三类** ⇒ 这是 MMORPG 任务进度的**最小完备集**。
2. **侠客行的 `T_COLLECT` 是"声明未用"的**（0/11 模板）⇒ 它的"3 类"是**设计意图**而非**已验证的实现**；
   **空空西游的三类都有 `updateXxxTaskData` 实现** ⇒ **`COLLECT` 这类应以空空西游为准**。
3. **对 JSTM 的落地建议**：三类不应新增到 `MissionType`（28 类里已有 `MIS_COLLECT=23`，语义不同），
   而应作为 **`Config.Mission[bid].progress` 的"计算方式"标注**，驱动服务端的进度判定分支。

---

## 五、逐项目任务证据（5 列表格）

> 格式：`文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因`

### 5.1 空空西游（★ 本矩阵的最佳任务参考）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `app/domain/task/task.js` | `TaskState{NOT_START/NOT_COMPLETED/NOT_DELIVERY/COMPLETED}` | **4 态枚举** | **★ 强适合** | 与 JSTM `mission_status 0/1/2/3` **1:1 同构**，可直接作为服务端内部命名与校验依据 |
| `app/domain/task/task.js` | `TaskType{KILL_MOB/COLLECT/TALK_NPC}` | **3 类枚举** | **★ 强适合** | 与侠客行独立收敛 ⇒ 可作为 JSTM `progress` 计算方式的最小集 |
| `app/domain/task/task.js` | `updateTaskData` / `updateCollectTaskData` | **按类型分派的进度更新** | **★ 强适合** | JSTM 目前按 `target/target_value/value` 通用更新 ⇒ 可参考其"类型→更新函数"的分派结构（**结构可学，代码不可抄**） |
| `app/domain/task/{taskMain,taskReward,tasks}.js` | 主线 / 奖励 / 任务集合 | 主线与支线分层 + 独立奖励模块 | 适合 | JSTM 的 `mission_chain` 只做了"线性链头"，未分主线/支线 ⇒ 可参考其分层 |
| `app/dao/...taskDao.js` | `tasksUpdate(player.curTasks)` | **玩家下线时批量落库任务**（配合 pomelo-sync 脏刷） | **★ 强适合** | ★ 与 `database_matrix` G6 同源：JSTM 当前"每改一次就 commit"，应改为**下线/定时批量落库** |
| `app/domain/entity/mob.js` | `updateTaskData` / `getKillExp` / `dropItem` | **怪物侧主动上报任务进度**（而非任务系统主动查询） | 适合 | ★ **"击杀事件 → 任务进度"由怪物侧触发**，与侠客行 `Monster.cpp:114 → checkKillMonster` **同一模式** ⇒ 两项目收敛，值得 JSTM 采用 |

### 5.2 侠客行（★ 4 态 + 3 类的第二个独立样本；但权威模型是反例）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/PreProcess.h:115-118` | `T_KILL 2001` / `T_COLLECT 2002` / `T_ACCESS 2003` | 3 类任务宏 | 适合（枚举） | 与空空西游收敛；**JSTM 应放 `progress` 而非 `MissionType`** |
| `Classes/PreProcess.h:121-124` | `NS_FREE 3001` / `NS_HTASK 3002` / `NS_WSTASK 3003` / `NS_STASK 3004` | 4 态 NPC 状态宏 | 适合（枚举） | 3002/3003/3004 ↔ JSTM 0/1/2；**3001 应对应"无行"**，⚠ 不要与 `status=0` 混淆 |
| `Classes/TaskSystem.h:14-26` | `struct TaskInfo` | 10 字段：`name/fromwho/destwho/schedulewho/glodreward/expreward/index/curschedule/allschedule/type` | **适合（字段语义）** | ★ `curschedule/allschedule` ↔ JSTM `value/target_value`；`type` ↔ progress 计算方式；**`fromwho/destwho` 是 JSTM `accept_npc_id/commit_npc_id` 的对照** |
| `Resources/Task/Task1..11.tsk` | 11 个任务模板（**已全部实读**） | 8 键：`name/schedulewho/glodreward/expreward/index/curschedule/allschedule/type` | **★ 适合（数值样本）** | ★ `Task1..10` 的 `schedulewho` **恰好是 10 个怪物名一一对应** ⇒ 可作为 JSTM 前 10 级新手任务的数值对照（奖励 500~1000 金币 / 550~800 经验） |
| `Resources/Task/{EndTask,NoEndTask}.tk` | — | **任务三态对话文本**（接取/未完成/可提交） | **★ 适合** | ★ **"任务状态 ↔ 对话文本"一一对应**；JSTM 的 `Config.Mission.accept_talk/commit_talk` 已有对白 id ⇒ 可参考其"每态一段对话"的组织方式 |
| `Classes/TaskSystem.cpp:110-122` | `pickupTask(index)` | `m_missedTask` → `m_pickedupTask` 迁移 | 适合（流程） | 接取的状态迁移最小实现；JSTM 对应 `mission_status 0→1` |
| `Classes/TaskSystem.cpp:124-140` | `submitTask(node,index)` | `addGlod` + `addExp` + 提示 + erase | ⛔ **不适合** | 🔴 **奖励在客户端内存结算**；且**不校验 `curschedule >= allschedule`**（D-3） |
| `Classes/TaskSystem.cpp:154-172` | `havePickedupTask(name)` | **用返回值符号位编码三态**：`+index`=可提交 / `-index`=未完成 / `0`=无 | ⚠ 部分 | 巧思但可读性差；**JSTM 用 `mission_status` 显式表达更清晰** |
| `Classes/TaskSystem.cpp:174-184` | `checkKillMonster(name)` | `schedulewho == name` 则 `curschedule++`；**不判 `type`、不封顶** | ⚠ 反面 | ★ **"击杀事件 → 任务进度"的触发模式对**（与空空西游 `mob.js` 一致）；**但通配匹配会造成类型间进度交叉污染**（D-2） |
| `Classes/TaskSystem.cpp:52-63` | `workThread()` | 后台线程每 **15 秒** `createTask()`（`rand()%11+1` 随机取模板） | ⛔ **不适合** | 🔴 **任务由客户端随机生成** ⇒ 服务端无法校验、不可运营 |
| `Classes/TaskSystem.cpp:101-102` | `createTask()` 尾部 | `fromwho/destwho` 由 `m_npcvec[rand()%4]` **随机指定，不来自 `.tsk`** | ⛔ **不适合** | 🔴 与 JSTM 的 `Config.Mission.accept_npc_id/commit_npc_id`**正好相反**：JSTM 把 NPC 关联固化在配置里（**正确**），侠客行随机 |
| `Classes/TaskSystem.h:104-109` | `m_missedTask`/`m_pickedupTask`/`m_taskindexs` | 3 个内存容器；**`#include<mutex>` 但无 mutex 成员** ⇒ 无锁数据竞争（D-4） | ⛔ | 工作线程与主线程并发读写无保护 |
| `Classes/TaskLayer.cpp:26-41` | `initTaskItem(basePos)` | 面板数据 = `TaskSystem::getPickedupTask()`；**最多 7 条**（`index > 6` return） | 适合（布局约束） | ★ JSTM 的 `mission_chain_max` = 1（避免同名重复），侠客行是"最多 7 条" ⇒ 两者都在解决**面板容量**问题 |
| `Classes/TaskItem.cpp:21-81` | `TaskItem::init(tinfo)` | 渲染：名 / `Process:curschedule/allschedule` / `DestMen:<提交人>` / `Kill\|Collect\|Access + 目标名` / `Glod` / `Exp` | **★ 适合（字段清单）** | ★ **任务详情面板的 6 要素**，可直接对照 JSTM `SC_12400` 的 11 字段做 UI 字段取舍 |

### 5.3 Survive（仅日常任务）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `groupserver/everydaytask.lua` | `DbStr/DbSave` | `{lastreset, tasks={[i]={type,counter,awarded}}}` → JSON 存 hash | ⚠ 部分 | 有 `type/counter/awarded`（**进度 + 已领奖标记**）三要素，语义等价 JSTM 的 `value/target_value` + "已领取"；**无状态机** |
| `groupserver/everydaytask.lua` | `CheckReset` | 跨天/跨月重置 | 适合 | ★ JSTM 有大量"日常/周常"任务（`MissionType` 含 `MIS_RICHANG=3`）⇒ **跨天重置**可直接参考其"lastreset 时间戳 + 比对"的做法 |
| `groupserver/everydaytask.lua` | `DbSave()` | **每次 `OnEvent` 都写库** | ⛔ 不适合 | 高频事件打爆 DB ⇒ JSTM 用 `missions` 表时**必须**内存累积 + 定时 flush（与 `database_matrix` G6 同一结论） |
| `groupserver/*` | — | ❌ **无主线/支线任务** | — | Survive **不能作为任务系统参考**（只有日常） |

### 5.4 大圣归来（无任务系统）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Server/gametable.sql` | — | **只有 1 张 `game` 表，无任务表** | ⛔ | 数据层不支撑任务 |
| `Server/游戏服务器/Form1.cs` | `manipulationData` | 8 个分支中**无任何任务消息** | ⛔ | 网络层不支撑任务 |
| （客户端） | — | 无任务相关类；`Player.h` 只有 `state{FREE,WALK,ATTACK,DEAD}` | ⛔ | 表现层不支撑任务 |
| **⇒ 结论** | — | **大圣归来在任务维度信息量为 0**，仅可作为"任务表设计失败的反面"（它连表都没有） | ⛔ | — |

### 5.5 YZXY / CXEngine（⚠ 关键文件未读）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `scripts/client/addon/quest.lua` | **（未读到）** | —— | **【未读到】** | 🔴 **`yzxy/architecture.md:214` 与 `yzxy/lua_server.md:422` 均明确记录该文件"仅读到片段/未读"** ⇒ **任何基于它的结论都不是取证结论** |
| `scripts/client/addon_manager.lua` | 加载 `addon/*` | 插件式装载 bag/props/battle/quest/options/action/hud | 适合（架构） | 「addon 按功能插件化」的结构可借鉴，**但 quest 内部实现未知** |
| `common/src/file_loading.cpp` | `FileLoadingThread::PostTask` | 异步加载任务表（同路径去重 + 主线程轮询状态） | 适合 | ★ 仅与"任务**配置表加载**"有关，与任务**逻辑**无关 |

---

## 六、逐字段映射：JSTM `missions` 列 ← 参考项目字段

| JSTM 列 | 侠客行 `TaskInfo` | 空空西游 | Survive | 建议 |
|---|---|---|---|---|
| `mission_bid` | `index` | `task.bid` | `[i]` 下标 | 保持 `bid`（JSTM 用 `Config.Mission` 的 846 条 bid） |
| `mission_status` | `NS_HTASK/NS_WSTASK/NS_STASK`（三态） | `TaskState`（4 态） | ❌ 无 | **★ 以空空西游 4 态为语义基准**；`mission_status=0` ≠ 侠客行 `NS_FREE` |
| `process_status` | ❌ 无 | ❌ 无 | `awarded`（是否已领奖） | ⚠ **JSTM 独有**；已实现为"0 进行中 / 1 已完成"（`:1862`）⇒ 与 `mission_status=2` 语义重叠，**建议明确二者边界**（见 G2） |
| `target` | `schedulewho`（**字符串名**） | 目标 id | `type` | JSTM 用 `uint32` 目标 id ⇒ **优于**侠客行的字符串匹配（侠客行的通配匹配造成交叉污染 D-2） |
| `target_value` | `allschedule` | ❌（隐含） | ❌ | ✅ 一致 |
| `value` | `curschedule` | `counter` | `counter` | ✅ 一致 |
| `commit_num` | ❌ | ❌ | ❌ | JSTM 独有（多次提交类任务） |
| `loop_count` / `loop_num` | ❌ | ❌ | ❌ | JSTM 独有（循环任务） |
| `code` | ❌ | ❌ | ❌ | ⚠ **`code` 语义未核对**（见 §八） |
| `accept_time` | ❌ | ❌ | `lastreset`（部分） | JSTM 独有 |
| `updated_at` | ❌ | ❌ | ❌ | JSTM 独有（好） |
| **（缺）`show_lave_time`/`lave_time`** | ❌ | ❌ | ❌ | **参考项目均无限时任务** ⇒ 只能按 `Config.Mission.time_limit` 自研（G3） |
| — 接取 NPC | `fromwho`（**随机**） | `accept_npc_id`（配置） | ❌ | **★ 以 JSTM `Config.Mission.accept_npc_id` 为准**（配置固化，正确） |
| — 交付 NPC | `destwho`（**随机**） | `commit_npc_id`（配置） | ❌ | **★ 同上** |
| — 任务类型 | `type`（3 类） | `TaskType`（3 类） | `type` | **★ 须落到 `progress` 计算方式，不是 `MissionType`** |

---

## 七、★ 五项目任务能力缺口（对 JSTM）

| # | 缺口 | 现状证据 | 参考依据 | 建议 | 优先级 |
|---|---|---|---|---|---|
| **G1** | **`mission_status` 只有 4 值，但 `MissionType` 有 28 类**，两者关系未文档化 | `task_data_model.md` §三（4 值已确认）；§二（28 类已确认） | 空空西游 `TaskState`×`TaskType` 两维正交 | 明确 **`MissionType` = 业务分类（28）、`progress` 计算方式 = 进度类型（≥3）** 两个**正交维度**，写进文档避免误用 | **P0（文档级）** |
| **G2** | `process_status` 与 `mission_status=2` 语义重叠 | `:1862` `'process_status':1 if done` + `:1864` `'mission_status':2 if done` ⇒ **同一条件同时改两列** | 侠客行 `NS_STASK` 单值表达"可提交"；空空西游 `NOT_DELIVERY` | 二选一：①`process_status` 改为"进度子状态"（如 目标是否全部命中/是否需要额外条件）；②保留但**文档化**两者边界 | **P0** |
| **G3** | **限时任务字段未落库** | `missions` 13 列**无** `show_lave_time`/`lave_time`；`Config.Mission.time_limit` 字段**已确认存在** | **参考项目均无限时任务** ⇒ 无参照 | 补两列；服务端在 `mission_rows` 计算剩余时间 | **P1** |
| **G4** | 任务进度"每改一次即 commit" | 29 处 `db_save_mission` 调用，每处独立 `commit` | ★ 空空西游 `taskDao.tasksUpdate`（下线批量）+ pomelo-sync 脏刷 | 与 `database_matrix` G6 合并：`dirty_registry` + 定时 flush | **P1** |
| **G5** | 未分主线/支线（只有线性链） | `mission_chain` 单链 + `mission_chain_max` | 空空西游 `taskMain` 与 `tasks` 分层；`MissionType` 含 `MIS_ZHU=1`（主线）`MIS_FUN=2`（支线） | 按 `MissionType` 分链 | P2 |
| **G6** | 无日常/周常重置 | 无 `lastreset` 类字段 | ★ Survive `everydaytask.CheckReset`（跨天重置） | 加 `daily_mission(rid, bid, progress, last_reset)` 或在 `missions` 上加重置字段；`MissionType` 含 `MIS_RICHANG=3` | P2 |
| **G7** | 39 条任务 CMD 只实现 8 条 | `task_protocol.md`：✅ 12400/12401/12402/12403/12407/12408/12409/12421 | — | 按真机实测优先级（只有 12400/12403/12409 真机发过）推进 | P2 |
| **G8** | 无可接取列表的独立通道 | `config.json` `mission_accept_max=6` + `mission_accept_note` 已说明要用 12407/12409 | 侠客行 `PickupTaskLayer`（接取面板只持 NPC 指针）；空空西游 `getWatcherUids` | 12407/12409 已实现 ⇒ 补真机验证 | P2 |

---

## 八、★ 一处必须更正的指引（R5）

| 位置 | 原文 | 问题 | 更正为 |
|---|---|---|---|
| `FINAL_SERVER_ARCHITECTURE.md` §四「任务 参考谁」 | 「任务 \| **CXEngine `addon/quest`** + **空空西游 `taskHandler`**」 | ① `scripts/client/addon/quest.lua` **从未被读过**（`yzxy/architecture.md:214`、`yzxy/lua_server.md:422` 均记录"未读"）⇒ **不是取证结论**；② `addon/quest` 的维度是"**目标类型**（击杀/收集/对话）"，而 JSTM 里该维度由 **`Config.Mission[bid].progress`** 承担，**与 `MissionType`（28 类业务分类）无关** | 「任务 \| **空空西游 `app/domain/task/*.js`（4 态 `TaskState` + 3 类 `TaskType`，已读且与 JSTM `mission_status 0/1/2/3` 同构）** + **侠客行 `TaskSystem`（作业为第二个独立 4 态样本与 11 模板数值）**；**CXEngine `addon/quest` 因未读，降级为【未知】，不作指引**」 |
| `comparison/architecture_matrix.md` 任务行 | 「可对照 CXEngine addon/quest 的目标类型」 | 同上 | 同上 |

**⇒ 这条更正的实质**：**原指引引用的参考项既未取证、维度也错位**；而真正同构、已取证的最佳参考是**空空西游的任务模块**（4 态同名 + 3 类同构 + 怪侧上报 + 下线批量落库）。

---

## 九、【待验证】/【未知】

| 项 | 状态 |
|---|---|
| `missions.code` 的语义 | 【待验证】与 `mission_status`/`process_status` 的职责划分未核对（`database_matrix` §七 亦记为待验证） |
| `Config.Mission[bid].progress` 的内层结构（`{1=..., 3=...}` 的键值语义） | 【待验证】`task_data_model.md` §二 已确认"键 = 合法 `mission_status`"、"531/846 条非空"，但**内层字段未解** |
| JSTM 28 个 `MissionType` 各自是否已实现 | 【未读到】`mock_server.py` 只见 `mission_chain`/`mission_rows` 通用逻辑，未见按 `MissionType` 分派 |
| `award_assets` 二元的含义（如 `{1=2, 2=1290}` 中 2/1290） | 【待验证】`task_data_model.md` §五 明确标为待验证 |
| 空空西游 `taskReward.js` 的奖励发放是否服务端事务 | 【未读到】只确认文件存在 |
| 侠客行服务端（CM-Server）的任务实现 | 【未读到】不在 ZIP |
| YZXY `addon/quest.lua` | 【未读到】**关键缺口**；若将来拿到该文件，本矩阵 §五.5 与 §八 需重评 |
| Survive 是否有主线任务（仅确认 `everydaytask.lua`） | 【待验证】未穷举 `groupserver/` |

---

## 十、一句话结论

> **JSTM 的任务系统在"数据模型"上已经领先 5 个参考项目**（4 态 `mission_status` + 13 列表 + 11/13 协议字段 + 服务端权威 + 线性链 + `mission_chain_max` 的实测驱动决策）。
>
> **它的 4 态与空空西游的 `TaskState` 是 1:1 同构，与侠客行的三态（+无任务）部分同构** ——
> **三个独立项目收敛到"4 态"，说明这不是设计偏好而是 MMORPG 任务的客观最小集**，
> 因此 JSTM **不应再自行发明状态命名**（`task_data_model.md` §三 的约束是对的）。
>
> **真正该做的三件事**：①**把 `MissionType`（28 类业务分类）与"进度类型"（3 类：击杀/收集/对话）明确为正交两维**并文档化；
> ②**澄清 `process_status` 与 `mission_status=2` 的语义重叠**；③**把任务进度从"每改即 commit"改为脏标记 + 定时/下线批量落库**（与 `database_matrix` G6 同源，唯一正面样本是**空空西游的 `taskDao.tasksUpdate` + pomelo-sync**）。
>
> **并纠正一处集成指引**：`FINAL_SERVER_ARCHITECTURE.md` 把任务参考指向 **CXEngine `addon/quest`** ——
> 该文件**从未被任何审计读过**，且其"目标类型"维度与 JSTM 的 `MissionType` **对不上**；
> 应改为指向 **空空西游 `app/domain/task/*.js`**（已读、同构）与 **侠客行 `TaskSystem`**（第二个 4 态样本 + 11 个任务模板数值）。
