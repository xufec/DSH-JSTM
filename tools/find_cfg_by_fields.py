# -*- coding: utf-8 -*-
"""R202：★★ **可靠的"字段名对应"扫描器** —— 给任意命令找配置源。

## ★ 为什么可靠（**纪律第 42 条**）

R201 证明：**基于"名字相似度"的匹配会被通用词污染**（`Item`/`assets`）。
★ 本工具改用**唯一可靠的判据**：
   **命令 SC 的"子表字段名集合" 与 某配置的"主表字段名集合" 的重合数 ≥ 2** ✓
   （**不看配置名、不看命令名** —— 只看**字段名**）

用法： python tools/find_cfg_by_fields.py 13569
       python tools/find_cfg_by_fields.py 13569 16664 16602
"""
import importlib.util
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location('g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

D = os.path.join(ROOT, 'server', 'cfg_kconst')

# ① 预扫：每个配置的"主表字段名集合"（取 hash 项最多的那个 dict 的键）
CFG = {}
for fn in sorted(os.listdir(D)):
    if not fn.endswith('.json'):
        continue
    try:
        j = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    except Exception:
        continue
    best = set()
    for v in j.values():
        for x in (v.get('kgc') or []):
            if isinstance(x, dict):
                h = x.get('hash') or {}
                if len(h) > len(best):
                    best = set(h.keys())
    if best:
        CFG[fn[:-5]] = best
print('  已扫 %d 个配置的主表字段名' % len(CFG))

CMDS = sys.argv[1:] or ['13569']
GENERIC = {'code', 'msg', 'result', 'tips', 'type', 'id', 'bid', 'val', 'num', 'state',
           'status', 'index', 'flag', 'time', 'end_time', 'start_time', 'name', 'lev'}
for c in CMDS:
    fs = sc.get(str(c)) or []
    print('\n' + '=' * 66)
    print('=== %s ===' % c)
    subs = [(f.get('name'), [i.get('name') for i in (f.get('items') or [])])
            for f in fs if isinstance(f, dict) and f.get('items')]
    if not subs:
        print('  （SC 没有子表）')
        continue
    for sname, sfields in subs:
        probe = {x for x in sfields if x not in GENERIC}
        if len(probe) < 2:
            print('  子表 %s: 字段太通用（%s）⇒ 跳过' % (sname, sfields))
            continue
        res = []
        for cfg, keys in CFG.items():
            ov = probe & {k for k in keys if isinstance(k, str)}
            if len(ov) >= 2:
                res.append((len(ov), cfg, sorted(ov)))
        res.sort(reverse=True)
        print('  子表 %s（%d 字段，探针 %d 个）⇒ ★ 候选 %d 个：' % (sname, len(sfields), len(probe), len(res)))
        for n, cfg, ov in res[:6]:
            print('     重合 %d: %-30s %s' % (n, cfg, ov))
