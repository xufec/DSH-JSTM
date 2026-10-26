# 副本 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（137 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 13300 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC friend_list:table |
| 13301 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string |
| 13302 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string |
| 13303 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC code:uint8; msg:string |
| 13304 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; name:string; sex:uint8; lev:uint8 |
| 13305 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; agreed:uint8 ／ SC rid:uint32; srv_id:string; code:uint8; msg:string |
| 13306 | CS+SC | ❌ |  |  | CS role_list:table ／ SC code:uint8; string:string |
| 13307 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; code:uint8; msg:string |
| 13308 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string |
| 13309 | CS+SC | ❌ |  |  | CS del_list:table ／ SC del_list2:table |
| 13310 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; code:uint8; string:string |
| 13311 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC all_give_times:uint8; all_award_times:uint8; give_times:uint8; award_times:uint8; give_list:table; be_give_list:table |
| 13312 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; name:string; spirit:uint8 |
| 13313 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; code:uint8; string:string |
| 13314 | CS+SC | ❌ |  |  | CS name:string ／ SC role_list:table |
| 13315 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; send_list:table ／ SC code:uint8; string:string |
| 13316 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC group_list:table |
| 13317 | CS+SC | ❌ |  |  | CS group_name:string ／ SC code:uint8; string:string |
| 13318 | CS+SC | ❌ |  |  | CS group_id:uint32 ／ SC code:uint8; string:string |
| 13319 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; old_group_id:uint32; new_group_id:uint32 ／ SC code:uint8; string:string |
| 13320 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC recommend_list:table |
| 13321 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC request_list:table |
| 13322 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC add_list:table |
| 13323 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; string:string |
| 13324 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; bid:uint32; num:uint32; auto_buy:uint8; msg:string ／ SC code:uint8; string:string; bid:uint32; num:uint32 |
| 13325 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; give_times:uint32; all_times:uint32 |
| 13326 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; name:string; career:uint16; is_online:uint8; courage:uint32; charm:uint32; send_num:uint32; send_list:table |
| 13328 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; name:string; career:uint16; b_rid:uint32; b_srv_id:string; b_name:string; b_career:uint16; item_bid:uint32 |
| 13331 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC courage:uint32; charm:uint32; courage_rank:uint8; charm_rank:uint8 |
| 13336 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; intimacy:uint32 |
| 13340 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC name:string; lev:uint8; career:uint8; sex:uint8; sign:string; guild_name:string; title:string; spouse_name:string; per_name:string; zone:string; city:string; gift_num:uint16; nice_nu |
| 13341 | CS+SC | ❌ |  |  | CS ord:uint8; max_len:uint8 ／ SC ord:uint8; max_len:uint8; msg_list:table |
| 13342 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; ord:uint8; max_len:uint8 ／ SC code:uint8; msg:string; ord:uint8; max_len:uint8; msg_list:table |
| 13343 | CS+SC | ❌ |  |  | CS content:string; friend_list:table ／ SC code:uint8; msg:string |
| 13344 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; index:uint32; type:uint8; to_rid:uint32; to_srv_id:string; to_name:string; comment:string ／ SC code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; comment_nu |
| 13345 | CS+SC | ❌ |  |  | CS index:uint32; srv_id:string ／ SC code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32 |
| 13346 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; index:uint32; say_rid:uint32; say_srv_id:string; say_ctime:uint32 ／ SC code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; say_rid:uint32; say_srv_id:string; |
| 13347 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; index:uint32 ／ SC code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; nice_num:uint8; nice_list:table |
| 13348 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; index:uint32 ／ SC code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; nice_num:uint8; nice_list:table |
| 13349 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC code:uint8; msg:string; name:string; lev:uint8; career:uint8; sex:uint8; sign:string; guild_name:string; title:string; spouse_name:string; per_name:string; zone:strin |
| 13350 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC code:uint8; msg:string; rid:uint32; srv_id:string; nice_num:uint32; gift_num:uint16 |
| 13351 | CS+SC | ❌ |  |  | CS num:uint16 ／ SC code:uint8; msg:string; gift_num:uint16 |
| 13352 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC role_list:table |
| 13353 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC role_list:table |
| 13354 | CS+SC | ❌ |  |  | CS type:uint8; ord:uint8; max_len:uint8 ／ SC type:uint8; ord:uint8; max_len:uint8; role_list:table |
| 13355 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; msg_list:table |
| 13356 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; index:uint32; msg_rid:uint32; msg_srv_id:string; ctime:uint32 ／ SC code:uint8; msg:string; msg_list:table |
| 13357 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13358 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; partner_id:uint32 ／ SC code:uint8; msg:string |
| 13359 | CS+SC | ❌ |  |  | CS content:string ／ SC code:uint8; msg:string; content:string |
| 13360 | CS+SC | ❌ |  |  | CS town:string; city:string ／ SC code:uint8; msg:string; town:string; city:string |
| 13361 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC zone_list:table; head_list:table |
| 13362 | CS+SC | ❌ |  |  | CS bid:uint16 ／ SC code:uint8; msg:string; bid:uint16 |
| 13363 | CS+SC | ❌ |  |  | CS type:uint8; bid:uint16 ／ SC code:uint8; msg:string; type:uint8; bid:uint16 |
| 13364 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC use_badge_list:table |
| 13365 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC act_badge_list:table |
| 13366 | CS+SC | ❌ |  |  | CS bid_list:table ／ SC code:uint8; msg:string; bid_list:table |
| 13367 | CS+SC | ❌ |  |  | CS type:uint8; index:uint32; rid:uint32; srv_id:string; name:string; reason:string; desc:string; content:string ／ SC code:uint8; msg:string; rid:uint32; srv_id:string |
| 13368 | CS+SC | ❌ |  |  | CS channel:uint16; len:uint8; msg:string ／ SC code:uint8; msg:string |
| 13369 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC black_list:table |
| 13370 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; op_type:uint8 ／ SC code:uint32; msg:string; rid:uint32; srv_id:string; op_type:uint8 |
| 13371 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC add_list:table |
| 13500 | CS+SC | ❌ |  |  | CS guild_name:string ／ SC code:uint8; msg:string |
| 13501 | CS+SC | ❌ |  |  | CS page:uint8; args:table; flag:uint8; num:uint8 ／ SC page:uint8; page_total:uint8; guilds:table; all_count:uint32 |
| 13502 | CS+SC | ❌ |  |  | CS gid:uint32; srv_id:string ／ SC index:uint8; gid:uint32; srv_id:string; realm:uint8; vip:uint8; guild_name:string; head_name:string; head_career:uint8; lev:uint8; role_count:uint16; max_role_count:u |
| 13503 | CS+SC | ❌ |  |  | CS gid:uint32; srv_id:string ／ SC code:uint8; msg:string |
| 13504 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC rid:uint32; srv_id:string; name:string; all_request:uint8 |
| 13505 | CS+SC | ❌ |  |  | CS type:uint8; rid:uint32; srv_id:string; name:string ／ SC type:uint8; rid:uint32; srv_id:string; code:uint8; msg:string |
| 13506 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC type:uint8 |
| 13507 | CS+SC | ❌ |  |  | CS page:uint32; num:uint8 ／ SC page:uint8; page_total:uint8; guids:table |
| 13508 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; role_name:string ／ SC code:uint8; msg:string |
| 13509 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC （无字段/空消息） |
| 13510 | CS+SC | ❌ |  |  | CS type:uint8; gid:uint32; gsrv_id:string ／ SC type:uint8; gid:uint32; gsrv_id:string; code:uint8; msg:string |
| 13511 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC gid:uint32; gsrv_id:string; gname:string; rname:string |
| 13512 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC （无字段/空消息） |
| 13513 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; name:string ／ SC rid:uint32; srv_id:string; code:uint8; msg:string |
| 13514 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13515 | CS+SC | ❌ |  |  | CS modify:table ／ SC code:uint8; msg:string |
| 13516 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13517 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; name:string ／ SC code:uint8; msg:string |
| 13518 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC guild_name:string; lev:uint8; role_count:uint16; max_role_count:uint16; stu_count:uint16; max_stu_count:uint16; aim:string; sign:string; qq:string; yy:string; head_name:string; maint |
| 13519 | CS+SC | ❌ |  |  | CS gid:uint32; gsrv_id:string ／ SC guid_roles:table |
| 13520 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; name:string; position:uint8; old_position:uint8 ／ SC rid:uint32; srv_id:string; position:uint8; code:uint8; msg:string |
| 13521 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC position1:uint8; now_position1:uint8; position2:uint8; now_position2:uint8; position3:uint8; now_position3:uint8; position4:uint8; now_position4:uint8; position5:uint8; now_position5 |
| 13522 | CS+SC | ❌ |  |  | CS gid:uint32; gsrv_id:string ／ SC gid:uint32; gsrv_id:string; code:uint8; msg:string |
| 13523 | CS+SC | ❌ |  |  | CS build_id:uint32; build_lev:uint32 ／ SC build_id:uint32; new_build_lev:uint32; up_status:uint32; up_time:uint32; speed_time:uint32; code:uint8; msg:string |
| 13524 | CS+SC | ❌ |  |  | CS gid:uint32; gsrv_id:string ／ SC guilds:table |
| 13525 | CS+SC | ❌ |  |  | CS good_bid:uint32; good_num:string ／ SC good_bid:uint32; buy_num:string; all_num:string; code:uint8; msg:string |
| 13526 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC guild_shop:table |
| 13527 | CS+SC | ❌ |  |  | CS type:uint32 ／ SC code:uint8; msg:string |
| 13528 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13529 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC status:uint8 |
| 13530 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC guild_shop:table |
| 13531 | CS+SC | ❌ |  |  | CS id:uint32; srv_id:string; good_bid:uint32; num:string ／ SC good_bid:uint32; num:string; code:uint8; msg:string |
| 13532 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; name:string; old_position:uint8 ／ SC code:uint8; msg:string |
| 13533 | CS+SC | ❌ |  |  | CS build_id:uint32; build_lev:uint32 ／ SC build_id:uint32; build_lev:uint32; up_status:uint32; up_time:uint32; speed_time:uint32; code:uint8; msg:string |
| 13534 | CS+SC | ❌ |  |  | CS build_id:uint32; speed_id:uint32 ／ SC build_id:uint32; speed_time:uint32; code:uint8; msg:string |
| 13535 | CS+SC | ❌ |  |  | CS mem_lev:uint32 ／ SC mem_lev:uint32; code:uint8; msg:string |
| 13536 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string |
| 13537 | CS+SC | ❌ |  |  | CS item_bid:uint32 ／ SC code:uint8; msg:string |
| 13538 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC guild_assets:table |
| 13539 | CS+SC | ❌ |  |  | CS guild_name:string ／ SC guilds:table |
| 13540 | CS+SC | ❌ |  |  | CS guild_list:table ／ SC guild_list:table; code:uint8; msg:string |
| 13541 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13542 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC type:uint8; guid_roles:table |
| 13543 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13546 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC gonggao_list:table |
| 13547 | CS+SC | ❌ |  |  | CS msg:string ／ SC code:uint8; msg:string |
| 13548 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC （无字段/空消息） |
| 13551 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC gift_num:uint32 |
| 13552 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC gift_num:uint32; id_list:table |
| 13553 | CS+SC | ❌ |  |  | CS id_list:table ／ SC code:uint8; msg:string; gift_num:uint32; id_list:table |
| 13556 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC contrib:uint32; gift_num:uint32; week_wage:uint32 |
| 13561 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC sign_list:table |
| 13562 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; sign:string ／ SC code:uint8; msg:string; rid:uint32; srv_id:string; sign:string |
| 13563 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC sign:string |
| 13564 | CS+SC | ❌ |  |  | CS id:uint16 ／ SC code:uint8; msg:string |
| 13565 | SC | ❌ |  |  | SC id:uint16; state:uint8; rid:uint32; srv_id:string; name:string; career:uint8; type:uint8; sex:uint8 |
| 13566 | CS+SC | ❌ |  |  | CS id:uint16 ／ SC code:uint8; msg:string; create_name:string; create_career:uint8; id:uint16; type:uint8; val:uint32; hongbao_get:uint16; hongbao_max:uint16; reward_get:uint32; reward_max:uint32; stop |
| 13567 | CS+SC | ❌ |  |  | CS id:uint16 ／ SC code:uint8; msg:string; id:uint16; val:uint32 |
| 13568 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string; type:uint8; val:uint16 |
| 13569 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC info:table |
| 13570 | CS+SC | ❌ |  |  | CS page:uint8; num:uint8 ／ SC page:uint8; page_total:uint8; role_list:table |
| 13571 | CS+SC | ❌ |  |  | CS partner_id:uint32 ／ SC code:uint8; msg:string |
| 13572 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; partner_id:uint32 ／ SC code:uint8; msg:string; partner_id:uint32 |
| 13573 | CS+SC | ❌ |  |  | CS partner_id:uint32 ／ SC code:uint8; msg:string; partner_id:uint32 |
| 13574 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; role_list:table |
| 13575 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; partner_list:table |
| 13576 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13577 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC page:uint8; page_total:uint8; role_list:table |
| 13578 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC act_list:table |
| 13579 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC tree_lev:uint8; strength_rest:uint32; strength_name:string; role_eff:uint32; role_delay:uint32; role_attrs:table; parter_eff:uint32; parter_delay:uint32; parter_attrs:table |
| 13580 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC worship_list:table |
| 13581 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string; new_type:uint8 |
| 13582 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string |
| 13583 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; strength_rest:uint32; strength_name:string |
| 13584 | CS+SC | ❌ |  |  | CS npc_x:int32; npc_y:int32 ／ SC code:uint8; msg:string |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
