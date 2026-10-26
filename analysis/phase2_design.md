# Phase 2 · Server Core 拆分设计文档

> 日期：2026-10-02
> 范围：**只读** `server/`；本文件是 Phase 2 的拆分蓝图。
> 硬约束：
> 1. **当前有实机取证在跑，server 进程必须保持稳定**——本文档不修改 `server/` 下任何文件。
> 2. **800 个去重命令号的入口语义不变**（1.4.9 / 1.4.11 已跑通），`_UNSUPPORTED_ACTION_CMDS` / `_GENERIC_DEFAULT_CMDS` 仍为空，`global_default_sc` 仍默认关。
> 3. 所有结论基于代码实况（行号 / 函数名 / 表名），来源：`server/mock_server.py`（18,506 行，982,387 B）、`analysis/server_capability_verified.md`（下称 *Capability*）、`analysis/PHASE0_AUDIT.md`（下称 *P0*）。
> 4. 不讨论具体数值实现；数值类系统一律保留 `TEST_ONLY` / `IMPLEMENTATION_FALLBACK` 标注，等 MuMu 取证后替换。

---

## 一、现状结构图（mock_server.py 实际内部组织）

### 1.1 文件级全景（行号锚点）

| 行号区间 | 内容 | 归属（现状） |
|---|---|---|
| L1–22 | shebang / docstring / imports（argparse/json/os/socket/socketserver/sqlite3/struct/sys/threading/time + http.server） | 入口 |
| L23–54 | 模块常量：`HERE` / `LOGDIR` / `CFG_PATH`；`ATTR_KEYS`(24 键) / `ATTR_DEFAULTS`；软依赖 `proto_defs`、`battle`（L34–37） | core/constants |
| L56–120 | **`role_attr_dict(cfg)` / `role_power(cfg)` / `attr_table_10304(ad)` / `attr_table_10306(ad)`** —— AttributeService 的雏形（docstring 自注 "PHASE 2.10 统一属性汇总入口"） | attribute（已有收敛点） |
| L122–136 | 软依赖 `aoi_mod` / `power_mod` / `pathfind_mod` | scene / power / scene |
| L138–149 | `DEFAULT_CFG`（bind/host/http_port=8080/game_port=9000/server_list/notice） | config |
| L152–179 | `log(name, text)` / `hexdump(data, annotate)` | core/logger |
| L180–249 | `normalize_server_item(s, cfg)`；**全局状态** `CFG = {}` (L232)、`LIVE_CONNECTIONS = []` (L233)、`LIVE_LOCK = threading.Lock()` (L234) | session |
| L250–309 | `_cfg_field_order(r)` / `_cfg_dump(r, order)`（配置表 dump 辅助） | config |
| L310–662 | 场景/AOI/推送辅助：`get_aoi()` (L310)、`load_mapblock()` (L337)、`_scene_grid(bid)` (L358)、`get_mapgrid(bid)` (L389)、`_current_bid(handler)` (L404)、`get_ratelimit()` (L412)、`live_push(cfg, what)` (L421)、`_scene_rid/_scene_enter/_scene_ensure/_scene_leave` (L469–540)、`_authoritative_pos` (L541)、`_scene_validate_move` (L553)、`_scene_apply_move` (L595)、`_scene_broadcast_10204` (L609)、`push_to_rid(rid, pkt)` (L640) | scene / session |
| **L663–1523** | **`class Handler(BaseHTTPRequestHandler)` 的 `do_GET`**：HTTP 8080 + **/DSH_ADMIN 44 个动作**（L704 `if p.startswith('/DSH_ADMIN/')`；动作清单见 *Capability* §四，行号 709–1473） | gm / http |
| L1524–1588 | `do_POST`（gateway `/gateway/mobile/json`、`/app/mobile/json`、CDN 静态） | http |
| L1576–1588 | `CMD_NAMES = {...}` | protocol |
| L1589–1610 | `w_u8 / w_u16 / w_u32 / w_str / pack_frame(cmd, body)` | protocol |
| L1611–1633 | `class FrameParser(object)`（大端 u32 长度 + u16 cmd + body） | protocol |
| L1634–1748 | `build_1110_roles(roles)`（登录回包编码） | account |
| L1749–2007 | `mission_cfg()` / `item_ids()` / `gift_contents(bid)` / `item_type_of(bid)` / `is_valid_item(bid)`；**`_GENERIC_DEFAULT_CMDS` (L1903–1979，空 frozenset)**、**`_UNSUPPORTED_ACTION_CMDS` (L1991–2002，空 frozenset)** | task / item / protocol |
| L2008–2030 | `_sc_fields(cmd)`（读 `protocol/fields.json`，3553 条） | protocol |
| L2030–4219 | **大段 DB/配置辅助函数**（约 2,200 行）：`db_vip_level`、`market_*` (L2049–2248)、`db_build_*` (L2249–2289)、`role_count`、`guild_rows`、`zone_dress_rows`、`demon_cfg/demon_one`、`map_npc_bids`、`db_mail_*` (L2418–2483)、`db_point_*`、`asset_label_map`、`equip_one`、`role_power_of(rid)` (L2551)、`group_control_*`、`dungeon_cfg/dungeon_rows`、`encode_eqm_list`、`dung_progress_of`、`encode_mingge_list`、`db_mingge_one/del`、`worship_rows`、`first_hero`、`tree_*` (L2765–2849)、`_dedicated_cmds()` (L2850)、`rank_metric_value`、`db_arena_trophy`、`qifu_*` (L2957–3032)、`encode_rank_elem/encode_rank_reply`、`_cs_fields/_sc_w/encode_by_sc_with_echo` (L3120–3236)、`kconst/kconst_count/kconst_rows/kconst_str/kconst_int` (L3237–3370)、`_kcfg_fields/_kcfg_row/kcfg_best_attr_table` (L3370–3446)、`db_role_attr(rid)` (L3447)、`attr_row_bytes`、`db_bag_item/db_bag_items_by_bid/bag_items_bytes`、`db_fabao_rows/fabao_list_bytes`、`role_row_bytes`、`kcfg/kcfg_rows/kcfg_count`、`_find_sc_field`、`hero_partner_bytes`、`kcfg2/kcfg2_rows`、`role_scalar_bytes/_emit_scalar/_emit_fields`、`db_row_of`、`_sc_defined/_build_default_sc` (L3863–3917)、`partner_base_cfg`、`function_cfg`、`mall_cfg`、`mall_zhenbao`、`build_goods_list_sc12836`、`shop_pay_asset/shop_find_goods/shop_try_buy` (L4041–4128)、`mall_exchange`、`build_goods_list_sc12840`、`mission_def`、`decode_award_assets` | persistence / config / shop / mail / tree / rank / mingge / fabao / partner / reward |
| L4197 | `DB_PATH = .../state/roles.db` | persistence |
| L4220–4258 | `db_conn()` / `db_release(con)`（连接池/线程本地）、`ver_family_of(body_len, args)`、**`CUR_VER = '1.4.9'` (L4256)** | persistence / core |
| **L4274–4322** | **`db_init()`**：建 `roles / accounts / role_attr / missions / role_assets / mall_bought` 6 张表（其余表由各 `db_*_init()` 在建库时补） | persistence |
| L4325–5606 | 资产/任务/场景/角色辅助：`db_get_assets/db_add_assets`、`db_get_missions/db_save_mission`、`mission_chain`、`mon_cfg/mon_def/static_mons`、`quest_spawn()` (L4516)、`map_cfg`、`scene_elems/scene_npcs/scene_mons/scene_quest_extras`、`mission_progress_advance` (L4694)、`accept_mission_rows`、`mission_rows`、`db_get_attr/db_save_attr/db_get_role/db_save_role`、`db_account_ensure/db_roles_of_uid/db_create_role`、`_sc_to_db_updates`、`role_state(cfg)` (L5057)、`build_10302/10303/10301` (L5123–5330)、`_role_state_path/load_role_state/save_role_pos/role_with_saved_pos`、`build_mission_entry/build_12400/build_10201/build_mons/build_elems/build_npcs` | currency / task / scene / monster / role / attribute |
| L5328 | `STATE_DIR = .../state` | persistence |
| L5549 | `BAG_MAIN = 1` | inventory |
| L5607–6600 | `item_cfg/item_exists/item_name`、`level_table/max_lev/level_row/level_need/level_next_total/level_attr_point` (L5661–5723)、`db_set_assets`、**`add_role_exp(cfg, rid, amount, apply_attr_growth=True)` (L5743)**、`apply_level_attr_growth(rid, ups)` (L5785)、`drop_cfg/roll_drops` (L5805–5884)、`db_bag_init/db_bag_get/db_bag_add/db_bag_compact/db_bag_delete`、`can_buy_num`、`bag_push_frames/live_push_bag`、`db_mall_bought_add/db_mall_bought`、`db_init_bag_volume/db_get_bag_volume/db_set_bag_volume`、`db_init_equip/db_equip_all/db_equip_put/db_equip_take/equip_slot_for`、`db_store_init/db_store_get/db_store_add`、`db_init_levgift/db_get_levgift/db_add_levgift`、`db_dung_init/db_dung_get/db_dung_set/db_dung_list`、`db_arena_init/db_arena_state/db_arena_records/arena_pk_record_body/db_arena_opponents/arena_pk_show_body`、`richang_cfg/richang_daily_tasks`、`db_hero_init/db_hero_list/db_hero_add`、`partner_def`、`_hero_state`、`_attr_data/_attr_key2id/_attr_show_keys`、`db_form_init/db_form_get/db_form_set`、`db_buff_init/db_buff_list/cfg_buff_base/db_buff_set` | item / level / reward / inventory / shop / equipment / package / dungeon / ranking / task / partner / formation / buff |
| L6247 | `STORAGE_CODE = 4` | inventory |
| L6600–9200 | 成长族 DB 辅助：`db_fabao_*`、`db_shenqi_*`、`wing_upstar_seq`、`db_lingshou_*`、`db_yuanshen_*`、`db_mingge_*`、`db_chair_*`、`db_wing_*`、`db_moment_add/db_chat_add`、`db_has_guild/db_guild_init/db_guild_create`、`db_team_*`（L7454–7632）、`db_jiebai_*`（L7633–7767）、`db_marry_*/db_marry_propose_*`（L7768–7878）、`db_fashion_*`（L7879–7938）、`db_halo_*/db_halo_equip_*`（L7939–8005）、`auction_cfg/auction_price_assets_code/db_market_set`、`db_dung_enter`、`item_value/mall_good/db_set_role_name`、`db_invest_*/invest_type_list/invest_milestones`、`ride_cfg/db_ride_state/db_ride_set/ride_attr_values/ride_skills/ride_can_items`、`db_equip_get_one/db_equip_delete/equip_grid_size`、`db_rune_*/rune_up_cost/mingge_cfg/mingge_stage_init/rune_exchange_cost/rune_cfg/rune_exchange_rows`、`invest_cfg/invest_level_gate`、`db_equip_rows`、`db_peakwar_init/db_peakwar_state/db_race_init/db_race_state/race_rank_list`、`promote_tips/richang_activity_tasks/db_daily_*/chengjiu_cfg/db_chengjiu_*/chengjiu_map`、`credit_mission_done`、`db_guaji_*/guaji_spots/map_def_xy/guaji_spot_for_lev`、`bag_items_of/bag_take_one/bag_put_one`、`db_init_sign/db_sign_got/db_sign_add`、`db_bag_get_one/db_bag_set_quantity`、`build_equip_items/build_bag_items`、**`make_battle(cfg, mon)` (L9200)** | fashion / wing / artifact / soulbone / partner / formation / equipment / enhancement / social / guild / team / destiny / amplification / ranking / achievement / activity / afk / sign / battle |
| **L9243–18442** | **`class TcpHandler(socketserver.BaseRequestHandler)`** | session + 全部业务 handler |
| L9245–9308 | `_register_live / _unregister_live / handle(self)`（接收循环、FrameParser.feed、版本族 `CUR_VER`、调 `self._reply(cmd, body)`） | session |
| L9310–9588 | `_send_10200(bid)`（服务端推进场景）、战斗计时器 `_battle_interval/_battle_tick/_battle_kick/_battle_push_round/_battle_timer/_battle_settle`、`_send_12831` | scene / battle |
| **L9589–18442** | **`_reply(self, cmd, body)` —— 8,854 行顺序 `if cmd == N: ... return` 链**。开头心跳 1199 (L9591) / 10001 (L9632) / 1110 (L9637)；结尾 L18431–18440 全局兜底 `if CFG.get('global_default_sc') and _sc_defined(cmd):` | 全部业务 |
| L18442 | `cfg = DEFAULT_CFG`（类属性） | — |
| **L18445–18503** | **`main()`**：argparse、读 config.json、`db_init()` + `db_bag_init()` + `db_init_bag_volume()` + `db_init_equip()` + `db_store_init()` + `db_init_levgift()` + `db_init_sign()`、`Handler.cfg = cfg`、`TcpHandler.cfg = cfg`、`CFG.clear(); CFG.update(cfg)`、起 `ThreadingHTTPServer(8080)` 线程、起 `Srv(ThreadingTCPServer)(9000).serve_forever()` | 入口 |
| L18505–18506 | `if __name__ == '__main__': main()` | — |

