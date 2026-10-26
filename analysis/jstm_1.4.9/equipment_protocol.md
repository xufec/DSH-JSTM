# 装备/仓库 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（66 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
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
| 11200 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC volume:uint8; volume_open:uint8; partner_bag:table; gratis:table |
| 11201 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC id:uint32; bid:uint32; type:uint8; color:uint8; lifttime:uint32; lev:uint8; exp:uint32; grow:uint16; score:uint32; stage:uint8; rebirth:uint8; acc:uint8; partner_attr:table; power:ui |
| 11202 | SC | ❌ |  |  | SC id:uint32; exp:uint32 |
| 11203 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string |
| 11204 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC id:uint32; skill:table |
| 11205 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; msg:string; id:uint32 |
| 11206 | CS+SC | ❌ | ✅ |  | CS state:uint8 ／ SC code:uint8; msg:string; volume:uint8; volume_open:uint8 |
| 11207 | SC | ❌ |  |  | SC lev_list:table |
| 11208 | CS+SC | ❌ |  |  | CS id:uint32; state:uint8 ／ SC code:uint8; msg:string |
| 11209 | SC | ❌ |  |  | SC lift_list:table |
| 11210 | SC | ❌ |  |  | SC id:uint32; lev:uint16; exp:uint32; color:uint8; score:uint32; partner_attr:table; power:uint32 |
| 11211 | SC | ❌ |  |  | SC id:uint32; talisman_skill:table |
| 11212 | CS+SC | ❌ |  |  | CS bid:uint32; type:uint8 ／ SC code:uint8; msg:string; bid:uint32; type:uint8 |
| 11213 | CS+SC | ❌ |  |  | CS id:uint32; attr_code:uint16 ／ SC code:uint8; msg:string; attr_code:uint16; attr_val:uint16 |
| 11214 | CS+SC | ❌ |  |  | CS from_code:uint8; target_code:uint8; partner_id:uint32 ／ SC code:uint8; msg:string; from_code:uint8; target_code:uint8; partner_id:uint32 |
| 11215 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC partner_list:table |
| 11216 | CS+SC | ❌ | ✅ |  | CS partner_bid:uint32; state:uint8 ／ SC code:uint8; msg:string; partner_bid:uint32 |
| 11217 | CS+SC | ❌ |  |  | CS id:uint32; state:uint8 ／ SC code:uint8; msg:string; id:uint32 |
| 11218 | CS+SC | ❌ |  |  | CS id:uint32; state:uint8 ／ SC code:uint8; msg:string; partner_bid:uint32 |
| 11221 | CS+SC | ❌ |  |  | CS srv_id:string; cache_id:uint32 ／ SC cache_id:uint32; partner_list:table; eqm_list:table |
| 11222 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint32; msg:string |
| 11223 | SC | ❌ |  |  | SC power_list:table |
| 11224 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; id:uint32 ／ SC id:uint32; partner_list:table; eqm_list:table |
| 11225 | SC | ❌ |  |  | SC id:uint32; ext:table |
| 11226 | CS+SC | ❌ |  |  | CS id:uint32; state:uint8 ／ SC code:uint8; msg:string; id:uint32 |
| 11227 | CS+SC | ❌ |  |  | CS id:uint32; hufu_id:uint32; fazhen_id:uint32 ／ SC code:uint8; msg:string; id:uint32 |
| 11228 | CS+SC | ❌ |  |  | CS id:uint32; item_id:uint32 ／ SC code:uint8; msg:string; id:uint32 |
| 11237 | CS+SC | ❌ |  |  | CS formation_type:uint32 ／ SC code:uint32; msg:string; stage:uint32; star:uint32; open_index:uint32; rune_data:table; formation_type:uint32; partner_list:table; exp:uint32; crit_cnt:uint32; not_crit_c |
| 11238 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint32; msg:string; stage:uint32; star:uint32; open_index:uint32; rune_data:table; exp:uint32; crit_cnt:uint32; not_crit_cnt:uint32; break:uint32; is_crit:uint8 |
| 11239 | CS+SC | ❌ |  |  | CS formation_type:uint32; index:uint32; partner_id:uint32; op_type:uint32 ／ SC code:uint32; msg:string; formation_type:uint32; index:uint32; partner_id:uint32; op_type:uint32 |
| 11240 | CS+SC | ❌ |  |  | CS index:uint32; rune_index:uint32; item_id:uint32; op_type:uint32 ／ SC code:uint32; msg:string; index:uint32; rune_index:uint32; item_id:uint32; op_type:uint32; items:table |
| 11241 | CS+SC | ❌ |  |  | CS index:uint32; rune_index:uint32; item_id:uint32; item_list:table ／ SC code:uint32; msg:string; index:uint32; rune_index:uint32; item_id:uint32; item_lev:uint32; item_exp:uint32; item_list:table |
| 11242 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint32; msg:string; stage:uint32; star:uint32; open_index:uint32; rune_data:table; exp:uint32; crit_cnt:uint32; not_crit_cnt:uint32; break:uint32 |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
