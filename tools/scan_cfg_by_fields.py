# -*- coding: utf-8 -*-
"""R202b：★ **批量用"字段名对应"扫全部命令** ⇒ 找"配置源可靠"的命令（**可靠判据**）。

★ 判据（**纪律第 42 条**）：命令 SC 的**子表字段名**（**排除通用词**）与某配置的
   **主表字段名** 重合 **≥ 3 个** ⇒ 视为"可靠的配置源" ✓
★ 只输出候选（**不自动改**），供逐条确认。
"""
import importlib.util
import io
import json
import os
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location('g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

D = os.path.join(ROOT, 'server', 'cfg_kconst')
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
        CFG[fn[:-5]] = {k for k in best if isinstance(k, str)}

GENERIC = {'code', 'msg', 'result', 'tips', 'type', 'id', 'bid', 'val', 'num', 'state',
           'status', 'index', 'flag', 'time', 'end_time', 'start_time', 'name', 'lev',
           'sex', 'career', 'rid', 'srv_id', 'power', 'items', 'item_list', 'list',
           'reward', 'reward_list', 'assets', 'item_bid', 'quantity', 'cnt', 'count',
           'value', 'key', 'data', 'info', 'attr', 'attrs', 'star', 'lev_max'}

allc = sorted(int(k) for k in sc.keys() if str(k).isdigit())
hits = []
for c in allc:
    fs = sc.get(str(c)) or []
    for f in fs:
        if not isinstance(f, dict) or not f.get('items'):
            continue
        probe = {i.get('name') for i in f['items'] if i.get('name') not in GENERIC}
        if len(probe) < 3:
            continue
        for cfg, keys in CFG.items():
            ov = probe & keys
            if len(ov) >= 3:
                hits.append((c, f.get('name'), cfg, len(ov), sorted(ov)))

print('  ★ 重合 ≥3 的（命令, 子表, 配置, 重合数）: %d 组' % len(hits))
cnt = Counter(h[2] for h in hits)
print('\n  ★ 被最多命令引用的配置 top 16：')
for cfg, n in cnt.most_common(16):
    cmds = sorted({h[0] for h in hits if h[2] == cfg})
    ovs = sorted({h[4][0] for h in hits if h[2] == cfg})[:4]
    print('     %-30s %3d 条 ｜ 例: %s' % (cfg, n, cmds[:8]))

out = os.path.join(ROOT, 'analysis', '1.4.9', '_cfg_by_fields.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for c, sn, cfg, n, ov in sorted(hits, key=lambda x: -x[3]):
        f.write('%d\t%s\t%s\t%d\t%s\n' % (c, sn, cfg, n, ','.join(ov)))
print('\n  ⇒ 已写 %s（%d 行）' % (out, len(hits)))
