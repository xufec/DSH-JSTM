# 空白提示框 —— 四个根因，均已确认并修复

> 现象：标题「提示」，正文空白，按钮「确定」。
> **结论：这个外观有四个独立来源，四个都已在实测中定位并消除。**
>
> ⚠ 阅读顺序：根因 1/2 是最早定位的；**根因 3（10102/10103 的 `code`）才是"选服后进不去游戏"的主因**，
> 根因 4（13200 空 msg）是修完主因后残留的最后一个空正文提示。
> 两者都记在文末「第四轮」一节，并附 A/B 实测证据。

---

## ⏱ 实测复核（2026-09-16 09:18–09:23，qihoo 1.4.9 + 本地服务）

对**当前已安装运行的构建**做了一轮干净重启复现，结论：

- **`message NIL` = 0 次，`CommonAlert NIL` = 0 次**（`server/logs/http.log` DSH_PROBE 段）。
  即空白框在本构建 + 本服务上**不复现**。
- `on1110Rolelist` 每次 `code=1`（1110 成功分支）→ 根因 1 的 `message('')` 分支未执行。
- 服务端对 `15801` 已不应答（`EMPTY_REPLIES` 中移除）→ 根因 2 的 `message(nil)` 未出现。
- 屏幕截图 `shots/live_after_entergame.png`：停在选服/登录页，**无对话框**。
- 真实卡点不是空框，而是：**登录握手全通（1110→10102→10200/10201），但 `scene=nil`，客户端主动断开反复重连**（`tcp.log` 每 ~30–60s 一条 `=== closed`+新 `connection`）；每次循环伴随一个 `CommonAlert_len6`（**有 6 字正文，非空白**）。

**6 字正文尚未落库**（钩子只报长度、不上报正文，避免 URL 吃掉中文）。它紧随 `on10102Login/on10103ReLogin code_0` 出现，高度疑似“10102 被视为失败”的错误提示，但按“只用真实数据”原则，需补一次最小化 `print("[DSH_ALERT_TEXT] "..msg)` 的日志补丁或卡点截图后才能坐实。详见 `report/jstm_enter_game_diagnosis.md`。

---

## 根因 1：`SCAccountLogin_1110.code` 不等于 `TRUE`

```
denglu_ctrl.luac proto[23] on1110Rolelist:
    if resp.code == TRUE then setCanLoginOpenGame(true)
    else setCanLoginOpenGame(false); message(resp.msg) end
common_define.luac proto[7]:  TRUE == 1 , FALSE == 0
```

早期服务端回 `code = 0` 且 `msg = ''` ⇒ 走 else ⇒ `message('')` ⇒ 空白框。

**A/B 对照**（只改服务端 1 字节）：`code=0` → 空串弹窗 2 次；`code=1` → **0 次**。

**修复**：`build_1110_roles()` 的 `code` 由 `0` 改为 **`1`**。

---

## 根因 2：对"没解出编码"的命令回了**猜的包**（`15801`）

这一条正是"**有本地私服、有测试角色，点进入游戏仍弹空白框**"的来源。

### 定位手段：给 `message` 挂钩并打印调用栈

```lua
_G.message = function(msg, ...)
  local parts = {}
  for lv = 2, 6 do local i = debug.getinfo(lv, 'Sl'); ... end
  report('alert', 'message ' .. desc(msg) .. ' at=' .. stack)
  return om(msg, ...)
end
```

实测输出（长度 + 调用栈）：

```
t=alert&v=message_NIL_at__C_:-1 | string config.luac:364
        | string game/beast/beast_ctrl.luac:0
        | string base/base_controller.luac:0
        | string sys/gamenet.luac:0
```

⇒ **`game/beast/beast_ctrl.luac` 以 `nil` 调用 `message`。**

### 为什么是 nil

`beast_ctrl.luac proto[1]` 注册的是 `on15801 / on15806 / on15807 / on15811 …`，
而这些处理器**统一是**：

```lua
function on15801(resp)  ...  message(resp.msg)  end
```

`15801` 恰好在我的 `EMPTY_REPLIES` 里，是**按猜的布局**回的包
（该消息含若干 `D|Dsc*|` 动态子表，提取器没解出编码）：

```python
15801: lambda: w_u8(0)+w_u16(0)+w_u16(0)+w_u16(0)+w_u8(0)+w_u8(0)+w_u16(0)*6
```

