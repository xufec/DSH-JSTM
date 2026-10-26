# 绝世唐门 1.4.9 私服 —— 剧情任务系统恢复阶段：状态报告

> 目标 APK：`anzbao/jstm.apk`
> 包名 `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**（模拟器 `127.0.0.1:16384` 实测确认）
> 本轮全部结论**只以 1.4.9 证据为准**；1.4.11 未参与任何判定。
> 环境：本地服务端 `server/mock_server.py`（TCP 9000 / HTTP 8080）+ 探针版 1.4.9 APK。

---

## 一、本轮最重要的三条结论

### 1. ★ 自动寻路**本来就是好的** —— 上一轮的"不工作"是**探针包错了对象**

上一轮探针包的是 `SceneModel.moveToNpc` / `SceneModel.moveToAutomate` /
`SceneModel.addMoveTarget` / `SceneModel.findVoTarget` / `SceneController.moveToAutomate`。

用 `tools/luac_defs.py` 还原 `mission_util.luac` 的方法表（proto#68）后确认：
`moveToNpc` / `moveToAutomate` **是 `MissionUtil` 的模块函数**，
最后一跳是 **`SceneModel:getInstance():getScene():gotoTarget(vo)`（实例方法）**。
⇒ **上一轮包的五个函数，一个都没包到点上**，所以"没有移动"的观测**不成立**。

订正探针后实测（`task_autopath_probe_result.md`）：

```
门禁  fight:false teamFollow:false convoy:false story:false xm:false fb:false sceneType:table   ← 全过
链路  moveToNpc_npc:10030_cfg_scene:10001_x:70_y:61
      gotoTarget_type:2_scene:10001_x:70_y:61_npc:10030
      SCENE.gotoTarget_type:2_scene:10001_npc:10030_pos:70_61        ← 走到最后一跳
