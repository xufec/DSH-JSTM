# -*- coding: utf-8 -*-
"""R203：★★ **分析门禁 E 登记的"空表"清单** —— 那是"待填真值"的权威清单。

★ `tools/_emitted_empty_allow.json` 有 435 条"已登记的空表理由"。
  ★★ 每一条都是**一个"专用分支里返回空表"的子表** ⇒ **那正是"逐条取证"的对象** ✓

★ 本脚本：
   ① 统计"哪些命令"的空表最多
   ② 对每个命令，用 `find_cfg_by_fields` 的判据找"可能的配置源"
   ③ 输出**待办清单**（按"命令的空表数"排序）
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

AL = json.load(open(os.path.join(ROOT, 'tools', '_emitted_empty_allow.json'), encoding='utf-8'))
allow = AL.get('allow') or {}
print('  门禁 E 登记的空表: %d 条' % len(allow))

by_cmd = Counter()
for k in allow:
    cmd = k.split(':')[0]
    by_cmd[cmd] += 1
print('  涉及 %d 个命令' % len(by_cmd))
print('\n  ★ 空表最多的命令 top 24：')
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
           'value', 'key', 'data', 'info', 'attr', 'attrs', 'star'}

todo = []
for cmd, n in by_cmd.most_common(24):
    fields = [k.split(':', 1)[1] for k in allow if k.split(':')[0] == cmd]
    # 找候选配置源
    cands = []
    for f in (sc.get(cmd) or []):
        if not isinstance(f, dict) or not f.get('items'):
            continue
        probe = {i.get('name') for i in f['items'] if i.get('name') not in GENERIC}
        if len(probe) < 2:
            continue
        for cfg, keys in CFG.items():
            ov = probe & keys
            if len(ov) >= 2:
                cands.append((len(ov), cfg, f.get('name'), sorted(ov)))
    cands.sort(reverse=True)
    print('  %-6s 空表 %d 个: %-44s ｜ 候选: %s'
          % (cmd, n, ','.join(fields)[:44],
             ('%s(%d, %s)' % (cands[0][1], cands[0][0], ','.join(cands[0][3][:3]))) if cands else '—'))
    todo.append((cmd, n, fields, cands[:2]))

out = os.path.join(ROOT, 'analysis', '1.4.9', '_empty_todo.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for cmd, n, fields, cands in todo:
        f.write('%s\t%d\t%s\t%s\n' % (cmd, n, ','.join(fields),
                                      ';'.join('%s:%d' % (c[1], c[0]) for c in cands)))
print('\n  ⇒ 已写 %s' % out)
