# -*- coding: utf-8 -*-
"""server.core —— Phase 2 运行时核心（壳）。

Phase 2 step 0：仅建壳，不搬迁任何已有逻辑。
未来归属（见 analysis/phase2_design.md §1.4 / §二）：
  - runtime.py  单例运行时（CFG / LIVE_CONNECTIONS / LIVE_LOCK / CUR_VER / ROLE_CACHE）
  - dispatch.py 命令分发表兼容层（DISPATCH_TABLE + register + handle + shadow_lint）
"""
