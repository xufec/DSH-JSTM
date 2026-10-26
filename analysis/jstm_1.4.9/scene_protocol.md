# 场景/地图/NPC 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（82 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 10601 | CS+SC | ❌ |  |  | CS flag:uint32 ／ SC p:uint32; skill_bid:uint32; lev:uint32; hero_list:table |
| 10610 | CS+SC | ❌ |  |  | CS fight_handle:table; mons_bid_value:table; fps:uint32 ／ SC code:uint8; msg:string |
| 10621 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC world_lev:uint16; skill_list:table |
| 10622 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string; skill_list:table |
| 10630 | SC | ❌ |  |  | SC skill_list:table |
| 10631 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string; skill_bid:uint32; last_time:uint32 |
| 10632 | CS+SC | ❌ |  |  | CS bid:uint32; target_type:uint8; target_id:uint32; target_srv_id:string ／ SC code:uint8; msg:string; skill_bid:uint32; last_time:uint32 |
| 10633 | CS+SC | ❌ |  |  | CS bid:uint32; x:uint16; y:uint16 ／ SC code:uint8; msg:string; skill_bid:uint32; last_time:uint32 |
| 10640 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC buff_list:table |
| 10650 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC talent_list:table |
| 10651 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10701 | CS+SC | ❌ |  |  | CS flag:uint8; type:uint8 ／ SC type:uint8; code:uint8; msg:string |
| 10702 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC all_building:table |
| 10705 | CS | ❌ |  |  | CS （无字段/空消息） |
| 10706 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC npc_list:table |
| 10707 | SC | ❌ |  |  | SC npc_bid:uint32; type:uint8 |
| 10708 | SC | ❌ |  |  | SC npc_bid:uint32 |
| 10709 | CS+SC | ❌ |  |  | CS time:uint16 ／ SC code:uint8; msg:string |
| 10710 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC lev:uint8; store_num:uint32; status:uint8; left_time:uint32; total_time:uint32 |
| 10711 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; val:uint32 |
| 10712 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10713 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10714 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC lev:uint8; InfoList:table |
| 10715 | SC | ❌ |  |  | SC TypeList:table |
| 10716 | SC | ❌ |  |  | SC type:uint8; val:uint32 |
| 10731 | CS+SC | ❌ |  |  | CS Type:uint8 ／ SC Type:uint8; lev:uint8; gold:uint32; next_time:uint16 |
| 10733 | CS+SC | ❌ |  |  | CS hero_list:table ／ SC code:uint8; msg:string; set_house_hero_return:table |
| 10734 | CS+SC | ❌ |  |  | CS Type:uint8 ／ SC code:uint8; msg:string; gold:uint32 |
| 10735 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC house_hero:table |
| 10741 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC lev:uint8; status:uint8; flag:uint8; time:uint32; all_time:uint32; can_get:uint32; be_rob:uint32 |
| 10742 | CS+SC | ❌ |  |  | CS flag:uint8 ／ SC code:uint8; msg:string |
| 10743 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10744 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; wood:uint32 |
| 10745 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10751 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC open_props_list:table |
| 10752 | CS+SC | ❌ |  |  | CS props_id:uint32; ext_queue_id:uint32 ／ SC code:uint8; msg:string |
| 10753 | CS+SC | ❌ |  |  | CS props_id:uint32; props_num:uint32; ext_queue_id:uint32 ／ SC code:uint8; msg:string |
| 10754 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC upgrate_time_list:table |
| 10755 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC make_time_list:table |
| 10756 | CS+SC | ❌ |  |  | CS queue_type:uint8; props_type:uint32 ／ SC code:uint8; msg:string |
| 10757 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC look_queue_list:table |
| 10761 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC lev:uint8; can_get:uint32; be_rob:uint32; next_time:uint16 |
| 10762 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; gold:uint32 |
| 10771 | SC | ❌ |  |  | SC all_building:table |
| 10900 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; hour:uint32; interdict:string ／ SC code:uint8; msg:string |
| 10901 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; hour:uint32; banned:string ／ SC code:uint8; msg:string |
| 10902 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; stop_role:string ／ SC code:uint8; msg:string |
| 10910 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC dnf_info:table |
| 10911 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; buffs:table |
| 10912 | SC | ❌ |  |  | SC bid:uint32; effect:table |
| 10913 | SC | ❌ |  |  | SC buffs:table |
| 10921 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC world_lev:uint8; next:uint32; exp:uint16; dec_exp:uint16; open_day:uint16 |
| 10922 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC act_list:table |
| 10923 | CS+SC | ✅ | ✅ | ✅ | CS id:uint16 ／ SC id:uint16; status:uint8; int_args:table |
| 10924 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC act_list:table |
| 10925 | CS+SC | ❌ |  |  | CS id:uint16 ／ SC id:uint16; status:uint8; int_args:table |
| 10930 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; double:uint16; double_sum:uint16 |
| 10931 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10932 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC double:uint16; double_sum:uint16; double_state:uint16; off_state:uint16 |
| 10933 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10934 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10935 | SC | ❌ |  |  | SC double:uint16 |
| 10941 | SC | ❌ |  |  | SC id:uint8 |
| 10942 | CS+SC | ❌ |  |  | CS id:uint8 ／ SC （无字段/空消息） |
| 10945 | CS+SC | ❌ |  |  | CS card_id:string ／ SC code:uint8; msg:string; items:table |
| 10946 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; item_bid:uint32 |
| 10947 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; name:string; lev:uint16; career:uint16; sex:uint8; is_vip:uint8; vip_lev:uint8; gname:string; cur_title:uint32; marry_state:uint8; spouse_n |
| 10948 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; items:table |
| 10949 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:ta |
| 10950 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:ta |
| 10951 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; color:uint8; wing_id:uint32; power:uint32; wing_skill:table; add_attr:table; star:uint16 |
| 10952 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; use_id:uint32; shenqi_list:table |
| 10953 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; type:uint8 ／ SC code:uint8; msg:string |
| 10954 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; name:string; stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; looks:table; surface_star |
| 10955 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table |
| 10957 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table |
| 10958 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; items:table |
| 10995 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC srv_list:table |
| 10996 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC cli_ver_list:table |
| 10997 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC flag:uint8 |
| 10998 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC cli_ver:uint16; flag:uint16 |
| 10999 | CS | ❌ | ✅ |  | CS msg:string |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
