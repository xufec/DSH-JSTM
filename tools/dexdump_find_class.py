#!/usr/bin/env python3
"""Find SDK-init call sites and dialog strings in a dexdump -d output.

usage:
  python tools/dexdump_find_class.py <dexdump.txt> SuperPlatform;.init
  python tools/dexdump_find_class.py <dexdump.txt> --strings 初始化失败
"""
import os
import re
import sys


def main():
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'SuperPlatform;.init'
    term = sys.argv[3] if len(sys.argv) > 3 else ''

    cur_class = cur_method = '?'
    pending = None
    hits = 0

    with open(path, encoding='utf-8', errors='replace') as f:
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

            if mode.startswith('--strings'):
                if term and term in line:
                    print('%s -> %s' % (cur_class, cur_method))
                    print('   ', s[:150])
                    hits += 1
            else:
                if mode in line and 'invoke' in line:
                    print('%s -> %s' % (cur_class, cur_method))
                    print('   ', s[:150])
                    hits += 1
            if hits > 12:
                break
    print('hits:', hits)
    return 0


if __name__ == '__main__':
    sys.exit(main())
