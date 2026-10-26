# -*- coding: utf-8 -*-
"""★ 扫描：**协议有 CS+SC、但不在任何专用分支里**的命令（= 仍走"全局兜底"的）。

★ 为什么需要：
   `_GENERIC_DEFAULT_CMDS` 已在 R191 **清零** ⇒ 旧脚本 `scan_unhandled_by_dir.py`
   报"0 条"，但**那只代表"默认集合空了"**，**不代表"没有命令走全局兜底"** ——
   `_reply` 的 **tail** 还有 `global_default_sc` 兜底（R151 的架构）。

★ 本脚本用**门禁 G 同款的静态查**（支持 `if cmd == N:` / `if cmd in (…)` / `if cmd in _VAR:`）。
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'mock_server.py')
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')


def dedicated(src):
    out = set()
    for m in re.finditer(r'if cmd == (\d{4,5}):', src):
        out.add(int(m.group(1)))
    for m in re.finditer(r'if cmd in \(([^)]*)\):', src, re.S):
        for x in re.findall(r'\b(\d{4,5})\b', m.group(1)):
            out.add(int(x))
    for m in re.finditer(r'if cmd in (_[A-Za-z0-9_]+):', src):
        var = m.group(1)
        m2 = re.search(re.escape(var) + r'\s*=\s*\{(.*?)\n\}', src, re.S)
        if m2:
            for x in re.findall(r'\b(\d{4,6})\s*:', m2.group(1)):
                out.add(int(x))
    return out


src = re.sub(r'#[^\n]*', '', open(SRC, encoding='utf-8').read())
ded = dedicated(src)
print('  专用分支（静态查）: %d 条' % len(ded))

d = json.load(open(FIELDS, encoding='utf-8'))
have = {}
for v in d.values():
    if not isinstance(v, dict):
        continue
    try:
        c = int(v.get('cmd'))
    except Exception:
        continue
    have.setdefault(c, set()).add(v.get('dir'))
# 协议里有 CS+SC 的
both = sorted(c for c, dirs in have.items() if 'cs' in dirs and 'sc' in dirs)
miss = [c for c in both if c not in ded]
print('  协议有 CS+SC: %d 条' % len(both))
print('  ★ 仍走全局兜底: %d 条' % len(miss))
print('     %s' % miss[:60])
with open(os.path.join(ROOT, 'analysis', '1.4.9', '_global_fallback.txt'), 'w',
          encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(str(c) for c in miss) + '\n')
print('  ⇒ 已写 analysis/1.4.9/_global_fallback.txt')
