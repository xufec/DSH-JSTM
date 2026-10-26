# Phase 5H–5K —— 完成任务 / 领取奖励 / 任务持久化 / 回归（✅ 全部完成）

> 一条命令闭环已跑通：**接取（5F）→ 提交（5H）→ 发奖（5I）→ 落库（5J）→ 重登仍正确（5K）**。
> 本轮同时**自查出并修复了 3 个真实 bug**（详见 §5）。

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | ① 新增 **`missions` 表**（`db_init`）＋ `db_get_missions` / `db_save_mission` / `mission_rows`（数据库优先、config 播种、**过滤已提交**）<br>② `12400`/`12401` 改走 `mission_rows()`（DB 为准）<br>③ **`12403` 完整结算**：幂等判断 → 发奖 → 角色数据落库 → 任务状态落库 → 回 `SC_12403` + 推 `12405`（更新）+ `12406`（移出列表）+ 刷新 `10301/10302/10303`<br>④ **第二处 `12400` 推送**也改走 `mission_rows()` |
| `server/config.json` | `missions[0]` 增加 `reward_exp=150` / `reward_gold=888`；`mission_status` 用于阶段实验 |
| `server/dsh_fake_login.lua`（调试探针） | 新增：调用 `MissionCtrl:getInstance():submit(10010)`（依据 `mission_ctrl proto[40]`），用于在 NPC 对话 UI 不可达时触发提交 |

**协议依据（全部 1.4.9）**：
- `mission_ctrl.luac` 的 `RegisterProtocal(12400–12406…)`
- `mission_ctrl proto[40] = submit(mission_bid)` → `GetPrototype(12403)` → `SendProtocal`
- 字段取自 `protocol/manual.md`（`tools/show_cmd.py 12403/12405/12406`）

---

## 2. 协议证据（本轮实测）

```
>> cmd=12403 ? body(8)=00 00 27 1a 2d 2d 2d 2d          ← CS_12403{mission_bid=10010}
<< 12403 SC_12403 commit mission_bid=10010 code=0 (13 bytes)
<< 12405 SC_12405 update_mission_list=0 (8 bytes)
<< 12406 SC_12406 del_mission_list=[10010] (12 bytes)
** mission 10010 committed: +150 exp, +888 gold (now exp=150 gold=1888)
<< 12400 skipped (no active mission)
```

| 消息 | 含义 |
|---|---|
| `CS_12403{mission_bid:u32}` | 客户端提交（由 `MissionCtrl:submit` 发出） |
| `SC_12403{mission_bid, code, msg}` | 服务端确认 |
| `SC_12405{update_mission_list}` | 任务增量更新（提交后列表为空） |
| `SC_12406{del_mission_list=[10010]}` | **把已完成任务移出列表**（该协议的正规用途） |
| `SC_10301/10302/10303` | 角色数据刷新（面板/经验条立刻更新） |

---

## 3. 5H / 5I / 5J / 5K 逐项结论

### 5H 完成任务 ✅
- 客户端发 `CS_12403{mission_bid=10010}`（**已验证**）
- 服务端识别任务、执行结算（**已验证**）
- **`MissionStatus.STATUS_2 = 2` 是"可提交"态**（依据 `commitMisByMyself` 里的 `mis_status == STATUS_2` 判断，**已确认**）

### 5I 领取奖励 ✅
```
** mission 10010 committed: +150 exp, +888 gold (now exp=150 gold=1888)
role   : {'level': 7, 'exp': 150, 'gold': 1888}
```
- 奖励写入**数据库**（`roles` 表），并推送 `10301/10302/10303` 让客户端刷新
- ⚠ **`award_assets` 二元组含义仍为待验证**，故本轮奖励值来自**我们显式配置的
  `reward_exp` / `reward_gold`**，**没有按猜测去解 `award_assets`**

### 5J 任务持久化 ✅
```
停服务端 → 端口监听数 0 → 重启
重启后 mission: {'mission_bid':10010,'mission_status':3,'commit_num':1}
重启后 role   : {'level':7,'exp':150,'gold':1888}
mission_rows() -> [{'mission_bid':10010,'mission_status':3,'commit_num':1}]
```
- **任务状态落在 SQLite `missions` 表**（新增），角色数据在 `roles` 表
- **活过服务器重启** ✅

### 5K 完整回归 ✅

