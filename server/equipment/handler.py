# -*- coding: utf-8 -*-
"""equipment.handler —— 装备命令族（P3deep 重排）。

注册命令：10601（hero_list 属性表）、10610（战斗上报回执）、10651（回执）。
迁移来源（mock_server.py _reply if 块 L12506–12527 的 106xx 共享块）。
10622 已在 skill/handler.py 注册。
"""

from core import runtime
from core.dispatch import register
from protocol.frame import w_u8, w_u32, w_str, pack_frame
from role.storage import role_state
from attribute.service import attr_row_bytes, db_role_attr

log = runtime.log


@register(10601)
def handle_10601(h, cmd, body):
    """{flag:u32} → {p:u32, skill_bid:u32, lev:u32, hero_list:table(22 战斗属性)}"""
    _rid = role_state(h.cfg).get('rid', 1001)
    _out = (w_u32(0) + w_u32(0) + w_u32(0) +
            attr_row_bytes(10601, 'hero_list', db_role_attr(_rid), _rid))
    h.request.sendall(pack_frame(10601, _out))
    log('tcp.log', '  << 10601 SC_10601 hero_list 收尾（%d bytes）' % len(_out))
    return True


@register(10610)
def handle_10610(h, cmd, body):
    """战斗上报 ⇒ 回执型"""
    _out = w_u8(1) + w_str('')
    h.request.sendall(pack_frame(10610, _out))
    log('tcp.log', '  << 10610 SC_10610 收尾（%d bytes）' % len(_out))
    return True


@register(10651)
def handle_10651(h, cmd, body):
    """无参 ⇒ 回执型"""
    _out = w_u8(1) + w_str('')
    h.request.sendall(pack_frame(10651, _out))
    log('tcp.log', '  << 10651 SC_10651 收尾（%d bytes）' % len(_out))
    return True
