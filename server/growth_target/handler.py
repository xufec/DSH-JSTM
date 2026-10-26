# -*- coding: utf-8 -*-
"""growth_target.handler —— 开服成长计划（30500 / 30501 / 30502）。

30501 领取登陆奖励 / 30502 领取充值奖励：`SC{result:u8, msg:s, items:table{item_bid:u32,num:u32}}`
30500 请求成长目标信息：面板整包（本批先给"已领状态 + 累计充值"的真值骨架）。
"""


from core import runtime
from core.dispatch import register
from protocol.frame import pack_frame, w_u8, w_u16, w_u32, w_str
from role.storage import role_state
from growth_target import service as svc

log = runtime.log


def _items_table(items):
    out = w_u16(len(items or []))
    for bid, num in (items or []):
        out += w_u32(int(bid)) + w_u32(int(num))
    return out


def _claim(h, cmd, day, kind):
    rid = role_state(h.cfg).get('rid', 1001)
    ok, msg, items = svc.claim(rid, day, kind)
    out = w_u8(1 if ok else 0) + w_str(msg) + _items_table(items)
    h.request.sendall(pack_frame(cmd, out))
    log('tcp.log', '  << %d SC_%d day=%d kind=%s ok=%s items=%s'
        % (cmd, cmd, day, kind, ok, items))


@register(30501)
def handle_30501(h, cmd, body):
    """领取登陆奖励 `CS{day:u8}`。"""
    day = body[0] if body else 0
    _claim(h, 30501, day, 'login')


@register(30502)
def handle_30502(h, cmd, body):
    """领取充值奖励 `CS{day:u8}`（需累计充值 >= charge_gold）。"""
    day = body[0] if body else 0
    _claim(h, 30502, day, 'charge')


@register(30500)
def handle_30500(h, cmd, body):
    """请求成长目标信息 → 各天的 (登录/充值) 领取状态 + 累计充值（真值）。"""
    rid = role_state(h.cfg).get('rid', 1001)
    st = svc.state(rid)
    days = sorted(svc.gt_cfg()['targets'].keys())
    out = (w_u8(1) + w_str('') +
           w_u32(int(st['login_day']) or 0) +   # current_day（按已领天数近似）
           w_u32(0))                            # remain_time（无配置来源 ⇒ 0，不编造）
    out += w_u16(len(days))
    for d in days:
        out += (w_u8(d & 0xff) +
                w_u8(1 if int(st['login_day']) >= d else 0) +
                w_u8(1 if int(st['charge_day']) >= d else 0) +
                w_u32(int(st['total_charge'])) +
                w_u16(0) +                      # targets 空表
                w_u8(0) + w_u8(0))
    h.request.sendall(pack_frame(30500, out))
    log('tcp.log', '  << 30500 SC_30500 days=%d login_day=%d charge_day=%d'
        % (len(days), st['login_day'], st['charge_day']))
