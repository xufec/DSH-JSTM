# -*- coding: utf-8 -*-
"""scene.handler —— 场景命令（Phase 2d）。

注册命令：10200（进入场景 CSRoleEnter）。
迁移来源（mock_server.py _reply if 块 L15244–15259）。
注：10201（地图格 build_10201 闭含 npcs/mons/elems）、10204/10205（AOI 子系统）
    闭包太深，本批留旧链，DB 落库行为保持不变。
"""
import struct

from core import runtime
from core.dispatch import register
from protocol.frame import w_u8, w_u16, w_u32, w_str, pack_frame

log = runtime.log


@register(10200)
def handle_10200(h, cmd, body):
    """CSRoleEnter_10200{bid:uint32}
       → SCRoleEnter_10200{code:uint8, msg:string, bid:uint32,
                           line_id:uint8, x:uint16, y:uint16, dir:uint8}"""
    bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 1
    sp = h.cfg.get('spawn', {})
    out = (w_u8(0) + w_str('') + w_u32(bid) +
           w_u8(sp.get('line_id', 1)) +
           w_u16(sp.get('x', 100)) + w_u16(sp.get('y', 100)) +
           w_u8(sp.get('dir', 0)))
    pkt = pack_frame(10200, out)
    h.request.sendall(pkt)
    log('tcp.log', '  << 10200 SCRoleEnter bid=%d line=%d (%d,%d) (%d bytes)'
        % (bid, sp.get('line_id', 1), sp.get('x', 100), sp.get('y', 100),
           len(pkt)))
    return True