布局猜错 ⇒ 客户端解出的 `msg` 为 `nil` ⇒ **`message(nil)` ⇒ 空白框**。

### 验证（一次只去掉这一条）

| | `message` 调用 |
|---|---|
| 去掉 15801 之前 | `message NIL` ← **空白框** |
| **去掉 15801 之后** | **`message NIL` 消失**，只剩 `CommonAlert len6`（6 字中文，**有正文**） |

`15801` 客户端仍在请求，只是我们**不再应答** —— 代价仅是那个面板空着，
远小于"弹一个空白错误框"。

### 结论性的做法

**宁可"不回"，也不要回一个会触发错误弹窗的畸形包。**
凡是 SC 结构里含未解出的 `D|Dsc*|` 动态子表的命令，
在把编码从 `cmd_resolve_<id>.luac` 的格式表里**真正还原出来之前，一律不应答**。

---

## 已排除的候选（保留记录）

| 候选 | 排除依据 |
|---|---|
| `sdkAlert('')` | **字节码级**：`sdk_function.luac proto[0]` 对 nil/空串**直接 return，不建框** |
| native 渠道 SDK 对话框 | `EWanSdk.is_close=true`，SDK 相关日志 **0 条**；且 A/B 已定位到 Lua 侧 |
| 初始化卡死 / 配置重试环 / 运行不稳定 | 前序方案已逐一解决（`GET /update/config` 729→0；驱动每帧挂钩稳定） |

---

## 一个必须记住的埋点教训

早期我给 `message` 上报的是 `message[<正文>]`，而 URL 安全替换会把**中文全变成下划线**，
于是"**中文有内容**"和"**空串**"在日志里长得一模一样，导致我误判了好几轮。

**改正**：只上报 **长度 / 是否 NIL**，不要把正文塞进 URL：

```lua
local function desc(v)
  if v == nil then return 'NIL' end
  return 'len' .. tostring(#tostring(v))
end
```

正是改成 `len`/`NIL` 之后，才一眼看出 `message NIL` 与 `CommonAlert len6` 的区别。

---

# 第四轮（12:34–12:56）——根因 3、根因 4

> 这一轮的两个根因都是**服务端应答的"code 约定 / 空正文"问题**，与前面同源：
> 客户端把协议应答里的 `code` 当"成败判定"、把 `msg` 当"提示正文"，
> 服务端一旦把这两者填错，就会走到 `message()/CommonAlert:show()` 分支上弹出空框。

## 根因 3：`SCRoleLogin_10102` / `SCRoleReLogin_10103` 的 `code` 必须等于 `TRUE`(=1)

### 字节码依据（与 1110 完全同一类约定）

```
denglu_ctrl.luac  on10102Login / on10103ReLogin:
    if resp.code == TRUE then
        SendProtocal(GetPrototype(10300))   -- 角色初始化
        LoginSucceedSendProtocal()
        DengluEvent:Fire(LOGIN_SUCCESS)      -- → SceneController 进场景
    else
        CommonAlert:show(resp.msg)           -- ← 弹框，且**不再往下走**
    end
common_define.luac proto[7]:  TRUE == 1 , FALSE == 0
```

⇒ 只要 10102/10103 回 `code = 0`，客户端就**永远不执行 `SendProtocal(10300)`、永不 Fire `LOGIN_SUCCESS`**，
`getScene()` 恒为 `nil`，界面停在登录态并反复重连。这正是"**选服后进不去游戏**"的直接原因。

### A/B 实测（只改服务端 1 字节）

| | 观察到的现象 | 证据 |
|---|---|---|
| `code = 0`（改前） | 每个连接都 `<< 10102 SCRoleLogin reply (code=0)`；随后立刻出现 `alertHex CommonAlert_hex_e7a1aee5ae9a … denglu_ctrl.luac`（正文 = **「确定」**，2 汉字 / 6 字节）；`state` 恒 `scene=nil` | `tcp.log` 12:24:04 / 12:29:13 / 12:33:32 三次 `CommonAlert`，`http.log` `t=state` 全是 `scene=nil` |
| `code = 1`（改后，`server/mock_server.py` 12:34:45） | `hit_on10103ReLogin code_1` / `hit_on10102Login code_1`；`state` 变成 `scene_table:_0xbee64310_role_table:_0xb3d8fec8_recv_N`；`CommonAlert` **0 条** | `http.log` 12:35:34 起持续到 12:56；`tcp.log` 心跳与 10206 正常 |

