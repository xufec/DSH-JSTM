# 《绝世唐门》PHASE C0 界面与功能清单

> 目标版本：1.4.11 ｜ 条目数：**391** ｜ 生成脚本：`tools/jstm_audit/gen_ui_inventory.py`
> 状态分布：**A=18 / B=338 / C=27 / D=8**

## 四类状态定义

- **A 已实际验证**：有实机/本地运行证据，见 evidence 字段
- **B 资源与模块均存在、尚未运行验证**：ui_by_module 有文件 + res_categories 有资源
- **C 仅图标/字符串证据**：模块缺失或极弱（本批骨架未触发）
- **D 疑似废弃/被版本替换**：1.4.11 缺失，diff 证据

## 按系统分组

### SYS_ACT_001 · Sign-in 签到  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| dailysign panel | dailysign | `assets/src/game/dailysign/dailysign_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['dailysign'] (apk_scan_1_4_11.json) |
| seven day view | dailysign | `assets/src/game/dailysign/seven_day_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['dailysign'] (apk_scan_1_4_11.json) |
| day login panel | dailysign | `assets/src/game/dailysign/day_login_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['dailysign'] (apk_scan_1_4_11.json) |
| daily reward view | dailysign | `assets/src/game/dailysign/daily_reward_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['dailysign'] (apk_scan_1_4_11.json) |

### SYS_ACT_003 · Invest 投资  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| invest panel | invest | `assets/src/game/invest/invest_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['invest'] (apk_scan_1_4_11.json) |
| invest sec panel | invest | `assets/src/game/invest/invest_sec_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['invest'] (apk_scan_1_4_11.json) |
| 运营活动-投资_sec (invest_sec) | invest_sec | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='投资_sec' name='invest_sec'；1.4.11 ui_by_module 无独立 'invest_se |

### SYS_ACT_004 · Turntable 转盘  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| rotatetable panel | rotatetable | `assets/src/game/rotatetable/rotatetable_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['rotatetable'] (apk_scan_1_4_11.json) |
| turntable ctrl | turntable | `assets/src/game/turntable/turntable_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['turntable'] (apk_scan_1_4_11.json) |
| 运营活动-奖池转盘 (jiangchi) | jiangchi | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='奖池转盘' name='jiangchi'；1.4.11 ui_by_module 无独立 'jiangchi' 模块， |
| 运营活动-幸运转盘 (lucky_turntable) | lucky_turntable | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='幸运转盘' name='lucky_turntable'；1.4.11 ui_by_module 无独立 'lucky_ |

### SYS_ACT_005 · Scratch Card 刮刮乐  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| scratcher ctrl | scratcher | `assets/src/game/scratcher/scratcher_ctrl.luac` | **A** | 是 | CS_16651,CS_16652 | tests/1.4.11/NEW_SYSTEMS_REGRESSION.md §一 (16651/16652 ALL PASS) ; PHASE2_14_SCRATCH.md |

### SYS_ACT_006 · Operation Activity 节日/运营活动  (51 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| action panel | action | `assets/src/game/action/action_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action attention view | action | `assets/src/game/action/action_attention_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action base view | action | `assets/src/game/action/action_base_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action breakeggs panel | action | `assets/src/game/action/action_breakeggs_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action buy view | action | `assets/src/game/action/action_buy_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action card view | action | `assets/src/game/action/action_card_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action cash view | action | `assets/src/game/action/action_cash_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action desc view | action | `assets/src/game/action/action_desc_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action discount panel | action | `assets/src/game/action/action_discount_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action double view | action | `assets/src/game/action/action_double_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action doublemoney panel | action | `assets/src/game/action/action_doublemoney_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action dragontreasure panel | action | `assets/src/game/action/action_dragontreasure_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action exchange view | action | `assets/src/game/action/action_exchange_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action exshop view | action | `assets/src/game/action/action_exshop_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action get reward panel | action | `assets/src/game/action/action_get_reward_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action gift back panel | action | `assets/src/game/action/action_gift_back_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action goldentower panel | action | `assets/src/game/action/action_goldentower_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action halloween panel | action | `assets/src/game/action/action_halloween_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action hero view | action | `assets/src/game/action/action_hero_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action jubaodz view | action | `assets/src/game/action/action_jubaodz_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| luckbox left view | action | `assets/src/game/action/luckbox_left_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action letter panel | action | `assets/src/game/action/action_letter_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action login view | action | `assets/src/game/action/action_login_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action love rank view | action | `assets/src/game/action/action_love_rank_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action luckday view | action | `assets/src/game/action/action_luckday_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action money buy view | action | `assets/src/game/action/action_money_buy_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action new show panel | action | `assets/src/game/action/action_new_show_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action paper panel | action | `assets/src/game/action/action_paper_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| sky present panel | action | `assets/src/game/action/sky_present_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action rank panel | action | `assets/src/game/action/action_rank_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action recharge view | action | `assets/src/game/action/action_recharge_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action refresh zhuan panel | action | `assets/src/game/action/action_refresh_zhuan_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action reputation view | action | `assets/src/game/action/action_reputation_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action reward view | action | `assets/src/game/action/action_reward_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action ride luck view | action | `assets/src/game/action/action_ride_luck_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action secret panel | action | `assets/src/game/action/action_secret_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action self select panel | action | `assets/src/game/action/action_self_select_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action shengdian panel | action | `assets/src/game/action/action_shengdian_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action shouji panel | action | `assets/src/game/action/action_shouji_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action super vip panel | action | `assets/src/game/action/action_super_vip_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action treasure buy panel | action | `assets/src/game/action/action_treasure_buy_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action turntable panel | action | `assets/src/game/action/action_turntable_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action wall panel | action | `assets/src/game/action/action_wall_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| action zhuan panel | action | `assets/src/game/action/action_zhuan_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['action'] (apk_scan_1_4_11.json) |
| activity ctrl | activity | `assets/src/game/activity/activity_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['activity'] (apk_scan_1_4_11.json) |
| flyup gift panel | flyup | `assets/src/game/flyup/flyup_gift_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['flyup'] (apk_scan_1_4_11.json) |
| flyup main panel | flyup | `assets/src/game/flyup/flyup_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['flyup'] (apk_scan_1_4_11.json) |
| jubaopen ctrl | jubaopen | `assets/src/game/jubaopen/jubaopen_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['jubaopen'] (apk_scan_1_4_11.json) |
| 运营活动-奖励 (reward) | reward | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='奖励' name='reward'；1.4.11 ui_by_module 无独立 'reward' 模块，由 acti |
| 运营活动-幸运宝箱 (luckbox) | luckbox | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='幸运宝箱' name='luckbox'；1.4.11 ui_by_module 无独立 'luckbox' 模块，由  |
| 运营活动-幸运翻牌 (xingyunfanpai) | xingyunfanpai | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='幸运翻牌' name='xingyunfanpai'；1.4.11 ui_by_module 无独立 'xingyunf |

### SYS_ACT_007 · Answer Quiz 答题(活动版)  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| actionanswer panel | actionanswer | `assets/src/game/actionanswer/actionanswer_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['actionanswer'] (apk_scan_1_4_11.json) |
| answer guess panel | answer | `assets/src/game/answer/answer_guess_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['answer'] (apk_scan_1_4_11.json) |
| answer panel | answer | `assets/src/game/answer/answer_panel.luac` | **A** | 是 | CS_16100,CS_16101,CS_16102… | tests/1.4.11/NEW_SYSTEMS_REGRESSION.md §一 (16100~16103 客户端回归 ALL PASS) ; PHASE2_12_ANSWER_QUIZ.md |

### SYS_ACT_008 · Operation Activity  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-竞猜 (guess) | guess | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='竞猜' name='guess'；1.4.11 ui_by_module 无独立 'guess' 模块，由 activi |

### SYS_ACT_009 · Money Tree  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| moneytree (1.3.0 已移除) | moneytree | `assets/src/game/moneytree/ (1.3.0 only, 1.4.11 缺失)` | **D** | 否 | UNKNOWN | diff.game_modules_only_in_1.3.0 含 'moneytree'；version_compare/1.3.0/extracted/game/moneytree/ 下有 ctrl/data/view 文件 |

### SYS_ACT_010 · Operation Activity  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-祈福墙 (zhufuqiang) | zhufuqiang | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='祈福墙' name='zhufuqiang'；1.4.11 ui_by_module 无独立 'zhufuqiang'  |

### SYS_ACT_011 · Treasure 夺宝  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| treasure ctrl | treasure | `assets/src/game/treasure/treasure_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['treasure'] (apk_scan_1_4_11.json) |
| 运营活动-一元夺宝 (duobao) | duobao | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='一元夺宝' name='duobao'；1.4.11 ui_by_module 无独立 'duobao' 模块，由 ac |

