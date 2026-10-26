# 最小回环 · 第 4 轮（自主续跑）—— 用"字节码里的真名"驱动：全链返回成功，字节仍然不出进程

> 时间：2026-10-01 12:30–13:00 ｜ 目标 APK：1.4.9 / `com.shiyue.dldl.ewan.qihoo`
> 本轮按第 3 轮给出的路线执行：**绕开 UI，直接驱动"选服/进服"**，并把驱动换成不受调度重置影响的挂点。

---

## 〇、一句话结论

> 本轮把"猜 API"彻底换成"**从字节码常量池读真名**"，并把驱动从 `cc.Director` 调度改挂到
> **每帧的 `GameNet.doOneMsg`**（v21 起生效，不会再"跑几拍就没了"）。
> 结果：**建连成功**（服务端 `=== 连接 127.0.0.1:12530`）、
> **`request10001ReConnectSocket()` / `request1110Role()` 都真实存在且返回 true**、
> 每帧泵 75+ 次、连接状态保持 true —— **但 9000 端口仍然 0 个数据包**。
> ⇒ 结论收敛为一句：**客户端 Lua 侧的"发送成功"是假的成功；字节从未离开进程**，
> 这不是 UI/点击问题，也不是服务端问题。

---

## 一、本轮完成（逐项）

| # | 事项 | 结果 | 证据 |
|---|---|---|---|
| 1 | **不再猜方法名**：从 `anzbao/jstm.apk` 的字节码常量池提取真实符号 | ✅ | `denglu_ctrl.luac`：`isOnBtnEnter`、`request10001ReConnectSocket`、`request1110Role`、`request10102Login`、`checkServerState`、`login_game_request`…；`denglu_mgr.luac`：`managerServerListByJsonObj`、`requestDefaultServerList`、`getServerList`… |
| 2 | 找到列表消费函数的**持有者** | ✅ `DengluMgr.inst` | v19：`ml19_owner=n=1 [DengluMgr.inst]` |
| 3 | **修驱动挂点**（v20 只跑了 3 行就停） | ✅ v21 起挂在 `GameNet.doOneMsg` | v21：`ml21_hook=doOneMsg_hooked`，之后 5 个阶段全部执行 |
| 4 | 让错误**可见**（v20 用 `pcall` 把异常吞了，等于自断证据） | ✅ 改 `xpcall + traceback` | v21 起错误文本直接落盘 |
| 5 | **重新建连**（v19–v21 漏了这步，所以连连接都没有） | ✅ | 服务端 `[12:43:28] === 连接 127.0.0.1:12530`；客户端 `ml22_conn=YES tries=1` |
| 6 | 调客户端**自己的**握手入口 | ✅ 返回 true | `ml22_reconnect ok=true`、`ml22_req1110 ok=true`、`ml22_methods` 两个都是 function |
| 7 | 每帧泵 | ✅ | `ml22_watch=n=10 conn=true pumps=75` |

---

## 二、本轮没完成

| # | 项 | 状态 | 说明 |
|---|---|---|---|
| 1 | 客户端发出第一个协议帧 | ❌ | `tcpdump 'port 9000'`：**0 个带数据的包**；服务端 0 个 `-- recv` |
| 2 | 喂服务器列表 | ❌ 仍报错 | `managerServerListByJsonObj` → `attempt to concatenate field 'zone_id' (a nil value)`；我已经在**条目内、顶层、data 内**三处都给了 `zone_id`，仍为 nil ⇒ 它读的**不是我给的那张表**（很可能它接收的是"已解开的 data"或"JSON 字符串"） |
| 3 | `isOnBtnEnter` | ❌ 不存在于 ctrl 实例 | `no_method` ⇒ 它更像是 `denglu_view` 里注册的**事件名**，不是 ctrl 的方法 |
| 4 | 真机跑完整条回环 | ❌ | 同 1 |

---

## 三、★ 该怎么继续（下一轮第一件事，已缩到很窄）

1. **查 `gn:GetLoginNetId()` 的返回值**（最可能一击命中）：
   若为 `nil`/`-1`，说明**原生层没把这个连接登记成"游戏网络"** ⇒
   `Encode()` 写进的缓冲区无人发送 —— 这正好解释"Lua 全 true、抓包 0 包"。
   若它有效，则问题在 `net_manager` 的发送条件上。
