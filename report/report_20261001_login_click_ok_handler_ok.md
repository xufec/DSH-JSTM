# v62/v63 结果：**点击有效、应答处理也正常（ok=true）** ⇒ 排除了"按钮被门禁挡住"与"处理器抛错"

> 时间：2026-10-01 ｜ 用户实测：账号界面点登录"没有报错，完全没反应"

---

## 〇、一句话结论

> 两个探针把问题**夹到了一个很窄的范围**：
>
> ```
> v62: ★ request1110Role 被调用 参数=            ← ★ 点按钮**确实走到了发登录请求**
>      setter setGatewayCallState = 0
>      -- tick10 gatewayCallState=0 票据=n/a
> v63: ★ on1110Rolelist 入口 code=1 类型=table ⇒ ok=true   ← ★ 应答处理器**跑完且无任何错误**
> ```
>
> ⇒ **"门禁挡住按钮"（我上一轮的假设）被否证**：`request1110Role` 被调用了；
> ⇒ **"处理器内部抛错被吞掉"（我原本最怀疑的）也被否证**：`ok=true`。
>
> 那么剩下的解释只可能是两类：
> **① 处理器把界面更新到了"另一个（非当前显示的）loginView 上"** —— 即**探针/视图层干涉**；
> **② 处理器内部有个"静默跳过"的条件**（例如它在等**网关服务器列表**到位后才切到选区）。

---

## 一、本轮证据

| 探针 | 观测 | 读法 |
|---|---|---|
| **v62** | `request1110Role 被调用`（参数为空）、随后 `setGatewayCallState = 0` | ★ 点击**有效**；按钮层无门禁问题 |
| v62 | `gatewayCallState=0`、`serverRolesRequestState=nil`、`changeUsrState=nil`、`票据=n/a` | 三个 getter 里只有一个存在；**票据取值方式 UNKNOWN**（我的调用方式可能不对） |
| **v63** | `on1110Rolelist 入口 code=1 类型=table ⇒ ok=true` | ★★ 处理器**无错误**；我的 `code=1` 被正确识别 |
| 服务端 | `<< 1110 roles=3 least_career=0xf8`；`POST /gateway/mobile/json` ×4 | 链路数据都对 |

---

## 二、★ 由"ok=true"推出的最可能原因

`on1110Rolelist`（proto#23）开头是：
```lua
if loginView and not tolua.isnull(loginView:getViewById(1)) then
    loginView:getViewById(1):stopAllActions()
    manager:setServerRolesRequestState(false); manager:setChangeUsrState(false)
    GlobalTimeTicket:getInstance():remove('LOGIN_REQUEST_tiket'); manager:setGatewayCallState(0)
end
…（按 msg.code 走成功分支：setLoginInfo / RoleCtrl / request10103ReLogin）
```
若 **`loginView` 指向的不是屏幕上那个视图**（或为 nil），这个处理器就会：
- 更新一个**看不见的视图**（或什么都不更新）⇒ **界面上"完全没反应"**；
- 且**不报错**（`ok=true`）—— 与实测**完全吻合**。

**谁会弄出"两个 loginView"？** 最可疑的是**我自己的探针**（fake-login 补丁 + 累加到 v63 的十几个块）。
本会话早前就有先例：**清空账号、写死区、自动登录**这几件事，都是我的探针把客户端流程搅乱。

---

## 三、下一枪（最高性价比）：**对我的探针做"二分"**

```
① 出一个**最小探针**（只保留"让客户端连到我服务器"的那一段驱动，其余 v39..v63 全不装）
   ⇒ 装、重启、点登录：若界面**正常跳转** ⇒ **确认是我的探针在干涉 UI**；
② 若是，再逐个加回块，找出"哪一块"导致 UI 不动（预计是碰 UserDefault / 视图 / 调度器的那几个）；
③ 若最小探针下**仍然无反应** ⇒ 才回到客户端本身（那时去看网关应答处理 + 面板切换函数）。
```

**为什么先做这个**：本轮两条假设都被否证，而"探针干涉 UI"是**唯一同时解释"ok=true + 界面无反应 + 无报错"**的原因，
且验证成本极低（一次打包 + 一次重启）。

---

## 四、完成 / 未完成

### 4.1 完成
1. ★★ **否证"按钮被门禁挡住"**：`request1110Role` **确实被调用**（v62 实测）。
2. ★★ **否证"应答处理器抛错"**：`on1110Rolelist` **`ok=true`**、`code=1` 被正确识别（v63 实测）。
3. ★ 由此把原因夹到两类：**探针/视图层干涉** 或 **处理器内部静默条件**，并指出前者更符合全部观测。
4. ★ 给出**二分法**验证方案（最小探针 → 逐块加回）。

### 4.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 是否我的探针干涉 UI | ❌ 下一轮（最小探针二分） |
| 2 | 网关应答处理 / 面板切换函数（若探针无关才查） | ❌ |
| 3 | 多账号隔离（`roles` 无 account 列、`1110` 账号解析失败） | ❌ |
| 4 | 进场景（`scene_nil`） | ❌（另有根因报告） |

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml62_add.lua` | ★ 门禁/按钮探针（证明点击有效） |
| `server/_ml63_add.lua` | ★ 处理器 pcall 探针（证明 `ok=true`） |
| 设备 `files/dsh_v62.txt` / `files/dsh_v63.txt` | ★ 本轮两条关键证据 |
| `analysis/denglu_ctrl.luac` | `on1110Rolelist`(proto#23) 反汇编依据 |
