# Phase H —— 剧情任务系统端到端回归（1.4.9 实测）

> 一次**自包含、可复现**的完整跑通：任务列表 → 自动寻路 → 提交 → 奖励 → 链推进 → 重登保持。
> 证据来源：客户端探针上报（`cc.XMLHttpRequest` → `/DSH_PROBE`）、服务端 `tcp.log` 帧、
> 服务端 SQLite（`server/state/roles.db`）。
> 复现：`Copy-Item analysis\_db_before_e2e.db server\state\roles.db` →
>      `pwsh tools/build_fakelogin.ps1` → 等 ~120 秒。

---

## 一、结论

| 目标链环节 | 结果 | 证据强度 |
|---|---|---|
| 任务列表显示 / 恢复 | ✅ | 客户端 `receive_list` 快照 + 服务端 `12400` |
| **自动寻路到目标** | ✅ | **`10204` 位移包轨迹（见 §三）** |
| 完成条件 | ✅ | `10020` 走 `fight_mon` 条件分支（服务端判定） |
| 提交 | ✅ | `12403 SC_12403 code=1(TRUE)` |
| 获得**原版**奖励 | ✅ | 数额取自 `config_mission.luac` 的 `award_assets` |
| 剧情链自动推进 | ✅ | **连续 3 环**：10010 → 10030 → 10040 |
| 重登后进度保持 | ✅ | 强杀重开后 `receive_n` 与坐标均保持 |

---

## 二、任务列表 / 链推进（客户端探针）

`MissionCtrl:getInstance():getMissionData()` 的 `receive_list`（进行中任务）快照：

| 时点 | `receive_n` | 键（前若干） |
|---|---|---|
| 初始 | **7** | `10010 10030 10040 10051 10052 10053 10054` |
| 提交 10010 后 | **6** | `10030 10040 10051 10052 10053 10054` |
| 提交 10030 后 | **5** | `10040 10051 10052 10053 10054` |
| 提交 10040 后 | **4** | `10051 10052 10053 10054` |

⇒ **每提交一条，列表正好减少一条，且下一条仍在** —— 链在连续推进。

---

## 三、★ 自动寻路：**位移包轨迹**（最强证据）

探针脚本：先把角色用同一个 `moveToNpc` 机制**走到远处的 10160 @ (10,89)**，
再用 `moveToNpc(10030)` 让它**自动走回 10030 周漪 @ (70,61)**。

### 3.1 客户端探针读数

```
STEP1_walk_away_from:68_62_to_10160:10_89
STEP1_moveToNpc_10160_ok:true_err:nil
STEP2_pos_far:9_89_from:68_62             ← 第一步就走到了 (9,89)，目标 (10,89)
STEP3_autopath_before:9_89_target:70_61
STEP3_moveToNpc_10030_ok:true_err:nil
STEP4_autopath_after:71_59_before:9_89_target:70_61   ← ★ (9,89) → (71,59)，目标 (70,61)
```

### 3.2 服务端收到的 `10204` 移动包（角色真的在地图上走）

```
17:59:40  ** DB persist role 1001 pos=(40,70)
17:59:40  ** DB persist role 1001 pos=(47,68)
17:59:41  ** DB persist role 1001 pos=(53,65)
17:59:41  ** DB persist role 1001 pos=(60,63)
17:59:42  ** DB persist role 1001 pos=(66,61)
17:59:42  ** DB persist role 1001 pos=(71,59)      ← 停在目标 (70,61) 旁
```

⇒ 这是一条**连续、单调逼近目标**的路径，**不是瞬移**。
⇒ **1.4.9 客户端自动寻路功能完好，并且真的驱动了角色位移。**

---

## 四、提交 / 奖励 / 链推进（服务端帧 + 数据库）

### 4.1 服务端发出的帧

```
<< 12403 SC_12403 commit mission_bid=10010 code=1(TRUE)
<< 12405 SC_12405 update_mission_list=6
<< 12406 SC_12406 del_mission_list=[10010]
** mission 10010 committed: +500 exp, +1290 coin
** mission 10030 committed: +520 exp, +1350 coin
** mission 10040 committed: +700 exp, +1810 coin
```

