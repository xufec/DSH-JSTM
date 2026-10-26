# 最小回环 · 第 15 轮（goal round 9/20）—— 环境位移（adb 端口 16384→7555）+ 幂等重试已生效；补推仍未验证

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：把"进场景"变稳定，并验证上一轮的任务列表补推。

---

## 〇、一句话结论

> 本轮先踩到一个**环境位移**：MuMu 实例的 adb 端口从 **16384 变成 7555**（16384 拒绝连接），
> 且该实例的 `/data/user/0/.../files/` **默认不可读**（要重新 `adb root`）——
> 这让我一度**误判"探针没在跑"**（其实文件在，只是没权限读）。
> 用 root 读到真实内容后：**配方在跑**（`Stop` 跳 → `initInstance` → `restartNetManager` → `call10102 ok=true`），
> 我新加的**幂等重试也确实触发了**（`v41_retry scene=nil 第 1 次 restartNetManager ok=true`），
> 但这次会话**scene 仍为 nil**，且客户端**没有把 10102 发上线**（服务端 `>> 10102` 计数 0）。
> ⇒ **任务列表补推依旧是 UNVERIFIED**（没有任何会话走到"在场景内 + 收到 10300"）。

---

## 一、本轮完成

| # | 事项 | 证据 |
|---|---|---|
| 1 | ★ **诊断"进场景不稳定"的工具落地**：给配方三步加时间戳思路 + **判据**（`SceneModel.scene`/`getScene()`） | `server/_ml41_add.lua` |
| 2 | ★ **幂等重试生效**：连上但 scene 仍 nil 时，隔 10 拍再 `restartNetManager()`（最多 3 次） | 设备内 `dsh_v41.txt`：`v41_retry=scene=nil 第 1 次 restartNetManager ok=true n=10` |
| 3 | **环境位移定位**：adb 端口 16384→7555；`files/` 需 root | `adb devices` 只剩 `127.0.0.1:7555`；`ls files/` → Permission denied；`adb root` 后可读 |
| 4 | **纠正一次自误判**：我曾据此认为"探针块没运行"，实际是**权限问题** | root 后 `dsh_v39/v40/v41` 俱全（v39 更新时间 14:54） |
| 5 | 自检保持 **45/45** | `python server/minloop/selftest.py` |

### 1.1 本次会话的客户端实况（`dsh_v39.txt`，root 后读取）

```
v39_wrap=Stop -> noop
v39_stop_skipped=called
v39_initInstance=called
v39_restarted=ok
v39_hook=CommonAlert.show / DengluMgr.managerServerListByJsonObj
v39_msgl_list=type=table ; v39_msg_list=n=0 []
v39_game_net_id=1
v39_call10102=ok=true          ← 调用了 request10102Login 且返回成功
v41_retry=scene=nil 第 1 次 restartNetManager ok=true n=10   ← 新加的幂等重试触发
```

而服务端 `live10` 侧：`>> 10102` **0 次**、`>> 10300` 1 次、命令种类仅 **16**、探针 `state=scene_nil_role_nil_recv_0`
⇒ **"函数返回成功"与"帧真的上线"仍然是两件事**（本轮再次复现该现象）。

### 1.2 新观察到的一处实例差异

```
dsh_v40.txt:  v40_read=local_srv_id= type=string      ← ★ 本实例里它是**空串**
```
（上一台实例里是 `"1"`；我第 4 轮把它设成 `'1'` 才修好了列表消费。）
⇒ **该修复依赖实例状态**，需要在探针里**无条件校正**（本轮的 v40 块已是"读到就设"，但要确认它在**每次启动**都执行且生效）。

---

## 二、未完成（如实）

| # | 项 | 状态 |
|---|---|---|
| 1 | **任务列表补推的效果** | **UNVERIFIED**（无会话走到触发点；`live10` 里"任务列表 push"计数 0） |
| 2 | 场景进入的**稳定性** | ❌ 本轮会话 `scene=nil`（幂等重试触发 1 次仍未成功） |
| 3 | `10102` 上线 | ❌ 服务端计数 0（尽管 `call10102 ok=true`） |
| 4 | `12400/12402/20002` | ❌ |
| 5 | 战斗→结算→掉落→提交→奖励 | ❌ |

