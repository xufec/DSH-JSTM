# NPC 交互流程（Phase 5A 审计）

> 方法：1.4.9 客户端字节码反汇编 + **实机点击测试**（保持服务器日志开启）
> 状态只用：**已确认 / 已验证 / 待验证 / 未知**

---

## 一、代码层确认的入口链（**已确认**）

```
scene/element/npc.luac  (Npc 实体，带点击体)
        │  点击
        ▼
npc_ctrl.luac  proto[17] = NpcCtrl:clickNpcOpenDialog(npc)
        │
        ├─ ProtocalRulesMgr:getInstance():GetPrototype(15203)
        └─ self:SendProtocal(proto)                    ← 发出 CS_15203
        ▼
（服务端应回 SC_15203{code:u8, msg:string}）
        ▼
NpcDialogs（npc_dialogs.luac）打开对话 UI
```

反汇编原文（`npc_ctrl proto[17]`，params=2，仅 5 条字节码）：

```lua
function NpcCtrl:clickNpcOpenDialog(npc)
  local proto = ProtocalRulesMgr:getInstance():GetPrototype(15203)
  self:SendProtocal(proto)
end
```

**⇒ 「NPC 点击 → `CS_15203`」是【已确认】（客户端代码证据）。**

---

## 二、实机点击测试（**四组，结果如实**）

环境：1.4.9 APK 已在史莱克城（map 10001）、服务器日志开启、`adb -s 127.0.0.1:16384`。

### 测试 A：点击 NPC

| 项 | 内容 |
|---|---|
| 操作 | 点击 NPC「唐舞桐」 |
| 客户端发出 | `>> cmd=10341 ? body(17)=00 01 00 00 03 e9 00 01 31 00 00 00 00 67 00 00 17`（**头像查询**）<br>`>> cmd=1199 heartbeast`（心跳） |
| **是否发出 `15203`** | ❌ **没有** |
| 结果 | **未复现 NPC 交互协议** |

### 测试 B：连续点击 NPC

| 项 | 内容 |
|---|---|
| 操作 | 同一位置连点 3 次 |
| 客户端发出 | `>> cmd=10204 ? body(8)=00 6b 00 31 03 e9 00 01`（**移动**）<br>`>> cmd=1199`（心跳） |
| 结论 | 点击被当成**地图移动指令**，**没有**重复发送交互协议 |

### 测试 C：靠近 NPC 后点击

| 项 | 内容 |
|---|---|
| 操作 | 先点 NPC 位置 4 次（走过去）→ 再点 3 次 |
| 客户端发出 | 仅 `>> cmd=1199`（心跳） |
| 结论 | **没有**触发交互协议 |

### 测试 D：点击不同 NPC

| 项 | 内容 |
|---|---|
| 操作 | 屏幕上另一定位的 NPC「霍雨浩」（1520,140） |
| 结果 | **本轮未执行**（前面的测试已显示点击不触发交互，先停下来记录） |
| 状态 | **未完成** |

---

## 三、时间线（实测，**未走通**）

```
T0  玩家进入地图                       ✅ 已验证
T1  NPC 已显示（唐舞桐 / 霍雨浩 等）    ✅ 已验证
T2  玩家点击 NPC                        ✅ 已做
T3  客户端发送 CMD：只有 10341 / 10204 / 1199    ⚠️ 不是 15203
T4  服务器收到                          ✅（收到了 10341 / 10204 / 1199）
T5  服务器返回                          ✅（10341 未实现；10204 已回）
T6  客户端收到响应                      ✅
T7  NPC 对话 UI 打开                    ❌ **未打开**
```

**⇒ 交互链路在 T3 就断了：点击没有走到 `clickNpcOpenDialog`。**

---

## 四、`15203` 的字段（**已确认**，来自 1.4.9）

```
CS_15203 — 无字段（空消息）
SC_15203 — code:uint8, msg:string
```

**注意：`CS_15203` 不带 NPC id。** ⇒ 点击哪一个 NPC **不在这个协议里**。

---

## 五、为什么点不出交互（**候选原因，全部为"待验证"，未确认**）

| # | 候选原因 | 支持/反对 | 状态 |
|---|---|---|---|
| 1 | 点击未命中 NPC 的点击体（屏幕坐标 ≠ 点击体坐标） | 点击确实落到了地图（产生 `10204` 移动），说明**命中了地图层** | **待验证** |
| 2 | NPC 需要"紧邻"才可交互，而角色未走到位 | 走近后仍无反应 | **待验证** |
| 3 | 我们下发的 NPC 条目缺某个"使能交互"的字段 | 名字能正确显示 ⇒ bid 有效，此条证据不足 | **待验证** |
| 4 | `clickNpcOpenDialog` 的触发不在普通单击上（可能需要双击/长按） | 无证据 | **未知** |

---

## 六、★★★ 决定性验证：`clickNpcOpenDialog` **从未被调用**

用探针包住 `NpcCtrl` 的点击入口（`clickNpcOpenDialog` / `setOpenNpc` / `open` /
`openElemDialogs`），然后实机点击 NPC。

