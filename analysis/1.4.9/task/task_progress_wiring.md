# 击杀/采集事件协议 · 与 `mission_progress_advance` 接线（✅ 完成，含**如实标注的替身机制**）

> **用户要求**：找出击杀/采集事件的协议，把 `mission_progress_advance` 接上，
> 让"需进度"的任务能自然完成。

---

## 1. ★ 调查结论：客户端**不上报**击杀/采集

| 查证项 | 结果 |
|---|---|
| `fight_mon` / `collect_elem` 在客户端被谁用 | ① `mission_util proto[0]`、② **`mission_util proto[7] = missionGoto`**、③ `sidebar_mis_item proto[12]` |
| **`missionGoto` 的用途** | **自动寻路**：把条件名/目标当成"要去的地方"（`fight_mon` → 去某怪、`collect_elem` → 去某采集点） |
| `scene_controller` 注册的 102xx（26 条） | `10200–10250`：进场景/图块/移动/瞬移/换线/图块变更… **没有"怪物死亡"类消息** |
| `10206`（最像攻击的） | `CS{x:uint32}` → `SC{code,msg}` —— 是**建造/交互**，不是击杀上报 |
| 击杀发生在哪里 | **战斗实例**：`11000`（`mon_list`）、`11200`/`11215`（`skill`/`jindan_skill`/`talisman_skill`）系列 |
| 结论 | **客户端在场景层不上报击杀/采集；任务进度由服务端记** ⇒ 需要服务端知道"击杀了" |

**⇒ 而"战斗系统"是阶段 5 明确禁止开发的范围。**

---

## 2. 因此采用的方案：**接线 + 明确标注的替身触发**

### 2.1 保留真实接口（将来直接换）

```python
def mission_progress_advance(rid, cond_name, target, n=1):
    """把满足条件（条件名 + 目标 id）的在途任务推进 n 点；
       够了就把 process_status 置 1（可提交）。"""
```

**⇒ 将来实现战斗后，只需在真实的"击杀/采集"事件处调用它即可，不必改其它逻辑。**

### 2.2 本阶段的替身（**开关控制，日志里明确标注**）

在 `CS_10204/10205`（移动）处理里接入：

```python
if self.cfg.get('mission_auto_progress'):
    for mb, mm in db_get_missions(rid).items():
        ...
        hit = mission_progress_advance(rid, cname, tgt, 1)
        if hit:
            log('tcp.log', '  .. [替身·无战斗] 移动推进 mission %s cond=%s target=%s -> %r' ...)
```

- **开关**：`mission_auto_progress`（config.json，默认开）
- **日志前缀 `[替身·无战斗]`** —— 一眼能看出这不是真实战斗逻辑
- **代码注释里写明**："已确认客户端不上报击杀；本段是替代，实现战斗后替换为真实事件调用"

---

## 3. ★ 端到端验证（两圈，**完整闭环**）

### 第一圈：条件未满足 ⇒ 提交被**正确拒绝**；移动后进度满足

```
[11:59:26]  << 12403 SC_12403 mission_bid=10020 code=1 (条件未满足 0/1)   ← ★ 完成判定生效
[11:59:27]  << 12400 SC_12400 mission_list=8 (280 bytes)                  ← 8 条任务
[11:59:34]  .. [替身·无战斗] 移动推进 mission 10020 cond=fight_mon target=20001 -> [10020]

missions: [(10010,1), (10020,1, target=20001, need=1, value=1), …]        ← value 已满足
```

### 第二圈：条件满足 ⇒ 提交**成功**、发奖、链前移

```
[12:03:07]  ** mission 10020 award_assets=[[2,1290],[4,500],[15,500]]
                          -> delta={'coin':1290, 'exp':500, 'hero_exp':500}
[12:03:07]  << 12403 SC_12403 commit mission_bid=10020 code=0            ← ★ 提交成功
[12:03:07]  << 12405 SC_12405 update_mission_list=7
[12:03:07]  << 12406 SC_12406 del_mission_list=[10020]
[12:03:07]  ** mission 10020 committed: +500 exp, +1290 coin, +0 gold
[12:03:08]  << 12400 SC_12400 mission_list=7

missions: [(10010,1), (10020,3, value=1), (10030,1), …]                   ← 10020 已提交
role_assets: [coin=1290, exp=500, hero_exp=500]
```

**⇒ 整条链路已闭环：**
`接取（APK 任务表）` → `条件（来自 progress）` → `进度推进` → **提交被拒（未满足）** →
**提交成功（满足）** → `配置驱动发奖` → `移出列表` → **链前移**

---

## 4. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | ① `CS_10204/10205` 里接入 **`mission_progress_advance`**（受 `mission_auto_progress` 控制，日志标注 `[替身·无战斗]`）<br>② 保留 `mission_progress_advance()` 作为**真实事件接口** |
| `server/config.json` | 新增 `mission_auto_progress = true` |
| `server/dsh_fake_login.lua`（调试探针） | 提交目标从 `10010` 改为 **`10020`**（当前链头，带进度条件），用于验证条件判定 |

---

## 5. 仍然缺失 / 待验证（如实）

1. **这不是真实的战斗驱动** —— 是**开关控制的替身**。真正的击杀/采集事件在
   `11000`/`11200` 系列（战斗实例）内，**属阶段 5 禁止范围**，故**未实现**。
   **日志与注释里都明确标注了这一点，没有伪装成真实逻辑。**
2. **`progress` 第 2 行含义未确认**（如 `[0,0,20010,0]`）⇒ 未使用、未猜。
3. **替身粒度较粗**：按"移动事件"推进，而不是"到达目标怪附近"。
   （因为没有怪物坐标数据；`config_map_npc` 只有 NPC，没有怪物布置。）
4. **未在 `10201.mons` 里下发怪物** —— 所以客户端其实看不到目标怪，寻路也无处可去。
5. NPC 对话 UI 仍未打通（提交走 `MissionCtrl:submit`）。

---

## 6. 本轮结论

| 项 | 结果 |
|---|---|
| 找击杀/采集协议 | ✅ **已查明：客户端场景层不上报**；击杀在战斗实例（禁止范围） |
| `mission_progress_advance` 接线 | ✅ **已接到移动事件**（开关 + 日志标注） |
| 完成判定 | ✅ **已验证**（未满足 ⇒ `code=1 条件未满足 0/1`） |
| "需进度"任务完成 | ✅ **已验证**（`10020` 推进后提交成功、发奖、链前移） |
| 真实性 | ⚠️ **是替身，不是真实战斗**（已明确标注，未伪装） |
| 改 APK / UI | ✅ 未做 |

**交付物**：本文件、`server/mock_server.py`、`server/config.json`、
`logs/1.4.9/task_progress_tcp.log`

---

**[WAITING FOR NEXT INSTRUCTION]**
