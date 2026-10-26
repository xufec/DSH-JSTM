# -*- coding: utf-8 -*-
"""scratch.handler —— 刮刮乐（16651 获取活动数据 / 16652 刮卡）。

迁移来源：`mock_server.py` 旧 `16652` 桩（仅回显 index + status=0）。
替换为：真消耗道具（28031）、真盘面（3 张同卡）、真开奖（钻石入账，幂等）。
"""

import struct

from core import runtime
from core.dispatch import register
from protocol.frame import pack_frame, w_u8, w_u16, w_u32, w_str
from role.storage import role_state
from scratch import service as svc

log = runtime.log


def _card_list(cards):
    out = w_u16(len(cards or []))
    for c in (cards or []):
        out += (w_u32(int(c.get('index') or 0)) + w_u32(int(c.get('card_id') or 0)) +
                w_u32(int(c.get('gold') or 0)) + w_u8(int(c.get('status') or 0) & 0xff))
    return out


@register(16651)
def handle_16651(h, cmd, body):
    """获取刮刮乐活动数据 → `SC_16651{code,msg,remain_sec,cash_reward,card_list,
    item_list,item_effect_list,client_reward}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    cash, cards = svc.take_reward(rid)          # 已全刮开 ⇒ 开奖并清盘
    cfg = svc.scratch_cfg()
    out = (w_u8(1) + w_str('') + w_u32(0) + w_u32(cash) +
           _card_list(cards) +
           w_u16(0) +                           # item_list 空（无额外产出）
           w_u16(0) +                           # item_effect_list 空
           w_str(''))                           # client_reward 空
    h.request.sendall(pack_frame(16651, out))
    log('tcp.log', '  << 16651 SC_16651 cash_reward=%d cards=%d（道具 %d）'
        % (cash, len(cards), cfg['item_bid']))


@register(16652)
def handle_16652(h, cmd, body):
    """刮卡 `CS{index:u32}` → `SC_16652{code,msg,index,status}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    ix = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
    ok, msg, cards, done, cash = svc.scratch(rid, ix)
    st = 0
    for c in (cards or []):
        if int(c.get('index') or 0) == ix:
            st = int(c.get('status') or 0)
            break
    out = w_u8(1 if ok else 0) + w_str(msg) + w_u32(ix) + w_u8(st & 0xff)
    h.request.sendall(pack_frame(16652, out))
    log('tcp.log', '  << 16652 SC_16652 index=%d ok=%s status=%d done=%s cash=%d'
        % (ix, ok, st, done, cash))
