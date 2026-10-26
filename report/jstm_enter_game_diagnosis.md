# 《绝世唐门》「点击进入游戏 → 空白提示框」诊断报告（实测复核）

> 对象：`patched/jstm_fakelogin.apk`（**1.4.9 / `com.shiyue.dldl.ewan.qihoo`**）
> 设备：MuMu 模拟器 `127.0.0.1:16384`（22041211A / Android 12）
> 服务器：`server/mock_server.py`（`config.json`，HTTP :8080 + 游戏服 TCP :9000，host `10.0.2.2`）
> 数据采集时段：2026-09-16 09:18–09:23（一轮干净重启 + 逐连接实测）
> **所有判定均来自本机抓到的真实数据（logcat / DSH_PROBE / tcp.server 抓包 / 屏幕截图），无任何编造。**
> 作用域：按你的选择，本报告以**当前已安装并运行的 qihoo 1.4.9** 为测试对象；baidu2 1.4.11 未在本轮实跑。

---

## 〇、一句话结论（先说真话）

> **在当前构建 + 当前本地服务器上，「标题=提示 / 正文空白 / 按钮=确定」的空白提示框 没有复现。**
>
> 实测到的是：**点“进入游戏”后，登录握手本身成功**（1110→10102→10200/10201 全通、角色数据到达、客户端继续发背包/角色信息请求），
> 但**客户端场景始终建不起来（`getScene()==nil`）**，随后**客户端主动断开并反复重连**，界面停留在选服/登录页，伴随一个**有 6 个汉字正文**（非空白）的提示框。
>
> 也就是说：你描述的“空白框”**不是**当前服务器/构建正在触发的现象；真正卡住的是**“登录成、进不了场景”的登录循环**。

我先把两条历史上已被确认的“空白框根因”用本轮真实数据复核后在第五节给出结论，再用 T0–T10 时间线把**当前真实行为**完整还原。

---

## 一、真实抓到的关键证据（逐条有出处）

### 证据 1 —— 服务端 DSH_PROBE：整个运行期 0 次“空白弹窗”

客户端注入的钩子会把每次弹窗**按“是否 NIL / 长度”**上报到 `http://10.0.2.2:8080/DSH_PROBE`（`server/logs/http.log`，09:1x–09:23 段）：

```
[09:18:32] hit_on1110Rolelist code=1_type=table      ← 1110 走“成功”分支，不是 message('')
[09:18:49] hit_on10102Login   code=0_type=table
[09:18:49] t=alert&v=CommonAlert_len6               ← 6 个字符，有正文
[09:19:14] acct set=true ; netTry ok ; handlerHooks installed
[09:19:20] relogin ok → on10103ReLogin code_0 → on10102Login code_0
[09:19:20] t=alert&v=CommonAlert_len6               ← 有正文
[09:21:16] hit_on1110Rolelist code_1 ; hit_on10102Login code_0
[09:21:16] t=alert&v=CommonAlert_len6               ← 有正文
```

- `message NIL`：**0 条**　`CommonAlert NIL`：**0 条**
- 全部 `t=alert` 都是 `CommonAlert_len6`——即正文是 **6 个字符的中文**，不是空白。
- `denglu_ctrl.on1110Rolelist` 每次都收到 `code=1`（成功分支），因此旧根因 1 的 `message('')` 分支从未执行。

> 注：钩子只上报“长度/NIL”而不上报正文（上轮踩坑：正文含中文会被 URL 安全替换成全下划线，区分不出空串）。所以**6 字提示的具体文本尚未落库**——见“尚未确认”。

### 证据 2 —— 游戏服 TCP 抓包：每次连接都完整互发登录帧

`server/logs/tcp.log`（09:18–09:23）逐连接序列完全一致、反复出现：

```
connection from 127.0.0.1:xxxx
>> cmd=10001 CSFirstPack          body: key="game_client"
>> cmd=1110  CSAccountLogin       10 字段 = account=dsh_local, timestamp=1789521557,
    enter_srv_id=1, platform=ewan, device_id=Redmi_rubens(22041211A),
    gettui_cid=ca221ee11822..., idfa, token=dsh_token, channelId=1, sign=dsh_sign
<< 1110 SCAccountLogin reply, roles=1 (code=1)
>> cmd=10102 RoleLogin 登录指定角色  body: rid=1001, srv_id="1"
<< 10102 SCRoleLogin reply (code=0)
<< 10200 SCRoleEnter (server push) bid=1 @(100,100)
<< 10201 SCMapGird (server push) roles=1
>> cmd=10502 背包（多 bag_code）→ 10301 角色基础信息
[数百~千字节后] === closed → 客户端隔一段时间重连，重跑以上序列
```

- **请求已发出、服务端已收到、服务端已返回、客户端已在处理**（1110/10102 handler 都 hit 过）。
- `host=10.0.2.2:9000`、`server_id=1`、`server_name=本地私服`、`platform=ewan`、角色 `rid=1001/srv_id=1`。
- 连接由**客户端主动断开**（服务端是 `while True` + 600s 空闲超时，短连接 ~30–60s 即 `=== closed`，故是客户端掐的）。

