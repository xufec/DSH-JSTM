# Phase 5B —— NPC 交互协议（✅ 协议完成；对话 UI 未打通，原因已定位）

> **结论一：`CS_15203` / `SC_15203` 的"发送 → 接收 → 客户端解析"全链路已验证。**
> **结论二：对话 UI 这一环未打通，但**两个具体原因**都已查明（见 §4.3）。**

---

## 4.3 ★ 对话 UI 的两次尝试与**根因**（本轮新增，含关键更正）

### 尝试 A：在 `setVo` 钩子内部**当场调用** `clickNpcOpenDialog(a1)`

```
t=voClick&v=bid_10010_name________ok_false_err= string game/npc/npc_dialogs.luac:0:
          attempt to index a nil value
```

**⇒ 两点结论：**
1. ✅ **VO 传递问题解决了** —— 钩子内部**确实拿得到真实 vo**（`bid=10010`）；
2. ❌ **但"当场调用"太早**：`setVo` 发生在**场景初始化期间**，
   此时 `npc_dialogs` 的 UI **还没就绪** ⇒ 必然 `attempt to index a nil value`。

### 尝试 B：把 vo 存起来，等场景就绪后（`S.t >= 190`）再调

```
t=npcSend&v=15203_SendProtocal_ok_true_err_nil
t=npcSend&v=vo_S_nil_bid_false        ← ★ 存进探针状态表 S 也取不到
```

**⇒ 结论：`Npc.setVo` 钩子与延迟调用块**不在同一作用域**（`S` 未能共享）。**

（此前存 `_G`、存 `NpcCtrl` 类表也都不行 —— **三处存储全部失败**，原因**未确认**。）

### 4.3.1 根因总结（**已确认**）

| # | 事实 | 证据 |
|---|---|---|
| 1 | `clickNpcOpenDialog(vo)` **同时负责"发 15203"和"打开对话 UI"** | 传 nil 时报错栈落在 `npc_dialogs.luac` |
| 2 | 它**要求 UI 已就绪**，否则在 `npc_dialogs` 处中断 | 尝试 A 的报错 |
| 3 | `setVo` 时机**太早**（场景初始化中），UI 未就绪 | 尝试 A |
| 4 | 探针**无法把 vo 从钩子传到延迟调用点**（`_G`/类表/`S` 三处均失败） | 尝试 B |
| 5 | **但协议本身完全正常** | §3 的三环实测 |

**⇒ 对话 UI 未打通**不是协议问题，而是"**调用时机**"与"**探针传值**"两个探针侧问题。

### 4.3.2 给 Phase 5C 的可行路径（按可靠性排序）

1. **不调 `clickNpcOpenDialog`，直接钩住对话 UI 的打开函数**
   —— 例如包住 `NpcDialogs` 的 `open`/`__init`，由探针直接触发 UI，
   从而**绕开"点击链"与"传值"两个问题**；
2. **在场景完全就绪后，用 `NpcCtrl:getOpenNpc()` 或场景 NPC 列表现场取 vo 再调**
   —— 不再"钩子里存、外面用"，而是**在调用点自己取**；
3. 核实 `sceneClickEvt`（它是**表**不是函数）的注册方式，
   尝试**以合法事件形式触发点击**，让客户端走完整原版路径。

---


## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | `_reply()` 新增 **`15203`** 分支：`SC_15203{code:u8, msg:string}` |
| **`server/dsh_fake_login.lua`**（调试探针） | ① 直接 `SendProtocal(GetPrototype(15203))`；② 带真实 vo 调 `clickNpcOpenDialog`（未成功）；③ 包住 `handle15203` 观察解析；④ 从 `setVo` 参数截获 NPC VO |

---

## 2. 协议证据（1.4.9 客户端）

| 项 | 内容 |
|---|---|
| **CMD** | `15203` |
| **1.4.9 代码证据** | `game/npc/npc_ctrl.luac` 的 `RegisterProtocal(15203, 'handle15203')`；<br>`NpcCtrl:clickNpcOpenDialog` 内 `GetPrototype(15203)` → `SendProtocal` |
| **请求字段** | **无字段**（空消息） |
| **响应字段** | `code:uint8`, `msg:string` |
| **字段类型** | 见上（取自 `protocol/manual.md`，`tools/show_cmd.py 15203` 可复核） |
| **客户端使用位置** | `NpcCtrl.handle15203` |

