# -*- coding: utf-8 -*-
"""R234：★★★ **对 130 条"仍由通用编码器处理"的命令，逐条找"确凿数据源"**。

★ 判据（**双重**）：
   ① **SC 的字段名**（含子表元素）∩ **某 DB 表的列名** ≥ 3 ⇒ DB 候选
   ② **SC 的字段名** ∩ **某配置（`cfg`/`cfg_kconfig`）的字段名** ≥ 4 ⇒ 配置候选
★ 输出：**按"重合数"排序的候选表**（不自动改，供逐条确认）。
"""
import importlib.util
import io
import json
import os
import re
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location(
    'g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

# ① 130 条清单
GAP = [int(x) for x in
       open(os.path.join(ROOT, 'analysis', '1.4.9', '_generic_mean.txt'),
            encoding='utf-8') if x.strip().isdigit()]
print('  ★ 缺口清单: %d 条' % len(GAP))

# ② DB 列名
con = sqlite3.connect(os.path.join(ROOT, 'server', 'state', 'roles.db'))
DBC = {}
for (t,) in con.execute("select name from sqlite_master where type='table'"):
    try:
        DBC[t] = set(r[1] for r in con.execute('pragma table_info("%s")' % t))
    except Exception:
        pass
con.close()
print('  ★ DB 表: %d 张' % len(DBC))

# ③ 配置字段名（cfg + cfg_kconfig）
CFG = {}
for d in ('cfg', 'cfg_kconfig'):
    p = os.path.join(ROOT, 'server', d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        if not fn.endswith('.json'):
            continue
        try:
            j = json.load(open(os.path.join(p, fn), encoding='utf-8'))
        except Exception:
            continue
        ks = set()
        for v in (j if d == 'cfg' else (j.get('rows') or {})).values():
            if isinstance(v, dict):
                ks |= set(v.keys())
        if ks:
            CFG[fn[:-5]] = ks
print('  ★ 配置: %d 个' % len(CFG))


def fields_of(cmd):
    names = set()
    for f in (sc.get(str(cmd)) or []):
        if not isinstance(f, dict):
            continue
        names.add(f.get('name'))
        for i in (f.get('items') or []):
            if isinstance(i, dict):
                names.add(i.get('name'))
    return {x for x in names if isinstance(x, str)}


res = []
for c in GAP:
    fns = fields_of(c)
    if not fns:
        continue
    dbh = sorted(((len(fns & cols), t) for t, cols in DBC.items()), reverse=True)
    cfh = sorted(((len(fns & ks), n) for n, ks in CFG.items()), reverse=True)
    d = dbh[0] if dbh and dbh[0][0] >= 3 else (0, '')
    f = cfh[0] if cfh and cfh[0][0] >= 4 else (0, '')
    if d[0] or f[0]:
        res.append((c, d, f, len(fns)))

res.sort(key=lambda x: -(x[1][0] + x[2][0]))
print('\n  ★★ **有候选数据源的: %d / %d 条**' % (len(res), len(GAP)))
for c, d, f, n in res[:40]:
    print('     cmd=%-6d 字段 %2d ｜ DB %-16s 重合 %2d ｜ 配置 %-24s 重合 %2d'
          % (c, n, d[1], d[0], f[1], f[0]))
out = os.path.join(ROOT, 'analysis', '1.4.9', '_gap_sources.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as fh:
    for c, d, f, n in res:
        fh.write('%d\t%s:%d\t%s:%d\n' % (c, d[1], d[0], f[1], f[0]))
print('\n  ⇒ 已写 %s' % out)
