# -*- coding: utf-8 -*-
"""R208c：★★ **给门禁 G 补一个盲区检查** —— "专用分支是否被外层 `if cmd in (...)` 筛掉"。

## ★ 发现的盲区（R208）

`11240` 有 `elif cmd == 11240:`，但它的**外层**是
```python
if cmd in (10506, 10517, …, 10592):     # ★ 不含 11240
    …
    elif cmd == 11240:                  # ⇒ 永不执行
```
★ 门禁 G 的静态查**只看"命令号是否出现"** ⇒ **没发现这个问题** ⇒
   实测（`tcp.log`）报 `<< 11240 SC_11240 **兜底响应**` ❌

## ★ 本检查

扫出所有"**elif 所在的外层 `if cmd in (...)` 不含该命令**"的情况。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'server', 'mock_server.py')
lines = open(P, encoding='utf-8').read().split('\n')

# ① 找所有 "if cmd in (…):" 及其 tuple 成员与缩进
#   ★★★ R208f：**还要找"范围判断"**（`if cmd // 100 == N:`）——
#     本工具第一版**漏了它** ⇒ 误报 `107xx` 的 9 条"永不执行"
#     （实际它们由 `if cmd // 100 == 107:` 处理，**我的"修复"反而遮蔽了它们**）
blocks = []
i = 0
while i < len(lines):
    ln = lines[i]
    m = re.match(r'^(\s*)if cmd in \((.*)$', ln)
    if m:
        indent = len(m.group(1))
        # 收集 tuple 文本（可能跨行）
        txt = m.group(2)
        j = i
        while '):' not in txt and j < len(lines) - 1:
            j += 1
            txt += ' ' + lines[j]
        cmds = set(int(x) for x in re.findall(r'\b(\d{4,6})\b', txt.split('):')[0]))
        blocks.append((i, indent, cmds, j))
        i = j
    i += 1
print('  找到 %d 个 `if cmd in (...)` 块' % len(blocks))

#   ★★★ R208f：**范围判断**（`if cmd // 100 == N:` 或 `if cmd // 1000 == N:`）
ranges = []
for i, ln in enumerate(lines):
    m = re.match(r'^(\s*)if cmd // (\d+) == (\d+):', ln)
    if m:
        ranges.append((i, len(m.group(1)), int(m.group(2)), int(m.group(3))))
print('  找到 %d 个"范围判断"（`cmd // K == N`）' % len(ranges))

# ② 找所有 "elif cmd == N:" 并判断其外层块
bad = []
for i, ln in enumerate(lines):
    m = re.match(r'^(\s*)elif cmd == (\d{4,6}):', ln)
    if not m:
        continue
    ind = len(m.group(1))
    cmd = int(m.group(2))
    # 往上找最近的"缩进更小"的 if cmd in 块
    outer = None
    for (bi, bind, bcmds, bj) in blocks:
        if bi < i and bind < ind:
            if outer is None or bi > outer[0]:
                outer = (bi, bind, bcmds, bj)
    # ★★★ R208f：**若外层是"范围判断"覆盖了该命令 ⇒ 不算问题**
    covered = False
    for (ri, rind, k, n) in ranges:
        if ri < i and rind < ind and (cmd // k) == n:
            covered = True
            break
    if covered:
        continue
    if outer and cmd not in outer[2]:
        bad.append((i + 1, cmd, outer[0] + 1, sorted(outer[2])[:6]))

print('\n  ★ 被外层 tuple 筛掉的 `elif`（**永不执行**）: %d 处' % len(bad))
for ln_no, cmd, outer_ln, sample in bad:
    print('     L%-6d `elif cmd == %d` ｜ 外层 L%d 的 tuple 不含它（样例 %s）'
          % (ln_no, cmd, outer_ln, sample))
if not bad:
    print('     （无）✓')
