# -*- coding: utf-8 -*-
"""npc.handler —— NPC 命令（Phase 2d）。

注册命令：15203（NPC 对话框应答）。
迁移来源（mock_server.py _reply if 块 L15645–15653）。
注：15202（挂机怪发起战斗，闭含 mon_def）留旧链。
"""

from core import runtime
from core.dispatch import register
from protocol.frame import w_u8, w_str, pack_frame

log = runtime.log


@register(15203)
def handle_15203(h, cmd, body):
    """CS_15203（空）→ SC_15203{code:uint8, msg:string}"""
    pkt = pack_frame(15203, w_u8(0) + w_str(''))
    h.request.sendall(pkt)
    log('tcp.log', '  << 15203 SC_15203 code=0 (%d bytes)' % len(pkt))
    return True
