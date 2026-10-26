"""解析"导出表 proto"里的 FNEW→GSET 配对：给出 函数名 → 子 proto 编号。

用法：python tools/export_map.py <file.luac> <exportProtoIdx> [名字关键字]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_file  # noqa: E402
from luajit_dis import OPS, kidx   # noqa: E402


def main():
    path = sys.argv[1]
    idx = int(sys.argv[2])
    key = sys.argv[3] if len(sys.argv) > 3 else None
    r = parse_file(path)
    pt = r.protos[idx]
    last = None
    for i, w in enumerate(pt.bc):
        op = OPS[w & 0xff]
        d = (w >> 16) & 0xffff
        if op == 'FNEW':
            last = kidx(pt, d)
        elif op == 'GSET':
            name = kidx(pt, d)
            tgt = None
            if last is not None:
                tgt = getattr(last, 'idx', None)
                if tgt is None:
                    tgt = getattr(last, 'proto_idx', None)
                if tgt is None:
                    tgt = repr(last)
            if key is None or (isinstance(name, str) and key in name):
                print('%-4d %-34s -> %s' % (i, name, tgt))
            last = None


if __name__ == '__main__':
    main()