---

## 三、下一轮直接照做（优先级）

1. **把所有 adb 操作固定到 7555**（并在每次操作前 `adb root`）——
   本轮的误判就是端口+权限造成的；把这条写进脚本，避免再浪费一轮。
2. **把 `local_srv_id` 的校正做成"无条件 + 每次启动"**（它在本实例是空串），
   并**先验证列表消费 `v39_consume_ret=ok=true`**（这是第 4 轮已经打通的一环，不能丢）。
3. **让 `10102` 真正上线**：既然 `call10102 ok=true` 但服务端收不到，
   说明"调用成功≠发包成功"；下一轮应在 **10102 的 `SendProtocal` 前后**加探针
   （复用第 10 轮那套 `v38_send` 观察：当时 `m_msg_type=10102` 出现过），
   确认它在**新实例**上是否仍进入发送器，以及发送器返回什么。
4. 只有 `10102` 上线、scene 起来之后，**才能**验证任务列表补推与后续 `12402/20002`。
5. 纪律：每轮先把"环境是否位移"确认掉（端口/root/进程），再解读日志。

---

## 五、★ 本轮追加：卡点被精确收窄到"**10102 发不出去**"

root 后补读该实例的完整证据：

```
dsh_v39.txt: v39_consume_ret=ok=true err=nil        （×2）   ← 列表消费**已经好了**
dsh_v40.txt: v40_set=setStringForKey(local_srv_id,1) ok=true now=1   ← 校正也生效
dsh_v41.txt: v41_retry=scene=nil 第 1 次 restartNetManager ok=true n=10
dsh_v39.txt: v39_call10102=ok=true                  ← 调用了 request10102Login 且返回成功
服务端 live10: >> 10102 = 0 次                      ← 但**帧没上线**
```

⇒ **本轮把当前唯一卡点钉成一句**：
> **配方（Stop 跳 + initInstance + restartNetManager）正常、服务器列表消费正常、
> `request10102Login` 调用返回成功 —— 但 `10102` 的帧没有发出去**
> ⇒ 服务端自然不会回 `10102`/`10200`/`10201` ⇒ `scene` 恒为 nil。

这与第 10 轮（`v38_send=SendProtocal m_msg_type=10102` 出现过却无字节）是同一类现象，
但**换了实例后仍未解决**，且**列表消费这一环现在是好的** ⇒ 可以把矛头完全集中到
"**`SendProtocal` 对 10102 为何不产出字节**"。

**下一轮第一件事**（复用已验证的观察方法）：
在该实例上重新挂 `DengluCtrl.SendProtocal` 观察器，确认：
① `10102` 是否仍进入发送器（`m_msg_type=10102`）；
② 进入时 `IsLoginServerConnect()` / `GetLoginNetId()` 的值；
③ 发送器返回值；
④ 若进入却没字节 ⇒ 去查 `SendProtocal` 内部对 `m_msg_type` 的分支
（`gamenet.luac` 里有 `recordMsg/replay/msg_list` 一族，可能与"游戏网"未建立有关）。

---

## 六、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_ml41_add.lua` | ★ 新增：场景判据 + **幂等重试**（连上但 scene nil ⇒ 再 restartNetManager，最多 3 次） |
| `server/dsh_minloop_probe.lua` | = 原探针 + v39(配方/三问钩子) + v40(`local_srv_id`) + **v41(幂等)**，过 `lua-check` |
| 设备内（7555 实例，需 root）`files/dsh_v39.txt` / `dsh_v40.txt` / `dsh_v41.txt` | 本轮客户端原始证据 |
| `logs/minloop/live10_stdout.log` | 服务端侧：本轮会话未出现 `10102`，任务补推计数 0 |
