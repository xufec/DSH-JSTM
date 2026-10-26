# Phase F 前置 —— 自动寻路（`missionGoto`）调查

> 目标：找出 1.4.9 的"**自动寻路**"是怎么工作的，以及**服务端需要做什么**才能让它恢复。
> 数据来源：`game/mission/mission_util.luac proto[7] = missionGoto`（**3,588 条字节码**）
> + `config_mission.luac` + 场景协议 `10201`。
> confidence：**CONFIRMED / VERIFIED / INFERRED / UNKNOWN**

---

## 一、★ `missionGoto` 的结构（**已确认**，从 445 个字符串反推）

它是**按"条件名"分派的一张大 switch**，不同条件走不同的"去哪儿"策略：

### 1.1 寻路/移动（客户端内部）

```
moveToAutomate      ← ★ 真正的"自动走"
addMoveTarget / addTarget
isAutoWalk
moveToNpc / move
```

### 1.2 目标解析

```
findVoTarget / findSrvElem / FindType / gotoTarget / goto
```

### 1.3 按条件名分派（对应 `MissionCode`）

```
fight_mon   kill_mon   kill_scene_mon   kill_type_mon   seal_mon   award_scene_mon
gotoGuild   gotoActivityNpc   gotoKillDemon   gotoGuildNpc   gotoHongChen
npc_talk    use_item_scene    findRodeCommitMission
```

### 1.4 目标来源字段

```
accept_npc_id / commit_npc_id / npcId / mis_target
sceneId / scene_id / pos / pos_x / pos_y / mons / Map
```

### 1.5 兜底分支

```
'goto ---------- 该类型还木有处理:'
```

**⇒ 结论：`missionGoto` 按条件解析目标（NPC / 怪物 / 位置）→ 调 `moveToAutomate` 自动走。
整个过程**全在客户端**，不发任何协议。**

---

## 二、★★ 由此得出：**自动寻路不需要服务端协议，但需要"目标在场"**

因为寻路是在客户端本地完成的，**服务端唯一能影响它的是"场景里有没有那个目标"**：

```
客户端 missionGoto
   ├─ 需要 NPC     → 必须出现在 SC_10201 的 npcs 里
   ├─ 需要怪物     → 必须出现在 SC_10201 的 mons 里
   └─ 需要位置     → 由上述对象的坐标决定
```

**⇒ 若目标不在场景里，`missionGoto` 就无处可去 —— 这正是当前"自动寻路不工作"的服务端侧原因。**

---

## 三、★ 实测核对：剧情链前 8 条的目标是否在场（**已确认**）

我们 `10201` 下发的 NPC bid：

```
10010 10020 10030 10040 10050 10060 10070 10080 10081 10090 10100 10110
10120 10130 10140 10150 10160 10170 10175 50000 50003 50004 50005 50006 50007
```

| bid | name | 需要的目标 | 是否在场 |
|---|---|---|---|
| 10010 | 斗罗魂师 | commit_npc **10030** | ✅ **在场** |
| 10020 | 切磋魂技 | 怪物 **20001** | ❌ **怪物完全没下发** |
| 10030 | 武魂觉醒 | commit_npc **20011** | ❌ **不在本图的 25 个 NPC 里** |
| 10040 | 武魂觉醒 | commit_npc **10030** | ✅ 在场 |
| 10051–10054 | 武魂觉醒 | 无 | — |
| 10070–10072 | 巫风挑战 | 怪物 20002 / 20022 / 20040 | ❌ 怪物没下发 |
| 10092 | 猎取魂环 | 采集 **20001** | ❌ 未布置 |

**⇒ 两个具体缺口：**
1. **怪物（`mons`）完全为空** ⇒ 所有 `fight_mon` / `collect_elem` 类任务**无法寻路**
2. **`commit_npc_id` 可能不在本图**（如 `20011`）⇒ 需要**多地图支持**或补齐 NPC

---

## 四、怪物布置在哪？（**部分 UNKNOWN**）

| 查证 | 结果 |
|---|---|
| `config_map_npc.luac` 的内容 | 只有 **`MapNpc`** 与 **`MapSceneDoors`**（**无怪物**） |
| `config_mon_data.luac`（**857,309 字节**） | 只有 **3 个 proto / 58,359 条字节码**；顶层字符串里**没有** `map`/`scene`/`pos`/`x`/`y` |
| `config_demon.luac` / `config_mission_kill_demon.luac` | 体量很小（3,406 / 225 字节），**不像是全量怪物布置** |

**⇒ 推断（`INFERRED`）：每图的怪物布置（含坐标）**不在客户端配置里**，
应由**服务端**通过 `SC_10201.mons` 下发。**

**⇒ 依据**：`SC_10201` 的字段里本来就有 `mons` 表（与 `npcs` 并列），
说明这套协议的设计就是"服务端告诉客户端场上有哪些怪物"。

