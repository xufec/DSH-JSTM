# -*- coding: utf-8 -*-
"""attribute.service —— 24 项属性汇总 + role_attr 表读写（Phase 2 step 3）。

设计依据：phase2_design.md §二 attribute/、§4.2 AttributeService。
迁移来源（mock_server.py 当前行号）：
  ATTR_KEYS                    L46–50
  role_attr_dict               L63–86（统一属性汇总入口，AttributeService 雏形）
  role_power                   L89–96
  attr_table_10304/10306       L106–127
  db_role_attr                 L3475–3490
  ATTR_FIELDS / ATTR_DEFAULTS / _ATTR_COL_SET   L5126–5148
  db_get_attr / db_save_attr   L4923–4958

★ 注意：原文件里 ATTR_DEFAULTS 有两次赋值（L52 hp_max=3000、L5137 hp_max=1000），
  模块加载后生效的是**后者**（同名覆盖）。本文件只保留生效版本（hp_max=1000），
  role_attr_dict 与 build_10303 运行时看到的都是它 —— 与拆分前字节一致。
"""

import os
import sqlite3
import time

from core import runtime
from persistence.db import db_conn, db_release, DB_PATH
from protocol.frame import w_u16, w_u32, w_str
from protocol.fields import _sc_fields, _sc_w

log = runtime.log

# ★ R213：SC 子表字段名 → role_attr 列名别名表（从 mock_server L3679 逐字下沉）
_ATTR_ALIAS = {
    'speed': 'atk_speed',
    'def_red_s': 'red_def_s',
    'def_red_p': 'red_def_p',
    'hit_rate': 'hit_rate_show',
    'crit_rate': 'crit_rate_show',
    'tenacity_rate': 'tenacity_rate_show',
    'dodge_rate': 'dodge_rate_show',
}


def attr_row_bytes(cmd, field_name, row, rid=1001):
    """★ R204：按 SC 的 field_name 子表字段顺序，用 row 同名字段生成 1 条。
    [P3deep-migrated 从 mock_server L3691 逐字下沉]"""
    for f in _sc_fields(cmd):
        if not (isinstance(f, dict) and f.get('name') == field_name):
            continue
        its = f.get('items') or []
        if not its:
            return w_u16(0)
        if not row:
            return w_u16(0)
        o = w_u16(1)
        for x in its:
            if not isinstance(x, dict):
                continue
            nm = x.get('name') or ''
            tp = (x.get('type') or '').lower()
            if x.get('items'):
                o += w_u16(0)
                continue
            v = row.get(nm)
            if v is None:
                _al = _ATTR_ALIAS.get(nm)
                if _al:
                    v = row.get(_al)
            if tp.startswith('string'):
                o += w_str(v if isinstance(v, str) else '')
                continue
            w = _sc_w(tp)
            try:
                v = int(v or 0)
            except Exception:
                v = 0
            o += (v & ((1 << (w * 8)) - 1)).to_bytes(w if w > 0 else 1, 'big')
        return o
    return w_u16(0)

# 10304/10306 的 24 项属性键顺序（来自 SC_10304 定义）
ATTR_KEYS = ['strength', 'intellect', 'armor', 'constiution', 'atk_s', 'atk_p',
             'def_s', 'def_p', 'hp_max', 'atk_speed', 'hit', 'dodge',
             'crit', 'tenacity', 'red_def_s', 'red_def_p',
             'atk_abs', 'def_abs', 'reduce', 'hurt', 'hit_rate_show',
             'dodge_rate_show', 'crit_rate_show', 'tenacity_rate_show']

# attr 里可配置的默认值（生效版 = 原 L5137；hp_max=1000）
ATTR_DEFAULTS = {
    'strength': 10, 'intellect': 10, 'armor': 10, 'constiution': 10,
    'atk_s': 100, 'atk_p': 100, 'def_s': 80, 'def_p': 80,
    'hp_max': 1000, 'atk_speed': 100, 'hit': 50, 'dodge': 50,
    'crit': 30, 'tenacity': 30, 'red_def_s': 0, 'red_def_p': 0,
    'atk_abs': 0, 'def_abs': 0, 'reduce': 0, 'hurt': 0,
    'hit_rate_show': 0, 'dodge_rate_show': 0,
    'crit_rate_show': 0, 'tenacity_rate_show': 0,
}

# SC_10303 的 attr 大表字段顺序
ATTR_FIELDS = [
    ('strength', 'u16'), ('intellect', 'u16'), ('armor', 'u16'), ('constiution', 'u16'),
    ('atk_s', 'u32'), ('atk_p', 'u32'), ('def_s', 'u32'), ('def_p', 'u32'),
    ('hp_max', 'u32'), ('atk_speed', 'u32'), ('hit', 'u32'), ('dodge', 'u32'),
    ('crit', 'u32'), ('tenacity', 'u32'), ('red_def_s', 'u32'), ('red_def_p', 'u32'),
    ('atk_abs', 'u32'), ('def_abs', 'u32'), ('reduce', 'u32'), ('hurt', 'u32'),
    ('hit_rate_show', 'u32'), ('dodge_rate_show', 'u32'),
    ('crit_rate_show', 'u32'), ('tenacity_rate_show', 'u32'),
]

_ATTR_COL_SET = {name for name, _ in ATTR_FIELDS}

# 软依赖原版权重模块 server/power.py（与现状一致）
try:
    import power as power_mod
except Exception:
    power_mod = None


