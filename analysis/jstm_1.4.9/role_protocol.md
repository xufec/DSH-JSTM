# 角色/属性/等级 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（42 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 10101 | CS+SC | ✅ |  |  | CS sex:uint8; name:string; career:int16; playform:string ／ SC code:uint8; msg:string; rid:uint32; srv_id:string |
| 10102 | CS+SC | ✅ |  |  | CS rid:uint32; srv_id:string ／ SC code:uint8; msg:string; timestamp:uint32; world_lev:uint16 |
| 10103 | CS+SC | ✅ | ✅ | ✅ | CS rid:uint32; srv_id:string ／ SC code:uint8; msg:string; timestamp:uint32; world_lev:uint16 |
| 10110 | SC | ❌ |  |  | SC method:uint8; url:string; args:table |
| 10111 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC cli_ver:uint16; flag:uint16 |
| 10300 | CS | ✅ | ✅ |  | CS （无字段/空消息） |
| 10301 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; name:string; lev:uint16; is_vip:uint8; vip_lev:uint8; sex:uint8; career:uint16; face_id:uint16; cur_title:uint16; ntm_title:uint32; gid:uint32; gsrv_id:str |
| 10302 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC lev:uint16; exp:uint32; gold:uint32; gold_acc:uint32; coin:uint32; sinew:uint32; experience:uint32; coupon:uint32; vitality:uint32; guild_contrib:uint32; practice_exp:uint32; tower_c |
| 10303 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; name:string; lev:uint16; is_vip:uint8; vip_lev:uint8; sex:uint8; career:uint16; volume:uint8; store_volume:uint8; store_partner_volume:uint8; volume_open:u |
| 10304 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; name:string; lev:uint16; is_vip:uint8; vip_lev:uint8; sex:uint8; career:uint16; volume:uint8; store_volume:uint8; store_partner_volume:uint |
| 10305 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC assets:table |
| 10306 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC attr:table; mspd:uint16; power:uint32 |
| 10310 | SC | ❌ |  |  | SC is_show:uint8; msg:string |
| 10311 | CS+SC | ❌ |  |  | CS msg:string ／ SC code:uint8; msg:string |
| 10312 | CS | ❌ |  |  | CS （无字段/空消息） |
| 10320 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; times:uint8 |
| 10321 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC times:uint8 |
| 10322 | CS+SC | ❌ |  |  | CS Code:uint8 ／ SC Code1:uint8 |
| 10323 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC Code:uint8 |
| 10324 | CS+SC | ❌ |  |  | CS name:string; is_rename:uint8 ／ SC code:uint8; msg:string; name:string |
| 10325 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC face_list:table |
| 10326 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC face_list:table |
| 10327 | CS+SC | ❌ |  |  | CS face_id:uint16 ／ SC code:uint8; msg:string; face_id:uint16 |
| 10328 | CS+SC | ❌ |  |  | CS assets:table ／ SC code:uint8; msg:string; point:uint16 |
| 10331 | CS+SC | ✅ | ✅ | ✅ | CS skill_bid:uint32 ／ SC code:uint8; msg:string |
| 10332 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC skill_list:table |
| 10333 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10334 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC coin:uint32 |
| 10340 | CS+SC | ❌ |  |  | CS img:bool; size:uint32 ／ SC code:uint8; msg:string; img_id:uint32 |
| 10341 | CS+SC | ❌ | ✅ |  | CS id_list:table ／ SC rid:uint32; srv_id:string; id:uint32; img:bool; upload_time:uint32 |
| 10342 | SC | ❌ |  |  | SC profit_exp:uint32 |
| 10343 | CS+SC | ❌ |  |  | CS new_name:string; auto_buy:uint8 ／ SC code:uint8; msg:string |
| 10346 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; id:uint32 |
| 10347 | SC | ❌ |  |  | SC face_list:table |
| 10348 | CS+SC | ❌ |  |  | CS face_id:uint16 ／ SC code:uint8; face_id:uint16; msg:string |
| 10388 | CS+SC | ❌ |  |  | CS id_list:table ／ SC online_roles:table |
| 10389 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC photos:table |
| 10390 | CS+SC | ❌ |  |  | CS msg:string; len:uint32 ／ SC msg:string |
| 10391 | CS+SC | ❌ |  |  | CS msg:string ／ SC type:uint8; data:string |
| 10396 | SC | ❌ |  |  | SC （无字段/空消息） |
| 10397 | CS | ✅ |  |  | CS status:uint8 |
| 10399 | CS+SC | ❌ |  |  | CS msg:string ／ SC code:uint8; msg:string |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
