# -*- coding: utf-8 -*-
"""R224：★ 找"升级/消耗"类专用分支里**写死的数值** —— 看能否用 `kcfg()`/`kconst()` 换成配置真值。

★ 判据：命令 SC/CS 里含 `lev`/`star`/`upgrade`/`cost`/`coin`/`need_*` 等
   ⇒ 该命令多半要"按配置算消耗"⇒ **若实现里是字面量（如 `w_u32(11000)`）⇒ 可疑**。
"""
import importlib.util
import io
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

src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
lines = src.split('\n')

# ① 找"含升级/消耗关键词"的命令
KW = ('upgrade', 'cost', 'need_coin', 'need_gold', 'star', 'lev_up', 'lvlup', 'uplev')
cands = {}
for c in sorted(int(k) for k in sc.keys() if str(k).isdigit()):
    names = set()
    for f in (sc.get(str(c)) or []):
        if isinstance(f, dict):
            names.add(f.get('name'))
            for i in (f.get('items') or []):
                if isinstance(i, dict):
                    names.add(i.get('name'))
    names |= {x.get('name') for x in (cs.get(str(c)) or []) if isinstance(x, dict)}
    hit = {n for n in names if isinstance(n, str) and
           any(k in n.lower() for k in KW)}
    if hit:
        cands[c] = sorted(hit)[:4]
print('  ★ 含"升级/消耗"字段的命令: %d 个' % len(cands))

# ② 对每个，找它的专用分支里"字面量大整数"
sus = []
for c, hit in cands.items():
    m = re.search(r'\n(\s*)(?:el)?if cmd == %d:\n(.*?)(?=\n\s*(?:el)?if cmd|\n\s*else:|\Z)'
                  % c, src, re.S)
    if not m:
        continue
    body = m.group(2)
    if 'kcfg(' in body or 'kconst(' in body or 'cfg(' in body:
        continue                       # ★ 已用配置 ⇒ 跳过
    # ★★ R224b：**排除"命令号本身"**（它们来自 `log(...)`/`pack_frame(cmd, …)`）
    #   第一版没排除 ⇒ 11 个全是假阳性（字面量 = 命令行号）❌
    nums = [x for x in re.findall(r'\b(\d{4,8})\b', body)
            if x not in ('1001', '10001', str(c)) and not x.startswith('1' + str(c)[1:3])]
    nums = [x for x in nums if x != str(c)]
    if nums:
        sus.append((c, hit, nums[:4], src[:m.start()].count('\n') + 1))

print('\n  ★★ **可疑（含升级字段、有专用分支、未用配置、有字面量大数）: %d 个**' % len(sus))
for c, hit, nums, ln in sorted(sus, key=lambda x: -len(x[2]))[:22]:
    print('     cmd=%-6d L%-6d 字段=%s ｜ 字面量=%s' % (c, ln, ','.join(hit), nums))