### SYS_ACT_012 · Return/Back Flow 回归  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| fb bind panel | friendback | `assets/src/game/friendback/fb_bind_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['friendback'] (apk_scan_1_4_11.json) |
| fb main panel | friendback | `assets/src/game/friendback/fb_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['friendback'] (apk_scan_1_4_11.json) |
| fb tips panel | friendback | `assets/src/game/friendback/fb_tips_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['friendback'] (apk_scan_1_4_11.json) |
| 运营活动-老玩家回归 (recruit) | recruit | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='老玩家回归' name='recruit'；1.4.11 ui_by_module 无独立 'recruit' 模块，由 |

### SYS_ACT_013 · Operation Activity  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-飞升返利礼包 (flyUp_gift) | flyUp_gift | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='飞升返利礼包' name='flyUp_gift'；1.4.11 ui_by_module 无独立 'flyUp_gif |
| 运营活动-充值翻倍 (charge_double) | charge_double | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='充值翻倍' name='charge_double'；1.4.11 ui_by_module 无独立 'charge_d |

### SYS_APPEAR_001 · Wing/Footmark 足迹  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| footmark ctrl | footmark | `assets/src/game/footmark/footmark_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['footmark'] (apk_scan_1_4_11.json) |
| wing fashion star panel | wing | `assets/src/game/wing/wing_fashion_star_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['wing'] (apk_scan_1_4_11.json) |

### SYS_APPEAR_002 · Mount 坐骑  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| horse eat panel | horse | `assets/src/game/horse/horse_eat_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['horse'] (apk_scan_1_4_11.json) |
| horse fashion panel | horse | `assets/src/game/horse/horse_fashion_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['horse'] (apk_scan_1_4_11.json) |
| horse info panel | horse | `assets/src/game/horse/horse_info_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['horse'] (apk_scan_1_4_11.json) |
| horse state panel | horse | `assets/src/game/horse/horse_state_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['horse'] (apk_scan_1_4_11.json) |

### SYS_APPEAR_003 · Beast 灵兽  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| beast eat panel | beast | `assets/src/game/beast/beast_eat_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['beast'] (apk_scan_1_4_11.json) |
| beast info panel | beast | `assets/src/game/beast/beast_info_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['beast'] (apk_scan_1_4_11.json) |
| beast migration panel | beast | `assets/src/game/beast/beast_migration_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['beast'] (apk_scan_1_4_11.json) |
| beast state panel | beast | `assets/src/game/beast/beast_state_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['beast'] (apk_scan_1_4_11.json) |

### SYS_APPEAR_004 · Yuanshen 元神  (8 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| yuanshen panel | yuanshen | `assets/src/game/yuanshen/yuanshen_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |
| yuanshen gain view | yuanshen | `assets/src/game/yuanshen/yuanshen_gain_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |
| yuanshen gongming panel | yuanshen | `assets/src/game/yuanshen/yuanshen_gongming_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |
| yuanshen handbook view | yuanshen | `assets/src/game/yuanshen/yuanshen_handbook_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |
| yuanshen mingpan view | yuanshen | `assets/src/game/yuanshen/yuanshen_mingpan_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |
| yuanshen pack view | yuanshen | `assets/src/game/yuanshen/yuanshen_pack_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |
| yuanshen show view | yuanshen | `assets/src/game/yuanshen/yuanshen_show_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |
| yuanshen soul view | yuanshen | `assets/src/game/yuanshen/yuanshen_soul_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuanshen'] (apk_scan_1_4_11.json) |

### SYS_APPEAR_005 · Divine Artifact 神器  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| artifact info panel | artifact | `assets/src/game/artifact/artifact_info_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['artifact'] (apk_scan_1_4_11.json) |
| artifact main ui | artifact | `assets/src/game/artifact/artifact_main_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['artifact'] (apk_scan_1_4_11.json) |
| artifact state panel | artifact | `assets/src/game/artifact/artifact_state_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['artifact'] (apk_scan_1_4_11.json) |

### SYS_APPEAR_008 · Chair/座驾(cook/cut/forge/mojo UI)  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| build ctrl | build | `assets/src/game/build/build_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['build'] (apk_scan_1_4_11.json) |
| chair ctrl | chair | `assets/src/game/chair/chair_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['chair'] (apk_scan_1_4_11.json) |

### SYS_APPEAR_009 · Fashion/Skin 时装(动画装备)  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| animaequip ctrl | animaequip | `assets/src/game/animaequip/animaequip_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['animaequip'] (apk_scan_1_4_11.json) |