### 1.2 _reply 命令分发区的系统分段（抽样锚点，来自 Grep）

> 以下锚点用于把 `_reply` 切成"系统片"。完整 800 命令分布见 *Capability* §二。

| 行号 | 命令 | 系统 |
|---|---|---|
| L9591 | 1199 心跳 | session |
| L9637 | 1110 登录 | account |
| L9676 | 10921 世界等级 | role |
| L9849 | 18909 | social |
| L9922 | 17100 魂师大赛 | battle/ranking |
| L9942 | 13901 充值 | shop |
| L9967 | 16900 | activity |
| L9983 | 21301 符文 | enhancement |
| L10089 | 15204 NPC | npc |
| L10107 | 19600 签到 | activity |
| L10277 | 13200 队伍 | social |
| L10539 | 18300 结婚 | social |
| L10814 | 19002 | social |
| L10883 | 18001 拍卖行 | shop |
| L11041 | 13004 副本 | dungeon |
| L11134–11176 | 30xxx 段（30104/30300/30400/30500/30701/30800/30900） | activity（老系统兼容层） |
| L11218–11301 | 17902/17700/17000/17400 跨服 | battle |
| L11393–11398 | 14203/14802 | activity |
| L11532 | 18020 拍卖行 | shop |
| L11643 | 12000 杂项 | role |
| L12059 | 10311 角色杂项 | role |
| L12263 | 10601 buff | attribute |
| L12369 | 10305 | role |
| L12670 | 19100 光环 | fashion |
| L12926 | 12601 爬塔 | dungeon |
| L13111/13122 | 18706 | social |
| L13202 | 10202 | scene |
| L13303 | 18400 | social |
| L13334 | 12414 交任务物品 | task |
| L13380 | 13801 充值 | shop |
| L13971 | 18900 法宝 | artifact |
| L14027 | 16200 | activity |
| L14041 | 11400 | partner |
| L14050 | 15801（设计不应答） | — |
| L14112 | 20800 | battle |
| L14130 | 11600 社交聊天 | social |
| L14170 | 30201 | activity |
| L14215 | 13500 | shop |
| L14251 | 18600 | social |
| L14426 | 17200 巅峰战 | battle |
| L14475 | 19400 | wing |
| L14701 | 21400 符文/魂星 | enhancement |
| L14744 | 16500 投资 | activity |
| L14771 | 18803 | social |
| L14801 | 14000 活动 | activity |
| L14887 | 13036 副本 | dungeon |
| L14974 | 13402 限购商店购买 | shop |
| L15035/15042 | 10514/10532 礼包 | reward |
| L15156 | 10101 建角 | account/role |
| L15183 | 10200 进场景 | scene |
| L15199 | 10201 场景格子 | scene |
| L15308 | 12400 任务列表 | task |
| L15325 | 10303 属性面板 | attribute |
| L15336 | 10302 货币 | currency |
| L15441 | 12901 排行 | ranking |
| L15470 | 14901 | activity |
| L15560/15584 | 15202/15203 NPC | npc |
| L15593 | 12402 接任务 | task |
| L15615 | 12403 交任务 | task |
| L15775 | 12831 商城 | shop |
| L15876 | 12840 珍宝 | shop |
| L15978/15985/16000 | 12801/12803/12805 商城 | shop |
| L16228 | 10301 角色 | role |
| L16283 | 14700 | activity |
| L16325 | 20100 养成/推广 | partner |
| L16370 | 10306 属性 | attribute |
| L16389 | 10304 属性+战力 | attribute/power |
| L16441 | 10300（仅触发补推） | role |
| L16546 | 10397（仅记录） | — |
| L16565 | 20002 开战 | battle |
| L16828 | 10505 礼包使用 | reward |
| L16889 | 10714 仓库 | inventory |
| L16923 | 14600 等级礼包 | package |
| L16982 | 11300 竞技场 | ranking |
| L17020 | 17301 竞速 | battle |
| L17073 | 17501 宗门战 | guild |
| L17083 | 11700 | partner |
| L17263 | 11200 伙伴 | partner |
| L17371 | 10800 邮件 | mail |
| L17428 | 10401 伙伴上阵 | partner |
| L17764 | 16400 成就 | achievement |
| L17803–17860 | 15405/15402/15403/15400 挂机 | afk |
| L18072 | 14100 | activity |
| L18138 | 17800 | battle |
| L18185 | 17600 宗门 | guild |
| L18253 | 30600 | activity |
| L18345 | 10502 背包查询 | inventory |
| L18397 | 20009 战斗选技 | battle |

