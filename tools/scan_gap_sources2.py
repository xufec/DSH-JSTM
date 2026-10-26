# -*- coding: utf-8 -*-
"""R238：★★★ **用 `cfg_kconfig2`（R237 的"完整行"配置）重扫候选数据源**。

★ 与 R234 的 `scan_gap_sources.py` 的区别：**配置源加了 `cfg_kconfig2`**（**245 个完整行**）。
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

GAP = [int(x) for x in
       open(os.path.join(ROOT, 'analysis', '1.4.9', '_generic_mean.txt'),
            encoding='utf-8') if x.strip().isdigit()]
print('  ★ 缺口清单: %d 条' % len(GAP))

con = sqlite3.connect(os.path.join(ROOT, 'server', 'state', 'roles.db'))
DBC = {}
for (t,) in con.execute("select name from sqlite_master where type='table'"):
    try:
        DBC[t] = set(r[1] for r in con.execute('pragma table_info("%s")' % t))
    except Exception:
        pass
con.close()

CFG = {}
for d, mode in (('cfg', 'plain'), ('cfg_kconfig', 'rows'), ('cfg_kconfig2', 'rows')):
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
        src = j if mode == 'plain' else (j.get('rows') or {})
        for k2, v in src.items():
            if isinstance(v, dict):
                ks |= set(v.keys())
        if ks:
            CFG['%s' % fn[:-5]] = CFG.get(fn[:-5], set()) | ks
print('  ★ 配置（合并 cfg+cfg_kconfig+cfg_kconfig2）: %d 个' % len(CFG))


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
print('\n  ★★ **有候选的: %d / %d 条**（**新阈值：配置重合 ≥5**）' % (len(res), len(GAP)))
for c, d, f, n in res[:36]:
    print('     cmd=%-6d 字段 %2d ｜ DB %-16s %2d ｜ 配置 %-26s %2d'
          % (c, n, d[1], d[0], f[1], f[0]))
out = os.path.join(ROOT, 'analysis', '1.4.9', '_gap_sources2.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as fh:
    for c, d, f, n in res:
        fh.write('%d\t%s:%d\t%s:%d\n' % (c, d[1], d[0], f[1], f[0]))
print('\n  ⇒ 已写 %s' % out)
