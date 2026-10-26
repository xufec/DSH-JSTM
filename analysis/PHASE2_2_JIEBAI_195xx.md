# PHASE 2.2 —— 结拜 / 金兰（195xx）真实实现

> 目标：把"客户端有入口、服务端仅默认生成/回执"的 **结拜** 打通为**可持久化**垂直闭环。
> 纪律同 PHASE2：字段以 `protocol/fields.json` 为准（CONFIRMED）；表结构无原版证据 ⇒ INFERENCE；不改既有系统；新专用分支必须可执行。

## 一、改动清单（server/mock_server.py）

| 位置 | 改动 |
|---|---|
| `db_team_hall` 之后 | 新增持久层：`db_jiebai_init / _jb_row / db_jiebai_of / db_jiebai_get / db_jiebai_save / db_jiebai_delete / db_jiebai_create / db_jiebai_cancel` |
| `_reply` 内（组队块之后） | 新增专用分支 `if cmd in (19505,19514,19530,19533,19536)` |
| R187 集合（`20xxx`+`19xxx`） | 移出 `19514` `19530` `19536`（否则遮蔽新专用实现） |
| R181-D 回执族集合 | 移出 `19505` `19533` |

**新表**：`role_jiebai(jid PK, leader_rid, front_name, end_name, lev, exp, notice, members TEXT(json), ctime)`（兼容层，INFERENCE）。

## 二、协议实现

| cmd | 语义 | SC | 行为 |
|---|---|---|---|
| 19505 | 发起结拜 | `{code,msg}` | 落库建结拜（单人）；已在 ⇒ `code=0` |
| 19514 | 打开结拜空间 | `{jid,j_srv_id,front_name,member_len,end_name,lev,leader_name,exp,common_notice,member_list,vote_type,...}` | 读 `role_jiebai`；**⚠ 无 code/msg** |
| 19530 | 成员列表 | `{member_list,end_time}` | 逐成员 9 字段；**⚠ 无 code/msg** |
| 19536 | 提升结拜空间等级 | `{code,msg,jlev}` | `lev += 1` 并落盘 |
| 19533 | 取消结拜 | `{code,msg}` | 删行 |

## 三、验证（可复跑）

```
python server/mock_server.py --http 8191 --game 9191
python tools/test_jiebai.py --port 9191      →  ALL PASS（11 项）
python tools/test_team.py   --port 9191      →  ALL PASS（16 项，回归）
```

要点：
- `19514` 返回**真实角色数据**：`leader='DSH' front='金兰' end='之谊'`；成员名 `DSH`（取自现有 role 服务）。
- 发起 → 空间（jid=2001，1 成员）→ 成员列表（1）→ 升级（jlev=2）→ 取消 → jid=0，全链一致。
- 跑完 `role_jiebai` 行数 = **0**。

**门禁**：`lint_dispatch_shadow.py` → `✓ 无分发遮蔽`（1430/0/0）。`py_compile` OK。

## 四、未做（诚实）

| 项 | 状态 |
|---|---|
| 19507/19509/19523/19527/19528 称号·绰号·宣言 | 仍通用回执（未落库；`role_jiebai` 已有 front_name/end_name/notice 字段，下一步接上即可） |
| 19511/19512/19515/19516 确认/技能 | 仍通用回执 |
| 19519-19522 投票 | 仍通用回执 |
| 19524 邀请好友加入 | 依赖好友系统 |
| 多人结拜（>1 成员） | 未验证：需先做会话隔离（所有连接默认同 rid） |

## 五、下一步

**结婚 183xx**（SC 规格已取证，见 `analysis/_jiebai_probe.txt` 附录）→ 时装 10573-10578 → 光环 19100/19103 → 拍卖 18020/18021。

[PHASE 2.2 结拜完成]