### 钩子安装结果（已装成功）

```
setOpenNpc_wrapped
clickNpcOpenDialog_wrapped          ← 已包裹
open_wrapped
openElemDialogs_wrapped
sceneClickEvt_NOT_function_table    ← sceneClickEvt 是"表"不是函数（事件注册表）
elemDialog_NOT_function_nil
```

### 点击 NPC 的结果

| 项 | 结果 |
|---|---|
| NPC 位置（视觉定位） | 「唐舞桐」名字在 **(470,475)**，头顶 ~(470,450) 有一个**蓝色对话气泡图标**（提示可交互） |
| 点击动作 | 依次点了 (470,475)、(470,450)、(470,480)、(470,470) |
| **`clickNpcOpenDialog` 是否被调用** | ❌ **一次都没有**（`npcH` 上报 0 条命中） |
| 服务器实际收到 | 全是 `>> cmd=10204`（**移动**）：`00 64 00 2c` → `00 63 00 2a` → … → `00 46 00 35` |
| 含义 | 角色**确实朝 NPC 的格子走了过去**（坐标一路变到 NPC 附近），但**全程只发移动包** |

### ★ 结论（**已确认**，非推测）

**点击 NPC 时，请求**根本没有进入 NPC 的点击处理链** ——
点击被**地图层**拦截，解释为"移动到该点"（`CS_10204`），
因此 `CS_15203` **从未被发出**。**

**⇒ 这也就解释了前四组测试为什么抓不到 NPC 交互协议：
不是"服务端没实现"，而是"客户端压根没发"。**

---

## 七、由此确定的 Phase 5B 首要任务

**必须让点击能命中 NPC**。已排除的与待查的：

| # | 候选 | 本轮证据 | 结论 |
|---|---|---|---|
| 1 | 点击坐标不对 | 点了 4 个位置（身体/气泡/上下），全部变成 `10204` | **倾向排除**（角色确实往 NPC 走） |
| 2 | NPC 未注册点击体 | `clickNpcOpenDialog` **0 次命中** | **强候选**（这正是"没注册"的表现） |
| 3 | 需要"紧邻才可交互" | 角色走到了 NPC 附近，仍只有 `10204` | **待验证**（未确认是否真的到位） |
| 4 | NPC 条目缺"使能交互"字段 | 名字显示正常，但交互无 | **强候选**（见 `npc_data_source.md` §四） |

**⇒ Phase 5B 第一步（最决定性）：检查我们下发的 `SC_10201.npcs` 条目
与客户端"可点击 NPC"所需的字段是否齐全** ——
重点比对 `scene/element/npc.luac`（`Npc` 实体）注册点击体时读了哪些字段。

---

## 九、★★★ 续查（本轮）：点击链路**其实通**，问题在"打不中"

### 9.1 代码层：`registEvent` 是**无条件**的

反汇编 `scene/element/npc.luac proto[4]`：

```lua
function Npc:registEvent()
  self.container:setTouchEnabled(true)
  self.container:addTouchEventListener(<closure>)   -- 点击回调，无条件注册
end
```

**⇒ NPC 实体创建时就会挂上点击回调，**不看任何数据字段**。**
（这也**否证**了"因为缺字段所以没注册点击体"这个候选原因。）

### 9.2 探针实测：25 个 NPC **全部**注册成功，且 `clickHandler` **被触发过**

包住 `Npc.registEvent` / `Npc.clickHandler` / `Npc.setVo` 后实测：

```
25 x  setVo                                     ← 25 个 NPC 都设了 VO
registEvent_vo_bid_10160 / 10170 / 10175 / 50000 / 50003 …  ← 逐个 NPC 都调用了 registEvent
1 x  clickHandler_vo_bid_10030_name_______      ← ★ clickHandler 确实被触发过
```

**⇒ 结论：`
· NPC 的点击体对 25 个 NPC **全部注册成功**；
· `clickHandler` **可达并被触发过**（`vo.bid=10030`，正是 `Config.Mission[10010].commit_npc_id`）。**

**⇒ 前几轮"点不出交互"的原因**不是"点击体没注册**，而是**我的点击多半落在**地图层**上
（被解释为 `CS_10204` 移动）** —— 即**操作问题，不是客户端问题**。

### 9.3 仍未能用"点屏幕"稳定命中 NPC

本轮最后又点了 5 个位置（含视觉给出的 NPC 身体位置 (440,60)/(720,840)/(840,840)），
结果**仍然只有 `10204` + `1199`，`npcE`/`npcH` 均 0 命中**。

**⇒ 结论（如实）：屏幕点击这条路我**没有**找到稳定命中的方法**（NPC 立绘窄、地图层遮挡）。

---

## 十、★ Phase 5B 的最优路径：**绕过点击，主动调用客户端入口**

既然已经确认：
- `NpcCtrl.clickNpcOpenDialog` 就是发送 `CS_15203` 的入口（**已确认**，代码证据）；
- `Npc.registEvent`/`clickHandler` 链路正常（**已验证**，探针实测）；

**⇒ 就不必再依赖"点中 NPC"，直接用 Phase 4B 那套"主动调用客户端 sender"的手法：**

```lua
-- 探针里直接调用（参数为相关 npc；注意 15203 本身不带字段）
NpcCtrl:getInstance():clickNpcOpenDialog(npc_vo)
```

这样**必定发出 `CS_15203`**，随后：

1. 先**只观察**客户端是否发出 `15203`（验证入口）；
2. 再实现 `SC_15203{code:u8, msg:string}` = `code=0` + 空串；
3. 观察 `NpcDialogs`（`npc_dialogs.luac`）是否打开原版对话 UI。

**⇒ 这条路径不依赖点击命中，可重复、可回归。**

---

## 十二、续查（主动调用入口）—— **撞到两堵墙，如实记录**

### 12.1 做法

用探针主动调用客户端的点击入口（**只观察，不改服务器协议**）：

```lua
NpcCtrl:getInstance():clickNpcOpenDialog(<npc_vo>)
```

### 12.2 结果

**第 1 次（未传 vo）**

```
t=npcClick&v=vo_type_nil_bid_false
t=npcClick&v=clickNpcOpenDialog_ok_false_err= string game/npc/npc_dialogs.luac:0:
           attempt to index a nil value
