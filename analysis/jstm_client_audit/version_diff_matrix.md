# 《绝世唐门》三版本差异矩阵（PHASE C0 审计）

> 生成：tools/jstm_audit/gen_version_diff.py（2026-10-15，只读审计）。
> 骨架：analysis/version_compare/version_diff_matrix.json（未修改）；新证据：_raw/apk_scan_*.json（CONFIRMED）+ server/*.json 实测（VERIFIED）。

- 维度总数：**39**（系统维度 24 + 扫描指标维度 15）
- 版本自证：1.3.0 NOW_VERSION=35（工程代号 INFERENCE）；1.4.9 NOW_VERSION=186；1.4.11 NOW_VERSION=208（均读 config.luac 明文，CONFIRMED）。

## 一、系统维度（24，沿用既有骨架，已补新扫描证据）

| 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 差异 | 证据等级 | 说明 |
|---|---|---|---|---|---|---|
| Lua模块 | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含完整 luac 模块族（1557 / 2234 / 2297 个，直接读 zip 中央目录，CONFIRMED）。game 模块目录数按新扫描口径：85 / 108 / 111（CONFIRMED，apk_scan_*.json 的 game_modules 列表长度）；旧 inventory 的 92/116/119 为早期分文件提取口径，已被本口径取代。1.4.11 新增模块含大量 _ctrl/_panel/_view UI 模块；1.4.9 UI corpus 仅部分反编译（提取层面覆盖度，非 UI 不存在）。 |
| cmd | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 共享同一 cmd registry 结构; 条目随 cmd_resolve 增长(89->122->124). registry cmd_table.json=1643 为 1.4.9-based, 不视为与 1.4.11 wire 格式相等; 1.4.11 cmd-diff 仅 INFERENCE. |
| protocol | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 共享 registry fields.json=3553; 1.4.9 已分系统整理. 1.3.0 解包内含 all_proto.luac(落于 extracted/config/protocal/). 存在性 CONFIRMED; 1.4.11 wire 一致性 INFERENCE. |
| cmd_resolve | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 计数 89 / 122 / 124（CONFIRMED，apk_scan_*.json 的 cmd_resolve 列表长度）。1.4.11 vs 1.3.0 新增 35 个（cmd_resolve_187..191 等段；apk_scan_summary.json diff）；1.3.0 无独有 cmd_resolve。1.4.11 另有 server_cmds.json / protocalrulesmgr.luac（version_compare/1.4.11/inventory.md）。 |
| config | 存在 | 存在 | 存在 | 修改 | CONFIRMED | config_*.luac 计数 168 / 227 / 233（CONFIRMED，apk_scan_*.json 的 config_tables 列表长度）。1.4.11 vs 1.3.0 独有表：auction/black_market/chair/chat_bubble/fashion/foot_print/holiday_*/mine/partner_fetter/score/shenqi 等；1.3.0 独有表仅 config_holiday.luac（1.4.11 拆为 config_holiday_* 系列=重命名/拆分）。 |
| item | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 config_item.luac 及 fuse/gift/misc/type_name 族（存在性 CONFIRMED，apk_scan config_tables 清单）。1.4.11 条数=3535（VERIFIED，本脚本实测 server/item_config.json 顶层键数；HANDOFF 指明 server/ 服务 1.4.11 主目标）。1.3.0 / 1.4.9 逐条条数=UNKNOWN（仅存在性证据，禁止按 ID 连续性推测）。注：旧矩阵曾把 3535 记为 1.4.9，经 HANDOFF 归属判定纠正为 1.4.11。 |
| equipment | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 config_intensify.luac/config_eqm_starup_data.luac. 1.4.11 新增 config_eqm_ancient.luac/config_red_eqm.luac/config_fabao.luac. 存在性 CONFIRMED. |
| skill | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 config_skill.luac + bullet/magic/scene/talent/trigger/xiulian 全家. 存在性 CONFIRMED. |
| task | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 config_mission.luac + buffy/escort/help/kill_demon/loop/marry/treasure 族（存在性 CONFIRMED）。1.4.11 条数=846（VERIFIED，server/mission_config.json 实测）。1.3.0 / 1.4.9 条数=UNKNOWN。 |
| partner | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 1.3.0 含 hero 模块 + config_partner_base/misc/skill.luac；1.4.11 新增 fetter/score/shenqi（共6表，存在性 CONFIRMED）。1.4.11 条数=53（VERIFIED，server/partner_config.json 实测）。1.3.0 / 1.4.9 条数=UNKNOWN。 |
| dungeon | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 1.3.0 已有 config_dungeon_new/tower/vip_single.luac. 1.4.11 新增 endless/gods/jieyi/rune/seal_demon/vip_single2 + kunshentower/crossdungeon 模块. 存在性 CONFIRMED. |
| activity | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版 config_function.luac 入口均为 91(id-count, VERIFIED). 1.3.0 无 auction/peakwar/holiday_* 系列; 1.4.11 新增 config_act/fest_data/holiday_*(由 config_holiday 重命名/拆分)等. 存在性 CONFIRMED. |
| shop | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 config_mall.luac/config_shop.luac/config_market.luac（存在性 CONFIRMED）。1.4.11 mall 条数=142（VERIFIED，server/mall_config.json 实测）。1.3.0 / 1.4.9 条数=UNKNOWN。 |
| currency | 存在 | 存在 | 存在 | 修改 | STRONG_INFERENCE | 三版同源 config_game_data.luac(AssetsEnToCode 资产/货币枚举); 精确货币 id 集合未逐一枚举. 存在性 STRONG_INFERENCE(同源引擎), 集合粒度 UNKNOWN. |
| UI | 存在 | 存在 | 存在 | 修改 | CONFIRMED | UI 文件计数 539 / 876 / 910（CONFIRMED，apk_scan_*.json 的 ui_files 列表长度）；UI 覆盖模块数 ui_by_module=89 / 112 / 115。1.3.0 独有 UI 文件：dungeon/gaolaozhuang/glz_main_ui、friend/friend_view 等；1.4.9 UI corpus 仅部分反编译（提取层面覆盖度，非 UI 不存在）。 |
| scene | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 map 模块 + config_map.luac/map_block/map_npc/map_icon_pos/map_partical/world_map. 存在性 CONFIRMED. |
| NPC | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 npc 模块 + config_npc.luac. 存在性 CONFIRMED. |
| monster | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 ghost/boss 模块 + config_mon_data.luac. 存在性 CONFIRMED. |
| GM | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含 gm_report 模块 + config_gm_cmd.luac. 存在性 CONFIRMED. |
| system entry | 存在 | 存在 | 存在 | 修改 | CONFIRMED | config_function.luac 入口三版均为 91（id-count，VERIFIED）；game 模块数 85 / 108 / 111（CONFIRMED）。存在性 CONFIRMED。 |
| resources | 存在 | 存在 | 存在 | 修改 | CONFIRMED | assets 未压缩字节 135.1MB / 241.3MB / 276.2MB（CONFIRMED，apk_scan_summary.json versions.*.assets_bytes，直接读 zip）；APK 压缩包体积 135.8MB / 230.5MB / 267.8MB。单资产文件清单未逐一枚举=UNKNOWN。 |
| strings | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 三版均含文案/常量表: 1.3.0 config_color.luac/config_color_code.luac/config_notice.luac; 1.4.11 另增 config_chat_bubble.luac 等. 存在性 CONFIRMED. |
| assets | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 总条目 10670 / 16379 / 19106（CONFIRMED，apk_scan_summary.json versions.*.entries，直接读 zip 中央目录）。单个资产文件清单未逐一枚举。 |
| data tables | 存在 | 存在 | 存在 | 修改 | CONFIRMED | 1.3.0 168 配置表 ⊂ 1.4.11 233(仅 config_holiday.luac 为 1.3.0 独有, 1.4.11 拆为 config_holiday_* 系列=重命名/拆分); item/skill/partner/mission/dungeon/activity 等大量重叠. 行级 table-count diff UNKNOWN. 存在性 CONFIRMED. |

