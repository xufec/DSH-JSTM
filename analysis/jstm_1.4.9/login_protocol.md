# 登录/账号 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（42 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 1100 | CS | ❌ |  |  | CS ticket:string; account:string |
| 1101 | SC | ❌ |  |  | SC code:uint8 |
| 1110 | CS+SC | ✅ | ✅ | ✅ | CS args:table ／ SC code:uint8; msg:string; roles:table; least_career:uint8 |
| 1199 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC time:uint32 |
| 1200 | CS | ❌ |  |  | CS len:uint16 |
| 1201 | CS+SC | ❌ |  |  | CS time:l; id:uint32; msg:string ／ SC time:l; id:uint32; msg:string |
| 10001 | CS | ✅ | ✅ |  | CS key:string |
| 10200 | CS+SC | ✅ |  | ✅ | CS bid:uint32 ／ SC code:uint8; msg:string; bid:uint32; line_id:uint8; x:uint16; y:uint16; dir:uint8 |
| 10201 | CS+SC | ✅ |  | ✅ | CS （无字段/空消息） ／ SC roles:table; npcs:table; mons:table; elems:table |
| 10202 | SC | ❌ |  |  | SC roles:table |
| 10203 | SC | ❌ |  |  | SC role_ids:table; bid:uint32 |
| 10204 | CS+SC | ✅ | ✅ | ✅ | CS x:uint16; y:uint16 ／ SC rid:uint32; srv_id:string; x:uint16; y:uint16 |
| 10205 | CS+SC | ✅ |  |  | CS x:uint16; y:uint16 ／ SC rid:uint32; srv_id:string; x:uint16; y:uint16 |
| 10206 | CS+SC | ❌ |  |  | CS x:uint32 ／ SC code:uint8; msg:string |
| 10207 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10208 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; change_list:table |
| 10209 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; change_list:table |
| 10210 | CS+SC | ❌ |  |  | CS line_id:uint8 ／ SC code:uint8 |
| 10211 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC all_line_status:table |
| 10212 | SC | ❌ |  |  | SC id:uint32; bid:uint32; type:uint8; name:string; realm:uint8; mspd:uint16; x:uint16; y:uint16; dir:uint8; res_id:string; status:uint8; enter_effect:uint8 |
| 10213 | SC | ❌ |  |  | SC id:uint32; x:uint16; y:uint16 |
| 10214 | SC | ❌ |  |  | SC id:uint32; status:uint8 |
| 10215 | SC | ❌ |  |  | SC id:uint32 |
| 10216 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; msg:string; id:uint32 |
| 10217 | SC | ❌ |  |  | SC id:uint32; bid:uint32; type:uint8; sub_type:uint8; name:string; x:uint16; y:uint16; res_id:string |
| 10218 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; role_attrs:table |
| 10219 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; misc_uint8:table; misc_uint16:table; misc_uint32:table; misc_str:table |
| 10220 | SC | ❌ |  |  | SC mon_ids:table; role_ids:table |
| 10221 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC mons:table |
| 10222 | CS+SC | ❌ |  |  | CS map_bid:uint32; x:uint32; y:uint32 ／ SC code:uint8; msg:string |
| 10223 | SC | ❌ |  |  | SC dynamic_block:table |
| 10224 | SC | ❌ |  |  | SC id:uint32; srv_id:string; type:uint8; val:int32 |
| 10230 | SC | ❌ |  |  | SC id:uint32; bid:uint32; type:uint8; x:uint16; y:uint16; name:string; misc:table; animate_res:table; member:table |
| 10231 | SC | ❌ |  |  | SC id:uint32 |
| 10232 | CS+SC | ❌ |  |  | CS npc_id:uint32; id:uint32 ／ SC code:uint8; msg:string |
| 10233 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; msg:string; id:uint32; time:uint32 |
| 10239 | SC | ❌ |  |  | SC id:uint32; bid:uint32; type:uint8; x:uint16; y:uint16; name:string; misc:table; animate_res:table; member:table |
| 10250 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; animate_res_replace:table; animate_res_del:table |
| 10295 | SC | ❌ |  |  | SC key:string; str_val:string; int_val:int32 |
| 10296 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; status:uint8 |
| 10297 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC status:uint8 |
| 10299 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; args:table ／ SC args:table |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
