# -*- coding: utf-8 -*-
"""task/service.py — Phase 2d 迁移。
任务协议的纯编码器（build_mission_entry / build_12400），从 mock_server.py 逐字搬入。
本批只搬编码器；mission_rows/db_get_missions 等 DB 读簇闭包太深，留旧链（见 baseline）。
"""
import sqlite3

# 编码/日志/DB 原语（与 mock_server 同源；runtime 提供 CUR_VER）
from protocol.frame import w_u8, w_u16, w_u32
from core.runtime import log
from persistence.db import db_conn, db_release

import os as _os
import json as _json

MISSION_CFG_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                 '..', 'mission_config.json')
_MISSION_CFG = None


def mission_cfg():
    """惰性加载 APK 任务全表（只读）。[P3deep-migrated 从 mock_server L1962 逐字下沉]"""
    global _MISSION_CFG
    if _MISSION_CFG is None:
        try:
            with open(MISSION_CFG_PATH, encoding='utf-8') as f:
                raw = _json.load(f)
            _MISSION_CFG = {int(k): v for k, v in raw.items()}
            log('server.log', 'mission config loaded: %d 条 <- %s'
                % (len(_MISSION_CFG), MISSION_CFG_PATH))
        except Exception as e:
            _MISSION_CFG = {}
            log('server.log', '!! mission config load failed: %r' % (e,))
    return _MISSION_CFG


def mission_def(bid):
    """按 bid 取 APK 里的任务定义（没有则返回 {}）。[P3deep-migrated]"""
    return mission_cfg().get(int(bid)) or {}


def mission_chain(cfg, rid=None):
    """决定当前该给玩家哪些任务（剧情链逐步解锁）。[P3deep-migrated 从 mock_server 逐字下沉]"""
    from role.storage import db_get_role
    explicit = cfg.get('mission_chain')
    if explicit:
        return [int(x) for x in explicit]
    rid = rid if rid is not None else (cfg.get('role') or {}).get('rid', 1001)
    row = db_get_role(rid) or {}
    lev = int(row.get('level') or (cfg.get('role') or {}).get('lev', 1) or 1)
    mx = int(cfg.get('mission_chain_max', 8))
    chain = sorted(b for b, v in mission_cfg().items()
                   if v.get('type') == 1 and int(v.get('lev') or 0) <= lev)
    if not cfg.get('mission_chain_lock', True):
        return chain[:mx]
    done = {b for b, m in db_get_missions(rid).items()
            if int(m.get('mission_status') or 0) == 3}
    start = 0
    for i, b in enumerate(chain):
        if b not in done:
            start = i
            break
    else:
        start = max(0, len(chain) - 1)
    return chain[start:start + mx]


