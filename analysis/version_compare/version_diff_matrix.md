# 绝世唐门 / JSTM — 三版本差异矩阵 (PHASE 0 audit, 1.3.0 已解包核实)

证据等级：**CONFIRMED**（直接读 APK / 解包数据）/ **VERIFIED**（实机 + 服务器验证）/ **STRONG_INFERENCE** / **INFERENCE** / **UNKNOWN**。

> ✅ **1.3.0 已完成解包并经本次审计核实**（`anzbao/dldlJl.apk`）。落盘 `1.3.0/extracted/` = **293 文件 / 6.95 MB**。
> 其内部版本串为 `NOW_VERSION=35 / VERSION=100`（`ewan` 渠道，`config.luac` 明文），「1.3.0」为本工程代号（INFERENCE）。
> 详见 `1.3.0/inventory.md`。注意：cmd_resolve 实际落于 `extracted/config/protocal/`（非 `extracted/protocal/`）。

## 〇、结构统计（CONFIRMED，直接读三个 APK，来源 `_apk_structural_compare.json`）

| 指标 | 1.3.0 (dldlJl) | 1.4.9 (jstm) | 1.4.11 (jstm_142165) |
|---|---|---|---|
| 总条目 | 10,670 | 16,379 | 19,106 |
| .luac 总数 | 1,557 | 2,234 | 2,297 |
| config_*.luac | 168 | 227 | 233 |
| cmd_resolve_*.luac | 89 | 122 | 124 |
| game 模块目录 | 92 | 116 | 119 |
| assets 字节 | 135.1 MB | 241.3 MB | 276.2 MB |

模块差异（CONFIRMED，diff 字段实算）：
- **仅 1.3.0 有、1.4.9/1.4.11 已无的 game 模块（4 个）**：`garden`(庄园) / `jingjie`(境界) / `moneytree`(摇钱树) / `xiulianhulu`(修炼葫芦)。
  其中 `config_garden_data.luac`、`config_money_tree.luac` 在 1.4.11 仍在（配置表保留、模块删除/合并，属改名/合并而非纯删除）；`jingjie`/`xiulianhulu` 在 1.4.11 是否彻底删除仍 UNKNOWN。
- **1.4.11 相对 1.3.0 新增的 game 模块（31 个）**：auction / animaequip / actionanswer / battlevideo / blackmarketeer / chair / chief / contact / crossdungeon / endless / flyup / footmark / friendback / godwar / gradebreak / guildrace / guildsecretarea / guildtarget / halo / jewelvip / kunshentower / loadres / mine / peakwar / scratcher / script / soulstar / sworn / treasure_plane / yuangu / yuanshen。
- **1.4.11 相对 1.3.0 新增 config 表 66 张**；**1.3.0 独有 config 表 1 张**：`config_holiday.luac`（在 1.4.9/1.4.11 拆分为 `config_holiday_*` 系列，属重命名/拆分）。
- cmd_resolve：1.4.11 较 1.3.0 多 35 个（`cmd_resolve_187..221/300..313` 段），1.3.0 无独有 cmd_resolve。

## 一、逐系统矩阵（24 维度）

> 版本列取值仅限 **存在 / 不存在 / 未知**；数量级与反编译覆盖度差异见备注。
> 变化列取值仅限 **新增 / 删除 / 修改 / 重命名 / 未知**（维度级）；子项级 新增/删除/重命名 明细见备注。
> 经本次核实，24 个维度在三个版本中**均存在**（差异为程度/内容演化，无整个维度被新增或删除）。