### 1.3 周边模块职责（已独立成文件，软依赖）

| 模块 | 行数 | 导出 | 现状 |
|---|---|---|---|
| `server/power.py` | 3,732 B | `_load()` (L39)、`attr_power(key)` (L53)、`calc_power(attrs)` (L59)、`power_items(attrs, top_n=20)` (L78)；权重来自 `_attr_data.json`（原版权重 AttrPower，*Capability* #5 CONFIRMED） | **PowerService 雏形，已独立** |
| `server/battle.py` | 18,253 B | `w_u8/i8/u16/u32/i32/str`、`MON_STATS` (L104)、`KILL_REWARD` (L111)、`FALLBACK_DROPS` (L117)、`calc_damage(atk, defense)` (L127)、`class Fighter` (L143)、`class Battle` (L210) | 数值全 TEST_ONLY，需 MuMu 取证 |
| `server/aoi.py` | 19,062 B | `class Entity` (L48)、`class AOI` (L67) | 自研均匀网格 AOI，已被 `get_aoi()` (L310) 使用 |
| `server/pathfind.py` | 14,861 B | `class MapGrid` (L38)、`find_path` (L171)、`verify_path` (L263)、`class MoveRateLimiter` (L300) | 自研 A* + 路径校验 + 限流器 |
| `server/quest_spawn.py` | 7,091 B | `class QuestSpawn` (L70) | 任务刷怪 |
| `server/world/` | 12 文件 | `AreaManager / Scene / Instance / InstancePool / Area / TickScheduler / MessageService / Channel / ChannelService / ActionManager / MoveAction / validate_client_move / Item / Mob / Player` | **P1 骨架，未被 mock_server import**（见 `world/__init__.py` L1–31；属 jstm 引擎路线，Phase 2 暂不合并） |

### 1.4 全局状态耦合点（拆分时必须收敛）

| 全局 | 行号 | 用途 | 拆分后归宿 |
|---|---|---|---|
| `CFG` (dict) | L232, L18482 | 运行配置热改 | `core/config.py` 单例 |
| `LIVE_CONNECTIONS` / `LIVE_LOCK` | L233–234, L9245–9262 | 在线连接表（供热改推送） | `session/registry.py` |
| `CUR_VER` | L4256, L9298 | 当前连接的版本族（1.4.9/1.4.11） | `session/context.py` 每连接 |
| `DB_PATH` / `STATE_DIR` | L4197, L5328 | SQLite 路径 | `persistence/sqlite.py` |
| `BAG_MAIN=1` / `STORAGE_CODE=4` | L5549, L6247 | 背包编码 | `inventory/constants.py` |
| `DEFAULT_UID`（账号回退） | L4293 引用 | 老库无主角色回退 | `account/service.py` |
| `LIVE_LOCK` / `TcpHandler.lock` | L9264–9265 | 连接计数与广播 | `session/registry.py` |
| `battle_mod / aoi_mod / power_mod / pathfind_mod` | L34, L123, L128, L133 | 软依赖模块句柄 | 拆分后改硬 import |

---

## 二、目标架构：目录骨架 ↔ 现有代码映射

> 用户规定的目标骨架（38 个目录）。"迁移源"列给出现有 `mock_server.py` 的行号区间 / 周边模块 / 表 / 配置。"新建"= 现有代码无对应物。

