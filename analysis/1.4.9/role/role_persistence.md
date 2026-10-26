# 1.4.9 角色状态持久化

> ## 🔴 **已过期（R7 标注，2026-09-18）** —— 请以 `server/state/roles.db` 为准
>
> 本文描述的是 **Phase 4E 之前**的"JSON 落盘"状态。**Phase 4E 起数据库已为权威**：
> `server/mock_server.py` 的 `save_role_pos()` docstring 原文即
> 「把坐标写进 **数据库**（**Phase 4E 起以 DB 为准**）。仍保留 `role_<rid>.json` 作为**可读快照**，便于人工核对。」
>
> **实测现状（`server/mock_server.py`）**：SQLite `server/state/roles.db` **11 张表 / 98 列**，其中
> **`roles` 表 23 列**已包含本文 §三 中标为 ⬜ 的绝大多数字段：
> `uid` / `name` / `level` / `career` / `sex` / `exp` / `hp` / `max_hp` / `mp` / `max_mp` / `scene_id` / `x` / `y` / `dir` / `gold` / `gold_acc` / `diamond` / `coin` / `vip_level` / `title` / `status` / `updated_at`。
> ⇒ 本文 §三「当前只落地了 rid + x + y」与 §四 的三条 ⬜ 验证项**均已不再成立**。
>
> **保留本文的价值**：其"设计意图"（§二：客户端移动 → 落盘 → 重登回原位，**不改客户端协议**）与
> "最低保存字段清单"（§三）仍是有效的设计讨论记录。**但不要再引用它的完成度结论。**
> 详见 `analysis/server_reference/comparison/role_matrix.md` §2.3 与 `README.md` §6.1 更正 17。

> 状态（**本文原述，已过期**）：**服务端已实现，端到端未实测**（因为"角色移动"未验证，没有坐标变化可存）。

---

## 一、实现方式（刻意保持最简）

按项目要求"不要一开始使用复杂数据库"，先用 **JSON 落盘**：

```
server/state/role_<rid>.json
{
  "rid": 1001,
  "x": <最后移动到的 x>,
  "y": <最后移动到的 y>,
  "saved_at": <unix 秒>
}
```

代码（`server/mock_server.py`）：

| 函数 | 作用 |
|---|---|
| `load_role_state(rid)` | 读 `server/state/role_<rid>.json`，不存在返回 nil |
| `save_role_pos(rid, x, y)` | 收到移动包时更新坐标并落盘（保留其它字段） |
| `role_with_saved_pos(cfg)` | 把配置角色 + 已持久化坐标合并，供 `10200`/`10201` 下发 |

触发时机：`CS_10204` / `CS_10205`（角色移动/瞬移）。
下发时机：`_send_10200()`（进场景通知）与 `10201` 应答，都走 `role_with_saved_pos()`。

---

## 二、设计意图

```
客户端移动 → CS_10204{x,y} → 服务端 save_role_pos() 落盘
                                   ↓
重新登录 → 10103 角色重连 → 服务端推 SCRoleEnter_10200
                                   ↓
                          x,y 取自 role_with_saved_pos()  ← 回到原位
```

这样"重登回到原位"不需要改任何客户端协议，只靠服务端记住坐标。

---

## 三、最低保存字段（对照项目要求）

要求保存：`uid rid name level career scene_id x y dir hp mp`

| 字段 | 当前状态 |
|---|---|
| `rid` | ✅ 已存 |
| `x` / `y` | ✅ 已存（移动包触发） |
| `name` / `level`(lev) / `career` | ⬜ 仍在 `server/config.json` 的静态配置里，未随角色状态落盘 |
| `scene_id` | ⬜ 未存（当前场景固定为 `bid=1`） |
| `dir` | ⬜ 协议里没有 dir（`CS_10204` 只有 x/y），客户端自行推导朝向 |
| `hp` / `mp` | ⬜ 未存；`SC_10301` 里也没有直接给 hp/mp（走 10302/10306 等资产/属性消息） |
| `uid` | ⬜ 未存（当前帐号固定 `dsh_local`） |

⇒ 当前只落地了 **rid + x + y**。其余字段需要先确认它们在
`10301`/`10302`/`10306` 等消息里的确切位置，再补进 JSON。

---

## 四、未完成的验证（不得写成已完成）

| 验证项 | 状态 | 怎么验 |
|---|---|---|
| 移动后落盘 | ⬜ | 需要先让客户端真的发出 `CS_10204`（见 `movement_test.md`） |
| 退出→重登→坐标恢复 | ⬜ | 上一步通了之后：移动→杀进程→重登→看 `10200` 的 x,y 是否等于退出前 |
| 服务器重启后角色仍在 | ⬜ | 重启 `mock_server.py`，再重登，看 `role_<rid>.json` 是否被读回 |

**一个可以直接做的静态验证**（不需要客户端移动）：
手工往 `server/state/role_1001.json` 写一个坐标（例如 x=777,y=888），
然后启动 APK 进图，看 `_send_10200` 的日志里坐标是否变成 `(777,888)`。
这条能**独立证明"落盘 → 重登读回"这一半是通的**，建议下一步先做它。
