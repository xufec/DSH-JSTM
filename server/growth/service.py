# -*- coding: utf-8 -*-
"""growth.service —— 翅膀/神器/命格 成长闭环（Phase 9）。

复用 mock_server 已建的 role_wing/role_shenqi/role_mingge 表（独立 SQL，不 import mock_server）。
配置 CONFIRMED 读取；消耗/属性无完整真值处标 # INFERENCE 替换点。
"""

import json
import os
import time

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log

_CFG = {
    'wing': os.path.join(runtime.HERE, 'cfg', 'config_wing_data.json'),
    'shenqi': os.path.join(runtime.HERE, 'cfg', 'config_shenqi.json'),
    'mingge': os.path.join(runtime.HERE, 'cfg', 'config_mingge.json'),
}
_cache = {}


def _load(name):
    if name in _cache:
        return _cache[name]
    try:
        with open(_CFG[name], encoding='utf-8') as f:
            _cache[name] = json.load(f)
    except Exception as e:
        log('server.log', '!! growth %s cfg load failed: %r' % (name, e))
        _cache[name] = {}
    return _cache[name]


# ── 族表独立读写 ──────────────────────────────────────────────────────────
def _wing_row(rid):
    con = db_conn()
    con.row_factory = None
    r = con.execute('SELECT color,wing_id,power,star FROM role_wing WHERE rid=?',
                    (int(rid),)).fetchone()
    db_release(con)
    if r:
        return {'color': int(r[0] or 0), 'wing_id': int(r[1] or 0),
                'power': int(r[2] or 0), 'star': int(r[3] or 0)}
    return {'color': 0, 'wing_id': 0, 'power': 0, 'star': 0}


def _wing_set(rid, color, wing_id, power):
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_wing VALUES (?,?,?,?,?,?)',
                (int(rid), int(color), int(wing_id), int(power), 0, int(time.time())))
    con.commit(); db_release(con)


def _shenqi_row(rid, sid):
    con = db_conn()
    r = con.execute('SELECT sid,lev,star,status,mark FROM role_shenqi WHERE rid=? AND sid=?',
                    (int(rid), int(sid))).fetchone()
    db_release(con)
    if r:
        return {'sid': int(r[0]), 'lev': int(r[1] or 1), 'star': int(r[2] or 0),
                'status': int(r[3] or 0), 'mark': int(r[4] or 0)}
    return None


def _shenqi_set(rid, sid, lev, star):
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_shenqi VALUES (?,?,?,?,?,?,?)',
                (int(rid), int(sid), int(lev), int(star), 1, 0, int(time.time())))
    con.commit(); db_release(con)


def _mingge_row(rid, bid):
    con = db_conn()
    r = con.execute('SELECT bid,lev FROM role_mingge WHERE rid=? AND bid=?',
                    (int(rid), int(bid))).fetchone()
    db_release(con)
    return {'bid': int(r[0]), 'lev': int(r[1] or 1)} if r else None


def _mingge_add(rid, bid, lev):
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_mingge VALUES (?,?,?,?,?,?)',
                (int(rid), int(bid), int(lev), 1, 0, int(time.time())))
    con.commit(); db_release(con)


# ── 闭环 1：翅膀升阶 ─────────────────────────────────────────────────────
# WingColor[color] = {next, assets:{coin}, condition:{lev}, atk_s:[null,v0,v1],...}
_WING_ATTR_KEYS = ('atk_s', 'atk_p', 'def_s', 'def_p', 'atk_speed', 'hp_max')


def wing_next_cost(rid):
    """下一阶翅膀的 {coin, req_lev, attrs}；已满阶返回 None。"""
    d = _load('wing')
    wc = d.get('WingColor') or {}
    cur = _wing_row(rid)
    nxt = cur['color'] + 1
    row = wc.get(str(nxt)) or {}
    h = row.get('hash') or {}
    if not h:
        return None
    assets = (h.get('assets') or {}).get('hash') or {}
    cond = (h.get('condition') or {}).get('hash') or {}
    attrs = {}
    for k in _WING_ATTR_KEYS:
        arr = h.get(k)
        if isinstance(arr, list) and len(arr) >= 2 and arr[1]:
            attrs[k] = int(arr[1])
    return {'next_color': nxt, 'coin': int(assets.get('coin') or 0),
            'req_lev': int(cond.get('lev') or 0), 'attrs': attrs}


