#!/usr/bin/env python3
"""Print raw LuaJIT instruction words + decoded A/B/C/D for chosen protos.

Goal: pin down the exact bit layout of the B and C operands empirically
(grep for calls whose argument count we can infer from the preceding MOVs).

usage: python tools/analyze_words.py <member> <idx> [idx...]
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import OPS  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def main():
    member = sys.argv[1]
    z = zipfile.ZipFile(APK)
    key = member if member in z.namelist() else 'assets/src/' + member.lstrip('/')
    r = parse_bytes(z.read(key))
    for a in sys.argv[2:]:
        pt = r.protos[int(a)]
        print('=== proto #%d bc=%d params=%d fs=%d' % (pt.index, len(pt.bc), pt.numparams, pt.framesize))
        for i, w in enumerate(pt.bc):
            op = w & 0xff
            nm = OPS[op] if op < len(OPS) else 'OP_%d' % op
            print('  %4d  %08x  %-7s A=%-3d b16=%-3d b24=%-3d D=%-6d'
                  % (i, w, nm, (w >> 8) & 0xff, (w >> 16) & 0xff, (w >> 24) & 0xff,
                     (w >> 16) & 0xffff))


if __name__ == '__main__':
    main()