| 目标模块 | 迁移源（行号 / 模块 / 表 / 配置） | 备注 |
|---|---|---|
| `core/` | L1–22 imports、L152–179 log/hexdump、L4220–4258 db_conn/db_release/ver_family_of、L9267–9308 handle() 接收循环 | 网络/线程/日志/版本族基础设施 |
| `core/protocol/` | L1589–1610 `w_u8/w_u16/w_u32/w_str/pack_frame`、L1611–1633 `FrameParser`、L1576 `CMD_NAMES`、L2008–2030 `_sc_fields`、L3120–3236 `_cs_fields/_sc_w/encode_by_sc_with_echo`、L3863–3917 `_sc_defined/_build_default_sc`、`proto_defs.py` (666KB)、`protocol/fields.json` (3553 条) | 帧编解码 + SC 规格注册表 |
| `core/session/` | L232–234 `CFG/LIVE_CONNECTIONS/LIVE_LOCK`、L469–662 `_scene_rid/_scene_enter/_scene_ensure/_scene_leave/_authoritative_pos/_scene_validate_move/_scene_apply_move/_scene_broadcast_10204/push_to_rid`、L9245–9308 `_register_live/_unregister_live/handle`、L9298 `CUR_VER` | 连接对象 / 在线注册表 / 每连接版本族 |
| `account/` | L9637–9668 `if cmd == 1110`、L1634–1748 `build_1110_roles`、L4969–5000 `db_account_ensure/db_roles_of_uid`、表 `accounts` (L4290)、`DEFAULT_UID` | 登录/多账号 |
| `role/` | L15151–15155 登角回包、L15156–15182 `10101` 建角、L4933–4968 `db_get_role/db_save_role`、L5035–5330 `_sc_to_db_updates/role_state/build_10301/10302/10303`、L16228–16282 `10301`、L16370–16388 `10306`、L16389–16440 `10304`、L16441–16545 `10300`、L16546–16564 `10397`、L12059 `10311`、L12369 `10305`、L11643 `12000`、L13380 `13801`、L8088 `db_set_role_name`、表 `roles` (L4277) | 角色主表 / 四件套 |
| `scene/` | L310–662 全部场景辅助、L9310–9381 `_send_10200`、L13202 `10202`、L15183–15198 `10200`、L15199–15284 `10201`、L15285–15307 `10204/10205`、`server/aoi.py`、`server/pathfind.py`、`map_block.json` (129KB)、`map_cfg()` (L4528)、`scene_elems/npcs/mons/quest_extras` (L4541–4693) | 场景/移动/AOI/寻路 |
| `npc/` | L15560 `15202`、L15584 `15203`、L10089/L10779 `15204`、`map_npc_bids()` (L2392)、`scene_npcs()` (L4564) | NPC 摆位/对话（UI 层客户端问题，见 *Capability* #41） |
| `task/` | L15308–15592 `12400/12402/12403`、L13334 `12414`、L13335–13379 `12415`、L4362–4464 `db_get_missions/db_save_mission/mission_chain`、L4694–4894 `mission_progress_advance/accept_mission_rows/mission_rows/build_mission_entry/build_12400`、L4159–4219 `mission_def/decode_award_assets`、L8881 `credit_mission_done`、表 `missions` (L4306)、`mission_config.json` (846 条) | 任务链/进度/提交 |
| `battle/` | L9382–9566 战斗计时器族、L16565–16827 `20002` 开战、L18397–18420 `20009` 选技、L9669–9675 `20021` ACK、L9922 `17100`、L14426 `17200`、L17020 `17301`、L18138 `17800`、L9200 `make_battle`、`server/battle.py` 全部、表 `arena_state/arena_record/peakwar_state/race_state` | 回合制战斗（数值 TEST_ONLY） |
| `monster/` | L4465–4515 `mon_cfg/mon_def/static_mons`、L4585–4639 `scene_mons`、L4640–4693 `scene_quest_extras`、L5805–5884 `drop_cfg/roll_drops`、L7028–7073 `boss_cfg/boss_rows`、L880 `/DSH_ADMIN/bosskill`、表 `role_boss_kill` | 怪物/BOSS |
| `level/` | L5661–5723 `level_table/max_lev/level_row/level_need/level_next_total/level_attr_point`、L5743–5784 `add_role_exp`、L5785–5804 `apply_level_attr_growth`、L1454 `/DSH_ADMIN/setlevel`、L709 `/DSH_ADMIN/getlevel`、`config.json` level 段 | 等级/经验 |
| `attribute/` | L56–120 `role_attr_dict/attr_table_10304/attr_table_10306`、L3447–3517 `db_role_attr/attr_row_bytes`、L4895–4932 `db_get_attr/db_save_attr`、L12263 `10601`、L6685–6720 `_attr_data/_attr_key2id/_attr_show_keys`、表 `role_attr` (L4295)、`_attr_data.json` | 24 项属性汇总（**已有收敛点，L56 docstring 自注 AttributeService 雏形**） |
| `power/` | L82–90 `role_power`、L2551–2561 `role_power_of(rid)`、L1067 `/DSH_ADMIN/power`、`server/power.py` 全部（`calc_power/power_items`）、`_attr_data.json` | 战力（原版权重 CONFIRMED） |
| `item/` | L180–249 `normalize_server_item`、L1778–1850 `item_ids/gift_contents/item_type_of/is_valid_item`、L5607–5660 `item_cfg/item_exists/item_name`、L8056–8087 `item_value/mall_good`、L9151–9199 `build_equip_items/build_bag_items`、`item_config.json` (3535 件)、`item_gift.json` (496 礼包) | 物品元数据 |
| `inventory/` | L5885–6067 `db_bag_init/db_bag_get/db_bag_add/db_bag_compact/db_bag_delete/can_buy_num/bag_push_frames/live_push_bag`、L6098–6150 `db_init_bag_volume/db_get_bag_volume/db_set_bag_volume`、L6250–6340 `db_store_init/db_store_get/db_store_add`、L9035–9150 `bag_items_of/bag_take_one/bag_put_one/db_bag_get_one/db_bag_set_quantity`、L18345–18396 `10502`、L16828–16888 `10505`、L16889–16922 `10714`、L790 `/DSH_ADMIN/addbag`、L1175 `/DSH_ADMIN/giveitem`、L1473 `/DSH_ADMIN/additem`、表 `bag_items/bag_volume/store_items` | 背包/仓库 |
| `equipment/` | L2539–2550 `equip_one`、L6151–6249 `db_init_equip/db_equip_all/db_equip_put/db_equip_take/equip_slot_for`、L8294–8337 `db_equip_get_one/db_equip_delete/equip_grid_size`、L8546–8568 `db_equip_rows`、L1231 `/DSH_ADMIN/setequip`、L1249 `/DSH_ADMIN/unequip`、L12640 `10573`、L12727 `10573`（时装/装备段）、表 `equip_items` | 装备穿脱 |
| `enhancement/` | L8338–8508 `db_rune_init/db_rune_lev/db_rune_set_lev/rune_up_cost/mingge_cfg/mingge_stage_init/rune_exchange_cost/rune_cfg/rune_exchange_rows`、L9983 `21301`、L14701 `21400`、`_rune_cfg.json` (1.7MB)、`_promote.json` | 强化/洗练/宝石/符文（数值 INFERENCE） |
| `skill/` | **新建**（*Capability* #13 UNKNOWN：命令扫描中未定位到技能学习/升级分支；战斗内 L18397 `20009` 选技） | Phase 2 仅建壳，不补功能 |
| `partner/` | L9689–9708 `11206`、L17263–17370 `11200`、L17428–17763 `10401`、L16982 `11300`、L17083 `11700`、L14041 `11400`、L16325–16369 `20100`、L6578–6684 `db_hero_init/db_hero_list/db_hero_add/partner_def/_hero_state`、L2753 `first_hero`、L3725–3761 `hero_partner_bytes`、L3918–3942 `partner_base_cfg`、L1029 `/DSH_ADMIN/hero`、L1258 `/DSH_ADMIN/setheros`、表 `role_heros/role_form`、`_partner_base.json` (53 个) | 伙伴/神将/上阵 |
| `wing/` | L7337–7371 `db_wing_state/db_wing_set`、L6933–6959 `wing_upstar_seq`、L953 `/DSH_ADMIN/wing`、L14130 `11600` 段附近、L14475 `19400`、表 `role_wing` | 翅膀 |
| `soulbone/` | **新建**（*Capability* #16 UNKNOWN：未定位到魂骨分支） | Phase 2 仅建壳 |
| `fashion/` | L7879–7938 `db_fashion_init/fashion_def/db_fashion_rows/db_fashion_get/db_fashion_upsert`、L7939–8005 `db_halo_init/db_halo_get/db_halo_set/db_halo_equip_rows/db_halo_equip_add/db_halo_equip_del`、L12670–12726 `19100`、L12727–12925 `10573–10578` 时装段、表 `role_fashion/role_halo/role_halo_equip` | 时装/光环 |
| `amplification/` | **新建**（*Capability* #18 UNKNOWN） | Phase 2 仅建壳 |
| `artifact/` | L3583–3630 `db_fabao_rows/fabao_list_bytes`、L6834–7003 `db_fabao_del/db_shenqi_*/db_fabao_one/db_fabao_update/wing_upstar_seq/db_fabao_list/db_fabao_add`、L13971–14026 `18900`、L869 `/DSH_ADMIN/fabao`、L924 `/DSH_ADMIN/shenqi`、表 `role_fabao/role_shenqi` | 法宝/神器 |
| `destiny/` | L2688–2735 `encode_mingge_list/db_mingge_one/db_mingge_del`、L7259–7301 `db_mingge_init/db_mingge_list/db_mingge_add`、L14476 `19400` 命格背包段、L934 `/DSH_ADMIN/mingge`、L8404–8441 `mingge_cfg/mingge_stage_init`、表 `role_mingge` | 命格 |
| `formation/` | L6721–6756 `db_form_init/db_form_get/db_form_set`、L1901 `FORMATION_BOOKS`、L18036 阵型属性汇总、L89 `/DSH_ADMIN/addbag` 阵法书、表 `role_form` | 阵法 |
| `dungeon/` | L2605–2687 `dungeon_cfg/dungeon_rows/encode_eqm_list/dung_progress_of`、L6378–6436 `db_dung_init/db_dung_get/db_dung_set/db_dung_list`、L8041–8055 `db_dung_enter`、L11041–11133 `13004`、L12926–13110 `12601`、L14887–14973 `13036`、表 `dungeon_progress` | 副本/爬塔 |
| `afk/` | L8917–9034 `db_guaji_init/db_guaji_state/db_guaji_update/db_guaji_get/db_guaji_set/guaji_spots/map_def_xy/guaji_spot_for_lev`、L17803–17948 `15400/15402/15403/15405`、L763 `/DSH_ADMIN/guaji`、L772 `/DSH_ADMIN/guaji_end`、表 `guaji_state`、`_guaji.json` | 挂机 |
| `shop/` | L2049–2248 `market_*`（摆摊）、L3959–4158 `mall_cfg/mall_zhenbao/build_goods_list_sc12836/shop_pay_asset/shop_find_goods/shop_try_buy/mall_exchange/build_goods_list_sc12840`、L6068–6097 `db_mall_bought_add/db_mall_bought`、L8006–8040 `auction_cfg/auction_price_assets_code/db_market_set`、L9942 `13901`、L10883 `18001`、L11532–11642 `18020/18021/18008/18024/18025`、L14215 `13500`、L14974–15034 `13402`、L15775–15977 `12831/12836/12840`、L15978–16000 `12801/12803/12805`、L838 `/DSH_ADMIN/marketgoods`、表 `mall_bought/role_market/role_market_goods`、`mall_config.json/mall_zhenbao.json/mall_exchange.json` | 商城/珍宝/摆摊/拍卖 |
| `currency/` | L4325–4361 `db_get_assets/db_add_assets`、L5724–5742 `db_set_assets`、L15336–15440 `10302`、L2516–2538 `asset_label_map`、L1387 `/DSH_ADMIN/setassets`、L1445 `/DSH_ADMIN/getassets`、表 `role_assets` (L4314) | 货币（钻石/银魂币/金魂币等 9 种） |
| `package/` | L6341–6377 `db_init_levgift/db_get_levgift/db_add_levgift`、L16923–16981 `14600`、L15035 `10514`、L15042 `10532`、L1208 `/DSH_ADMIN/givegift`、表 `levgift_got`、`item_gift.json` | 礼包/等级礼包 |
| `activity/` | L3943–3958 `function_cfg`、L6556–6577 `richang_cfg/richang_daily_tasks`、L8687–8717 `promote_tips/richang_activity_tasks`、L8718–8880 `db_daily_*/chengjiu_cfg/db_chengjiu_*/chengjiu_map`、L8104–8180 `db_invest_*/invest_type_list/invest_milestones`、L8509–8545 `invest_cfg/invest_level_gate`、L9090–9120 `db_init_sign/db_sign_got/db_sign_add`、L9967 `16900`、L10107 `19600`、L10143 `16300`、L10180 `16700`、L11393 `14203`、L11398 `14802`、L14744 `16500`、L14801 `14000`、L15470 `14901`、L16283 `14700`、L18072 `14100`、L18253 `30600`、L11134–11176 `30xxx` 段、L715 `/DSH_ADMIN/daily`、L741 `/DSH_ADMIN/chengjiu`、L964 `/DSH_ADMIN/invest`、表 `daily_progress/daily_lingqu/chengjiu_progress/sign_got/role_invest`、`_richang.json/_chengjiu.json/_invest_cfg.json/_dial_reward.json/config_checkin` | 日常/成就/签到/投资/节日活动 |
| `reward/` | L4164–4219 `decode_award_assets`、L5805–5884 `drop_cfg/roll_drops`、L5743–5784 `add_role_exp`、L9490 `KILL_REWARD`（battle.py）、L15035 `10514`、L15042 `10532`、L16828 `10505` | 奖励统一发放（幂等见 §六） |
| `social/` | L7372–7403 `db_moment_add/db_chat_add`、L14130–14169 `11600`、L14251–14425 `18600`、L10539–10778 `18300–18322` 结婚段、L10409 附近 `19505–19536` 结拜段、L9849 `18909`、L10814 `19002`、L10916 `18502`、L10929 `18100`、L10931 `18200`、L13111 `18706`、L13303 `18400`、L14771 `18803`、L13971 `18900` 段、表 `role_chat/role_moments/role_marry/role_marry_propose/role_jiebai` | 聊天/动态/结婚/结拜 |
| `guild/` | L2290–2335 `role_count/guild_rows`、L7404–7453 `db_has_guild/db_guild_init/db_guild_create`、L2249–2289 `db_build_state/db_build_set`、L2765–2849 `tree_cfg/tree_static/tree_worship_name/tree_max_lev/db_tree_state/db_tree_set`、L2957–3032 `qifu_pray_cfg/qifu_tiers/db_qifu_init/db_qifu_state/db_qifu_set`、L17073 `17501`、L18185 `17600`、L849 `/DSH_ADMIN/build`、L859 `/DSH_ADMIN/tree`、L996 `/DSH_ADMIN/qifu`、表 `role_guild/role_build/role_build_learn/role_tree/role_qifu` | 公会/建筑/摇钱树/祈福（本体多 0 行，见 *Capability* #33） |
| `ranking/` | L2850–2936 `_dedicated_cmds/rank_metric_value`、L2937–2956 `db_arena_trophy`、L3033–3119 `encode_rank_elem/encode_rank_reply`、L7004–7027 `self_rank_row`、L8569–8686 `db_peakwar_init/db_peakwar_state/db_race_init/db_race_state/race_rank_list`、L15441–15469 `12901`、L16982 `11300`、L7074–7092 `db_title_add`、L896 `/DSH_ADMIN/title`、表 `arena_state/arena_record/peakwar_state/race_state/role_title` | 排行榜/称号 |
| `mail/` | L2418–2483 `db_mail_init/db_mail_list/db_mail_add/db_mail_read`、L17371–17427 `10800–10810`、L830 `/DSH_ADMIN/mail`、表 `role_mail` (194 行) | 邮件 |
| `achievement/` | L8794–8880 `chengjiu_cfg/db_chengjiu_init/db_chengjiu_get/db_chengjiu_add/chengjiu_map`、L17764–17802 `16400`、L741 `/DSH_ADMIN/chengjiu`、表 `chengjiu_progress` (342 条配置) | 成就 |
| `gm/` | L663–1523 `class Handler.do_GET` 整段（44 个 `/DSH_ADMIN/*` 动作）、L1524–1588 `do_POST` | HTTP 管理面 |
| `persistence/` | L4220–4258 `db_conn/db_release`、L4274–4322 `db_init`、L4197 `DB_PATH`、L5328 `STATE_DIR`、所有 `db_*` 函数（L2030–9200 中约 200 个 db_*）、`state/roles.db` (376KB, 55 表) | SQLite 访问层 |
| `config/` | L138–149 `DEFAULT_CFG`、L232 `CFG`、L250–309 `_cfg_field_order/_cfg_dump`、L3237–3370 `kconst_*`、L3370–3446 `_kcfg_fields/_kcfg_row/kcfg_best_attr_table`、L3681–3710 `kcfg/kcfg_rows/kcfg_count`、L3762–3787 `kcfg2/kcfg2_rows`、L1342 `/DSH_ADMIN/reload`、`config.json`、`cfg/`(231)、`cfg_kconst/`(285)、`cfg_kconfig/`(245)、`cfg_kconfig2/`(245) | 运行配置 + 反构造配置表 |
| `tools/` | 根目录 `server/_fix_*.py`（20+ 个一次性修复脚本）、`gen_proto_defs.py`、`tools/extract_*.py`（在项目根 tools/） | 运维脚本（不拆） |
| `tests/` | `server/minloop/`（`min_loop_server.py` 83KB、`selftest.py` 43KB、`replay_real_frames.py`、`replay_stateful.py`）、`tests/1.4.9_regression.md`、`tests/run_stability_5.ps1` | 回归基座 |