## 二、新增扫描指标维度（zip 中央目录直读，CONFIRMED）

| 指标 | 1.3.0 | 1.4.9 | 1.4.11 | 1.4.11 vs 1.3.0 | 证据等级 | 说明 |
|---|---|---|---|---|---|---|
| APK 体积 | 135.8MB | 230.5MB | 267.8MB | +138366797 | CONFIRMED | zip 文件字节数；证据 apk_scan_summary.json versions.*.apk_bytes。 |
| APK 条目总数 | 10670 | 16379 | 19106 | +8436 | CONFIRMED | zip 中央目录条目数；证据 apk_scan_*.json。 |
| assets 字节数(未压缩) | 135.1MB | 241.3MB | 276.2MB | +148004638 | CONFIRMED | assets/ 条目未压缩字节合计；证据 apk_scan_summary.json。 |
| luac 文件总数 | 1557 | 2234 | 2297 | +740 | CONFIRMED | assets/src/**.luac 计数；证据 apk_scan_*.json。 |
| game 模块目录数 | 85 | 108 | 111 | +26 | CONFIRMED | assets/src/game/ 下模块目录数（新扫描口径，取代旧 inventory 92/116/119 提取口径）；证据 apk_scan_*.json game_modules。 |
| config 表数(config_*.luac) | 168 | 227 | 233 | +65 | CONFIRMED | 证据 apk_scan_*.json config_tables 列表。 |
| cmd_resolve 文件数 | 89 | 122 | 124 | +35 | CONFIRMED | 证据 apk_scan_*.json cmd_resolve 列表。 |
| UI 文件数 | 539 | 876 | 910 | +371 | CONFIRMED | 证据 apk_scan_*.json ui_files 列表。 |
| UI 覆盖模块数(ui_by_module) | 89 | 112 | 115 | +26 | CONFIRMED | 证据 apk_scan_*.json ui_by_module 字典键数。 |
| res 资源分类数 | 821 | 1178 | 1251 | +430 | CONFIRMED | 证据 apk_scan_*.json res_categories 字典键数。 |
| 版本自证(NOW_VERSION) | 35 | 186 | 208 | +173 | CONFIRMED | 读 assets/src/config.luac 明文 NOW_VERSION（apk_scan_*.json version_probe）。'1.3.0' 是工程代号 INFERENCE（实际版本串 1.0.100/35，ewan 渠道）。 |
| item 配置条数 | UNKNOWN | UNKNOWN | 3535 | N/A | VERIFIED | 1.4.11=server/item_config.json 顶层键数（本脚本实测）；1.3.0/1.4.9 仅 config 表存在性证据，条数 UNKNOWN。 |
| mission 配置条数 | UNKNOWN | UNKNOWN | 846 | N/A | VERIFIED | 1.4.11=server/mission_config.json 顶层键数（本脚本实测）；1.3.0/1.4.9 条数 UNKNOWN。 |
| mall 配置条数 | UNKNOWN | UNKNOWN | 142 | N/A | VERIFIED | 1.4.11=server/mall_config.json 顶层条数（本脚本实测）；1.3.0/1.4.9 条数 UNKNOWN。 |
| partner 配置条数 | UNKNOWN | UNKNOWN | 53 | N/A | VERIFIED | 1.4.11=server/partner_config.json 顶层条数（本脚本实测）；1.3.0/1.4.9 条数 UNKNOWN。 |

## 三、证据等级定义

- **CONFIRMED**：直接读 APK / 解包数据（主源证据）
- **VERIFIED**：实机 + 服务器验证（次级但可靠）
- **STRONG_INFERENCE**：同源/强推断，无逐字段直接核对
- **INFERENCE**：合理推断，无直接核对
- **UNKNOWN**：缺少直接证据

## 四、注意事项

- protocol registry (cmd_table.json 1643, fields.json 3553) 跨版本共享且偏 1.4.9-based —— 不可视为与 1.4.11 wire protocol 相等；1.4.11 的 cmd-diff 结论仅 INFERENCE，直到做 1.4.11 提取。
- 1.3.0 已解包（extracted/，293 文件/6.95MB，本次审计已核实目录树），各格存在性现为 CONFIRMED；仅「1.3.0」这一工程代号本身为 INFERENCE（内部版本串 NOW_VERSION=35/VERSION=100）。
- 1.4.9 与 1.4.11 的 config_function 均为 91 条（id-count），但各行内容 delta 未在此对比。
- 1.3.0 cmd_resolve 解包实际落于 extracted/config/protocal/（非 extracted/protocal/）。
- [C0 新增] game 模块数口径：旧 inventory/旧矩阵记 92/116/119（分文件提取口径），本矩阵采用 apk_scan zip 中央目录口径 85/108/111。
- [C0 纠正] item/mission/mall/partner 条数归属：旧矩阵记为 1.4.9 VERIFIED；按 HANDOFF.md（主兼容版本=1.4.11，server/ 服务该客户端）纠正为 1.4.11 VERIFIED（本脚本实测 server/*.json 计数）。1.3.0/1.4.9 条数无证据，保持 UNKNOWN，禁止按 ID 连续性推测。已剔除旧矩阵中「1.4.11 条数 UNKNOWN、1.4.9=3535」的过时 caveat。
- [C0] assets_bytes 为未压缩字节合计（MiB 口径）：135.1/241.3/276.2MB 与旧 inventory 数值一致；APK 压缩包体积 135.8/230.5/267.8MB 为本轮新增。
