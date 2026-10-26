# 登录/选区/选角：本轮定位与现状（用户：卡在账号界面、登不进去；要能自己切账号/选区/选角）

> 时间：2026-10-01 ｜ 用户选择：**先保证"能自己切账号、选区、选角"**

---

## 〇、本轮先回滚了我上一轮的错误

| 我上一轮做的 | 后果（用户实测） | 本轮处置 |
|---|---|---|
| **清空 `last_login_account`**（想把账号交回用户） | 客户端**"没有账号、登不进去了"** | ✅ **已回滚**：写回可用账号 `dsh_local` + 区 `1` |
| 停止写 `local_srv_id` | 选区流程不稳 | ✅ 恢复写入（选区/列表消费的前置） |

**当前服务端侧实测（`logs/minloop/live20_stdout.log`）**：
```
POST /gateway/mobile/json ×4                      ← ★ 客户端**确实在要选区数据**
>> 1110 body(217)=00 0a 00 07 'account' 00 09 'dsh_local' …   ← ★ 账号确实在发（我的日志打 None 是**我的解析缺陷**）
<< 1110 SCAccountLogin roles=3 least_career=0xf8   ← 回 3 个角色 ✓
hit_on10102Login code_1 type_table                 ← ★ 客户端的角色登录处理器**跑过且 code=1**
… 最终: scene_nil role_nil recv_35 / no_scene_view_instance   ← 但仍未进场景
```

---

## 一、★ 本轮反汇编发现：客户端**自己走的是 `10103`**

`denglu_ctrl.luac::on1110Rolelist`（proto#23）关键字符串与结构：
```
loginView:getViewById(1):stopAllActions(); manager:setServerRolesRequestState(false);
manager:setChangeUsrState(false); GlobalTimeTicket:remove('LOGIN_REQUEST_tiket');
manager:setGatewayCallState(0)
… 若 msg.code == TRUE 则 …  'setLoginInfo' / 'srv_id' / 'rid' / 'request10103ReLogin' / 'RoleCtrl'
```
⇒ **`1110` 成功后，客户端用 `setLoginInfo(rid, srv_id)` + `request10103ReLogin`（角色重连）进入游戏**，
即它的入口命令是 **`10103`**（不是 `10102`）。
本服已把 `10103` 转发到与 `10102` 相同的处理（回 `code=1` 并推 `10200/10201`）⇒ 这条链路理论上通。

---

## 二、由此得到的两个"可修"缺口（下一轮直接做）

| # | 缺口 | 影响 | 修法 |
|---|---|---|---|
| 1 | **`on_1110` 解析不到账号**（日志恒为 `account=None`，而客户端确实发了 `{account:"dsh_local"}`） | 无法按账号区分角色 ⇒ **"切换账号"做不到该有的效果** | 按 `CSAccountLogin_1110.args` 的**真实结构**读账号（先打印原始解码，不猜字段名） |
| 2 | **`roles` 表没有 account 列** | 角色列表是"全服角色"而不是"本账号角色" ⇒ 多账号会互相看到彼此的角色 | 加 `account` 列：建角时写入；`1110` 按账号过滤（**先确证账号字段语义**） |

> 这两条合起来正是"**多账号 / 切换账号**"的地基；而"选区"依赖网关列表（客户端已在请求，×4 次）。

---

## 三、需要你提供的一个关键信息（我看不到画面）

**你在账号界面点"登录"之后，屏幕上发生了什么？**
- 有没有**报错文字/提示框**（把文字告我，这是最有用的线索）？
- 是**停留不动**、还是**闪一下又回到账号界面**、还是**转圈**？

有了这句提示文字，我可以直接去查对应的客户端分支（例如 `CommonAlert:show(msg)` 是哪个 handler 触发的），
而不是继续盲猜。

---

## 四、完成 / 未完成

### 4.1 完成
1. ★ **回滚了上一轮"清空账号"的错误**（写回 `dsh_local` + 区 1）⇒ 客户端重新"有账号"。
2. ★ **实测确认三条链路都在动**：网关选区请求 ×4、`1110` 带账号、`on10102Login` code=1。
3. ★ **反汇编查清客户端自己的入口是 `10103`（角色重连）**，并确认本服已支持。
4. ★ **定位两个可修缺口**：`1110` 账号解析、`roles` 缺 account 列（"切换账号"的地基）。

### 4.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 界面具体表现（报错文字） | **需要你告我** |
| 2 | `1110` 账号解析 / 多账号隔离 | ❌ 下一轮 |
| 3 | 进场景（`scene_nil` / `no_scene_view_instance`） | ❌（另有报告：`config` 竞态 + `addNpc` 形状等） |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml41_add.lua` | ★ 回滚：写回可用账号 `dsh_local` + 区 1（`v49c`） |
| `logs/minloop/live20_stdout.log` | ★ 本轮证据（网关×4、`1110` 带账号、`on10102Login code_1`、终态 `scene_nil`） |
| `analysis/denglu_ctrl.luac` | ★ `on1110Rolelist`(proto#23) / `on10101Create`(proto#26) / `request10101Create`(proto#27) |
