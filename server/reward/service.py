# -*- coding: utf-8 -*-
"""reward.service —— 统一发奖入口 + 幂等日志（Phase 2c，新增）。

设计依据：phase2_design.md §二 reward/、§4.4。
★ 本批只建表与入口，**不改变任何现有系统的调用行为**——现有系统仍走旧逻辑，
  Phase 5 再把各发奖点切到 grant()。

幂等：同一 (rid, reference_id) 只发一次；reward_log 表记录已发 reference_id。
"""

import time

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log


def db_reward_init():
    """建 reward_log 幂等表（由 persistence.db.db_init 调用）。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS reward_log (
        rid INTEGER, reference_id TEXT, source TEXT, granted_ts INTEGER,
        PRIMARY KEY (rid, reference_id))""")
    con.commit()
    db_release(con)


def reward_log(rid, reference_id):
    """该 (rid, reference_id) 是否已发过奖。"""
    try:
        con = db_conn()
        row = con.execute('SELECT 1 FROM reward_log WHERE rid=? AND reference_id=?',
                          (rid, str(reference_id))).fetchone()
        db_release(con)
        return row is not None
    except Exception as e:
        log('tcp.log', '  !! reward_log query failed: %r' % (e,))
        return False


def _mark_granted(rid, reference_id, source):
    con = db_conn()
    con.execute('INSERT OR IGNORE INTO reward_log (rid,reference_id,source,granted_ts) '
                'VALUES (?,?,?,?)', (rid, str(reference_id), str(source or ''),
                                     int(time.time())))
    con.commit()
    db_release(con)


def grant(rid, awards, reference_id, source=''):
    """统一发奖入口（幂等）。

    awards: [{'kind': 'asset'|'item', 'code': <资产名或bid>, 'amount': n}, ...]
    返回 dict(ok, already, applied)。已发过则直接返回 already=True，不重复发。
    """
    if reference_id and reward_log(rid, reference_id):
        return {'ok': True, 'already': True, 'applied': []}
    applied = []
    try:
        for a in (awards or []):
            kind = a.get('kind')
            if kind == 'asset':
                from currency.service import db_add_assets
                db_add_assets(rid, {a.get('code'): int(a.get('amount') or 0)})
                applied.append(a)
            elif kind == 'item':
                from inventory.service import db_bag_add
                db_bag_add(rid, int(a.get('bid')), int(a.get('amount') or 1))
                applied.append(a)
        if reference_id:
            _mark_granted(rid, reference_id, source)
        log('tcp.log', '  ** grant rid=%s ref=%s src=%s n=%d'
            % (rid, reference_id, source, len(applied)))
        return {'ok': True, 'already': False, 'applied': applied}
    except Exception as e:
        log('tcp.log', '  !! grant failed rid=%s ref=%s: %r' % (rid, reference_id, e))
        return {'ok': False, 'already': False, 'applied': applied}
