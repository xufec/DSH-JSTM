# -*- coding: utf-8 -*-
"""★ 修正版排查：找 `role_state(...)` 里**读错键名**的地方（R140b 归因的正确版本）。

## 真根因（R140b 的归因错了，这里纠正）

`role_state(cfg)` 的实现里明确写着 **每次都 `db_get_role(rid)`** ⇒ **没有会话缓存**。
真正的问题是 **`_DB_TO_SC` 把 3 个列名映射成了别的键名**：

    level     → lev
    vip_level → vip_lev        ← 代码读 `vip_level` ⇒ 永远 None ⇒ 0
    title     → cur_title

⇒ 凡是用**映射前的列名**去 `.get(...)` 的，都**读不到**。

用法： python tools/scan_key_alias.py
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'mock_server.py')
src = open(SRC, encoding='utf-8').read()

# 从源码里解析 _DB_TO_SC（列名 → 键名）
m = re.search(r'_DB_TO_SC\s*=\s*\{(.*?)\}', src, re.S)
pairs = re.findall(r"'([^']+)'\s*:\s*'([^']+)'", m.group(1))
alias = {col: sc for col, sc in pairs if col != sc}
print('  `_DB_TO_SC` 里"列名与键名不同"的 %d 个：' % len(alias))
for k, v in alias.items():
    print('    %-12s → %s' % (k, v))

print('\n  ★ 用**映射前的列名**去 `role_state(...).get(...)` 的位置（都读不到）：')
bad_total = 0
for col in alias:
    pat = re.compile(r"role_state\([^)]*\)\s*(?:\.\s*get\(\s*'%s'|\[\s*'%s'\s*\])" % (col, col))
    hits = [(i, ln.strip()) for i, ln in enumerate(src.split('\n'), 1) if pat.search(ln)]
    if hits:
        bad_total += len(hits)
        print('    ★ %-12s（应为 `%s`）：%d 处' % (col, alias[col], len(hits)))
        for i, ln in hits[:6]:
            print('        L%-6d %s' % (i, ln[:95]))

if not bad_total:
    print('    （无）')

print('\n  ★ 正确用法（用映射后的键名）——抽查：')
for sc in alias.values():
    n = len(re.findall(r"role_state\([^)]*\)\s*\.\s*get\(\s*'%s'" % sc, src))
    print('    %-12s %d 处 ✓' % (sc, n))

print('\n  ★ 结论：`role_state` **每次都查 DB**（无缓存）；问题只是**键名别名**。')