| 步骤 | 结果 |
|---|---|
| 进图（**按提示先点取消按钮 (2200,85)**） | ✅ |
| 任务自动接取（`auto_accept=1`）→ 追踪栏显示 | ✅（5F 已验证） |
| 提交（`12403`） | ✅ 1 次 |
| 发奖 | ✅ +150 exp / +888 gold，**只发一次** |
| 任务移出列表（`12406`） | ✅ |
| 重登 | ✅ `10302 lev=7 exp=150 gold=1888` 正确 |
| 重登后**不再推送已完成任务** | ✅ `12400 skipped (no active mission)` |
| 重登后客户端再发一次 `12403` | ⚠️ 会发，但**被幂等拦住**：`commit_num` 仍 1、`exp/gold` 不变 ✅ |

---

## 4. 指令节奏（本轮统一做法，值得记下）

每次实机跑都按这个顺序：
```
am force-stop → am start → 等 ~60s →
input tap 2200 85（**关掉进图后的提示框**）→ 再点一次 → 再等 ~150s → 收日志
```
**`(2200,85)` 这个取消按钮是用户提示的**，不点它会挡住后续操作。

---

## 5. ★ 自查发现并修复的 3 个 bug（本轮重点）

| # | Bug | 现象 | 修复 |
|---|---|---|---|
| **1** | **重复提交导致刷奖励** | `commit_num=4`、`exp=600`、`gold=12440`（应为 1/150/1888） | `12403` 加**幂等保护**：`mission_status==3` 时只回包、**不再发奖** |
| **2** | **已完成任务仍留在列表** | 提交后 `status=3` 的任务仍被 `12400` 推给客户端 ⇒ 客户端反复提交 | `mission_rows()` **过滤掉 `status=3`**；并在提交后发 **`12406 del_mission_list`** 把任务移出 |
| **3** | **第二处 `12400` 推送点未走 DB** | 重登时仍用 `config` 直接推 ⇒ 又把已完成任务推出去 | 第二处也改走 `mission_rows()`；无任务时打 `12400 skipped` |

**另外还自查出一处"我自己的疏漏"**：修 bug #2 时，`12403` 里的幂等判断一度也用了被过滤的
`mission_rows()` ⇒ 已提交任务会走到 `no such mission` ⇒ **改用未过滤的 `db_get_missions()`**，
并在库为空时**先播种再读**（否则 `12403` 早于 `12400` 到达时会报 `code=1`）。

**⇒ 修复后干净一轮的读数：**
```
<< 12403 code=0 / << 12405 / << 12406 del=[10010]
** +150 exp, +888 gold (now exp=150 gold=1888)
mission: {'mission_status':3,'commit_num':1}
role   : {'exp':150,'gold':1888}
```

---

## 6. 日志位置

```
logs/1.4.9/task_5h_tcp.log        提交/结算/移出列表
logs/1.4.9/task_5h_probe.log      探针（submit 调用）
shots/p5k_accepted.png            第 1 轮（提交前后）
shots/p5k_relogin.png             第 2 轮（重登）
server/state/roles.db             missions + roles + role_attr 三张表
```

---

## 7. 仍然缺失 / 待验证（如实）

1. **`award_assets` 二元组含义**（如 `{1=2,2=1290}`）**待验证** ⇒ 目前奖励用显式配置值。
2. **"完成/可提交"标记**在界面上**未复现**（5G 已排除 `process_status` / `target` / `value`）。
3. **NPC 对话 UI 仍未打通**（5C 遗留；`openNpc` 报 `npc_dialogs.luac: attempt to index a nil value`）。
   ⇒ 故本轮提交是**用探针调用客户端 `MissionCtrl:submit`** 完成的，**不是**走 NPC 对话。
4. **客户端重登后会再发一次 `12403`** —— 目前靠幂等兜住；**根因待查**（可能客户端本地缓存了任务）。
5. `12407–12460` / `154xx` / `185xx` / `19500` 等**用途未知**。

---

## 8. Phase 5H–5K 结论

| 项 | 结果 |
|---|---|
| 5H 完成任务 | ✅ 已验证 |
| 5I 领取奖励 | ✅ 已验证（+150 exp / +888 gold，仅一次） |
| 5J 任务持久化 | ✅ 已验证（SQLite，活过服务器重启） |
| 5K 完整回归 | ✅ 通过 |
| 自查与修复 | ✅ **发现并修了 3 个 bug + 1 处自身疏漏** |
| 改 APK 业务 / UI / 新增任务定义 | ✅ 未做 |

**⇒ Phase 5 的「NPC 交互 → 第一条任务完整闭环」中，
「任务」这一侧的闭环（接取 → 提交 → 发奖 → 落库 → 重登）已经完整跑通。**

---

**[WAITING FOR NEXT INSTRUCTION]**
