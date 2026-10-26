# -*- coding: utf-8 -*-
"""task.handler —— 任务命令（Phase 2d）。

注册命令：12408（删除列表，回空表）。
迁移来源（mock_server.py _reply if 块 L15361–15368）。
注：12400/12401/12402/12407/12409/12403 的 DB 读簇闭包太深，本批留旧链。
"""

from core import runtime
from core.dispatch import register
from protocol.frame import w_u16, pack_frame

log = runtime.log


@register(12408)
def handle_12408(h, cmd, body):
    """CS_12408（空）→ SC_12408{ delete_list: table(mission_bid:u32) }
    暂无需要从"可接取"删除的项 ⇒ 回空表（不编造）。"""
    body = w_u16(0)
    pkt = pack_frame(12408, body)
    h.request.sendall(pkt)
    log('tcp.log', '  << 12408 SC_12408 delete_list=0 (%d bytes)' % len(pkt))
    return True


from role.storage import role_state
from task.service import mission_rows, build_12400


@register(12400)
def handle_12400(h, cmd, body):
    """CS_12400（空）→ SC_12400{mission_list}  [P3deep-migrated]"""
    ms = mission_rows(h.cfg, role_state(h.cfg).get('rid', 1001))
    pkt = pack_frame(12400, build_12400(ms))
    h.request.sendall(pkt)
    log('tcp.log', '  << 12400 SC_12400 mission_list=%d (%d bytes)'
        % (len(ms), len(pkt)))
    return True


@register(12401)
def handle_12401(h, cmd, body):
    """CS_12401（空）→ SC_12401{missions}  [P3deep-migrated]"""
    ms = mission_rows(h.cfg, role_state(h.cfg).get('rid', 1001))
    pkt = pack_frame(12401, build_12400(ms))
    h.request.sendall(pkt)
    log('tcp.log', '  << 12401 SC_12401 missions=%d (%d bytes)'
        % (len(ms), len(pkt)))
    return True
