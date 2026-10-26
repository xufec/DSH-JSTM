#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the CS/SC message definitions for one or more command numbers,
extracted from protocol/manual.md (the auto-generated protocol manual).

usage: python tools/show_cmd.py 10921 10924 13200
"""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TXT = open('protocol/manual.md', encoding='utf-8').read()


def section(cmd):
    m = re.search(r'^## 命令 %d\s*$(.*?)(?=^## 命令 |\Z)' % cmd, TXT, re.M | re.S)
    return m.group(1) if m else None


def main():
    for a in sys.argv[1:]:
        cmd = int(a)
        body = section(cmd)
        print('=' * 62)
        if body is None:
            print('命令 %d : manual.md 里没有该段' % cmd)
            continue
        print('命令 %d' % cmd)
        for ln in body.strip().splitlines():
            s = ln.strip()
            if s.startswith('- `C') or s.startswith('- `S'):
                print('  ' + s)
            elif s.startswith('|'):
                print('      ' + s)


if __name__ == '__main__':
    main()
