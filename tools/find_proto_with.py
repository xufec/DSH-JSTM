"""在指定 .luac 里找出"含某字符串常量的 proto 编号"，便于定位枚举/表定义。

用法：python tools/find_proto_with.py <file.luac> MIS_ [--disasm]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_file  # noqa: E402
from luajit_dis import disasm  # noqa: E402


def main():
    path = sys.argv[1]
    needle = sys.argv[2] if len(sys.argv) > 2 else 'MIS_'
    do_dis = '--disasm' in sys.argv
    r = parse_file(path)
    print('=== %s protos=%d  检索 %r ===' % (os.path.basename(path), len(r.protos), needle))
    for i, pt in enumerate(r.protos):
        hits = [s for s in pt.strings if needle in s]
        if hits:
            print('  proto#%-4d bc=%-6d 命中 %d: %s'
                  % (i, len(pt.bc), len(hits), hits[:30]))
    if do_dis:
        for i, pt in enumerate(r.protos):
            if any(needle in s for s in pt.strings):
                print('\n--- 反汇编 proto#%d (bc=%d) ---' % (i, len(pt.bc)))
                print('  strings: %s' % (pt.strings[:60],))
                for t in pt.tables[:10]:
                    print('  table: %r' % (t,))
                if pt.knum:
                    print('  knum: %s' % (pt.knum[:40],))
                disasm(pt, 0, min(len(pt.bc), 200))


if __name__ == '__main__':
    main()