### SYS_APPEAR_010 · Halo 光环  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| halo ctrl | halo | `assets/src/game/halo/halo_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['halo'] (apk_scan_1_4_11.json) |

### SYS_BACK_001 · Config Tables 配置表  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| config arena data | config | `assets/src/game/config/config_arena_data.luac` | **B** | 否 | UNKNOWN | ui_by_module['config'] (apk_scan_1_4_11.json) |

### SYS_BATTLE_001 · Turn-based Battle 回合制战斗  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| battle ctrl | battle | `assets/src/game/battle/battle_ctrl.luac` | **A** | 是 | SC_20010 BattleStart,SC_20013 BattleRound,SC_20020 BattleEnd | runtime_findings.md §D3 (20010 mon_hp=2400, 20013 回合 hit) ; tcp.log L1169-1236 |

### SYS_BATTLE_002 · Auto-battle/AFK 挂机  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| automate panel | automate | `assets/src/game/automate/automate_panel.luac` | **A** | 是 | CS_15400/15402/15405 挂机族 | extraction/ui_display_values.md §5 ; shots/uival_19_guaji.png, afk_05_afkpanel.png |

### SYS_BATTLE_003 · Battle Replay 战报  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| battlevideo main panel | battlevideo | `assets/src/game/battlevideo/battlevideo_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['battlevideo'] (apk_scan_1_4_11.json) |

### SYS_BATTLE_004 · God War 帝国战  (13 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| mount result panel | diguowar | `assets/src/game/diguowar/mount_result_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['diguowar'] (apk_scan_1_4_11.json) |
| godwar panel | godwar | `assets/src/game/godwar/godwar_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar battle result panel | godwar | `assets/src/game/godwar/godwar_battle_result_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar hall ui | godwar | `assets/src/game/godwar/godwar_hall_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar msg view | godwar | `assets/src/game/godwar/godwar_msg_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar plan view | godwar | `assets/src/game/godwar/godwar_plan_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar reward panel | godwar | `assets/src/game/godwar/godwar_reward_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar rule view | godwar | `assets/src/game/godwar/godwar_rule_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar side ui | godwar | `assets/src/game/godwar/godwar_side_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| godwar team check panel | godwar | `assets/src/game/godwar/godwar_team_check_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['godwar'] (apk_scan_1_4_11.json) |
| xianmo ctrl | xianmo | `assets/src/game/xianmo/xianmo_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['xianmo'] (apk_scan_1_4_11.json) |
| 运营活动-众神联赛场景 (godwarscene) | godwarscene | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='众神联赛场景' name='godwarscene'；1.4.11 ui_by_module 无独立 'godwarsc |
| 运营活动-跨服仙魔 (kuafu_xianmo) | kuafu_xianmo | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='跨服仙魔' name='kuafu_xianmo'；1.4.11 ui_by_module 无独立 'kuafu_xia |

### SYS_BATTLE_005 · Boss System BOSS  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| boss ctrl | boss | `assets/src/game/boss/boss_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['boss'] (apk_scan_1_4_11.json) |

### SYS_COMM_001 · Rank 排行榜  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| linshi rank panel | rank | `assets/src/game/rank/linshi_rank_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['rank'] (apk_scan_1_4_11.json) |
| 运营活动-新消耗排行榜 (xfphb) | xfphb | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='新消耗排行榜' name='xfphb'；1.4.11 ui_by_module 无独立 'xfphb' 模块，由 ac |
| 运营活动-新充值排行榜 (czphb) | czphb | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='新充值排行榜' name='czphb'；1.4.11 ui_by_module 无独立 'czphb' 模块，由 ac |
| 运营活动-活动排行榜 (actionrank) | actionrank | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='活动排行榜' name='actionrank'；1.4.11 ui_by_module 无独立 'actionrank |

### SYS_COMM_002 · Arena 竞技场  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| arena panel | arena | `assets/src/game/arena/arena_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['arena'] (apk_scan_1_4_11.json) |

### SYS_COMM_003 · Peakwar 巅峰战  (14 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| peakwar ctrl | peakwar | `assets/src/game/peakwar/peakwar_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar award ui | peakwar | `assets/src/game/peakwar/pwar_award_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar box panel | peakwar | `assets/src/game/peakwar/pwar_box_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar grade ui | peakwar | `assets/src/game/peakwar/pwar_grade_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar group ui | peakwar | `assets/src/game/peakwar/pwar_group_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar hall ui | peakwar | `assets/src/game/peakwar/pwar_hall_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar main ui | peakwar | `assets/src/game/peakwar/pwar_main_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar rank panel | peakwar | `assets/src/game/peakwar/pwar_rank_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar record info ui | peakwar | `assets/src/game/peakwar/pwar_record_info_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar result ui | peakwar | `assets/src/game/peakwar/pwar_result_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar side ui | peakwar | `assets/src/game/peakwar/pwar_side_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar upgrade ui | peakwar | `assets/src/game/peakwar/pwar_upgrade_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar upprogress ui | peakwar | `assets/src/game/peakwar/pwar_upprogress_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |
| pwar wait ui | peakwar | `assets/src/game/peakwar/pwar_wait_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['peakwar'] (apk_scan_1_4_11.json) |

### SYS_COMM_004 · Race/Guild Race 竞速  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| guild race super panel | guildrace | `assets/src/game/guildrace/guild_race_super_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guildrace'] (apk_scan_1_4_11.json) |
| race ctrl | race | `assets/src/game/race/race_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['race'] (apk_scan_1_4_11.json) |

### SYS_COMM_005 · Cross-server 跨服  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| cross panel | crossserver | `assets/src/game/crossserver/cross_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['crossserver'] (apk_scan_1_4_11.json) |
| prog panel | crossserver | `assets/src/game/crossserver/prog_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['crossserver'] (apk_scan_1_4_11.json) |

### SYS_COMM_006 · Mining 采矿  (13 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| mine panel | mine | `assets/src/game/mine/mine_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine base panel | mine | `assets/src/game/mine/mine_base_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine common view | mine | `assets/src/game/mine/mine_common_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine fetter panel | mine | `assets/src/game/mine/mine_fetter_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine form main panel | mine | `assets/src/game/mine/mine_form_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine guild view | mine | `assets/src/game/mine/mine_guild_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine message panel | mine | `assets/src/game/mine/mine_message_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine partner panel | mine | `assets/src/game/mine/mine_partner_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine result panel | mine | `assets/src/game/mine/mine_result_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine reward panel | mine | `assets/src/game/mine/mine_reward_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine rob panel | mine | `assets/src/game/mine/mine_rob_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine search panel | mine | `assets/src/game/mine/mine_search_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |
| mine wild panel | mine | `assets/src/game/mine/mine_wild_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mine'] (apk_scan_1_4_11.json) |

