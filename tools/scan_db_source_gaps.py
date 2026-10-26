# -*- coding: utf-8 -*-
"""R218：★★ **"同源子表"扫描（通用版）** —— 对 DB 的每张"实体表"找"同源命令"，
   并标出**"无专用分支"**的缺口。

★ 表清单：`bag_items` / `equip_items` / `role_attr` / `role_heros` / `role_wing` /
   `role_shenqi` / `role_mingge` / `role_ride` / `role_chair` / `role_build` / `missions`
★ 判据：SC 子表/顶层字段 ∩ 表列名 ≥ 3 ⇒ "同源"；再标"有无专用分支"。
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

con = sqlite3.connect(os.path.join(ROOT, 'server', 'state', 'roles.db'))
TABLES = ['bag_items', 'equip_items', 'role_attr', 'role_heros', 'role_wing',
          'role_shenqi', 'role_mingge', 'role_ride', 'role_chair', 'role_build',
          'missions', 'role_assets', 'role_runes', 'role_fabao', 'role_tree']
COLS = {}
for t in TABLES:
    try:
        COLS[t] = set(r[1] for r in con.execute('pragma table_info("%s")' % t))
    except Exception:
        pass
con.close()
print('  可用表: %s' % ', '.join(sorted(COLS)))

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

# ★ 每个命令：收集"所有子表元素字段 ∪ 顶层标量字段名"
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

gaps = []
allc = sorted(int(k) for k in sc.keys() if str(k).isdigit())
for c in allc:
    fns = field_names(c)
    for t, cols in COLS.items():
        if not cols:
            continue
        ov = len(fns & cols)
        if ov >= 3:
            gaps.append((c, t, ov, c in ded))

# ★ 只列"无专用分支"的（缺口）
miss = [x for x in gaps if not x[3]]
print('\n  ★★ **"同源但无专用分支"的缺口: %d 组**' % len(miss))
for c, t, ov, _ in sorted(miss, key=lambda x: (-x[2], x[0]))[:30]:
    print('     cmd=%-6d ← %-14s 重合 %2d ｜ %s'
          % (c, t, ov, '★ 走兜底' if c not in ded else ''))
print('  （有专用分支的同源命令: %d 组）' % (len(gaps) - len(miss)))
