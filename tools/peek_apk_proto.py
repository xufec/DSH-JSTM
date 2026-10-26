# -*- coding: utf-8 -*-
"""从 APK 中直接反汇编某个 .luac 的指定 proto（一步到位，不落盘）。
用法: python tools/peek_apk_proto.py <apk> <member> [#proto ...]
     #proto 省略时只列出所有 proto 的摘要
"""
import sys, os, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader
from luajit_dis import disasm


def load(apk, member):
    with zipfile.ZipFile(apk) as z:
        with z.open(member) as f:
            return f.read()


def main():
    apk, member = sys.argv[1], sys.argv[2]
    want = [int(x) for x in sys.argv[3:]]
    r = Reader(load(apk, member))
    r.parse()
    print('=== %s : %s version=%d flags=0x%02x protos=%d ==='
          % (os.path.basename(apk), member, r.version, r.flags, len(r.protos)))
    for i, pt in enumerate(r.protos):
        if want and i not in want:
            continue
        print('\n--- proto #%d bc=%d param=%d fsize=%d uv=%d flags=0x%02x ---'
              % (i, len(pt.bc), pt.numparams, pt.framesize, pt.numuv, pt.flags))
        if pt.strings:
            print('  strings(%d): %s' % (len(pt.strings),
                  ', '.join(repr(s) for s in pt.strings[:60])))
        if pt.tables:
            for t in pt.tables[:8]:
                print('  table: %s' % repr(t)[:260])
        if len(pt.knum):
            print('  knum: %s' % pt.knum[:40])
        if want:
            print('  --- code ---')
            disasm(pt, 0, int(os.environ.get('PEEK_COUNT', '400')))


if __name__ == '__main__':
    main()
