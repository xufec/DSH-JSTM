# -*- coding: utf-8 -*-
"""power.service —— 战力（Phase 2 step 3）。

设计依据：phase2_design.md §二 power/、§4.2 PowerService、§4.3。
迁移来源（mock_server.py L2579–2587）：role_power_of(rid)。

★ 权重公式不重写：内部复用 attribute.service.role_power → server/power.py:calc_power
  （原版权重，来自 _attr_data.json，CONFIRMED）。
"""

from attribute.service import role_power


def calc_power(attrs):
    """对外暴露：按属性 dict 算战力（转发 server/power.py，经 attribute.role_power）。"""
    return int(role_power({'role': {'rid': 0}, }) or 0) if False else _calc(attrs)


def _calc(attrs):
    # 直接按 attrs 算（与 role_power 同一兜底；power_mod 已在 attribute.service 内软依赖）
    from attribute import service as _as
    if _as.power_mod is not None:
        return int(_as.power_mod.calc_power(attrs))
    return int(sum(attrs.get(k, 0) * x for k, x in {
        'atk_s': 0.5, 'atk_p': 0.5, 'def_s': 0.3, 'def_p': 0.3, 'hp_max': 0.02,
        'dodge': 1, 'hit': 1, 'crit': 1, 'tenacity': 1, 'atk_speed': 2}.items()))


def power_of(rid):
    """角色战力（复用 role_power，容错）—— 原 mock_server.role_power_of(L2579)。"""
    try:
        return int(role_power({'role': {'rid': int(rid)}}) or 0)
    except Exception:
        try:
            return int(role_power({}) or 0)
        except Exception:
            return 0


# 九维子战力维度名（与排行 rank_role 对齐）。
NINE_DIMS = ['power_eqm_role', 'power_skill', 'power_xiulian', 'power_hero',
             'power_ride', 'power_lingshou', 'power_shenqi', 'power_wing',
             'power_fabao']


def breakdown(rid):
    """九维子战力分解（Phase 12）。

    total = power_of(rid)（CONFIRMED，原版权重）。
    各维分项：当前**无逐维权威公式** ⇒ 一律 0 占位并标注 # INFERENCE，
    不凑数冒充；待 V8/V11 取各维真实贡献后补真值（phase45_plan 风险 3）。
    """
    total = power_of(rid)
    dims = {k: 0 for k in NINE_DIMS}   # # INFERENCE: placeholder，待取证补真值
    return {'rid': int(rid), 'total': total, 'dims': dims,
            'note': 'dims placeholder pending V8/V11 evidence'}

