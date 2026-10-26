# -*- coding: utf-8 -*-
"""server.session —— Phase 2 连接/会话层（壳）。

Phase 2 step 0：仅建 __init__.py。未来归属（phase2_design.md §二 core/session/）：
  - LIVE_CONNECTIONS / LIVE_LOCK 在线注册表   -> mock_server.py L233–234
  - 每连接版本族 CUR_VER                       -> mock_server.py L4256 / L9298
  - _register_live / _unregister_live / handle -> mock_server.py L9245–9308
  - push_to_rid / _scene_* 会话推送           -> mock_server.py L469–662
本步不搬迁任何变量或函数。
"""