### SYS_COMM_009 · Freight/Escort 押镖  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| convoy guess panel | convoy | `assets/src/game/convoy/convoy_guess_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['convoy'] (apk_scan_1_4_11.json) |
| convoy panel | convoy | `assets/src/game/convoy/convoy_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['convoy'] (apk_scan_1_4_11.json) |

### SYS_CORE_001 · Account Login 登录  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| login panel | login | `assets/src/game/login/login_panel.luac` | **A** | 是 | CS_1110 AccountLogin,CS_10103 RoleReLogin,CS_1199 heartbeat | runtime_evidence/README.md ; shots/20261002_002907_00_initial.png, p16_login.png |
| platform panel | login | `assets/src/game/login/platform_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['login'] (apk_scan_1_4_11.json) |
| server panel | login | `assets/src/game/login/server_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['login'] (apk_scan_1_4_11.json) |
| user panel | login | `assets/src/game/login/user_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['login'] (apk_scan_1_4_11.json) |

### SYS_CORE_003 · Role Main UI 主界面  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| durable panel | main | `assets/src/game/main/durable_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['main'] (apk_scan_1_4_11.json) |

### SYS_CORE_005 · NPC 交互  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| npc ctrl | npc | `assets/src/game/npc/npc_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['npc'] (apk_scan_1_4_11.json) |
| scene view | scene | `assets/src/game/scene/scene_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['scene'] (apk_scan_1_4_11.json) |

### SYS_CORE_006 · System 系统层  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| language mgr | sys | `assets/src/game/sys/language_mgr.luac` | **B** | 否 | UNKNOWN | ui_by_module['sys'] (apk_scan_1_4_11.json) |
| plist mgr | util | `assets/src/game/util/plist_mgr.luac` | **B** | 否 | UNKNOWN | ui_by_module['util'] (apk_scan_1_4_11.json) |

### SYS_CORE_007 · Resource Update 资源更新  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| res download mgr | loadres | `assets/src/game/loadres/res_download_mgr.luac` | **B** | 否 | UNKNOWN | ui_by_module['loadres'] (apk_scan_1_4_11.json) |

### SYS_CORE_008 · Red Dot/Hide 红点隐藏  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| hide view | hide | `assets/src/game/hide/hide_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['hide'] (apk_scan_1_4_11.json) |
| notice view | notice | `assets/src/game/notice/notice_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['notice'] (apk_scan_1_4_11.json) |
| prompt ctrl | prompt | `assets/src/game/prompt/prompt_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['prompt'] (apk_scan_1_4_11.json) |

### SYS_CORE_009 · Base View 基础视图  (5 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| base view | base | `assets/src/game/base/base_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['base'] (apk_scan_1_4_11.json) |
| shortcut equip panel | common | `assets/src/game/common/shortcut_equip_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['common'] (apk_scan_1_4_11.json) |
| set channel panel | set | `assets/src/game/set/set_channel_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['set'] (apk_scan_1_4_11.json) |
| set panel | set | `assets/src/game/set/set_panel.luac` | **A** | 是 | UNKNOWN (本地面板为主) | shots/uival_01_more.png, v7_more_a_203916.png |
| bushou tips panel | sidebar | `assets/src/game/sidebar/bushou_tips_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sidebar'] (apk_scan_1_4_11.json) |

### SYS_DUNGEON_001 · Dungeon 副本  (14 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| failure panel | dungeon | `assets/src/game/dungeon/failure_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fire acc ui | dungeon | `assets/src/game/dungeon/fire_acc_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fb alert ui | dungeon | `assets/src/game/dungeon/fb_alert_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fb boss ui | dungeon | `assets/src/game/dungeon/fb_boss_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fire buff ui | dungeon | `assets/src/game/dungeon/fire_buff_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| vip fb one key panel | dungeon | `assets/src/game/dungeon/vip_fb_one_key_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fire hard ui | dungeon | `assets/src/game/dungeon/fire_hard_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fb info ui | dungeon | `assets/src/game/dungeon/fb_info_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fire main ui | dungeon | `assets/src/game/dungeon/fire_main_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fb pick ui | dungeon | `assets/src/game/dungeon/fb_pick_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| door question panel | dungeon | `assets/src/game/dungeon/door_question_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| door side ui | dungeon | `assets/src/game/dungeon/door_side_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fb team ui | dungeon | `assets/src/game/dungeon/fb_team_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |
| fb ying ui | dungeon | `assets/src/game/dungeon/fb_ying_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['dungeon'] (apk_scan_1_4_11.json) |

### SYS_DUNGEON_002 · Endless Dungeon 无尽  (6 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| endless form help panel | endless | `assets/src/game/endless/endless_form_help_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['endless'] (apk_scan_1_4_11.json) |
| endless form panel | endless | `assets/src/game/endless/endless_form_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['endless'] (apk_scan_1_4_11.json) |
| endless hire panel | endless | `assets/src/game/endless/endless_hire_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['endless'] (apk_scan_1_4_11.json) |
| endless main panel | endless | `assets/src/game/endless/endless_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['endless'] (apk_scan_1_4_11.json) |
| endless preview panel | endless | `assets/src/game/endless/endless_preview_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['endless'] (apk_scan_1_4_11.json) |
| endless send panel | endless | `assets/src/game/endless/endless_send_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['endless'] (apk_scan_1_4_11.json) |

### SYS_DUNGEON_003 · Tower 镇魂塔  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| demontower ctrl | demontower | `assets/src/game/demontower/demontower_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['demontower'] (apk_scan_1_4_11.json) |
| kunshentower ctrl | kunshentower | `assets/src/game/kunshentower/kunshentower_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['kunshentower'] (apk_scan_1_4_11.json) |
| tower select panel | tower | `assets/src/game/tower/tower_select_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['tower'] (apk_scan_1_4_11.json) |

### SYS_DUNGEON_005 · Cross-server Dungeon 跨服副本  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| cross dungeon box menber view | crossdungeon | `assets/src/game/crossdungeon/cross_dungeon_box_menber_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['crossdungeon'] (apk_scan_1_4_11.json) |
| trial ui panel | trial | `assets/src/game/trial/trial_ui_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['trial'] (apk_scan_1_4_11.json) |
| yuangu ctrl | yuangu | `assets/src/game/yuangu/yuangu_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['yuangu'] (apk_scan_1_4_11.json) |

