# -*- coding: utf-8 -*-
"""growth_target.service —— 开服成长计划（30500/30501/30502）。

★ 证据等级：
  · 命令语义：**CONFIRMED** —— `protocol/cmd_table.json` 明确写
      `30501 领取登陆奖励` / `30502 领取充值奖励` / `30500 请求成长目标信息`
      （比"从字节码猜 type 映射"权威；先前由 `action_kaifu_growplan_item.luac`
      的 type 分派推出的"30507=登录"是**错的**，已由命令名纠正）
  · 帧结构：**CONFIRMED** —— `protocol/fields.json`
      SC_30501/30502 = {result:u8, msg:s, items:table{item_bid:u32, num:u32}}
  · 奖励数值：**CONFIRMED** —— `server/cfg/config_growth_target_data.json`
      GrowthTarget[day] = {charge_gold, login_reward{items}, charge_reward{items}}
  · `total_charge`（累计充值）：**INFERENCE** —— 原版存于服务端；本实现落在
      `role_gt.total_charge`，由充值/GM 写入。

★ 幂等：发奖走 `reward.service.grant`，reference_id = `gt:{kind}:{rid}:{day}` ⇒
  重复点击/断线重连重发**不会**重复发。发过就不再发（`reward_log` 兜底），
  认领状态另存 `role_gt`（面板要用）。
"""

import json
import os

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.normpath(os.path.join(HERE, '..', 'cfg', 'config_growth_target_data.json'))

_cfg = None


def gt_cfg():
    """读 config_growth_target_data.json。返回 {'targets': {day:int -> row}}。"""
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(CFG, encoding='utf-8') as f:
            j = json.load(f)
        t = {}
        for k, v in (j.get('GrowthTarget') or {}).items():
            if str(k).isdigit():
                t[int(k)] = (v.get('hash') or v)
        _cfg = {'targets': t, 'today': (j.get('TodayTarget') or {}),
                'half': (j.get('HalfDiscountBuy') or {}),
                'groups': (j.get('RewardGroup') or {})}
        log('server.log', 'growth_target cfg: %d days' % len(t))
    except Exception as e:
        log('server.log', '!! config_growth_target_data load failed: %r' % (e,))
        _cfg = {'targets': {}, 'today': {}, 'half': {}, 'groups': {}}
    return _cfg


def _awards(reward_map):
    """配置的 `{1:[null,bid,cnt,?], ...}` → RewardService 的 awards。"""
    out = []
    for _k, row in (reward_map or {}).items():
        try:
            bid = int(row[1]); cnt = int(row[2])
        except Exception:
            continue
        if bid and cnt:
            out.append({'kind': 'item', 'bid': bid, 'amount': cnt})
    return out


def db_gt_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_gt (
        rid INTEGER PRIMARY KEY, login_day INTEGER, charge_day INTEGER,
        total_charge INTEGER)""")
    con.commit()
    db_release(con)


def state(rid):
    db_gt_init()
    con = db_conn()
    r = con.execute('SELECT login_day,charge_day,total_charge FROM role_gt WHERE rid=?',
                    (int(rid),)).fetchone()
    db_release(con)
    if not r:
        return {'login_day': 0, 'charge_day': 0, 'total_charge': 0}
    return {'login_day': int(r[0] or 0), 'charge_day': int(r[1] or 0),
            'total_charge': int(r[2] or 0)}


def _save(rid, **kw):
    s = state(rid)
    s.update(kw)
    db_gt_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_gt VALUES (?,?,?,?)',
                (int(rid), int(s.get('login_day') or 0), int(s.get('charge_day') or 0),
                 int(s.get('total_charge') or 0)))
    con.commit()
    db_release(con)
    return s


def set_total_charge(rid, amount):
    """由充值链路/GM 调用，记录累计充值（`30502` 的门槛依据）。"""
    return _save(rid, total_charge=int(amount))


def claim(rid, day, kind='login'):
    """领取 `day` 的 登录/充值 奖励。返回 (ok, msg, items[(bid,cnt)])。

    kind: 'login' → `login_reward`（无门槛）
          'charge' → `charge_reward`（需 `total_charge >= charge_gold`）
    """
    row = (gt_cfg()['targets'] or {}).get(int(day))
    if not isinstance(row, dict):
        return False, '无此天数配置', []
    st = state(rid)
    if kind == 'login':
        if int(st['login_day']) >= int(day):
            return False, '已领取', []
        awards = _awards(row.get('login_reward'))
        ref = 'gt:login:%d:%d' % (int(rid), int(day))
    else:
        need = int(row.get('charge_gold') or 0)
        if int(st['total_charge']) < need:
            return False, '累计充值不足', []
        if int(st['charge_day']) >= int(day):
            return False, '已领取', []
        awards = _awards(row.get('charge_reward'))
        ref = 'gt:charge:%d:%d' % (int(rid), int(day))
    if not awards:
        return False, '该档无奖励配置', []
    from reward.service import grant
    res = grant(rid, awards, ref, source='growth_target')
    if not (res or {}).get('ok'):
        return False, '发放失败', []
    _save(rid, **({'login_day': int(day)} if kind == 'login'
                  else {'charge_day': int(day)}))
    items = [(a['bid'], a['amount']) for a in awards]
    log('tcp.log', '  ** 成长计划领取 rid=%d day=%d kind=%s items=%s already=%s'
        % (rid, day, kind, items, (res or {}).get('already')))
    return True, '', items
