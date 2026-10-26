# -*- coding: utf-8 -*-
"""dungeon.service —— 副本列表 + 通关奖励闭环（Phase 10）。"""

import json
import os

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log

_CFG_PATH = os.path.join(runtime.HERE, 'cfg', 'config_dungeon_new.json')
_cfg = None

# # INFERENCE：首通奖励在配置 coin/exp 为 0 时的兜底金币（替换点，按各副本 drop_show 标定）。
FIRST_CLEAR_GOLD = 5000


def _load():
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(_CFG_PATH, encoding='utf-8') as f:
            _cfg = json.load(f)
    except Exception as e:
        log('server.log', '!! dungeon cfg load failed: %r' % (e,))
        _cfg = {}
    return _cfg


def _kv_get(rid, ptype, pkey, default=0):
    con = db_conn()
    r = con.execute('SELECT value FROM dungeon_progress WHERE rid=? AND ptype=? AND pkey=?',
                    (int(rid), ptype, str(pkey))).fetchone()
    db_release(con)
    return int(r[0]) if r is not None else int(default)


def _kv_set(rid, ptype, pkey, value):
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO dungeon_progress (rid,ptype,pkey,value) VALUES (?,?,?,?)',
                (int(rid), ptype, str(pkey), int(value)))
    con.commit()
    db_release(con)


def catalog():
    """34 条副本配置 [{bid,name,type,count,level_low,coin,role_exp,hero_exp}]。"""
    d = _load().get('Dungeon') or {}
    out = []
    for k, v in d.items():
        h = (v or {}).get('hash') or {}
        try:
            bid = int(h.get('dung_id') or k)
        except Exception:
            bid = 0
        if bid:
            out.append({'bid': bid, 'name': h.get('name') or '', 'type': int(h.get('type') or 0),
                        'count': int(h.get('count') or 0), 'level_low': int(h.get('level_low') or 0),
                        'coin': int(h.get('coin') or 0),
                        'role_exp': int(h.get('role_exp') or 0),
                        'hero_exp': int(h.get('hero_exp') or 0)})
    return sorted(out, key=lambda x: x['bid'])


def list_panel(rid):
    """副本列表：配置 34 条 + 每副本剩余次数(dung_left) + 是否已首通(dung_got)。"""
    rows = []
    for c in catalog():
        left = _kv_get(rid, 'dung_left', c['bid'], c['count'])
        got = _kv_get(rid, 'dung_got', c['bid'], 0)
        rows.append({'bid': c['bid'], 'name': c['name'], 'level_low': c['level_low'],
                     'left': left, 'first_clear': bool(got)})
    return rows


def clear(rid, bid):
    """通关一个副本（首通奖励幂等）。返回结果 dict。"""
    from reward.service import grant
    from role.storage import db_get_role

    bid = int(bid)
    cfg = next((c for c in catalog() if c['bid'] == bid), None)
    if not cfg:
        return {'ok': False, 'err': 'unknown_dungeon', 'bid': bid}

    role = db_get_role(rid) or {}
    lv = int(role.get('level') or 1)
    if lv < cfg['level_low']:
        return {'ok': False, 'err': 'level_too_low', 'need': cfg['level_low'], 'have': lv}

    left = _kv_get(rid, 'dung_left', bid, cfg['count'])
    if left <= 0:
        return {'ok': False, 'err': 'no_count_left', 'left': left}

    # 奖励：配置 coin/exp + INFERENCE 首通兜底 gold
    awards = []
    if cfg['coin']:
        awards.append({'kind': 'asset', 'code': 'coin', 'amount': cfg['coin']})
    if cfg['role_exp']:
        awards.append({'kind': 'asset', 'code': 'exp', 'amount': cfg['role_exp']})
    # 首通兜底金币（幂等）
    awards.append({'kind': 'asset', 'code': 'gold', 'amount': FIRST_CLEAR_GOLD})

    ref = 'dungeon:%d:%d:first' % (bid, int(rid))
    res = grant(int(rid), awards, ref, source='dungeon_clear')

    # 扣次数 + 标记首通（无论是否已发奖，次数-1 模拟一次挑战）
    _kv_set(rid, 'dung_left', bid, left - 1)
    _kv_set(rid, 'dung_got', bid, 1)
    log('tcp.log', '  ** dungeon.clear rid=%d bid=%d left %d->%d grant_already=%s ref=%s'
        % (rid, bid, left, left - 1, res.get('already'), ref))
    return {'ok': True, 'bid': bid, 'left_after': left - 1,
            'already': res.get('already'), 'applied': res.get('applied')}
