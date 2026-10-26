#!/usr/bin/env python3
"""找"客户端发了、服务端没回"的命令（多版本适配的诊断工具）。

用途：1.4.11 / 1.3.0 能进主城但**功能 UI 为空**——多半是它们请求的某些命令
服务端没有应答（客户端拿不到功能开放数据 ⇒ 主界面按钮不生成）。

做法：扫描 tcp.log 尾部一段，按连接内的顺序找 `>> cmd=X` 之后**没有** `<< ... X`
（也没有别的 `<<` 提到该 cmd）的条目。

用法：python tools/find_unanswered.py [--tail 4000]
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
TCP = os.path.join(ROOT, 'server', 'logs', 'tcp.log')

RE_CMD = re.compile(r'>> cmd=(\d+)')
RE_REPLY = re.compile(r'<< .*?(\d{4,5})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tail', type=int, default=4000)
    args = ap.parse_args()

    lines = open(TCP, encoding='utf-8', errors='replace').read().splitlines()[-args.tail:]
    pending = None          # (cmd, lineno)
    sent = collections.Counter()
    replied = collections.Counter()
    unanswered = collections.Counter()
    examples = {}

    for idx, ln in enumerate(lines):
        m = RE_CMD.search(ln)
        if m:
            # 上一条还没等到应答 ⇒ 记为"无应答"
            if pending is not None:
                unanswered[pending[0]] += 1
                examples.setdefault(pending[0], '')
            cmd = int(m.group(1))
            pending = (cmd, ln.strip())
            sent[cmd] += 1
            continue
        r = RE_REPLY.search(ln)
        if r:
            c = int(r.group(1))
            replied[c] += 1
            if pending is not None and pending[0] == c:
                pending = None

    print('扫描 %d 行（尾部）' % len(lines))
    print('%-7s %-6s %-6s %s' % ('cmd', '发出', '应答', '备注'))
    print('-' * 62)
    rows = []
    for c in sorted(sent, key=lambda x: -sent[x]):
        if sent[c] >= 1:
            rows.append((c, sent[c], replied.get(c, 0)))
    for c, s, rp in rows[:28]:
        note = ''
        if rp == 0:
            note = '★ 从未应答'
        elif s > rp:
            note = '应答少于发出（%d/%d）' % (rp, s)
        print('%-7d %-6d %-6d %s' % (c, s, rp, note))


if __name__ == '__main__':
    main()
