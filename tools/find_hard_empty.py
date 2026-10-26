# -*- coding: utf-8 -*-
"""R206：★ **只找"硬编码的空表"**（排除"条件性空"= 已实现的）。

★ 判据（纪律第 46 条）：
   · **硬编码** ⇒ 形如 `w_u16(0) +  # xxx 空表`（**没有变量**）
   · **条件性空** ⇒ 形如 `build_xxx(ms)` / `encode_xxx(...)`（**有数据源**）⇒ **排除**

★ 输出：**"恒空 + 有注释说明"**的清单（**那才是待填对象**）。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'server', 'mock_server.py')
lines = open(P, encoding='utf-8').read().split('\n')

# ① 找所有"硬编码的空表"
hard = []
for i, ln in enumerate(lines, 1):
    st = ln.strip()
    if not st.startswith('w_u16(0)'):
        continue
    # 注释里的"表名"线索
    m = re.search(r'#\s*(.+)$', ln)
    note = m.group(1).strip() if m else ''
    if not note:
        # 看下一行是否也是 w_u16(0)
        nxt = lines[i].strip() if i < len(lines) else ''
        note = ('连续空表' if nxt.startswith('w_u16(0)') else '')
    hard.append((i, note, ln.strip()[:70]))

print('  ★ 硬编码空表（`w_u16(0)` 起头）: %d 处' % len(hard))
from collections import Counter
kw = Counter()
for i, note, s in hard:
    for k in ('attr', 'list', 'item', 'skill', 'record', 'rank', 'mission', 'box',
              'reward', 'role', 'hero', 'mon', 'guild', 'shop', 'charge', 'sign'):
        if k in note.lower():
            kw[k] += 1
print('  ★ 注释里的关键词统计: %s' % dict(kw.most_common(12)))

# ② 找"附近的 cmd"（往上找最近的 `if cmd ...`）
def near_cmd(idx):
    for j in range(idx - 1, max(0, idx - 120), -1):
        m = re.search(r'if cmd (?:==|in) \(?([\d,\s]+)', lines[j - 1])
        if m:
            return m.group(1).strip()[:40]
    return '?'

print('\n  ★ 硬编码空表清单（行号 / 所属命令 / 注释）:')
out = os.path.join(ROOT, 'analysis', '1.4.9', '_hard_empty.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for i, note, s in hard:
        c = near_cmd(i)
        f.write('%d\t%s\t%s\t%s\n' % (i, c, note, s))
        if i % 1 == 0 and len([x for x in hard if x[0] < i]) < 40:
            print('     L%-6d cmd=%-22s %s' % (i, c, note[:60]))
print('\n  ⇒ 已写 %s（%d 行）' % (out, len(hard)))
