# -*- coding: utf-8 -*-
"""server.persistence —— Phase 2 SQLite 持久层（壳）。

Phase 2 step 0：仅建壳。实际 DB 访问目前仍在 server/mock_server.py：
  - DB_PATH / STATE_DIR        -> mock_server.py L4197 / L5328
  - db_conn() / db_release()   -> mock_server.py L4220–4258（线程本地连接池）
  - db_init()                  -> mock_server.py L4274–4322（建 6 张主表）
  - 其余 49 张表由各 db_*_init() 零散建（见 schema.py 清单）
集中 schema 登记见本包 schema.py（只读清单 + 黄金 schema 引用，不改动 db_init 执行）。
"""