位移  (64,56) → (68,62)  朝目标 (70,61)                                   ← ★ 真的走了
```

### 2. ★ 真正的缺口是"**目标解析不出来**"

`mission_util` proto#38 `moveToNpc(npcId)` 只有两条路：

```
① Config.MapNpc[npcId]                         → 有坐标 ⇒ 能寻路
② StoryCtrl:getInstance():getView():findSrvNpc(npcId)  → 剧情场景里的服务端 NPC
```

实测对照：

| 调用 | 结果 |
|---|---|
| `moveToNpc(10030)`（在 `Config.MapNpc`） | ✅ 命中 → 角色真的走过去 |
| `moveToNpc(20011)`（不在 `Config.MapNpc`） | ❌ `cfg_notInMapNpc` → **完全没有 `gotoTarget`** → 不动 |

### 3. ★ 缺的两张表**不在客户端 APK 里**（如实标注，不编造）

| 缺口 | 影响 | 判定 |
|---|---|---|
| **怪物摆位** | `fight_mon` 类 **38 条**主线 | `Config.Map[*].mons` 实测**全表为空** ⇒ **UNKNOWN** |
| **剧情场景编排**（20xxx 剧情 NPC 在哪张图） | **60 条**主线 | 不在 `MapNpc`/`Map`/`Drama`/`Chapter`/`Lead` ⇒ **UNKNOWN** |

⇒ 这两张表属于**原版服务端**数据。**已放弃编造**，明确标 `UNKNOWN`。

---

## 二、本轮新增的可用数据源（全部 1.4.9 APK 直读）

| 表 | 文件 | 内容 | 结果 |
|---|---|---|---|
| `Config.MapNpc` | `config_map_npc.luac` | `npc_id -> {scene_id,x,y}` | **54 个** |
| `Config.MapSceneDoors` | `config_map_npc.luac` | 场景传送图 | **18 条** |
| `Config.Map` | `config_map.luac` | 场景名/尺寸/进入点 + `npcs/mons/elems` | **124 场景** |
| `Config.Npc` | `config_npc.luac` | NPC 名字/模型/对话 | **456 个** |
| `Config.Mon` | `config_mon_data.luac` | 怪物定义（**无坐标**） | 2645 条可配平 |

**直接收益**：`story_quest_route` 里原本全为 `UNKNOWN` 的
`submit_scene_id / submit_x / submit_y / submit_npc_name`，
现在 **128/188 条主线**可给出 **CONFIRMED** 的真实值。

例（前几条主线）：

| task | name | submit_npc | NPC 名 | 场景 | 坐标 |
|---|---|---|---|---|---|
| 10010 | 斗罗魂师 | 10030 | 周漪 | 10001 史莱克城 | (70,61) |
| 10030 | 武魂觉醒 | 20011 | 少年雨浩 | 【UNKNOWN】剧情场景 | — |
| 10040 | 武魂觉醒 | 10030 | 周漪 | 10001 史莱克城 | (70,61) |
| 10080 | 先天魂力 | 10170 | — | 10001 史莱克城 | (45,47) |
| 10090 | 猎取魂环 | 10080 | — | 10001 史莱克城 | (41,22) |

---

## 三、本轮已实现并验证的服务端改动

| 改动 | 文件 | 状态 |
|---|---|---|
| `SC_10201.mons` **从写死 0 条 → 真实下发**（字段顺序取 `protocol/manual.md`） | `server/mock_server.py` | ✅ 已实现 |
| `SC_10201.elems` 真实下发 | 同上 | ✅ 已实现 |
| 任务链所需的**剧情 NPC / 目标怪物**自动进当前场景 | `server/quest_spawn.py` | ✅ 已实现 |
| 客户端**确认收到并创建**注入的 NPC | — | ✅ 实测 `addNpc id_20011 x_47 y_68` |

服务端日志：

```
★ quest_spawn scene=10001 +1 npc [20011] +1 mon [20001]
<< 10201 SCMapGird (server push) roles=1 npcs=26 mons=1 (650 bytes)
```

**坐标性质声明**：原版摆位表不在 APK 里，`quest_spawn.py` 下发的是
「以场景**声明的进入点** `Config.Map[scene].def_x/def_y` 为锚 + 黄金角错开」的
**仿真摆位**，每项带 `source='emulated'`，**不是原版坐标**。

---

## 四、稳定性与回归

| 项 | 状态 |
|---|---|
| 服务端干净重启 | ✅ `mission config loaded: 846 条` |
| 登录 / 角色列表 / 进图 / 地图 / NPC / UI | ✅ 正常（每轮构建后均复验） |
| 角色数据 | ✅ `lev_7 exp_500 gold_1000 gold_acc_5000`（**奖励确已发放**） |
| 心跳保活 | ✅ 持续 `cmd=1199` |
| 探针自动触发已**默认关闭**（`_G.__dsh_auto_probe`） | ✅ 不再干扰正常游玩 |

**构建流水线**：`pwsh tools/build_fakelogin.ps1`（注入→zipalign→签名→安装）
实测 **20 秒**，已可高频迭代。

---

## 五、交付物索引

### 分析文档（`analysis/1.4.9/task/`）

| 文件 | 内容 |
|---|---|
| `task_autopath_correction.md` | **订正**上一轮寻路结论 + 真实调用链（含 proto#8 七道门禁逐条） |
| `task_autopath_probe_result.md` | **实测证据**：门禁全过、链路全通、角色真的位移 |
| `task_story_scene_finding.md` | 剧情 NPC 为何仍寻不到路 + 剧情场景 UNKNOWN 的完整查证过程 |
| `npc_scene_position_map.md` | NPC/场景/坐标全表 + 可寻路性逐条判定 |
| `story_quest_route.md` / `.json` | 262 条主线路线（**本轮补入真实坐标**） |
| `task_dependency_graph.md` | 依赖图（线性为主 + lev 分段） |
| `task_module_inventory.md` | 任务模块清单 |
| `task_protocol_matrix.md` | 任务协议矩阵 |

### 数据文件（`analysis/1.4.9/task/`）

`map_npc.json`、`map_scene_doors.json`、`config_map.json`、`config_npc.json`、
`config_mon.json`、`config_chapter.json`

### 工具（`tools/`）

| 工具 | 作用 |
|---|---|
| `luac_defs.py` | **方法名→proto 还原**（本轮定位"包错对象"的关键） |
| `luac_callgraph.py` | 原型的"外部调用序列"提取 |
| `luac_method_map.py` | 模块方法表还原 |
| `extract_map_npc.py` / `extract_config_map.py` / `extract_config_npc.py` / `extract_config_mon.py` | 各配置表提取 |
| `extract_config_table.py` | 通用 TDUP 配置表提取 |
| `scan_apk_strings.py` | 在全部 `.luac` 字符串池里检索 |
| `apk_assets_inventory.py` / `apk_extract_luac.py` | 资产清单 / 单文件提取 |
| `build_quest_route2.py` / `build_npc_scene_map.py` | 路线与坐标表生成 |
| `build_fakelogin.ps1` | **20 秒**构建+安装流水线 |

### 服务端

`server/quest_spawn.py`（新增）、`server/mock_server.py`（`build_mons`/`build_elems`/`scene_quest_extras`）

### 备份

`backup/before_quest_restore/`（含 `ENVIRONMENT.md`、`SHA256SUMS.txt`）
`backup/before_quest_restore/phaseF_probe_state/`（订正探针前的状态 + 当时的 `http.log`）

---

## 六、★ 端到端回归（已完成，一次自包含跑通）

详见 `analysis/1.4.9/task/task_e2e_regression.md`。要点：

| 目标链环节 | 结果 | 关键证据 |
|---|---|---|
| 任务列表显示 / 恢复 | ✅ | `receive_list` 快照 + `12400 mission_list=6` |
| **自动寻路到目标** | ✅ | **`10204` 位移包轨迹 `(40,70)→(47,68)→(53,65)→(60,63)→(66,61)→(71,59)`（目标 70,61）** |
| 完成条件 | ✅ | `10020` 走 `fight_mon` 条件分支 |
| 提交 | ✅ | `12403 … code=1(TRUE)` |
| 获得**原版**奖励 | ✅ | 数额直取 `config_mission.luac` 的 `award_assets`：coin 1290→2580→3930→**5740**，exp 500→1000→1520→**2220** |
| 剧情链**自动推进** | ✅ | **连续 3 环** 10010→10030→10040，`receive_n` 7→6→5→4 |
| **重登后进度保持** | ✅ | 强杀重开后 `receive_n:6`（已完成的不再出现）、坐标 `(71,59)` 保持 |

复现：`Copy-Item analysis\_db_before_e2e.db server\state\roles.db` → `pwsh tools\build_fakelogin.ps1` → 等 ~120 秒。

### 覆盖范围（诚实交代）

| 类别 | 条数 | 状态 |
|---|---|---|
| 提交 NPC 在 `Config.MapNpc`（可自动寻路） | **128** | ✅ 全链可用 |
| 提交 NPC 为剧情 NPC（20xxx） | **60** | ⚠️ 可显示/可提交，自动寻路不可用 |
| `fight_mon` 类（需战斗结算） | **38** | ⚠️ 寻路可派发，击杀需战斗系统 |

---

## 七、下一步

| # | 事项 | 前置条件 |
|---|---|---|
| 1 | 把 60 条剧情 NPC 主线的对话/提交做成**可玩流程**（不依赖自动寻路） | 无需新数据，**可直接做** |
| 2 | `fight_mon`（38 条）：确认战斗实例（11000/11200 系列）是否纳入范围 | 需确认范围 |
| 3 | 补齐 60 条剧情 NPC 的**剧情场景**（11101 剧情负载内容） | **需原版服务端数据**（客户端 APK 无） |
| 4 | 1.4.11 交叉验证（仅找线索，不作判定依据） | 可选 |

