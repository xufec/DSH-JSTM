#!/usr/bin/env python3
"""Disassemble a standalone .luac file (not inside an APK).

Usage: python tools/dis_luac_file.py <file.luac> [proto_idx] [start] [count]
  proto_idx default: list protos then dump all (limited)
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader
from luajit_dis import disasm


def main():
    path = sys.argv[1]
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else -1
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
    data = open(path, 'rb').read()
    r = Reader(data)
    r.parse()
    print('=== %s version=%d flags=0x%02x protos=%d ==='
          % (os.path.basename(path), r.version, r.flags, len(r.protos)))
    idxs = [idx] if idx >= 0 else range(len(r.protos))
    for i in idxs:
        pt = r.protos[i]
        print('\n--- proto #%d bc=%d param=%d fsize=%d uv=%d flags=0x%02x ---'
              % (i, len(pt.bc), pt.numparams, pt.framesize, pt.numuv, pt.flags))
        strs = pt.strings
        if strs:
            print('  strings(%d): %s' % (
                len(strs), ', '.join(repr(s) for s in strs[:80])))
        if pt.tables:
            print('  tables(%d):' % len(pt.tables))
            for t in pt.tables[:20]:
                print('    ', repr(t)[:220])
        if len(pt.knum):
            print('  knum(%d): %s' % (len(pt.knum), pt.knum[:50]))
        print('  --- code ---')
        disasm(pt, start, count)


if __name__ == '__main__':
    main()