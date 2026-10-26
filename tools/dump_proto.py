#!/usr/bin/env python3
"""Dump prototypes of a .luac member with disassembly, filtered by keyword.

Usage: python tools/dump_proto.py <apk> <member> [keyword] [max_instr]
"""
import sys, os, re, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader, TableConst, ChildRef
from luajit_dis import decode


def main():
    apk, member = sys.argv[1], sys.argv[2]
    kw = sys.argv[3] if len(sys.argv) > 3 else None
    maxi = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    z = zipfile.ZipFile(apk)
    r = Reader(z.read(member))
    r.parse()
    print('=== %s  protos=%d ===' % (member, len(r.protos)))
    for pt in r.protos:
        strs = [s for s in pt.strings]
        if kw and not any(kw in s for s in strs):
            continue
        print('\n--- proto #%d bc=%d kgc=%d params=%d uv=%d flags=0x%02x'
              % (pt.index, len(pt.bc), len(pt.kgc), pt.numparams, pt.numuv, pt.flags))
        print('    strings:', ', '.join(repr(s) for s in strs[:28]))
        for t in pt.tables[:4]:
            vals = [repr(x) for x in t.array if isinstance(x, str)][:10]
            print('    table  : {%s}' % ', '.join(vals))
        for i in range(min(len(pt.bc), maxi)):
            name, a, d, extra = decode(pt.bc[i], pt)
            if isinstance(d, str):
                print('      %4d  %-7s A=%-3d %s%s' % (i, name, a, d, extra))
            else:
                print('      %4d  %-7s A=%-3d D=%-6d%s' % (i, name, a, d, extra))
        if len(pt.bc) > maxi:
            print('      ... (%d more instructions)' % (len(pt.bc) - maxi))


if __name__ == '__main__':
    main()