> 注：`server/world/`（AreaManager/Scene/Instance/TickScheduler 等 P1 骨架）**不并入 Phase 2**——它未被 mock_server import，属独立 jstm 引擎路线，Phase 2 完成后再决定是否替换现有 `scene/`。

---

## 三、拆分策略（关键决策）

### 3.1 推荐：**"先建壳后搬家"（Build Shells First, Move Later）**

> **不推荐**"先搬家后拆壳"——那意味着在 8,854 行 if 链中间动刀，每刀都可能遮蔽/改语义，且当前实机取证在跑，server 必须稳。

**做法**：
1. **第一步（不动业务）**：在 `server/` 下新建目标目录骨架（38 个 `__init__.py` + 空模块），在 `mock_server.py` 顶部 import 一个新的 `dispatch.py`。
2. **第二步（兼容层）**：在 `_reply` 开头插入**优先查表**：
   ```python
   # 在 _reply(self, cmd, body) 的最开头（L9591 之前）
   handler = DISPATCH_TABLE.get(cmd)
   if handler is not None:
       try:
           return handler(self, cmd, body)
       except Exception as e:
           log('tcp.log', '  !! DISPATCH handler %d failed: %r' % (cmd, e))
           # 不 return，继续落到旧 if 链，保证可用性
   ```
   旧 if 链**原封不动保留**作为 fallback。
3. **第三步（逐系统搬运）**：每选一个系统（如 `attribute/`），把 L56–120、L3447–3517、L4895–4932、L12263 等相关函数与 if 块**复制**（不是剪切）到新模块，新模块里用 `@register(cmd)` 注册。复制后先在 DISPATCH_TABLE 里注册，跑 miniloop 145 自检 + 实机冒烟；通过后再把旧 `mock_server.py` 里的 if 块**注释掉**（不是删除），跑一周无回归后再物理删除。
4. **第四步（收敛全局状态）**：每个模块需要的全局（`CFG`/`LIVE_CONNECTIONS`/`db_conn`）通过 `core/runtime.py` 的单例访问器注入，不再 `from mock_server import *`。

### 3.2 为什么不是"先搬家后拆壳"

| 维度 | 先建壳后搬家（推荐） | 先搬家后拆壳 |
|---|---|---|
| 对运行中 server 的影响 | 零（新模块不注册就不生效） | 高（每搬一块都在动 if 链） |
| 回滚成本 | 删一行 `DISPATCH_TABLE[cmd]=...` 即回滚 | 需 git revert 整段 |
| 800 命令语义保证 | 未注册命令 100% 走旧路径，字节级一致 | 搬家过程中命令语义可能漂移 |
| 并行实机取证 | 取证流量走旧路径不受影响 | 取证流量与重构流量混在一起 |
| 模块边界 | 先有壳，搬运时自然归类 | 边搬边定边界，容易反复 |

