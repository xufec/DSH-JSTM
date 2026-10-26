# 最小回环 · 第 18 轮（goal round 12/20）—— 长窗口观察：稳定"连上+登录+心跳"，但 **10102/10103 到不了线上**

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：给会话更长窗口，看回环是否自行推进。

---

## 〇、一句话结论

> 长窗口（>5 分钟）下客户端处于**稳定状态**：连接保持、账号登录成功、心跳 52 次，
> 但**始终停在"选角色"之前**。逐条证据把这一点钉死：
>
> | 命令 | 是否进入客户端 `SendProtocal` | 发送器返回 | 服务端是否收到 |
> |---|---|---|---|
> | `10001` | ✅ | true | ✅ |
> | `1110` | ✅ | true/false 都有 | ✅ |
> | `1199` | ✅（52 次） | true | ✅（52 次） |
> | **`10102`** | ✅（1 次，`m_type=cs … rid=1001 srv_id=1`） | **true** | ❌ **0 次** |
> | **`10103`** | ✅（3 次，同上属性） | **true** | ❌ **0 次** |
>
> ⇒ **同一条连接、同一个发送器、同样的属性：`10001/1110/1199` 上线，`10102/10103` 不上线。**
> 并且第 10 轮已记录：此时客户端 `manager:getLoginData()` 是**空的**（`ip/port/srv_id/srv_name` 全空）。

---

## 一、本轮证据（全部可复查）

### 1.1 服务端侧（`logs/minloop/live11_stdout.log`）

```
连接: 11 次 ｜ 客户端命令种类: 3
命令: {1199: 52, 10001: 1, 1110: 1}
```
（同一日志里 `10102` / `10103` 的 `>>` 计数为 **0**。）

### 1.2 客户端侧

```
dsh_v39.txt:  v39_restarted=ok
              v39_call10102=ok=true            ← 我的块调了 request10102Login，返回成功
              v39_consume_ret=ok=true err=nil  ← 服务器列表消费也成功（×3）
dsh_v42.txt:  m_msg_type=1199 ×8
              m_msg_type=1110 ×2
              m_msg_type=10001 ×2
              m_msg_type=10103 ×1              ← ★ 进了发送器
              m_msg_type=10102 ×1              ← ★ 进了发送器
dsh_v42.txt:  v42_send=ret_true/nil conn_true netid_1 gid_1 | m_type=cs,m_msg_type=10102,srv_id=1,rid=1001,tables=3
dsh_v41.txt:  v41_watch=scene=nil conn=true restarts=0 n=120/160/200
```

**读法**：
1. 连接**是好的**（`conn=true`，服务端 11 次连接、1199 心跳来回 52 次）；
2. 列表消费**是好的**（`v39_consume_ret=ok=true`）；
3. `10102/10103` **确实进了发送器**、属性与其他命令**同型**、**返回 true**；
4. 但**服务端收不到** ⇒ 卡点在**发送器内部对这两条消息的处理**，不在连接、不在列表。

### 1.3 与之相关的另一条旧证据（第 10 轮）

```
dsh_v38.txt: v38_logindata_v=open_time=0,srv_name=,ip=,port=,srv_id=     ← ★ loginData 全空
```

⇒ **最强假设**：客户端发送 `10102/10103` 时需要"当前选中的服务器"（`loginData`），
而 `loginData` 为空 ⇒ 帧被静默丢弃（但函数返回 true）。
**这条假设本轮未验证**（见下）。

---

## 二、完成 / 未完成

### 2.1 完成
1. **长窗口稳定态确认**：`conn=true` 保持、`1199` 双向 52 次、`scene=nil`、`restarts=0`
   ⇒ 连接纪律（只救一次、连上别碰）**在长窗口下也稳定**。
2. ★ **把卡点收窄到"发送器内部"**：`10102/10103` 进发送器、同型、返回 true，却不上线
   （`10001/1110/1199` 同条件上线）⇒ **排除**：连接问题、列表消费问题、命令类型差异、队列（`msg_list=0`）。
3. 列出两条仍可能的解释（下轮验）。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `10102/10103` 上线 | ❌ |
| 2 | **`loginData` 为空是否为直接原因** | **UNKNOWN**（本轮未做对照实验） |
| 3 | `scene` 非 nil（本轮 `scene_nil`） | ❌ |
| 4 | `12402`/`20002`/战斗→结算→掉落→提交→奖励 | ❌ |
| 5 | 两实例差异（16384 曾进场景 / 7555 未进） | **UNKNOWN** |

