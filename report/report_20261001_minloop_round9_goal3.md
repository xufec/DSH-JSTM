# 最小回环 · 第 9 轮（goal round 3/20）—— 卡点细化：`10102` **发出去了但没上线**；`loginData` 是空的

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：让客户端发出 `10102`（登录指定角色）。

---

## 〇、一句话结论

> **本轮把卡点从"客户端不发 10102"精确改判为：`10102` 已经在客户端内部被 `SendProtocal` 发出，
> 但字节没有上线；而根子在"客户端手里没有服务器地址"。**
> 证据（v38，客户端 `dsh_v38.txt`）：
> ```
> v38_send=SendProtocal m_msg_type=10102          ← ★ 10102 确实进了发送器（不是弹窗分支）
> v38_call=request10102Login(1001,1) ok=true ret/err=nil
> v38_logindata_v=open_time=0,srv_name=,ip=,port=,srv_id=    ← ★ 服务器信息**全空**
> ```
> 同期服务端 `live7` 里 **`>> 10102` 一条都没有**，而 `10001/1110/1199` 都正常到达
> ⇒ 不是"发送器坏了"，而是 **10102/10103 这类"游戏服消息"被扣住了**。

---

## 一、本轮做的静态分析（不依赖模拟器，一次命中）

新增工具 `tools/ml_dump_proto.py`：**按 proto 序号**反汇编（补 `dump_proto.py` 只能按关键字过滤的短板 ——
方法名往往不在它自己的常量池里，关键字过滤找不到本体）。

### 1.1 `request10102Login` = `denglu_ctrl.luac` proto#32（params=3 ⇒ self,rid,srv_id）

```
0-3    d = self.manager:getLoginData()
4-12   now = GameNet:getInstance():getTime() ;  now - d.open_time
13-15  if (now - open_time) >= 0 then JMP 43        ← 已开服 → 直接发
16-42  **否则** CommonAlert.showLeftApply('服务器【x】开服时间:y'...) → RET0（不发包）
43-50  ProtocalRulesMgr:getInstance():GetPrototype(10102)
51-54  proto.rid=rid ; proto.srv_id=srv_id ; proto.temp_rid=rid ; proto.temp_srv_id=srv_id
55-58  self:SendProtocal(proto)
```

**⇒ `request10102Login` 只有"开服时间"一个闸门**，没有别的隐藏条件；v37 的"返回成功却不发"不是它挡的。

### 1.2 旁证：`gamenet` 里有**消息队列**机制

proto#12 的常量池里同时出现 `'msg_list'`、`'in_async_connect'`；方法表里还有
`recordMsg`（proto#21, bc=61）/ `replay`（proto#24, bc=59）/ `game_net_id`
⇒ **有"记录—重放"的消息队列**，与"某些消息要等游戏网就绪才发"完全吻合。

---

## 二、本轮实测（v37 / v38，两轮都是已验证配方：跳 Stop → initInstance → restartNetManager）

| 版本 | 加了什么 | 客户端侧 | 服务端侧 | 判定 |
|---|---|---|---|---|
| **v37** | 连上稳定后调 `request10102Login(1001,'1')` | 入口存在、`ok=true ret=nil` | **没有 10102** | ⚠️ 未发 |
| **v38** | + 包 `CommonAlert.showLeftApply` 与 `DengluCtrl.SendProtocal` | ★ `v38_send m_msg_type=10102`；**没有 `v38_alert`**（说明**没走弹窗分支**）；`loginData` 全空 | **没有 10102** | ★ 卡点改判 |

### 2.1 v38 的发送序列（原样）

```
v38_send=SendProtocal m_msg_type=10103     ← 角色重连（也没上线）
v38_send=SendProtocal m_msg_type=1199      ← 心跳（上线了 ✅）
v38_send=SendProtocal m_msg_type=10102     ← ★ 游戏登录（没上线）
v38_call=request10102Login(1001,1) ok=true ret/err=nil
v38_send=SendProtocal m_msg_type=1199      ← 心跳（上线了 ✅）
v38_send=SendProtocal m_msg_type=10001     ← 连接首包（上线了 ✅）
```

**同一台客户端、同一个 `SendProtocal`**：`1199/10001/1110` 上线，`10102/10103` 不上线。

---

## 三、卡点根因（本轮结论，可证伪）

> `manager:getLoginData()` **是空的**（`ip/port/srv_id/srv_name` 全空）
> ⇒ 客户端**没有游戏服的地址**
> ⇒ 「游戏网」建立不起来 ⇒ `10102/10103` 这类走**游戏服**的消息被压在队列里（`msg_list` / `recordMsg` / `replay` 这一族机制）
> ⇒ 服务端永远收不到 `10102`。

**而 `loginData` 为空的上游原因**（前几轮已有证据）：服务器列表**从未被客户端真正消费**——
`DengluMgr:getServerList()` 返回 `nil`（v23 实测），而 v19 我手动喂列表时它报
`attempt to concatenate field 'zone_id' (a nil value)`（说明我喂的形状不对）。

---

## 四、完成 / 未完成

