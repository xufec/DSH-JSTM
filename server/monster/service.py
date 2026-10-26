# -*- coding: utf-8 -*-
"""monster.service —— 怪物数值读取层（Phase 5 战斗数值引擎）。

依据：analysis/extraction/monster_values.md E1/E2——
  cfg/config_mon_data.json 的 Mon/MonData/data 三个核心 dict **均为空**，
  且怪物表**无显式 HP/ATK/DEF**（由服务端公式 level×type×scale 计算）。

# INFERENCE: JSTMCompatibleMonsterModel, formula UNKNOWN per E1/E2。
  原版公式在服务端、APK 内无法取证。本模型是**兼容占位**，不是真值：
    hp_max = base_hp(lev) * type_mult * scale
    atk_s  = base_atk(lev) * type_mult * scale
    def_s  = base_def(lev) * type_mult * scale
    exp    = base_exp(lev) * scale
    coin   = base_coin(lev) * scale
  一旦 cfg/config_mon_data.json 的 Mon 主表非空，_load() 优先返回真值行（替换点）。
"""
import os
import json

from core import runtime

log = runtime.log

_MON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                         'cfg', 'config_mon_data.json')
_MON = None


def _load():
    """惰性加载 config_mon_data.json 的 Mon 主表（当前为空 dict）。"""
    global _MON
    if _MON is None:
        try:
            with open(_MON_PATH, encoding='utf-8') as f:
                cfg = json.load(f)
            _MON = {(v.get('id') or k): v
                    for k, v in ((cfg.get('Config') or {}).get('Mon') or {}).items()}
            log('server.log', 'monster config loaded: %d 条 <- %s'
                % (len(_MON), _MON_PATH))
        except Exception as e:
            _MON = {}
            log('server.log', '!! monster config load failed: %r' % (e,))
    return _MON


# # INFERENCE: JSTMCompatibleMonsterModel base 表（自行设计，非原版）
_BASE_HP = lambda lev: 200 + lev * 25      # lv70 → 1950
_BASE_ATK = lambda lev: 8 + lev * 1.2      # lv70 → 92
_BASE_DEF = lambda lev: 4 + lev * 0.6     # lv70 → 46
_BASE_EXP = lambda lev: lev * 8           # lv70 → 560
_BASE_COIN = lambda lev: lev * 5          # lv70 → 350

# # INFERENCE: type 倍率（normal/elite/boss，config 无显式 type 字段时默认 normal=1.0）
_TYPE_MULT = {'normal': 1.0, 'elite': 1.5, 'boss': 2.5}


# ── 目标④补强：怪物等级来源（把「疑似」换成 CONFIRMED 配置）────────────────
_GUAJI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_guaji.json')
_GUAJI_BAND = None


def band_level(mon_id):
    """`mon_bid` → 挂机地图**等级区间上界**（CONFIRMED 来源：`server/_guaji.json`）。

    为什么用它：挂机图（map_bid 10002~10011）的怪与**等级区间**强绑定，这份表由客户端
    `config_guaji` 导出，且**已被实机 UI 对表验证**（挂机面板显示「乾坤日月谷 65–74 级」
    与配置逐字一致）。取区间**上界**：玩家按区间进图，怪按区间上界取数值，
    避免出现"图是 65–74、怪却按 35 级算"。

    非挂机怪（如 `20001`）取不到 ⇒ 返回 None，由调用方回退到 APK 表字段（INFERRED）。
    """
    global _GUAJI_BAND
    if _GUAJI_BAND is None:
        _GUAJI_BAND = {}
        try:
            with open(_GUAJI_PATH, encoding='utf-8') as f:
                for s in (json.load(f).get('spots') or []):
                    mb = int(s.get('mon_bid') or 0)
                    if mb > 0:
                        _GUAJI_BAND[mb] = int(s.get('lev_r') or 0)
        except Exception as e:
            log('server.log', '!! guaji band load failed: %r' % (e,))
    return _GUAJI_BAND.get(int(mon_id)) or None


def get_mon(mon_id, mon_lev=1, mon_type='normal', scale=1.0):
    """取怪物数值 {hp_max, atk_s, def_s, exp, coin}。

    优先级：config Mon 主表（非空）→ JSTM 兼容模型计算。
    # INFERENCE: JSTMCompatibleMonsterModel, formula UNKNOWN per E1/E2。
    """
    row = _load().get(int(mon_id))
    if row and row.get('hp_max'):   # 真值行（一旦抽到）
        return {k: row.get(k) for k in ('hp_max', 'atk_s', 'def_s', 'exp', 'coin')}
    # JSTM 兼容模型（占位）
    tm = _TYPE_MULT.get(mon_type, 1.0) * max(0.7, min(15.0, float(scale or 1.0)))
    return {
        'hp_max': int(_BASE_HP(mon_lev) * tm),
        'atk_s': int(_BASE_ATK(mon_lev) * tm),
        'def_s': int(_BASE_DEF(mon_lev) * tm),
        'exp': int(_BASE_EXP(mon_lev) * tm),
        'coin': int(_BASE_COIN(mon_lev) * tm),
    }
