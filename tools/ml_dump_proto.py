#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按**proto 序号**反汇编 .luac（补 dump_proto.py 只能按关键字过滤的短板）。

用法：python tools/ml_dump_proto.py <apk> <member> <proto_index> [max_instr]

为什么要它：定位某个方法时，方法名往往**不在它自己的常量池里**（名字在类表那一层），
所以 `dump_proto.py <关键字>` 过滤不到它。先用 `tools/luac_defs.py <luac>` 拿到
"方法名 -> proto#N"，再用本工具按序号 dump。
"""
import sys
import os
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader  # noqa: E402
from luajit_dis import decode  # noqa: E402


def main():
    apk, member, idx = sys.argv[1], sys.argv[2], int(sys.argv[3])
    maxi = int(sys.argv[4]) if len(sys.argv) > 4 else 80
    z = zipfile.ZipFile(apk)
    r = Reader(z.read(member))
    r.parse()
    for pt in r.protos:
        if pt.index != idx:
            continue
        print('=== %s proto #%d bc=%d kgc=%d params=%d uv=%d flags=0x%02x ==='
              % (member, pt.index, len(pt.bc), len(pt.kgc), pt.numparams, pt.numuv, pt.flags))
        print('  strings:', ', '.join(repr(s) for s in pt.strings[:40]))
        for i in range(min(len(pt.bc), maxi)):
            name, a, d, extra = decode(pt.bc[i], pt)
            if isinstance(d, str):
                print('   %4d  %-7s A=%-3d %s%s' % (i, name, a, d, extra))
            else:
                print('   %4d  %-7s A=%-3d D=%-6d%s' % (i, name, a, d, extra))
        if len(pt.bc) > maxi:
            print('   ... (%d more)' % (len(pt.bc) - maxi))
        return 0
    print('proto #%d not found' % idx)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
