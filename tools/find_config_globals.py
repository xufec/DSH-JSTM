#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find every GGET/GSET site of a config global inside a .luac corpus.

Purpose: determine the *contract* that assets/src/config.luac (and the CDN
url_config_ewan.lua it downloads) must satisfy — i.e. for each global name,
is it read as a value (string/number) or CALLED as a function, and with how
many arguments?

LuaJIT CALL semantics (src/lj_bc.h):
    CALL:  A = base register, C field = nargs+1, B field = nresults+1
           (B == 0 means "multiple results")

usage:
  python tools/find_config_globals.py <apk> <regex> [--win 8]
"""
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes          # noqa: E402
from luajit_dis import OPS, decode         # noqa: E402


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def fmt(pt, i):
    name, a, d, extra = decode(pt.bc[i], pt)
    if isinstance(d, str):
        return '%4d  %-7s A=%-3d %s%s' % (i, name, a, d, extra)
    return '%4d  %-7s A=%-3d D=%-6d%s' % (i, name, a, d, extra)


def main():
    apk = sys.argv[1]
    pat = re.compile(sys.argv[2])
    win = 8
    if '--win' in sys.argv:
        win = int(sys.argv[sys.argv.index('--win') + 1])

    z = zipfile.ZipFile(apk)
    names = sorted(n for n in z.namelist() if n.endswith('.luac'))
    total = 0
    for n in names:
        data = z.read(n)
        if data[:3] != b'\x1bLJ':
            continue
        try:
            r = parse_bytes(data)
        except Exception:
            continue
        for pt in r.protos:
            sites = []
            for i, w in enumerate(pt.bc):
                if OPS[w & 0xff] in ('GGET', 'GSET'):
                    v = kidx(pt, (w >> 16) & 0xffff)
                    if isinstance(v, str) and pat.search(v):
                        sites.append((i, v))
            if not sites:
                continue
            print('==== %s  proto[%d]  params=%d bc=%d'
                  % (n, pt.index, pt.numparams, len(pt.bc)))
            for i, v in sites:
                total += 1
                print('  -- %s (%s) @%d --' % (v, OPS[pt.bc[i] & 0xff], i))
                lo = max(0, i - 4)
                hi = min(len(pt.bc), i + win)
                for j in range(lo, hi):
                    mark = '>>' if j == i else '  '
                    print('  %s%s' % (mark, fmt(pt, j)))
    print('\ntotal sites matched: %d' % total)


if __name__ == '__main__':
    main()
