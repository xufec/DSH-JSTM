#!/usr/bin/env python3
"""Print the dexdump disassembly of one class (authoritative, from dexdump -d).

usage:
  python tools/dexdump_class.py com/example/supersdk200/ewan/baidu/MainActivity
  python tools/dexdump_class.py --grep <pattern>     # class names matching
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(ROOT, 'tools', 'dexdump_full.txt')


def main():
    if not os.path.isfile(DUMP):
        print('missing %s (run dexdump first)' % DUMP)
        return 2
    arg = sys.argv[1] if len(sys.argv) > 1 else ''
    if arg == '--grep':
        pat = sys.argv[2]
        with open(DUMP, encoding='utf-8', errors='replace') as f:
            for line in f:
                if 'Class descriptor' in line and pat in line:
                    print(line.strip())
        return 0

    keep = False
    printed = 0
    with open(DUMP, encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'Class descriptor' in line:
                keep = ("'L%s;'" % arg) in line or (arg in line)
                if keep:
                    print('\n===== %s' % line.strip())
                continue
            if keep:
                print(line.rstrip())
                printed += 1
    print('lines printed:', printed)
    return 0


if __name__ == '__main__':
    sys.exit(main())
