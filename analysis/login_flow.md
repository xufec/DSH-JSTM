# 登录链路分析（login flow）

> 对象：`anzbao/jstm.apk`（1.4.9 / `com.shiyue.dldl.ewan.qihoo`）
> 方法：LuaJIT 字节码逐指令反汇编 + 实机运行验证；全部结论都有出处。

---

## 一、"进入游戏"按钮 → 后续调用

服务端视角实测到的命令序列（客户端自发发出，非我方代调时）：

```
10001 (FirstPack) → 1110 (帐号登录) → 10102 (登录指定角色) → 10103 (角色重连)
→ 10301 (获取角色基础信息) → 10502 (背包) → 10921/10922/10924/... 全子系统
```

对应的客户端处理函数（`denglu_ctrl.luac` 类表，`FNEW+TSETS` 映射得到）：

| 方法 | proto | 作用 |
|---|---|---|
| `request1110Role` | 24 | 发帐号登录（见第三节） |
| `on1110Rolelist` | 23 | 处理 1110 应答（角色列表 / 自动重连判定） |
| `request10102Login` | 32 | 登录指定角色 |
| `on10102Login` | 30 | 处理 10102 应答 → 发 10300 |
| `request10103ReLogin` | 34 | 角色重连 |
| `on10103ReLogin` | 33 | 处理 10103 → 转 `on10102Login` + Fire `RE_LINK_GAME` |
| `request10101Create` | 27 | 创建角色 |
| `requirehand` | 37 | 发 10001（`key="game_client"`） |
| `require1199` | 54 | 心跳 |

### `on1110Rolelist` 的自动重连分支（proto[23]）

```lua
local selfRoleVo = RoleCtrl:getInstance():getSelfRoleVo()
local scene      = SceneModel:getInstance():getScene()
if scene and selfRoleVo then
  self:request10103ReLogin(selfRoleVo.rid, selfRoleVo.srv_id)   -- 自动重连
else
  self.manager:setLoginInfo(resp)                                -- 否则显示角色列表
end
```

**注意：自动重连不由 `is_online` 决定，而由本机是否已有"角色+场景"决定。**
全新环境下不会走这条，会展示角色列表。

---

## 二、`loginData` / token / ticket / host / port 的来源

| 项 | 来源（有出处） |
|---|---|
| `loginData` | `DengluMgr`：`self.manager:getLoginData()`，字段含 `srv_id` / `account` / `platform` |
| `host` / `port` | 来自**服务器列表接口**下发的条目（`denglu_mgr` proto[8] 归一化后的 `ip` / `port`），再经 `GameNet:SetLoginServerInfo(host, port)` 传入 |
| `account` | `DengluCtrl.account`；**实测初值为 nil**，nil 时 1110 会组装失败（见下） |
| `token` / `sign` / `timestamp` / `channelId` | `DengluPlatForm:getInstance():getToken()/getSign()/getTimestamp()/getChannelId()`；由平台登录回调 `sdkBackLogin` 经 `onLoginInfo(data)` 写入 |
| `ticket` | `LOGIN_REQUEST_tiket`（`GlobalTimeTicket` 的条目名，不是网络票据） |
| `server_id` / `srv_id` | 服务器列表条目里的 `srv_id`（缺省由 `platform .. "_" .. zone_id` 拼出） |

### `request1110Role`（proto[24]）组装过程

```lua
if not GameNet:getInstance():IsLoginServerConnect() then return end   -- ①门禁
local proto = ProtocalRulesMgr:getInstance():GetPrototype(1110)
local args = { {key='account', val=self.account}, ... }   -- 共 10 项，见下
proto.args = args
self:SendProtocal(proto)
```

10 项 `args`（实抓 body 也逐项对上了）：
`account / timestamp / enter_srv_id / platform / device_id /
gettui_cid / idfa / token / channelId / sign`

**实测坑**：`self.account` 为 nil 时，`SendProtocal` 内部 `Encode` 失败并**静默返回 false**，
1110 根本发不出去。补上 `account` 后才成功。

---

## 三、连接游戏服的 API（反汇编确认的签名）

```lua
GameNet:SetLoginServerInfo(host_name, host_port)   -- proto[8]
GameNet:AsyncConnectLoginServer(timeout:number)    -- proto[12]
      -- 内部：net_manager:ConnectAsyn(host, port, timeout)
      -- ⚠ 第 3 个真参必须是 number（传 function 报
      --   "argument #4 is 'function'; 'number' expected"）
GameNet:IsLoginServerConnect()                     -- proto[9]，读 self.is_login_server_connected
```

`GameNet` 类表实际导出的方法（实测枚举）：
`AsyncConnectLoginServer, ConnectLoginServer, DisconnectLoginServer, GetLoginNetId,
IsLoginServerConnect, OnAsyncConnected, OnDisconnect, OnRecvMsg,
RegisterMsgOperate, SetFCMState, SetLoginServerInfo`

⚠ `Update` **不在类表里**（是 `gamenet.luac` 的局部函数），无法从 Lua 包装。

---

## 四、原生 → Lua 的回调契约（重要）

`lib/armeabi/libcocos2dlua.so` 符号可读，网络层就是 `cocos2d::CCNetManager`：

```
CCNetManager::OnConnect / OnRecv / OnDisconnect
CCNetManager::ON_NET_RECV / ON_NET_ASYNC_CONNECTED
GameNet::TcpClientBase::ConnectAsyn / BindCallbacks
UserMsgAdapter::SetRecvMsg(char const*, uint16, int)     ← C++ 类
```

而 `assets/src/game_start.luac proto[54]`（根 chunk）注册了 **5 个 Lua 全局**，
原生就是**按名字**调它们：

```lua
beginGame | OnNetAsyncConnected(=proto3) | OnNetRecv(=proto4)
          | OnNetDisconnect | OnNetSend
```

- `OnNetAsyncConnected(a,b,c)` → `DengluCtrl:openReconnect(false)` +
  `GameNet:OnAsyncConnected(a,b,c)`（= `gamenet` proto[13]，它才正规地置连接标志并调
  `requirehand()` + `request1110Role()`）
- `OnNetRecv(cmd, a2, a3)` → `GameNet:OnRecvMsg(...)`（`gamenet` proto[17]）

实测：四个回调都是 function；`OnNetRecv` 被调用时**第一参数就是命令号**。

---

## 五、渠道 SDK 的参与程度（是否需要在 Lua 层绕过）

`com/shiyue/sdk/EWanSdk` 的**每个**方法都以 `if (!this.is_close)` 开头，
而 `is_close` 在整个 dex 里**只有 `<init>` 一处写入**。

当前联调构建（`patched/jstm_fakelogin.apk`）把该字段置为 `true`（dex 单字节补丁
`0x61EDFD: 00 → 10`，即 `const/4 v0,#1`），效果实测：

```
SuperThirdSdk_360 日志 : 0 条
ContainerActivity      : 0 条
EWanSdk 日志           : 0 条
```

⇒ **渠道 SDK 全程不参与**，`sdkBackInit` / `sdkBackLogin` 由注入的 Lua 自供。
因此"进入游戏"阶段的失败**不来自渠道 SDK**。
（若换用未打该补丁的构建，则 SDK 会参与，native 对话框可能因此出现——见
`analysis/blank_dialog.md` 第二节。）
