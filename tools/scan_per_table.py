# -*- coding: utf-8 -*-
"""R219：★ **按表分组**找"每张有数据的表的最佳同源命令"（含已实现的，看是否真接了 DB）。"""
import importlib.util
import io
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

con = sqlite3.connect(os.path.join(ROOT, 'server', 'state', 'roles.db'))
TABS = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
INFO = {}
for t in TABS:
    try:
        n = con.execute('select count(*) from "%s"' % t).fetchone()[0]
        cols = set(r[1] for r in con.execute('pragma table_info("%s")' % t))
    except Exception:
        continue
    INFO[t] = (n, cols)
con.close()

src = re.sub(r'#[^\n]*', '', open(os.path.join(ROOT, 'server', 'mock_server.py'),
                                  encoding='utf-8').read())
ded = set()
for m in re.finditer(r'if cmd == (\d{4,6}):', src):
    ded.add(int(m.group(1)))
for m in re.finditer(r'if cmd in \(([^)]*)\):', src, re.S):
    for x in re.findall(r'\b(\d{4,6})\b', m.group(1)):
        ded.add(int(x))
for m in re.finditer(r'if cmd // (\d+) == (\d+):', src):
    k, n = int(m.group(1)), int(m.group(2))
    for c in range(n * k, n * k + k):
        ded.add(c)


def field_names(cmd):
    names = set()
    for f in (sc.get(str(cmd)) or []):
        if not isinstance(f, dict):
            continue
        names.add(f.get('name'))
        for i in (f.get('items') or []):
            if isinstance(i, dict):
                names.add(i.get('name'))
    return {x for x in names if isinstance(x, str)}


ALL = {}
for c in (int(k) for k in sc.keys() if str(k).isdigit()):
    ALL[c] = field_names(c)

print('  ★ 每张"有数据的表"的最佳同源命令（重合 ≥2）:')
for t, (n, cols) in sorted(INFO.items(), key=lambda x: -x[1][0]):
    if n <= 0 or not cols:
        continue
    best = []
    for c, fns in ALL.items():
        ov = len(fns & cols)
        if ov >= 2:
            best.append((ov, c))
    best.sort(reverse=True)
    if not best:
        print('  %-18s %2d 行 ｜ （无同源命令）' % (t, n))
        continue
    top = best[:3]
    desc = ' ｜ '.join('cmd=%d(重合%d%s)' % (c, ov, '★已实现' if c in ded else '⚠无分支')
                      for ov, c in top)
    print('  %-18s %2d 行 ｜ %s' % (t, n, desc))
