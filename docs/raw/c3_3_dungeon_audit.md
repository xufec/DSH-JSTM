# C3.3 第二分片 · 副本入口与业务闭环诊断

- 日期：2026-10-16（纯只读审计；不实施任何修改）
- 方法：不假设服务端缺协议；先定位入口不可达的真实原因。
- 证据等级：`V`=真机帧/实机点测；`C`=配置表/代码/客户端文件；`I`=本服务端实现；`U`=UNKNOWN。

---

## §1 副本入口资源 / 脚本 / 注册情况

| 项 | 结论 | 证据 | 等级 |
|---|---|---|---|
| 客户端模块 | `assets/src/game/dungeon/` 26 个文件：dungeon_ctrl / dungeon_mgr / dungeon_data；子目录 fourdoor/door_main_view（四门）、zhenhuo/fire_main_ui（真火）；fb_alert/boss/info/pick/team/ying_ui；fire_acc/buff/hard_ui；vip_fb_*；ycj_*；fly_fb_view；success/failure_panel | analysis/_raw/apk_scan_1_4_11.json → ui_by_module.dungeon；三版均存在 | C |
| SYS_DUNGEON_001 面板盘点 | 14 个 UI：8 个 IMPLEMENTED_UNVERIFIED（failure/fire_acc/fb_alert/fb_boss/fire_buff/vip_fb_one_key/fire_hard/fb_info），fire_main_ui=**UNKNOWN** | docs/C2_全量界面恢复总表.md:298-306 | C |
| 入口按钮 | **实机未见**：主界面/宗门/更多菜单均无副本入口（C2.3 G5 BLOCKED）；config_function 91 个入口中**无副本主入口条目**（id=504 挂机、1010 宗门副本、1011 秘境探宝之外无 dungeon） | docs/C2.3_未完成项与阻塞问题.md G5；server/cfg/config_function.json | V+C |
| 入口注册方式 | UNKNOWN。原版可能经日常活动面板/世界地图传送门/NPC 打开 door_main_view；本地无 dungeon_ctrl 反汇编可查调用方 | U |

## §2 显示条件 / 前置任务 / 等级 / 场景限制

| 条件 | 证据 | 等级 |
|---|---|---|
| 各副本开放等级 | config_dungeon_new.json 每条 dung 带 open_lev：历练副本·新生考核 lv33、封神之路 lv24、镇魂塔 lv45、传灵塔 lv55、遗迹一层 lv78、神界试炼 lv73/83/93、结拜副本 lv48 等 34 条 | C |
| 队伍限制 | type_team=1 单人 / =4 组队；team_confirm=1 需确认（无尽兽潮、神界试炼≥3 人） | C |
| 每日次数 | count 字段（如新生考核=1、乾坤问情=5）；服务端 13005 查 dung_left 默认 5 | C+I |
| 前置任务链 | TypeName/next_elem 链存在（如无尽兽潮 30001→30004）；完整前置任务要求未提取 | U |

## §3 按钮事件是否实际执行

- C2.3 实机：**入口根本不可见**，按钮事件无从触发 → UNKNOWN（不是「点了没反应」，是「没有按钮可点」）。
- 服务端角度：旧会话日志中客户端曾发出 CS_21306 / CS_21312（server/logs/server_stdout.log:8904-8906）——说明某条流程里副本面板能被打开并发列表请求；但 C2.3/C2.4 测试路径（主界面/宗门/更多）未触达。

## §4 客户端是否发请求及内容

| 命令 | 真机证据 | 说明 |
|---|---|---|
| 21306 副本列表 | server_stdout.log:8904 `>> cmd=21306 body(0)` | 客户端确会发；spec SC{list[{bid,enter_count,buy_count,time,is_finish}]}（fields.json:79824） |
| 13036 塔设置 | mock_server.py:15840 注释引真机帧 `00009c41010100008959` | demontower_ctrl 真发过 3 次 |
| 13035/13038 | R46 注释：真机 7 次全 GAP（无应答） | tower/demontower_ctrl |
| 21308 进本 / 21309 退本 | **tcp.log 全部历史无帧** | 入口从未到达，符合 §1 |

## §5 服务端是否注册和处理

| handler | 当前行号 | 回包 | 评价 |
|---|---|---|---|
| 21306 副本列表 | mock_server.py:14377 | 34 行 config_dungeon_new 全 0 次数 | ✅ 已实现 |
| 13005 副本次数 | :15827 | bid/flag/left_times（dung_left 默认 5） | ✅ |
| 13036 塔设置 | :15837 | {0,0}（照 minloop；落库 dung_setting） | ✅ round44.1 |
| 13042 爬塔进度 | :15872 | high_floor/clear_list 读 dungeon_progress | ✅ R46 |
| 13035 塔队伍 | :15895 | 单机 1 人 | ✅ R46 |
| 13038 塔记录 | :15918 | record_str=空 | ✅ R46（不编造） |
| 13037 挑战层 | 仅落入 13xxx 通用组 :12588 | 通用回包与 SC_13037 spec{Bid:u32,ceng:u8,tips:u8,msg:s} **结构不符** | ⚠ 桩错误配 |
| 21307 结算 / 21308 进本 / 21309 退本 / 21310 扫荡 | **未注册** | — | ❌ GAP |

**勘误**：C1_系统恢复总表 / C2.3 清单把 `11700`（实为排行榜记录：free_times/all_times/reward_coin，mock_server.py:18159）、`11710-11713`（实为聚宝盆抽奖，:18666-18700）标为「副本 handler」——读码证伪，它们不是副本。

