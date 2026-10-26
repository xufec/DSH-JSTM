# -*- coding: utf-8 -*-
"""server.protocol —— Phase 2 帧编解码（壳）。

Phase 2 step 0：仅建壳。实际编解码函数目前仍在 server/mock_server.py：
  - w_u8 / w_u16 / w_u32 / w_str / pack_frame   -> mock_server.py L1589–1610
  - class FrameParser（大端 u32 长度 + u16 cmd + body）-> mock_server.py L1611–1633
  - CMD_NAMES                                   -> mock_server.py L1576–1588
  - ver_family_of(body_len, args)               -> mock_server.py L4259 附近
本包不复制实现，只登记迁移锚点。
"""
