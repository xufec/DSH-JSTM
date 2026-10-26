# 战斗 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（98 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 13000 | CS+SC | ❌ |  |  | CS dung_bid:uint32 ／ SC tips:uint16; msg:string |
| 13001 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC tips:uint16; msg:string |
| 13002 | SC | ❌ |  |  | SC use_time:uint32; task_all:uint8; task_process_cur:uint8; task_tips:string; task_type:uint8; arg_list:table; cur_task_num:uint8; has_time_limit:uint8; task_time_limit:uint32; time_limit:uint32 |
| 13003 | SC | ❌ |  |  | SC bid:uint16; star:uint8; min_round:uint8; max_round:uint8; time:uint16; gain:table; items:table |
| 13004 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string; count:uint16 |
| 13005 | CS+SC | ❌ |  |  | CS bid:uint32; flag:uint8 ／ SC bid:uint32; flag:uint8; left_times:uint32 |
| 13007 | SC | ❌ |  |  | SC bid:uint32; left_time:uint32 |
| 13008 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC chapter_bid:uint32 |
| 13010 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC bids:table |
| 13011 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC chapter_star:table |
| 13012 | CS+SC | ❌ |  |  | CS chapter_id:uint32; flag:uint8; star:uint32 ／ SC code:uint8; msg:string |
| 13013 | SC | ❌ |  |  | SC chapter_bid:uint32; flag:uint8; star:uint8 |
| 13015 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC chapter_reward:table |
| 13016 | SC | ❌ |  |  | SC bid:uint32; flag:uint8; min_round:uint8; max_round:uint8 |
| 13017 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC bid:uint32; role_out:table; hero_out:table; mon_out:table |
| 13018 | CS+SC | ❌ |  |  | CS floor:uint8; pos:uint8 ／ SC code:uint8; msg:string; pos:uint8; count:uint8; items:table; all:uint8; items_other:table |
| 13019 | SC | ❌ |  |  | SC pos:uint8; member_id:uint32; member_srv_id:string; member_name:string; items:table; all:uint8; items_other:table |
| 13020 | CS+SC | ❌ |  |  | CS dung_bid:uint32; args:table ／ SC tips:uint16; msg:string |
| 13021 | CS+SC | ❌ |  |  | CS dung_bid:uint32; arg:uint8 ／ SC tips:int8; msg:string |
| 13022 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC section:uint8; challenge:uint8; hard:uint8; assets:table |
| 13023 | SC | ❌ |  |  | SC gain:table; items:table; vip_gain:table |
| 13024 | SC | ❌ |  |  | SC level:uint8; pk_id:uint32; pk_srv_id:string; mon_bid:uint32; pk_name:string; pk_lev:uint8; pk_career:uint8; pk_sex:uint8; pk_power:uint8; pk_status:uint8; gain:table; items:table; hard:uint8 |
| 13025 | SC | ❌ |  |  | SC Bid:uint32; Count:uint8 |
| 13026 | CS+SC | ❌ |  |  | CS Bid:uint32; select:uint8 ／ SC tips:uint8; msg:string |
| 13027 | SC | ❌ |  |  | SC bid:uint32; arg:uint16; gain:table; items:table |
| 13028 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC count:uint8; dung_list:table |
| 13029 | SC | ❌ |  |  | SC bid:uint32; round:uint16; star:uint16; score:uint16; gain:table; items:table; effect_type_per:table |
| 13030 | SC | ❌ |  |  | SC flag:int16; time:uint16 |
| 13031 | SC | ❌ |  |  | SC bid:uint32; round_num:uint8; cur_hp:uint32 |
| 13032 | SC | ❌ |  |  | SC dung_bid:uint32; floor:uint8; BossList:table |
| 13033 | SC | ❌ |  |  | SC floor:uint8; round:int16; time:uint16; rank:uint8; output:uint32 |
| 13034 | CS+SC | ❌ |  |  | CS dung_bid:uint32 ／ SC dung_bid:uint32; CengList:table |
| 13035 | CS+SC | ❌ |  |  | CS dung_bid:uint32; ceng:uint8 ／ SC team_list:table |
| 13036 | CS+SC | ❌ |  |  | CS dung_bid:uint32; key:uint8; value:uint8 ／ SC key:uint8; value:uint8 |
| 13037 | CS+SC | ❌ |  |  | CS Bid:uint32; ceng:uint8 ／ SC Bid:uint32; ceng:uint8; tips:uint8; msg:string |
| 13038 | CS+SC | ❌ |  |  | CS Bid:uint32; ceng:uint8 ／ SC record_str:string |
| 13039 | SC | ❌ |  |  | SC Bid:uint32 |
| 13040 | SC | ❌ |  |  | SC Bid:uint32; MonList:table |
| 13041 | SC | ❌ |  |  | SC mon_bid:uint32 |
| 13042 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC high_floor:uint32; ceng_list:table; status:uint8; cur_ceng:uint8; left_time:uint32; clear_list:table; count:uint8 |
| 13043 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC tips:uint16; msg:string; count:uint8 |
| 13044 | CS+SC | ❌ |  |  | CS Bid:uint32 ／ SC tips:uint16; msg:string |
| 13045 | CS+SC | ❌ |  |  | CS floor:uint32 ／ SC floor:uint32; rid:uint32; srv_id:string; name:string; fast_rid:uint32; fast_srv_id:string; fast_name:string; first_get:uint8 |
| 13046 | SC | ❌ |  |  | SC dung_bid:uint32; floor:uint8; BossList:table |
| 13047 | SC | ❌ |  |  | SC floor:uint8; left_time:uint32 |
| 13048 | SC | ❌ |  |  | SC floor:uint8; gain:table; items:table |
| 13049 | SC | ❌ |  |  | SC floor:uint8; gain:table; items:table; first_items:table |
| 13050 | CS | ❌ |  |  | CS （无字段/空消息） |
| 13051 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC tips:uint16; msg:string |
| 13052 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC select_hard:uint8; section:uint8; hard:uint8; challenge:uint8; left_times:uint8; assets:table |
| 13053 | SC | ❌ |  |  | SC FloorAwardList:table |
| 13054 | SC | ❌ |  |  | SC star:uint32; EffectList:table; effect_type_per:table |
| 13055 | CS+SC | ❌ |  |  | CS EffectId:uint32 ／ SC tips:uint16; msg:string; star:uint32; effect_type_per:table |
| 13056 | SC | ❌ |  |  | SC bid:uint32; score:uint32; max_wave:uint8; gain:table; items:table |
| 13057 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC tips:uint16; msg:string |
| 13058 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC cur_score:uint32; get_score:uint32; max_wave:uint8; gain:table; AwardBidList:table |
| 13059 | SC | ❌ |  |  | SC bid:uint32; round:uint32; star:uint32; hard_boss:table |
| 13060 | CS+SC | ❌ |  |  | CS bid:uint32; round:uint32; hard:uint8 ／ SC tips:uint16; msg:string; round:uint32 |
| 13061 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC wave:uint16 |
| 13062 | CS+SC | ❌ |  |  | CS ceng:uint8 ／ SC tips:uint16; msg:string; ceng:uint8 |
| 13065 | SC | ❌ |  |  | SC npc_bid:uint32; question_id:uint32 |
| 13066 | CS+SC | ❌ |  |  | CS npc_bid:uint32; question_id:uint32; answer_id:uint32 ／ SC npc_bid:uint32; answer_id:uint32 |
| 13067 | SC | ❌ |  |  | SC msg:string |
| 13068 | SC | ❌ |  |  | SC dung_bid:uint32; npc_status:table; mons:table |
| 13069 | SC | ❌ |  |  | SC dung_bid:uint32; cur_round:uint8; vese_id:uint32; verse_status:table |
| 13070 | SC | ❌ |  |  | SC npc_bid:uint32 |
| 13071 | SC | ❌ |  |  | SC dung_bid:uint32; box_num:uint8; open_box_num:uint8; boss_bid:uint32; num:uint8 |
| 13072 | SC | ❌ |  |  | SC dung_bid:uint32; mon_status:table; boss_bid:uint32; num:uint8 |
| 13073 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC floor_count:table |
| 13074 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 13075 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC code:uint8; msg:string |
| 13076 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC role_list:table |
| 13079 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string; bid:uint32; enter_count:uint16; buy_count:uint16 |
| 13080 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC list:table |
| 13081 | SC | ❌ |  |  | SC bid:uint32; gain:table; items:table |
| 13082 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC tips:uint8; msg:string; time:uint16 |
| 13083 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC tips:uint8; msg:string |
| 13084 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC max_wave:uint16; rank:uint16; partner_list:table; goods_index:uint16; goods_flag:uint8; max_passed:uint16 |
| 13085 | CS+SC | ❌ |  |  | CS type:uint8; start_rank:uint16; end_rank:uint16 ／ SC type:uint8; rank_list:table |
| 13086 | CS+SC | ❌ |  |  | CS partner_list:table; rid:uint32; srv_id:string; partner_id:uint32 ／ SC tips:uint16; msg:string |
| 13087 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC wave:uint16; rank:uint16; per_name:string; per_wave:uint16; assets:table |
| 13088 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC wave:uint16; rank:uint16; add_rank:int16; assets:table; rank_list:table |
| 13094 | SC | ❌ |  |  | SC dung_bid:uint32; floor:uint8; BossList:table |
| 13095 | SC | ❌ |  |  | SC floor:uint8; round:int16; time:uint16; rank:uint8; output:uint32 |
| 13096 | CS+SC | ❌ |  |  | CS dung_bid:uint32; ceng:uint8 ／ SC team_list:table |
| 13097 | CS+SC | ❌ |  |  | CS dung_bid:uint32 ／ SC dung_bid:uint32; CengList:table |
| 13098 | CS+SC | ❌ |  |  | CS Bid:uint32; ceng:uint8 ／ SC Bid:uint32; ceng:uint8; tips:uint8; msg:string |
| 13099 | SC | ❌ |  |  | SC dung_bid:uint32; floor:uint8; time_out:uint32; ElemList:table; MonList:table; BossList:table |
| 16300 | CS+SC | ❌ |  |  | CS ElementId:uint32 ／ SC flower_id:uint32; rid:uint32; srv_id:string; r_name:string; water_count:uint16; rate:uint16; asset_code:uint8; asset_val:uint32 |
| 16301 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC water_count:uint16; code:uint8; rid:uint32; srv_id:string; msg:string |
| 16302 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC code:uint8; msg:string |
| 16303 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC water_list:table |
| 16304 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC flowers:table |
| 16400 | CS+SC | ❌ | ✅ |  | CS type:uint8 ／ SC type:uint8; chengjiu:table; chengjiu_has:table; chengjiu_rate:table |
| 16401 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string; bid:uint32 |
| 16402 | SC | ❌ |  |  | SC chengjiu:table |
| 16403 | SC | ❌ |  |  | SC chengjiu:table |
| 16404 | CS+SC | ❌ |  |  | CS group:uint32 ／ SC code:uint8; msg:string; chengjiu_rate:table |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