### 证据 3 —— 端侧状态上报：场景一直 nil

`server/logs/http.log` 每 15 tick 一条 `t=state`：

```
state  t=6315  scene=nil  role=table  recv=58
```

角色已登录（`role` 是 table），但 **`SceneModel:getInstance():getScene()` 始终 nil**。

### 证据 4 —— 屏幕实况：当前停在选服/登录页，无对话框

`shots/live_after_entergame.png`（本次实测截图）：
- 可见“本地私服（绿点在线）”“点击选区”“新”
- 主按钮“进入游戏”、“切换账号”、“公告”、“版本号 v1.0.186”
- **没有任何对话框/弹窗**。

### 证据 5 —— 服务器状态（只读）

- 本轮开始前：`server/mock_server.py`（PID 8956）**已停止**（:8080/:9000 无监听，进程消失，`server.log` 无异常栈、最后停在 09:11，判断为外部终止）。这是首轮重启后应用连 `10.0.2.2:8080` 报 `ConnectException`、且服务端日志不再增长的原因。
- 重启（同文件、同 config.json，业务逻辑未改）后：PID 14064 监听 `0.0.0.0:8080/9000`，随后的复现正常走通登录握手。
- 服务端对 `15801` **已不应答**（`EMPTY_REPLIES` 中已移除，见 mock_server.py 注释）；`build_1110_roles` 已回 `code=1(TRUE)`。

---

## 二、T0–T10 时间线（本轮实测，09:19–09:21 一次典型循环）

| 时刻 | 事件 | 证据 |
|---|---|---|
| T0 进入选服界面 | 收到服务器列表，显示“本地私服” | 截图证据4；列表接口来自 `get_servers_url`→`10.0.2.2:8080/gateway/mobile/json` |
| T1 点击/驱动进入游戏 | 客户端连游戏服 TCP | `tcp.log` `connection from 127.0.0.1:xxxx` |
| T2 客户端执行 | `OnConnect→requirehand(10001)→request1110Role(1110)` | 抓包 10001 + 1110 |
| T3 HTTP | 已在此前完成（服务器列表/热更检查） | `http.log` `/gateway/*`、`/update/*` |
| T4 TCP | ✅ 连上 `10.0.2.2:9000` | 抓包 |
| T5 host:port | `10.0.2.2:9000` | 抓包 |
| T6 请求类型 | 10001→1110→10102→10502/10301（心跳 1199 并行） | `tcp.log` |
| T7 服务端返回 | ✅ 回 1110(roles=1)、10102、10200、10201、1199 | `tcp.log` |
| T8 客户端解析 | ✅ `on1110Rolelist code_1`、`on10102Login code_0` 均 hit | DSH_PROBE |
| T9 哪一层出错 | **非异常、非空白弹窗**；`scene` 始终 nil，登录未形成场景 | `state scene=nil` |
| T10 触发提示框 | 弹出的只有 `CommonAlert_len6`（6 字正文，非空白） | DSH_PROBE `alert CommonAlert_len6` |

---

## 三、逐条回答你的 20 项要求