### 3.3 兼容层设计（dispatch 表 + handler 注册表）

```python
# server/core/dispatch.py（新建）
DISPATCH_TABLE = {}  # cmd -> fn(handler_self, cmd, body)

def register(*cmds):
    def deco(fn):
        for c in cmds:
            DISPATCH_TABLE[c] = fn
        return fn
    return deco

# 用法（新模块内）：
# from core.dispatch import register
# @register(1110, 10102, 10103)
# def handle_login(h, cmd, body): ...
```

**硬规则**：
- handler 函数签名统一为 `fn(h: TcpHandler, cmd: int, body: bytes) -> None`；直接用 `h.request.sendall(pack_frame(cmd, out))` 发回，与现状一致。
- handler 内部需要的 DB/配置/推送，通过 `h`（TcpHandler 实例）上挂的新属性访问：`h.ctx.rid`、`h.services.currency`、`h.services.attribute` 等（见 §四）。
- **未注册的命令**：继续走旧 if 链，字节级行为不变。
- **已注册但 handler 抛异常**：catch 后**不 return**，落到旧 if 链兜底——保证永远有应答。
- 旧 `_UNSUPPORTED_ACTION_CMDS` / `_GENERIC_DEFAULT_CMDS` 仍为空 frozenset，`global_default_sc` 仍默认关——**Phase 2 不碰这三个开关**。

---

## 四、统一服务设计

### 4.1 服务注册与生命周期

在 `main()` (L18445) 里、`db_init()` 之后构造一组服务单例，挂到 `TcpHandler.services`：

```python
# server/core/services.py（新建）
class Services:
    def __init__(self, cfg):
        self.persistence = PersistenceService(cfg)        # 包 db_conn/db_init
        self.config = ConfigService(cfg)                  # 包 CFG/kconst/kcfg/kcfg2
        self.session = SessionRegistry()                  # 包 LIVE_CONNECTIONS
        self.attribute = AttributeService(self)           # 包 role_attr_dict
        self.power = PowerService(self)                   # 包 power.py
        self.currency = CurrencyService(self)             # 包 db_get_assets/db_add_assets
        self.reward = RewardService(self)                 # 包 decode_award_assets/roll_drops
        self.item = ItemService(self)                     # 包 item_config/gift_contents
        self.inventory = InventoryService(self)           # 包 db_bag_*
        self.mail = MailService(self)
        self.gm = GmService(self)                         # 包 /DSH_ADMIN 44 动作
```

### 4.2 五个核心服务接口签名草案

> 命名与现有函数对齐，避免二次翻译。所有方法默认 `rid: int` 首位。

#### AttributeService（`attribute/service.py`）

```python
class AttributeService:
    def get_attr_dict(self, rid: int) -> dict:
        """对应 L56 role_attr_dict(cfg)：合并 ATTR_DEFAULTS + cfg['role_attrs'] + DB role_attr。"""
    def get_attr_table_10304(self, rid: int) -> bytes:
        """对应 L99 attr_table_10304(ad)：4×u16 + 20×u32。"""
    def get_attr_table_10306(self, rid: int) -> bytes:
        """对应 L109 attr_table_10306(ad)：4×u16 + 12×u32 + 4×u16 + 4×u32。"""
    def apply_delta(self, rid: int, delta: dict) -> None:
        """成长系统（翅膀/时装/法宝…）追加属性加成，写 role_attr 表。
        ★ 红线：成长系统禁止自己算属性，必须走这里。"""
    def reload(self, rid: int) -> dict:
        """重算并返回最新属性（升级/穿脱装备后调）。"""
```

#### PowerService（`power/service.py`）

```python
class PowerService:
    def calc_power(self, attrs: dict) -> int:
        """对应 power.py:59 calc_power(attrs)，读 _attr_data.json 原版权重。"""
    def power_of(self, rid: int) -> int:
        """对应 L2551 role_power_of(rid)：取属性 → 算战力。"""
    def power_items(self, rid: int, top_n: int = 20) -> list:
        """对应 power.py:78 power_items(attrs, top_n)：战力明细（GM /DSH_ADMIN/power 用）。"""
```

#### CurrencyService（`currency/service.py`）

```python
class CurrencyService:
    CODES = {'gold': 1, 'coin': 2, 'coupon': 3, ...}   # 对应 asset_label_map (L2516)
    def get(self, rid: int) -> dict:
        """对应 L4325 db_get_assets(rid)。"""
    def add(self, rid: int, delta: dict, reference_id: str = '') -> bool:
        """对应 L4338 db_add_assets(rid, delta)；reference_id 幂等键见 §六。"""
    def spend(self, rid: int, need: dict, reference_id: str = '') -> bool:
        """扣费，余额不足返回 False。商城/礼包/强化走这里。"""
    def set(self, rid: int, values: dict) -> None:
        """对应 L5724 db_set_assets（GM /DSH_ADMIN/setassets 用）。"""
```

#### RewardService（`reward/service.py`）

```python
class RewardService:
    def decode_award(self, award_assets: str) -> list:
        """对应 L4164 decode_award_assets：解析 mission_config 的 award_assets 串。"""
    def grant(self, rid: int, awards: list, reference_id: str, source: str = '') -> dict:
        """统一发奖入口。awards=[{'type':'asset','code':'gold','num':100},
                              {'type':'item','bid':35001,'num':1}, ...]
        reference_id 幂等键；返回 {'granted': {...}, 'skipped': [...]}。"""
    def roll_drops(self, mon_bid: int) -> list:
        """对应 L5821 roll_drops(mon_bid)：杀怪掉落（当前 TEST_ONLY）。"""
```

#### ItemService（`item/service.py`）

```python
class ItemService:
    def cfg(self) -> dict:
        """对应 L5607 item_cfg()：item_config.json 3535 件。"""
    def exists(self, bid: int) -> bool: ...
    def name(self, bid: int) -> str: ...
    def type_of(self, bid: int) -> int: ...           # 对应 L1827 item_type_of
    def gift_contents(self, bid: int) -> list:       # 对应 L1807
    def normalize(self, s, cfg) -> dict:               # 对应 L180 normalize_server_item
```

### 4.3 power.py / battle.py 如何收敛

- **power.py** → 直接作为 `power/formula.py`，`PowerService.calc_power` 内部 `import power as f; return f.calc_power(attrs)`。**不重写权重公式**（原版权重 CONFIRMED，等 MuMu 取证 V9 后替换）。
- **battle.py** → 拆成 `battle/formula.py`（`calc_damage`/`MON_STATS`/`KILL_REWARD`/`FALLBACK_DROPS`，保持 TEST_ONLY 标注）+ `battle/session.py`（`Fighter`/`Battle` 回合状态机）。`TcpHandler` 里 L9382–9566 的 `_battle_*` 计时器族搬进 `battle/session.py`，由 `BattleSession` 自己 tick。
- **aoi.py / pathfind.py** → 原封不动作为 `scene/aoi.py` / `scene/pathfind.py`，`scene/service.py` 持有 `AOI` 单例与 `MapGrid` 表。

### 4.4 GM 修改链路示例（GM → Service → Persistence → ClientSync）

以 `/DSH_ADMIN/setlevel?lev=80`（L1454）为例：

```
HTTP GET /DSH_ADMIN/setlevel?lev=80&rid=1001
  → gm/handler.py: handle_setlevel(qs)
    → services.persistence.db_save_role(rid, level=80, exp=0)
    → services.level.on_level_changed(rid, new_level=80)
        → services.attribute.apply_delta(rid, level_attr_growth)   # 对应 L5785
        → services.power.power_of(rid)                              # 重算战力
    → services.session.push_to_rid(rid, pack_frame(10301, build_10301(...)))  # 推角色
    → services.session.push_to_rid(rid, pack_frame(10302, build_10302(...)))  # 推货币
    → services.session.push_to_rid(rid, pack_frame(10304, ...))              # 推属性+战力
    → log('logs/gm.log', 'setlevel rid=1001 -> 80 by DSH plugin')
```

**纪律**：GM 动作**禁止**直接写 SQL；必须走 Service；必须落 `logs/gm.log`；必须触发客户端同步推送。

---

## 五、数据层设计

### 5.1 55 张表 → 模块映射

