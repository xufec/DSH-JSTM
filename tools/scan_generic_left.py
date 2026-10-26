# -*- coding: utf-8 -*-
"""R226：★★★ **权威清单：所有"只由通用编码器处理"的命令**。

★ 背景：R189 的 229 条大 tuple 走 `encode_by_sc_with_echo` ⇒ **"空表/0"是"未填真值"**。
   R191–R225 逐条升级了一部分 ⇒ ★★ **本工具列出"剩余"的** ⇒ **那才是"待填真值"的权威清单** ✓

★ 判据：命令号**只出现在"大 tuple"里**（且该 tuple 的 body 调 `encode_by_sc_with_echo`），
   **没有**独立的 `if cmd == N:` 专用分支。
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
s2 = re.sub(r'#[^\n]*', '', src)

# ① 独立专用分支（`if cmd == N:` / `if cmd in (…)` 且 body **不**含 encode_by_sc_with_echo）
own = set()
# ★ R232b：**"有独立分支"就算移出**（不论 body 调什么）——
#   旧判据要求"body 不调 encode_by_sc_with_echo" ⇒ **R232 的 7 条被误判为"通用编码器"** ❌
for m in re.finditer(r'\n(\s*)(?:el)?if cmd == (\d{4,6}):', src):
    own.add(int(m.group(2)))
for m in re.finditer(r'\n(\s*)(?:el)?if cmd in \(([^)]*)\):', src, re.S):
    mem = [int(x) for x in re.findall(r'\b(\d{4,6})\b', m.group(2))]
    # ★ R233b：**用 R189 的"特征串"识别那个通用编码器 tuple** ——
    #   旧判据"成员数 ≥ 50"不可靠（**我的 83 条新 tuple 也被算进去**）❌
    if len(mem) > 150:      # ★ R233c：**R189 的大 tuple 有 229 个成员**（我的最大 83）
        continue                       # ★ 那是 R189 的 229 条大 tuple
    own.update(mem)
# ★ 范围判断
for m in re.finditer(r'if cmd // (\d+) == (\d+):', s2):
    k, n = int(m.group(1)), int(m.group(2))
    for c in range(n * k, n * k + k):
        own.add(c)

# ② 只在"通用编码器 tuple"里的
gen = set()
for m in re.finditer(r'if cmd in \(([^)]*)\):\n(.*?)(?=\n\s*(?:el)?if cmd|\n\s*else:|\Z)',
                     src, re.S):
    if 'encode_by_sc_with_echo' not in m.group(2):
        continue
    for x in re.findall(r'\b(\d{4,6})\b', m.group(1)):
        gen.add(int(x))
print('  ★ 独立专用分支: %d 条' % len(own))
print('  ★ 通用编码器 tuple: %d 条' % len(gen))

rest = sorted(c for c in gen if c not in own)
print('\n  ★★★ **"只由通用编码器处理"（= 待填真值的权威清单）: %d 条**' % len(rest))
print('     %s' % rest[:60])

# ③ 分类：CS+SC（客户端会发）vs 只有 SC
both, sconly = [], []
for c in rest:
    d = set()
    for x in (cs.get(str(c)) or []):
        d.add('cs')
    for x in (sc.get(str(c)) or []):
        d.add('sc')
    (both if 'cs' in d else sconly).append(c)
print('\n  ★ 其中 **CS+SC（客户端会发，优先）: %d 条**' % len(both))
print('     %s' % both[:60])
print('  ★ "只有 SC"（推送型）: %d 条' % len(sconly))

out = os.path.join(ROOT, 'analysis', '1.4.9', '_generic_left.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('通用编码器处理（全部 %d）:\n%s\n\nCS+SC（优先）:\n%s\n'
            % (len(rest), rest, both))
print('\n  ⇒ 已写 %s' % out)
