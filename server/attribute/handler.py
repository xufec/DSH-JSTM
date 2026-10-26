# -*- coding: utf-8 -*-
"""attribute.handler —— 角色属性+战力命令（Phase 2 step 3）。

注册命令：10304、10306。
迁移来源（mock_server.py _reply if 块）：
  10306  L16409–16426   10304  L16427–16478

★ 10304 是 DSH 实机验收的关键帧（hp_max=4381 / atk_s=789 / power），逐字节复制。
"""

from core import runtime
from core.dispatch import register
from protocol.frame import w_u8, w_u16, w_u32, w_str, pack_frame
from role.storage import role_state
from attribute.service import role_attr_dict, role_power, attr_table_10304, attr_table_10306

log = runtime.log


@register(10306)
def handle_10306(h, cmd, body):
    """SC_10306 属性同步小包（attr 表 + mspd + power）。"""
    st = role_state(h.cfg)
    ad = role_attr_dict(h.cfg)
    pw = role_power(h.cfg)
    out = attr_table_10306(ad)                        # 专用编码器（尾段 u16）
    out += w_u16(int(st.get('mspd', 0)) & 0xffff)    # mspd:uint16
    out += w_u32(pw & 0xffffffff)                    # power:uint32
    h.request.sendall(pack_frame(10306, out))
    log('tcp.log', '  << 10306 attr=24 mspd=%d power=%d (%d bytes)'
        % (int(st.get('mspd', 0)), pw, len(out)))


@register(10304)
def handle_10304(h, cmd, body):
    """SC_10304 角色属性+战力大包（逐字复制自原 if 块）。"""
    rid = role_state(h.cfg).get('rid', 1001)
    default_attr = role_attr_dict(h.cfg)
    power = role_power(h.cfg)
    st = role_state(h.cfg)
    out = (w_u32(st.get('rid', rid)) + w_str(st.get('srv_id', '1')) +
           w_str(st.get('name', 'DSH')) + w_u16(st.get('lev', 160)) +
           w_u8(st.get('is_vip', 0)) + w_u8(st.get('vip_lev', 0)) +
           w_u8(st.get('sex', 0)) + w_u16(st.get('career', 1)) +
           w_u8(st.get('volume', 200)) + w_u8(st.get('store_volume', 0)) +
           w_u8(st.get('store_partner_volume', 0)) +
           w_u8(st.get('volume_open', 200)) +
           w_u8(st.get('store_volume_open', 0)) +
           w_u8(st.get('store_partner_volume_open', 0)) +
           w_u16(st.get('attr_point', 0)) +
           w_u16(0))  # skill_list 空
    out += w_u32(power)  # ★ 战力
    out += (w_u32(st.get('exp', 0)) + w_u32(st.get('gold', 0)) +
            w_u32(st.get('coin', 0)) + w_u32(st.get('gold_acc', 0)) +
            w_u32(st.get('sinew', 0)) + w_u32(st.get('experience', 0)) +
            w_u32(st.get('coupon', 0)) + w_u32(st.get('vitality', 0)) +
            w_u32(st.get('guild_contrib', 0)) + w_u32(st.get('practice_exp', 0)) +
            w_u32(st.get('tower_cent', 0)) + w_u32(st.get('arena_cent', 0)))
    out += attr_table_10304(default_attr)             # attr 表：1 条
    out += w_u16(int(st.get('mspd', 0)) & 0xffff)     # mspd:uint16
    out += w_u16(0)                                   # animate_res 空表
    out += w_u32(int(st.get('vip_exp', 0)) & 0xffffffff)
    out += w_str(str(st.get('jiebai_title', '')))     # jiebai_title:string
    out += w_u8(int(st.get('jiebai_lev', 0)) & 0xff)  # jiebai_lev:uint8
    pkt = pack_frame(10304, out)
    h.request.sendall(pkt)
    log('tcp.log', '  << 10304 SC_10304 power=%d attr=24+1 (%d bytes)' % (power, len(pkt)))