| 模块 | 表 |
|---|---|
| `account/` | `accounts` |
| `role/` | `roles` |
| `attribute/` | `role_attr`、`role_point` |
| `currency/` | `role_assets` |
| `inventory/` | `bag_items`、`bag_volume`、`store_items` |
| `equipment/` | `equip_items` |
| `task/` | `missions` |
| `partner/` | `role_heros`、`role_form` |
| `wing/` | `role_wing` |
| `artifact/` | `role_fabao`、`role_shenqi` |
| `soulbone/` | `role_lingshou`（魂兽/灵兽，归这里；魂骨本体 UNKNOWN） |
| `destiny/` | `role_mingge` |
| `fashion/` | `role_fashion`、`role_halo`、`role_halo_equip` |
| `enhancement/` | `role_runes` |
| `amplification/` | （无表，新建占位） |
| `formation/` | `role_form`（与 partner 共用） |
| `dungeon/` | `dungeon_progress` |
| `afk/` | `guaji_state` |
| `shop/` | `mall_bought`、`role_market`、`role_market_goods` |
| `package/` | `levgift_got` |
| `activity/` | `daily_progress`、`daily_lingqu`、`sign_got`、`role_invest` |
| `achievement/` | `chengjiu_progress` |
| `social/` | `role_chat`、`role_moments`、`role_marry`、`role_marry_propose`、`role_jiebai`、`role_team`、`role_team_invite` |
| `guild/` | `role_guild`、`role_build`、`role_build_learn`、`role_tree`、`role_qifu` |
| `ranking/` | `arena_state`、`arena_record`、`peakwar_state`、`race_state`、`role_boss_kill`、`role_title` |
| `mail/` | `role_mail` |
| `battle/` | `role_buffs`（buff 表，当前 0 行） |
| `persistence/` | `sqlite_sequence`（自增主键表） |

> 表数量对齐 *Capability* §三：54 用户表 + 1 sqlite_sequence = 55。

### 5.2 Dirty State 保存策略

现状：每次 `db_add_assets` / `db_bag_add` 等函数**立即 `con.commit()`**（L4321 风格）。Phase 2 改为：

- **每连接/每请求事务**：一个 CS 命令（如 12403 交任务）在 Service 层组装一批写操作，最后由 `PersistenceService.commit()` 一次性提交。
- **Dirty 标记**：内存对象（role_state / bag / attr）在请求处理完标 `dirty=True`，由 `SessionContext` 在连接空闲时落库；**关键路径（发奖/扣费/买东西）仍然同步 commit**，保证崩溃不丢。
- **长事务红线**：单请求事务不超过 100ms；AOI 广播 / 战斗 tick 等异步路径不持 DB 锁。
- **SQLite 并发**：保留 `db_conn()` 线程本地连接池（L4220），写操作串行化由 SQLite WAL 负责（Phase 2 可开 `PRAGMA journal_mode=WAL`，但**不在本轮改**——等实机取证结束）。

### 5.3 logs/ 审计写入点

现状 `log(name, text)` (L152) 写 `server/logs/<name>.log`。Phase 2 固定 13 类日志：

| 日志文件 | 写入点 | 触发时机 |
|---|---|---|
| `logs/login.log` | `account/service.py` login() | 1110 登录成功/失败 |
| `logs/role.log` | `role/service.py` create/login/relogin | 10101/10102/10103 |
| `logs/battle.log` | `battle/session.py` start/settle | 20002 开战 / 20023 结算 |
| `logs/reward.log` | `reward/service.py` grant() | 任何发奖（含 reference_id） |
| `logs/currency.log` | `currency/service.py` add/spend | 任何货币变动 |
| `logs/inventory.log` | `inventory/service.py` add/delete/move | 背包增删 |
| `logs/equipment.log` | `equipment/service.py` put/take | 穿脱装备 |
| `logs/partner.log` | `partner/service.py` add/upstar | 伙伴操作 |
| `logs/task.log` | `task/service.py` accept/submit | 接交任务 |
| `logs/activity.log` | `activity/service.py` daily/chengjiu/sign | 日常/成就/签到 |
| `logs/gm.log` | `gm/handler.py` 每个动作 | 任何 /DSH_ADMIN/* |
| `logs/protocol.log` | `core/protocol.py` | 收发包（替代当前 tcp.log 全量） |
| `logs/error.log` | `core/runtime.py` 全局 except | 任何未捕获异常 |

> 现状 `logs/tcp.log`（全量 hex dump，体积巨大）在 Phase 2 降级为 debug 级别，生产默认关；`logs/protocol.log` 只记 cmd + rid + 关键 body 字段。

---

## 六、幂等性设计

### 6.1 现状

`mock_server.py` **没有幂等键**：网络重发（如客户端超时重发 12403 交任务）会导致重复发奖。这是已知漏洞，Phase 2 必须补。

### 6.2 三级幂等键

| 键 | 作用域 | 接入点 |
|---|---|---|
| `reference_id` | 业务级（发奖/买东西/交任务） | `RewardService.grant(rid, awards, reference_id)`、`CurrencyService.spend(rid, need, reference_id)`、`InventoryService.add(rid, bid, num, reference_id)` |
| `transaction_id` | 命令级（CS 帧带的唯一序列号） | `core/protocol.py` 解帧时从 body 提取（若协议有）；若无，则由客户端在 1110 登录后分配一个递增 seq，服务端记 `last_seen_seq[rid]` |
| `reward_id` | 奖励发放记录 | 新建表 `reward_log(rid, reference_id, reward_json, granted_at)`，主键 `(rid, reference_id)`；重复 grant 直接返回上次结果 |

### 6.3 接入策略

- **老命令兼容**：客户端不传 `reference_id` 时，由服务端用 `(cmd, rid, body_hash)` 生成一个确定性 ID，落 `reward_log`；重发同一 body 直接命中。
- **GM 动作**：`/DSH_ADMIN/*` 必须显式带 `?ref=gm-<timestamp>-<rid>`，否则拒绝。
- **战斗结算**：`20023` 结算帧的 `battle_uuid`（若协议有）作为 reference_id；无则用 `(rid, battle_start_ts)`。

---

## 七、迁移顺序（按依赖图）

> 每步必须 miniloop 145 自检 + 实机冒烟通过才进下一步。

| # | 步骤 | 内容 | 验收标准 |
|---|---|---|---|
| 0 | **实机取证冻结** | 等当前 MuMu 取证跑完，记录最后一份 tcp.log 基线 | 基线归档到 `analysis/_tmp/phase2_baseline_tcp.log` |
| 1 | **core / protocol / persistence / config** | 建壳：`core/`、`core/protocol/`、`persistence/`、`config/`、`core/dispatch.py`（DISPATCH_TABLE + register 装饰器）；在 `_reply` 开头插查表逻辑（§3.3）；旧 if 链不动 | 启动 server，800 命令全部走旧路径；miniloop 145/145 PASS；实机登录→进场景→走 12400 任务链一次无回归 |
| 2 | **session / account / role** | 搬 `LIVE_CONNECTIONS`、1110、10101、10102/10103、10301–10306；建 `SessionRegistry` | miniloop 145 PASS；实机登录→建角→登角→四件套推送与基线字节级 diff（允许日志行差异，SC 帧必须一致） |
| 3 | **attribute / power / level** | 搬 `role_attr_dict/role_power/attr_table_*`、`db_get_attr/db_save_attr`、`add_role_exp/apply_level_attr_growth`、`power.py`；建 `AttributeService/PowerService/LevelService`；GM setlevel 走新链路 | 10304 战力值与基线完全一致；/DSH_ADMIN/setlevel 后客户端四件套刷新正常 |
| 4 | **currency / reward / item** | 搬 `db_get_assets/db_add_assets/db_set_assets`、`decode_award_assets/roll_drops`、`item_cfg/item_exists`；建三级幂等表 `reward_log` | 杀怪一次金币数与基线一致；重发 12403 不重复发奖；/DSH_ADMIN/giveitem 生效 |
| 5 | **inventory / equipment / package** | 搬 `db_bag_*/db_equip_*/db_store_*/db_levgift_*`；10502/10505/10714/14600 | 背包查询帧与基线一致；穿脱装备后 10304 属性差与基线一致 |
| 6 | **task / npc / monster / afk** | 搬 12400/12402/12403/12414/12415、15202/15203/15204、`mon_cfg/static_mons/scene_mons`、15400–15405 | miniloop 任务链全过；挂机轮次推进正常 |
| 7 | **scene / battle** | 搬 10200/10201/10204/10205、`_send_10200`、`_battle_*` 计时器族、`battle.py`；aoi/pathfind 原封迁入 | 进场景帧与基线一致；一场战斗 20010/20012/20013/20020/20023 字节级 diff 为空 |
| 8 | **partner / wing / fashion / artifact / destiny / formation / enhancement** | 搬成长族 DB 函数与对应命令段 | 每个成长系统穿/升一阶后，10304 属性差与基线一致；/DSH_ADMIN/fabao/wing/mingge 等发放生效 |
| 9 | **shop / activity / achievement / mail / ranking / social / guild / dungeon** | 搬商城/活动/成就/邮件/排行/社交/公会/副本 | 商城购买扣币+发货一致；邮件收发一致；排行榜返回与基线一致 |
| 10 | **gm / tools / tests** | 把 44 个 /DSH_ADMIN 动作迁入 `gm/handler.py`，全部走 Service；旧 `mock_server.py` if 链物理删除 | 44 个 GM 动作逐个 curl 测一遍，返回与基线一致；最终 `mock_server.py` 缩到只剩 `main()` + import |
| 11 | **tests/1.4.11/ 补全** | 见 §八 | 实机全场景冒烟通过 |

> 依赖原则：**被依赖者先搬**。core → persistence → config → attribute/power → currency/reward → 其余业务系统。

---

## 八、回归策略（保证 1.4.11 实机仍跑通）

### 8.1 回归基座三层

| 层 | 工具 | 位置 | 用途 |
|---|---|---|---|
| L1 单元 | miniloop selftest | `server/minloop/selftest.py`（145 项） | 每步迁移后必跑；验 SC 结构严格合规格 |
| L2 回放 | replay_real_frames / replay_stateful | `server/minloop/replay_real_frames.py`、`replay_stateful.py` | 用 Phase 0 抓到的真机帧回放，对比新旧 server 的 SC 字节 |
| L3 实机 | MuMu 12 + 1.4.11 补丁包 | `D:\MuMuPlayer` + `patched/jstm_1411_fakelogin_aligned.apk` | 最终验收：登录→建角→进场景→打怪→交任务→买东西→发邮件全流程 |

### 8.2 `tests/1.4.11/` 结构（新建）

```
tests/1.4.11/
  baseline_tcp.log          # Phase 2 冻结前抓的最后一份全量 tcp.log
  baseline_frames.jsonl     # 从 baseline_tcp.log 解析出的 (cmd, sc_bytes) 列表
  diff_report.md            # 每步迁移后生成：新 server 跑同一客户端流程，SC 字节 diff
  smoke_flow.md             # 实机冒烟脚本：登录→10200→12400→20002→12403→12801→10800
  run_smoke.ps1             # 启动 server + adb 启动客户端 + 抓 logcat + 对比 baseline
