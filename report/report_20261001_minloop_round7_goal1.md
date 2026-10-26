# 最小回环 · 第 7 轮（goal round 1/20）—— 复现失败三次；假设被否证；新证据：客户端**自己**在早期就尝试过建连

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标（上一轮遗留的**第一优先**）：
> 把 v27 那一次"真机发出真实帧"的**配方复现出来**。

---

## 〇、一句话结论

> **本轮三次独立尝试（v31 / v32 / v33 / v34）都没能复现 v27 的帧交换，并两次否证自己的假设。**
> 其中我原先提出的"`DeleteMe` 是罪魁"这个假设，**被 v31 直接否证**（只跳 `Stop`、保留 `DeleteMe`
> 依然 `conn=false`、服务端 0 连接 0 帧）。
> v33 的新证据（本次最有价值）：**客户端自己在早期就调用过**
> `SetLoginServerInfo(10.0.2.2, nil)` + `AsyncConnectLoginServer(10, nil)`，
> 而且 `beginGame` 也确实被调用过；但 `conn` 一路为 `false`，
> 且 `net_manager` **始终是 userdata（没被 DeleteMe 销毁）** ——
> 说明"客户端要连、但连不上"，问题在**建连本身**，不在"它没尝试"。

---

## 一、本轮三次实验（全部走新的 `lua-check` 真闸门，未再装坏包）

| 版本 | 干预 | 客户端侧 | 服务端侧 | 判定 |
|---|---|---|---|---|
| **v31** | **只跳 `Stop`**（保留 `DeleteMe`），不替它做事 | `initInstance=ok=true`；`conn=false netid=1` 全程 | 0 连接 / 0 帧 | ❌ 否证"DeleteMe 是罪魁" |
| **v32** | 只跳 `Stop` + **每帧驱动建连** + 客户端自己的握手入口 | `initInstance=ok=true`；`v32_try` 涨到 61，`v32_connected` **永不出现** | 0 连接 / 0 帧 | ❌ 保留 DeleteMe 时我方建连也失败（旧 net 对象已被销毁） |
| **v33** | 只跳 `Stop`，**只挂观察钩子**（包装 `SetLoginServerInfo/ConnectLoginServer/AsyncConnectLoginServer`、`openView`、`beginGame`、`video_player`） | ★ 见下 | 0 连接 / 0 帧 | ⚠️ 未复现，但拿到关键证据 |

### 1.1 v33 的关键证据（客户端 `files/dsh_v33.txt` 原样）

```
v33_wrap=Stop -> noop（DeleteMe 保留）
v33_hooks=installed
v33_call=SetLoginServerInfo(10.0.2.2,nil)      ← ★ 客户端自己设登录服
v33_call=AsyncConnectLoginServer(10,nil)       ← ★ 客户端自己发起异步建连
v33_stop_skipped=called                        ← 随后 initInstance 里 Stop 被跳过
v33_call=beginGame                             ← 游戏的 beginGame 确实被调到
v33_initInstance=ok=true ret/err=195
v33_watch=n=12 conn=false netid=1 nm=userdata   ← conn 一直 false；net_manager 仍是 userdata
...（n=24/36/…/108 全部 conn=false）
```

**读法**：
1. 客户端**不是"没去连"**——它在很早（t≈25，探针原有驱动那一步）就已经调了 `SetLoginServerInfo` + `AsyncConnectLoginServer`；
2. 但 `IsLoginServerConnect()` 全程 `false` ⇒ **连不上**；
3. `net_manager` 一直是 `userdata` ⇒ 这次 **`DeleteMe` 并没有跑**（与 v27 那次的差异点又多了一处，但方向仍未定）；
4. `beginGame` 被调用 ⇒ 客户端确实在往"开局"方向走。

---

## 二、已否证 / 已被推翻（诚实清单，保留在案）

| 曾经的假设 | 现状 | 依据 |
|---|---|---|
| "客户端不发帧 ⇒ 客户端根本没尝试建连" | ❌ **否证** | v33：它调了 `SetLoginServerInfo` + `AsyncConnectLoginServer` |
| "`DeleteMe` 把 net 对象销毁导致后续全失败" | ❌ **否证** | v31：保留 `DeleteMe`（只跳 `Stop`）依然失败 |
| "强制建连 + 客户端握手入口 ⇒ 一定有帧" | ❌ **否证** | v29/v32 均 0 帧 |
| "`Stop` 死等是唯一根因，绕过即通" | ⚠️ **部分成立** | 绕过能让 `initInstance` 返回（四轮 `ok=true`），但**不足以**产生帧 |
| v27 那次帧交换 | ✅ **事实仍成立**（`round6_exchange.txt`） | 但**三次未能复现** ⇒ 必有一个未定位的**外部状态**参与 |

---

## 三、本轮完成

