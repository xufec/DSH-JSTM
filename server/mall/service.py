# -*- coding: utf-8 -*-
"""mall.service —— 商城配置只读列表（Phase 11）。"""

import json
import os

from core import runtime

log = runtime.log

_CFG_PATH = os.path.join(runtime.HERE, 'cfg', 'config_mall.json')
_cfg = None


def _load():
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(_CFG_PATH, encoding='utf-8') as f:
            _cfg = json.load(f)
    except Exception as e:
        log('server.log', '!! mall cfg load failed: %r' % (e,))
        _cfg = {}
    return _cfg


def _rows(section):
    d = _load().get(section) or {}
    out = []
    for k, v in d.items():
        h = (v or {}).get('hash') or {}
        try:
            gid = int(h.get('id') or k)
        except Exception:
            gid = 0
        if gid:
            out.append({'gid': gid, 'item_bid': int(h.get('item_bid') or 0),
                        'price': int(h.get('price') or 0),
                        'pay_type': int(h.get('pay_type') or 0),
                        'cli_tag': h.get('cli_tag') or '',
                        'limit_week': int(h.get('limit_week') or 0),
                        'limit_day_cli': int(h.get('limit_day_cli') or 0),
                        'type': int(h.get('type') or 0)})
    return sorted(out, key=lambda x: x['gid'])


def list_panel():
    """商城三档只读列表：普通(MallGoods)/周限购(MallWeek)/限时(MallXian)。"""
    return {'normal': _rows('MallGoods'),
            'week': _rows('MallWeek'),
            'xian': _rows('MallXian')}


def counts():
    p = list_panel()
    return {'normal': len(p['normal']), 'week': len(p['week']), 'xian': len(p['xian'])}
