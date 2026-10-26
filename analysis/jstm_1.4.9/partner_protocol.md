# 伙伴 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（28 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 10401 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC hero_bag:table; hero_chip:table |
| 10402 | CS+SC | ✅ | ✅ | ✅ | CS hero_bid:uint32 ／ SC bid:uint16; lev:uint8; color:uint8; exp:uint32 |
| 10403 | CS+SC | ✅ | ✅ | ✅ | CS hero_bid:uint32 ／ SC bid:uint16; attr:table |
| 10404 | CS+SC | ✅ | ✅ | ✅ | CS hero_bid:uint32 ／ SC bid:uint16; lev:uint8; exp:uint32; color:uint8 |
| 10405 | CS+SC | ❌ |  |  | CS hero_bid:uint32 ／ SC code:uint8; msg:string; hero_bid:uint32; color:uint8; chip:uint16; skills:table |
| 10406 | CS+SC | ❌ |  |  | CS hero_bid:uint32 ／ SC hero_bid:uint32; code:uint8; msg:string |
| 10407 | CS+SC | ❌ |  |  | CS args:table ／ SC hero_error:table |
| 10408 | SC | ❌ |  |  | SC hero_chips:table |
| 10409 | CS+SC | ❌ |  |  | CS hero_bid:uint32 ／ SC hero_bid:uint32; exp:uint32 |
| 10410 | CS+SC | ❌ |  |  | CS hero_bid:uint32 ／ SC code:uint8; msg:string |
| 10411 | CS+SC | ❌ |  |  | CS hero_bid:uint32 ／ SC bid:uint16; skills:table |
| 10412 | SC | ❌ |  |  | SC hero_bid:uint32; state:uint8 |
| 10413 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC hero_states:table |
| 10414 | SC | ❌ |  |  | SC lev:uint8 |
| 10421 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC max_point:uint8; cur_point:uint8; sec:uint16 |
| 10422 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC count:uint8; gold:uint16; add_point:uint16 |
| 10423 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; cur_point:uint16 |
| 10424 | CS+SC | ❌ |  |  | CS bid:uint32; skill_bid:uint32 ／ SC code:uint8; msg:string; bid:uint32; skill_bid:uint32; new_skill_bid:uint32 |
| 11600 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC color:uint8; wing_id:uint32; power:uint32; wing_skill:table; add_attr:table; star:uint16; lingxi_num:uint32; jiewing_id:uint32; surface_list:table |
| 11601 | CS+SC | ❌ |  |  | CS is_buy:uint8 ／ SC code:uint8; msg:string; wing_id:uint32; star:uint8; power:uint32 |
| 11602 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; wing_id:uint32; skill_bid:uint32; add_attr:table; power:uint32 |
| 11603 | CS+SC | ❌ |  |  | CS is_buy:uint8 ／ SC code:uint8; msg:string; color:uint8; star:uint16; wing_id:uint32; wing_skill:table; power:uint32 |
| 11604 | CS+SC | ❌ |  |  | CS item_bid:uint32 ／ SC code:uint8; msg:string |
| 11605 | CS+SC | ❌ |  |  | CS item_bid:uint32 ／ SC code:uint8; msg:string |
| 11606 | CS+SC | ❌ |  |  | CS surface_id:uint16 ／ SC code:uint8; msg:string; animate:uint16 |
| 11607 | CS+SC | ❌ |  |  | CS surface_id:uint16 ／ SC code:uint8; msg:string; surface_id:uint16 |
| 11698 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC wing_id:uint32; star:uint8; power:uint32 |
| 11699 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; wing_id:uint32; star:uint8; power:uint32 |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
