# 背包/物品 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（75 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 10500 | SC | ❌ |  | ✅ | SC bag_code:uint8; items:table |
| 10501 | SC | ❌ |  |  | SC code:uint8; num_up_arr:table |
| 10502 | CS+SC | ✅ | ✅ | ✅ | CS bag_code:uint8 ／ SC bag_code:uint8; items:table |
| 10503 | SC | ❌ |  |  | SC code:uint8; del_ids_arr:table |
| 10504 | CS+SC | ❌ |  |  | CS code:uint8; items_id:table ／ SC code:uint8; msg:string |
| 10505 | CS+SC | ✅ | ✅ | ✅ | CS code:uint8; item_id:uint32; use_num:uint16; type:uint32; bid:uint32 ／ SC code:uint8; msg:string; item_bid:uint32 |
| 10506 | CS+SC | ❌ |  |  | CS bag_item_id:uint32; hero_bid:uint32 ／ SC code:uint8; msg:string; bag_item_id:uint32; item_bid:uint32; hero_bid:uint32; eqm_new_pos:uint8 |
| 10507 | CS+SC | ❌ |  |  | CS item_bid:uint32 ／ SC code:uint8; msg:string |
| 10508 | SC | ❌ |  |  | SC code:uint8; pos_up_arr:table |
| 10509 | CS+SC | ✅ | ✅ | ✅ | CS bag_code:uint8 ／ SC code:uint8; msg:string |
| 10510 | SC | ❌ |  |  | SC code:uint8; volume:uint8; open_volume:uint8 |
| 10511 | CS+SC | ✅ | ✅ | ✅ | CS bag_item_id:uint32; eqm_item_id:uint32; hero_bid:uint32 ／ SC code:uint8; msg:string; is_auto:uint8; bag_item_id:uint32; eqm_item_id:uint32; eqm_new_pos:uint8; hero_bid:uint32 |
| 10512 | CS+SC | ✅ | ✅ |  | CS eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 ／ SC code:uint8; msg:string; eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 |
| 10513 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32; state:uint8 ／ SC code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; eqm_item_id_new:uint32; eqm_item_bid_new:uint32; eqm_item_power_new:uint32 |
| 10514 | CS+SC | ❌ | ✅ |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; bag_to_eqm:table; bag_replace_eqm:table |
| 10515 | SC | ❌ |  |  | SC durable_update:table |
| 10516 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32 ／ SC code:uint8; msg:string |
| 10517 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10518 | CS+SC | ❌ |  |  | CS item_list:table ／ SC code:uint8; msg:string |
| 10519 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32; state:uint8 ／ SC code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; lev:uint8; power:uint32 |
| 10520 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32; count:uint16; state:uint8 ／ SC code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; color:uint8; lev:uint8; exp:uint16; power:uint32 |
| 10521 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32; jewel_item_id:uint32 ／ SC code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; pos:uint8 |
| 10522 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32; pos:uint8 ／ SC code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32 |
| 10523 | CS+SC | ❌ |  |  | CS item_bid:uint32; gold_state:uint8; all_state:uint8 ／ SC code:uint8; msg:string; item_bid:uint32; bid_list:table |
| 10524 | CS+SC | ❌ |  |  | CS item_bid:uint32; all_state:uint32 ／ SC code:uint8; msg:string; fc_bid_list:table; bid_list:table |
| 10525 | CS+SC | ❌ |  |  | CS from_code:uint8; item_id:uint32 ／ SC uniq_id:uint32; from_code:uint8; item_id:uint32 |
| 10526 | CS+SC | ❌ |  |  | CS srv_id:string; uniq_id:uint32 ／ SC items:table |
| 10527 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC state_list:table |
| 10528 | CS+SC | ✅ | ✅ | ✅ | CS lev:uint8; type:uint8 ／ SC code:uint8; msg:string; lev:uint8; state_list:table |
| 10529 | CS+SC | ❌ |  |  | CS code_bag:uint8; eqm_item_id:uint32; state:uint8 ／ SC code:uint8; msg:string; code_bag:uint8; eqm_item_id:uint32; score:uint16; power:uint32; refine:uint16; attr:table |
| 10530 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32; jewel_pos:uint8; state:uint8 ／ SC code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; jewel_pos:uint8; jewel_bid:uint8 |
| 10531 | CS+SC | ❌ |  |  | CS item_list:table ／ SC item_coin:table |
| 10532 | CS+SC | ❌ | ✅ |  | CS bag_code:uint8; type:uint8; item_id:uint32 ／ SC val:int32 |
| 10533 | CS+SC | ❌ |  |  | CS type:uint8; partner_id:uint32 ／ SC val:uint8 |
| 10534 | CS+SC | ✅ | ✅ | ✅ | CS item_bid:uint32 ／ SC val:uint8 |
| 10535 | SC | ❌ |  |  | SC gift_item_bid:uint32; item_list:table; assets_list:table |
| 10536 | CS+SC | ❌ |  |  | CS item_id:uint32; item_num:uint32 ／ SC code:uint8; msg:string; bid_list:table |
| 10537 | CS+SC | ❌ |  |  | CS item_id:uint32 ／ SC code:uint8; msg:string; item_id:uint32 |
| 10540 | SC | ❌ |  |  | SC eqm_list:table |
| 10541 | CS+SC | ❌ |  |  | CS bag_code:uint8; eqm_item_id:uint32; state:uint8 ／ SC code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; grade:uint8; power:uint32 |
| 10542 | SC | ❌ |  |  | SC item_bid:uint32; val:string; msg:string |
| 10543 | SC | ❌ |  |  | SC code:uint8; up_date_ext:table |
| 10544 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC attrs_ext_list:table |
| 10545 | CS+SC | ❌ |  |  | CS eqm_item_id_1:uint32; eqm_item_id_2:uint32 ／ SC code:uint8; msg:string; new_eqm_item_id:uint32 |
| 10546 | CS+SC | ❌ |  |  | CS eqm_item_id:uint32; state:uint8 ／ SC code:uint8; msg:string; new_eqm_item_id:uint32; skill_list:table; attr:table |
| 10547 | CS+SC | ❌ |  |  | CS eqm_item_id_1:uint32 ／ SC code:uint8; msg:string |
| 10548 | SC | ❌ |  |  | SC item_bid:uint32; val:uint32; msg:string |
| 10551 | CS+SC | ✅ |  |  | CS item_bid:uint32 ／ SC val:uint32 |
| 10552 | CS+SC | ✅ | ✅ | ✅ | CS bag_code:uint8; volume:uint8; state:uint8 ／ SC code:uint8; msg:string; bag_code:uint8; old:uint16; new:uint16 |
| 10553 | CS+SC | ❌ |  |  | CS from_code:uint8; from_item_id:uint32; to_code:uint8; to_item_id:uint32 ／ SC code:uint8; msg:string; from_code:uint8; from_item_id:uint32; to_code:uint8; to_item_id:uint32 |
| 10554 | CS+SC | ✅ | ✅ | ✅ | CS from_code:uint8; target_code:uint8; item_id:uint32 ／ SC code:uint8; msg:string; from_code:uint8; target_code:uint8; item_id:uint32 |
| 10555 | CS+SC | ❌ |  |  | CS items_id:table ／ SC code:uint8; msg:string |
| 10556 | SC | ❌ |  |  | SC （无字段/空消息） |
| 10557 | CS+SC | ✅ |  |  | CS bag_code:uint8; args:table ／ SC code:uint8; msg:string |
| 10558 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC suit_lev:uint16; next_suit_lev:uint16 |
| 10560 | CS+SC | ❌ | ✅ |  | CS args:table ／ SC args:table |
| 10561 | CS+SC | ❌ |  |  | CS key:uint16; args:table ／ SC key:uint16; args:table |
| 10570 | CS+SC | ✅ | ✅ | ✅ | CS bag_code:uint8; ItemIdList:table ／ SC bag_code:uint8; code:uint8; msg:string |
| 10571 | CS+SC | ❌ |  |  | CS item_id:uint32; is_buy:uint8 ／ SC code:uint8; msg:string; item_id:uint32; star_lev:uint8; star_grid:uint8 |
| 10572 | CS+SC | ❌ |  |  | CS gift_id:uint32; chose_ids:table; count:uint16 ／ SC code:uint8; msg:string |
| 10573 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; bid:uint32; msg:string |
| 10574 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; id:uint32; msg:string |
| 10575 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; id:uint32; msg:string |
| 10576 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; id:uint32; msg:string |
| 10577 | SC | ❌ |  |  | SC id:uint32 |
| 10578 | CS+SC | ❌ |  |  | CS bid:uint32 ／ SC code:uint8; msg:string |
| 10582 | SC | ❌ |  |  | SC item_id:uint32; item_bid:uint32; type:uint8; item_list:table |
| 10586 | CS+SC | ❌ |  |  | CS ItemIdList:table ／ SC code:uint8; msg:string |
| 10587 | CS+SC | ❌ |  |  | CS bag_item_id:uint32; eqm_item_id:uint32; hero_bid:uint32 ／ SC code:uint8; msg:string; is_auto:uint8; bag_item_id:uint32; eqm_item_id:uint32; eqm_new_pos:uint8; hero_bid:uint32 |
| 10588 | CS+SC | ❌ |  |  | CS eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 ／ SC code:uint8; msg:string; eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 |
| 10589 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC flyup_lev:uint8; flyup_stage:uint8; exp:uint32; dan_cnt:uint8 |
| 10590 | CS+SC | ❌ |  |  | CS ItemIdList:table ／ SC code:uint8; msg:string; ItemIdList:table |
| 10591 | CS+SC | ❌ |  |  | CS item_bid:uint32; use_num:uint8 ／ SC code:uint8; msg:string; item_bid:uint32; use_num:uint8 |
| 10592 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC end_time:uint32; GiftList:table |
| 10593 | CS+SC | ❌ |  |  | CS id:uint32 ／ SC code:uint8; msg:string; id:uint32; cnt:uint16 |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）
