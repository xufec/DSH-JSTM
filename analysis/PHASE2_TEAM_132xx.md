# PHASE 2 —— 组队（132xx）真实实现

> 目标：把"客户端有入口、服务端仅回执"的 **组队** 打通为**可持久化**的垂直闭环。
> 纪律：字段以 `protocol/fields.json` 为准（CONFIRMED）；表结构无原版证据 ⇒ 标 INFERENCE；
> 不改动任何既有系统；新专用分支必须可执行（无分发遮蔽）。

## 一、改动清单（server/mock_server.py）

| 位置 | 改动 |
|---|---|
| `db_guild_create` 之后 | 新增组队持久层：`db_team_init / _team_members / _team_row / db_team_get / db_team_of / db_team_save / db_team_delete / db_team_create / db_team_leave / db_team_disband / db_team_hall` |
| `_reply` 内（16xxx 收尾之后、R189 之前） | 新增专用分支 `if cmd in (13200,13201,13210,13218,13226,13237)` |
| R191 集合 | 移出 `13200` `13201`（否则遮蔽新专用实现） |
| R189 集合 | 移出 `13218` |
| `{tips,msg}` 集合 | 移出 `13210` `13226` |
| R182 族集合 | 移出 `13237` |

**新增数据表**：`role_team(team_id PK, leader_rid, leader_srv, members TEXT(json), ctime)`
（表结构 = **兼容层，INFERENCE**；原版队伍表结构在 APK 中不可取证。）

## 二、协议实现（字段来自 `cmd_resolve_132.luac`）

| cmd | 方向 | 语义 | SC 字段 | 行为 |
|---|---|---|---|---|
| 13201 | C→S | 创建队伍 | `{tips:u16,msg}` | 落库建队；已在队 ⇒ `tips=0` |
| 13200 | C→S | 队伍信息 | `{msg,team_id,team_srv_id,leader_id,leader_srv_id,leader_speed,team_member_list}` | 读 `role_team`，逐成员 11 字段 |
| 13210 | C→S | 退出队伍 | `{tips:u16,msg}` | 队长离队⇒移交；最后一人⇒解散 |
| 13226 | C→S | 解散队伍 | `{tips:u16,msg}` | 仅队长；非队长 ⇒ `tips=0` |
| 13218 | C→S | 组队大厅 | `{team_list:table}` | 列全部队伍，10 字段/条 |
| 13237 | C→S | 查看他人队伍 | `{team_id,team_srv_id,num,gid,gsrv,gname}` | 按目标 rid 查；无 ⇒ tid=0 |

## 三、验证（可复跑）

```
# 起测试实例（避开在线的 8080/9000）
python server/mock_server.py --http 8191 --game 9191
python tools/test_team.py --port 9191
```

**结果：`ALL PASS`（16 项检查）**。要点：
- `13200` 返回**真实角色数据**：`name='DSH' lev=70 career=1 power=133960`（取自现有 role/attr/power 服务）。
- 建队 → 查队 → 大厅 → 解散 → 空队 → 再建 → 离队 → 解散，全链一致。
- 跑完 `role_team` 行数 = **0**（无残留）。

**门禁**：`python tools/lint_dispatch_shadow.py` → `✓ 无分发遮蔽`（专用分支 1430 / 默认集合 0 / 未开放集合 0）。
**编译**：`python -m py_compile server/mock_server.py` → OK。
**核心回归**：1199/10300/10301/10302/12400 在测试实例上均有正确应答（含 10200/10201 主动推送）。

## 四、未做 / 边界（诚实）

| 项 | 状态 |
|---|---|
| 多人（>1 角色）同队 | **未验证**：本服 `TcpHandler.cfg` 默认全连接共享，多角色需先解会话隔离 |
| 13202/13203/13204/13205（邀请/申请/应答） | 仍为通用回执（未落库） |
| 13219/13223/13224/13250（招募/快速组队/阵法） | 仍为通用回执 |
| 队伍广播（组队后通知在线队员） | 未实现（依赖在线会话表） |

## 五、下一步（优先级顺序）

组队已为 **结拜（19505 队长发起）** 与 **结婚（18501 队长邀请配偶进队）** 铺好底座。
下一项：**结拜 195xx** → **结婚 183xx** → 时装 10573-10578 → 光环 19100/19103 → 拍卖 18020/18021。

[PHASE 2 组队完成]