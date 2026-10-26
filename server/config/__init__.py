# -*- coding: utf-8 -*-
"""server.config —— Phase 2 运行配置层（壳）。

Phase 2 step 0：仅建壳。四套配置来源与加载函数目前仍在 server/mock_server.py / server/：
  - config.json（DEFAULT_CFG L138–149；运行时 CFG L232；main() 读 CFG_PATH）
  - cfg/         目录（231 个业务配置 json）
  - cfg_kconst/  目录（285，kconst_* 读取见 mock_server.py L3237–3370）
  - cfg_kconfig/ 目录（245，_kcfg_fields/_kcfg_row 见 L3370–3446）
  - cfg_kconfig2/目录（245，kcfg2/kcfg2_rows 见 L3762–3787）
配置热改 /DSH_ADMIN/reload 见 mock_server.py L1342。本步不搬实现。
"""
