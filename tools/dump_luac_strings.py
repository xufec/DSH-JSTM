#!/usr/bin/env python3
"""Dump readable Lua string constants from .luac files inside the game APK.

Navigation tool for the private-server / single-player work: it answers
"which module talks to the network, and what does it call" much faster than
disassembling everything.  The full bytecode parser is tools/luajit_bc.py; this
only reads the per-prototype constant pools.

usage:
  python tools/dump_luac_strings.py assets/src/sys/gamenet.luac
  python tools/dump_luac_strings.py --all --grep "Connect|Send|Recv"
"""
import argparse
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import parse_bytes  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def strings_of(data):
    r = parse_bytes(data)
    out = []
    for pt in r.protos:
        out.extend(pt.strings)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--grep', default=None)
    ap.add_argument('--limit', type=int, default=300)
    args = ap.parse_args()

    pat = re.compile(args.grep, re.I) if args.grep else None
    items = []
    if args.all:
        z = zipfile.ZipFile(APK)
        for n in z.namelist():
            if n.endswith('.luac'):
                items.append((n, z.read(n)))
    elif args.files:
        z = zipfile.ZipFile(APK)
        for f in args.files:
            key = f if f in z.namelist() else 'assets/src/' + f.lstrip('/')
            if key in z.namelist():
                items.append((key, z.read(key)))
            elif os.path.isfile(f):
                with open(f, 'rb') as fh:
                    items.append((f, fh.read()))
            else:
                print('!! not found: %s' % f)
    else:
        ap.error('give files or --all')

    for name, data in items:
        try:
            ss = strings_of(data)
        except Exception as e:
            print('-- %s: parse failed: %r' % (name, e))
            continue
        hits = [s for s in ss if (pat is None or pat.search(s))]
        if not hits:
            continue
        print('==== %s  (%d/%d strings)' % (name, len(hits), len(ss)))
        for s in hits[:args.limit]:
            print('   ', (s if len(s) < 160 else s[:157] + '...'))


if __name__ == '__main__':
    main()