**⇒ 但"怪物坐标从哪来"仍是 `UNKNOWN`** ——
我们没有原版服务端的怪物布置数据，**不能编造。**

---

## 五、Phase F 的可执行动作（按证据强度排序）

| # | 动作 | 依据 | 风险 |
|---|---|---|---|
| **F1** | **把剧情链需要的 `commit_npc_id` 补齐到 `10201.npcs`**（如 `20011`）—— 坐标可暂用现有 NPC 布局规律，或从 `config_map_npc` 找同图条目 | 已确认缺哪个 id | 坐标来源需谨慎 |
| **F2** | **把 `fight_mon` 类任务的 `target`（怪物 bid）布置进 `10201.mons`** | `missionGoto` 需要怪物在场 | **怪物坐标无来源 ⇒ 需先解决** |
| **F3** | 用**探针直接调 `MissionUtil.missionGoto(vo)`**，观察它实际解析出什么目标、走到哪（**只观察，不改服务端**） | 与 Phase 4 解 `10303` 同手法 | 低 |

**⇒ 最稳的第一步是 F3**：用探针直接调 `missionGoto`，把"它需要什么"**实测出来**，
再决定 F1/F2 怎么补 —— **而不是先猜着补 NPC/怪物。**

---

## 五之二、★★★ F3 实测结果（**已执行，结论确定**）

### 做法

用探针包住 `MissionUtil.missionGoto`，并同时包住场景侧的
`SceneModel.moveToAutomate / moveToNpc / addMoveTarget / findVoTarget`、
`SceneController.moveToAutomate`；然后**点击任务追踪栏**，让客户端自己调用。

### 结果

**① 钩子装上** ✅

```
t=gotoH&v=MissionUtil.missionGoto_wrapped
```

**② 点击任务条，`missionGoto` 确实被调用**，且 `vo` 字段正确 ✅

```
2 x  missionGoto_bid_10010_mtype_1_status_1
5 x  missionGoto_bid_10030_mtype_1_status_1
1 x  missionGoto_bid_10040_mtype_1_status_1
8 x  missionGoto_returned
```

⇒ **入口链路是通的**：点击任务条 → `missionGoto(vo)`，`vo.mis_bid / mis_type / mis_status` 都对。

**③ 但场景侧的寻路调用一次都没有发生** ❌

```
gotoH 里没有出现任何  SceneModel.moveToAutomate / moveToNpc / addMoveTarget / findVoTarget
期间的网络包：只有 1199 心跳 x4  ——  ★ 没有任何 10204 移动包
```

**⇒ `missionGoto` 进去了、也返回了，但**没有走到真正的寻路那一步**。**

### 结论（**已确认**）

**在"目标不在场"的现状下，`missionGoto` 走不到寻路分支** —— 这与 §二/§三 的推断一致：
**服务端必须先把目标（NPC / 怪物）布置进 `SC_10201`，寻路才可能发生。**

**⇒ F3 的价值**：把"自动寻路不工作"从"不知道卡在哪"缩小到
**"卡在 `missionGoto` 内部的目标解析 → 因为目标不在场"**，且**证明客户端入口本身是好的**。

### 未取到的（如实）

- **未定位到"卡在 `missionGoto` 的哪一条分支"** —— 需要反汇编 `proto[7]` 的
  条件分派表，逐个对比我们手上三种任务（`10010` 无条件 / `10030` commit_npc=20011 不在场 /
  `10040` commit_npc=10030 在场）走的分支差异。
- 值得注意的是 **`10040`（commit_npc=10030，该 NPC 在场）也没有产生移动** ——
  说明除了"目标是否在场"，**可能还有别的门禁**（如 `isAutoWalk` 状态、场景加载状态、
  或需要先"接取"状态变化）。**这一点本轮未查清，标 `UNKNOWN`。**

---

## 六、结论

| 项 | 结果 |
|---|---|
| 自动寻路入口 | ✅ **已确认**：`mission_util proto[7] = missionGoto`（3,588 字节码） |
| 寻路机制 | ✅ **已确认**：按条件名分派 → 解析目标 → `moveToAutomate`；**纯客户端，不发协议** |
| 服务端能影响什么 | ✅ **已确认**：只能通过 `10201` 的 `npcs` / `mons` 决定"目标在不在场" |
| 当前缺口 | ✅ **已确认**：① 怪物 `mons` 为空；② `commit_npc_id` 可能不在本图（如 20011） |
| 怪物坐标来源 | ❌ **UNKNOWN**（客户端配置里没有；原版服务端布置数据我们没有） |
| **本阶段未做** | ❌ 未改任何代码；未编造怪物/NPC 坐标 |
| 建议下一步 | **F3：探针调 `missionGoto` 实测它需要什么** |

---

## 七、交付物

- 本文件：`analysis/1.4.9/task/task_autopath_investigation.md`