def mission_rows(cfg, rid, include_done=False):
    """取该角色的任务列表：DB优先；库里没有按 APK 任务表播种。
    [P3deep-migrated 从 mock_server L5006 逐字下沉]"""
    from role.storage import db_get_role
    rows = db_get_missions(rid)
    seeded = 0
    if not rows:
        for m in (cfg.get('missions') or []):
            mm = {'mission_bid': m.get('mission_bid', 0)}
            for c in _MIS_COLS:
                if c in m:
                    mm[c] = m[c]
            db_save_mission(rid, mm)
            seeded += 1
    _have = {int(x.get('mission_bid', -1)) for x in rows.values()}
    for bid in mission_chain(cfg, rid):
        if bid in _have:
            continue
        d = mission_def(bid)
        prog = d.get('progress') or []
        cond = None
        if prog and isinstance(prog[0], (list, tuple)) and len(prog[0]) >= 3:
            cond = {'name': prog[0][0], 'target': prog[0][1], 'need': prog[0][2]}
        db_save_mission(rid, {
            'mission_bid': bid,
            'mission_status': 1 if cond else 2,
            'process_status': 0,
            'target': int(cond['target']) if cond else 0,
            'target_value': int(cond['need']) if cond else 0,
            'value': 0,
            'commit_num': 0, 'loop_count': 0, 'loop_num': 1,
            'code': 0, 'accept_time': 0,
        })
        log('tcp.log', '  .. mission %d (%s) 播种 cond=%r status=%d'
            % (bid, d.get('name'), cond, 1 if cond else 2))
        seeded += 1
    rows = db_get_missions(rid)
    if seeded:
        log('tcp.log', '  ** missions seeded into DB for rid=%s (+%d, 共 %d 条, '
                       '来自 APK 任务表/等级 %s)'
            % (rid, seeded, len(rows),
               (db_get_role(rid) or {}).get('level')))
    _chain = mission_chain(cfg, rid)
    _head = None
    for _b in _chain:
        _m = rows.get(_b)
        if _m is not None and int(_m.get('mission_status') or 0) < 3:
            _head = _b
            break
    _changed = 0
    for k, m in list(rows.items()):
        st = int(m.get('mission_status') or 0)
        if st == 3:
            continue
        prog = (mission_def(k).get('progress') or [])
        if prog and isinstance(prog[0], (list, tuple)) and len(prog[0]) >= 3:
            need = int(m.get('target_value') or 0)
            have = int(m.get('value') or 0)
            if need > 0 and have >= need:
                if st != 2:
                    db_save_mission(rid, {'mission_bid': k, 'mission_status': 2})
                    m['mission_status'] = 2
                    _changed += 1
            continue
        if k == _head:
            if st != 2:
                db_save_mission(rid, {'mission_bid': k, 'mission_status': 2})
                m['mission_status'] = 2
                _changed += 1
        elif st == 2:
            db_save_mission(rid, {'mission_bid': k, 'mission_status': 1})
            m['mission_status'] = 1
            _changed += 1
    if _changed:
        log('tcp.log', '  .. mission status normalized: chain_head=%s (变更 %d 条)'
            % (_head, _changed))
    out = [rows[k] for k in sorted(rows)]
    if not include_done:
        out = [m for m in out if int(m.get('mission_status') or 0) != 3]
    return out


_MIS_COLS = ['mission_status', 'process_status', 'target', 'target_value',
             'value', 'commit_num', 'loop_count', 'loop_num', 'code',
             'accept_time']


def db_get_missions(rid):
    """读该角色的全部任务（返回 dict: bid -> 行）。[③第一步 从 mock_server L4577 逐字下沉]"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        rows = con.execute('SELECT * FROM missions WHERE rid=?', (rid,)).fetchall()
        db_release(con)
        return {int(r['mission_bid']): dict(r) for r in rows}
    except Exception as e:
        log('tcp.log', '  !! db_get_missions failed: %r' % (e,))
        return {}


def db_save_mission(rid, m):
    """按 bid upsert 一条任务状态。[③ 从 mock_server L4592 逐字下沉]"""
    import time as _time
    try:
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO missions (rid, mission_bid) VALUES (?,?)',
                    (rid, m['mission_bid']))
        cols = [c for c in _MIS_COLS if c in m]
        if cols:
            con.execute('UPDATE missions SET %s, updated_at=? WHERE rid=? AND mission_bid=?' %
                        ','.join('%s=?' % c for c in cols),
                        [m[c] for c in cols] + [int(_time.time()), rid, m['mission_bid']])
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_save_mission failed: %r' % (e,))
        return False



def build_mission_entry(m):
    """任务条目（SC_12400.mission_list / SC_12401.missions 的元素）

    字段来自 protocol/manual.md（全部简单类型，无未解出的 D|Dsc*| 子表）：
      mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16,
      loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32,
      value:u32, show_lave_time:u8, lave_time:u32, accept_time:u32
    """
    def _n(v, d):
        return d if v is None else v
    return (w_u32(_n(m.get('mission_bid'), 35000)) +
            w_u8(_n(m.get('mission_status'), 1)) +
            w_u16(_n(m.get('commit_num'), 0)) +
            w_u16(_n(m.get('loop_count'), 0)) +
            w_u16(_n(m.get('loop_num'), 1)) +
            w_u8(_n(m.get('code'), 0)) +
            w_u8(_n(m.get('process_status'), 0)) +
            w_u32(_n(m.get('target'), 0)) +
            w_u32(_n(m.get('target_value'), 1)) +
            w_u32(_n(m.get('value'), 0)) +
            w_u8(_n(m.get('show_lave_time'), 0)) +
            w_u32(_n(m.get('lave_time'), 0)) +
            w_u32(_n(m.get('accept_time'), 0)))


def build_12400(missions):
    """SC_12400 = mission_list:table(见 build_mission_entry)"""
    b = w_u16(len(missions))
    for m in missions:
        b += build_mission_entry(m)
    return b
