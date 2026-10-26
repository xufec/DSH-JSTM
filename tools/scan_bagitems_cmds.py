# -*- coding: utf-8 -*-
"""R210：★ **扫所有"SC 里有 `items` 类子表"的命令** ⇒ 找 `bag_items_bytes` 的复用对象。

★ 判据：SC 的子表元素字段与 `bag_items` 的列（`item_id`/`bid`/`pos`/`quantity`/`ctime`）
   重合 ≥ 5，且命令号带 `uniq_id`/`item_id`/`item_bid` 的查询键。
"""
import importlib.util
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location('g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

# bag_items 的列
COLS = {'id', 'item_id', 'bid', 'pos', 'quantity', 'ctime', 'hero_bid', 'bind',
        'intensify_lev', 'expire_ts', 'durable', 'object', 'attrs_ext'}

src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
s2 = re.sub(r'#[^\n]*', '', src)
# 已在专用分支里的命令
ded = set()
for m in re.finditer(r'if cmd == (\d{4,6}):', s2):
    ded.add(int(m.group(1)))
for m in re.finditer(r'if cmd in \(([^)]*)\):', s2, re.S):
    for x in re.findall(r'\b(\d{4,6})\b', m.group(1)):
        ded.add(int(x))
for m in re.finditer(r'if cmd // (\d+) == (\d+):', s2):
    k, n = int(m.group(1)), int(m.group(2))
    pass

cands = []
for c in sorted(int(k) for k in sc.keys() if str(k).isdigit()):
    fs = sc.get(str(c)) or []
    keys = [x.get('name') for x in (cs.get(str(c)) or []) if isinstance(x, dict)]
    for f in fs:
        if not (isinstance(f, dict) and f.get('items')):
            continue
        en = [i.get('name') for i in f['items'] if isinstance(i, dict)]
        ov = len(set(en) & COLS)
        if ov >= 5:
            cands.append((c, f.get('name'), ov, keys))

print('  ★ 子表与 `bag_items` 列重合 ≥5 的命令: %d 条' % len(cands))
seen = set()
for c, sn, ov, keys in sorted(cands, key=lambda x: -x[2]):
    if c in seen:
        continue
    seen.add(c)
    flag = '★已实现' if c in ded else '（无专用分支）'
    print('  %-6d %-16s 重合 %2d ｜ CS=%s ｜ %s' % (c, sn, ov, keys[:4], flag))
print('  共 %d 条（去重）' % len(seen))
