# jstm_audit — 《绝世唐门》PHASE C0 只读审计脚本体系

本目录下全部脚本为**只读审计**：只读取 APK / 既有文件（analysis/、protocol/、server/、
analysis/jstm_game_systems/ 等），只向 `analysis/jstm_client_audit/`（及 `_raw/`）写新产物。
任何脚本都不修改 APK、`server/mock_server.py` 或 analysis 下既有文件。

运行环境：Windows PowerShell，`python` 已在 PATH；UTF-8 编码。

## 数据流向

```
anzbao/*.apk (1.3.0 / 1.4.9 / 1.4.11 三包)
        │  scan_apk.py（只读 zip 中央目录，不解包）
        ▼
analysis/jstm_client_audit/_raw/apk_scan_<ver>.json   ← 一切存在性判定的唯一事实来源
analysis/jstm_client_audit/_raw/apk_entries_<ver>.txt
analysis/jstm_client_audit/_raw/apk_scan_summary.json
        │
        ├── presence_lib.py（共享判定库，被各脚本 import）
        ├── gen_systems_master.py     ┐
        ├── gen_protocol_inventory.py │
        ├── gen_data_inventory.py     ├─► analysis/jstm_client_audit/<name>.json + .md
        ├── gen_ui_inventory.py       │   （最终交付物）
        └── gen_version_diff.py       ┘
        │
        ▼
audit_consistency.py（交叉核验全部交付物）
        ▼
analysis/jstm_client_audit/_raw/consistency_report.txt（每次运行覆盖）
```

版本写法约定：脚本命令行里用 `1.4.11`；raw 文件名内用下划线 `1_4_11`。

## 脚本清单

### 1. scan_apk.py — 三版本 APK 只读扫描器（事实来源）
- **用途**：只读 zip 中央目录，把三包条目粗分类（luac / config_*.luac / cmd_resolve_*.luac /
  UI 文件 / res 类目），并做跨版本 diff。可重复执行。
- **输入**：`anzbao/dldlJl.apk`(1.3.0)、`anzbao/jstm.apk`(1.4.9)、`anzbao/jstm_142165.apk`(1.4.11)。
- **输出**：`_raw/apk_entries_<ver>.txt`、`_raw/apk_scan_<ver>.json`、`_raw/apk_scan_summary.json`。
- **运行**（仓库根 `C:\Users\xu\Desktop\DSH` 下执行）：
  ```powershell
  python tools/jstm_audit/scan_apk.py                  # 全量扫三包
  python tools/jstm_audit/scan_apk.py --only 1.4.11    # 只扫单包
  python tools/jstm_audit/scan_apk.py --strings        # 额外抽 luac 可打印字符串样本
  ```
- 注意：脚本行为勿修改；向后兼容的增强需在本行说明。当前未做任何修改。

### 2. presence_lib.py — 三版本存在性判定共享库
- **用途**：被 audit_consistency.py 及各 gen_*.py import；不直接独立运行（附自检）。
- **输入**：`_raw/apk_scan_<ver>.json`（自动缓存）。
- **输出**：无文件输出。
- **主要 API**：
  - `load_scan(version)` → 原始 scan dict（缓存）
  - `module_present(ver, basename)` → `(bool, evidence_str)`：该 luac basename 是否在包内
  - `config_present(ver, basename)` → `(bool, evidence_str)`：是否在 config_tables
  - `cmdresolve_present(ver, n)` → `(bool, evidence_str)`：`cmd_resolve_<n>.luac` 是否存在
  - `ui_module_files(ver, module)` → 该模块 UI luac basename 列表
  - 批量集合：`luac_set / config_set / cmdresolve_set / game_module_set /
    ui_module_keys / res_category_set(ver)`
- **自检运行**：
  ```powershell
  python tools/jstm_audit/presence_lib.py
  ```

### 3. audit_consistency.py — 最终交付物交叉核验审计器
- **用途**：对 `analysis/jstm_client_audit/` 下全部 json/md 交付物做 a)~g) 七项核验
  （json 可解析+md 成对 / 协议 token 对齐 / 配置表存在性 / 数据清单对齐 / UI 清单对齐 /
  present_in_* 复算 / system 集合对齐）。缺失文件优雅跳过并在报告中标 SKIPPED。
  可重复运行，每次覆盖报告。
