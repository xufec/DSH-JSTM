# -*- coding: utf-8 -*-
"""role.handler —— 角色四件套命令（Phase 2 step 2）。

注册命令：10301、10302、10303。
迁移来源（mock_server.py _reply if 块）：
  10301  L16267–16272   10303  L15364–15373   10302  L15374–15385
"""

from core import runtime
from core.dispatch import register
from protocol.frame import pack_frame
from role.storage import role_state, build_10301, build_10302, build_10303
from attribute.service import db_get_attr

log = runtime.log


@register(10301)
def handle_10301(h, cmd, body):
    """CS_10301（空）→ SC_10301 角色基础信息。"""
    pkt = pack_frame(10301, build_10301(role_state(h.cfg), h.cfg.get('skills', [])))
    h.request.sendall(pkt)
    log('tcp.log', '  << 10301 SC_10301 role info (%d bytes)' % len(pkt))


@register(10303)
def handle_10303(h, cmd, body):
    """CS_10303（空）→ SC_10303 角色属性（含 attr 大表）。"""
    pkt = pack_frame(10303, build_10303(role_state(h.cfg),
                                        h.cfg.get('skills', []),
                                        h.cfg.get('attr')))
    h.request.sendall(pkt)
    aa = db_get_attr(role_state(h.cfg).get('rid', 1001)) or {}
    log('tcp.log', '  << 10303 SC_10303 attr (hp_max=%s atk_s=%s) (%d bytes)'
        % (aa.get('hp_max'), aa.get('atk_s'), len(pkt)))


@register(10302)
def handle_10302(h, cmd, body):
    """CS_10302（空）→ SC_10302 资产/经验刷新。"""
    r = role_state(h.cfg)
    # 2026-10-17：原来这里先拼了一个 out（lev/exp/gold），但真正下发的是 build_10302(r)，
    #   out 从未使用 —— 删掉死代码（协议形状不变）。
    pkt = pack_frame(10302, build_10302(r))
    h.request.sendall(pkt)
    log('tcp.log', '  << 10302 SC_10302 lev=%d exp=%d gold=%d gold_acc=%d (%d bytes)'
        % (r.get('lev', 1), r.get('exp', 0), r.get('gold', 0),
           r.get('gold_acc', 0), len(pkt)))
