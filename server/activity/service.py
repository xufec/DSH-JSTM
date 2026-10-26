# -*- coding: utf-8 -*-
"""activity.service —— 活动/签到（Phase 11；①c 真值替换）。

签到奖励改为 config_checkin.json Checkin(30天) 配置驱动（CONFIRMED，①c）：
  Day1=银魂币(coin)250000 ... 替换原 INFERENCE gold=1000/coin=5000 占位。
幂等：ref = sign:<rid>:<YYYY-MM-DD>，当天重复领取被 reward_log 拦截。
连续天数按该角色已签次数（streak）取第 (streak%30)+1 天奖励。
"""

import datetime
import json
import os

from core import runtime

log = runtime.log

_CHECKIN = os.path.join(runtime.HERE, 'cfg', 'config_checkin.json')
_tbl = None


def _load():
    global _tbl
    if _tbl is not None:
        return _tbl
    try:
        with open(_CHECKIN, encoding='utf-8') as f:
            raw = json.load(f).get('Checkin') or {}
        _tbl = {}
        for k, v in raw.items():
            _tbl[int(k)] = (v or {}).get('hash') or {}
    except Exception as e:
        log('server.log', '!! checkin cfg load failed: %r' % (e,))
        _tbl = {}
    return _tbl


# assets type 映射（与 currency 资产名对齐：type2=coin 银魂币）。
_ASSET_TYPE_NAME = {1: 'gold', 2: 'coin', 3: 'coupon'}


def today():
    return datetime.date.today().isoformat()


def _streak(rid):
    """该角色累计签到次数（幂等由 reward_log 保证，streak 用已发奖天数）。"""
    try:
        from persistence.db import db_conn, db_release
        con = db_conn()
        r = con.execute("SELECT COUNT(*) FROM reward_log WHERE rid=? AND reference_id LIKE 'sign:%'",
                        (int(rid),)).fetchone()
        db_release(con)
        return int(r[0] or 0)
    except Exception:
        return 0


def day_reward(rid):
    """按连续天数取当日奖励 [{kind,...}]。"""
    tbl = _load()
    n = (_streak(rid) % 30) + 1
    row = tbl.get(n) or {}
    awards = []
    for _aid, spec in (row.get('assets') or {}).items():
        # spec = [null, type, amount]
        if isinstance(spec, list) and len(spec) >= 3:
            name = _ASSET_TYPE_NAME.get(int(spec[1]), 'coin')
            awards.append({'kind': 'asset', 'code': name, 'amount': int(spec[2])})
    for _slot, spec in (row.get('item') or {}).items():
        # spec = [null, bid, count, ...]
        if isinstance(spec, list) and len(spec) >= 3:
            awards.append({'kind': 'item', 'bid': int(spec[1]), 'amount': int(spec[2])})
    return n, awards


def sign(rid):
    """每日签到（幂等）。"""
    from reward.service import grant
    ref = 'sign:%d:%s' % (int(rid), today())
    n, awards = day_reward(rid)
    if not awards:
        # # INFERENCE：该天配置为空时兜底 coin（替换点）
        awards = [{'kind': 'asset', 'code': 'coin', 'amount': 10000}]
    res = grant(int(rid), awards, ref, source='daily_sign')
    log('tcp.log', '  ** activity.sign rid=%d day=%s streak_day=%d already=%s n_awards=%d ref=%s'
        % (rid, today(), n, res.get('already'), len(awards), ref))
    return {'ok': True, 'day': today(), 'streak_day': n,
            'already': res.get('already'), 'awards': awards}
