# 1.4.11 Inventory

> Resource corpus for version **1.4.11** (jstm_142165.apk, baidu2 channel, NOW_VERSION=208, 267.8MB). This is the **PRIMARY compatibility target**. Extraction lives under `_tmp_cfg\`.

## Version identity
- APK: `C:\Users\xu\Desktop\DSH\anzbao\jstm_142165.apk`
- Version: **1.4.11**, NOW_VERSION=208, baidu2 channel. CONFIRMED (verified by `file_update_1411.luac`).

## Config tables (extracted)
Under `_tmp_cfg\` (total 305 files):
- **233 config_*.luac tables** (223 `config_*.luac` by name)
- **8 config_*.json** exports incl.:
  - `config_function.json` (91 entries)
  - `config_act.json`, `config_fest_data.json`, `config_growth_target.json`, `config_invest.json`, `config_invest_dec.json`, `config_rank.full.json`, `config_rune_dec.json`
- Notable config tables present: `config_item.luac`, `config_skill.luac` (+ skill_bullet/magic/scene/talent/trigger/xiulian), `config_partner_base/fetter/misc/score/shenqi/skill.luac`, `config_mission.luac` (+ mission_buffy/escort/help/kill_demon/loop/marry/treasure), dungeon family (`config_dungeon_*.luac`), activity family (`config_activity`-related, `activity_ctrl.luac`, `config_festival_goods.luac`, etc.), shop/mall (`config_mall.luac`, `config_shop.luac`, `config_market.luac`), currency/item (`config_currency`-family via `config_item*.luac`), UI modules (`*_ctrl.luac`, `*_panel.luac`, `*_view.luac`, `race_ui_*`), GM (`config_gm_cmd.luac`), scene/map (config_map/map_block/map_npc/map_icon_pos/map_partical), NPC (config_npc.luac), monster (config_mon_data.luac).

## cmd_resolve / protocol files
- `protocol\cmd_table.json` (1643 commands), `protocol\fields.json` (3553 entries) — **shared/version-agnostic, treated as 1.4.9-based** (not confirmed to match 1.4.11). INFERENCE.
- `_tmp_cfg\server_cmds.json`, `_tmp_cfg\protocalrulesmgr.luac`, `_tmp_cfg\rank.asm`.

## UI modules / luac
Extensive `_tmp_cfg\` includes many UI controllers/panels: `action_ctrl/panel`, `activity_ctrl`, `daily_*`, `shop_*`, `invest_*`, `qifu_*`, `race_*`, `guild_*`, `rank_*`, `market_ctrl`, `role_ctrl`, `scene_controller`, `notice`, `cross_ctrl`, `ghost_*`, `demontower_ctrl`, `endless_form_ctrl`, `sky_present_ctrl`, `automate_ctrl`, `guildwars_ctrl`, `race_ctrl`, etc.

## Counts
- config_function entries: **91** (matches 1.4.9's 91 by the same `"id"`-count method) — VERIFIED.