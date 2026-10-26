# -*- coding: utf-8 -*-
"""currency.service —— 通用资产（货币/经验）读写（Phase 2 step 2/3）。

设计依据：phase2_design.md §二 currency/。
迁移来源（mock_server.py 当前行号）：
  db_get_assets   L4353–4363
  db_add_assets   L4366–4382
  db_set_assets   L5752–5768

只依赖 persistence.db（db_conn/db_release）+ core.runtime.log。无循环 import。
"""

from persistence.db import db_conn, db_release
from core import runtime

log = runtime.log


def db_get_assets(rid):
    """读该角色的全部资产 → {资产名: 数量}。"""
    try:
        con = db_conn()
        rows = con.execute('SELECT name, amount FROM role_assets WHERE rid=?',
                           (rid,)).fetchall()
        db_release(con)
        return {r[0]: r[1] for r in rows}
    except Exception as e:
        log('tcp.log', '  !! db_get_assets failed: %r' % (e,))
        return {}


def db_add_assets(rid, delta):
    """按 {资产名: 增量} 累加（不存在则插入）。"""
    if not delta:
        return True
    try:
        con = db_conn()
        for name, amount in delta.items():
            con.execute('INSERT OR IGNORE INTO role_assets (rid, name, amount) '
                        'VALUES (?,?,0)', (rid, str(name)))
            con.execute('UPDATE role_assets SET amount = amount + ? '
                        'WHERE rid=? AND name=?', (int(amount), rid, str(name)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_add_assets failed: %r' % (e,))
        return False


def db_set_assets(rid, values):
    """把通用资产表里的某些项**设为绝对值**（db_add_assets 只能加）。"""
    if not values:
        return True
    try:
        con = db_conn()
        for name, amount in values.items():
            con.execute('INSERT OR IGNORE INTO role_assets (rid, name, amount) '
                        'VALUES (?,?,0)', (rid, str(name)))
            con.execute('UPDATE role_assets SET amount = ? WHERE rid=? AND name=?',
                        (int(amount), rid, str(name)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_set_assets failed: %r' % (e,))
        return False
