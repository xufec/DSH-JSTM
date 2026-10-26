# 1.3.0（dldlJl.apk）资源盘点 — 已解包

> 更新：PHASE 0 后续。**本版本已实际解包**（此前为 UNKNOWN）。
> 目标文件：`anzbao/dldlJl.apk`（135.8MB，渠道 ewan/91CW）。

## 一、版本自证（CONFIRMED，读自 `assets/src/config.luac` 明文）

| 项 | 值 |
|---|---|
| `VERSION` | **100**（"1.0.100" 前缀，展示用） |
| `NOW_VERSION` | **35** |
| `BUILD_VERSION` | 10 |
| `PLATFORM_NAME` | `ewan` |
| `GAME_NAME` | 绝世唐门 |
| `URL_LUA_CONFIG` | `http://cdnres.jstm.shiyuegame.com/update/config/url_config_ewan.lua` |

> **结论**：该包内部版本为 `NOW_VERSION=35 / VERSION=100`，**并非字面上的 "1.3.0"**。
> "1.3.0" 是本工程给出的代号；使用时须注明这是**最旧包**，实际版本串为 1.0.100/35。证据等级：CONFIRMED。

## 二、结构统计（CONFIRMED，直接读 APK 条目）

| 指标 | 1.3.0 (dldlJl) | 1.4.9 (jstm) | 1.4.11 (jstm_142165) |
|---|---|---|---|
| 总条目 | **10,670** | 16,379 | 19,106 |
| `.luac` 总数 | **1,557** | 2,234 | 2,297 |
| `assets/src/**.luac` | **1,557** | 2,234 | 2,297 |
| `config_*.luac` 表 | **168** | 227 | 233 |
| `cmd_resolve_*.luac` | **89** | 122 | 124 |
| game 模块目录 | **92** | 116 | 119 |
| assets 总字节 | 135.1 MB | 241.3 MB | 276.2 MB |

来源：`analysis/version_compare/_apk_structural_compare.json`（脚本 `_compare3apk.py`）。

## 三、已解包内容（本次）

落盘目录：`analysis/version_compare/1.3.0/extracted/`（**293 文件 / 6.95 MB**）

| 类别 | 数量 | 路径 |
|---|---|---|
| 配置表 `config_*.luac` | 165 | `extracted/config/` |
| `cmd_resolve_*.luac` + `all_proto.luac` | 90 | `extracted/protocal/` |
| `config.luac` / `version.luac` / `protocalrulesmgr.luac` | 3 | `extracted/` |
| 1.3.0 独有模块 `jingjie`(境界) | 9 | `extracted/game/jingjie/` |
| 1.3.0 独有模块 `garden`(庄园) | 6 | `extracted/game/garden/` |
| 1.3.0 独有模块 `moneytree`(摇钱树) | 3 | `extracted/game/moneytree/` |
| 1.3.0 独有模块 `xiulianhulu`(修炼葫芦) | 1 | `extracted/game/xiulianhulu/` |
| 其它（view/rank/chongzhi/sys） | 16 | 各自目录 |

完整条目清单：`analysis/version_compare/1.3.0/_apk_entries.txt`（10,670 行）。

## 四、1.3.0 相对 1.4.11 的独有内容（找回对象）

**仅 1.3.0 有、1.4.11 已无的模块（4 个）**：`garden`（庄园）、`jingjie`（境界）、`moneytree`（摇钱树）、`xiulianhulu`（修炼葫芦）。
> 注意：`moneytree`、`garden` 在 1.4.11 以配置表形式仍在（`config_money_tree`、`config_garden_data`），
> 属**改名/合并**而非删除；`jingjie`、`xiulianhulu` 需在 1.4.11 中另行确认是否被删除（当前列 UNKNOWN）。

**仅 1.3.0 有的配置表（1 个）**：`config_holiday.luac`（1.4.11 拆成 `config_holiday_*` 系列）。

**1.4.11 新增（1.3.0 无）的 66 张配置表** 与 **31 个新模块**（auction/blackmarketeer/chair/chief/crossdungeon/endless/footmark/friendback/godwar/gradebreak/guildrace/guildsecretarea/guildtarget/halo/jewelvip/kunshentower/loadres/mine/peakwar/scratcher/script/soulstar/sworn/treasure_plane/yuangu/yuanshen/battlevideo/actionanswer/animaequip/contact 等）
见 `_apk_structural_compare.json` 的 `diffs` 字段。

## 五、证据等级

| 结论 | 等级 |
|---|---|
| 条目数/配置表数/模块数 | CONFIRMED（直接读 APK） |
| VERSION/NOW_VERSION 等版本串 | CONFIRMED（config.luac 明文） |
| "1.3.0" 名称 | INFERENCE（工程代号，非内部版本串） |
| `jingjie`/`xiulianhulu` 在 1.4.11 是否被删除 | UNKNOWN（需在 1.4.11 全量配置中确认） |