- **输入**：全部 `_raw/apk_scan_*.json` + 各交付物 `*.json`。
- **输出**：`_raw/consistency_report.txt`。
- **运行**：
  ```powershell
  python tools/jstm_audit/audit_consistency.py
  python tools/jstm_audit/audit_consistency.py --out C:\path\to\report.txt
  ```

### 4. gen_systems_master.py — 系统总目录生成器
- **用途**：以既有 124 系统骨架 + raw 扫描 + 协议字段 spec + mock_server 注册表，生成
  统一系统注册表（lua_modules / config_files / protocol_ids / present_in_* 等）。
- **输入**：`analysis/jstm_game_systems/systems_master.json`、`_raw/apk_scan_*.json`、
  `protocol/fields.json`、`protocol/cmd_table.json`、`server/mock_server.py`。
- **输出**：`systems_master.json/.md`、`system_dependency_graph.md`、`unimplemented_systems.md`。
- **运行**：
  ```powershell
  python tools/jstm_audit/gen_systems_master.py
  ```

### 5. gen_protocol_inventory.py — 协议总目录生成器
- **用途**：汇总 CS/SC 协议（cmd、方向、字段、触发模块、版本存在性）。
- **输入**：`protocol/fields.json`、`protocol/cmd_table.json`、`protocol/registry_classes.json`、
  `analysis/jstm_game_systems/systems_master.json`、`_raw/apk_scan_*.json`、
  `analysis/jstm_1.4.9/*_protocol.md`、`analysis/extraction/*.md`、`server/proto_defs.py`。
- **输出**：`protocol_inventory.json/.md`。
- **运行**：
  ```powershell
  python tools/jstm_audit/gen_protocol_inventory.py
  ```

### 6. gen_data_inventory.py — 数据资源总目录生成器
- **用途**：按业务类别汇总数据表（config_files 按版本列出、计数、id_range）。
- **输入**：`_raw/apk_scan_*.json`、`analysis/version_compare/1.3.0/extracted/config/*.luac`、
  `server/*.json`、`server/cfg/*.json`、`analysis/extraction/{truth_values,monster_values}.json`。
- **输出**：`data_inventory.json/.md`。
- **运行**：
  ```powershell
  python tools/jstm_audit/gen_data_inventory.py
  ```

### 7. gen_ui_inventory.py — UI 清单生成器
- **用途**：以 1.4.11 `ui_by_module`(115 模块) 为骨架，逐界面列模块、入口 luac、
  资源类、状态分级。
- **输入**：`_raw/apk_scan_*.json`、`analysis/jstm_game_systems/systems_master.json`。
- **输出**：`ui_inventory.json/.md`。
- **运行**：
  ```powershell
  python tools/jstm_audit/gen_ui_inventory.py
  ```

### 8. gen_version_diff.py — 三版本差异矩阵生成器
- **用途**：在 24 系统差异骨架上，用 raw 扫描与 server 配置实测计数填充版本差异。
- **输入**：`analysis/version_compare/version_diff_matrix.json`、`_raw/apk_scan_summary.json`、
  `_raw/apk_scan_*.json`、`server/{item_config,mission_config,mall_config,partner_config}.json`。
- **输出**：`version_diff_matrix.json/.md`。
- **运行**：
  ```powershell
  python tools/jstm_audit/gen_version_diff.py
  ```

> 附：`_verify.py` 是生成方的临时自检脚本，不属于正式交付链路，重跑前先确认其内容。

## 推荐执行顺序

```powershell
cd C:\Users\xu\Desktop\DSH
python tools/jstm_audit/scan_apk.py            # 1) 先刷新 raw 事实来源
python tools/jstm_audit/gen_systems_master.py  # 2) 各生成器（彼此独立，顺序不限）
python tools/jstm_audit/gen_protocol_inventory.py
python tools/jstm_audit/gen_data_inventory.py
python tools/jstm_audit/gen_ui_inventory.py
python tools/jstm_audit/gen_version_diff.py
python tools/jstm_audit/audit_consistency.py   # 3) 最后交叉核验
```

## 核验口径备注（见 consistency_report.txt 对应章节）

- raw `config_tables` 只枚举 `config_*.luac`；交付物中出现的 `.json` 配置表不在此清单内，
  报告把它们单列在 info 段，不算硬冲突。
- `present_in_*` 复算口径为保守重推导（lua_modules/client_entry/config basename 命中 raw
  即 true）；gen_systems_master 的规则额外允许 protocol-chunk 等证据，报告中的冲突项需人工复核。
