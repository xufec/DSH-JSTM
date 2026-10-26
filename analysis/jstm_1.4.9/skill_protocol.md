# 技能 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（23 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 11400 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11401 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11402 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC pos_list:table |
| 11403 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC role_list:table |
| 11404 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string; type:uint8; tr_rid:uint32; tr_srv_id:string |
| 11405 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC leave_list:table |
| 11406 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC leave_list:table |
| 11407 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; name:string; power:uint32 |
| 11408 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC kill_num:uint8; cent:uint16; room_id:uint8; x_realm:uint16; m_realm:uint16; role_list:table |
| 11409 | SC | ❌ |  |  | SC kill_num:uint8; cent:uint16; realm_win:uint8; role_list:table |
| 11410 | CS+SC | ❌ |  |  | CS sm_lev:uint8; room_id:uint8 ／ SC sm_lev:uint8; room_id:uint8; win_realm:uint8; role_list:table |
| 11411 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC sm_lev:uint8; room_id:uint8; win_realm:uint8; role_list:table; rank:table |
| 11412 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC pos:uint8; realm:uint8; state:uint8; skill_list:table |
| 11413 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; skii_type:uint8 |
| 11414 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC assets_list:table |
| 11500 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC lingqi:uint32; garden_work:table |
| 11501 | CS+SC | ❌ |  |  | CS type:uint8; partner_id:uint32 ／ SC code:uint8; msg:string; type:uint8; partner_id:uint32; state:uint8; time_out:uint32; val:uint32 |
| 11502 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string; type:uint8; volume:uint8 |
| 11503 | CS+SC | ❌ |  |  | CS type:uint8; partner_id:uint32 ／ SC code:uint8; msg:string; type:uint8; partner_id:uint32 |
| 11504 | SC | ❌ |  |  | SC type:uint8; partner_id:uint32; state:uint8; time_out:uint32 |
| 11505 | SC | ❌ |  |  | SC lingqi:uint32 |
| 11506 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; garden_partner:table |
| 11507 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