| # | 项 | 结果 |
|---|---|---|
| 1 | APK 版本 | **1.4.9**，`com.shiyue.dldl.ewan.qihoo`（= `jstm.apk` 的 fakelogin 构建） |
| 2 | 测试设备 | MuMu 模拟器 `127.0.0.1:16384`（22041211A / Android 12） |
| 3 | APK 启动 | ✅ 成功（PID 3629，AppActivity 前台） |
| 4 | 初始化 | ✅ 成功（`sdkBackInit 0 DSH伪登录初始化成功`；scene/* 模块全部 require） |
| 5 | 选服 | ✅ 成功（显示“本地私服”） |
| 6 | 本地私服显示 | ✅（截图证据4） |
| 7 | 点击进入游戏后 | 登录握手全通，但场景未建立、客户端反复重连；**未出现空白框** |
| 8 | 空白框触发位置 | **本轮未触发**（`message NIL`/`CommonAlert NIL` 均为 0） |
| 9 | 具体 Lua 文件 | 旧根因：`game/login/denglu_ctrl.luac`、`game/beast/beast_ctrl.luac`（复核未命中） |
| 10 | 具体函数 | `on1110Rolelist`（code=1，成功分支）；`beast_ctrl.on15801`（服务端已不应答 15801） |
| 11 | 具体协议 | `SCAccountLogin_1110`、`SCRoleLogin_10102`、`SCRoleReLogin_10103`、`SCRoleEnter_10200`、`SCMapGird_10201` |
| 12 | host | `10.0.2.2` |
| 13 | port | HTTP **8080** / 游戏服 TCP **9000** |
| 14 | 请求是否发送 | ✅（10001/1110/10102/10502/10301 均有抓包） |
| 15 | 服务端是否收到 | ✅（`tcp.log` `>> cmd=…`） |
| 16 | 服务端是否返回 | ✅（`tcp.log` `<< …`） |
| 17 | 客户端是否解析 | ✅（1110/10102 handler 均 hit） |
| 18 | 最终错误原因 | **场景未建立（`scene=nil`）+ 客户端登录循环重连**；空白框未触发 |
| 19 | 当前阻塞点 | 进入场景（`10200 RoleEnter` 已推，但场景模型未初始化）→ **场景构建链路**是下一步 |
| 20 | 最小修改方案 | 不改 APK业务逻辑；下一步先在**服务端**补齐/校准 10301 角色基础信息应答，并捕获 6 字提示正文以判断循环直接原因 |

---

## 四、结论分层：已排除 / 尚未确认 / 下一步证据

### 已排除（有数据）
1. **“空白提示框根因 1”（1110.code≠TRUE → `message('')`）在本轮不成立**：`on1110Rolelist` 恒为 `code=1`（成功分支）。
2. **“空白提示框根因 2”（对 15801 回猜的包 → `message(nil)`）在本轮不成立**：服务端已不应答 15801，且全运行期 `message NIL`=0。
3. **空白框本身**：本轮目标构建 + 当前服务上不出现（截图无对话框；全期 0 次 NIL 弹窗）。

### 尚未确认（需补证据）
- **那 6 个汉字提示的具体文本**。钩子只报长度（避免 URL 吃掉正文），故正文未落库。
  - 它每次都在 `on10102Login/on10103ReLogin`（code=0）之后出现，**极可能是客户端把 `10102` 的 `code=0` 当作失败而提示的登录错误**（如“登录游戏失败”一类 6 字文本），但**仅凭现存数据不能断定**——不能编造。
- **客户端为何在握手成功后主动断开、进入循环**。`scene=nil` 很可能是果而非因；直接因可能落在“客户端收 10102/10301 应答后判定失败 → 重连”。需断点那一刻的客户端侧调用栈。

### 下一步需要的最小证据（不批量改动）
1. **（服务端，不改业务）给 mock_server 对 `10300/10301` 按 `manual_login.md` 结构真正回包**，看是否消除重连循环——这同时能确认循环是否因“基础信息无应答”引起。
2. **（若需捕捉正文，做一次最小化日志补丁）** 在 `CommonAlert.show` 钩子里新增一条不上报 URL、而是 `print("[DSH_ALERT_TEXT] "..tostring(msg))` 的打印，重打一次 APK 后抓 logcat，据此拿到 6 字正文。**只此一处**，且备份原文件后再改。
3. 若你要的是 **baidu2 1.4.11**（`jstm_142165.apk`）的空框，需用同一套注入/钩子在其上实跑一次；本报告结论不代其生效。

---

## 五、与 “上一阶段报告” 的关系（避免误解）

上一阶段 `analysis/blank_dialog.md` 已确认 blank 空框**有两个根因并都已通过改服务端消除**：
- 根因 1：`SCAccountLogin_1110.code` 应=TRUE(=1)，服务端已改 `code=1`；
- 根因 2：对未解出编码的 `15801` 回了猜的包→`message(nil)`，服务端已将其从 `EMPTY_REPLIES` 移除。

因此**在本构建 + 本服务上，空白框本身已不会由这两个来源产生**（本轮实测复核一致：0 次 NIL）。当前真正卡住的是**“登录成、进不了场景、反复重连”**，这与“空白框”是两个不同的现象，报告如实区分。

---

## 六、交付物

- `report/jstm_enter_game_diagnosis.md`（本文件）
- `logs/jstm_enter_game.log`（本轮干净 logcat，394,475 字节）
- `logs/jstm_activity.txt`、`logs/jstm_process.txt`
- `shots/live_after_entergame.png`（本轮实测截图，显示选服/登录页、无对话框）
- 服务端只读证据：`server/logs/http.log`（DSH_PROBE 段）、`server/logs/tcp.log`（抓包段）、`server/logs/server.log`
- 静态分析沿用：`analysis/login_flow.md`、`analysis/protocol_flow.md`、`analysis/blank_dialog.md`

## 七、本轮环境备注（重要，写清真实情况）

- **服务器在我开始前已停止**；我以**同一文件、同一 config.json** 重启后才完成复现（业务逻辑零改动）。这说明该阶段实验结果依赖“本地服务处于运行态”。
- 三点 adb 端点（16384/5555/7555）实为同一台模拟器（同一 ActivityRecord / product model），统一使用 `127.0.0.1:16384`。
- 复现采用项目既定注入驱动走完 1110→10102/10103→… 链路；它驱动的正是与“手动点进入游戏”相同的网络处理函数，且按你的要求仅连 `10.0.2.2`（我控制的本地服务）。

---

**【WAITING FOR NEXT INSTRUCTION】**