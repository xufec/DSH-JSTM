# 最小回环 · 第 19 轮（goal round 13/20）—— `SendProtocal` 发送链与**两处静默跳过**已定位

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：包住 socket 的 `WriteHeader`/`Encode`，判定 10102 卡在哪一步。

---

## 〇、一句话结论

> 本轮把 `SendProtocal`（`assets/src/base/base_controller.luac` **proto#3**）完整解出来，
> 得到**一条能解释"返回 true 却无字节"的机制**：
> ```
> GameNet:getInstance() → IsLoginServerConnect()
>   ├─ 未连接 ⇒ RET0（无字节）
>   └─ 已连接 ⇒ Debug('发送协议:', m_msg_type)
>                socket:WriteBegin()
>                socket:WriteHeader(m_msg_type, 0)
>                  └─ ★ 若返回假 ⇒ **跳转、不执行 Send**（但函数仍可能返回 true）
>                proto:Encode(socket)
>                  └─ ★ 若返回假 ⇒ **跳转、不执行 Send**（同上）
>                socket:Send(GameNet:getInstance())
> ```
> 因为 `10001/1110/1199` 在**同一 socket、同一函数**里都能成功，
> ⇒ `10102/10103` 的差异**只能出在这两个 proto 自身的 `WriteHeader` 或 `Encode` 结果**上。
> 本轮**尚未**取到运行期那一步的返回值（未做该次探测），故结论只到"机制已定位"。

---

## 一、本轮完成

| # | 事项 | 证据 |
|---|---|---|
| 1 | 抽出并反汇编发送侧核心 | `assets/src/base/base_controller.luac`，`SendProtocal = proto#3`（bc=43, params=2） |
| 2 | **拿到完整发送链与两处静默跳过点** | 见上（`WriteHeader` / `Encode` 各自"失败即跳、不 Send"） |
| 3 | 取得 proto#3 的常量池（名字全表） | `game_net_id, Send, Encode, WriteHeader, WriteBegin, UserMsgAdapter, '发送协议:', m_msg_type, socket, Debug, IsLoginServerConnect, getInstance, GameNet` |
| 4 | 记录一个**未解的技术点**（诚实） | `dump_proto.py`/`ml_dump_proto.py` 对 `GGET` 的 `D=` **没有解析出全局名**（`decode` 的 `extra` 为空）⇒ **socket 管理器那个全局叫什么，本轮 UNKNOWN** |

### 1.1 由常量池得到的两条可检验假设

- **假设 A（包头被拒）**：`socket:WriteHeader(m_msg_type, 0)` 对 `10102/10103` 返回假
  （例如这两个命令号不在客户端的某个"注册表/白名单"里）。
- **假设 B（编码失败）**：`proto:Encode(socket)` 对这两个 proto 返回假
  ⇒ 说明**客户端对这两条 CS 的字段规格与我 `show_cmd.py` 读到的不同**
  （本项目早有先例：`CS_16603`/`16500` 的"4 字节缓冲区残留"）。

两条都**只需一次运行期探测**即可分辨（见下）。

---

## 二、未完成

| # | 项 | 状态 |
|---|---|---|
| 1 | **socket 管理器全局名的运行期确定** | UNKNOWN（静态没解出来；下一轮用探针枚举 `_G` 中带 `.socket` 的对象） |
| 2 | `WriteHeader`/`Encode` 对 10102 的返回值 | ❌ 未取到（本轮未做该次探测） |
| 3 | `10102/10103` 上线 | ❌ |
| 4 | `scene` 非 nil、`12402`/`20002`、完整奖励链 | ❌ |
| 5 | 两实例差异（16384 曾进场景 / 7555 未进） | UNKNOWN |

---

## 三、下一轮直接照做（很窄，一次运行可分辨）

1. **运行期找 socket 管理器**：遍历 `_G`，找出所有满足
   "`v.socket` 是 table 且其上有 `WriteBegin`/`WriteHeader`/`Send`"的对象，打印它们的名字。
   （再顺手试 `NetWork`/`SocketMgr`/`GameSocket`/`NetManager` 等常见名。）
2. **按 `m_msg_type` 分别观测**：包住该 socket 的 `WriteHeader` 与 `Encode`：
   - `10102` 的 **`WriteHeader` 返假** ⇒ 假设 A 成立 ⇒ 去查客户端"命令号注册表"；
   - `10102` 的 **`Encode` 返假** ⇒ 假设 B 成立 ⇒ 用真机抓包的 `10102` 原始 CS 字节
     与 `protocol/fields.json` 的 CS 规格**逐字节对照**（本项目最擅长的那套）。
3. 弄清之后，`10102` 上线 → 接着验证第 11 轮的**幂等提交**（`<< 12403 提交成功` + 奖励落库）。
4. 顺带：把 `dump_proto.py` 的 `GGET` 全局名解析补上（现在解不出，影响后续所有静态定位）。

---

## 四、本轮产物

| 文件 | 说明 |
|---|---|
| `analysis/base_controller.luac` | 从 APK 抽出的发送侧字节码（`SendProtocal` 所在） |
| `tools/ml_dump_proto.py` | 按 proto 序号反汇编（本轮用它解出 proto#3） |
| 本报告 §一 的发送链 | 描述"返回 true 却无字节"的机制 |
| `logs/minloop/live11_stdout.log` | 上一轮长窗口证据（连接/心跳稳定、无 10102） |
