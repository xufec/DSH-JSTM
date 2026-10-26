# -*- coding: utf-8 -*-
"""R201b：★ **严格匹配** —— 用**配置的"顶层键"**（`kgc` 里的字符串常量，如 `Config.Function`）
   与**命令 SC 的子表名**逐字比对。

★ 判据（比 R201 的关键词匹配严格得多）：
   · 配置的字符串常量里有 `"Xxx"`（`Config` 前的那个，是**顶层键名**）
   · 命令 SC 的子表名是 `xxx_list` / `xxx` ⇒ **去掉 `_list` 后与 `Xxx` 同名（忽略大小写）**
   ⇒ 才算"匹配" ✓
"""
import importlib.util
import io
import json
import os
import re
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location('g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

D = os.path.join(ROOT, 'server', 'cfg_kconst')
# ① 每个配置的"顶层键名集合"（字符串常量里去掉 Config/常量类名）
cfg_keys = {}
for fn in sorted(os.listdir(D)):
    if not fn.endswith('.json'):
        continue
    name = fn[:-5]
    j = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    ks = set()
    for v in j.values():
        for x in (v.get('kgc') or []):
            if isinstance(x, str) and x and x != 'Config' and len(x) < 40:
                ks.add(x)
    cfg_keys[name] = ks
print('  cfg_kconst: %d 个配置（已提取顶层键）' % len(cfg_keys))

# ② 命令 SC 的子表名 → 归一化
def norm(s):
    s = (s or '').lower()
    for suf in ('_list', 'list', 'data', '_data'):
        if s.endswith(suf) and len(s) > len(suf):
            s = s[:-len(suf)]
    return s

allc = sorted(int(k) for k in sc.keys() if str(k).isdigit())
hits = []
for c in allc:
    for f in (sc.get(str(c)) or []):
        if not isinstance(f, dict) or not f.get('items'):
            continue
        n = norm(f.get('name'))
        if len(n) < 3:
            continue
        for cfg, ks in cfg_keys.items():
            for k in ks:
                if norm(k) == n:
                    hits.append((c, f.get('name'), cfg, k))
print('  ★ 严格匹配：%d 组' % len(hits))

cnt = Counter(h[2] for h in hits)
print('\n  ★ 被最多命令引用的配置 top 24：')
for cfg, n in cnt.most_common(24):
    cmds = sorted({h[0] for h in hits if h[2] == cfg})
    ks = sorted({h[3] for h in hits if h[2] == cfg})
    print('     %-30s %3d 条 ｜ 键=%s ｜ 例: %s' % (cfg, n, ','.join(ks[:3]), cmds[:7]))

# ③ 落盘（供人工确认）
out = os.path.join(ROOT, 'analysis', '1.4.9', '_cfg_match.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for c, fn, cfg, k in hits:
        f.write('%d\t%s\t%s\t%s\n' % (c, fn, cfg, k))
print('\n  ⇒ 已写 %s（%d 行）' % (out, len(hits)))
