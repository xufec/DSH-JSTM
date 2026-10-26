#!/usr/bin/env python3
"""Startup/update-flow analysis helper.

Dumps per-proto string constants + table constants for selected .luac members
of the game APK, so we can locate the update entry points quickly.

usage:
  python tools/analyze_startup_flow.py <member> [--grep RE] [--tables]
"""
import argparse
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes, TableConst, ChildRef  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def load(member, apk=APK):
    z = zipfile.ZipFile(apk)
    key = member if member in z.namelist() else 'assets/src/' + member.lstrip('/')
    return z.read(key), key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--grep', default=None)
    ap.add_argument('--tables', action='store_true')
    ap.add_argument('--limit', type=int, default=400)
    args = ap.parse_args()
    pat = re.compile(args.grep, re.I) if args.grep else None

    for f in args.files:
        try:
            data, key = load(f)
            r = parse_bytes(data)
        except Exception as e:
            print('!! %s: %r' % (f, e))
            continue
        print('==== %s  protos=%d  (file len=%d)' % (key, len(r.protos), len(data)))
        for i, pt in enumerate(r.protos):
            ss = pt.strings
            hits = [s for s in ss if (pat is None or pat.search(s))]
            if pat and not hits:
                continue
            print('  [%d] %r params=%d uv=%d fs=%d' % (i, pt, pt.numparams, pt.numuv, pt.framesize))
            for s in (hits[:args.limit] if pat else ss[:args.limit]):
                print('        S %r' % (s if len(s) < 200 else s[:197] + '...'))
            if args.tables:
                for t in pt.tables:
                    print('        T arr=%r hash=%r' % (t.array[:12], t.hash[:12]))


if __name__ == '__main__':
    main()
