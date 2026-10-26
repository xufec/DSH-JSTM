# -*- coding: utf-8 -*-
"""achievement 包 —— 成就系统服务端闭环（任务2）。

数据：config_chengjiu.ChengJiuData 342 条 CONFIRMED（bid/name/desc/cent积分/trigger_mod）。
状态：复用 dungeon_progress KV（ptype='ach'）：
  pkey='bid:<bid>'  = state（0未达成/1已达成未领/2已领）。
奖励：领取经 RewardService.grant 幂等 ref=ach:<bid>:<rid>。
  # INFERENCE：cent 积分 -> 金币奖励 = cent*100（配置无金币字段，替换点）。
CS 客户端命令：帧格式未取证，本批不接客户端命令（待帧格式确认后补）。
"""

import json
import os

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log
_CJ = os.path.join(runtime.HERE, 'cfg', 'config_chengjiu.json')


def _load_all():
    try:
        with open(_CJ, encoding='utf-8') as f:
            d = json.load(f)
        rows = d.get('ChengJiuData') or []
        if isinstance(rows, dict):
            rows = list(rows.values())
        out = []
        for it in rows:
            # ★ 2026-10-17 修（运行期实报 AttributeError: 'str' object has no attribute 'get'）：
            #   原来无脑 `(it or {}).get('hash')`，只要**有一条**条目不是 dict（配置写坏/半写入/
            #   旧版结构），整个 try 就炸 ⇒ **342 条成就全部加载不出来**（成就面板全空）。
            #   改为：单条形状不认识就跳过（不猜），不影响其它条目。
            if not isinstance(it, dict):
                continue
            h = it.get('hash')
            if not isinstance(h, dict):
                h = it                     # 没有 hash 层时，条目本身即字段表
            out.append({'bid': int(h.get('bid') or 0), 'name': h.get('name') or '',
                        'desc': h.get('desc') or '', 'cent': int(h.get('cent') or 0),
                        'type': int(h.get('type') or 0)})
        return out
    except Exception as e:
        log('server.log', '!! achievement load failed: %r' % (e,))
        return []


def list_all():
    return _load_all()


def _state_get(rid, bid):
    con = db_conn()
    r = con.execute('SELECT value FROM dungeon_progress WHERE rid=? AND ptype=? AND pkey=?',
                    (int(rid), 'ach', 'bid:%d' % int(bid))).fetchone()
    db_release(con)
    return int(r[0]) if r is not None else 0


def _state_set(rid, bid, state):
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO dungeon_progress (rid,ptype,pkey,value) VALUES (?,?,?,?)',
                (int(rid), 'ach', 'bid:%d' % int(bid), int(state)))
    con.commit()
    db_release(con)


def progress(rid):
    """返回该 rid 的成就进度列表（state 标注）。"""
    out = []
    for a in _load_all():
        out.append({'bid': a['bid'], 'name': a['name'], 'desc': a['desc'],
                    'cent': a['cent'], 'state': _state_get(rid, a['bid'])})
    return out


def mark_done(rid, bid):
    """模拟达成（GM 驱动）：未达成 -> state=1。"""
    st = _state_get(rid, bid)
    if st >= 1:
        return {'ok': True, 'already': True, 'state': st}
    _state_set(rid, bid, 1)
    log('tcp.log', '  ** ach.mark_done rid=%d bid=%d' % (rid, bid))
    return {'ok': True, 'already': False, 'state': 1}


def claim(rid, bid):
    """领取成就奖励（幂等）：state 须=1；grant ref=ach:<bid>:<rid>。"""
    st = _state_get(rid, bid)
    if st == 0:
        return {'ok': False, 'err': 'not_done'}
    if st == 2:
        return {'ok': False, 'err': 'already_claimed'}
    meta = next((a for a in _load_all() if a['bid'] == int(bid)), None)
    cent = (meta or {}).get('cent', 0)
    # # INFERENCE：cent*100 金币奖励（配置无金币字段，替换点）
    awards = [{'kind': 'asset', 'code': 'gold', 'amount': cent * 100}]
    from reward.service import grant
    ref = 'ach:%d:%d' % (int(bid), int(rid))
    res = grant(int(rid), awards, ref, source='achievement')
    _state_set(rid, bid, 2)
    log('tcp.log', '  ** ach.claim rid=%d bid=%d cent=%d gold+%d already=%s ref=%s'
        % (rid, bid, cent, cent * 100, res.get('already'), ref))
    return {'ok': True, 'cent': cent, 'gold': cent * 100, 'already': res.get('already')}
