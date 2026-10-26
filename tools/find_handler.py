#!/usr/bin/env python3
"""Scan APK .luac files for a handler/string and report matching protos.

Usage: python tools/find_handler.py <apk> <needle> [name_filter_substr]

Prints, for every .luac (optionally filtered by path substring) that mentions
<needle>, the proto indices and the neighbouring strings, so we can decide what
convention the handler uses (code == TRUE / 0 / 1 ...).
"""
import sys, os, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader


def main():
    apk, needle = sys.argv[1], sys.argv[2]
    name_filter = sys.argv[3] if len(sys.argv) > 3 else ''
    z = zipfile.ZipFile(apk)
    hits = 0
    for info in z.infolist():
        n = info.filename
        if not n.startswith('assets/src/') or not n.endswith('.luac'):
            continue
        if name_filter and name_filter not in n:
            continue
        try:
            data = z.read(n)
            r = Reader(data)
            r.parse()
        except Exception:
            continue
        for i, pt in enumerate(r.protos):
            strs = [str(s) for s in pt.strings]
            joined = ' '.join(strs)
            if needle in joined:
                hits += 1
                print('=== %s proto #%d ===' % (n, i))
                print('   ', ' , '.join(repr(s) for s in strs[:30]))
    print('total proto hits: %d' % hits)


if __name__ == '__main__':
    main()