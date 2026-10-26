# -*- coding: utf-8 -*-
"""friend.handler —— 好友系统（13300 / 13321 / 13303 / 13305）。

替换原"通用编码器"恒空表实现。好友元素统一 15 字段（见 service.profile）。
"""

import struct

from core import runtime
from core.dispatch import register
from protocol.frame import pack_frame, w_u8, w_u16, w_u32, w_str
from role.storage import role_state
from friend import service as svc

log = runtime.log


def _elem(p):
    """好友元素：15 字段（顺序与 fields.json 的 friend_list.items 一致）。"""
    return (w_u32(int(p.get('rid') or 0)) + w_str(str(p.get('srv_id') or '1')) +
            w_str(str(p.get('name') or '')) + w_u8(int(p.get('sex') or 0) & 0xff) +
            w_u16(int(p.get('lev') or 1) & 0xffff) +
            w_u16(int(p.get('career') or 1) & 0xffff) +
            w_u32(int(p.get('power') or 0) & 0xffffffff) +
            w_u32(int(p.get('login_time') or 0) & 0xffffffff) +
            w_u8(int(p.get('face_id') or 0) & 0xff) +
            w_u8(int(p.get('is_online') or 0) & 0xff) +
            w_u32(int(p.get('group_id') or 0) & 0xffffffff) +
            w_u32(int(p.get('intimacy') or 0) & 0xffffffff) +
            w_u32(int(p.get('grid') or 0) & 0xffffffff) +
            w_str(str(p.get('gsrv_id') or '1')) +
            w_str(str(p.get('guild_name') or '')))


def _table(rows):
    out = w_u16(len(rows or []))
    for r in (rows or []):
        out += _elem(r)
    return out


def _push(rid, pkt):
    """向指定 rid 投递（惰性导入 mock_server 的 push_to_rid，避免模块循环导入）。"""
    try:
        from mock_server import push_to_rid
        return push_to_rid(int(rid), pkt)
    except Exception as e:
        log('tcp.log', '  !! friend push 失败 rid=%s: %r' % (rid, e))
        return 0


def _push_13304(to_rid, from_rid):
    """告诉 B：A 想加你好友 → `SC_13304{rid,srv_id,name,sex,lev}`。"""
    p = svc.profile(from_rid)
    pkt = pack_frame(13304, w_u32(from_rid) + w_str(str(p.get('srv_id') or '1')) +
                     w_str(str(p.get('name') or '')) +
                     w_u8(int(p.get('sex') or 0) & 0xff) +
                     w_u8(int(p.get('lev') or 1) & 0xff))
    return _push(to_rid, pkt)


def _push_13322(to_rid, other_rid):
    """告诉 X：新增好友 → `SC_13322{add_list:table}`。"""
    return _push(to_rid, pack_frame(13322, _table([svc.profile(other_rid)])))


def _push_13308(to_rid, other_rid, srv='1'):
    """被动删友通知 → `SC_13308{rid,srv_id}`。"""
    return _push(to_rid, pack_frame(13308, w_u32(other_rid) + w_str(str(srv or '1'))))


@register(13300)
def handle_13300(h, cmd, body):
    """获取好友列表 → `SC_13300{friend_list:table}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    rows = svc.friends(rid)
    h.request.sendall(pack_frame(13300, _table(rows)))
    log('tcp.log', '  << 13300 SC_13300 friend_list=%d（role_friend 真值）' % len(rows))


@register(13321)
def handle_13321(h, cmd, body):
    """获取好友申请列表 → `SC_13321{request_list:table}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    rows = svc.requests(rid)
    h.request.sendall(pack_frame(13321, _table(rows)))
    log('tcp.log', '  << 13321 SC_13321 request_list=%d' % len(rows))


@register(13303)
def handle_13303(h, cmd, body):
    """请求加好友 `CS{rid:u32, srv_id:s}` → `SC{code:u8, msg:s}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    trid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
    sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
    srv = body[6:6 + sl].decode('utf-8', 'replace') if len(body) >= 6 + sl else '1'
    ok, msg = svc.add_request(rid, trid, srv or '1')
    if ok and trid:
        _push_13304(trid, rid)          # ★ 告诉 B：A 想加你好友
    h.request.sendall(pack_frame(13303, w_u8(1 if ok else 0) + w_str(msg)))
    log('tcp.log', '  << 13303 SC_13303 ok=%s msg=%r（target=%d）' % (ok, msg, trid))


@register(13305)
def handle_13305(h, cmd, body):
    """应答加好友 `CS{rid:u32, srv_id:s, agreed:u8}` → `SC{rid,srv_id,code,msg}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    fr = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
    sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
    srv = body[6:6 + sl].decode('utf-8', 'replace') if len(body) >= 6 + sl else '1'
    agreed = body[6 + sl] if len(body) >= 7 + sl else 0
    ok, msg = svc.answer(rid, fr, agreed, srv or '1')
    if ok and agreed and fr:
        _push_13322(rid, fr)            # ★ 告诉 B：A 成为你好友
        _push_13322(fr, rid)            # ★ 告诉 A：B 成为你好友
    out = (w_u32(fr) + w_str(srv or '1') + w_u8(1 if ok else 0) + w_str(msg))
    h.request.sendall(pack_frame(13305, out))
    log('tcp.log', '  << 13305 SC_13305 from=%d agreed=%s ok=%s' % (fr, agreed, ok))


@register(13307)
def handle_13307(h, cmd, body):
    """主动删除好友 `CS{rid:u32, srv_id:s}` → `SC{rid,srv_id,code,msg}`（并通知对方 13308）。"""
    rid = role_state(h.cfg).get('rid', 1001)
    fr = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
    sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
    srv = body[6:6 + sl].decode('utf-8', 'replace') if len(body) >= 6 + sl else '1'
    ok, msg = svc.del_friend(rid, fr)
    if ok and fr:
        _push_13308(fr, rid, srv)       # ★ 被动删友通知
    out = w_u32(fr) + w_str(srv or '1') + w_u8(1 if ok else 0) + w_str(msg)
    h.request.sendall(pack_frame(13307, out))
    log('tcp.log', '  << 13307 SC_13307 rid=%d ok=%s' % (fr, ok))


@register(13323)
def handle_13323(h, cmd, body):
    """一键清空好友申请 → `SC{code:u8, string:s}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    ok, msg = svc.clear_requests(rid)
    h.request.sendall(pack_frame(13323, w_u8(1 if ok else 0) + w_str(msg)))
    log('tcp.log', '  << 13323 SC_13323 code=%d（清空申请）' % (1 if ok else 0))