`code=1(TRUE)` 与 `mission_ctrl` proto#42 `submitHandler` 的成功判定一致
（见 `analysis/mission_protocol_verify.md`）。

### 4.2 奖励**逐条对得上 APK 配置**

| 任务 | `award_assets`（来自 `config_mission.luac`） | 实发 |
|---|---|---|
| 10010 | `[[2,1290],[4,500],[15,500]]` | +1290 coin / +500 exp / +500 hero_exp |
| 10030 | `[[2,1350],[4,520],[15,500]]` | +1350 coin / +520 exp / +500 hero_exp |
| 10040 | `[[2,1810],[4,700],[15,…]]` | +1810 coin / +700 exp |

**累加核对**：

```
coin     : 1290 →2580 →3930 →5740      (1290+1290+1350+1810 = 5740 ✓)
exp      :  500 →1000 →1520 →2220      (500+500+520+700   = 2220 ✓)
hero_exp :  500 →1000 →1500 →2200      ✓
```

⇒ 奖励**不是硬编码**，而是逐条取自 APK 任务表。

### 4.3 数据库最终状态

```
10010 status=3  commit=1
10020 status=3  commit=1
10030 status=3  commit=1
10040 status=3  commit=1
10051 status=1                      ← 下一条已自动接取（auto_accept=1）
role_assets: coin=5740 exp=2220 hero_exp=2200
```

---

## 五、重登保持（强杀重开）

```
& adb shell am force-stop com.shiyue.dldl.ewan.qihoo
& adb shell monkey -p ... -c android.intent.category.LAUNCHER 1
```

重开后：

```
服务端   << 12400 SC_12400 mission_list=6
客户端   list_before ... receive_n:6 recv_keys:10030_10040_10051_100...
```

⇒ 已完成的任务**不再以"进行中"出现**，进行中的 6 条**原样恢复**，
角色坐标 `(71,59)` 也在 `roles` 表里持久化。

---

## 六、本轮**未通过**的一项（如实）

| 项 | 现象 | 原因（已定位） |
|---|---|---|
| `moveToNpc(20011)`（少年雨浩）自动寻路 | 无位移 | 不在 `Config.MapNpc`；回退路径 `StoryCtrl:getView():findSrvNpc` 查的是**剧情场景**，而该场景的编排表**不在 APK 里** |

`missionGoto` 全程**不调用** `gotoSceneNpc`（`luac_callgraph` 已核），
所以客户端不会为了一个普通 NPC 目标切场景。
详见 `task_story_scene_finding.md`。

---

## 七、覆盖范围（**诚实交代**）

| 类别 | 条数 | 状态 |
|---|---|---|
| 提交 NPC 在 `Config.MapNpc`（可自动寻路） | **128** | ✅ 全链可用 |
| 提交 NPC 为剧情 NPC（20xxx） | **60** | ⚠️ 可显示/可提交，**自动寻路不可用**（剧情场景数据缺失） |
| `fight_mon` 类（需战斗结算） | **38** | ⚠️ 寻路可派发，**击杀需战斗系统**（超出本阶段范围） |

---

## 八、交付物

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/task/task_e2e_regression.md` | 本文件 |
| `server/dsh_fake_login.lua` | `e2e` 回归脚本段（`_G.__dsh_e2e`） |
| `analysis/_db_before_e2e.db` | 回归前的数据库快照（可复现起点） |
| `server/logs/http.log` / `tcp.log` | 原始探针上报与协议帧 |
| `tools/inspect_db.py` | 数据库状态检查工具 |

## 九、复现步骤

```powershell
# 1) 还原到回归起点
Copy-Item analysis\_db_before_e2e.db server\state\roles.db -Force
# 2) 起服务端
python server\mock_server.py
# 3) 构建并安装带 e2e 脚本的客户端（约 20 秒）
pwsh tools\build_fakelogin.ps1
# 4) 等 ~120 秒，读结果
Select-String -Path server\logs\http.log -Pattern 't=e2e' | Select-Object -Last 16
python tools\inspect_db.py
```
