# Phase F 订正 —— 自动寻路（`missionGoto`）真实调用链与上一轮结论的推翻

> 本文**推翻**上一版 `task_autopath_investigation.md` 的结论，并给出可复核的证据。
> 全部证据来自 **1.4.9** `anzbao/jstm.apk` 的 LuaJIT 字节码反汇编，未编造。
> confidence：**CONFIRMED / VERIFIED / INFERRED / UNKNOWN**

---

## 零、一句话结论

**上一轮"点击任务条 → `missionGoto` 进入了但没有走到寻路分支"的结论不成立。**
原因是**探针包错了对象**：它包的是 `SceneModel.moveToNpc` / `SceneModel.moveToAutomate`
等**并不存在（也不被调用）**的函数；真正被调用的是
**`MissionUtil.moveToNpc` / `MissionUtil.gotoTarget`（模块函数）** 和
**`SceneModel:getInstance():getScene():gotoTarget(vo)`（实例方法）**。

---

## 一、方法表（**CONFIRMED**）—— 先确认"名字到底挂在谁身上"

`mission_util.luac` 的方法表在 **proto#68** 里构建（`FNEW <child> ; TSETS <tbl>,'<name>'`）。
`tools/luac_defs.py` 扫描全部 69 个 proto 得到：

| 方法名 | proto | 字节码条数 |
|---|---|---|
| `missionGoto` | **#7** | 3588 |
| `gotoTarget` | **#8** | 161 |
| `gotoGuildNpc` | #31 | 60 |
| `gotoSceneNpc` | #34 | 39 |
| `gotoActivityNpc` | #37 | 41 |
| **`moveToNpc`** | **#38** | 40 |
| **`moveToAutomate`** | **#39** | 52 |
| `killSceneMon` | #50 | 40 |

⇒ **`moveToNpc` / `moveToAutomate` 是 `MissionUtil` 的模块函数，不是 `SceneModel` 的。**
复用命令：`python tools/luac_defs.py analysis/1.4.9/_mission_util.luac`

---

## 二、`missionGoto`（proto#7）到底调了什么（**CONFIRMED**）

`tools/luac_callgraph.py analysis/1.4.9/_mission_util.luac 7` 统计：

| 次数 | 调用 |
|---|---|
| 32 | `MissionUtil.getProgressArg` |
| **16** | **`MissionUtil.moveToNpc`** |
| **12** | **`MissionUtil.gotoTarget`** |
| 1 | `MissionUtil.moveToAutomate` |
| 8 | `SceneModel.getInstance` |
| 3 | `getView.findSrvElem` |
| 2 | `SceneModel:getInstance():addTarget` |

且 proto#7 的字符串常量里**同时**含有
`moveToAutomate / addMoveTarget / isAutoWalk / findVoTarget / addTarget / gotoTarget /
findSrvElem / moveToNpc`。
⇒ 上一轮是**拿这张字符串表猜函数归属**，猜成了 `SceneModel.*`，**这正是错误来源**。

---

## 三、`gotoTarget`（proto#8）逐指令（**CONFIRMED**）

`gotoTarget` 共 **8 个参数**，语义由调用点与字段写入反推：

```
gotoTarget(type, sceneId, x, y, monBid, npcId, pointBid, open)
```

### 3.1 七道门禁（任一命中就 **直接 return，不产生任何移动**）

| # | 判断 | 命中时 |
|---|---|---|
| 1 | `Battle:getInstance():inFight()` | return |
| 2 | `SceneModel:getInstance():isOnTeamFollow()` | `message(getString('您正在队伍跟随状态'))` → return |
| 3 | `ConVoyCtrl:getInstance():isConvoyState()` | `message(getString('您正在护送中'))` → return |
| 4 | `StoryCtrl:getInstance():getData():isStoryState()` | return |
| 5 | `SceneModel:getInstance():getIsOnXM()` | return |
| 6 | `SceneModel:getInstance():getIsOnFB()` | return |
| 7 | `SceneModel:getInstance():getScene()` 为 nil | return |

### 3.2 通过门禁后的固定动作

```
scene = SceneModel:getInstance():getScene()
scene:cancelWalk()
scene.currentFindVo = nil
vo = {}
vo.type    = type            -- FindType.NPC / MONSTER / POINT
vo.sceneId = sceneId
vo.pos     = cc.p(x, y)
vo.open    = open
if type == FindType.NPC     then vo.npcId = npcId end
if type == FindType.MONSTER then vo.bid   = monBid; vo.isTask = nil end
if type == FindType.POINT   then vo.bid   = pointBid end
GameData:getInstance():getRoleVo():setRoleAttribute('isAutoWalk', …)
SceneModel:getInstance().findVoTarget = vo
scene:gotoTarget(vo)          -- ★ 真正的"开始走"
```

⇒ **寻路的最后一跳是 `scene:gotoTarget(vo)`**（`scene` 是**实例**，不是类表）。
⇒ 上一轮探针包的是 `SceneModel.moveToAutomate / moveToNpc / addMoveTarget / findVoTarget`
与 `SceneController.moveToAutomate` —— **五个全部没包到点上**。

---

