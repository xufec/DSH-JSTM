# 最小回环 · 第 8 轮（goal round 2/20）★★★ 配方找到并**复现成功**：连接 + 登录 + 心跳稳定 + 客户端开始收帧

> 时间：2026-10-01 14:00–14:15 ｜ 目标 APK 1.4.9 ｜ 本轮目标：把上一轮遗留的"复现 v27 帧交换"做出来。

---

## 〇、一句话结论

> **配方找到了，而且这次是"有原理、可复现"的**：
> ① 跳过 `net_manager:Stop()`（否则客户端启动链会死等）
> ② 自己调 `initInstance()`
> ③ ★ **再调 `GameNet:restartNetManager()`** —— 这是本轮从**静态反汇编**里挖出来的关键一步
> 结果（客户端 `dsh_v35.txt` / 服务端 `live7_stdout.log`）：
> `conn=true netid=1`，服务端收到 **`10001 ×1 → 1110 ×1`（登录+角色列表）**，
> 之后 **`1199` 心跳 34 次**双向稳定；同一连接上抓包 `:9000` **65 个数据包**。
> 下一版（v36）继续稳定：**`>> 1199 ×70 ↔ << 1199 ×70`**，
> 且客户端自己的探针报告里 **`recv_28`** —— **它开始收到我们服务端的帧了**（此前历轮恒为 `recv_0`）。

---

## 一、★ 本轮的关键：从反汇编里挖出"被拆掉之后要重新拉起网络对象"

### 1.1 静态证据（本轮新做，不依赖模拟器）

工具：`tools/luac_defs.py`（方法→proto 映射）+ `tools/dump_proto.py`（按 proto 反汇编）。

```
gamenet.luac 定义表（proto#31 里 TSETS 出来的方法）：
  SetLoginServerInfo      -> proto#8   bc=5
  ConnectLoginServer      -> proto#10  bc=44
  AsyncConnectLoginServer -> proto#12  bc=56
  restartNetManager       -> proto#29  bc=29     ★ 就是它
  stopNetManager          -> proto#30  bc=21
  doOneMsg                -> proto#20  bc=48
  initSchedule            -> proto#2

proto#29 restartNetManager 的常量池与指令（原样）：
  strings: 'initSchedule','Start','restartNetManager','game_net_id','OnNetDisconnect',
           'print','isnull','tolua','sharedNetManager','CCNetManager','net_manager'
  0  GGET tolua ; 2 TGETS 'sharedNetManager' ; 3 CALL
  4  TSETS 'net_manager'        ← self.net_manager = CCNetManager:sharedNetManager()
  ... 21 TGETS 'net_manager' →（随后 Start）
  ⇒ **重启网络的正规做法就是它**：重新取共享 net manager 并 `Start()`

proto#12 AsyncConnectLoginServer 的前置条件（原样）：
  0 TGETS is_login_server_connected → 1 IST → 2 JMP      （已连则直接返回）
  3 TGETS in_async_connect       → 4 ISF → 5 JMP
  7 TGETS is_login_server_info_set → 8 IST → 9 JMP
 10 GGET print ; 11 KSTR 'Please set login server info before async connect!'
 21 TGETS net_manager ; 23 TGETS 'ConnectAsyn' → CALL
  ⇒ 它只是"检查三个标志 + 调原生 ConnectAsyn"；**完成回调 OnAsyncConnected 才置 is_login_server_connected**
```

### 1.2 这解释了 v31~v34 的全部失败

`initInstance()` 会 `stopNetManager`（内部调原生的 `Stop()`/`DeleteMe()`）⇒ **网络对象被拆掉**。
此后无论怎么 `SetLoginServerInfo` + `AsyncConnectLoginServer`（参数都对，v34 已证 `nargs=2, port=9000`），
**都没有可用的 net 对象**，所以 `conn` 恒 `false`。
**必须补 `restartNetManager()`** —— 事实也正是如此。

---

## 二、本轮实测（v35 / v36）

| 版本 | 配方 | 客户端侧 | 服务端侧 | 判定 |
|---|---|---|---|---|
| **v35** | 跳 `Stop` + `initInstance()` + **`restartNetManager()`** | `v35_restarted=ok=true`；`conn=false` → **`conn=true netid=1`** 并保持 | `=== 连接` ×1；**`>> 10001 ×1`、`>> 1110 ×1`、`<< 1110 ×1`、`>> 1199 ×34 ↔ << 1199 ×34`**；抓包 65 个数据包 | ✅ **成功** |
| **v36** | v35 + 连上稳定 6 拍后 **dump UI 坐标** | `v36_conn=stable streak=6`；UI dump 完成 | `>> 10001 ×2`、`>> 1110 ×2`、`<< 1110 ×2`、**`>> 1199 ×70 ↔ << 1199 ×70`** | ✅ 稳定复现 |

