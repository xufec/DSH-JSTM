# -*- coding: utf-8 -*-
"""R211：★★ **重扫"真正未实现"的命令**（含"排除推送型"的新判据 = 纪律第 50 条）。

## ★ 判据（四步）

1. **协议有 SC**（客户端期待回包）
2. ★ **不是"CS-only"**（CS-only ⇒ 服务端不该答）
3. ★★ **不在任何专用分支里**（4 种分发形式都要查：
   `if cmd == N:` / `if cmd in (…)` / `if cmd in _VAR:` / **`if cmd // K == N:`**）
4. ★★★ **不是"推送型"**（**没有 `sendall(pack_frame(N, …))`** —— 纪律第 50 条）
"""
import importlib.util
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'server', 'mock_server.py')
src = open(P, encoding='utf-8').read()
s2 = re.sub(r'#[^\n]*', '', src)

# ① 专用分支（4 种形式）
ded = set()
for m in re.finditer(r'if cmd == (\d{4,6}):', s2):
    ded.add(int(m.group(1)))
for m in re.finditer(r'if cmd in \(([^)]*)\):', s2, re.S):
    for x in re.findall(r'\b(\d{4,6})\b', m.group(1)):
        ded.add(int(x))
for m in re.finditer(r'if cmd in (_[A-Za-z0-9_]+):', s2):
    # ★★★ R211d：**支持单行字典**（`_R171 = {12904: (…), 12913: (…)}`）——
    #   第一版正则要求 `\n\}` ⇒ **单行字典匹配不到** ⇒ 误报 33 条 `129xx`
    mm = re.search(re.escape(m.group(1)) + r'\s*=\s*\{(.*?)\}\s*$', s2, re.S | re.M)
    if mm:
        for x in re.findall(r'\b(\d{4,6})\s*:', mm.group(1)):
            ded.add(int(x))
# ★ 范围判断
for m in re.finditer(r'if cmd // (\d+) == (\d+):', s2):
    k, n = int(m.group(1)), int(m.group(2))
    # 该块内的 `if cmd == N` / `elif cmd == N` 已由上面收；范围本身覆盖 [n*k, n*k+k)
    for c in range(n * k, n * k + k):
        ded.add(c)
print('  专用分支（静态查，含范围判断）: %d 条' % len(ded))

# ② 推送型（有 sendall(pack_frame(N, …)) 或 pack_frame(N, …) 被 sendall）
push = set()
for m in re.finditer(r'sendall\(pack_frame\((\d{4,6})', s2):
    push.add(int(m.group(1)))
for m in re.finditer(r'pack_frame\((\d{4,6}),', s2):
    push.add(int(m.group(1)))
print('  ★ 推送型（`pack_frame(N, …)`）: %d 条' % len(push))

# ③ 协议有 CS+SC 的命令
sp = importlib.util.spec_from_file_location(
    'g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

have = {}
for k in cs:
    have.setdefault(str(k), set()).add('cs')
for k in sc:
    have.setdefault(str(k), set()).add('sc')

miss = []
for k, dirs in have.items():
    if not k.isdigit():
        continue
    c = int(k)
    if 'sc' not in dirs:
        continue                       # CS-only ⇒ 不该答
    if c in ded:
        continue                       # 有专用分支
    if c in push:
        continue                       # ★ 推送型（纪律第 50 条）
    miss.append(c)

miss.sort()
print('\n  ★★ **真正未实现**（有 SC、无专用分支、非推送）: %d 条' % len(miss))
print('     %s' % miss[:60])