## 四、`moveToNpc`（proto#38）—— ★ 目标坐标的**客户端数据源**（**CONFIRMED**）

```
moveToNpc(npcId)
  local e = Config.MapNpc[npcId]          -- TGETS 'MapNpc' / TGETV [npcId]
  if e then
     MissionUtil.gotoTarget(FindType.NPC, e[1], e[2], e[3], nil, npcId)
  else
     local vo = StoryCtrl:getInstance():getView():findSrvNpc(npcId)   -- 场景内"服务端 NPC"
     if vo then MissionUtil.gotoTarget(FindType.NPC, vo.scene_id, vo.x, vo.y, nil, npcId) end
  end
```

⇒ **两条路**：
1. **`Config.MapNpc[npcId] = {scene_id, x, y}`** —— 客户端本地就有坐标；
2. 否则退化为"**在当前场景里找服务端下发的这个 NPC**"（`findSrvNpc`）。

⇒ 这解释了"某些 NPC 能寻路、某些不能"：**能不能寻路 = 目标在不在 `Config.MapNpc`，
或者服务端有没有把它放进当前场景**。

---

## 五、由此得到的**新数据源**（本阶段新增交付物）

| 表 | 文件 | 内容 | 交付物 |
|---|---|---|---|
| `Config.MapNpc` | `config_map_npc.luac` | `npc_id -> {scene_id, x, y}`（**54 个**） | `map_npc.json` |
| `Config.MapSceneDoors` | `config_map_npc.luac` | 场景传送图（**18 条**） | `map_scene_doors.json` |
| `Config.Map` | `config_map.luac` | **124 个场景**：`name/rows/cols/def_x/def_y` + `npcs/mons/elems` | `config_map.json` |
| `Config.Npc` | `config_npc.luac` | **456 个 NPC**：`name/face/res_id/talk/talk2/button` | `config_npc.json` |
| `Config.Mon` | `config_mon_data.luac` | 怪物**定义**（7956 条 id，23 字段）**无坐标** | 待提取 |

**⇒ 上一版把 `target_scene_id / target_x / target_y / submit_scene_id` 全标 `UNKNOWN`，
现在其中 128/188 条主线可以给出 `CONFIRMED` 的真实坐标。**

---

## 六、仍然缺的（**如实标注，不编造**）

| 缺口 | 证据 | 判定 |
|---|---|---|
| **怪物坐标** | `Config.Map[*].mons` 实测**全表为空**（合计 0 条）；`Config.Mon` 只有定义无位置 | **UNKNOWN** |
| **剧情 NPC 的位置**（如 `20011 少年雨浩`、`20070 少年王冬`） | 不在 `Config.MapNpc`、不在 `Config.Map[*].npcs` | **UNKNOWN** —— 应由原版服务端在场景里下发 |
| `accept_npc_id` 的场景 | 主线 `auto_accept=1`，`accept_npc_id` 普遍为 0 | 不适用 |

⇒ **因此服务端侧要做的事情被精确定位为两件**：
1. **把任务链需要的剧情 NPC 放进 `SC_10201.npcs`**（原版位置 **UNKNOWN**，需另行求证或按最小必要处理）；
2. **把 `fight_mon` 类任务的目标怪物放进 `SC_10201.mons`**（原版坐标 **UNKNOWN**）。

---

## 七、本轮"只观察"实测（订正后的探针）

订正后的探针（`server/dsh_fake_login.lua` 的 `gt2` 段）包住了**正确对象**：

- `MissionUtil.missionGoto`（入口）
- `MissionUtil.moveToNpc`（含 `Config.MapNpc[npcId]` 命中情况）
- `MissionUtil.gotoTarget`（8 个参数全记录）
- `MissionUtil.moveToAutomate`
- `SceneModel:getInstance():getScene():gotoTarget(vo)`（**实例方法，拿到实例后再包**）
- 7 道门禁在 `missionGoto` / `gotoTarget` 入口的**实时快照**
- 角色坐标周期采样（判定"到底有没有走"）
- 到点主动调用 `moveToNpc(10030)` / `gotoTarget(FindType.NPC,10001,70,61,nil,10030)`

实测结果见 `task_autopath_probe_result.md`。

---

## 八、交付物

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/task/task_autopath_correction.md` | 本文件（**订正**上一版结论） |
| `analysis/1.4.9/task/map_npc.json` | `Config.MapNpc`：54 条 npc→场景→坐标 |
| `analysis/1.4.9/task/map_scene_doors.json` | `Config.MapSceneDoors`：18 条场景传送 |
| `analysis/1.4.9/task/config_map.json` | `Config.Map`：124 场景 + npcs/mons/elems |
| `analysis/1.4.9/task/config_npc.json` | `Config.Npc`：456 NPC 名称/模型/对话 |
| `tools/luac_defs.py` | 方法名→proto 的还原工具（本轮定位错误的关键工具） |
| `tools/luac_callgraph.py` | 原型的"外部调用序列"提取 |
| `tools/extract_map_npc.py` / `extract_config_map.py` / `extract_config_npc.py` | 上述三张表的提取脚本 |
| `tools/build_fakelogin.ps1` | 1.4.9 探针版 APK 一键构建+安装 |