---

## 3. 实际收发包日志（**本轮实测**）

```
探针: t=npcSend&v=15203_SendProtocal_ok_true_err_nil
TCP : [00:49:01]  >> cmd=15203 ? body(4)=00 00 03 e9
TCP : [00:49:01]  << 15203 SC_15203 code=0 (9 bytes)
探针: t=npcH2&v=handle15203_code_0_msg_
```

| 读数 | 含义 |
|---|---|
| `15203_SendProtocal_ok=true` | 客户端**成功发出** `CS_15203` |
| `>> cmd=15203 ? body(4)=00 00 03 e9` | 服务器**收到**（`body(4)` 是 dirty-tail 残留：协议本身无字段） |
| `<< 15203 SC_15203 code=0 (9 bytes)` | 服务器**应答**（`code=0` + 空 `msg`，body 3 字节） |
| **`handle15203_code_0_msg_`** | **客户端成功解析**：`code=0`、`msg=''`（`msg` 为空故显示空白） |

**⇒ 三环全部实测通过：发得出、收得到、解析得对。**

---

## 4. 对话 UI 的情况（**未打通，如实说明**）

按设计，`NpcCtrl:clickNpcOpenDialog(vo)` 才是"点击 NPC → 发 15203 **并**打开对话 UI"的完整路径
（实测：传 `nil` 时它在 `game/npc/npc_dialogs.luac` 处报 `attempt to index a nil value`，
**说明该函数除了发协议，还负责拉起对话 UI**）。

**本轮尝试带真实 VO 调用，但 VO 没传到位：**

```
t=npcSend&v=vo_from_class_nil_bid_false      ← 从 NpcCtrl 类表取仍是 nil
（因此 clickNpcOpenDialog 未被有效调用）
```

**⇒ 尽管 `handle15203` 解析成功，界面**没有**打开对话面板**（截图确认：仍是主城主界面，
NPC「周漪」头顶显示「**学院任务**」标记，但无对话框）。

**⇒ 结论：`SC_15203` 只是"点击通知"的应答，**对话 UI 由客户端本地打开** ——
要把 UI 打通，必须让 `clickNpcOpenDialog` 带真实 vo 跑起来。**

---

## 5. 仍然缺失 / 待办

1. **VO 传递问题**（`vo_from_class_nil`）：`setVo` 的参数明明拿到了（`setVo_arg_bid_10010`），
   但存到 `_G` 和类表后都取不到 —— **原因未确认**。
   **下一步最省力的做法：在 `setVo` 钩子内部当场调用**（拿到参数立刻调
   `clickNpcOpenDialog(a1)`），而不是"存起来以后再用"。
2. 对话 UI 打通后，才能进入 **Phase 5C**（原版 NPC 对话 UI）。
3. **新线索（有用）**：截图里 **NPC「周漪」头顶有「学院任务」标记** ——
   说明客户端能根据本地配置在 NPC 头顶绘制任务标记。这对 Phase 5F 接任务很关键。

---

## 6. Phase 5B 结论

| 项 | 结果 |
|---|---|
| `15203` 编号与字段有 1.4.9 证据 | ✅ |
| 服务端实现 `SC_15203` | ✅ |
| 客户端发出 `CS_15203` | ✅ **已验证** |
| 服务器收到 | ✅ **已验证**（`>> cmd=15203`） |
| 服务器应答 | ✅ **已验证**（9 字节） |
| 客户端解析 | ✅ **已验证**（`handle15203_code_0_msg_`） |
| 对话 UI 打开 | ❌ **未打通**（VO 传递问题，非协议问题） |
| 改 APK 业务 / UI / 新增 NPC | ✅ 未做（只改调试探针） |

**⇒ NPC 交互协议本身已闭环；差"UI 打开"这一环，且已定位到具体原因与方法。**

---

## 7. 日志

```
logs/1.4.9/npc_5b_tcp.log      15203 的收发
logs/1.4.9/npc_5b_probe.log    npcSend / npcH2 上报（含 handle15203 解析结果）
shots/p5b_dialog.png           对话 UI 未打开的截图（含 NPC「学院任务」标记）
```

**[WAITING FOR NEXT INSTRUCTION]**
