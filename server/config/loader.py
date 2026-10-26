# -*- coding: utf-8 -*-
"""config.loader —— 反构造配置表加载（Phase 2 step 1：从 mock_server.py 搬入）。

设计依据：analysis/phase2_design.md §二 config/（kconst/kcfg/kcfg2/四套 cfg 目录）。

迁移来源（mock_server.py 当前行号）：
  _KCONST_CACHE / kconst / kconst_count / kconst_rows / kconst_str / kconst_int
                                  L3249–3379
  _KCFG_FIELDS_CACHE / _kcfg_fields / _kcfg_row / kcfg_best_attr_table
                                  L3382–3459
  _KCFG_CACHE / kcfg / kcfg_rows / kcfg_count
                                  L3693–3723
  _KCFG2_CACHE / kcfg2 / kcfg2_rows
                                  L3774–3800

四套配置目录（均在 server/ 下，逐字同路径）：
  cfg_kconst/   原始常量池（285 个）        → kconst()
  cfg_kconfig/  配置表形态（可按字段取值）   → kcfg()
  cfg_kconfig2/ 散片合并版（按 bid/id 拼行）→ kcfg2()

本模块只依赖标准库 os/json + core.runtime.HERE，无循环 import。
"""

import os
import json

from core import runtime

HERE = runtime.HERE

# 四套配置来源路径（step 0 登记保留；与上述函数用同一 HERE）。
CONFIG_SOURCES = {
    'config.json':   os.path.join(HERE, 'config.json'),
    'cfg_dir':       os.path.join(HERE, 'cfg'),
    'cfg_kconst':    os.path.join(HERE, 'cfg_kconst'),
    'cfg_kconfig':   os.path.join(HERE, 'cfg_kconfig'),
    'cfg_kconfig2':  os.path.join(HERE, 'cfg_kconfig2'),
}


def sources():
    """返回四套配置来源路径（只读登记）。"""
    return dict(CONFIG_SOURCES)


_KCONST_CACHE = {}


def kconst(name):
    """★ R196：读 server/cfg_kconst/<name>.json（R195 dump 出的常量池）。

    ★ 这是一个与 server/cfg 并列的数据源 —— cfg 是"线性解构"结果（拿不到嵌套函数里的数据），
      cfg_kconst 是常量池（285/286 个配置全有数据）。
    ★ 返回 {'proto0': {'kgc': [...], 'knum': [...], 'kstr': [...]}, ...}。
    """
    if name in _KCONST_CACHE:
        return _KCONST_CACHE[name]
    out = {}
    try:
        p = os.path.join(HERE, 'cfg_kconst', name + '.json')
        with open(p, encoding='utf-8') as f:
            out = json.load(f)
    except Exception:
        out = {}
    _KCONST_CACHE[name] = out
    return out


def kconst_count(name):
    """★ R196：该配置的常量池条数 = KGC 的项数（每个 TableConst 即一条配置）。"""
    j = kconst(name)
    best = 0
    for v in (j or {}).values():
        best = max(best, len(v.get('kgc') or []))
    return best


def kconst_rows(name):
    """★ R199：把 cfg_kconst/<name>.json 的行取出来（[(key, row_dict), ...]）。

    ★ 两种形态都支持：
      ① 一个 dict 装 N 行 ⇒ 拆成 N 行
      ② N 个 dict 各装一行（每个 dict 一行）⇒ 用其 hash
    """
    j = kconst(name)
    dicts = []
    for v in (j or {}).values():
        for x in (v.get('kgc') or []):
            if isinstance(x, dict) and (x.get('hash') or x.get('array')):
                dicts.append(x)
    # ★ 形态 ②：多个 dict ⇒ 每个 dict 一行（用它的 hash）
    if len(dicts) >= 3:
        out = []
        for i, d in enumerate(dicts):
            h = d.get('hash') or {}
            if not h:
                continue
            # 若这个 dict 只装"一行"（含字段名），直接用它；否则当"多行"拆开
            has_id = any(k in h for k in ('id', 'bid', 'ID', 'Bid'))
            if has_id or len(h) <= 24:
                out.append((str(h.get('id', h.get('bid', i + 1))), h))
            else:
                out.extend(list(h.items()))
        if out:
            return out
    # ★ 形态 ①：一个 dict 装 N 行
    best = None
    for d in dicts:
        h = d.get('hash') or {}
        if best is None or len(h) > len(best):
            best = h
    return list((best or {}).items())


def kconst_str(row, *names):
    """★ R199：从行里按候选字段名取一个字符串（找不到 ⇒ ''）。"""
    if not isinstance(row, dict):
        return ''
    for nm in names:
        v = row.get(nm)
        if isinstance(v, str) and v:
            return v
    for nm in names:
        v = row.get(nm)
        if v is not None and not isinstance(v, (dict, list)):
            return str(v)
    return ''


