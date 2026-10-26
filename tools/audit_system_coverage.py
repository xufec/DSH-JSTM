# -*- coding: utf-8 -*-
"""系统覆盖矩阵（**只认活代码**）：协议声明的命令 / 服务端真处理的 / 客户端真发过的。

为什么要它（2026-10-17 教训）：
  `mock_server.py` 里有大量**注释掉的旧 if 块**（`# [P3deep-migrated] ...`）。
  用正则扫原文会把注释里的 `if cmd == N` 也当成"已处理" ⇒ 覆盖矩阵全是 ✔（假阳性）。
  本工具全部走 **AST**（只看 `@register(N)` 与真实 `if cmd == N` / `if cmd in (...)`），
  并扫描**整个 server 包**（handler 模块也注册命令，第一版只扫 mock_server 得出过假阴性）。

输出（按系统分组）：
  · `协议`   ：protocol/fields.json 里声明了 CS 的命令数
  · `处理`   ：活代码里显式处理的命令（含 @register）
  · `发过`   ：全部轮转日志里客户端真实发过的次数
  · `未测`   ：协议有 CS、也处理了，但**客户端从来没发过** ⇒ 覆盖空白（下一步的候选）

用法：
    python tools/audit_system_coverage.py
    python tools/audit_system_coverage.py 11200 10500 20000 10600   # 自定义区间起点
"""
import ast
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'server')
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')
RANGES = {'伙伴 112xx': (11200, 11299), '背包 105xx': (10500, 10599),
          '战斗 200xx': (20000, 20099), '魂技 106xx': (10600, 10699),
          '等级/属性 103xx': (10300, 10399), '任务 124xx': (12400, 12499),
          '场景 102xx': (10200, 10299), '账号 101xx/1110': (10100, 10199)}


def live_handlers():
    """扫整个 server 包，返回 (显式处理的命令集, 位置说明)。"""
    live, where = set(), {}
    for dirpath, dirnames, filenames in os.walk(SERVER):
        if 'backup' in dirpath or '__pycache__' in dirpath:
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            p = os.path.join(dirpath, fn)
            try:
                src = open(p, encoding='utf-8', errors='replace').read()
                tree = ast.parse(src)
            except Exception:
                continue
            rel = os.path.relpath(p, ROOT)
            for n in ast.walk(tree):
                if isinstance(n, ast.FunctionDef):
                    for d in n.decorator_list:
                        s = (ast.get_source_segment(src, d) or '').strip()
                        m = re.match(r'register\((\d+)\)', s)
                        if m:
                            c = int(m.group(1)); live.add(c); where.setdefault(c, '%s:%d' % (rel, n.lineno))
                if isinstance(n, ast.Compare):
                    s = (ast.get_source_segment(src, n) or '').strip()
                    mm = re.match(r'^cmd == (\d+)$', s)
                    if mm:
                        c = int(mm.group(1)); live.add(c); where.setdefault(c, '%s:anyif' % rel)
                    elif re.match(r'^cmd in \([\d,\s]+\)$', s):
                        for x in re.findall(r'\d+', s):
                            live.add(int(x)); where.setdefault(int(x), '%s:anyif' % rel)
    return live, where


def sent_counts():
    sent = collections.Counter()
    for p in glob.glob(os.path.join(SERVER, 'logs', 'tcp*.log')):
        for line in open(p, encoding='utf-8', errors='replace'):
            m = re.search(r'>> cmd=(\d+)', line)
            if m:
                sent[int(m.group(1))] += 1
    return sent


def main():
    ranges = dict(RANGES)
    if len(sys.argv) > 1:
        ranges = {}
        for a in sys.argv[1:]:
            lo = int(a)
            ranges['%d-' % lo] = (lo, lo + 99)

    raw = json.load(open(FIELDS, encoding='utf-8'))
    cs_cmds, sc_cmds = set(), set()
    for k, v in raw.items():
        try:
            c = int(v.get('cmd'))
        except Exception:
            continue
        (cs_cmds if (v.get('dir') or '') == 'cs' else sc_cmds).add(c)

    live, where = live_handlers()
    sent = sent_counts()
    print('协议: CS %d 条 / SC %d 条 ｜ 活代码显式处理 %d 条 ｜ 客户端(历史日志)发过 %d 条'
          % (len(cs_cmds), len(sc_cmds), len(live), len(sent)))
    print('⚠ "发过"取自 server/logs/tcp*.log —— **自检工具自己发的命令也在里面**')
    print('  （smoke_systems.py / verify_systems.py 跑过之后，这些命令就不再算"未测"）。')
    for name, (lo, hi) in ranges.items():
        cs = sorted(c for c in cs_cmds if lo <= c <= hi)
        handled = [c for c in cs if c in live]
        sented = [(c, sent[c]) for c in cs if sent.get(c)]
        untested = [c for c in handled if not sent.get(c)]
        print('\n===== %s =====' % name)
        print('  协议 CS %d ｜ 活代码处理 %d ｜ 客户端发过 %d ｜ **未测** %d'
              % (len(cs), len(handled), len(sented), len(untested)))
        if sented:
            print('  客户端发过: ' + ', '.join('%d×%d' % (c, n) for c, n in sorted(sented)))
        nohandle = [c for c in sented if c[0] not in live]
        if nohandle:
            print('  ⚠ 客户端发过但**没在活代码里显式处理**: ' + ', '.join('%d×%d' % (c, n) for c, n in nohandle))
        if untested:
            print('  未测候选(处理了但客户端没发过): ' + ', '.join(map(str, untested[:28]))
                  + (' …' if len(untested) > 28 else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
