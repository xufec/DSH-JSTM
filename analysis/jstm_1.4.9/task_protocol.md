# 任务 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（39 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 12400 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC mission_list:table |
| 12401 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC missions:table |
| 12402 | CS+SC | ✅ |  |  | CS mission_bid:uint32 ／ SC code:uint8; msg:string; missions:table |
| 12403 | CS+SC | ✅ | ✅ | ✅ | CS mission_bid:uint32 ／ SC mission_bid:uint32; code:uint8; msg:string |
| 12404 | CS+SC | ❌ |  |  | CS mission_bid:uint32 ／ SC code:uint8; msg:string; mission_bid:uint32 |
| 12405 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC update_mission_list:table |
| 12406 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC del_mission_list:table |
| 12407 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC add_mission_list:table |
| 12408 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC delete_list:table |
| 12409 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC missions:table |
| 12410 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC id:uint32; lottery_list:table |
| 12411 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC id:uint32; code:uint8; msg:string |
| 12412 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC bid:uint32; assets:table; items:table; guild_assets:uint32; guild_wage:uint32 |
| 12413 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC bid:uint32; progress_list:table |
| 12414 | CS+SC | ❌ |  |  | CS talk_bid:uint32; mission_bid:uint32; npc_bid:uint32 ／ SC mission_bid:uint32; npc_bid:uint32; code:uint8; msg:string |
| 12415 | CS+SC | ❌ |  |  | CS mission_bid:uint32; item_bid:uint32; item_num:uint32 ／ SC mission_bid:uint32; item_bid:uint32; item_num:uint32; code:uint8; msg:string |
| 12416 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC mission_bid:uint32 |
| 12417 | CS+SC | ❌ |  |  | CS mission_bid:uint32; partner_id:uint32; partner_num:uint32 ／ SC mission_bid:uint32; partner_id:uint32; partner_num:uint32; code:uint8; msg:string |
| 12418 | CS+SC | ❌ |  |  | CS mission_bid:uint32 ／ SC uniq_id:uint32; mission_bid:uint32 |
| 12419 | CS+SC | ❌ |  |  | CS srv_id:string; uniq_id:uint32 ／ SC mission_bid:uint32; mission_status:uint8; commit_num:uint16; loop_count:uint16; loop_num:uint16; code:uint8; process_status:uint8; target:uint32; target_value:uin |
| 12420 | SC | ❌ |  |  | SC name:string |
| 12421 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC finish_task_list:table |
| 12422 | CS+SC | ❌ |  |  | CS mission_bid:uint32; item_list:table ／ SC mission_bid:uint32; code:uint8; msg:string |
| 12430 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; quantity:uint8; msg:string |
| 12431 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC bonus:table; cur_quantity:uint32; free_refresh_times:uint8; times:uint8; total_times:uint8; assist_times:uint8; total_assist_times:uint8 |
| 12432 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 12433 | SC | ❌ |  |  | SC times:uint8; coin:uint32; exp:uint32; hero_exp:uint32; old_coin:uint32; old_exp:uint32; old_hero_exp:uint32 |
| 12434 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 12435 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC total_win:uint8; round:uint8; quality:uint8; team_win:table |
| 12436 | CS+SC | ❌ |  |  | CS finger:uint8 ／ SC rid:uint32; srv_id:string; role_finger:uint8 |
| 12437 | SC | ❌ |  |  | SC total_win:uint8; quality:uint8 |
| 12438 | SC | ❌ |  |  | SC total_win:uint8; round:uint8; result:uint8; win_count:uint8; quality:uint8; sys_finger:uint8; team_win:table |
| 12439 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string |
| 12440 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC bid:uint32; items:table |
| 12450 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string; type:uint8; question_id:uint32; answer_id:uint8 |
| 12451 | CS+SC | ❌ |  |  | CS type:uint8; answer_id:uint8 ／ SC code:uint8; msg:string |
| 12452 | SC | ❌ |  |  | SC spouse_answer_id:uint8 |
| 12460 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string |
| 12499 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC type:uint8; num:uint8 |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
