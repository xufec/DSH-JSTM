"""提取某个 LuaJIT 原型的"外部调用序列"（GGET 全局 -> TGETS 方法 -> CALL）。

用途：不需要完整反编译，就能看清一个函数**到底调用了哪些模块的哪些方法**，
以及它引用了哪些字符串常量（用于判断分支条件名）。

用法：
    python tools/luac_callgraph.py <file.luac> <proto_index> [--strings] [--filter 正则]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import ChildRef, TableConst, parse_file  # noqa: E402
from luajit_dis import OPS, decode, kidx  # noqa: E402


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def main():
    path = sys.argv[1]
    idx = int(sys.argv[2])
    show_strings = '--strings' in sys.argv
    filt = None
    if '--filter' in sys.argv:
        filt = re.compile(sys.argv[sys.argv.index('--filter') + 1], re.I)

    r = parse_file(path)
    pt = r.protos[idx]
    bc = pt.bc

    print('=== %s proto#%d bc=%d params=%d kgc=%d ==='
          % (os.path.basename(path), idx, len(bc), pt.numparams, len(pt.kgc)))

    if show_strings:
        print('--- 全部字符串常量 (%d) ---' % len(pt.strings))
        for i, s in enumerate(pt.strings):
            if filt is None or filt.search(s):
                print('  [%3d] %s' % (i, s))

    # 追踪寄存器: reg -> (kind, value)
    regs = {}
    calls = []
    print('--- 调用序列 ---')
    for i, w in enumerate(bc):
        op = op_name(w)
        a = (w >> 8) & 0xff
        c = (w >> 16) & 0xff
        d = (w >> 16) & 0xffff
        if op == 'GGET':
            v = kidx(pt, d)
            regs[a] = ('global', v)
        elif op in ('TGETS', 'TSETS'):
            v = kidx(pt, c)
            if op == 'TGETS':
                base = regs.get((w >> 24) & 0xff)
                regs[a] = ('method', (base[1] if base else '?', v))
            else:
                regs.setdefault(a, ('table', '?'))
        elif op == 'KSTR':
            v = kidx(pt, d)
            regs[a] = ('str', v)
        elif op == 'KSHORT':
            regs[a] = ('int', d)
        elif op == 'TDUP':
            v = kidx(pt, d)
            regs[a] = ('table', v)
        elif op == 'TNEW':
            regs[a] = ('table', '{}')
        elif op == 'FNEW':
            v = kidx(pt, d)
            regs[a] = ('func', v)
        elif op in ('MOV',):
            pass
        elif op in ('CALL', 'CALLM', 'CALLMT', 'CALLT'):
            f = regs.get(a)
            tag = '?'
            if f and f[0] == 'method':
                mod, meth = f[1]
                modn = mod[1] if isinstance(mod, tuple) else mod
                tag = '%s.%s' % (modn, meth)
            elif f and f[0] == 'global':
                tag = 'GLOBAL(%s)' % (f[1],)
            elif f and f[0] == 'func':
                tag = 'local_func#%s' % (f[1],)
            elif f and f[0] == 'str':
                tag = 'STR_CALL(%r)' % (f[1],)
            arg0 = regs.get(a + 1)
            arg = arg0[1] if arg0 else None
            calls.append((i, tag, arg, op))
            if filt is None or filt.search(str(tag)):
                print('  %5d  %-6s %-52s arg1=%r' % (i, op, tag, arg))

    print('--- 调用统计 ---')
    from collections import Counter
    cnt = Counter(t for _, t, _, _ in calls)
    for t, n in cnt.most_common(60):
        print('  %4d x  %s' % (n, t))


if __name__ == '__main__':
    main()