### 2.1 最有价值的一条新信号

客户端**自己的探针**报告：`t=state&v=t_11355_scene_nil_role_nil_recv_28`
—— `recv_28` 表示**客户端已收到 28 个来自我们服务端的帧**。
历轮这个数**恒为 `recv_0`** ⇒ **双向通路这次真的通了**。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★ **可复现的配方**：`跳 Stop → initInstance → restartNetManager`（两轮连续成功：v35、v36）。
2. ★ **真机 ↔ 最小回环服的稳定双向连接**：登录（1110）成功、心跳 70 次双向、客户端 `recv_28`。
3. ★ **根因与修法都有出处**：`restartNetManager` 是从 `gamenet.luac` 反汇编挖出来的，不是猜的。
4. 一条新的**负结论**（有价值）：**光有"参数正确的 SetLoginServerInfo + AsyncConnectLoginServer"不够**，
   必须先把网络对象重新拉起来 —— 这解释了 v31~v34 的 4 次失败。
5. 静态工具链跑通：`luac_defs.py` / `dump_proto.py`（本轮第一次真正用来定位方法签名）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 客户端发 `10102`（登录指定角色） | ❌ 仍停在"选角色"这一步（只有 1110 + 心跳） |
| 2 | 进场景（10200/10201）、任务、战斗、结算、掉落、提交、奖励 | ❌ 全部未开始 |
| 3 | 那条 UI dump 的可点列表**没有文字标签**（全是 `?[nil]`） | ⚠️ 没法据此判断该按哪个按钮（下一轮要修 dump） |

---

## 四、下一轮直接照做（优先级）

1. **让客户端发出 `10102`** —— 先走静态这条路（v37 已把范围缩到"它的前置条件"）：
   - (a) ★ 反汇编 `denglu_ctrl.luac` 的 `request10102Login`，找出它检查的状态字段并直接补齐；
   - (b) 备选：修 UI dump 的**标签提取**（现在取不到 `Label` 文本），再按坐标长按"进入游戏"。
2. 一旦 `10102` 发出 ⇒ 本服会推 `10200/10201`（进场景）⇒ 再往 `10300/12400/20002/12403/10502` 推进。
3. 纪律不变：每轮留客户端落盘证据 + 抓包；0 事件结论必须带同窗口自证。

---

## 四之补、★ v37 追加实验：`request10102Login` 调得动，但**帧没发出去**

| 观测 | 结果 |
|---|---|
| 入口存在性 | `v37_entry=DengluCtrl=table request10102Login=function` ✅ |
| 调用结果 | `v37_login10102=ok=true ret/err=nil`（**函数返回成功**） |
| 服务端是否收到 `10102` | ❌ **没有**（`live7` 里搜不到 `>> 10102`） |
| 同期的其他证据 | 客户端探针报 `n10201 SceneController.on10201_wrapped`、`recv_25/recv_28` ⇒ 双向通路仍是好的 |

⇒ **判定**：`request10102Login` 内部有**未满足的前置条件**（最可能是"UI 里还没选中角色/服务器"这类状态），
于是它像早前那些 `SendProtocal` 调用一样"返回成功但不产出字节"。
**下一轮的第一步就是静态解它**：用 `tools/luac_defs.py` + `tools/dump_proto.py`
把 `denglu_ctrl.luac` 里 `request10102Login` 的实现反汇编出来，看它到底检查哪些字段
（与 `restartNetManager` 那次一样 —— 静态反汇编一次命中，比在模拟器里瞎试快得多）。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_minloop_block.lua` | 现为 **v36**：跳 Stop + initInstance + **restartNetManager** + 连上后 dump UI 坐标 |
| `server/dsh_minloop_probe.lua` / `patched/jstm_minloop.apk` | 探针与装机包（过 `lua-check` 真闸门） |
| 设备内 `files/dsh_v35.txt`（★ 配方成功）、`dsh_v36.txt`（+UI dump） | 客户端原始证据 |
| `logs/minloop/live7_stdout.log` | 服务端侧：`10001/1110/1199` 双向交换（本轮核心证据） |
| 静态分析 | `tools/luac_defs.py`（方法→proto）、`tools/dump_proto.py`（proto#29/12 反汇编） |
