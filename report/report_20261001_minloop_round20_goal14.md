# 最小回环 · 第 20 轮（goal round 14/20）—— 否证"编码失败"；找到发送对象 **`UserMsgAdapter`**；`Send` 确实被调用

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：分辨 `10102` 卡在 `WriteHeader` 还是 `Encode`。

---

## 〇、一句话结论

> 本轮把上一轮的两条假设做了运行期判定，**结果是否证 + 缩小**：
>
> | 假设 | 判定 | 证据 |
> |---|---|---|
> | B：`proto:Encode(socket)` 对 10102 返假 | ❌ **否证** | `v43_enc=m_msg_type=10102 Encode=true` |
> | A：`socket:WriteHeader(10102,0)` 返假 | ⚠️ **未取到**（我的钩子没被这条路径命中，见下） | 无 `v43_wh` 输出 |
>
> 并且**意外收获**：发送侧那个"socket"对象就是全局 **`UserMsgAdapter`**（`v43_socket=FOUND UserMsgAdapter(self)`），
> 而且 **`Send` 确实被频繁调用**（`v43_send_raw=Send 被调用` ×14）。
> ⇒ 发送链**走完了全过程**（`Encode` 成功、`Send` 被调），**但服务端依旧收不到 `10102`**
> ⇒ 字节的丢失点在 **`UserMsgAdapter:Send` 内部或其后**（不是 WriteHeader/Encode）。

---

## 一、本轮证据（客户端 `files/dsh_v43.txt`）

```
v43_socket=FOUND UserMsgAdapter(self)      ← ★ 发送对象 = 全局 UserMsgAdapter
v43_hook=WriteHeader
v43_send_raw=Send 被调用   ×14             ← ★ Send 一直在被调用
v43_hook=proto.Encode
v43_enc=m_msg_type=10102 Encode=true       ← ★ 10102 的编码成功
```
服务端侧：`>> 10102` 依旧 **0 次**（`live11` 里搜不到）。

---

## 二、由本轮结果得到的**新**判断

1. **排除"编码/包头被拒"这条线**：`Encode(10102)` 返回 **true**；
2. **发送链被完整走到**（`Encode` → `Send`），因此"函数提前 return"这类解释**也被削弱**；
3. ⇒ 剩下的可能集中在 **`UserMsgAdapter:Send` 的行为**：
   - 它可能是个**适配器**（名字即暗示）：把消息**投递到某个队列/通道**，由底层在"就绪"时才真正写出；
     这与本项目在 `gamenet.luac` 里发现的 `recordMsg` / `replay` / `msg_list` / `game_net_id`
     一族"记录—重放"机制**高度吻合**（而 `msg_list` 我们实测是空的 ⇒ 也许用的是**另一个**队列）；
   - 也可能它按 `m_msg_type` **分流**（登录类 vs 游戏类），而游戏类的通道未就绪 ⇒ 丢弃。
4. ⚠️ **UNKNOWN**：`WriteHeader` 的返回值本轮**没能观测到**（我的包装只对 10102/10001/1110/10103 打印，
   但一条都没出现）⇒ 说明**`SendProtocal` 里那次 `WriteHeader` 并不是调在这个对象的 `WriteHeader` 上**
   （可能调在另一个内部对象上）⇒ 该点需重做（下一轮）。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★ **否证假设 B**（`Encode(10102)=true`）——省掉一整条排查线。
2. ★ **找到发送对象**：全局 **`UserMsgAdapter`**（含 `WriteBegin`/`WriteHeader`/`Send`）。
3. ★ **确认发送链被完整执行**（`Encode` 成功 → `Send` 被调用 ×14）。
4. 新增可复用探针能力：**运行期枚举/定位"像 socket 的对象"**（`_ml43_add.lua`）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `WriteHeader` 的实际返回值（本轮钩子未被命中） | **UNKNOWN** |
| 2 | **`Send` 与消息号的对应关系**（Send 是否真为 10102 而调） | **UNKNOWN**（本轮只记了"被调用"） |
| 3 | `10102/10103` 上线 | ❌ |
| 4 | `scene`、`12402`、`20002`、完整奖励链 | ❌ |
| 5 | 两实例差异（16384 曾进场景 / 7555 未进） | **UNKNOWN** |

---

## 四、下一轮直接照做（已缩到很窄）

1. ★ **给 `UserMsgAdapter:Send` 记录"正在发哪条消息"**：
   - 包装方式：`WriteHeader(m_msg_type,0)` 时把 `m_msg_type` 记到 `UserMsgAdapter` 的临时字段上，
     然后在 `Send` 里读出来一起打印 —— 这样就能回答"**Send 到底有没有为 10102 调过**"。
   - 若 **Send 为 10102 调过** ⇒ 字节**确实交给适配器了** ⇒ 去查它内部的**队列/通道**（对照 `recordMsg/replay`）；
   - 若 **Send 从未为 10102 调过** ⇒ 说明 `Encode=true` 之后仍有分支跳过了 `Send`（回到 proto#3 的
     "WriteHeader 失败跳转"分支，需要重新把那个 WriteHeader 找出来）。
2. **重新定位 `WriteHeader` 的真实宿主**：在 `SendProtocal` 执行期间遍历可疑对象的 `WriteHeader`
   （不再假设是 `UserMsgAdapter`）。
3. 弄清 `Send` 的行为后，`10102` 上线 → 立刻验证第 11 轮的**幂等提交**（`<< 12403 提交成功` + 奖励落库）。
4. 补 `dump_proto.py` 的 `GGET` 全局名解析（第 19 轮记录的技术缺口，仍在）。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_ml43_add.lua` | ★ 新增：运行期定位"像 socket 的对象" + 包 `WriteHeader`/`Send`/`proto.Encode` |
| `server/dsh_minloop_probe.lua` | = 原探针 + v39/v40/v41/v42/v43（过 `lua-check`） |
| 设备内（7555，需 root）`files/dsh_v43.txt` | ★ 本轮核心证据（`UserMsgAdapter`、`Encode=true`、`Send 被调用`） |
| `logs/minloop/live11_stdout.log` | 服务端侧：`10102` 仍为 0 |