---

## 三、下一轮直接照做（优先级）

1. ★ **做"loginData 对照实验"**（一次挂钩子即可定论）：
   - 在发送 `10102` 之前，把 `manager:getLoginData()` 的字段打印出来；
   - 若确为空 ⇒ **用客户端自己的入口把服务器"选上"**（`DengluMgr:setCurSrv(...)`，
     该方法名已从 proto#8 常量池确证），再发 `10102`；
   - 判据：服务端出现 `>> 10102`（而后应连锁出现 `<< 10200/10201`、`>> 10300`）。
2. 若 `loginData` 不空 ⇒ 转去**反汇编 `DengluCtrl.SendProtocal` 的实现**（在基类里），
   看它对 `m_msg_type` 是否有**白名单/前置状态**（这是目前唯一还没静态看过的发送侧代码）。
3. 若 `10102` 上线 ⇒ 立刻验证第 11 轮做的**幂等提交**（`<< 12403 提交成功` + 真实奖励落库）。
4. 仍建议顺手做"两实例差异"对比（存档/资源），这是最后一个未解变量。

---

## 五、★ 本轮追加（静态）：`SendProtocal` 的完整实现已反汇编出来

`assets/src/base/base_controller.luac` **proto#3 `SendProtocal`**（params=2 ⇒ self, proto，bc=43）：

```
0-3    GameNet:getInstance()
5-6    IsLoginServerConnect()
7-9    if not <连接> then RET0 end                  ← 未连接则直接返回（无字节）
10-15  Debug('发送协议:', proto.m_msg_type)          ← 客户端日志里"发送协议:"出处
16-18  socket:WriteBegin()
19-23  socket:WriteHeader(proto.m_msg_type, 0)
24-25  if not <WriteHeader> then <跳转>              ← ★ 静默失败点 ①
26-29  proto:Encode(socket)
30-31  if not <Encode> then <跳转>                   ← ★ 静默失败点 ②（很可能就是这里）
32-37  socket:Send(GameNet:getInstance())
```
常量池：`game_net_id, Send, Encode, WriteHeader, WriteBegin, UserMsgAdapter, '发送协议:', m_msg_type, socket, Debug, IsLoginServerConnect, GameNet`

**读法**：
1. 发送链是 `socket:WriteBegin → WriteHeader → proto:Encode(socket) → socket:Send(...)`；
2. 其中 **`WriteHeader` 与 `Encode` 都有"失败就跳转"的分支** —— 跳转后**不执行 `Send`**，
   但函数**仍可能返回 true** ⇒ **完全解释**"返回 true 却无字节"；
3. 因为 `10001/1110/1199` 在**同一个 socket、同一个函数**里能成功，
   ⇒ 差异只能出在 **`10102/10103` 这两个 proto 自身的 `WriteHeader`/`Encode` 结果**上。

### 5.1 下一轮要打的两个点（很窄、很便宜）

在探针里包住 `socket`（`GGET D=7` 那个全局 —— 需先确认它的名字，可能是 `NetSocket`/`Socket`）的
`WriteHeader` 与 `Encode`，**按 `m_msg_type` 分别计数**：
- 若 `10102` 的 `WriteHeader` 返回假 ⇒ 命令号/包头被拒（例如该号不在客户端注册表里）；
- 若 `Encode` 返回假 ⇒ **客户端 CS 规格与我的理解有差异**（此时应回到 `show_cmd.py` 与真机抓包的对照）。

> 这一步做完，"10102 为何不上线"就能给出**闭口结论**（而不是继续假设）。

---

## 六、本轮产物

| 文件 | 说明 |
|---|---|
| `logs/minloop/live11_stdout.log` | 长窗口证据：连接 11 / `1199`×52 / 无 `10102` |
| 设备内 `files/dsh_v41.txt`（`v41_watch` 稳定）、`dsh_v42.txt`（发送器记录）、`dsh_v39.txt`（消费/调用） | 客户端侧原始证据 |
| `report/report_20261001_minloop_round17_goal11.md` | 上一轮：连接纪律 + 幂等提交 |
