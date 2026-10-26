# -*- coding: utf-8 -*-
"""gm.service —— GM Manager 正式服务链路（Phase 13，§36 硬性要求）。

GM 修改必须走 Service 链路，禁止散落直改。提供：
  - log_gm(action, rid, detail)：写 server/logs/gm.log 审计。
  - set_level(rid, lev)：正式等级变更（roles 表权威落库）。
  - set_assets(rid, vals, mode)：正式资产变更，经 currency.service。
reference_id = gm:<action>:<rid>:<ts>（审计溯源）。
"""

import os
import time

from core import runtime

LOG_PATH = os.path.join(runtime.HERE, 'logs', 'gm.log')


def log_gm(action, rid, detail=''):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = '[%s] %s rid=%s %s\n' % (ts, action, rid, detail)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        try:
            runtime.log('server.log', '!! gm.log write failed: %r' % (line,))
        except Exception:
            pass
    return line


def set_level(rid, lev):
    """正式等级变更链路：更新 roles.level，返回 {'old','new'}。

    属性/战力重算由调用侧推送前经 attribute.service 触发；本函数只做权威落库。
    """
    from persistence.db import db_conn, db_release
    lev = int(lev)
    con = db_conn()
    r = con.execute('SELECT level FROM roles WHERE rid=?', (int(rid),)).fetchone()
    old = int(r[0]) if r else 0
    con.execute('UPDATE roles SET level=? WHERE rid=?', (lev, int(rid)))
    if con.total_changes == 0:
        con.execute('INSERT OR IGNORE INTO roles (rid, level) VALUES (?,?)', (int(rid), lev))
    con.commit()
    db_release(con)
    log_gm('setlevel', rid, 'old=%d new=%d ref=gm:setlevel:%d:%d' % (old, lev, int(rid), int(time.time())))
    return {'old': old, 'new': lev}


def set_assets(rid, vals, mode='set'):
    """正式资产变更链路：经 currency.service.db_add_assets。返回 {'mode','delta','now'}。"""
    from currency.service import db_add_assets, db_get_assets
    rid = int(rid)
    if mode == 'add':
        delta = {k: int(v) for k, v in vals.items()}
    else:
        cur = db_get_assets(rid)
        delta = {k: int(v) - int(cur.get(k, 0) or 0) for k, v in vals.items()}
    db_add_assets(rid, delta)
    now = db_get_assets(rid)
    log_gm('setassets', rid, 'mode=%s delta=%r ref=gm:setassets:%d:%d'
           % (mode, delta, rid, int(time.time())))
    return {'mode': mode, 'delta': delta, 'now': {k: now.get(k, 0) for k in vals}}