### SYS_ECON_002 · Inventory/Bag 背包  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| backpack ctrl | backpack | `assets/src/game/backpack/backpack_ctrl.luac` | **A** | 是 | CS_10502 BagSync,CS_10552 BagVolume | runtime_findings.md §D2 ; shots/20261002_003407_tap_hunang.png, d2root_06_bag_open.png |

### SYS_ECON_003 · Mall/Shop 现金商城  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| cash exchange panel | cash | `assets/src/game/cash/cash_exchange_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['cash'] (apk_scan_1_4_11.json) |
| cash record panel | cash | `assets/src/game/cash/cash_record_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['cash'] (apk_scan_1_4_11.json) |
| cash shop panel | cash | `assets/src/game/cash/cash_shop_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['cash'] (apk_scan_1_4_11.json) |
| shop ctrl | shop | `assets/src/game/shop/shop_ctrl.luac` | **A** | 是 | CS_12803 MallList,CS_12805 Buy(未实测购买) | runtime_findings.md §D5.3 ; shots/20261002_003741_tap_mall.png, mall_clean.png |

### SYS_ECON_004 · Storage 仓库  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| warehouse panel | warehouse | `assets/src/game/warehouse/warehouse_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['warehouse'] (apk_scan_1_4_11.json) |

### SYS_ECON_005 · Trade Market 市场  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| market buy more panel | market | `assets/src/game/market/market_buy_more_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['market'] (apk_scan_1_4_11.json) |

### SYS_ECON_006 · Black Market 黑市  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| blackmarketeer main panel | blackmarketeer | `assets/src/game/blackmarketeer/blackmarketeer_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['blackmarketeer'] (apk_scan_1_4_11.json) |

### SYS_ECON_007 · Operation Activity  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-运营兑换 (yunyingduihuan) | yunyingduihuan | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='运营兑换' name='yunyingduihuan'；1.4.11 ui_by_module 无独立 'yunying |

### SYS_ECON_008 · Auction/拍卖  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| auction bid panel | auction | `assets/src/game/auction/auction_bid_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['auction'] (apk_scan_1_4_11.json) |
| auction main ui | auction | `assets/src/game/auction/auction_main_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['auction'] (apk_scan_1_4_11.json) |
| auction record panel | auction | `assets/src/game/auction/auction_record_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['auction'] (apk_scan_1_4_11.json) |

### SYS_ECON_009 · Mail 邮件  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| mail ctrl | mail | `assets/src/game/mail/mail_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['mail'] (apk_scan_1_4_11.json) |

### SYS_ECON_010 · Recharge/充值  (4 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| chongzhi panel | chongzhi | `assets/src/game/chongzhi/chongzhi_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['chongzhi'] (apk_scan_1_4_11.json) |
| recharge first panel | recharge | `assets/src/game/recharge/recharge_first_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['recharge'] (apk_scan_1_4_11.json) |
| recharge weapon panel | recharge | `assets/src/game/recharge/recharge_weapon_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['recharge'] (apk_scan_1_4_11.json) |
| 运营活动-合服首充 (hfsc) | hfsc | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='合服首充' name='hfsc'；1.4.11 ui_by_module 无独立 'hfsc' 模块，由 activi |

### SYS_ECON_012 · Drop/Loot 掉落  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| drop ctrl | drop | `assets/src/game/drop/drop_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['drop'] (apk_scan_1_4_11.json) |

### SYS_EQUIP_001 · Equipment 装备  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| equip ctrl | equip | `assets/src/game/equip/equip_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['equip'] (apk_scan_1_4_11.json) |

### SYS_EQUIP_002 · Smith/Forge 锻造/合成  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| alchemy panel | alchemy | `assets/src/game/alchemy/alchemy_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['alchemy'] (apk_scan_1_4_11.json) |
| equipforge panel | equipforge | `assets/src/game/equipforge/equipforge_panel.luac` | **A** | 是 | UNKNOWN (锻造族) | shots/user_assist/forge_upgrade_panel.png (用户协助) |

### SYS_FRIEND_001 · Partner/Hero 伙伴  (22 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| hero ctrl | hero | `assets/src/game/hero/hero_ctrl.luac` | **A** | 是 | CS_11215 PartnerList | extraction/ui_display_values.md §2 ; shots/uival_07_partner.png |
| partner aptitude ui | hero | `assets/src/game/hero/partner_aptitude_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| hero artifact panel | hero | `assets/src/game/hero/hero_artifact_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner atlas aptitude ui | hero | `assets/src/game/hero/partner_atlas_aptitude_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner base panel | hero | `assets/src/game/hero/partner_base_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| hero equip panel | hero | `assets/src/game/hero/hero_equip_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| tfcard exchange panel | hero | `assets/src/game/hero/tfcard_exchange_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner fetter eat panel | hero | `assets/src/game/hero/partner_fetter_eat_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner gain panel | hero | `assets/src/game/hero/partner_gain_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner grow panel | hero | `assets/src/game/hero/partner_grow_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner hp view | hero | `assets/src/game/hero/partner_hp_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner item backpack panel | hero | `assets/src/game/hero/partner_item_backpack_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner join panel | hero | `assets/src/game/hero/partner_join_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner juling panel | hero | `assets/src/game/hero/partner_juling_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner learn skill panel | hero | `assets/src/game/hero/partner_learn_skill_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| hero list view | hero | `assets/src/game/hero/hero_list_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner mission view | hero | `assets/src/game/hero/partner_mission_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner pack view | hero | `assets/src/game/hero/partner_pack_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| hero show panel | hero | `assets/src/game/hero/hero_show_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner skill pack view | hero | `assets/src/game/hero/partner_skill_pack_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner train item panel | hero | `assets/src/game/hero/partner_train_item_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |
| partner xisui skill ui | hero | `assets/src/game/hero/partner_xisui_skill_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['hero'] (apk_scan_1_4_11.json) |

### SYS_FRIEND_002 · Formation 阵法  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| form defence panel | form | `assets/src/game/form/form_defence_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['form'] (apk_scan_1_4_11.json) |
| form help panel | form | `assets/src/game/form/form_help_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['form'] (apk_scan_1_4_11.json) |
| form panel | form | `assets/src/game/form/form_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['form'] (apk_scan_1_4_11.json) |

### SYS_FRIEND_006 · Partner Weapon 伙伴武器  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| weapon panel | weapon | `assets/src/game/weapon/weapon_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['weapon'] (apk_scan_1_4_11.json) |

