# Phase F 实测记录 —— 自动寻路「能用」的**决定性证据**

> 探针版本：`server/dsh_fake_login.lua` 的 `gt2` 段（**订正后**，包正确的对象）
> 复现命令：`pwsh tools/build_fakelogin.ps1`（注入 → zipalign → 签名 → 安装，实测 **19 秒**）
> 数据来源：客户端 `cc.XMLHttpRequest` → `http://10.0.2.2:8080/DSH_PROBE?t=gt2&v=…`
> 日志：`server/logs/http.log`

---

## 一、结论（**先给结论**）

**1.4.9 客户端的自动寻路是好的，而且能真的把角色走过去。**

上一轮 "自动寻路不工作" 的判断是**探针包错对象**造成的假象 —— 详见
`task_autopath_correction.md`。

---

## 二、探针安装成功（**CONFIRMED**）

```
17:32:40  moveToAutomate_wrapped
17:32:40  moveToNpc_wrapped
17:32:40  gotoTarget_wrapped
17:32:40  missionGoto_wrapped
17:32:40  posTicker_installed
17:32:46  SCENE.gotoTarget_wrapped        ← ★ 实例方法也包上了（上一轮漏掉的就是它）
```

---

## 三、★ 七道门禁**全部通过**（**CONFIRMED**）

主动调用 `MissionUtil.moveToNpc(10030)` 时，`gotoTarget` 入口的门禁快照：

```
17:33:26  GATE2_gotoTarget_fight:false_teamFollow:false_convoy:false
          _story:false_xm:false_fb:false_sceneType:table
```

| 门禁 | 值 | 结果 |
|---|---|---|
| `Battle:inFight()` | `false` | 通过 |
| `isOnTeamFollow()` | `false` | 通过 |
| `isConvoyState()` | `false` | 通过 |
| `isStoryState()` | `false` | 通过 |
| `getIsOnXM()` | `false` | 通过 |
| `getIsOnFB()` | `false` | 通过 |
| `getScene()` | `table`（非 nil） | 通过 |

⇒ **没有任何一道门禁把寻路挡掉。**

---

## 四、★ 完整调用链**逐级命中**（**CONFIRMED**）

一次 `moveToNpc(10030)` 产生的**全部**上报（时间序）：

```
moveToNpc_npc:10030_cfg_scene:10001_x:70_y:61     ← ① Config.MapNpc[10030] 命中！
gotoTarget_type:2_scene:10001_x:70_y:61_mon:nil_npc:10030   ← ② 派发（type=2=FindType.NPC）
SCENE.gotoTarget_type:2_scene:10001_npc:10030_bid:nil_pos:70_61  ← ③ ★ 走到最后一跳！
moveToNpc_returned
```

对照 `task_autopath_correction.md` §三，③ 正是 `proto#8` 的
`SceneModel:getInstance():getScene():gotoTarget(vo)`。

⇒ **链路：`moveToNpc` → `Config.MapNpc` 命中 → `gotoTarget` → `scene:gotoTarget(vo)` 全通。**

---

## 五、★★ 角色**真的走了**（位置采样，**CONFIRMED**）

```
17:33:21  pos n:40  xy:64_56      ← 调用前
17:33:26  pos n:45  xy:64_56      ← 此刻触发 moveToNpc(10030)
17:33:31  pos n:50  xy:68_62      ← ★ 位置变了！
17:33:37  pos n:55  xy:68_62      ← 到达后停住
…
17:34:17  pos n:95  xy:68_62
```

| 项 | 值 |
|---|---|
| 调用前 | `(64, 56)` |
| 目标（`Config.MapNpc[10030]`） | `(70, 61)` |
| 调用后 | **`(68, 62)`** |
| 位移 | **(+4, +6)**，朝目标方向 |
| 停止 | 到达后不再变化（正常寻路结束） |

⇒ **自动寻路不仅被调用，而且真的驱动了角色位移并正确停在目标附近。**

---

## 六、由此定位到的**真正缺口**（**CONFIRMED**）

上一轮把问题错误地归因为"客户端寻路坏了"。真正的缺口是
**"目标解析不出来"**，而目标解析有两条路（`mission_util` proto#38）：

```
moveToNpc(npcId)
  ├─ ① Config.MapNpc[npcId] 命中 → 有坐标 → 能寻路
  └─ ② 否则 StoryCtrl:getInstance():getView():findSrvNpc(npcId)
        → 只有在「服务端把它放进当前场景」时才拿得到坐标
        → 拿不到 ⇒ 不调用 gotoTarget ⇒ **没有移动**
```

**统计（`tools/build_quest_route2.py`，262 条主线）：**

| 情况 | 条数 | 能否寻路 |
|---|---|---|
| `commit_npc_id` **在** `Config.MapNpc` | **128** | ✅ **已经可以寻路** |
| `commit_npc_id` **不在** `Config.MapNpc` | **60** | ❌ 需服务端下发到场景 |
| `fight_mon` 类条件（怪物目标） | **38** | ❌ `Config.Map[*].mons` 实测**全表为空** |

⇒ **服务端侧要补的就是这两件事**（剧情 NPC / 目标怪物进场景），
而不是去改客户端寻路。

---

## 七、反例验证（**本轮已加入探针，见 `NEG_*` 上报**）

| 测试 | 期望 | 依据 |
|---|---|---|
| `moveToNpc(20011)`（少年雨浩） | `cfg_notInMapNpc`，且**不出现** `SCENE.gotoTarget` | 20011 不在 `Config.MapNpc`，服务端也没下发 |
| `gotoTarget(MONSTER, …, 20001, …)` | 能派发，但场景无该怪物 ⇒ 不会真正移动 | `Config.Map[10001].mons` 为空 |

---

## 八、交付物

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/task/task_autopath_probe_result.md` | 本文件（实测证据） |
| `analysis/1.4.9/task/task_autopath_correction.md` | 调用链订正与真实机制 |
| `server/logs/http.log` | 原始探针上报 |
| `tools/build_fakelogin.ps1` | 19 秒可复现构建+安装 |