def kconst_int(row, *names):
    """★ R199：从行里按候选字段名取一个整数（找不到 ⇒ 0）。"""
    if not isinstance(row, dict):
        return 0
    for nm in names:
        v = row.get(nm)
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str) and v.lstrip('-').isdigit():
            return int(v)
    return 0


_KCFG_FIELDS_CACHE = None


def _kcfg_fields():
    """★ R203：预扫 cfg_kconst 的"主表字段名"（每个配置一个集合）。"""
    global _KCFG_FIELDS_CACHE
    if _KCFG_FIELDS_CACHE is not None:
        return _KCFG_FIELDS_CACHE
    out = {}
    try:
        d = os.path.join(HERE, 'cfg_kconst')
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.json'):
                continue
            try:
                with open(os.path.join(d, fn), encoding='utf-8') as f:
                    j = json.load(f)
            except Exception:
                continue
            best = set()
            for v in (j or {}).values():
                for x in (v.get('kgc') or []):
                    if isinstance(x, dict):
                        h = x.get('hash') or {}
                        if len(h) > len(best):
                            best = set(k for k in h.keys() if isinstance(k, str))
            if best:
                out[fn[:-5]] = best
    except Exception:
        out = {}
    _KCFG_FIELDS_CACHE = out
    return out


def _kcfg_row(name):
    """★ R203：取配置的"主表行"（hash 项最多的那个 dict）—— 用于按字段名取真值。"""
    j = kconst(name)
    best = {}
    for v in (j or {}).values():
        for x in (v.get('kgc') or []):
            if isinstance(x, dict):
                h = x.get('hash') or {}
                if len(h) > len(best):
                    best = h
    return best


def kcfg_best_attr_table(elem_names, min_overlap=8):
    """★ R203：为一组元素字段名找"字段重合 ≥ min_overlap"的配置。

    ★ 返回 (配置名, 行 dict) 或 (None, None)。
    ★★ min_overlap=8 是极高置信度阈值（避免通用词污染 —— 纪律第 42 条）。
    """
    probe = set(x for x in (elem_names or []) if isinstance(x, str))
    if len(probe) < min_overlap:
        return (None, None)
    best = (None, None, 0)
    for cfg, keys in _kcfg_fields().items():
        ov = len(probe & keys)
        if ov > best[2]:
            best = (cfg, keys, ov)
    if best[2] >= min_overlap:
        # ★★ R203b：必须 _row 非空才返回（否则填 1 条全 0 ❌）
        _r = _kcfg_row(best[0])
        if _r:
            # ★ 再确认"行里真的含探针字段"（避免选到"字段名对但行是模板"的配置）
            if len(probe & set(_r.keys())) >= min_overlap:
                # ★★★ R203c：再确认"探针字段的值不全为 0"（主表是字段名清单 ⇒ 值全 0）
                _vals = [_r.get(k) for k in probe]
                _nonzero = sum(1 for v in _vals if isinstance(v, (int, float)) and v)
                if _nonzero * 2 >= len(probe):
                    return (best[0], _r)
    return (None, None)


_KCFG_CACHE = {}


def kcfg(name):
    """★ R222：读 server/cfg_kconfig/<name>.json（"常量池 → 配置表"产物）。

    ★ 形态：{'rows': {id: row}, 'lists': {序号: [...]}}。
    ★ 与 kconst()（原始常量池）的区别：这份是"配置表形态" ⇒ 可直接按字段取值 ✓
    """
    if name in _KCFG_CACHE:
        return _KCFG_CACHE[name]
    out = {}
    try:
        p = os.path.join(HERE, 'cfg_kconfig', name + '.json')
        with open(p, encoding='utf-8') as f:
            out = json.load(f)
    except Exception:
        out = {}
    _KCFG_CACHE[name] = out
    return out


def kcfg_rows(name):
    """★ R222：[(id, row), …]（与 kconst_rows 同形，便于复用）。"""
    j = kcfg(name)
    return list((j.get('rows') or {}).items())


def kcfg_count(name):
    """★ R222：行数。"""
    return len(kcfg(name).get('rows') or {})


_KCFG2_CACHE = {}


def kcfg2(name):
    """★ R237b：读 server/cfg_kconfig2/<name>.json（"散片合并"版）。

    ★ 与 kcfg()（每个 dict 当一行版）的区别：kcfg2 按 bid/id 把散片合并成完整行。
    """
    if name in _KCFG2_CACHE:
        return _KCFG2_CACHE[name]
    out = {}
    try:
        p = os.path.join(HERE, 'cfg_kconfig2', name + '.json')
        with open(p, encoding='utf-8') as f:
            out = json.load(f)
    except Exception:
        out = {}
    _KCFG2_CACHE[name] = out
    return out


def kcfg2_rows(name):
    """★ R237b：[(id, row), …]（跳过 _global）。"""
    j = kcfg2(name)
    return [(k, v) for k, v in (j.get('rows') or {}).items() if k != '_global']
