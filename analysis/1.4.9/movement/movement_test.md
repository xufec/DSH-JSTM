# 1.4.9 角色移动 —— 测试记录（已验证）

> 结论：**协议链路、四方向移动、落盘、重登恢复、服务器重启后恢复 —— 全部实测通过。**
> 但**有一个必须说清的前提**：为绕过客户端"地图资源未加载完"的门禁，
> 诊断时用探针把 `isLoadState__` 强行置为 `true`；
> **原版客户端在自然操作（摇杆）下仍然不能移动**，原因见第六节。

---

## 一、✅ 四方向移动全部成功（实测抓包）

探针按顺序调用客户端自己的 `SceneController:getInstance():move({x,y})`：

| 方向 | 目标坐标 | 服务端收到的 `CS_10204` | 落盘 |
|---|---|---|---|
| 右 | 1324,2040 | `05 2c 07 f8` → x=0x52c=1324, y=0x7f8=2040 | `persist pos=(1324,2040)` ✅ |
| 下 | 1320,2044 | `05 28 07 fc` → x=1320, y=2044 | `persist pos=(1320,2044)` ✅ |
| 左 | 1316,2040 | `05 24 07 f8` → x=1316, y=2040 | `persist pos=(1316,2040)` ✅ |
| 上 | 1320,2036 | `05 28 07 f4` → x=1320, y=2036 | `persist pos=(1320,2036)` ✅ |

⇒ **A 向上 / B 向下 / C 向左 / D 向右 全部通过**（E 连续移动＝连续四次成功；F 停止＝不再调 `move()` 后无新包）。

---

## 二、✅ 重登恢复坐标（实测）

退出前落盘 `x=1320, y=2036` → 杀进程 → 重新登录：

```
[13:34:27]  .. role 1001 restored pos=(1320,2036) from state
[13:34:27]  << 10200 SCRoleEnter (server push) bid=10001 (1320,2036) (19 bytes)
[13:34:27]  << 10201 SCMapGird (server push) roles=1 (62 bytes)
```

⇒ **重登后服务端下发的进场景坐标 = 退出前最后位置。**

## 三、✅ 服务器重启后角色仍在（实测）

停掉旧服务端（释放 8080/9000）→ 重新启动（新 PID 24760）→ 再登录：

```
[13:36:03]  .. role 1001 restored pos=(1320,2036) from state
[13:36:03]  << 10200 SCRoleEnter (server push) bid=10001 (1320,2036) (19 bytes)
```

⇒ **JSON 落盘跨进程重启有效。**

---

## 四、服务端实现

```python
if cmd in (10204, 10205):                      # CS_10204{x:u16,y:u16} / CS_10205 瞬移
    x, y = struct.unpack_from('>HH', body, 0)
    save_role_pos(rid, x, y)                   # → server/state/role_<rid>.json
    send(pack_frame(cmd, w_u32(rid)+w_str(srv_id)+w_u16(x)+w_u16(y)))   # SC_10204
```

`_send_10200()` / `10201` 应答都先走 `role_with_saved_pos(cfg)`，把落盘坐标填回。

---

## 五、`isLoadState` 门禁（已定位）

`scene_controller.move`（proto[37]）开头：

```lua
if self.model:isOnTeamFollow() then return end
if not self.model:isLoadState() then return end      -- ★ 卡在这里
```

| 谁管 | 行为 |
|---|---|
| `scene_view proto[1] @95-99` | 视图初始化 → `setLoadState__(false)` |
| **`scene_view proto[37] @18-22`** | **地图资源异步加载完成 → `setLoadState__(true)`** |

探针实测 `isLoadState` 恒为 `false` ⇒ `move()` 空转（`pcall` 返回 ok 但不发包）。

**诊断实验**：探针把 `setLoadState__(true)` 强行置位后，`move()` 立刻正常发包（上表四方向即由此得到）。
⇒ 这**区分开了**两种可能：**移动协议与服务端完全没问题**，卡点纯在客户端的加载门禁。

---

## 六、⚠️ 仍然存在的真实阻塞

**原版客户端在自然操作下仍不能移动**：`isLoadState` 从不为真，
说明**地图资源异步加载没有走完**（`scene_view proto[35]/[36]` 的 `mapResAsyncList` 未完成）。

已排除：

| 候选 | 排除依据 |
|---|---|
| 点错屏幕坐标 | 已绕过输入，直接调 `move()` |
| `bid` 非法 | **`bid=10001` 合法**：`assets/res/scene/10001/` 存在，192 个文件 |
| 向我们下载资源失败 | HTTP 日志里**没有**任何 `/cdn/`、`/res/`、`.plist`、`.png` 请求 |

**可疑线索**：场景阶段 logcat 出现加载 `src/common/error_msg.luac` 与
`src/game/battle/battle_fail.luac`，说明走过错误显示路径。
下一步应先查 `mapResAsyncList` 在等什么、以及这两个文件被谁触发。

