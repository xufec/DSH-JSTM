# -*- coding: utf-8 -*-
"""R222：★ **用 `cfg_kconfig`（新救回的配置）找"之前无源"的命令**。

★ 判据：命令 SC 的子表元素字段 ∩ 某 `cfg_kconfig` 配置的"行字段" ≥ 4
   ⇒ 该命令可用这个配置填真值。
★ 并且：**优先"cfg 里没有、kconfig 里有"的那 6 个配置**（`config_fashion_upgrade`/`config_rank`/
   `notice`/`notice7day`/`config_dragon`/`activity_ctrl`）。
"""
import importlib.util
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location(
    'g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

D = os.path.join(ROOT, 'server', 'cfg_kconfig')
CFG = {}
for fn in sorted(os.listdir(D)):
    if not fn.endswith('.json'):
        continue
    name = fn[:-5]
    p1 = os.path.join(ROOT, 'server', 'cfg', fn)
    s1 = os.path.getsize(p1) if os.path.exists(p1) else 0
    if s1 >= 300:
        continue                      # ★ 只看"cfg 里没救回的"
    try:
        j = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    except Exception:
        continue
    keys = set()
    for r in (j.get('rows') or {}).values():
        if isinstance(r, dict):
            keys |= set(r.keys())
    if keys:
        CFG[name] = keys
print('  ★ "cfg 里没救回、kconfig 有数据"的配置: %d 个' % len(CFG))
for n, ks in sorted(CFG.items(), key=lambda x: -len(x[1]))[:10]:
    print('     %-30s %3d 个字段' % (n, len(ks)))

# 已实现
src = re.sub(r'#[^\n]*', '', open(os.path.join(ROOT, 'server', 'mock_server.py'),
                                  encoding='utf-8').read())
ded = set()
for m in re.finditer(r'if cmd == (\d{4,6}):', src):
    ded.add(int(m.group(1)))
for m in re.finditer(r'if cmd in \(([^)]*)\):', src, re.S):
    for x in re.findall(r'\b(\d{4,6})\b', m.group(1)):
        ded.add(int(x))

hits = []
for c in sorted(int(k) for k in sc.keys() if str(k).isdigit()):
    for f in (sc.get(str(c)) or []):
        if not (isinstance(f, dict) and f.get('items')):
            continue
        en = {i.get('name') for i in f['items'] if isinstance(i, dict)}
        for cfg, keys in CFG.items():
            ov = len(en & keys)
            if ov >= 4:
                hits.append((c, f.get('name'), cfg, ov))
print('\n  ★ 同源（重合 ≥4）: %d 组' % len(hits))
for c, sn, cfg, ov in sorted(hits, key=lambda x: -x[3])[:24]:
    print('     cmd=%-6d %-16s ← %-28s 重合 %2d ｜ %s'
          % (c, sn, cfg, ov, '★已实现' if c in ded else '⚠走兜底'))