## §6 副本配置 / 关卡 / 怪物 / 次数 / 奖励

- `config_dungeon_new.json`：34 条，12 类（type：2 封神之路/3 极地寻宝/4 镇魂塔三塔/5 无尽兽潮/8 乾坤问情/9 海神九考/10 历练副本 70001-70006/11 神界试炼/13 结拜/18 遗迹一~九层/19 星辰殿/255 困神塔），含 open_lev/type_team/count/map_bid/dung_id 映射 MapDung、TypeName。
- `config_dungeon_tower.json`：DungeonTower 9 层（map 21000-21008、boss 18201-18209、首通 first_kill、通关奖励 clear_item/clear_asset、下层 next_elem 链）+ DungeonTowerHard 9 层（map 22000-22008、boss 18401-18409）。
- 其余表：endless/gods/jieyi/rune/seal_demon/vip_single/vip_single2/reward_desc（1.4.11 配置表清单）。

## §7 副本进入/战斗/完成/失败/退出状态流转

| 阶段 | 协议证据 | 现状 |
|---|---|---|
| 列表 | CS_21306 → SC list | ✅ 已接 |
| 进入 | CS_21308{bid:u32} → SC{tips:u8,msg:s,time:u16}（fields.json:79909）；进本后经 10200 传送到 MapDung 指定 map_bid | ❌ 未接 |
| 战斗 | 20002 战斗族（通用）+ 塔 boss 18201-18209 | 通用族在 |
| 完成结算 | SC_21307{bid:u32,gain:[{type:u8,count:...}]}（:79865） | ❌ 未接 |
| 退出 | CS_21309{bid} → SC{tips,msg,bid}（:79941） | ❌ 未接 |
| 扫荡 | SC_21310 one_key_sweep_list（:79973） | ❌ 未接 |
| 塔专用 | CS_13037{Bid,ceng} 挑战层；13036 设置；13042 进度；13038 记录；13035 队伍 | 13037 桩错配，其余在 |

## §8 版本差异（1.4.11 vs 1.4.9 vs 1.3.0）

- dungeon 模块三版均存在（version_diff_matrix.md:45）；1.3.0 已有 config_dungeon_new/tower/vip_single。
- 1.4.11 新增 endless/gods/jieyi/rune/seal_demon/vip_single2 六表 + kunshentower/crossdungeon 两模块。
- **核心副本（历练/塔/遗迹）配置无版本缺失**；入口不可达不是「缺资源」。

## §9 问题归类与根因判定

| 候选类别 | 判定 | 证据 |
|---|---|---|
| 协议缺失 | 否 | 21306/13005/13035/13036/13038/13042 已接；未接的 21307/21308/21309 只在进入后才需要 |
| 配置缺失 | 否 | 34 副本 + 塔 18 层配置完整 |
| **UI/导航（入口可达性）** | **★ 根因** | C2.3 G5：主界面/宗门/更多均无入口；config_function 无副本主入口；入口很可能在日常活动面板/世界地图传送门路径上，而该路径受 G8 世界地图传送 BLOCK 牵连 |
| 业务逻辑 | 次因 | 即便入口可达，21308 进本/21307 结算/21309 退本未接，闭环断在「进本」 |
| 前置条件 | 待证 | open_lev 均 ≤ 当前 lev(70)；前置任务链未提取 |

**根因结论：副本不可达 = UI 导航层问题（入口按钮不可见/未被导航到），不是服务端缺协议、也不是缺配置。** 入口真实挂载点 UNKNOWN（需反汇编 dungeon_mgr/door_main_view 的打开方，或在日常活动面板内逐一点测）。

---

## 最小副本候选（仅列证据充分、依赖少者）

### 候选 1：镇魂塔 / 爬塔（demontower）——证据最充分

| 项 | 内容 | 证据 |
|---|---|---|
| 客户端 | demontower_ctrl/view/data.luac 齐备；ctrl 发 13036/13037/13038 + 20025/20026（战斗回放） | analysis/_demontower_dis.txt:169-175,234 |
| 配置 | DungeonTower 9 层 + Hard 9 层，每层 map_bid/boss/首通/通关奖励/下层链完整 | server/cfg/config_dungeon_tower.json |
| 服务端 | 13035/13036/13038/13042 已接（R46/round44.1）；**13037 桩错配待修** | mock_server.py:15837-15927 |
| 进入条件 | dung 40001 镇魂塔 open_lev=45（config_dungeon_new type=4）；当前 lev=70 满足 | C |
| 状态流转 | 查进度(13042)→挑战层(13037)→传送 21000+ map→boss 战→结算（21307 未接，需补） | C+缺口标注 |
| 主要缺口 | ①13037 按 spec{Bid,ceng,tips,msg} 重写；②入口按钮挂载点；③结算 21307 | — |

### 候选 2：历练副本·单人（type=10，dung 70001-70006）

- 单人(type_team=1)、等级 33-83、count=1；配置齐全；不依赖组队系统。
- 缺口：21308 进本/21307 结算/21309 退本全未接；入口同样不可达。证据量少于候选 1（无专用客户端模块反汇编）。

---

## 自检记录

- 只读纪律：未改任何代码/配置，仅新建本文件与 c3_3_hangup_audit.md。
- 未编造：入口挂载点、10931 语义、挂机收益表、副本前置任务链均标 U/BLOCKED。
- 勘误两条已写入：①11700/11710-11713 非副本；②154xx=挂机怪族 ≠ 挂机面板族（面板族=1093x）。