服务器是否收到 15203：❌ 没有
```

**第 2 次（从 `Npc:setVo` 的参数截获 vo）**

```
setVo_wrapped
setVo_arg_bid_10010_arg_name_______        ← 截获成功（参数里确实有 vo）
setVo_arg_bid_10020_arg_name__________
…
t=npcClick&v=vo_type_nil_bid_false         ← ★ 但调用时 _G.__dsh_npc_vo 仍是 nil
t=npcClick&v=clickNpcOpenDialog_ok_false_err= … npc_dialogs.luac:0: attempt to index a nil value
服务器是否收到 15203：❌ 没有
```

### 12.3 本轮的两条**新结论**（都算收获）

| # | 结论 | 依据 | 状态 |
|---|---|---|---|
| 1 | **`clickNpcOpenDialog` 不只会 `SendProtocal(15203)`，它还会调用 `npc_dialogs.luac`** | 传 nil 时报错位置在 `npc_dialogs.luac: attempt to index a nil value` | **已确认** |
| 2 | 用 nil 调用 ⇒ 在 `npc_dialogs` 处中断 ⇒ **`15203` 不会发出** | 两次调用均无 `15203` | **已确认** |

> 注：第 1 条说明我之前对 `npc_ctrl proto[17]`（仅 5 条字节码）的读取**不完整** ——
> `SendProtocal(15203)` 之后还有 UI 相关调用（或在另一层包装里）。
> **这一点更正已记录**，避免后续按"只发协议"去理解。

### 12.4 未解决（**待验证**）

- **截获到的 vo 没能传到调用点**（`setVo_arg_bid_10010` 拿到了，但 `_G.__dsh_npc_vo` 在调用时是 nil）。
  **原因未确认**（可能：探针块与钩子块不在同一全局环境、或插入顺序问题）。
- **⇒ 因此 `CS_15203` 至今仍未抓到**，5A 的"抓到 NPC 点击实际协议"这一项**仍未达成**。

### 12.5 下一步（给 Phase 5B 的更保守路径）

1. 先解决"把真实 vo 交给调用点"——例如**在钩子里当场调用**（拿到 `a1` 立刻调
   `clickNpcOpenDialog(a1)`），而不是存到全局后再调；
2. 或者**不调用 `clickNpcOpenDialog`**，直接 `SendProtocal(GetPrototype(15203))`
   （绕开 `npc_dialogs` 那段），先确认"`15203` 能不能发出去、服务器能不能收到"；
3. 再实现 `SC_15203` 并观察对话 UI。

**⇒ 第 2 条最干净：它把"能不能发/能不能收"与"UI 能不能开"两件事分开验证。**

---

## 十三、日志

| 文件 | 内容 |
|---|---|
| `logs/1.4.9/npc_interaction.log` | 前四组"点屏幕"测试的 TCP 日志 |
| `logs/1.4.9/npc_click_probe.log` | 包住 `NpcCtrl` 点击入口的 `npcH` 上报（0 命中） |
| `logs/1.4.9/npc_click_tcp.log` | 上述期间的 TCP（全是 `10204` 移动） |
| `logs/1.4.9/npc_entity_probe.log` | 包住 `Npc.registEvent/clickHandler/setVo` 后的日志 |

> ⚠ **证据留存的诚实说明**：`25×setVo、逐 NPC registEvent、1×clickHandler` 这组读数
> 来自"包住实体后**第一轮**"的终端输出；随后我在做点击测试前**清空了 `http.log`**，
> 因此磁盘上的 `npc_entity_probe.log` 是**点击测试那一轮**的日志（其中 `npcE` 为 0 条）。
> **这组读数的原始日志未能落盘**，只有上面的转写记录 —— 如实标注，避免误当成"文件里的证据"。
> 若需可复现，重跑一次"只等待不点击"即可重新得到该组上报。
