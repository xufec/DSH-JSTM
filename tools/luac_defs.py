"""扫描 .luac 全部 proto，找出每个方法名在哪个 proto 里被定义（FNEW -> TSETS/TSETV）。

同时支持按名字反查所在 proto，便于定位 MissionUtil.moveToNpc 之类的实现体。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import ChildRef, parse_file  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def scan(pt):
    """返回 [(name, child_idx, bc_idx, kind)]"""
    out = []
    bc = pt.bc
    for i, w in enumerate(bc):
        op = op_name(w)
        if op == 'FNEW':
            a = (w >> 8) & 0xff
            d = (w >> 16) & 0xffff
            ch = kidx(pt, d)
            if not isinstance(ch, ChildRef):
                continue
            nm = None
            for j in range(i + 1, min(i + 6, len(bc))):
                w2 = bc[j]
                o2 = op_name(w2)
                if o2 in ('TSETS',):
                    a2 = (w2 >> 8) & 0xff
                    c2 = (w2 >> 16) & 0xff
                    v = kidx(pt, c2)
                    if isinstance(v, str):
                        nm = (v, 'TSETS', a2, a)
                    break
                if o2 in ('TSETV', 'TSETB'):
                    a2 = (w2 >> 8) & 0xff
                    c2 = (w2 >> 16) & 0xff
                    v = kidx(pt, c2)
                    nm = (repr(v), o2, a2, a)
                    break
                if o2 in ('FNEW', 'CALL', 'RET0', 'RET1'):
                    break
            if nm:
                out.append((nm[0], ch.index, i, '%s(a=%d,fnew_a=%d)' % (nm[1], nm[2], nm[3])))
    return out


def main():
    path = sys.argv[1]
    want = sys.argv[2] if len(sys.argv) > 2 else None
    r = parse_file(path)
    print('=== %s protos=%d ===' % (os.path.basename(path), len(r.protos)))
    total = 0
    for i, pt in enumerate(r.protos):
        ms = scan(pt)
        if not ms:
            continue
        total += len(ms)
        print('--- proto#%d (bc=%d) 定义 %d 个 ---' % (i, len(pt.bc), len(ms)))
        for name, ci, bi, kind in ms:
            mark = '  <<<<' if (want and want in name) else ''
            ch = r.protos[ci]
            print('    %-34s -> proto#%-4d bc=%-5d  %s%s'
                  % (name, ci, len(ch.bc), kind, mark))
    print('合计定义点: %d' % total)


if __name__ == '__main__':
    main()