def db_role_attr(rid):
    """★ R204：读 role_attr 表首行为 dict（玩家属性面板真值来源）。None 忠实呈现。"""
    try:
        con = db_conn()
        cur = con.execute('SELECT * FROM role_attr WHERE rid=? LIMIT 1', (int(rid),))
        row = cur.fetchone()
        if not row:
            return {}
        cols = [d[0] for d in (cur.description or [])]
        return dict(zip(cols, row))
    except Exception:
        return {}


def role_attr_dict(cfg):
    """角色属性字典 —— ★ PHASE 2.10：**统一属性汇总入口（AttributeService 雏形）**。

    优先级：`ATTR_DEFAULTS` < `cfg['role_attrs']` < **DB `role_attr`（按 rid）**。

    ★ 修复的**真实不一致**（本轮发现）：此前本函数**只读 cfg** ⇒
      `10304`/`10306`（角色面板 + 战力）用的是**缺省值**，
      而 `10947`/`10601` 读 `role_attr` 表 ⇒ **同一角色两套属性**（面板与详情对不上）。
    ★ DB 只覆盖「**非 None** 且 **在 ATTR 键集内**」的列（与 `role_state` 同纪律），
      绝不把缺省值抹成 0。
    ★ 成长系统（时装/光环/…）**以后**只需把加成写进 `role_attr` 或在此累加，
      即可**一次性**影响面板与战力 —— 这就是"禁止各系统自算属性"的收敛点。
    """
    a = dict(ATTR_DEFAULTS)
    a.update(dict(cfg.get('role_attrs') or {}))
    try:
        _rid = (cfg.get('role') or {}).get('rid')
        if _rid:
            for _k, _v in (db_role_attr(_rid) or {}).items():
                if _v is not None and _k in a:
                    a[_k] = _v
    except Exception as _e:
        log('tcp.log', '  !! role_attr_dict 合并 DB 失败: %r' % (_e,))
    # practice_exp dynamic: read xiulian progress (bid=10822 exp, same src as 10621 skill_list)
    # DB role_attr.practice_exp=0 overrides default => read config skills real progress.
    try:
        for _sk in (cfg.get("skills") or []):
            if int(_sk.get("bid", 0)) == 10822:
                a["practice_exp"] = int(_sk.get("exp", 0))
                break
    except Exception:
        pass
    return a



def role_power(cfg):
    """角色总战力（与 SC_10304.power 同一算法，供 12901 战力榜复用）。"""
    a = role_attr_dict(cfg)
    if power_mod is not None:
        return int(power_mod.calc_power(a))
    return int(sum(a.get(k, 0) * x for k, x in {
        'atk_s': 0.5, 'atk_p': 0.5, 'def_s': 0.3, 'def_p': 0.3, 'hp_max': 0.02,
        'dodge': 1, 'hit': 1, 'crit': 1, 'tenacity': 1, 'atk_speed': 2}.items()))


def attr_table_10304(ad):
    """SC_10304 的 attr 表：4×u16 + 20×u32。"""
    out = w_u16(1)
    for k in ATTR_KEYS[:4]:
        out += w_u16(int(ad.get(k, 0)) & 0xffff)
    for k in ATTR_KEYS[4:]:
        out += w_u32(int(ad.get(k, 0)) & 0xffffffff)
    return out


def attr_table_10306(ad):
    """SC_10306 的 attr 表：4×u16 + 12×u32 + 4×u16 + 4×u32（尾段不是全 u32）。"""
    out = w_u16(1)
    for k in ATTR_KEYS[0:4]:
        out += w_u16(int(ad.get(k, 0)) & 0xffff)
    for k in ATTR_KEYS[4:16]:
        out += w_u32(int(ad.get(k, 0)) & 0xffffffff)
    for k in ATTR_KEYS[16:20]:
        out += w_u16(int(ad.get(k, 0)) & 0xffff)
    for k in ATTR_KEYS[20:24]:
        out += w_u32(int(ad.get(k, 0)) & 0xffffffff)
    return out


def db_get_attr(rid):
    """读属性行；不存在返回 None。"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT * FROM role_attr WHERE rid=?', (rid,)).fetchone()
        db_release(con)
        if not row:
            return None
        d = dict(row)
        d.pop('rid', None)
        d.pop('updated_at', None)
        return {k: v for k, v in d.items() if v is not None}
    except Exception as e:
        log('tcp.log', '  !! db_get_attr failed: %r' % (e,))
        return None


def apply_delta(rid, delta):
    """★ Phase 8：按属性名**增量**叠加到 role_attr（成长/伙伴/技能属性贡献统一入口）。

    delta = {'atk_s': +5, 'hp_max': +100, ...}；只落 _ATTR_COL_SET 内的键。
    写后 get_attr_dict 即可见；配合 power.service.power_of(rid) 重算战力。
    """
    cur = db_get_attr(rid) or {}
    changed = {}
    for k, v in (delta or {}).items():
        if k in _ATTR_COL_SET:
            changed[k] = int(cur.get(k) or 0) + int(v)
    if not changed:
        return False
    return db_save_attr(rid, changed)


def db_save_attr(rid, attr):
    """按协议字段名增量保存属性。"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO role_attr (rid) VALUES (?)', (rid,))
        cols = [c for c in attr if c in _ATTR_COL_SET]
        if cols:
            vals = [attr[c] for c in cols]
            con.execute('UPDATE role_attr SET %s, updated_at=? WHERE rid=?' %
                        ','.join('%s=?' % c for c in cols),
                        vals + [int(time.time()), rid])
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_save_attr failed: %r' % (e,))
        return False
