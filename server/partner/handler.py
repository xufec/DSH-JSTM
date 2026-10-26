# -*- coding: utf-8 -*-
"""partner.handler —— 伙伴面板命令（Phase 8）。

注册命令：11215（伙伴列表/图鉴面板 partner_list）。
迁移来源：mock_server.py _reply if 块 L17417–17479（旧块将标注 # [P8-migrated]）。

闭环：CS_11215(空/rid) → SC_11215{partner_list: 53 行}。
  数据源 = partner.service.build_panel_11215（配置 53 + role_heros 已拥有 lev）。
"""

from core import runtime
from core.dispatch import register
from protocol.frame import pack_frame
from role.storage import role_state
from partner import service as svc

log = runtime.log


@register(11215)
def handle_11215(h, cmd, body):
    """CS_11215 → SC_11215 partner_list（53 配置伙伴 × DB 已拥有 lev/exp）。"""
    rid = role_state(h.cfg).get('rid', 1001)
    out = svc.build_panel_11215(rid)
    pkt = pack_frame(11215, out)
    h.request.sendall(pkt)
    log('tcp.log', '  << 11215 SC_11215 partner_list=%d（partner.service 配置驱动）(%d bytes)'
        % (len(svc._live_list or []), len(pkt)))