def wing_up(rid):
    from currency.service import db_get_assets, db_add_assets
    from attribute.service import apply_delta
    from power.service import power_of
    from role.storage import db_get_role

    nxt = wing_next_cost(rid)
    if not nxt:
        return {'ok': False, 'err': 'wing_maxed'}
    role = db_get_role(rid) or {}
    lv = int(role.get('level') or 1)
    if lv < nxt['req_lev']:
        return {'ok': False, 'err': 'level_too_low', 'need': nxt['req_lev'], 'have': lv}

    before = db_get_assets(rid)
    coin_now = int(before.get('coin') or 0)
    if coin_now < nxt['coin']:
        return {'ok': False, 'err': 'not_enough_coin', 'need': nxt['coin'], 'have': coin_now}

    db_add_assets(rid, {'coin': -nxt['coin']})
    cur = _wing_row(rid)
    _wing_set(rid, nxt['next_color'], cur['wing_id'] or 1, cur['power'])
    if nxt['attrs']:
        apply_delta(rid, nxt['attrs'])
    log('tcp.log', '  ** growth.wing_up rid=%d color %d->%d coin -%d attrs=%s ref=growth:wing:%d:%d'
        % (rid, cur['color'], nxt['next_color'], nxt['coin'], nxt['attrs'], nxt['next_color'], rid))
    return {'ok': True, 'color_before': cur['color'], 'color_after': nxt['next_color'],
            'coin_spent': nxt['coin'], 'attr_delta': nxt['attrs'], 'power_after': power_of(rid)}


