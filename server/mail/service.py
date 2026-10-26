# -*- coding: utf-8 -*-
"""mail.service —— 邮件列表/读取/领取附件（Phase 12）。

数据表：role_mail（rid,id,from_name,subject,content,assets,items,send_time,read_time,time_out）。
附件领取：RewardService.grant(reference_id=mail:<mid>:<rid>) 幂等，重复领取被 reward_log 拦截。
"""

import json
import sqlite3

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log


def _ensure(con):
    con.execute("""CREATE TABLE IF NOT EXISTS role_mail (
        rid INTEGER, id INTEGER, from_name TEXT, subject TEXT, content TEXT,
        assets TEXT, items TEXT, send_time INTEGER, read_time INTEGER,
        time_out INTEGER, PRIMARY KEY (rid, id))""")


def list_mails(rid):
    out = []
    con = db_conn()
    _ensure(con)
    con.row_factory = sqlite3.Row
    for r in con.execute('SELECT * FROM role_mail WHERE rid=? ORDER BY id DESC', (int(rid),)):
        out.append({'id': r['id'], 'from': r['from_name'], 'subject': r['subject'],
                    'has_read': bool(r['read_time']),
                    'assets': r['assets'], 'items': r['items']})
    db_release(con)
    return out


def claim(rid, mid):
    """领取一封邮件附件（幂等）。"""
    from reward.service import grant
    con = db_conn()
    _ensure(con)
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT assets, items FROM role_mail WHERE rid=? AND id=?',
                    (int(rid), int(mid))).fetchone()
    db_release(con)
    if r is None:
        return {'ok': False, 'err': 'mail_not_found', 'mid': mid}
    awards = []
    try:
        for a in (json.loads(r['assets'] or '[]') or []):
            awards.append({'kind': 'asset', 'code': str(a.get('type') or a.get('code')),
                           'amount': int(a.get('count') or a.get('amount') or 0)})
        for it in (json.loads(r['items'] or '[]') or []):
            awards.append({'kind': 'item', 'bid': int(it.get('bid') or 0),
                           'amount': int(it.get('num') or 1)})
    except Exception as e:
        log('tcp.log', '  !! mail.claim parse failed rid=%d mid=%d: %r' % (rid, mid, e))
        return {'ok': False, 'err': 'parse_failed'}
    if not awards:
        return {'ok': False, 'err': 'no_attachment', 'mid': mid}
    ref = 'mail:%d:%d' % (int(mid), int(rid))
    res = grant(int(rid), awards, ref, source='mail_claim')
    log('tcp.log', '  ** mail.claim rid=%d mid=%d already=%s ref=%s n=%d'
        % (rid, mid, res.get('already'), ref, len(awards)))
    return {'ok': True, 'mid': mid, 'already': res.get('already'), 'awards': awards}
