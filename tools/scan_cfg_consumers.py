# -*- coding: utf-8 -*-
"""R241：★★★ **"配置 → 消费命令"反查** —— 对 `cfg_kconfig2` 的 245 个配置，
   找"SC 有 ≥4 个字段与它重合"的命令（**不限缺口清单**）。

★ 输出三分类：
   ① **命令已成专用分支，且已调 `kcfg2`/`kcfg`/`cfg`** ⇒ ✅ 已接
   ② **命令已成专用分支，但没调配置** ⇒ ⚠ **可能有更真值的配置可接**
   ③ **命令仍由大 tuple 处理，且有配置重合** ⇒ ★ **候选**（**下一批**）
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

# ① 配置字段
CFG = {}
D = os.path.join(ROOT, 'server', 'cfg_kconfig2')
for fn in os.listdir(D):
    if not fn.endswith('.json'):
        continue
    try:
        j = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    except Exception:
        continue
    ks = set()
    for k, v in (j.get('rows') or {}).items():
        if isinstance(v, dict):
            ks |= set(v.keys())
    if ks:
        CFG[fn[:-5]] = ks
print('  ★ cfg_kconfig2 配置: %d 个' % len(CFG))

# ② 源码：大 tuple 成员 / 各命令 body 是否调配置
src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
s2 = re.sub(r'#[^\n]*', '', src)
lines = s2.split('\n')
# ★ R241b：**"大 tuple" = "成员最多的那个含编码器的 tuple"**（不用固定阈值 —— 纪律第 73 条）
blocks = []
for i, ln in enumerate(lines):
    if re.match(r'^\s*if cmd in \(', ln):
        txt = ln
        j = i
        while '):' not in txt and j < len(lines) - 1:
            j += 1
            txt += ' ' + lines[j]
        head = txt.split('):')[0]
        mem = [int(x) for x in re.findall(r'\b(\d{4,6})\b', head)]
        body = '\n'.join(lines[i:min(i + 80, len(lines))])
        blocks.append({'ln': i, 'mem': mem, 'echo': 'encode_by_sc_with_echo' in body})
_echo = [b for b in blocks if b['echo']]
BIGBLK = max(_echo, key=lambda b: len(b['mem'])) if _echo else None
BIG = set(BIGBLK['mem']) if BIGBLK else set()
_big_ln = BIGBLK['ln'] if BIGBLK else -1
# ★ 只有"最后一个含它的 tuple"是那个大 tuple ⇒ 才算"仍由大 tuple 处理"
_last = {}
for b in blocks:
    for c in b['mem']:
        _last[c] = b['ln']
BIG = {c for c in BIG if _last.get(c) == _big_ln}
print('  ★ 大 tuple: L%d（%d 个成员）｜ **仍由它处理: %d 个**'
      % (_big_ln + 1, len(BIGBLK['mem']) if BIGBLK else 0, len(BIG)))

# ③ 各专用分支的 body（粗粒度：到下一个同级 if）
BODY = {}
for m in re.finditer(r'\n(\s*)(?:el)?if cmd (?:== (\d{4,6})|in \(([^)]*)\)):', s2):
    cmds = [int(m.group(2))] if m.group(2) else [
        int(x) for x in re.findall(r'\b(\d{4,6})\b', m.group(3) or '')]
    body = s2[m.end():m.end() + 2500]
    for c in cmds:
        BODY.setdefault(c, '')
        BODY[c] += body[:1500]
print('  ★ 有独立分支的命令: %d 个' % len(BODY))


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


ALL = sorted(int(k) for k in sc.keys() if str(k).isdigit())
res = []
for c in ALL:
    fns = fields_of(c)
    if not fns:
        continue
    best = sorted(((len(fns & ks), n) for n, ks in CFG.items()), reverse=True)
    if not best or best[0][0] < 4:
        continue
    ov, cfgname = best[0]
    body = BODY.get(c, '')
    if c in BIG:
        tag = '③ 大tuple'
    elif any(w in body for w in ('kcfg2(', 'kcfg(', 'cfg(', 'kcfg2_rows(', 'kconst(')):
        tag = '✅ 已接配置'
    else:
        tag = '⚠ 有分支未接配置'
    res.append((tag, c, cfgname, ov))

from collections import Counter
print('\n  ★ 分类统计: %s' % dict(Counter(x[0] for x in res)))
for tag in ('③ 大tuple', '⚠ 有分支未接配置'):
    sel = [x for x in res if x[0] == tag]
    sel.sort(key=lambda x: -x[3])
    print('\n  ★★ **%s（%d 条）前 30**：' % (tag, len(sel)))
    for _, c, cfgname, ov in sel[:30]:
        print('     cmd=%-6d ← %-30s 重合 %2d' % (c, cfgname, ov))
