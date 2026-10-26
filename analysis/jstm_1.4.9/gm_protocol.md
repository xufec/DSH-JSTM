# GM 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（20 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 14000 | CS+SC | ❌ | ✅ |  | CS flag:uint8 ／ SC flag:uint8; select_type:uint8; info_list:table |
| 14001 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ SC tips:uint16; msg:string; flag:uint8; pos_info:table |
| 14002 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ SC tips:uint16; msg:string; flag:uint8; pos_info:table |
| 14003 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8 ／ SC tips:uint16; msg:string; flag:uint8; s_type:uint8 |
| 14004 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC tips:uint16; msg:string; type:uint8; f_lev:uint8 |
| 14005 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8 ／ SC tips:uint16; msg:string; flag:uint8; type:uint8; f_lev:uint8; hero_pos_info:table; member_pos_info:table |
| 14006 | CS+SC | ❌ |  |  | CS flag:uint8; hero_bid:uint32; pos:uint8 ／ SC tips:uint16; msg:string; flag:uint8; cheer_hero:table |
| 14007 | CS+SC | ❌ |  |  | CS flag:uint8; hero_bid:uint32 ／ SC flag:uint8; cheer_hero:table |
| 14008 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8; hero_bid:uint32 ／ SC tips:uint16; msg:string; flag:uint8; pos_info:table |
| 14009 | CS+SC | ✅ | ✅ | ✅ | CS flag:uint8 ／ SC flag:uint8; cheer_hero:table |
| 14020 | CS+SC | ❌ |  |  | CS flag:uint8 ／ SC flag:uint8; select_type:uint8; info_list:table |
| 14021 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ SC tips:uint16; msg:string; flag:uint8; pos_info:table |
| 14022 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ SC tips:uint16; msg:string; flag:uint8; pos_info:table |
| 14023 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8 ／ SC tips:uint16; msg:string; flag:uint8; s_type:uint8 |
| 14028 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8; hero_bid:uint32 ／ SC tips:uint16; msg:string; flag:uint8; pos_info:table |
| 14099 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC attr_list:table |
| 14100 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC days:uint8; is_get:uint8; vip_lev:uint8 |
| 14101 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC tips:uint16; msg:string; days:uint8; assets:table; items:table |
| 14600 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC days:uint16; get_day:table |
| 14601 | CS+SC | ✅ |  |  | CS days:uint8 ／ SC tips:uint16; msg:string; days:uint8 |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
