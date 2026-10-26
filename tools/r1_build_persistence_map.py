#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1.3-③：服务端**持久化关联精确化**（把"邻域 ±120 行扫表名"升级为按处理函数体解析）。

## 原口径的问题
上一版对每个命令号，扫其 handler 行**后 120 行**内出现的表名 —— 会**跨函数误捕**
（相邻 handler 的表被算进来）、也会**漏**（函数体超过 120 行）。

## 新口径（三路证据，逐条标来源）
  1. **SQL 文本**：函数体内 `FROM/INTO/UPDATE/TABLE <表>` 的显式表名
  2. **`db_*` 辅助函数**：先建 `db_fn → 表集合` 映射（扫该函数自身函数体），
     再把 handler 里调用的 `db_xxx(...)` 映射成表
  3. **字面量表名实参**：如 `db_row_of('role_ride', ...)` 这种直接把表名当字符串传的

块范围用**缩进**判定：从 handler 行起，到下一个缩进 ≤ handler 缩进的非续行止。
表名白名单取自**真实数据库**（`server/state/roles.db` 的 sqlite_master），不靠猜。
"""
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index')
SRV = os.path.join(ROOT, 'server')
DB = os.path.join(SRV, 'state', 'roles.db')

SQL_RE = re.compile(r'\b(?:FROM|INTO|UPDATE|TABLE|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)', re.I)
DBFN_RE = re.compile(r'\b(db_[a-z_0-9]+)\s*\(')
LIT_RE = re.compile(r"'([a-z_][a-z0-9_]*)'")
DEF_RE = re.compile(r'^(\s*)def\s+(db_[a-z_0-9]+)\s*\(')


def real_tables():
    con = sqlite3.connect(DB)
    ts = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    return ts


def block(lines, start_idx):
    """按缩进取函数体块：从 start_idx 起，到下一个缩进 <= 起始缩进的非空/非续行止。"""
    base = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    out = [lines[start_idx]]
    for i in range(start_idx + 1, len(lines)):
        ln = lines[i]
        if not ln.strip():
            out.append(ln)
            continue
        ind = len(ln) - len(ln.lstrip())
        if ind <= base and not ln.lstrip().startswith(('#', ')', ']', '}')):
            break
        out.append(ln)
    return out


def scan_tables(blob, tables, dbmap):
    """三路证据 → (表集合, 证据明细)。"""
    found = defaultdict(set)
    for m in SQL_RE.finditer(blob):
        t = m.group(1)
        if t in tables:
            found[t].add('sql')
    for m in DBFN_RE.finditer(blob):
        for t in (dbmap.get(m.group(1)) or ()):
            found[t].add('db_fn:' + m.group(1))
    for m in LIT_RE.finditer(blob):
        if m.group(1) in tables:
            found[m.group(1)].add('literal')
    return {k: sorted(v) for k, v in found.items()}


def main():
    tables = real_tables()
    print('真实数据库表: %d' % len(tables))

    src = open(os.path.join(SRV, 'mock_server.py'), encoding='utf-8',
               errors='replace').read().split('\n')
    # 也把各业务包纳入（@register handler 在那里）
    files = {'server/mock_server.py': src}
    for root, dirs, fns in os.walk(SRV):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'logs', 'state', 'backup')]
        for fn in fns:
            if fn.endswith('.py'):
                rel = os.path.relpath(os.path.join(root, fn), ROOT).replace('\\', '/')
                if rel not in files:
                    files[rel] = open(os.path.join(root, fn), encoding='utf-8',
                                      errors='replace').read().split('\n')

    # ── 1) db_fn → 表集合 ──
    dbmap = {}
    for rel, lines in files.items():
        for i, ln in enumerate(lines):
            m = DEF_RE.match(ln)
            if not m:
                continue
            body = '\n'.join(block(lines, i))
            ts = set()
            for mm in SQL_RE.finditer(body):
                if mm.group(1) in tables:
                    ts.add(mm.group(1))
            for mm in LIT_RE.finditer(body):
                if mm.group(1) in tables:
                    ts.add(mm.group(1))
            if ts:
                dbmap.setdefault(m.group(2), set()).update(ts)
    print('db_* 辅助函数 → 表 映射: %d 个' % len(dbmap))

    # ── 2) 逐 handler 精确解析 ──
    sv = json.load(open(os.path.join(OUT, 'R1_服务端处理映射.json'), encoding='utf-8'))
    per_cmd = {}
    ev_kind = Counter()
    for cmd_s, hs in sv['handlers'].items():
        agg = defaultdict(set)
        locs = []
        for h in hs:
            if not h.get('active'):
                continue
            rel = h['file']
            lines = files.get(rel)
            if lines is None or h['line'] - 1 >= len(lines):
                continue
            body = '\n'.join(block(lines, h['line'] - 1))
            t = scan_tables(body, tables, dbmap)
            locs.append({'file': rel, 'line': h['line'], 'block_lines': len(body.split('\n'))})
            for k, v in t.items():
                agg[k].update(v)
        if agg:
            per_cmd[cmd_s] = {k: sorted(v) for k, v in agg.items()}
            for k, v in agg.items():
                for e in v:
                    ev_kind[e.split(':')[0]] += 1

    out = {
        '_meta': {
            'phase': 'R1.3', 'step': '03_persistence_precise',
            'generated_by': 'tools/r1_build_persistence_map.py',
            'method': '按**处理函数体**（缩进判定块范围）解析三路证据：'
                      '①SQL 文本 FROM/INTO/UPDATE/TABLE ②db_* 辅助函数（先建 fn→表 映射）'
                      '③字面量表名实参',
            'improvement_over': '上一版为"handler 行后 120 行"邻域扫描 —— 会跨函数误捕、'
                                '也会因函数体超长而漏',
            'table_whitelist': '取自真实数据库 sqlite_master（%d 张）' % len(tables),
            'evidence_kinds': {'sql': 'SQL 文本里显式出现',
                               'db_fn': '经由 db_* 辅助函数（含函数名）',
                               'literal': '作为字符串字面量传入'},
            'caveat': '仍为**静态**解析：动态拼表名（如 f-string / 变量）无法覆盖，未捕获即未标。',
        },
        'stats': {'cmds_with_persistence': len(per_cmd),
                  'tables_in_db': len(tables),
                  'db_fn_mapped': len(dbmap),
                  'evidence_kind_counts': dict(ev_kind)},
        'db_fn_to_tables': {k: sorted(v) for k, v in sorted(dbmap.items())},
        'by_cmd': per_cmd,
        'by_table': {},
    }
    # 反查：表 → 命令号（按表查业务）
    bt = defaultdict(list)
    for cmd_s, tmap in per_cmd.items():
        for t in tmap:
            bt[t].append(int(cmd_s))
    out['by_table'] = {k: sorted(v) for k, v in sorted(bt.items())}

    p = os.path.join(OUT, 'R1_服务端持久化映射.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('有持久化关联的命令号: %d ｜ 证据分布 %s'
          % (len(per_cmd), dict(ev_kind)))
    print('按表反查覆盖表数: %d' % len(bt))
    print('写出: %s' % p)


if __name__ == '__main__':
    main()