### SYS_GM_001 · GM Tools  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| gm report ctrl | gm_report | `assets/src/game/gm_report/gm_report_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['gm_report'] (apk_scan_1_4_11.json) |

### SYS_GROWTH_001 · Skill 技能  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| skill panel | skill | `assets/src/game/skill/skill_panel.luac` | **A** | 是 | CS_10621 SkillList,CS_10622 LearnedSkill,CS_10650 Talent | extraction/skill_panel_located.md ; shots/hj_1710_224355.png, uival_05_skill.png |

### SYS_GROWTH_005 · Morale/Advance  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| advance new panel | advance | `assets/src/game/advance/advance_new_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['advance'] (apk_scan_1_4_11.json) |

### SYS_HIDDEN_002 · XiuLuo/Ghost 修罗  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| ghost ctrl | ghost | `assets/src/game/ghost/ghost_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['ghost'] (apk_scan_1_4_11.json) |

### SYS_HIDDEN_003 · Chief 会长/百官  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| chief result panel | chief | `assets/src/game/chief/chief_result_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['chief'] (apk_scan_1_4_11.json) |

### SYS_HIDDEN_004 · Star Soul 星魂  (11 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| soulstar ctrl | soulstar | `assets/src/game/soulstar/soulstar_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar artifice panel | soulstar | `assets/src/game/soulstar/soulstar_artifice_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar form panel | soulstar | `assets/src/game/soulstar/soulstar_form_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar list view | soulstar | `assets/src/game/soulstar/soulstar_list_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar main panel | soulstar | `assets/src/game/soulstar/soulstar_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar pack view | soulstar | `assets/src/game/soulstar/soulstar_pack_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar review panel | soulstar | `assets/src/game/soulstar/soulstar_review_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar select panel | soulstar | `assets/src/game/soulstar/soulstar_select_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar side ui | soulstar | `assets/src/game/soulstar/soulstar_side_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar success panel | soulstar | `assets/src/game/soulstar/soulstar_success_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |
| soulstar viewstar panel | soulstar | `assets/src/game/soulstar/soulstar_viewstar_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['soulstar'] (apk_scan_1_4_11.json) |

### SYS_HIDDEN_005 · God Redemption 神位  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| godredeem panel | godredeem | `assets/src/game/godredeem/godredeem_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['godredeem'] (apk_scan_1_4_11.json) |
| xianzun ctrl | xianzun | `assets/src/game/xianzun/xianzun_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['xianzun'] (apk_scan_1_4_11.json) |

### SYS_HIDDEN_006 · Operation Activity  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-巨龙/神龙 (julong) | julong | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='巨龙/神龙' name='julong'；1.4.11 ui_by_module 无独立 'julong' 模块，由 a |

### SYS_MAP_001 · World Map 世界地图  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| map view | map | `assets/src/game/map/map_view.luac` | **A** | 是 | UNKNOWN (本地为主) | shots/phase1_world_131336.png, v7_world_203911.png ; skill_panel_located.md §三 (世界地图 X=(2060,85)) |
| nav ctrl | nav | `assets/src/game/nav/nav_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['nav'] (apk_scan_1_4_11.json) |
| tp menu view | treasure_plane | `assets/src/game/treasure_plane/tp_menu_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['treasure_plane'] (apk_scan_1_4_11.json) |

### SYS_MAP_002 · Team 组队  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| team screen panel | team | `assets/src/game/team/team_screen_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['team'] (apk_scan_1_4_11.json) |

### SYS_QUEST_001 · Mission 任务  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| mission nycollect panel | mission | `assets/src/game/mission/mission_nycollect_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['mission'] (apk_scan_1_4_11.json) |
| mission panel | mission | `assets/src/game/mission/mission_panel.luac` | **A** | 是 | CS_12400 MissionList,CS_12401 MissionNPC,CS_12403 MissionCommit | runtime_findings.md §D5.2 ; shots/uival_09_quest.png, uival_18_quest.png |

### SYS_QUEST_002 · Daily/Active 日常活跃  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| daily calendar panel | daily | `assets/src/game/daily/daily_calendar_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['daily'] (apk_scan_1_4_11.json) |
| daily panel | daily | `assets/src/game/daily/daily_panel.luac` | **A** | 是 | CS_13781 Huoli,CS_13786 RiChang | extraction/daily_panel_realclick.md ; shots/v_daily2_201708.png, st_daily_open.png |

### SYS_QUEST_003 · Achievement 成就  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| achieve panel | achieve | `assets/src/game/achieve/achieve_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['achieve'] (apk_scan_1_4_11.json) |

### SYS_QUEST_004 · Operation Activity  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-成长目标 (target) | target | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='成长目标' name='target'；1.4.11 ui_by_module 无独立 'target' 模块，由 ac |

### SYS_QUEST_005 · Guide System 新手引导  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| guider ctrl | guider | `assets/src/game/guider/guider_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['guider'] (apk_scan_1_4_11.json) |
| guide ctrl | newguide | `assets/src/game/newguide/guide_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['newguide'] (apk_scan_1_4_11.json) |
| story ctrl | story | `assets/src/game/story/story_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['story'] (apk_scan_1_4_11.json) |

### SYS_ROLE_001 · Role Attribute 角色属性  (13 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| role ctrl | role | `assets/src/game/role/role_ctrl.luac` | **A** | 是 | CS_10301,CS_10303,CS_10304… | runtime_findings.md §D1 ; shots/20261002_003507_tap_attr.png, p45a_attr.png, p2b_charpanel.png |
| role changename view | role | `assets/src/game/role/role_changename_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role check panel | role | `assets/src/game/role/role_check_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role decorate panel | role | `assets/src/game/role/role_decorate_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role display panel | role | `assets/src/game/role/role_display_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role fashion view | role | `assets/src/game/role/role_fashion_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| weapon gain panel | role | `assets/src/game/role/weapon_gain_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| fashion grow panel | role | `assets/src/game/role/fashion_grow_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role hero panel | role | `assets/src/game/role/role_hero_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role main view | role | `assets/src/game/role/role_main_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| fashion pack view | role | `assets/src/game/role/fashion_pack_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role show panel | role | `assets/src/game/role/role_show_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |
| role weapon view | role | `assets/src/game/role/role_weapon_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['role'] (apk_scan_1_4_11.json) |

### SYS_ROLE_002 · Operation Activity  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-门派 (menpai) | menpai | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='门派' name='menpai'；1.4.11 ui_by_module 无独立 'menpai' 模块，由 acti |

