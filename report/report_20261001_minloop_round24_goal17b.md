# 最小回环 · 第 24 轮（goal round 17/20）★★ 结论闭口：`10102` 的两处静默跳过**都没走**，丢失点在 `UserMsgAdapter:Send`

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：给包装做自证，并读出 `WriteHeader` 的真实返回值。

---

## 〇、一句话结论

> **自证版包装一次成功**（安装有据、逐次有归属），并**直接回答了上一轮留下的唯一问题**：
>
> ```
> v46_installed=UserMsgAdapter@table: 0xc5256510 WriteHeader_ok=true Send_ok=true
> v46_wh  =arg_mt=0 cur_mt=10102 WriteHeader=true     ← ★ WriteHeader 返 **true**
> v46_send=cur_mt=10102 nargs=0                       ← ★ **Send 确实为 10102 被调用了**
> v46_sp  =SendProtocal m_msg_type=10102 ret=true     ← 整个 SendProtocal 返回 true
> ```
> 而服务端同窗口计数只有 `{10001: 28, 1110: 4, 1199: 303}` —— **没有 `10102/10103`**。
> ⇒ **`WriteHeader` 与 `Encode` 两处"静默跳过 Send"的分支都没有走**；
> **`Send` 被正常调用**，帧却没上线 ⇒ **丢失点确定在 `UserMsgAdapter:Send` 内部或其下游**。

---

## 一、本轮方法与结果

### 1.1 方法（上一轮的教训已修正）
- **安装自证**：装上即落盘 `v46_installed=UserMsgAdapter@table:0xc5256510 …ok=true/true`（此前两轮的包装"一条都没打印"，无法自证）；
- **对象身份比对**：每 30 拍比对 `_G.UserMsgAdapter`，变了就重装；
- **不做命令号过滤**（避免过滤逻辑自身出错），只限量；
- **守卫修正**：成功之后才置位（`_G.__dsh_ml46_tag`），失败下拍重试。
⇒ 本轮**包装确实生效**（`v46_watch=n=180 wh_logged=24 send_logged=24 ua=table: 0xc5256510`，对象身份稳定）。

### 1.2 关键数据（客户端 `files/dsh_v46.txt`）

| 命令 | `WriteHeader` | `Send` 是否被调 | `SendProtocal` 返回 | 服务端是否收到 |
|---|---|---|---|---|
| `10001` | true | ✅（`cur_mt=10001`） | true | ✅（28 次累计） |
| `1110` | true | ✅ | **false**（注意：仍上线） | ✅（4 次） |
| `10103` | true | ✅（`cur_mt=10103`） | true | ❌ |
| **`10102`** | **true** | ✅（`cur_mt=10102`） | true | ❌ |
| `1199` | —（限量已满） | — | true | ✅（303 次） |

---

## 二、由数据得到的判定

1. ★ **否证"静默跳过"分支是原因**：`10102` 的 `WriteHeader` 为 **true**，
   且第 20 轮已测 `Encode(10102)=true` ⇒ **proto#3 里那两处 `goto ret_true` 都没走**。
2. ★ **`Send` 确实被调用**（且归属正确 `cur_mt=10102`）⇒ 帧**已经交给 `UserMsgAdapter`**。
3. ★ ⇒ **丢失点 = `UserMsgAdapter:Send`**（内部队列/通道）**或其下游**。
4. ⚠️ 两处**参数映射的疑点**（新发现，下一轮要解）：
   - `v46_send … nargs=0`：按反汇编 `Send(GameNet:getInstance().game_net_id)` 应带 **1 个**实参；
     实测却是 **0 个** ⇒ **`game_net_id` 很可能为 nil**（或该调用点与反汇编的不是同一处）；
   - `v46_wh … arg_mt=0`：反汇编推的是 `proto.m_msg_type`，实测第一实参却是 **0**。
   ⇒ **若 `game_net_id` 为 nil，`Send` 无法选择通道 ⇒ 帧被丢弃**，这与"连接在 net id=1、
     而发送时拿不到可用 net id"高度吻合（第 10 轮曾观测 `netid` 在 1↔2 之间跳变）。
5. ⚠️ `SendProtocal` 对 `1110` 返回 **false** 却仍上线 ⇒ **该返回值不能当作"是否发出"的判据**（记录以免误导）。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★ **包装自证方法论落地**（安装留据 + 身份比对 + 无过滤 + 守卫修正）——补上了第 20/21 轮的缺口。
2. ★★ **闭口一个关键问题**：`10102` 的 `WriteHeader=true`、`Send` 被调用、`SendProtocal=true`
   ⇒ 两处静默跳过**都不是**原因 ⇒ **丢失点在 `UserMsgAdapter:Send` 及下游**。
3. ★ 新发现两处**参数映射疑点**（`nargs=0` / `arg_mt=0`），并给出最可能解释（`game_net_id` 为 nil）。
4. 记录一条**判据纠偏**：`SendProtocal` 的返回值**不代表是否发出**（1110 返 false 却上线）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `UserMsgAdapter:Send` 内部到底做了什么（写 socket？入队？） | **UNKNOWN** |
| 2 | `game_net_id` 在发送时的取值 | **UNKNOWN**（`nargs=0` 强烈暗示为 nil） |
| 3 | `10102/10103` 上线、`scene`、`12402`、`20002`、奖励链 | ❌ |
| 4 | 两实例差异 | **UNKNOWN** |

---

## 四、下一轮直接照做（最后两三步就能收口）

1. ★ **查 `game_net_id` 在发送时的值**：在 `SendProtocal` 包装里同时记录
   `GameNet:getInstance().game_net_id`（`rawget`）。
   - 若为 **nil/0** ⇒ **根因锁定**：适配器拿不到可用 net id ⇒ 帧被丢。
     修法方向：让客户端在**它自己的 OnConnect 之后**再发（即不要用我们强制的连接），
     或等 `game_net_id` 变为有效值后再驱动发送。
2. ★ **看 `Send` 内部**：包 `UserMsgAdapter` 上它真正写出的地方（若有 `socket`/`write` 字段），
   或对 `Send` 前后的 `_G`/适配器内部状态做快照（例如它是否把数据放进了某个 list）。
3. 一旦 `10102` 上线 ⇒ 立刻验证第 11 轮的**幂等提交**（`<< 12403 提交成功` + 奖励落库）。
4. 纪律保留：**包装必须自证**（本轮已模板化），**返回值不等于发出**（本轮已记录）。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_ml46_add.lua` | ★ 自证版包装（安装留据 + 身份比对 + 无过滤 + 守卫修正） |
| 设备内（7555，需 root）`files/dsh_v46.txt` | ★ 本轮核心证据（`10102` 的 `WriteHeader=true` + `Send` 被调 + `ret=true`） |
| `logs/minloop/live11_stdout.log` | 同期服务端计数（无 `10102/10103`）⇒ 与客户端侧形成对照 |
| `report/report_20261001_minloop_round23_goal17.md` | 上一轮：`SendProtocal` 全链反汇编（两处静默跳过） |
