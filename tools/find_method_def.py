#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Locate a method's definition (FNEW+TSETS) inside the .luac corpus.

LuaJIT operand fields differ per opcode, which is easy to get wrong:
  * GGET / GSET  : D field (bits 16-31) indexes kgc
  * TGETS/TSETS  : C field (bits 16-23) indexes kgc   <-- a 8-bit field
Passing a 16-bit D mask for TGETS silently matches nothing.

usage: python tools/find_method_def.py <apk> <methodName>
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes      # noqa: E402
from luajit_dis import OPS            # noqa: E402


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def main():
    apk, name = sys.argv[1], sys.argv[2]
    z = zipfile.ZipFile(apk)
    for n in sorted(x for x in z.namelist() if x.endswith('.luac')):
        data = z.read(n)
        if data[:3] != b'\x1bLJ':
            continue
        try:
            r = parse_bytes(data)
        except Exception:
            continue
        for pt in r.protos:
            for i, w in enumerate(pt.bc):
                op = OPS[w & 0xff]
                if op != 'TSETS':
                    continue
                c = (w >> 16) & 0xff
                if kidx(pt, c) != name:
                    continue
                prev = pt.bc[i - 1] if i > 0 else 0
                child = None
                if OPS[prev & 0xff] == 'FNEW':
                    v = kidx(pt, (prev >> 16) & 0xffff)
                    if hasattr(v, 'index'):
                        child = v.index
                print('DEF  %s  proto[%d] @%d  -> child proto[%s]'
                      % (n, pt.index, i, child))
                if child is not None:
                    cp = r.protos[child]
                    ss = [x for x in cp.kgc if isinstance(x, str)]
                    print('     child proto[%d] params=%d bc=%d' %
                          (child, cp.numparams, len(cp.bc)))
                    print('     strings: %s' % ss)
        # also report plain reads of the name
        for pt in r.protos:
            for i, w in enumerate(pt.bc):
                op = OPS[w & 0xff]
                if op in ('GGET', 'GSET'):
                    if kidx(pt, (w >> 16) & 0xffff) == name:
                        print('GGET/GSET %s proto[%d] @%d %s' % (n, pt.index, i, op))
                elif op in ('TGETS', 'TSETS'):
                    if kidx(pt, (w >> 16) & 0xff) == name:
                        print('TGETS/TSETS %s proto[%d] @%d %s' % (n, pt.index, i, op))


if __name__ == '__main__':
    main()
