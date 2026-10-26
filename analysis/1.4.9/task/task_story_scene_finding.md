# 剧情 NPC（20011 等）为什么仍在主城里寻不到路 —— 实测与判定

> 承接 `task_autopath_correction.md` / `task_autopath_probe_result.md`。
> 本文记录**服务端补发剧情 NPC 之后的实测结果**，以及剩余缺口的**精确定位**。
> confidence：CONFIRMED / VERIFIED / INFERRED / UNKNOWN

---

## 一、背景：主城寻路的两种目标来源（**CONFIRMED**）

`mission_util` proto#38 `moveToNpc(npcId)`：

```
local e = Config.MapNpc[npcId]                                  -- ① 客户端静态表
if e then MissionUtil.gotoTarget(FindType.NPC, e[1], e[2], e[3], nil, npcId)
else
  local vo = StoryCtrl:getInstance():getView():findSrvNpc(npcId) -- ② ★ 注意是 StoryCtrl
  if vo then MissionUtil.gotoTarget(FindType.NPC, vo.scene_id, vo.x, vo.y, nil, npcId) end
end
```

⇒ **② 的宿主是 `StoryCtrl`（剧情控制器）的 view，不是主场景的 view。**

---

## 二、服务端侧修复已生效（**CONFIRMED**，实测）

`server/quest_spawn.py` + `mock_server.py`：把任务链当前需要的剧情 NPC / 目标怪物
放进当前场景的 `SC_10201`。

服务端日志：

```
[17:41:30]  ★ quest_spawn scene=10001 +1 npc [20011] +1 mon [20001]
[17:41:30]  << 10201 SCMapGird (server push) roles=1 npcs=26 mons=1 (650 bytes)
```

⇒ 场景 NPC 数由 **25 → 26**，并且 `mons` 由**写死的 0 条**变成真正下发。

---

## 三、客户端**确实收到了**这个 NPC（**CONFIRMED**，探针实测）

```
[17:42:52] t=smCall  addNpc_n_27_a_1_id_20011_bid_20011_type_0_x_47_y_68_name______
[17:42:55] t=npcE    registEvent_vo_bid_20011_name_____________
[17:42:55] t=npcE    setVo_arg_bid_20011_arg_name_____________
```

⇒ `SceneModel:addNpc(...)` 被调用，NPC 元素也被 `setVo` / `registEvent` 创建了。
**协议与渲染这一层是通的**，不是编码错。

---

## 四、但寻路**仍然没有发生**（**CONFIRMED**，探针实测）

```
[17:43:47] t=gt2  moveToNpc_npc:20011_cfg_notInMapNpc
[17:44:27] t=gt2  moveToNpc_npc:20011_cfg_notInMapNpc
[17:44:27] t=gt2  EXP_moveToNpc_20011_ok:true_err:nil
```

**期间没有任何一条 `gotoTarget` / `SCENE.gotoTarget` 上报**，角色坐标全程停在 `(68,62)`：

```
n:40 xy:68_62 … n:115 xy:68_62      ← 完全没有任何位移
```

⇒ `moveToNpc(20011)` 进了 else 分支，而 **`findSrvNpc(20011)` 返回了 nil**。

---

## 五、判定（**INFERRED，但依据充分**）

把三、四放在一起：

| 事实 | 含义 |
|---|---|
| 客户端把 20011 建成**主场景**的 NPC 元素了 | 它就在**主场景**里 |
| `findSrvNpc(20011)` 仍返回 nil | `findSrvNpc` 找的**不是主场景**的 NPC |

⇒ 与 §一 的 `StoryCtrl:getView()` 吻合：

**`findSrvNpc` 查的是「剧情场景（StoryCtrl 的 view）」里的服务端 NPC，
而不是主城（SceneModel 的 scene）里的 NPC。**

⇒ **因此：把剧情 NPC 塞进主城 `SC_10201.npcs` 不能让它变得可寻路。**
要让 `moveToNpc(20011)` 成立，客户端必须**先进入该 NPC 所在的剧情场景**。

---

## 六、剧情场景 id 的来源：**仍然 UNKNOWN**（如实标注）

已逐表查证，**都没有**主线 10030 的剧情场景：

| 查证对象 | 结果 |
|---|---|
| `Config.MapNpc[20011]` | ❌ 不存在 |
| `Config.Map[*].npcs / mons / elems` 含 20011 | ❌ 全表都没有 |
| `Config.Drama`（`config_drama_data.luac`） | 只含**功能类**剧情（bid 50060–50072，`map_bid` 全为 0），**没有主线的** |
| `Config.Chapter`（`config_chapter.luac`） | 无数字键条目（0 条） |
| `Config.Lead`（`config_lead_data.luac`） | 是"引导/指引"，不含坐标 |
| `Config.MapBlock` | 只有通行格，没有 NPC 位 |

⇒ **结论：`mission_config` 的 `commit_npc_id` 为 20xxx 的 60 条主线，
其目标 NPC 所在的剧情场景与坐标，客户端 APK 里没有 ⇒ `UNKNOWN`。**

**这是一个"必须放弃编造"的点**：原版服务端的剧情场景编排表不在客户端，
本阶段无法取证。**不得自行指定一个场景冒充原版。**

---

## 七、本阶段真正可交付的部分（**已实现并验证**）

| # | 能力 | 状态 |
|---|---|---|
| 1 | 客户端自动寻路**确认可用**（实测角色从 (64,56) 走到 (68,62)） | ✅ **VERIFIED** |
| 2 | 静态 NPC 目标（128/188 条主线）**已经能寻路** | ✅ **VERIFIED** |
| 3 | `SC_10201.mons` **从写死 0 条改为真实下发**（字段顺序取 `protocol/manual.md`） | ✅ **已实现** |
| 4 | 剧情 NPC 进主场景（客户端确认收到并创建） | ✅ **已实现** |
| 5 | `fight_mon` 类目标怪物进场景（38 条主线） | ✅ **已实现**（坐标为仿真摆位） |
| 6 | 剧情 NPC 的**剧情场景**定位 | ❌ **UNKNOWN**（见 §六） |

---

## 八、坐标性质声明（**必须随交付说明**）

原版「怪物摆位 / 剧情 NPC 站位」的表**不在客户端 APK 里**。
`server/quest_spawn.py` 下发的是：

> 以该场景**声明的进入点** `Config.Map[scene].def_x/def_y`（真实配置值）
> 为锚点，用黄金角螺旋错开，并夹进场景边界内的**仿真摆位**。

每一项都带 `source='emulated'`，**不得表述为原版坐标**。

---

## 九、交付物

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/task/task_story_scene_finding.md` | 本文件 |
| `server/quest_spawn.py` | 剧情 NPC / 目标怪物的场景下发模块 |
| `server/mock_server.py` | `build_mons` / `build_elems` / `scene_quest_extras` 接入 |
| `analysis/1.4.9/task/config_mon.json` | `Config.Mon` 提取结果（2645 条可配平） |