2. **把 `net_manager.__index` 这个函数问全**：v10 只问了 20 个候选名（只有 `Update` 命中）。
   下一轮应**按字节码里的真实符号表**去问（而不是我列的英文猜名）。
3. **换一条根本不同的路**（若 1/2 都不通）：不指望这个 build 的 Lua 发送路径，
   改为**在原生层观察/介入**（frida 必须先自证钩子有效，见第 2 轮的教训）。
4. **喂列表的正确形状**：先 `getServerList()` 看 mgr 自己认的条目长什么样，
   再按那个形状构造（比继续加层级靠谱）。

---

## 四、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_minloop_block.lua` | 现为 **v22**：每帧驱动 + 强制建连 + `request10001ReConnectSocket`/`request1110Role` + 每帧泵 |
| `server/dsh_minloop_probe.lua` / `patched/jstm_minloop.apk` | 探针源与装机包（过 `lua-check`） |
| 设备内 `files/dsh_srv.txt`(v19)、`dsh_enter.txt`(v20)、`dsh_e21.txt`(v21)、`dsh_e22.txt`(v22) | 逐轮原始证据 |
| 设备内 `/data/local/tmp/s*.txt` | 每轮的 tcpdump 抓包（判"有没有真发帧"） |
| `logs/minloop/live*.log` | 服务端侧：连接、字节级 recv、网关 POST 节奏 |

---

## 五、★ 本轮追加实验（v23 / v24）：把"原生层"这条线也走完

| 实验 | 假设 | 结果 | 判定 |
|---|---|---|---|
| **v23** | "原生层没把这个连接登记成游戏网络 ⇒ `Encode()` 写进无人发送的缓冲区" | `gn:GetLoginNetId()` = **1**（number，有效） | ❌ **假设否证**（连接确实登记了） |
| **v23** | 顺带看 mgr 认的服务器条目形状 | `getServerList()` → `nil`、`getServerData()` → `nil` | ⇒ 我喂的列表**根本没进去**（zone_id 报错的同源问题） |
| **v24** | "`net_manager:Start()` 才是收发开关（`initInstance` 里出现过对称的 `Stop()`）" | `ml24_start=ok=true`；随后重走客户端自己的 `request10001ReConnectSocket()`/`request1110Role()` 都真返回 true；`ml24_watch netid=1 conn=true` | ❌ **仍 0 数据包**（"Start 是开关"也否证） |

**至此，Lua 侧能想到的开关全部试过并全部返回成功**：
建连（net id 有效）→ 客户端自己的握手入口 → 每帧泵（`net_manager:Update()` + `doOneMsg()`）→ `net_manager:Start()`。
**抓包始终 0 个数据包**（`tcpdump 'port 9000'`，五轮独立抓包）。

> ★ 综合判定（CONFIRMED）：**这个 build 在"由探针驱动"的状态下，客户端的外发字节通路不工作**；
> 所有 Lua 可见的"成功"都是**假的成功**。它依赖的额外原生状态，只有在客户端**自己完整走完启动流程**时才会就绪
> —— 而那条流程在本环境里停在加载界面（隐藏对话框不可点、`GameNet:Update` 这个函数压根不存在）。
> 这是**客户端/环境侧**的结论，不是最小回环服的缺陷（服务端侧已用控制客户端 + 8831 真机帧回放双重验证）。

---

## 六、累计状态（总账）

| 维度 | 状态 |
|---|---|
| 最小回环服务器（`server/minloop/`，1180 行） | ✅ 自检 **44/44**；真机真实帧回放 **292 帧 / 0 规格不符 / 0 危险应答** |
| 客户端能起来并请求自建服网关 | ✅（探针放行后客户端自己 `POST /gateway/mobile/json`，网关应答已对齐参考服） |
| 客户端连上自建服 TCP | ✅（服务端日志有 `=== 连接`） |
| 客户端发出协议帧 | ❌ **0 字节**（Lua 侧全 true，抓包 0 数据包） |
| 真机跑完整条回环 | ❌ 阻塞在上一条 |