**修复**：10102/10103 应答的第一个字节由 `0` 改为 `1`（`w_u8(1)`）。
**注意与 10200 相反**：`scene_controller.luac proto[16]` 的 `on10200` 是
`if resp.code ~= 0 then message2(resp.msg) end`，即 **10200 的 0 才是成功**，不要一起改。

## 根因 4：`SC_13200` 回了个 `msg = ''` 的猜包 ⇒ `team_data` 里 `message('')`

### 字节码依据

`team_data.luac proto[3]` 尾段（`SC_13200` 的列表处理函数）**无条件**执行：

```
    91  GGET    A=2   D=25       ; message
    92  TGETS   A=3   B=1   C=26 ; resp.msg      ← B=1 是入参 resp
    93  CALL    A=2   D=258
    94  RET0
```

即函数末尾就是 `message(resp.msg)`，**没有任何 `if msg ~= ''` 之类的判空**。
我们回的 `SC_13200` 里 `msg=''` ⇒ 客户端执行 `message('')` ⇒ 空正文提示。

### 一一对应的实测证据

| 时刻 | `tcp.log` | `http.log` |
|---|---|---|
| 12:35:34 | `>> cmd=13200` + `<< 13200 empty-but-valid reply (26 bytes)` | `alertHex message_hex_（空）… team_data.luac … team_ctrl.luac` |
| 12:35:38 | 同上 | 同上 |
| 12:37:20 | 同上 | 同上 |

三对时间戳**逐条吻合**（13200 请求在哪一秒发出，`message('')` 就在那一秒上报）。

### 修复与复核

按与 15801 相同的原则处理：**把 13200 从 `EMPTY_REPLIES` 中移除**（不再应答）。
`SC_13200` 的字段顺序本就来自手册推断、未经核验，属"猜的包"，宁可不回。

复核（12:50:02，服务端重启后客户端自动重连）：

```
[12:50:02]   >> cmd=13200 ? body(4)=01 01 03 e9
             （没有 << 13200 —— 按预期不应答）
```

- `alertHex`：**12:37:20 之后再无任何一条**（整个 12:38–12:56 区间为 0）。
- `state`：`t_74190_scene_table:_0xbee64310_role_table:_0xb3d8fec8_recv_307` —— 场景与角色对象持续存在。
- 截屏复核（12:50 与 12:53 两张）：九宫格 `center_lum=84 / edge_lum=91 / delta=-6` ⇒ 均匀、**无居中弹窗**；
  OCR 只识别到场景内的系统喊话「欢迎来到绝世唐门」，无任何弹窗正文。

## 本轮的口径修正（纠正前面两处读数）

1. **`len6` 是字节数，不是 6 个汉字。** Lua 的 `#s` 计字节，`len6` = 6 字节 = **2 个汉字**。
   改用 hex 上报后量到的就是 `e7a1aee5ae9a` = 「确定」。所以那句"6 字正文尚未落库"应更正为
   "**正文 2 汉字「确定」**"。
2. **`CommonAlert` 与 `message` 是两个不同的入口**，都要挂钩上报：
   `CommonAlert.show` 会建带标题（`common_alert.luac proto[6]` 用 `getString('提示')`）与 ok 按钮的弹窗；
   `message` 是全局提示函数（`common_function.luac proto[120]` 里在 `IS_TEST_SERVER` 下转发给原始实现）。
   两个钩子都装，才能不漏判。

## 本轮之后的已知残留（非阻塞，已确认不影响进入游戏）

| 现象 | 来源 | 判定 |
|---|---|---|
| 「该功能暂未开放」 | `game/daily/daily_ctrl.luac`（12:37:11，`message_hex_e8afa5…` 正文非空） | 服务端 10922 只回了 0 条活动，客户端点开未开放入口时的**正常业务提示**，正文有内容、非空白框；不影响场景 |
| `>> cmd=10206`（移动请求）无应答 | `scene_controller.luac proto[41]` 的 `move` → `SendProtocal(10206)`；服务端未实现 | 实测不发包也不报错、不弹框、场景照常渲染（12:45 与 12:50 两段日志中 10206 均无应答，全程 0 告警）。按"猜的包不回"原则**保持不应答**，直到 `SC_10206` 的真实字段约定被核验 |