### 4.1 完成
1. 新增**按序号反汇编**工具 `tools/ml_dump_proto.py`（可复用）。
2. `request10102Login` **全量反汇编**：确认唯一闸门是"开服时间"，且它确实会 `SendProtocal(10102)`。
3. **卡点改判**（本轮最重要的产出）：不是"客户端不发"，而是"**发了但被扣住**"，
   并用"同一发送器里 1199/10001 能上线、10102/10103 不能"把范围锁死。
4. 找到**消息队列**机制的存在证据（`msg_list`/`recordMsg`/`replay`/`game_net_id`）。
5. 配方继续稳定复现（v37/v38 都连上并登录，心跳正常）。

### 4.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 服务端收到 `10102` | ❌（已定位到上游：客户端的 `loginData` 为空） |
| 2 | 服务器列表被客户端正确消费 | ❌ `getServerList()` 仍为空 |
| 3 | 进场景/任务/战斗/结算/掉落/提交/奖励 | ❌ 未开始 |
| 4 | "10102 是否真的躺在 `msg_list` 里" | **UNKNOWN**（本轮未验证，见下） |

---

## 五、下一轮直接照做（优先级）

1. **先证实/否证队列假设（最便宜）**：在探针里打印 `rawget(GameNet:getInstance(),'msg_list')`
   的长度与内容（`m_msg_type` 列表）。
   - 若含 `10102/10103` ⇒ **队列假设成立**，接着只需让它有机会被 `replay`（通常要"游戏网"就绪）。
   - 若不含 ⇒ 队列假设**否证**，转去查 `SendProtocal` 对这两条消息的差异分支。
2. **修服务器列表的消费**（治本）：按 §五 反汇编出来的**真实读法/键表**核对应答，
   并用 `CommonAlert.show` + `managerServerListByJsonObj` 两个钩子定位"没被消费"的确切位置。
   这与 `restartNetManager` 那次一样 —— **静态反汇编一次命中**。
3. 拿到 10102 上线后，本服会推 `10200/10201` 进场景，再往 `10300/12400/20002/12403/10502` 推进。

---

## 五、★ 本轮追加：服务器列表消费方的**权威反汇编**（治本线索）

`tools/ml_dump_proto.py` 反汇编 `denglu_mgr.luac` 的 **proto#8 `managerServerListByJsonObj`**（bc=237）：

```
0-5    self.server_list = {}
8-14   local x = arg1 ; if x.data == nil then x = x.msg end      ← 与 server_list_protocol.md 一致
15-16  local sl = x['server_list']
18-22  if next(sl) then 跳 37（正常解析）  ← 非空
23-36  **空列表分支**：CommonAlert.show('当前请求到服务器列表信息为空','重新请求', retry, nil,{no_clear=true}) → RET0
37+    server_list = x['server_list'] ; default_zone = x['default_zone'] ; 逐条归一化
```

它逐条读取的键（常量池原样，**与我的网关应答逐字段对得上**）：
`srv_id / platform / zone_id / srv_name / name / ip / port / erl_port / host / platform_flag /
can_create_role / maintain(→isClose) / first_zone(→isTry) / recommed(→isRecomed) / isnew(→isNew) /
open_time / begin_time / main_platform / main_zone_id / main_srv_id`，
之后还会写 `loginData / getServer / setCurSrv / serverlist_completed / REQUEST_SERVERLIST_SUCCESS`。

### 5.1 因此上游问题被锁定到"**应答有没有被消费**"

| 观测（零成本，直接查日志） | 结果 |
|---|---|
| 客户端 POST 的**请求体** | **空**（服务端日志里 `HTTP POST /gateway/mobile/json` 没有 `body=`） |
| 我的应答形状 | 与 proto#8 期望**逐字段一致**（本地复现过） |
| 客户端行为 | 仍**每 ~50–60 秒重发一次**（与文档里"列表为空 → 重新请求"的重试环**特征一致**） |
| `getServerList()` / `getLoginData()` | 仍为空 |

⇒ **下一轮第一件事**（都是挂钩子，不用猜）：
1. 包住 `CommonAlert.show` ⇒ 若出现 `'当前请求到服务器列表信息为空'`，就**确证**客户端走了空列表分支；
2. 包住 `DengluMgr.managerServerListByJsonObj` ⇒ 看它**到底有没有被调用**、传入的 `x` 是什么：
   - **没被调用** ⇒ 问题在**客户端 HTTP 回调**（应答没进 Lua），转去查它的 HTTP 层；
   - **被调用但结果为空** ⇒ 问题在**归一化**，按上面那份键表逐字段比对。

---

## 六、本轮产物

| 文件 | 说明 |
|---|---|
| `tools/ml_dump_proto.py` | ★ 新增：按 proto 序号反汇编 |
| `server/_minloop_block.lua` | 现为 **v38**：配方 + `CommonAlert.showLeftApply`/`SendProtocal` 观察钩子 + `loginData` 打印 |
| 设备内 `files/dsh_v37.txt` / `dsh_v38.txt` | 客户端原始证据（含 `m_msg_type` 序列） |
| `logs/minloop/live7_stdout.log` | 服务端侧（10001/1110/1199 到达；10102 缺席） |
| `analysis/denglu_ctrl.luac` | 从 APK 抽出的待分析字节码 |
