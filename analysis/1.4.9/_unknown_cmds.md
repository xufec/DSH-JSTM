| cmd | 归属（客户端） | 我们的状态 | 默认响应 | 真机总发 | SC 字段 |
|---|---|---|---|---|---|
| `13200` | team_ctrl, config_demon, config_role_career | 默认 | 61 | 61 | msg:string, team_id:uint32, team_srv_id:string, leader_id:uint32, leader_srv_id:string, le |
| `16500` | invest_ctrl, config_act, cmd_resolve_165 | 默认 | 56 | 56 | info:table |
| `13300` | friend_ctrl, config_role_career, config_skill_talent | 默认 | 52 | 52 | friend_list:table |
| `13321` | friend_ctrl, cmd_resolve_133 | 默认 | 52 | 52 | request_list:table |
| `16664` | action_ctrl, cmd_resolve_166 | 默认 | 48 | 48 | msg:string, bid:uint32, remain_sec:uint32, status:uint32, end_time:uint32, rate:uint32, cl |
| `17200` | invest_ctrl, config_role_career, config_skill_talent | 默认 | 47 | 47 | day:uint32, status:uint8 |
| `16602` | action_ctrl, config_act, cmd_resolve_166 | 默认 | 46 | 46 | type:uint8, holiday_list:table |
| `19400` | yuanshen_ctrl, cmd_resolve_194 | 默认 | 41 | 41 | bag_code:uint8, mingge_stage:uint8, mingge_list:table |
| `10932` | automate_ctrl, cmd_resolve_109 | 默认 | 38 | 38 | double:uint16, double_sum:uint16, double_state:uint16, off_state:uint16 |
| `11600` | wing_ctrl, config_act, config_title | 默认 | 38 | 38 | color:uint8, wing_id:uint32, power:uint32, wing_skill:table, add_attr:table, star:uint16,  |
| `13569` | qifu_ctrl, cmd_resolve_135 | 默认 | 38 | 38 | info:table |
| `13579` | tree_ctrl, cmd_resolve_135 | 默认 | 38 | 38 | tree_lev:uint8, strength_rest:uint32, strength_name:string, role_eff:uint32, role_delay:ui |
| `13580` | tree_ctrl, cmd_resolve_135 | 默认 | 38 | 38 | worship_list:table |
| `13806` | market_ctrl, cmd_resolve_138 | 默认 | 38 | 38 | add_space:uint8, goods_list:table |
| `15501` | horse_ctrl, cmd_resolve_155 | 默认 | 38 | 38 | jie:uint8, jie_luck:uint16, grow:uint16, zz:uint16, face:uint8, use:uint8, skill_list:tabl |
| `15700` | artifact_ctrl, config_role_career, config_skill_talent | 默认 | 38 | 38 | use_id:uint32, shenqi_list:table |
| `15801` | beast_ctrl, cmd_resolve_158 | 默认 | 38 | 38 | jie:uint8, jie_luck:uint16, grow:uint16, zz:uint16, face:uint8, use:uint8, skill_list:tabl |
| `16704` | vip_ctrl, cmd_resolve_167 | 默认 | 38 | 38 | vip_lev:uint8, status:uint8 |
| `16706` | vip_ctrl, cmd_resolve_167 | 默认 | 38 | 38 | status:uint8, qq:string, items:table |
| `18900` | role_ctrl, config_partner_skill, cmd_resolve_189 | 默认 | 38 | 38 | coin_times:uint16, power:uint16, fabao_list:table |
| `19406` | yuanshen_ctrl, cmd_resolve_194 | 默认 | 38 | 38 | soul:uint16, soul_max:uint16, coin_type:uint8, price:uint32, is_tick:uint8 |
| `20500` | friendback_ctrl, config_npc, config_chengjiu | 默认 | 38 | 38 | end_time:uint32, role_id:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, career: |
| `20800` | chair_ctrl, config_chengjiu, global_const_define | 默认 | 38 | 38 | stage:uint8, power:uint32, luck:uint16, res_stage:uint8, grow:uint16, skill_list:table, it |
| `20504` | friendback_ctrl, cmd_resolve_205 | 默认 | 32 | 32 | type:uint8, mission_list:table |
| `13741` | build_ctrl, cmd_resolve_137 | 默认 | 30 | 30 | lev:uint8, learn_list:table |
| `13331` | role_ctrl, cmd_resolve_133 | 默认 | 29 | 29 | courage:uint32, charm:uint32, courage_rank:uint8, charm_rank:uint8 |
| `13361` | circle_ctrl, cmd_resolve_133 | 默认 | 29 | 29 | zone_list:table, head_list:table |
| `15204` | npc_ctrl, cmd_resolve_152 | 默认 | 29 | 29 | num:uint8, gold:uint8 |
| `16200` | boss_ctrl, config_act, config_role_career | 默认 | 29 | 29 | count:uint8, boss_list:table |
| `17001` | npc_ctrl, config_chengjiu, cmd_resolve_170 | 默认 | 29 | 29 | max_gate:uint8 |
| `17306` | race_ctrl, cmd_resolve_173 | 默认 | 29 | 29 | reward_list:table |
| `17310` | race_ctrl, cmd_resolve_173 | 默认 | 29 | 29 | score_list:table |
| `18307` | wedding_ctrl, config_demo, cmd_resolve_183 | 默认 | 29 | 29 | a_name:string, b_name:string, type:uint8, rest_time:uint32, status:uint8, end_time:uint32 |
| `20501` | friendback_ctrl, config_partner_skill, cmd_resolve_205 | 默认 | 29 | 29 | friend_list:table |
| `21306` | dungeon_ctrl, config_item, config_partner_fetter | 默认 | 29 | 29 | list:table |
| `21312` | dungeon_ctrl, config_item, config_partner_fetter | 默认 | 29 | 29 | one_key_sweep_list:table |
| `21400` | soulstar_ctrl, config_item, config_chengjiu | 默认 | 29 | 29 | role_eqm:table, partner_eqm:table, eqm_grid:uint8, dung_bid:uint32, floor:uint8 |
| `21410` | soulstar_ctrl, config_item, config_rune_data | 默认 | 29 | 29 | free_times:uint8, is_haft:uint8, free_end_time:uint32, rest_times:uint8, coin_count:uint8, |
| `30716` | guild_race_ctrl, cmd_resolve_307 | 默认 | 29 | 29 | start_time:table, elimination_match:table, champion_id:int8 |
| `19600` | dailysign_ctrl, cmd_resolve_196 | 默认 | 23 | 23 | type:uint8, list:table |
| `30715` | guild_race_ctrl, cmd_resolve_307 | 默认 | 23 | 23 | （无字段） |
| `13701` | build_ctrl, cmd_resolve_137 | 默认 | 18 | 18 | type:uint8, lev:uint8 |
| `13841` | market_ctrl, cmd_resolve_138 | 默认 | 17 | 17 | type:uint16, yinbi_list:table |
| `16601` | action_ctrl, config_act, cmd_resolve_166 | 默认 | 15 | 15 | holiday_list:table |
| `10341` | circle_ctrl, head_photo_ctrl, config_fabao | 默认 | 14 | 14 | rid:uint32, srv_id:string, id:uint32, img:bool, upload_time:uint32 |
| `12922` | tower_ctrl, config_role_career, cmd_resolve_129 | 默认 | 14 | 14 | my_ord:uint8, my_val:uint32, rank_list:table |
| `13227` | team_ctrl, cmd_resolve_132 | 默认 | 14 | 14 | team_num:uint16, role_num:uint16 |
| `13341` | circle_ctrl, cmd_resolve_133 | 默认 | 14 | 14 | ord:uint8, max_len:uint8, msg_list:table |
| `13354` | circle_ctrl, cmd_resolve_133 | 默认 | 14 | 14 | type:uint8, ord:uint8, max_len:uint8, role_list:table |
| `13501` | guild_ctrl, config_item, config_market | 默认 | 14 | 14 | page:uint8, page_total:uint8, guilds:table, all_count:uint32 |
| `13702` | build_ctrl, cmd_resolve_137 | 默认 | 14 | 14 | code:uint8, msg:string, type:uint8, lev:uint8 |
| `13703` | build_ctrl, cmd_resolve_137 | 默认 | 14 | 14 | code:uint8, msg:string, type:uint8, lev:uint8 |
| `13801` | market_ctrl, cmd_resolve_138 | 默认 | 14 | 14 | left_time:uint16, type:uint16, cur_page:uint8, max_page:uint8, goods_list:table |
| `13906` | chongzhi_ctrl, cmd_resolve_139 | 默认 | 14 | 14 | label:uint8, val_list:table |
| `17308` | race_ctrl, cmd_resolve_173 | 默认 | 14 | 14 | rank_list:table |
| `18865` | chief_ctrl, cmd_resolve_188 | 默认 | 14 | 14 | career:uint8, ord:uint8, num:uint8, rank:uint16, total_score:uint32, score:uint32, dan_sco |
| `20028` | battlevideo_ctrl, config_map, config_item | 默认 | 14 | 14 | type:uint8, replay_list:table |
| `10930` | automate_ctrl, config_mission, cmd_resolve_109 | 未开放 | 0 | 29 | code:uint8, msg:string, double:uint16, double_sum:uint16 |
| `11400` | title_ctrl, xianmo_ctrl, config_title | 未开放 | 0 | 29 | code:uint8, msg:string |
| `13201` | team_ctrl, cmd_resolve_132 | 未开放 | 0 | 29 | tips:uint16, msg:string |