1. **三次独立实验 + 一次假设否证**（v31/v32/v33），全部通过 `lua-check` 真闸门，未再产生坏包。
2. **拿到"客户端自己在早期尝试建连"这条新证据** ⇒ 把问题从"它不尝试"**准确定位到"尝试了但连不上"**。
3. 确认了 `net_manager` 在 `Stop` 被跳过的情形下**不会被销毁**（`nm=userdata`）。
4. 服务端侧继续为 0 字节，但**服务端本身已被多路验证无缺陷**（44/44 自检、真机帧回放 0 规格不符、控制客户端可发帧被正常记录）。

---

## 四、下一轮直接照做（优先级从高到低，已按 v34 结果修正）

1. **搞清 `ConnectLoginServer` 的真实签名**（现在这是钥匙）：从 `gamenet.luac` 反汇编出它的
   参数表（是否要传端口/超时），并**对照 v22/v24 那两次"同步调用确实连上"**的事实，
   确定该用同步还是异步、实参该怎么给。
2. 定下来之后：**只补这一步**（不接管客户端流程），然后立刻看服务端有没有 `>> ` 帧。
3. 建连稳定后，再用**已验证的 UI dump + 长按**驱动客户端自己的 `10102`（角色登录）→ 进场景。
4. 维护纪律：任何"0 事件/0 字节"结论都要带同窗口自证；**每轮都要先怀疑自己的仪器**
   （本轮"端口 nil"就是我自己包装写错导致的假线索，已是本会话第 3 次）。

---

## 五、★ 线索复核结果：**"端口为 nil"是我自己的日志 bug**（自我更正）

v33 里那条 `SetLoginServerInfo(10.0.2.2,nil)` 让我以为"游戏自己没带端口"。
v34 把参数个数与 traceback 一并打印后，**当场否证**：

```
v34_setlogin=nargs=2 a1=10.0.2.2 a2=9000 tb= config.luac:1590 ...
v34_async=nargs=1 已确保 10.0.2.2:9000
```

| 事实 | 说明 |
|---|---|
| 端口**确实是 9000**（`nargs=2`） | 调用点 `config.luac:1590` = **探针自己**那段（`dsh_fake_login.lua:1547`），本来传的就是 9000 |
| v33 为什么打印 `nil` | 我写的是 `local a1, a2 = ..., nil` —— **这个 `, nil` 把第二个 vararg 丢掉了**，是我自己的包装 bug（本会话第 3 次"仪器本身出错"） |
| `AsyncConnectLoginServer(10)` | 只带超时，符合文档签名 |

⇒ **"端口为 nil"这条线索作废**，不作数。

### 5.1 但 v34 换来一条更实在的事实（本轮真正的收获）

既然参数都对、`Stop` 也跳过了、`initInstance` 也返回了（`ok=true`），**`conn` 依旧全程 `false`**：

| 实参都对、流程也放行了 | 结果 |
|---|---|
| `SetLoginServerInfo('10.0.2.2', 9000)` ✅ | `conn=false` 全程 |
| `AsyncConnectLoginServer(10)` ✅ | 服务端 **0 连接 / 0 帧** |
| `v34_initInstance=ok=true` ✅ | 抓包 `:9000` 仍为 **0** 数据包 |

### 5.2 把历轮"能连上 vs 连不上"按调用方式对齐（这是下一轮的钥匙）

| 情形 | 调用了什么 | 是否连上 |
|---|---|---|
| v22 / v24（**initInstance 之前**） | `SetLoginServerInfo` + **同步 `ConnectLoginServer(5)`** + `AsyncConnectLoginServer(5)` | ✅ 服务端有 `=== 连接` |
| v27（唯一出帧那次） | 只有探针原有的 `AsyncConnectLoginServer(10)` | ✅ 那次连上并出帧 |
| v31/v33/v34（本轮） | 只有探针原有的 `AsyncConnectLoginServer(10)` | ❌ `conn=false` |
| v32（每帧重试） | 同步 + 异步**反复**调 | ❌ 连不上 |

⇒ 结论（可执行）：**唯一稳定出现过连接的调用是"同步 `ConnectLoginServer`"**（v22/v24）；
本轮的失败全部是"只有异步". 下一轮应先搞清 `ConnectLoginServer` 的**真实签名**（是否要传端口），
再决定用哪一种，而不是继续堆假设。

---

## 六、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_minloop_block.lua` | 现为 **v33**（只跳 Stop + 观察钩子，含 `SetLoginServerInfo/ConnectLoginServer/AsyncConnectLoginServer/openView/beginGame/video_player` 包装） |
| `server/dsh_minloop_probe.lua` / `patched/jstm_minloop.apk` | 探针与装机包（过 `lua-check` 真闸门） |
| 设备内 `files/dsh_v31.txt` / `dsh_v32.txt` / `dsh_v33.txt` | 本轮三次实验的客户端原始证据 |
| `logs/minloop/live7_stdout.log` | 服务端侧（本轮 0 连接 0 帧） |
| `report/report_20261001_minloop_round6_BREAKTHROUGH.md` | 上一轮：根因定位 + 唯一一次真实帧交换 |
