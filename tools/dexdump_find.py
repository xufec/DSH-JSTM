#!/usr/bin/env python3
"""Search dexdump output for a string and report the owning class/method.

dexdump (Android SDK build-tools) gives authoritative disassembly; we scan it
linearly and backtrack to the nearest `Class descriptor` / `name` markers.

usage:
  python tools/dexdump_find.py 初始化失败
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(ROOT, 'tools', 'dexdump_full.txt')


def main():
    term = sys.argv[1] if len(sys.argv) > 1 else '初始化失败'
    tb = term.encode('utf-8')
    cur_class = '?'
    cur_method = '?'
    pending_method = None
    hits = 0
    with open(DUMP, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if "Class descriptor" in line:
                m = re.search(r"'([^']+)'", line)
                if m:
                    cur_class = m.group(1)
            if line.strip().startswith('name') and ':' in line:
                m = re.search(r":\s*'([^']+)'", line)
                if m:
                    pending_method = m.group(1)
            if "(in " in line and pending_method:
                cur_method = pending_method
            if term in line:
                print('=== hit %d' % (hits + 1))
                print('    class : %s' % cur_class)
                print('    method: %s' % cur_method)
                print('    line  : %s' % line.strip()[:160])
                hits += 1
                if hits > 25:
                    break
    print('total shown:', hits)
    return 0


if __name__ == '__main__':
    sys.exit(main())
