# 聊天 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（15 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 12201 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; minerals:table |
| 12202 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; coin:uint32 |
| 12203 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC type:uint8; status:uint8; item_id:uint32; total:uint32; speed:uint32; left_time:uint32; stronghold:table |
| 12204 | CS+SC | ❌ |  |  | CS id:uint32; s_id:uint8 ／ SC code:uint8; msg:string |
| 12205 | CS+SC | ❌ |  |  | CS id:uint32; s_id:uint8; flag:uint8; hero_list:table; g_flag:uint8; g_list:table ／ SC code:int8; msg:string |
| 12206 | CS+SC | ❌ |  |  | CS id:uint32; stronghold_id:uint8; hero_list:table ／ SC code:uint8; msg:string; total:uint32; speed:uint32 |
| 12207 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC id:uint32 |
| 12208 | CS+SC | ❌ |  |  | CS id:uint32; stronghold_id:uint8 ／ SC code:uint8; msg:string; s_id:uint8; rid:uint32; srv_id:string; name:string; face_id:uint16; mon_list:table; hero_list:table |
| 12209 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC id:uint32 |
| 12210 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; msg:string; type:uint8; lev:uint8; item_id:uint32; total:uint32 |
| 12211 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC minerals:table |
| 12212 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC id:uint32 |
| 12213 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC type:uint8; lev:uint8; item_id:uint32; total:uint32 |
| 12214 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC hero_list:table |
| 12215 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC id:uint32 |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
