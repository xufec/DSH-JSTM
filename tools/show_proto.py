"""按 proto 编号反汇编一个 .luac（通用分析小工具，与 find_proto_with.py 配合使用）。

用法：
    python tools/show_proto.py <file.luac> <protoIdx> [maxBC] [--around <str> <ctx>]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_file  # noqa: E402
from luajit_dis import disasm      # noqa: E402


def main():
    path = sys.argv[1]
    idx = int(sys.argv[2])
    rest = sys.argv[3:]
    needle, ctx = None, 8
    if '--around' in rest:
        i = rest.index('--around')
        needle = rest[i + 1]
        if len(rest) > i + 2:
            ctx = int(rest[i + 2])
        maxbc = 100000
    else:
        maxbc = int(rest[0]) if rest else 400

    r = parse_file(path)
    pt = r.protos[idx]
    print('=== %s proto#%d  bc=%d ===' % (os.path.basename(path), idx, len(pt.bc)))
    print('strings: %s' % (pt.strings,))
    if pt.knum:
        print('knum: %s' % (pt.knum[:60],))
    if needle is not None:
        print('--- 全量反汇编（用 --around 时请自行 grep %r）---' % needle)
        disasm(pt, 0, len(pt.bc))
        return
    print('--- disasm ---')
    disasm(pt, 0, min(len(pt.bc), maxbc))


if __name__ == '__main__':
    main()