### SYS_ROLE_003 · Title 称号  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| title ctrl | title | `assets/src/game/title/title_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['title'] (apk_scan_1_4_11.json) |

### SYS_ROLE_004 · VIP/宝石VIP  (8 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| jewelvip activate panel | jewelvip | `assets/src/game/jewelvip/jewelvip_activate_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['jewelvip'] (apk_scan_1_4_11.json) |
| jewelvip base panel | jewelvip | `assets/src/game/jewelvip/jewelvip_base_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['jewelvip'] (apk_scan_1_4_11.json) |
| jewelvip becoming panel | jewelvip | `assets/src/game/jewelvip/jewelvip_becoming_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['jewelvip'] (apk_scan_1_4_11.json) |
| jewelvip forever panel | jewelvip | `assets/src/game/jewelvip/jewelvip_forever_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['jewelvip'] (apk_scan_1_4_11.json) |
| jewelvip limitvip panel | jewelvip | `assets/src/game/jewelvip/jewelvip_limitvip_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['jewelvip'] (apk_scan_1_4_11.json) |
| jewelvip rebate panel | jewelvip | `assets/src/game/jewelvip/jewelvip_rebate_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['jewelvip'] (apk_scan_1_4_11.json) |
| jewelvip shop panel | jewelvip | `assets/src/game/jewelvip/jewelvip_shop_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['jewelvip'] (apk_scan_1_4_11.json) |
| vip ctrl | vip | `assets/src/game/vip/vip_ctrl.luac` | **A** | 是 | UNKNOWN (super_vip) | shots/20261002_003351_close_recharge.png (误触打开后立即关闭) |

### SYS_ROLE_005 · Grade Break 等级突破  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| gradebreak rank panel | gradebreak | `assets/src/game/gradebreak/gradebreak_rank_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['gradebreak'] (apk_scan_1_4_11.json) |
| gradebreak reward panel | gradebreak | `assets/src/game/gradebreak/gradebreak_reward_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['gradebreak'] (apk_scan_1_4_11.json) |
| gradebreak seal panel | gradebreak | `assets/src/game/gradebreak/gradebreak_seal_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['gradebreak'] (apk_scan_1_4_11.json) |

### SYS_ROLE_006 · Avatar/Head 头像  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| head ctrl | head | `assets/src/game/head/head_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['head'] (apk_scan_1_4_11.json) |

### SYS_SOCIAL_001 · Chat 聊天  (2 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| chat panel | chat | `assets/src/game/chat/chat_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['chat'] (apk_scan_1_4_11.json) |
| chat private panel | chat | `assets/src/game/chat/chat_private_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['chat'] (apk_scan_1_4_11.json) |

### SYS_SOCIAL_002 · Friend 联系人  (6 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| contact ctrl | contact | `assets/src/game/contact/contact_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['contact'] (apk_scan_1_4_11.json) |
| friend panel | friend | `assets/src/game/friend/friend_panel.luac` | **A** | 是 | CS_13300 FriendList,CS_13321 FriendUpdate | tests/1.4.11/NEW_SYSTEMS_REGRESSION.md §一 (13300/13321 客户端回归 ALL PASS) ; PHASE2_15_FRIEND.md |
| friend black list ui | friend | `assets/src/game/friend/friend_black_list_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['friend'] (apk_scan_1_4_11.json) |
| friend contact ui | friend | `assets/src/game/friend/friend_contact_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['friend'] (apk_scan_1_4_11.json) |
| friend list ui | friend | `assets/src/game/friend/friend_list_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['friend'] (apk_scan_1_4_11.json) |
| friend say panel | friend | `assets/src/game/friend/friend_say_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['friend'] (apk_scan_1_4_11.json) |

### SYS_SOCIAL_003 · Moments/朋友圈  (13 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| circle ctrl | circle | `assets/src/game/circle/circle_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle decorate panel | circle | `assets/src/game/circle/circle_decorate_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle detail ui | circle | `assets/src/game/circle/circle_detail_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle dyna ui | circle | `assets/src/game/circle/circle_dyna_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle gift panel | circle | `assets/src/game/circle/circle_gift_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle hot ui | circle | `assets/src/game/circle/circle_hot_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle info ui | circle | `assets/src/game/circle/circle_info_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle list flower ui | circle | `assets/src/game/circle/circle_list_flower_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle main panel | circle | `assets/src/game/circle/circle_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle msg ui | circle | `assets/src/game/circle/circle_msg_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle say panel | circle | `assets/src/game/circle/circle_say_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle send panel | circle | `assets/src/game/circle/circle_send_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |
| circle zone panel | circle | `assets/src/game/circle/circle_zone_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['circle'] (apk_scan_1_4_11.json) |

### SYS_SOCIAL_004 · Guild 公会  (25 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| target panel | guild | `assets/src/game/guild/target_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild action view | guild | `assets/src/game/guild/guild_action_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild aim panel | guild | `assets/src/game/guild/guild_aim_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild allocate panel | guild | `assets/src/game/guild/guild_allocate_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild apply view | guild | `assets/src/game/guild/guild_apply_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild base panel | guild | `assets/src/game/guild/guild_base_panel.luac` | **A** | 是 | CS_183xx 公会族 | shots/activity_guild_smoke.png ; skill_panel_located.md §三 (1960,1320 宗门面板) |
| guild build panel | guild | `assets/src/game/guild/guild_build_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild create panel | guild | `assets/src/game/guild/guild_create_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild flower panel | guild | `assets/src/game/guild/guild_flower_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild fortune panel | guild | `assets/src/game/guild/guild_fortune_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| lgf gang panel | guild | `assets/src/game/guild/lgf_gang_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild info view | guild | `assets/src/game/guild/guild_info_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild lists panel | guild | `assets/src/game/guild/guild_lists_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild mgr panel | guild | `assets/src/game/guild/guild_mgr_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild mis panel | guild | `assets/src/game/guild/guild_mis_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild mission panel | guild | `assets/src/game/guild/guild_mission_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild notice panel | guild | `assets/src/game/guild/guild_notice_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| lgf own panel | guild | `assets/src/game/guild/lgf_own_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| water record panel | guild | `assets/src/game/guild/water_record_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild sign panel | guild | `assets/src/game/guild/guild_sign_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild skill limit panel | guild | `assets/src/game/guild/guild_skill_limit_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild trainee panel | guild | `assets/src/game/guild/guild_trainee_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild union panel | guild | `assets/src/game/guild/guild_union_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild welcome view | guild | `assets/src/game/guild/guild_welcome_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |
| guild welfare view | guild | `assets/src/game/guild/guild_welfare_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['guild'] (apk_scan_1_4_11.json) |

### SYS_SOCIAL_005 · Marriage 结婚  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| wedding ring panel | wedding | `assets/src/game/wedding/wedding_ring_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['wedding'] (apk_scan_1_4_11.json) |

