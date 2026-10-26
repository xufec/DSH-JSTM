# 社交/好友/帮会 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（35 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 11700 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC free_times:uint8; all_times:uint8; reward_coin:uint32; one_name:string; one_coin:uint32; record_server:table; record_self:table |
| 11701 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC code:uint8; msg:string; id:uint8 |
| 11702 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11703 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC get_times:uint8; all_times:uint8; reward_gold:uint32; one_name:string; one_coin:uint32; record_server:table; record_self:table |
| 11704 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC code:uint8; msg:string; id:uint8 |
| 11705 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11706 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC time:uint32 |
| 11707 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC record_server:table |
| 11708 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; id:uint8 |
| 11709 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11710 | CS+SC | ✅ | ✅ | ✅ | CS type:uint8 ／ SC type:uint8; get_times:uint8; record_server:table; record_self:table |
| 11711 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; id:uint8 |
| 11712 | CS+SC | ✅ | ✅ |  | CS type:uint8; count:uint8 ／ SC code:uint8; type:uint8; msg:string; Items:table |
| 11713 | CS+SC | ✅ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11717 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC timestamp:uint32; free_time:uint8; holiday_name:string; reward_list:table; record_server:table; show_list:table |
| 11718 | CS+SC | ❌ |  |  | CS pay_type:uint8 ／ SC code:uint8; msg:string; id:uint32; reward_id:uint32; record_server:table; reward:table |
| 11719 | CS+SC | ❌ |  |  | CS pay_type:uint8 ／ SC code:uint8; msg:string; record_server:table; reward:table |
| 11720 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; free_time:uint8; reward_list:table |
| 11721 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11800 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 11801 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; set_line:uint8 ／ SC code:uint8; msg:string; rid:uint32; srv_id:string |
| 11900 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC first_reward:uint8; day_reward:uint8; online_time:uint32; online_id:uint8; lev_list:table; timer_reward:uint8 |
| 11901 | CS+SC | ❌ |  |  | CS type:uint8 ／ SC code:uint8; msg:string; type:uint8 |
| 11902 | SC | ❌ |  |  | SC type:uint8 |
| 12000 | CS+SC | ❌ |  |  | CS dung_bid:uint32 ／ SC tips:uint16; msg:string; mon_list:table; item_list:table |
| 12001 | CS+SC | ❌ |  |  | CS dung_bid:uint32; finish:uint32; live_num:uint8 ／ SC bid:uint16; star_lev:uint8; gain:table; items:table |
| 12002 | CS+SC | ❌ |  |  | CS dung_bid:uint32 ／ SC code:uint8; msg:string; dung_bid:uint32; gain:table; items:table |
| 12003 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC chapter_bid:uint32 |
| 12004 | CS+SC | ❌ |  |  | CS chapter_bid:uint32 ／ SC code:uint8; msg:string |
| 12005 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC chapter_star:table |
| 12006 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC bid:uint32; left_times:uint32 |
| 12007 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC bid:uint32; buy_times:uint32 |
| 12008 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string; count:uint16 |
| 12021 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC week:uint8; interval_list:table |
| 12022 | CS+SC | ❌ |  |  | CS dung_bid:uint16 ／ SC num:uint8; sec:uint32 |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
