# -*- coding: utf-8 -*-
"""growth.handler —— 成长族面板命令（Phase 9）。

[P9 裁剪说明] 翅膀(11600)/神器/命格(19400)/阵法/时装的面板编码器深耦合在
mock_server.py 旧链（依赖 role_state / encode_mingge_list / w_u8 / pack_frame 等
模块级助手），且已读同一批 role_wing/role_shenqi/role_mingge 表。按 Phase 2/9
裁剪约定：**面板留旧链**，本包不重复注册（避免帧字节漂移）。
本包的价值在**写闭环**（service.wing_up/shenqi_up/mingge_activate）：
配置驱动消耗 → CurrencyService → 族表 → apply_delta → power 重算。
成长后旧链面板重连即见新阶/新星，10304/10502 由 live_push 推送。
"""

from core import runtime
from core.dispatch import register
from protocol.frame import pack_frame
from role.storage import role_state
from growth import service as svc

log = runtime.log


@register(11600)
def handle_11600(h, cmd, body):
    """CS_11600 翅膀面板 → SC_11600（② 解耦：读 role_wing 真表替换 EMPTY_REPLIES 全 0）。

    旧链 11600 在 EMPTY_REPLIES 返全 0 ⇒ 面板从不显示 P9 wing_up 后的 color/star。
    本编码器字段顺序逐字对齐 proto_defs SC_11600，未成长字段与旧链零字节一致，
    仅 color/wing_id/power/star 为 role_wing 真值（P9 wing_up 后 color=3）。
    旧 EMPTY_REPLIES[11600] 保留为兜底（# [②GROWTH-migrated]）。
    """
    rid = role_state(h.cfg).get('rid', 1001)
    out = svc.build_panel_11600(rid)
    pkt = pack_frame(11600, out)
    h.request.sendall(pkt)
    st = svc._wing_row(rid)
    log('tcp.log', '  << 11600 SC_11600 wing color=%d wing_id=%d power=%d star=%d（growth.service 真表）(%d bytes)'
        % (st['color'], st['wing_id'], st['power'], st['star'], len(pkt)))


def on_load():
    log('server.log', 'growth.handler loaded (11600 decoupled to real role_wing; panels 19400/10952 retained on old chain)')
