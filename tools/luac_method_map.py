"""把一个 LuaJIT .luac 模块的"方法名 -> 子原型索引"映射还原出来。

原理：`function M.foo() end` 编译为
      FNEW  A=r, <child>          ; 取子原型
      TSETS A=r-1, C='foo'        ; 赋给表字段
因此扫描 root 原型字节码，遇到 FNEW 后向后看 1~4 条指令内的 TSETS 即可拿到名字。

用法：
    python tools/luac_method_map.py <file.luac> [--disasm <name>]
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


def map_methods(pt):
    """返回 [(name, child_index, bc_index)]"""
    out = []
    bc = pt.bc
    for i, w in enumerate(bc):
        if op_name(w) != 'FNEW':
            continue
        a_fnew = (w >> 8) & 0xff
        d = (w >> 16) & 0xffff
        child = kidx(pt, d)
        if not isinstance(child, ChildRef):
            continue
        name = None
        for j in range(i + 1, min(i + 5, len(bc))):
            w2 = bc[j]
            if op_name(w2) != 'TSETS':
                continue
            a2 = (w2 >> 8) & 0xff
            if a2 != (a_fnew - 1) & 0xff:
                continue
            c = (w2 >> 16) & 0xff
            v = kidx(pt, c)
            if isinstance(v, str):
                name = v
            break
        out.append((name, child.index, i))
    return out


def main():
    path = sys.argv[1]
    want = None
    if '--disasm' in sys.argv:
        want = sys.argv[sys.argv.index('--disasm') + 1]

    r = parse_file(path)
    print('=== %s version=%d flags=0x%02x protos=%d name=%r ==='
          % (os.path.basename(path), r.version, r.flags, len(r.protos), r.name))

    root = r.protos[0]
    print('root: %r' % root)
    ms = map_methods(root)
    print('--- root 直接定义的方法 (%d) ---' % len(ms))
    for name, ci, bi in ms:
        ch = r.protos[ci] if ci < len(r.protos) else None
        print('  %-28s -> proto#%-4d bc=%-5s  (bc idx %d)'
              % (name, ci, len(ch.bc) if ch else '?', bi))

    # 也扫描全部 proto，找出嵌套定义的函数
    print('--- 所有 proto 概览 ---')
    for i, pt in enumerate(r.protos):
        ss = pt.strings
        head = [s for s in ss[:6]]
        print('  #%-4d bc=%-6d params=%-2d kgc=%-4d uv=%-2d  %s'
              % (i, len(pt.bc), pt.numparams, len(pt.kgc), pt.numuv,
                 ', '.join(repr(s)[:32] for s in head)))

    if want is not None:
        hits = [m for m in ms if m[0] == want]
        if not hits:
            print('!! root 里没找到方法 %r' % want)
            return
        for name, ci, bi in hits:
            pt = r.protos[ci]
            print('\n=== 反汇编 %s (proto#%d, %d 条字节码) ===' % (name, ci, len(pt.bc)))
            print('  strings(%d): %s' % (len(pt.strings),
                                         ', '.join(repr(s) for s in pt.strings[:120])))
            for t in pt.tables[:20]:
                print('  table: %r' % (t,))
            if pt.knum:
                print('  knum: %s' % (pt.knum[:40],))
            print('  --- code ---')
            from luajit_dis import disasm
            disasm(pt, 0, len(pt.bc))


if __name__ == '__main__':
    main()
