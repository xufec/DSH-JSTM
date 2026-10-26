# -*- coding: utf-8 -*-
"""enhance.service —— 装备强化服务（Phase 7；①c 真值替换）。

①c CONFIRMED：config_intensify.json
  Intensify[lev]               成功率 rate_srv（概率点，L1=1000/10000=100%）。
  IntensifyCost[lev][eqm_type] coin 消耗（L1=2400）+ stone_bid=36006。
  IntensifyReward / IntensifyAllReward 单件/全套属性加成。
强化成功 → AttributeService.apply_delta → PowerService 重算 → 推送 10304/10502。
"""

import json
import os

from core import runtime

log = runtime.log

_PATH = os.path.join(runtime.HERE, 'cfg', 'config_intensify.json')
_cfg = None


def _load():
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(_PATH, encoding='utf-8') as f:
            _cfg = json.load(f)
    except Exception as e:
        log('server.log', '!! intensify cfg load failed: %r' % (e,))
        _cfg = {}
    return _cfg


def _h(v):
    return (v or {}).get('hash') or v or {}


def success_rate(level):
    """强化到 level 的成功率（CONFIRMED：Intensify[level].rate_srv / 10000）。"""
    e = _h((_load().get('Intensify') or {}).get(str(int(level))))
    rs = int(e.get('rate_srv') or 1000)
    return rs / 1000.0


def enhance_cost(level, eqm_type=100):
    """强化到 level 的消耗（CONFIRMED：IntensifyCost）。"""
    c = (_load().get('IntensifyCost') or {}).get(str(int(level))) or {}
    row = _h(c.get(str(int(eqm_type))) or c.get('100'))
    return {'coin': int(row.get('coin') or 0),
            'stone_bid': int(row.get('stone_bid') or 36006),
            'stone_num': int(row.get('num') or 1)}


def apply_enhance(eq_attrs, level):
    """把强化等级叠加进装备属性。# INFERENCE：线性放大系数，待 IntensifyReward 逐档精确接线。"""
    mult = 1.0 + 0.05 * level
    return {k: int(v * mult) for k, v in (eq_attrs or {}).items()}
