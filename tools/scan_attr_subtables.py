# -*- coding: utf-8 -*-
"""R217：★ **扫所有"子表字段与 `role_attr` 同源"的命令** ⇒ `attr_row_bytes` 的复用对象。

★ 判据：SC 的子表元素字段 ∩ (`role_attr` 的列 ∪ `_ATTR_ALIAS` 的键) ≥ 6
   ⇒ 该子表可用 `role_attr` 填（**R204 的 `attr_row_bytes` + R213 的别名表**）。
"""
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

# role_attr 的列 + 别名表的键
con = sqlite3.connect(os.path.join(ROOT, 'server', 'state', 'roles.db'))
COLS = set(r[1] for r in con.execute('pragma table_info("role_attr")'))
con.close()
ALIAS = {'speed', 'def_red_s', 'def_red_p', 'hit_rate', 'crit_rate',
         'tenacity_rate', 'dodge_rate'}
POOL = COLS | ALIAS
print('  role_attr 列 %d 个 + 别名 %d 个' % (len(COLS), len(ALIAS)))

# 已实现的命令
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

cands = []
for c in sorted(int(k) for k in sc.keys() if str(k).isdigit()):
    for f in (sc.get(str(c)) or []):
        if not (isinstance(f, dict) and f.get('items')):
            continue
        en = [i.get('name') for i in f['items'] if isinstance(i, dict)]
        ov = len(set(en) & POOL)
        if ov >= 6:
            cands.append((c, f.get('name'), ov, len(en)))
print('\n  ★ 子表与 `role_attr` 同源（重合 ≥6）: %d 条' % len(cands))
seen = set()
for c, sn, ov, n in sorted(cands, key=lambda x: (-x[2], x[0])):
    if (c, sn) in seen:
        continue
    seen.add((c, sn))
    print('  %-6d %-16s 重合 %2d/%2d ｜ %s' % (c, sn, ov, n,
                                              '★已实现' if c in ded else '（无专用分支）'))
print('  共 %d 组' % len(seen))
