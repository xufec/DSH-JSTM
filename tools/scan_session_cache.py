# -*- coding: utf-8 -*-
"""★ 系统性复查"**会话缓存**"问题（R140 发现的 bug 类）。

## 背景

R140 发现：`16704`/`16706` 用 `role_state(self.cfg).get('vip_level')` 读 VIP，
而**那是会话开始时装载的配置** ⇒ DB 改了它**读不到**（实测 DB=3 却读成 0）。

## 本脚本做什么

1. 从 `roles` 表列出所有列（那些都是**玩家状态**）
2. 扫服务端所有 `role_state(...).get('X')` / `role_state(...)['X']` 用法
3. 标出 **X 是 `roles` 的列** 的那些位置 ⇒ **这些都有"会话缓存"风险**
4. 同时列出**正确做法**（从 DB 直读）的现有辅助，便于改

用法： python tools/scan_session_cache.py
"""
import io
import os
import re
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
SRC = os.path.join(ROOT, 'server', 'mock_server.py')

con = sqlite3.connect(DB)
cols = [r[1] for r in con.execute('PRAGMA table_info(roles)')]
con.close()
print('  `roles` 表共 %d 列（这些都是**玩家状态**）：' % len(cols))
print('    %s\n' % ', '.join(cols))

src = open(SRC, encoding='utf-8').read()
lines = src.split('\n')

# 扫 `role_state(...) . get('X')` 与 `role_state(...)[ 'X' ]`
pat = re.compile(r"role_state\([^)]*\)\s*\.\s*get\(\s*'([^']+)'")
pat2 = re.compile(r"role_state\([^)]*\)\s*\[\s*'([^']+)'\s*\]")
hits = {}
for i, ln in enumerate(lines, 1):
    for m in pat.finditer(ln):
        hits.setdefault(m.group(1), []).append(i)
    for m in pat2.finditer(ln):
        hits.setdefault(m.group(1), []).append(i)

risk = [(k, v) for k, v in hits.items() if k in cols]
safe = [(k, v) for k, v in hits.items() if k not in cols]

print('  ★ **有会话缓存风险**的键（在 `roles` 列里，却从 `role_state` 读）：%d 个' % len(risk))
for k, v in sorted(risk, key=lambda x: -len(x[1])):
    print('    %-16s 用了 %2d 处  行号: %s' % (k, len(v), ','.join(map(str, v[:12]))))

print('\n  其它键（不在 `roles` 列里，可能是会话常量）：%d 个' % len(safe))
for k, v in sorted(safe, key=lambda x: -len(x[1]))[:14]:
    print('    %-16s 用了 %2d 处' % (k, len(v)))

print('\n  ★ 已有的"从 DB 直读"辅助（可复用的模式）：')
for m in re.finditer(r'def (db_\w+)\(', src):
    n = m.group(1)
    if any(x in n for x in ('vip', 'lev', 'asset', 'state', 'list', '_get')):
        print('    %s()' % n)
