# 1.4.9 Inventory

> Resource corpus for version **1.4.9** (jstm.apk, qihoo/360 channel, NOW_VERSION=186, 230.5MB). Extractions live under `analysis\1.4.9\` and `analysis\jstm_1.4.9\`.

## Version identity
- APK: `C:\Users\xu\Desktop\DSH\anzbao\jstm.apk`
- Version: **1.4.9**, NOW_VERSION=186, qihoo/360 channel. CONFIRMED.

## Config tables (extracted)
Under `analysis\1.4.9\`:
- JSON configs: `config_exchange.json`, `config_function.json` (91 entries by `"id"` count)
- Sub-directories: `battle/`, `item/`, `level/`, `login/`, `mission/`, `movement/`, `npc/`, `protocol/`, `role/`, `scene/`, `shop/`, `shop_luac/`, `task/`, `ui/`
- `item\config_item.json` (~ item rows; 3535 reported)
- `task\config_chapter.json`, `task\config_map.json`, `task\config_mon.json`, `task\config_npc.json`, `task\config_role_attr.json`, `task\map_npc.json`, `task\map_scene_doors.json`, `task\story_quest_route.json`
- `level\level_table.json`, `level\role_attr.json`, `level\role_career.json`, plus raw dumps `level\_attr.json`, `_hero_attr_raw.json`, `_role_attr_raw.json`, `_role_attribute.json`, `_role_career_raw.json`, `_proto_spec_exp.json`, `_reward.json`
- `shop_luac\_mall_all.json`, `shop_luac\mall_table_1_Config.json` (142 mall goods reported)
- `item\_config_drop_item.json`, `item\_config_drop.json`, `item\_assets_config.json`
- Decompiled `_config_*.luac` (11 files): `_config_attr`, `_config_chapter`, `_config_drama_data`, `_config_lead_data`, `_config_map_block`, `_config_map_npc`, `_config_map`, `_config_mon_data`, `_config_npc`, `_config_role_attr`, `_config_role_career`
- Other `.luac`: `_mission_ctrl`, `_mission_data2`, `_mission_util`, `_npc_ctrl`, `_npc_dialogs`, `_npc_mission_manager`, `_npc_mission_vo`, `_npc_talk_manager`, `_story_ctrl`, `_story_data`, `_story_view`

## cmd_resolve / protocol files
- Shared registry `protocol\cmd_table.json` (1643 commands), `protocol\fields.json` (3553 entries). The registry is **version-agnostic / 1.4.9-based** — this is noted in the matrix.
- `analysis\jstm_1.4.9\`: per-system protocol docs (`login`, `role`, `inventory`, `equipment`, `skill`, `partner`, `task`, `scene`, `movement`, `battle`, `dungeon`, `chat`, `social`, `gm`), `protocol_index.md`, `README.md`, `_impl_cmds.txt`, `_observed_cmds.txt`.

## UI modules / luac
- Partial / descendant files only (e.g. `_npc_*`, `_mission_*`, `_story_*`). No full 1.4.9 UI module corpus beyond what is listed above.

## Counts (VERIFIED per task context)
- items (server item_config): 3535
- missions (server mission_config): 846
- mall goods (server mall_config): 142
- partners (server partner_config): 53
- config_function entries: 91