# -*- coding: utf-8 -*-
"""R233c：★ 用**最可靠**的判据重写 `scan_generic_left.py` 的"专用 vs 通用"分流。

## ★ 判据（不再依赖"成员数阈值"）

对一个命令号 `c`：
   ① 收集**所有**含它的分发点（`if cmd == c:` / `if cmd in (…):` / `if cmd // K == N:`）
   ② **取"位置最后"的那个**（**专用分支都在大 tuple 之后**）
   ③ 若"最后那个"是**大 tuple（成员数最多、且 body 调 `encode_by_sc_with_echo`）**
      ⇒ **未移出**（**仍由通用编码器处理**）
   ④ 否则 ⇒ **已移出** ✓
"""
import importlib.util
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'server', 'mock_server.py')
src = open(P, encoding='utf-8').read()
s2 = re.sub(r'#[^\n]*', '', src)
lines = s2.split('\n')

sp = importlib.util.spec_from_file_location(
    'g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

# ① 收集所有"if cmd in (…)"块：成员 + 是否调编码器 + 规模
blocks = []
i = 0
while i < len(lines):
    ln = lines[i]
    m = re.match(r'^(\s*)if cmd in \((.*)$', ln)
    if m:
        txt = m.group(2)
        j = i
        while '):' not in txt and j < len(lines) - 1:
            j += 1
            txt += ' ' + lines[j]
        head = txt.split('):')[0]
        mem = [int(x) for x in re.findall(r'\b(\d{4,6})\b', head)]
        # body：到下一个同级 `if cmd`（或 40 行）
        body = '\n'.join(lines[i:min(i + 60, len(lines))])
        blocks.append({'ln': i, 'mem': mem, 'echo': 'encode_by_sc_with_echo' in body})
        i = j
    i += 1

# ② 大 tuple = "调编码器"里**成员最多**的那个
echo_blocks = [b for b in blocks if b['echo']]
BIG = max(echo_blocks, key=lambda b: len(b['mem'])) if echo_blocks else None
print('  ★ "通用编码器" tuple: L%d（%d 个成员）' % (BIG['ln'] + 1, len(BIG['mem'])) if BIG else '  （无）')
BIGSET = set(BIG['mem']) if BIG else set()
BIGLN = BIG['ln'] if BIG else -1

# ③ 逐命令：找"最后一个含它的 tuple"
last = {}
own_single = set()
for m in re.finditer(r'if cmd == (\d{4,6}):', s2):
    own_single.add(int(m.group(1)))
for b in blocks:
    for c in b['mem']:
        last[c] = b['ln']

# ④ 分流
both = [int(x) for x in sc.keys() if str(x).isdigit()]
res_big, res_own = [], []
for c in sorted(set(both)):
    if c in own_single:
        res_own.append(c)
        continue
    ln = last.get(c)
    if ln is None:
        res_own.append(c)              # ★ 不在任何 tuple 里 ⇒ 不属"通用编码器"
    elif ln == BIGLN and c in BIGSET:
        res_big.append(c)              # ★ 最后落在"大 tuple" ⇒ 仍由通用编码器处理
    else:
        res_own.append(c)
print('  ★★ **仍由"大 tuple（通用编码器）"处理: %d 条**' % len(res_big))
print('     %s' % res_big[:50])
out = os.path.join(ROOT, 'analysis', '1.4.9', '_generic_mean.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(str(x) for x in res_big) + '\n')
print('  ⇒ 已写 %s' % out)
