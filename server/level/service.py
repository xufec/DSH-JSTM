# -*- coding: utf-8 -*-
"""level.service —— 等级/经验/升级成长（Phase 2 step 3）。

设计依据：phase2_design.md §二 level/。
迁移来源（mock_server.py 当前行号）：
  LEVEL_TABLE_PATH / level_table / max_lev / level_row /
  level_need / level_next_total / level_attr_point   L5683–5735
  LEVEL_ATTR_GROWTH                                  L5744–5749
  add_role_exp                                       L5771–5810
  apply_level_attr_growth                            L5813–5830

★ 循环依赖处理：add_role_exp 需要 role.storage 的 role_state/db_save_role/_sc_to_db_updates，
  而 role.storage.role_state 又需要本模块的 level_need —— 在函数体内**惰性 import** role.storage，
  避免加载期循环。
"""

import os
import json

from core import runtime

log = runtime.log

LEVEL_TABLE_PATH = os.path.join(runtime.HERE, '..', 'analysis', '1.4.9', 'level',
                                'level_table.json')
_LEVEL_TABLE = None


def level_table():
    global _LEVEL_TABLE
    if _LEVEL_TABLE is None:
        try:
            with open(LEVEL_TABLE_PATH, encoding='utf-8') as f:
                _LEVEL_TABLE = json.load(f)
            log('server.log', 'level table loaded: max_lev=%s (%d 级) <- %s'
                % (_LEVEL_TABLE.get('max_lev'),
                   len(_LEVEL_TABLE.get('levels') or {}), LEVEL_TABLE_PATH))
        except Exception as e:
            log('server.log', '!! level table load failed: %r（升级将不可用）' % (e,))
            _LEVEL_TABLE = {'max_lev': 1, 'levels': {}}
    return _LEVEL_TABLE


def max_lev():
    return int(level_table().get('max_lev') or 1)


def level_row(lev):
    """取 Config.RoleAttr[lev] 的 5 个字段；查不到返回 None。"""
    return (level_table().get('levels') or {}).get(str(int(lev)))


def level_need(lev):
    """从 lev 级升到 lev+1 级所需经验 = RoleAttr[lev+1].exp_max（与客户端一致）。

    越界（已到上限）返回 None。
    """
    if int(lev) >= max_lev():
        return None
    r = level_row(int(lev) + 1)
    if not r:
        return None
    return int(r.get('exp_max') or 0)


def level_next_total(lev):
    """RoleAttr[lev+1].exp_total —— 对应 SC_10301 的 exp_total_nextlev。"""
    r = level_row(int(lev) + 1)
    return int(r.get('exp_total') or 0) if r else 0


def level_attr_point(lev):
    """RoleAttr[lev+1].attr_point —— 对应 SC_10301 的 attr_point。"""
    r = level_row(int(lev) + 1)
    return int(r.get('attr_point') or 0) if r else 0


# ★ 逐级属性成长 —— IMPLEMENTATION_FALLBACK / TEST_ONLY（APK 内无逐级属性表）。
LEVEL_ATTR_GROWTH = {
    'strength': 1, 'intellect': 1, 'armor': 1, 'constiution': 1,
    'atk_s': 12, 'atk_p': 8, 'def_s': 6, 'def_p': 4,
    'hp_max': 60, 'atk_speed': 1, 'hit': 4, 'dodge': 4,
    'crit': 2, 'tenacity': 2,
}


def add_role_exp(cfg, rid, amount, apply_attr_growth=True):
    """★ Phase E 核心：给角色加经验，并按原版等级表结算升级（原 mock_server L5771）。

    返回 dict(old_lev, lev, exp, ups, need_next)。
    """
    # 惰性 import，避免与 role.storage 的加载期循环
    from role.storage import role_state, db_save_role, _sc_to_db_updates
    from currency.service import db_set_assets

    st = role_state(cfg)
    lev = int(st.get('lev') or 1)
    old_lev = lev
    exp = int(st.get('exp') or 0) + int(amount)
    ups = 0
    while lev < max_lev():
        need = level_need(lev)
        if not need or exp < need:
            break
        exp -= need
        lev += 1
        ups += 1

    db_set_assets(rid, {'exp': exp})
    db_save_role(rid, **_sc_to_db_updates(dict(st, lev=lev, exp=exp)))
    if ups:
        if apply_attr_growth:
            apply_level_attr_growth(rid, ups)
        log('tcp.log', '  ** LEVEL UP role %s: %d -> %d (升 %d 级), exp 余 %d, '
                       '下一级需 %s' % (rid, old_lev, lev, ups, exp, level_need(lev)))
    return {'old_lev': old_lev, 'lev': lev, 'exp': exp, 'ups': ups,
            'need_next': level_need(lev)}


def apply_level_attr_growth(rid, ups):
    """升级后按 LEVEL_ATTR_GROWTH 增加属性（IMPLEMENTATION_FALLBACK）。"""
    from attribute.service import db_get_attr, db_save_attr
    try:
        attr = db_get_attr(rid) or {}
        upd = {}
        for k, per in LEVEL_ATTR_GROWTH.items():
            if k in attr and attr[k] is not None:
                upd[k] = int(attr[k] or 0) + per * int(ups)
        if upd:
            db_save_attr(rid, upd)
            log('tcp.log', '  ** level attr growth x%d (FALLBACK): %s'
                % (ups, {k: upd[k] for k in list(upd)[:5]}))
    except Exception as e:
        log('tcp.log', '  !! apply_level_attr_growth failed: %r' % (e,))
