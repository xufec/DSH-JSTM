# 最小回环 · 第 16 轮（goal round 10/20）—— 修好"重启后不建连"；**任务列表补推已被客户端收到**；NPC/任务环在跑

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：查"10102 为何进不了 socket"。

---

## 〇、一句话结论

> 本轮用"发送器全属性对比"把问题钉死，并**修掉了一个真实缺陷**：
> `restartNetManager()` **只换新 net 对象、不发连接**，`SetLoginServerInfo()` **只写 host/port、也不发连接**
> ——所以上一轮的幂等重试里"只重启+设地址"⇒ 客户端 Lua 侧 `conn=true`（旧标志）而
> 服务端**一条 `=== 连接` 都没有**，于是所有 `SendProtocal` 都"返回 true 却没字节"。
> **补上真正的连接调用后**：服务端 **连接 6 次**（此前 0），
> 并且 **`<< 12400 任务列表 push`（第 8 轮加的那条补推）真的发出、且被客户端收到**
> （`recvHook n_9_a1_12403` → 紧接着收到 12400）。
> 客户端侧 `15203`（NPC 对话）处理器以 **code=1** 跑通（`npcH2=handle15203_code_1_msg_`），
> 并发出 `12403`（任务提交）—— **任务/NPC 这条环已经在线上跑起来了**。
> 仍未完成：本实例上 `scene` 仍为 nil、`20002`（战斗）未出现、App 反复重启。

---

## 一、★ 决定性证据：发送器全属性对比（v42）

```
v42_hook=DengluCtrl.SendProtocal
v42_send=ret=true/nil  conn=true netid=1 gid=1 | m_type=cs,m_msg_type=10001,key=game_client,tables=3
v42_send=ret=false/nil conn=true netid=1 gid=1 | m_type=cs,m_msg_type=1110,tables=4
v42_send=ret=true/nil  conn=true netid=1 gid=1 | m_type=cs,m_msg_type=10103,srv_id=1,rid=1001,tables=3
v42_send=ret=true/nil  conn=true netid=1 gid=1 | m_type=cs,m_msg_type=1199,tables=3
v42_send=ret=true/nil  conn=true netid=1 gid=1 | m_type=cs,m_msg_type=1199,tables=3
v42_send=ret=true/nil  conn=true netid=1 gid=1 | m_type=cs,m_msg_type=10102,srv_id=1,rid=1001,tables=3
v42_watch=n=20..140 msg_list_n=0
```

**读法**：
1. `10102` 与 `10001` **属性完全同型**（都是 `m_type=cs`、`conn=true`、`netid=1`、`gid=1`），
   并且 `SendProtocal` **返回 `true`** ⇒ "命令类型不同/被队列扣住"这类假设**都否证**（`msg_list` 全程 0）。
2. 但服务端**收不到 `10102`/`10103`**（`>> 10102` = 0）。
3. 对照服务端日志：这段时间**根本没有 `=== 连接`** ⇒
   **不是"帧发出去了但丢了"，而是"根本没有可供发送的连接"**；
   `conn=true` 只是客户端 Lua 侧的**旧标志**。

### 1.1 根因与修法（本轮自证）

| 调用 | 它到底做什么 | 是否发连接 |
|---|---|---|
| `restartNetManager()` | 取 `CCNetManager:sharedNetManager()` 换新对象 + `Start()` | ❌ |
| `SetLoginServerInfo(host,port)` | 只写 `login_server_host_name/_port` 与 `is_login_server_info_set` | ❌ |
| **`AsyncConnectLoginServer(timeout)`** | 真正发起异步连接（内部 `net_manager:ConnectAsyn`） | ✅ |
| `ConnectLoginServer(...)` | 同步连接（v22/v24 用过、当时确实建连成功） | ✅ |

⇒ 幂等重试从"只 `restartNetManager` + `SetLoginServerInfo`"改成
**"重启 + 设地址 + `AsyncConnectLoginServer(10)`（并补一次 `ConnectLoginServer(5)`）"**。

---

## 二、★ 修好之后（同一套探针，仅这一处改动）

| 指标 | 修前（同轮上半场） | **修后** |
|---|---|---|
| 服务端 `=== 连接` | **0** | **6** |
| 客户端命令种类 | 16 | **27** |
| 任务列表补推（`<< 12400 …补推…`） | 0 | ★ **2** |
| 客户端是否收到该补推 | — | ★ **收到**：`recvHook n_9_a1_12403` 之后紧接着收到 12400 |
| `15203`（NPC 对话） | 1 | **2**（且 `npcH2=handle15203_code_1_msg_` ⇒ 客户端以 **code=1 成功**处理） |
| `12403`（任务提交） | 0 | **2** |

⇒ **第 8 轮加的"任务列表补推"本轮终于被验证：既发出去了、也被客户端收到了。**

---

## 三、完成 / 未完成

### 3.1 完成
1. ★ **否证两条假设**：`10102` 与 `10001` **同型**（不存在"游戏网专属类型"），
   且 **`msg_list` 全程为 0**（不是被队列扣住）。
2. ★ **定位并修掉真缺陷**：`restartNetManager`/`SetLoginServerInfo` **都不建连** ⇒ 必须显式 `AsyncConnectLoginServer`。
3. ★ **补推任务列表已被客户端接收**（`recvHook` 有据），`15203` 以 **code=1** 被客户端处理。
4. 客户端开始发 `12403`（任务提交）⇒ **任务/NPC 环已在线上跑**。
5. 修好 `install()` 的守卫缺陷（本轮自踩：守卫置位早于成功 ⇒ 整轮无数据）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 本实例 `scene` 非 nil | ❌ 仍 `scene_nil`（`v41_retry scene=nil`；上一台实例 `live9` 曾成功） |
| 2 | `12400`（客户端**主动**请求任务列表） | ❌（只收到服务端补推） |
| 3 | `12402`（接取）/ `20002`（战斗） | ❌ |
| 4 | 战斗→结算→掉落→提交→奖励 | ❌ |
| 5 | App 稳定性 | ⚠️ 反复重启（`recv_0`、tick 计数重置） |

---

## 四、下一轮直接照做（优先级）

1. ★ **把"每台实例都能进场景"搞清楚**：同一份 APK + 同一份服务端，在 16384 实例上曾进场景、
   在 7555 实例上始终 `scene_nil` ⇒ 先对比两实例的**存档/资源状态**
   （`local_srv_id`、`last_login_accounts`、是否缺 CDN 资源）。**这是当前最大变量。**
2. 若 `scene` 起来：本服已经会推 `12400`、并已实现 `12402/20002/20010/…/10500`，
   直接用**UI dump + 长按**驱动任务面板/怪，走完 `12402 → 20002 → 20020 → 10500 → 12403 → 奖励`。
3. 若 `scene` 起不来：把"服务端侧能独立验证的部分"继续做扎实（本轮回环命令已实现且自检 45/45），
   并把客户端侧的门做成**每次运行都落盘**的诊断（哪一步没走到）。
4. 纪律：`adb` 固定 7555 + 每次 `adb root`（第 15 轮教训）；每轮先确认环境未位移。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_ml42_add.lua` | ★ 新增：发送器全属性观察（`m_type`/字段/连接状态/返回值） |
| `server/_ml41_add.lua` | ★ 修：幂等重试补上**真正的连接调用**（`AsyncConnectLoginServer` + `ConnectLoginServer`） |
| `logs/minloop/live10_stdout.log` | 本轮证据：连接 6 次、`12400` 补推 2 次、`15203`/`12403` |
| 设备内（7555，需 root）`files/dsh_v42.txt` | ★ 发送器对比原始数据 |
