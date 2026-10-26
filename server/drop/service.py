# -*- coding: utf-8 -*-
"""drop.service —— 怪物掉落表接线（Phase 16，1.4.11 config_drop.json 29 组 CONFIRMED）。

结构：Drop[mon_bid] = {coin:"{min,max}", normal:{item_bid:{level:{num,min,max,pp}}},
                      core, core_p, first, holiday}。
按 mon_bid 解析：金币(coin 池) + 普通物品(normal 池，按 pp 概率)。
无配置怪 ⇒ 空（真话，不编造）；物品发放由调用方经 reward.grant（幂等）。
"""

import json
import os
import random

from core import runtime

log = runtime.log
_PATH = os.path.join(runtime.HERE, 'cfg', 'config_drop.json')
_cfg = None


def _load():
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(_PATH, encoding='utf-8') as f:
            _cfg = json.load(f).get('Drop') or {}
    except Exception as e:
        log('server.log', '!! drop cfg load failed: %r' % (e,))
        _cfg = {}
    return _cfg


def groups():
    return sorted(_load().keys())


def _coin_val(s):
    try:
        return int(str(s).strip('{}'))
    except Exception:
        return 0


def resolve(mon_bid):
    """按 mon_bid 解析一次掉落。返回 {'coin':n, 'items':[(bid,num)]}。

    normal：每个 item_bid 的 level=1 项按 pp 概率命中 ⇒ 数量 num/min~max。
    # INFERENCE：概率 = pp/1000（normal_sum 基准），待实机标定。
    无配置怪 ⇒ {'coin':0,'items':[]}。
    """
    e = _load().get(str(int(mon_bid)))
    if not e:
        return {'coin': 0, 'items': []}
    e = e.get('hash') if isinstance(e, dict) and 'hash' in e else e
    coin = _coin_val(e.get('coin') or 0)
    items = []
    for bid, levels in (e.get('normal') or {}).items():
        lv = (levels or {}).get('1') or {}
        lv = lv.get('hash') if isinstance(lv, dict) and 'hash' in lv else lv
        pp = int(lv.get('pp') or 0)
        if pp <= 0:
            continue
        if random.randint(1, 1000) <= pp:
            num = int(lv.get('num') or 1)
            items.append((int(bid), num))
    first = int(e.get('first') or 0)  # CONFIRMED: 20012=1001,20024=1002 首杀
    return {'coin': coin, 'items': items, 'first': first}