| 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 变化 | 备注 / evidence |
|---|---|---|---|---|---|
| Lua模块 | 存在 | 存在 | 存在 | 修改 | 1.3.0: 1557 luac / 92 game 模块；1.4.9: 2234/116；1.4.11: 2297/119。1.4.11 新增 31 模块、含大量 _ctrl/_panel/_view UI 模块。1.4.9 仅部分反编译。CONFIRMED（三版均直接读 APK）。 |
| cmd | 存在 | 存在 | 存在 | 修改 | 共享同一 cmd registry 结构；条目数随 cmd_resolve 增长（89→122→124）。共享 registry `protocol/cmd_table.json`=1643 条为 1.4.9-based，不视为与 1.4.11 wire 格式相等。CONFIRMED（存在性）；1.4.11 cmd-diff 仅 INFERENCE。 |
| protocol | 存在 | 存在 | 存在 | 修改 | 共享 registry（`fields.json`=3553）；1.4.9 已分系统整理。1.3.0 解包内含 `all_proto.luac`（落于 `extracted/config/protocal/`）。存在性 CONFIRMED；1.4.11 wire 一致性 INFERENCE。 |
| cmd_resolve | 存在 | 存在 | 存在 | 修改 | 计数 1.3.0: 89；1.4.9: 122；1.4.11: 124。1.4.11 较 1.3.0 新增 35 个（187..221/300..313 段）；1.3.0 无独有。1.4.11 另有 `server_cmds.json`/`protocalrulesmgr.luac`。CONFIRMED。 |
| config | 存在 | 存在 | 存在 | 修改 | config_*.luac 计数 1.3.0: 168；1.4.9: 227；1.4.11: 233。1.4.11 新增 66 表（auction/black_market/fashion/holiday_*/mine/partner_fetter/score/shenqi 等）。CONFIRMED。 |
| item | 存在 | 存在 | 存在 | 修改 | 三版均含 `config_item.luac` 及其 fuse/gift/misc/type_name 族。1.4.9 server item_config=3535（VERIFIED）；**1.4.11 item 条数未逐表提取 = UNKNOWN**。存在性 CONFIRMED。 |
| equipment | 存在 | 存在 | 存在 | 修改 | 三版均含 `config_intensify.luac`/`config_eqm_starup_data.luac`。1.4.11 新增 `config_eqm_ancient.luac`/`config_red_eqm.luac`/`config_fabao.luac`。存在性 CONFIRMED。 |
| skill | 存在 | 存在 | 存在 | 修改 | 三版均含 `config_skill.luac` + bullet/magic/scene/talent/trigger/xiulian 全家。存在性 CONFIRMED。 |
| task | 存在 | 存在 | 存在 | 修改 | 三版均含 `config_mission.luac` + buffy/escort/help/kill_demon/loop/marry/treasure 族。1.4.9 server mission_config=846（VERIFIED）；**1.4.11 mission 条数未提取 = UNKNOWN**。存在性 CONFIRMED。 |
| partner | 存在 | 存在 | 存在 | 修改 | 1.3.0 含 hero 模块 + `config_partner_base/misc/skill.luac`；1.4.11 新增 fetter/score/shenqi 三表（共 6 表）。1.4.9 server partner_config=53（VERIFIED）；**1.4.11 partner 条数未提取 = UNKNOWN**。存在性 CONFIRMED。 |
| dungeon | 存在 | 存在 | 存在 | 修改 | 1.3.0 已有 `config_dungeon_new/tower/vip_single.luac`。1.4.11 新增 endless/gods/jieyi/rune/seal_demon/vip_single2 + kunshentower/crossdungeon 模块。存在性 CONFIRMED。 |
| activity | 存在 | 存在 | 存在 | 修改 | 三版 `config_function.luac` 入口均为 91（id-count，VERIFIED）。1.3.0 无 auction/peakwar/holiday_* 系列；1.4.11 新增 config_act/fest_data/holiday_*（重命名自 config_holiday）等。存在性 CONFIRMED。 |
| shop | 存在 | 存在 | 存在 | 修改 | 三版均含 `config_mall.luac`/`config_shop.luac`/`config_market.luac`。1.4.9 server mall_config=142（VERIFIED）；**1.4.11 mall 条数未提取 = UNKNOWN**。存在性 CONFIRMED。 |
| currency | 存在 | 存在 | 存在 | 修改 | 三版同源 `config_game_data.luac`（AssetsEnToCode 资产/货币枚举）；精确货币 id 集合未逐一枚举。存在性 STRONG_INFERENCE（同源引擎），集合粒度 UNKNOWN。 |
| UI | 存在 | 存在 | 存在 | 修改 | 1.3.0 存在 UI 模块（1557 luac 内）但数量少于 1.4.11；1.4.9 UI corpus 仅部分反编译（_mission/_npc/_story 等后代文件）；1.4.11 有完整 _ctrl/_panel/_view。存在性 CONFIRMED；1.4.9 覆盖度为部分（提取层面，非 UI 不存在）。 |
| scene | 存在 | 存在 | 存在 | 修改 | 三版均含 map 模块 + `config_map.luac`/map_block/map_npc/map_icon_pos/map_partical/world_map。存在性 CONFIRMED。 |
| NPC | 存在 | 存在 | 存在 | 修改 | 三版均含 npc 模块 + `config_npc.luac`。存在性 CONFIRMED。 |
| monster | 存在 | 存在 | 存在 | 修改 | 三版均含 ghost/boss 模块 + `config_mon_data.luac`。存在性 CONFIRMED。 |
| GM | 存在 | 存在 | 存在 | 修改 | 三版均含 gm_report 模块 + `config_gm_cmd.luac`。存在性 CONFIRMED。 |
| system entry | 存在 | 存在 | 存在 | 修改 | `config_function.luac` 入口三版均为 91（VERIFIED）；但 1.4.11 功能模块总数多于 1.3.0（后者 92 vs 119 game 模块）。存在性 CONFIRMED。 |
| resources | 存在 | 存在 | 存在 | 修改 | 1.3.0 assets 135.1MB vs 1.4.11 276.2MB（直接读 APK 字节数，CONFIRMED）；1.4.9 有 `_assets_config.json`，资源清单完整性未全枚举。存在性 CONFIRMED。 |
| strings | 存在 | 存在 | 存在 | 修改 | 三版均含文案/常量表：1.3.0 `config_color.luac`/`config_color_code.luac`/`config_notice.luac`；1.4.11 另增 `config_chat_bubble.luac` 等。存在性 CONFIRMED。 |
| assets | 存在 | 存在 | 存在 | 修改 | 总条目 1.3.0: 10670；1.4.9: 16379；1.4.11: 19106（直接读 APK，CONFIRMED；旧版本表曾误标 1.4.11=未知，已修正）。单个资产文件清单未逐一枚举。存在性 CONFIRMED。 |
| data tables | 存在 | 存在 | 存在 | 修改 | 1.3.0 168 配置表 ⊂ 1.4.11 233（仅 `config_holiday.luac` 为 1.3.0 独有，1.4.11 拆为 config_holiday_* 系列 = 重命名/拆分）；item/skill/partner/mission/dungeon/activity 等大量重叠。精确 table-count 行级 diff UNKNOWN。存在性 CONFIRMED。 |

**Systems counted: 24.**

### Evidence notes
- 协议注册表（`protocol/cmd_table.json` 1643 / `fields.json` 3553）跨版本共享、偏 1.4.9；不可视为与 1.4.11 wire protocol 相等。1.4.11 专属 cmd 差异标 INFERENCE，直至做 1.4.11 提取。
- 1.3.0 各格存在性现为 **CONFIRMED**（已解包并经本次审计核实目录树）；仅「1.3.0」这一工程代号本身为 INFERENCE。
- 1.4.11 的 item / task / partner / mall 逐条计数仍未提取 ⇒ 相关 count 标 **UNKNOWN**（仅存在性 CONFIRMED）；1.4.9 的对应 count（3535/846/53/142）为 VERIFIED（服务器）。
- 1.3.0 解包落盘：`extracted/config/`（165 文件，其中 164 个精确匹配 config_*.luac）、`extracted/config/protocal/`（90 文件 = 89 cmd_resolve + all_proto.luac）、`extracted/game/{jingjie:9,garden:16,moneytree:5,xiulianhulu:1,chongzhi:1,rank:2}`、`extracted/sys/protocalrulesmgr.luac`、根级 config.luac/config_demo.luac/version.luac。合计 293 文件 / 6.95 MB。
