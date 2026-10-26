# 「点登录完全没反应、无报错」—— 定位到**登录门禁**这一层（下一枪已明确）

> 时间：2026-10-01 ｜ 用户实测：**没有报错，完全没反应**（账号界面点登录无任何变化）

---

## 〇、一句话结论

> **"无报错 + 无反应"是"按钮被门禁提前 return"的典型签名**，而证据正好指向这一层：
> `denglu_ctrl.luac::on1110Rolelist`（proto#23）的字符串里就有**一整套登录状态门禁**：
>
> ```
> 'setGatewayCallState'  'setServerRolesRequestState'  'setChangeUsrState'
> 'GlobalTimeTicket'     'LOGIN_REQUEST_tiket'         'remove'
> 'setCanLoginOpenGame'  'TRUE'  'code'
> ```
> ⇒ 客户端有一条 **"网关调用状态机 + 限流票据"**：若 `LOGIN_REQUEST_tiket` 未被清掉、
> 或 `gatewayCallState` 停在非预期值，**登录按钮就不会真正发请求**（既不报错也不跳转）。

---

## 一、本轮已核实的事实（服务端侧，`logs/minloop/live20_stdout.log`）

| 观测 | 值 | 读法 |
|---|---|---|
| 选区数据请求 | `POST /gateway/mobile/json` ×4 | ✅ 客户端**在要**服务器列表 |
| 账号登录请求 | `>> 1110 body=…'account'…'dsh_local'…` | ✅ **账号确实发出去了** |
| 我的应答 | `<< 1110 SCAccountLogin roles=3 least_career=0xf8` | ✅ 回了 3 个角色 |
| 客户端角色登录处理器 | `hit_on10102Login code_1 type_table` | ✅ 跑过、且 code=1 |
| 终态 | `scene_nil role_nil recv_35` / `no_scene_view_instance` | ❌ 仍未进场景 |

**注意**：这些 `1110` 可能来自**客户端自身重试/探针驱动**，**不等于**你点按钮真的触发了（这正是"没反应"要区分的地方）。

---

## 二、本轮排除与收窄（静态）

| 查了什么 | 结果 |
|---|---|
| `game/login/` 目录 | 抽出 `login_panel`（账号面板）、`server_panel`（选区）、`create_view`（建角）、`role_cell_login` 等 |
| `login_panel.luac`（18 个 proto） | **不含** `GatewayCallState/tiket/ChangeUsr/request1110/loginView` 任何门禁字符串 ⇒ **门禁不在这里** |
| ⇒ 门禁应在 | **`denglu_view.luac`（视图/按钮回调）**、**`user_panel.luac`**、**`denglu_mgr.luac`（状态机本体）** |

---

## 三、下一枪（已明确，二选一，都很快）

### 方案 A（最省、最直接）：**运行期把门禁值打出来**
探针 v62 挂钩并打印（点一次登录，立刻能看到被哪一项挡住）：
```lua
-- ① 状态机
pcall(function() log(DengluMgr:getInstance():getGatewayCallState()) end)
-- ② 限流票据是否还在
pcall(function() log(GlobalTimeTicket:getInstance():get('LOGIN_REQUEST_tiket')) end)
-- ③ 包住状态设置器，看谁在设置、设成什么
for _, m in ipairs({'setGatewayCallState','setServerRolesRequestState','setChangeUsrState'}) do 包一层 end
-- ④ 包住 request1110Role（proto#24）：确认"你点按钮"到底有没有走到它
```
**判据（一次性分辨）**：
- `request1110Role` **没被调用** ⇒ 按钮被**前置门禁**挡住（看 ① ② 的值就知道是哪一项）；
- 被调用但没上线 ⇒ 与早前"调用成功却不发包"同类（那时是客户端状态不对）。

### 方案 B：**静态读登录按钮回调**
`denglu_view.luac` / `user_panel.luac` 里找按钮回调与其**提前 return** 的条件
（重点看是否 `if ticket then return end` / `if state ~= X then return end`）。

---

## 四、完成 / 未完成

### 4.1 完成
1. ★ **回滚了上一轮"清空账号"的错误**（写回 `dsh_local` + 区 1）⇒ 客户端重新"有账号"。
2. ★ **核实三条链路都在动**（网关×4、`1110` 带账号、`on10102Login code_1`），但**终态仍 `scene_nil`**。
3. ★ **定位到"登录门禁"这一层**，并**排除 `login_panel.luac`**（不含门禁字符串）⇒ 下一步锁定
   `denglu_view` / `user_panel` / `denglu_mgr`。
4. ★ 把"无报错无反应"与"门禁 early-return"的对应关系写成可检验的假设。

### 4.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 点登录时**到底哪一项门禁挡着** | ❌ 下一轮（v62 运行期打印，一次性分辨） |
| 2 | 多账号隔离（`roles` 无 account 列 + `1110` 账号解析失败） | ❌ |
| 3 | 进场景（`scene_nil`） | ❌（另有根因：`config` 竞态、`addNpc` 形状等，见各自报告） |

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `analysis/login_panel.luac` / `server_panel.luac` | 本轮抽出的登录/选区面板（已排除门禁在此） |
| `logs/minloop/live20_stdout.log` | 本轮证据（网关×4 / `1110` 带账号 / `on10102Login code_1` / 终态 `scene_nil`） |
| `server/_ml41_add.lua` | ★ 回滚：写回可用账号 + 区 |
| 本报告 | ★ 门禁假设 + 下一枪 A/B 方案 |