# ── 闭环 2：神器升星 ─────────────────────────────────────────────────────
def shenqi_next(rid, sid):
    """下一阶节点 {coin_cost, attrs}；已满返回 None。

    ShenqiUpgrade[sid] = {"1":{"1":node_hash,"2":node_hash},"2":{...}}（星×节点），
    这里扁平化为节点序列，按已完成节点数(star)取下一节点。
    """
    d = _load('shenqi')
    up = d.get('ShenqiUpgrade') or {}
    sid_up = up.get(str(sid)) or {}
    nodes = []
    for sk in sorted(sid_up.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
        stage = sid_up[sk] or {}
        for nk in sorted(stage.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
            h = (stage[nk] or {}).get('hash') or {}
            if h:
                nodes.append(h)
    cur = _shenqi_row(rid, sid)
    done = (cur['star'] if cur else 0)
    if done >= len(nodes):
        return None
    h = nodes[done]
    cost = int(h.get('coin_cost') or 0)
    attrs = {}
    for _, av in (h.get('attr') or {}).items():
        a = av.get('array') if isinstance(av, dict) else av
        if isinstance(a, list) and len(a) >= 3 and a[1]:
            attrs[str(a[1])] = int(a[2] or 0)
    return {'next_node': done + 1, 'coin_cost': cost, 'attrs': attrs}


def shenqi_up(rid, sid):
    from currency.service import db_get_assets, db_add_assets
    from attribute.service import apply_delta
    from power.service import power_of

    nx = shenqi_next(rid, sid)
    if not nx:
        return {'ok': False, 'err': 'shenqi_maxed_or_unknown', 'sid': sid}
    before = db_get_assets(rid)
    coin_now = int(before.get('coin') or 0)
    if coin_now < nx['coin_cost']:
        return {'ok': False, 'err': 'not_enough_coin', 'need': nx['coin_cost'], 'have': coin_now}

    db_add_assets(rid, {'coin': -nx['coin_cost']})
    cur = _shenqi_row(rid, sid)
    lev = (cur['lev'] if cur else 1)
    _shenqi_set(rid, sid, lev, nx['next_node'])
    if nx['attrs']:
        apply_delta(rid, nx['attrs'])
    log('tcp.log', '  ** growth.shenqi_up rid=%d sid=%d node->%d coin -%d attrs=%s ref=growth:shenqi:%d:%d'
        % (rid, sid, nx['next_node'], nx['coin_cost'], nx['attrs'], sid, rid))
    return {'ok': True, 'sid': sid, 'star_after': nx['next_node'],
            'coin_spent': nx['coin_cost'], 'attr_delta': nx['attrs'],
            'power_after': power_of(rid)}


# ── 闭环 3：命格激活 ─────────────────────────────────────────────────────
# MinggeOpen[slot]={grade,lev}（门槛 CONFIRMED）；Mingge[bid]=效果串（无直接数值属性）。
# # INFERENCE：激活折算给玩家的属性（替换点，等命格数值表实取）。
_MINGGE_ACTIVATE_DELTA = {'atk_s': 30, 'hp_max': 150}


def mingge_slots():
    d = _load('mingge')
    openm = d.get('MinggeOpen') or {}
    out = []
    for slot, vv in openm.items():
        # MinggeOpen[slot] = {"1":{hash:{grade,lev}}, ...}（再嵌一层）
        inner = vv or {}
        h = None
        for _, iv in inner.items():
            h = (iv or {}).get('hash') or {}
            if h:
                break
        h = h or {}
        out.append({'slot': int(slot), 'grade': int(h.get('grade') or 0),
                    'req_lev': int(h.get('lev') or 0)})
    return out


def mingge_activate(rid, bid):
    """激活一个命格 bid。门槛取 MinggeOpen 首条（CONFIRMED lev）；消耗 coin # INFERENCE。"""
    from currency.service import db_get_assets, db_add_assets
    from attribute.service import apply_delta
    from power.service import power_of
    from role.storage import db_get_role

    bid = int(bid)
    if _mingge_row(rid, bid):
        return {'ok': False, 'err': 'already_activated', 'bid': bid}
    slots = mingge_slots()
    req_lev = slots[0]['req_lev'] if slots else 1
    role = db_get_role(rid) or {}
    if int(role.get('level') or 1) < req_lev:
        return {'ok': False, 'err': 'level_too_low', 'need': req_lev}
    # # INFERENCE：激活消耗（替换点）
    cost = 2000
    before = db_get_assets(rid)
    coin_now = int(before.get('coin') or 0)
    if coin_now < cost:
        return {'ok': False, 'err': 'not_enough_coin', 'need': cost, 'have': coin_now}
    db_add_assets(rid, {'coin': -cost})
    _mingge_add(rid, bid, 1)
    apply_delta(rid, _MINGGE_ACTIVATE_DELTA)
    log('tcp.log', '  ** growth.mingge_activate rid=%d bid=%d coin -%d ref=growth:mingge:%d:%d'
        % (rid, bid, cost, bid, rid))
    return {'ok': True, 'bid': bid, 'coin_spent': cost,
            'attr_delta': _MINGGE_ACTIVATE_DELTA, 'power_after': power_of(rid)}


def build_panel_11600(rid):
    """SC_11600 翅膀面板（② 解耦：读 role_wing 真表，替换 EMPTY_REPLIES 全 0）。
    字段 = proto_defs SC_11600：color u8, wing_id u32, power u32,
    wing_skill table, add_attr table, star u16, lingxi_num u32, jiewing_id u32, surface_list table。
    """
    from protocol.frame import w_u8, w_u16, w_u32
    st = _wing_row(rid)
    return (w_u8(st.get("color",0)) +          # color（P9 wing_up 后=3）
            w_u32(st.get("wing_id",0)) +
            w_u32(st.get("power",0)) +
            w_u16(0) +                          # wing_skill 空表
            w_u16(0) +                          # add_attr 空表
            w_u16(st.get("star",0)) +
            w_u32(0) +                          # lingxi_num
            w_u32(0) +                          # jiewing_id
            w_u16(0))                           # surface_list 空表
