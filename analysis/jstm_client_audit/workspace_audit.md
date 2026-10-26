# 当前工作区与项目结构审计（PHASE C0）

> 审计日期：2026-10-15。**只读审计**：未修改任何既有文件，仅新建本任务指定产物。
> 数据来源：目录枚举（文件数/字节数）、`HANDOFF.md`（2026-10-02 更新）、`analysis/PHASE0_AUDIT*.md`、`tests/1.4.11/FINAL_REGRESSION.md`、apk_scan 证据。
> 证据等级沿用五档：CONFIRMED / VERIFIED / STRONG_INFERENCE / INFERENCE / UNKNOWN。

---

## 一、项目根目录树摘要（C:\Users\xu\Desktop\DSH）

| 目录 | 规模（文件数 / 体积） | 用途 | 审计备注 |
|---|---|---|---|
| `analysis/` | 1528 / 814.7MB | 分析产物主目录（见第二节） | 含 `_tmp/`(72 项)、`1.4.9/`(325 项) 提取中间产物 |
| `anzbao/` | 6 / 634.3MB | 3 个原版 APK：`dldlJl.apk`(1.3.0)、`jstm.apk`(1.4.9)、`jstm_142165.apk`(1.4.11) | 唯一 APK 真值来源；只读 |
| `patched/` | 50 / 6,147.1MB | 1.4.11 补丁包（`jstm_1411_fakelogin_aligned.apk` 等） | 体积大，含历史补丁 APK |
| `server/` | 9634 / 330.2MB | mock_server 主服务 + 模块群 + 配置 JSON + 历史备份 | 见第二节；含大量 `_*.py` 一次性脚本与 `.bak_rXXX` 备份链 |
| `tools/` | 47988 / 15,870.3MB | 工具集（jadx/dexdump/frida/lua 反编译等第三方目录 + 数百脚本） | 绝大部分为一次性 diag/probe/fix 脚本，**仅少数可复用** |
| `protocol/` | 8 / 3.2MB | 共享协议 registry：`cmd_table.json`(1643 条)、`fields.json`(3553 条) | **1.4.9-based，不可等同 1.4.11 wire**（INFERENCE） |
| `tests/1.4.11/` | 4 文件 | `FINAL_REGRESSION.md`、`regression_baseline.md`(97KB)、`NEW_SYSTEMS_REGRESSION.md`、`RUN_TESTS.ps1` | 回归基线存档 |
| `docs/` | 7 / 0.3MB | 文档 | 小规模 |
| `report/` | 113 / 4.8MB | 报告存档 | |
| `logs/` | 177 / 103.9MB | 运行日志 | 历史运行证据，非交付物 |
| `backup/` | 21 / 3.8MB | 备份（含 `replay_before.json` 战斗重放锚点） | |
| `cankao/` | 5 项目 / 594.9MB | 5 个参考游戏项目（Survive/kongkongxiyou/CXEngine/YZXY/MahatmaComeBack/ChivalrousMan） | **仅借架构；协议/数值/规则一律禁用**（HANDOFF 第十节纪律） |
| `_tmp_cfg/` | 305 / 16.2MB | 1.4.11 配置提取（`_tmp_cfg\`） | HANDOFF 登记的正式提取目录 |
| `shots/` `photo/` | 34 / 11 文件 | 实机截屏 | 运行证据 |
| `001/` | 76780 / 8,053.1MB | **未登记目录**（疑似大批量解包/反编译中间产物） | HANDOFF 未记载；按暂存对待，不可当证据引用 |
| `null/` | 8 / 7.1MB | 异常命名目录（疑似命令输出误重定向产物） | 暂存 |
| `skill/` | 692 / 12.1MB | 技能/脚本资源 | |
| `PowerShell 7.5.4/` | — | 疑似误落的运行时目录 | 非项目资产 |
| `.dsh-vision-router/` `.trae-html-share-packages/` | — | 工具运行配置目录 | 非项目资产 |
| 根目录 20+ 个 `_tmp_*`（`_tmp_battle`、`_tmp_fashion`、`_tmp_wedding` 等） | 各数文件 | 探针/提取暂存 | **临时目录，不可当作完成证据** |

---

## 二、可复用资产清单

### 2.1 `analysis/jstm_client_audit/`（本阶段 C0 审计产物）

| 路径 | 内容 | 规模 | 证据等级 |
|---|---|---|---|
| `systems_master.json` / `.md` | 系统百科（124 系统） | 213KB / 14.8KB | STRONG_INFERENCE~CONFIRMED |
| `protocol_inventory.json` / `.md` | 协议清单 | 2.1MB / 491KB | CONFIRMED（基于 registry + 提取） |
| `ui_inventory.json` / `.md` | UI 文件清单（1.4.11） | 378KB / 70KB | CONFIRMED |
| `system_dependency_graph.md` | 系统依赖图 | 5.9KB | INFERENCE |
| `unimplemented_systems.md` | 未实现系统清单（42 项） | 20KB | STRONG_INFERENCE |
| `_raw/apk_scan_summary.json` + 三份 `apk_scan_*.json` + `apk_entries_*.txt` | 三版本 zip 中央目录只读扫描 | 59KB+ | **CONFIRMED**（C0 主证据） |
| `version_diff_matrix.json` / `.md`（本任务产出） | 三版本差异矩阵 39 维 | 11.5KB md | 见矩阵内逐格标注 |
| `workspace_audit.md`（本任务产出） | 本文件 | — | — |

### 2.2 `analysis/version_compare/`（上一轮三版本对比，**勿改**）

| 路径 | 内容 | 证据等级 |
|---|---|---|
| `version_diff_matrix.json` / `.md`（2026-10-02） | 24 系统骨架矩阵；1.4.11 的 item/mission/partner/mall 条数原标 UNKNOWN | CONFIRMED（存在性） |
| `_apk_structural_compare.json` | 三版 APK 结构对比明细（39KB） | CONFIRMED |
| `1.3.0/inventory.md` + `extracted/`（293 文件/6.95MB） | 1.3.0 已解包；版本自证 NOW_VERSION=35/VERSION=100（"1.3.0"=工程代号 INFERENCE） | CONFIRMED |
| `1.4.9/inventory.md` | 1.4.9 盘点（NOW_VERSION=186, qihoo） | CONFIRMED |
| `1.4.11/inventory.md` | 1.4.11 盘点（NOW_VERSION=208, baidu2，主目标） | CONFIRMED |
| `_compare3apk.py` / `_update_matrix.py` | 旧对比脚本 | — |

### 2.3 其他 analysis 子目录

| 路径 | 内容 | 规模 | 证据等级 |
|---|---|---|---|
| `analysis/jstm_game_systems/` | systems_master(139KB/119KB)、依赖图、`unimplemented_systems.md`(28KB) | 6 项 | STRONG_INFERENCE |
| `analysis/1.4.9/` | 1.4.9 提取目录（battle/item/mission/npc/scene/shop/task/ui 等子目录 + config JSON） | 325 项 | CONFIRMED（提取层） |
| `analysis/jstm_1.4.9/` | 16 份分系统协议文档（login/role/inventory/equipment/skill/partner/task/scene/movement/battle/dungeon/chat/social/gm）+ `_impl_cmds.txt`/`_observed_cmds.txt` | 18 项 | CONFIRMED |
| `analysis/extraction/` | 55 项：`truth_values.json/md`（CONFIRMED 真值 10+ 项）、`gap_dig.json/md`、`monster_values.json/md`、`ui_display_values.json/md`、`ui_button_map.json/md`、`xiulian_frame_spec.md`、`patrol_button_spec.md`、phase1 系列账本 | 55 项 | CONFIRMED~VERIFIED（逐项见文件头） |
| `analysis/runtime_evidence/` | 实机证据：`shots/`、`frames/`、`probes/`、calibration_R/V、`runtime_findings.md` | 8 项 | VERIFIED（实机） |
| `analysis/server_reference/` | 参考项目对照（`FINAL_SERVER_ARCHITECTURE.md`、license_audit、6 个参考项目子目录） | 12 项 | 仅架构参考 |
| `analysis/_tmp/` | 72 项临时分析文本 | — | 暂存，勿当交付 |
| `analysis/` 根散落 `_*.txt`/`*.luac` | 数百份反编译/探针转储（`_npc_dialogs.txt` 等） | — | 原始证据，需配合说明使用 |

### 2.4 `server/`（mock_server 现状）

- 主服务：`mock_server.py`（约 18.5k 行单体，1.09MB；改前存 `.bak_rXXX`，现存 100+ 个 `.bak_r*` 历史快照）；TCP 9000 + HTTP 8080 `/DSH_ADMIN`。
- 模块群：`core/persistence/protocol/attribute/currency/role/task/equipment/scene/npc/item/inventory/skill/partner/wing/soulbone/fashion/artifact/destiny/formation/dungeon/afk/shop/package/activity/reward/social/guild/ranking/mail/achievement/gm/` 等。
- 自检：`min_loop_server.py`，基线 **145/145 PASS**。
- 配置真值（1.4.11，本任务实测）：`item_config.json`=3535 条、`mission_config.json`=846、`mall_config.json`=142、`partner_config.json`=53。
- 注意：`server/` 根目录下 `_*.py`/`_*.json` 数百个一次性修复/探针脚本（`_fix_rXXX.py`、`_p2b_wire*.py`、`_diag_rXXX.py`）与大量 `.bak_rXXX` 备份，**均为历史过程产物，不是当前代码资产**。

### 2.5 `tools/`（提取脚本）

- 可复用：`tools/jstm_audit/scan_apk.py`（C0 三版 APK 扫描器）、`gen_data_inventory.py` / `gen_protocol_inventory.py` / `gen_systems_master.py` / `gen_ui_inventory.py`、本任务新增 `gen_version_diff.py`。
- 历史脚本：`extract_config*.py`、`dump_config_luac.py`、数百个 `verify_*/test_*/_fix_r*` 一次性脚本——可查参考，不可当稳定资产。

---

## 三、已完成闭环（依据 HANDOFF.md + regression 报告）

**已闭环系统（37 项，HANDOFF 第四节）**：登录 / 角色 / 等级 / 经验 / 背包 / 仓库 / 装备 / 任务 / 商城 / 黑市 / 邮件 / 排行 / 副本 / 挂机 / 签到 / 日常 / 成就 / 结拜 / 结婚 / 拍卖 / 法宝 / 翅膀 / 坐骑 / 魂兽 / 元神 / 神器 / 命格 / 椅子 / 时装 / 光环 / 符文 / 投资 / BOSS / 称号 / 阵法书 / 伙伴面板 / 技能学习 / GM Manager。

**基线**：miniloop **145/145 PASS**；`/status` lv70/gold=1799840/coin=9904599/scene=10001；battle_replay 两次重放 hex 一致；shadow_lint 干净。
**registered CS 命令**：19 个（1110/10101/10200/10301-10304/10306/10502/10601/10610/10622/10651/11215/11600/12400/12401/12408/15203）。

---

## 四、缺口与风险

### 4.1 HANDOFF 登记的 9 项缺口（截至 2026-10-02）
1. 怪物 HP/ATK 真值 UNKNOWN（公式在服务端）
2. 伙伴基础喂养消耗 UNKNOWN（需先获得伙伴实机取证）
3. 宝石镶嵌加成：总属性表已接线，单宝石拆分 INFERENCE
4. 修炼 UI "50" 语义 CONFIRMED（=本级进度满值）
5. **修炼消耗/拥有 EXP 下发：进行中**（practice_exp 已=35，待用户二次回证上屏）
6. 巡逻按钮激活条件 待证
7. chengjiu_has.state 子字段语义 UNKNOWN
8. 真服全量数值标定 待办（真服大概率已下线）
9. 20002 战斗族注册：裁定保留旧链，不再下沉

### 4.2 本矩阵仍 UNKNOWN 的单元格（数量类）
- 1.3.0 / 1.4.9 的 item / mission / mall / partner 逐条配置条数 = UNKNOWN（仅 config 表存在性 CONFIRMED；禁止按 ID 连续性推测）。
- 1.4.11 的货币 id 集合粒度、单资产文件清单、config_function 行级 delta、跨版本行级 table-count diff = UNKNOWN。
- 1.4.11 wire protocol 与共享 registry（1.4.9-based）一致性 = INFERENCE。

### 4.3 不可当作"完成"的内容（暂存/临时）
- 根目录 20+ 个 `_tmp_*`、`analysis/_tmp/`(72 项)、`server/scratch/`、`001/`(8GB)、`null/`、`PowerShell 7.5.4/`、`shots/` 与 `photo/` 的区别等——均为过程产物或误落目录。
- `server/` 下 `_fix_r*.py`/`_diag_r*.py`/`.bak_rXXX` 备份链——历史过程，非当前代码。
- `cankao/` 参考项目的任何协议/数值——**纪律性禁用**。
- `protocol/cmd_table.json`、`fields.json`——1.4.9-based，引用时必须标注，不可直接当 1.4.11 wire 真值。
- `analysis/1.4.9/` 的 UI 语料仅部分反编译，覆盖度不足；"不存在"不得反推。

---

## 五、审计方法自检
- 目录规模枚举：PowerShell 递归统计（只读）。
- 配置计数：`python` 实测 `server/*.json` 顶层条目（item=3535 / mission=846 / mall=142 / partner=53）。
- 三版本指标：全部来自 `_raw/apk_scan_*.json`（zip 中央目录只读扫描），未反编译、未修改 APK。
- 既有文件零修改：`analysis/version_compare/` 全程只读。
