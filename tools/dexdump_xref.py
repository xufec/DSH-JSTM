#!/usr/bin/env python3
"""List call sites (and the enclosing method) of a DEX method, from dexdump -d.

dexdump's invoke lines include the resolved target, e.g.
    invoke-static {v0}, Lcn/ewan/supersdk/open/SuperPlatform;.init:(...)V // method@1234
so a linear scan with class/method tracking is exact and fast.

usage:
  python tools/dexdump_xref.py SuperPlatform.init
  python tools/dexdump_xref.py --grep "SuperPlatform;.init"
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(ROOT, 'tools', 'dexdump_full.txt')


def main():
    pat = sys.argv[1] if len(sys.argv) > 1 else 'SuperPlatform;.init'
    cur_class = '?'
    cur_method = '?'
    pending = None
    hits = 0
    with open(DUMP, encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'Class descriptor' in line:
                m = re.search(r"'([^']+)'", line)
                if m:
                    cur_class = m.group(1)
            s = line.strip()
            if s.startswith('name') and ':' in s:
                m = re.search(r":\s*'([^']+)'", s)
                if m:
                    pending = m.group(1)
            if '(in ' in line and pending:
                cur_method = pending
            if pat in line and ('invoke' in line):
                print('  %s->%s\n      %s' % (cur_class, cur_method, s[:170]))
                hits += 1
                if hits > 40:
                    break
    print('call sites:', hits)
    return 0


if __name__ == '__main__':
    sys.exit(main())