### SYS_SOCIAL_006 · Jiebai 结拜  (15 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| sworn ctrl | sworn | `assets/src/game/sworn/sworn_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn base panel | sworn | `assets/src/game/sworn/sworn_base_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn confirm panel | sworn | `assets/src/game/sworn/sworn_confirm_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn introduce panel | sworn | `assets/src/game/sworn/sworn_introduce_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn invite panel | sworn | `assets/src/game/sworn/sworn_invite_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn leave panel | sworn | `assets/src/game/sworn/sworn_leave_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn main panel | sworn | `assets/src/game/sworn/sworn_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn message view | sworn | `assets/src/game/sworn/sworn_message_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn notice panel | sworn | `assets/src/game/sworn/sworn_notice_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn rule view | sworn | `assets/src/game/sworn/sworn_rule_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn side ui | sworn | `assets/src/game/sworn/sworn_side_ui.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn skill view | sworn | `assets/src/game/sworn/sworn_skill_view.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn title panel | sworn | `assets/src/game/sworn/sworn_title_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn vote panel | sworn | `assets/src/game/sworn/sworn_vote_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |
| sworn votething panel | sworn | `assets/src/game/sworn/sworn_votething_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['sworn'] (apk_scan_1_4_11.json) |

### SYS_SOCIAL_007 · Operation Activity  (1 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| 运营活动-送花 (flower) | flower | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='送花' name='flower'；1.4.11 ui_by_module 无独立 'flower' 模块，由 acti |

### SYS_SOCIAL_009 · Guild Wars 公会战  (5 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| gangwars list panel | gangwars | `assets/src/game/gangwars/gangwars_list_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['gangwars'] (apk_scan_1_4_11.json) |
| gangwars panel | gangwars | `assets/src/game/gangwars/gangwars_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['gangwars'] (apk_scan_1_4_11.json) |
| guildwars panel | guildwars | `assets/src/game/guildwars/guildwars_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guildwars'] (apk_scan_1_4_11.json) |
| guildwars result panel | guildwars | `assets/src/game/guildwars/guildwars_result_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guildwars'] (apk_scan_1_4_11.json) |
| 运营活动-跨服公会战 (kuafu_guildwars) | kuafu_guildwars | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='跨服公会战' name='kuafu_guildwars'；1.4.11 ui_by_module 无独立 'kuafu |

### SYS_SOCIAL_010 · Guild Secret Area 公会秘境  (3 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| guild secret area roll panel | guildsecretarea | `assets/src/game/guildsecretarea/guild_secret_area_roll_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guildsecretarea'] (apk_scan_1_4_11.json) |
| guild target main panel | guildtarget | `assets/src/game/guildtarget/guild_target_main_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guildtarget'] (apk_scan_1_4_11.json) |
| guild target mon panel | guildtarget | `assets/src/game/guildtarget/guild_target_mon_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['guildtarget'] (apk_scan_1_4_11.json) |

### SYS_UNKNOWN_002 · 封测/活动运营  (12 条)

| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |
|---|---|---|---|---|---|---|
| fengce ctrl | fengce | `assets/src/game/fengce/fengce_ctrl.luac` | **B** | 否 | UNKNOWN | ui_by_module['fengce'] (apk_scan_1_4_11.json) |
| xuan panel | xuan | `assets/src/game/xuan/xuan_panel.luac` | **B** | 否 | UNKNOWN | ui_by_module['xuan'] (apk_scan_1_4_11.json) |
| garden (1.3.0 已移除) | garden | `assets/src/game/garden/ (1.3.0 only, 1.4.11 缺失)` | **D** | 否 | UNKNOWN | diff.game_modules_only_in_1.3.0 含 'garden'；version_compare/1.3.0/extracted/game/garden/ 下有 ctrl/data/view 文件 |
| jingjie (1.3.0 已移除) | jingjie | `assets/src/game/jingjie/ (1.3.0 only, 1.4.11 缺失)` | **D** | 否 | UNKNOWN | diff.game_modules_only_in_1.3.0 含 'jingjie'；version_compare/1.3.0/extracted/game/jingjie/ 下有 ctrl/data/view 文件 |
| xiulianhulu (1.3.0 已移除) | xiulianhulu | `assets/src/game/xiulianhulu/ (1.3.0 only, 1.4.11 缺失)` | **D** | 否 | UNKNOWN | diff.game_modules_only_in_1.3.0 含 'xiulianhulu'；version_compare/1.3.0/extracted/game/xiulianhulu/ 下有 ctrl/data/view 文件 |
| glz main ui  | dungeon | `assets/src/game/dungeon/gaolaozhuang/glz_main_ui.luac  (1.3.0 only)` | **D** | 否 | UNKNOWN | diff.ui_files_only_in_1.3.0 含 'assets/src/game/dungeon/gaolaozhuang/glz_main_ui.luac' |
| friend view  | friend | `assets/src/game/friend/friend_view.luac  (1.3.0 only)` | **D** | 否 | UNKNOWN | diff.ui_files_only_in_1.3.0 含 'assets/src/game/friend/friend_view.luac' |
| mail panel  | mail | `assets/src/game/mail/mail_panel.luac  (1.3.0 only)` | **D** | 否 | UNKNOWN | diff.ui_files_only_in_1.3.0 含 'assets/src/game/mail/mail_panel.luac' |
| libao view  | shop | `assets/src/game/shop/libao_view.luac  (1.3.0 only)` | **D** | 否 | UNKNOWN | diff.ui_files_only_in_1.3.0 含 'assets/src/game/shop/libao_view.luac' |
| 运营活动-合服 (hefu) | hefu | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='合服' name='hefu'；1.4.11 ui_by_module 无独立 'hefu' 模块，由 activity |
| 运营活动-FC (fc) | fc | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='FC' name='fc'；1.4.11 ui_by_module 无独立 'fc' 模块，由 activity_ctr |
| 运营活动-密令 (miling) | miling | `(无独立 luac；由 activity_ctrl.luac 按 name 分派)` | **C** | 否 | CS_10924 ActList,CS_10925 ActHandler | extraction/client_activity_icon_registry.md：活动图标注册表含 label='密令' name='miling'；1.4.11 ui_by_module 无独立 'miling' 模块，由 acti |

## 未确认项清单（status=UNKNOWN/字段空缺）

共 **338** 条协议号未确认（B 类默认）。完整列表见 json。