```

### 8.3 每步验收清单

1. `python server/minloop/selftest.py` → 145/145 PASS（用 tempfile，不碰 minloop.db）。
2. `python server/minloop/replay_real_frames.py --baseline analysis/_tmp/phase2_baseline_tcp.log` → SC 帧 diff 为空（日志行差异可忽略）。
3. 实机冒烟：MuMu 启动 1.4.11 → 登录 → 走到与 baseline 相同的 UI 屏 → 截图对比。
4. `/DSH_ADMIN/status` 一次拉全状态，与基线 JSON diff。
5. 若任一步失败：`git checkout server/mock_server.py`（或删除对应 `DISPATCH_TABLE` 注册行），回滚后再分析。

---

## 九、风险清单

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | **单文件全局状态耦合**：`mock_server.py` 有 200+ 个 `db_*` 函数互相调用，且大量直接读写模块级 `CFG` / `LIVE_CONNECTIONS` / `CUR_VER`；新模块若 `from mock_server import *` 会形成循环 import | 高 | 禁止 `import mock_server`；所有全局通过 `core/runtime.py` 的单例访问器注入；`mock_server.py` 最终只保留 `main()` 作为入口壳 |
| 2 | **if 链遮蔽**：*Capability* §八提到历史上出现过"前面 if cmd in (11216) 遮蔽后面真正写库的 11216"；迁移时若漏删旧 if 块，新 handler 会被遮蔽 | 高 | DISPATCH_TABLE 在 `_reply` **最开头**查表，已注册命令不走到旧 if 块；每步迁移后用 `tools/lint_dispatch_shadow.py`（现有）扫一遍遮蔽 |
| 3 | **SQLite 55 表 schema 漂移**：`db_init()` (L4274) 只建 6 张表，其余 49 张由各 `db_*_init()` 在 `main()` 里零散建（L18460–18470）；搬迁时若漏搬某个 `db_*_init`，新库起不来 | 高 | Phase 2 第一步先建 `persistence/schema.py`，把所有 `CREATE TABLE IF NOT EXISTS` 集中；用 `server/_db_schema.py`（现有）导出当前 roles.db schema 作为黄金文件，启动时比对 |
| 4 | **版本族字节级差异**：`CUR_VER` (L4256) 控制 build_* 按 1.4.9/1.4.11 产出不同字段布局；搬迁时若把 `build_10301/10302/10303/10304` 搬错版本分支，客户端直接崩 | 高 | 每个 build_* 函数搬迁后必须用 `replay_real_frames.py` 对比两版本的 baseline 帧；版本族判定 `ver_family_of()` (L4259) 原封不动搬到 `core/protocol.py` |
| 5 | **战斗计时器线程安全**：`_battle_tick/_battle_kick/_battle_settle` (L9390–9566) 是 `threading.Timer` 驱动的异步回调，持有 `self._battle_*` 状态；搬到 `battle/session.py` 后跨线程访问 `TcpHandler.request` 可能抛 socket 异常 | 中 | `BattleSession` 与 `TcpHandler` 解耦：session 只产出 SC 帧字节，通过 `SessionRegistry.push_to_rid(rid, pkt)` 投递；timer 回调里不直接碰 socket |
| 6 | **编码历史包袱**：文件里大量 `R42/R48/R50/R150/R190/R230` 注释说明"为什么这段代码长这样"（如 L9692 的 11216 遮蔽史、L18425 的 global_default_sc 位置史）；搬迁时若不读注释直接复制，会把历史 workaround 也复制过去 | 中 | 每个函数搬迁时把注释一起带走；在新模块 docstring 里标注"原 mock_server.py Lxxxx，R 系列修复史"；不擅自"清理" workaround |
| 7 | **实机取证干扰**：当前 MuMu 取证在跑，Phase 2 若同时改 server，取证数据会污染 | 中 | Phase 2 第一步（建壳+插 dispatch 查表）必须在取证冻结后做；未注册的命令 100% 走旧路径，取证流量不受影响；建议取证期间只动 `analysis/`，不动 `server/` |
| 8 | **配置热重载**：`/DSH_ADMIN/reload` (L1342) 会重新读 config.json；搬迁后若 `ConfigService` 不是单例，热重载不生效 | 中 | `ConfigService` 做线程安全单例；`reload()` 方法重建内部 dict 并广播给所有在线 session |
| 9 | **AOI 广播性能**：`push_to_rid` (L640) 遍历 `LIVE_CONNECTIONS`；搬到 session/registry.py 后若不加分组，跨场景广播会 O(N) | 低 | Phase 2 不优化性能，只搬结构；分组留到 Phase 3 |
| 10 | **未知系统（魂骨/增幅/技能/公会本体）**：*Capability* C 组 11 个 UNKNOWN；Phase 2 建空壳但不补功能，可能被误读为"已实现" | 低 | 空壳模块 docstring 顶部标 `# PLACEHOLDER: not implemented, see Capability §6.1.C`；GM /status 里这些系统返回空表并注明 |

---

## 十、Phase 2 边界声明

**本轮做**：
- 拆目录、建 dispatch 兼容层、搬 core/persistence/config/session/account/role/attribute/power/currency/reward/item/inventory/equipment/task/battle（即 §七 步骤 1–7）。
- 其余业务系统（成长族/社交/商城/活动/GM）在步骤 8–10 搬，但**不改任何数值**。

**本轮不做**：
- 不补 UNKNOWN 系统（魂骨/增幅/技能学习/公会本体）。
- 不优化性能（GIL / WAL / AOI 分组）。
- 不替换 TEST_ONLY 数值（等 MuMu 取证 V1–V12）。
- 不动 `server/world/`（jstm 引擎路线独立评估）。
- 不改协议字段、不改命令号、不改 SC 布局。

---

*设计文档完。所有行号基于 2026-10-02 快照的 `server/mock_server.py`（18,506 行）。*