**必须强调**：把 `setLoadState__` 强行置真是**诊断手段，不是修复**。
不得据此宣布"角色可以正常移动"。


---

## 一、服务端实现（已完成）

```python
if cmd in (10204, 10205):                      # CS_10204{x:u16,y:u16} / CS_10205 瞬移
    x, y = struct.unpack_from('>HH', body, 0)
    save_role_pos(rid, x, y)                   # 落盘 server/state/role_<rid>.json
    send(pack_frame(cmd, w_u32(rid)+w_str(srv_id)+w_u16(x)+w_u16(y)))   # SC_10204
```

---

## 二、✅ 已验证：客户端确实会发 `CS_10204`，服务端确实收到并落盘

实测抓包（`server/logs/tcp.log`）：

```
[13:24:12]   >> cmd=10204 ? body(8)= 05 28 07 f8 | 00 01 31 6f
                                  x = 0x0528 = 1320
                                  y = 0x07F8 = 2040
```

同时 `server/state/role_1001.json` 的 `saved_at` **被更新**（`save_role_pos()` 执行）。

⇒ **"客户端发移动包 → 服务端收包 → 落盘"这条链是通的。**

---

## 三、❌ 未通过：`move()` 因加载门禁而空转

`scene_controller.move`（proto[37]，params=2，收 `{x,y}`）开头两个门禁：

```lua
if self.model:isOnTeamFollow() then return end
if not self.model:isLoadState() then return end      -- ★ 卡在这里
```

探针实测（`t=gates` 上报）：

```
t=gates&v=idx_1_isOnTeamFollow_nil_isLoadState_false
t=gates&v=idx_2_isOnTeamFollow_nil_isLoadState_false
t=gates&v=idx_3_isOnTeamFollow_nil_isLoadState_false
t=gates&v=idx_4_isOnTeamFollow_nil_isLoadState_false
```

**`isLoadState()` 恒为 `false`** ⇒ `move()` 直接 return，不发包。

我主动调用 `SceneController:getInstance():move({x=1324,y=2040})` 四次（方向各一），
`pcall` 全部 `ok=true`，但**只有**那次客户端自发的 10204 出现在日志里。

---

## 四、`isLoadState` 是谁在管（已定位）

| 位置 | 行为 |
|---|---|
| `scene_view.luac proto[1] @95-99` | 视图初始化时 `self.model:setLoadState__(false)` |
| **`scene_view.luac proto[37] @18-22`** | **地图资源异步加载完成时 `self.model:setLoadState__(true)`**，并删除 loading、清 `mapResAsyncList`、播场景音乐 |
| `scene_view.luac proto[35]/[36]/[65]` | 维护 `mapResAsyncList`（异步加载列表） |
| `scene_view.luac proto[28]` | 检查 `isAddedAll` 后再置位 |

⇒ **`isLoadState=false` 表示"地图资源异步加载尚未完成"**，是**客户端内部**的加载门禁。

---

## 五、已排除的原因

| 候选 | 排除依据 |
|---|---|
| 我点错了屏幕坐标（没打到地图/摇杆） | 已绕过输入，直接调客户端自己的 `move()`，仍然不发包 |
| `10200.bid` 是非法地图 id | **`bid=10001` 是合法地图**：`assets/res/scene/10001/` 存在，含 **192 个文件** |
| 客户端在向我们下载地图资源但失败 | 实测 HTTP 日志里**没有任何** `/cdn/`、`/res/`、`.plist`、`.png` 请求；只有每 60s 一次的服务器列表 POST |

---

## 六、尚未确认 / 下一步

1. **为什么地图资源异步加载不完成**——需要盯 `mapResAsyncList`
   （`scene_view proto[35]/[36]`）到底在等什么资源。
2. **logcat 里出现了可疑迹象**：场景阶段加载了
   `src/common/error_msg.luac` 与 `src/game/battle/battle_fail.luac`，
   说明走到过**错误显示路径**。建议顺着这两个文件往上找触发者。
3. 可考虑的可控实验：在探针里直接 `setLoadState__(true)` 后再调 `move()`，
   用来**区分**"是移动协议/服务端的问题"还是"纯粹被加载门禁挡住"。
   （这只是诊断实验，不是修复。）

---

## 七、测试项状态

| 测试项 | 状态 |
|---|---|
| A 向上 / B 向下 / C 向左 / D 向右 | ⬜ 未通过（`move()` 空转） |
| E 连续移动 / F 停止移动 | ⬜ 未实测 |
| 客户端发出 `CS_10204` | ✅ **已实测到** |
| 服务端收到并落盘 | ✅ **已实测**（state 文件 `saved_at` 更新） |
| 服务端记录 x/y | ✅ 已写入 `role_1001.json` |
| 不闪退 | ✅ 进程稳定、无 FATAL |

**不得写成"角色可以移动已完成"。**
