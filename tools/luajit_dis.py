#!/usr/bin/env python3
"""Minimal LuaJIT 2.0 bytecode disassembler + semantic helper.

Opcode order taken from LuaJIT v2.0 src/lj_bc.h (BCDEF order matters).
Enough to read registration calls: KSTR / KSHORT / KNUM / FNEW / TDUP /
GGET / TGETS / TSETS / CALL / UCLO / RET0 ...
"""
import sys, os, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# ★ R158：`reconfigure` 在 stdout 已被别处关闭/替换时会抛 `ValueError: I/O operation on
#   closed file` ⇒ 被 import 时直接崩。加 try/except（它只是为了让中文能打印）。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
from luajit_bc import Reader, TableConst, ChildRef

OPS = [
    'ISLT', 'ISGE', 'ISLE', 'ISGT',
    'ISEQV', 'ISNEV', 'ISEQS', 'ISNES', 'ISEQN', 'ISNEN', 'ISEQP', 'ISNEP',
    'ISTC', 'ISFC', 'IST', 'ISF',
    'MOV', 'NOT', 'UNM', 'LEN',
    'ADDVN', 'SUBVN', 'MULVN', 'DIVVN', 'MODVN',
    'ADDNV', 'SUBNV', 'MULNV', 'DIVNV', 'MODNV',
    'ADDVV', 'SUBVV', 'MULVV', 'DIVVV', 'MODVV',
    'POW', 'CAT',
    'KSTR', 'KCDATA', 'KSHORT', 'KNUM', 'KPRI', 'KNIL',
    'UGET', 'USETV', 'USETS', 'USETN', 'USETP', 'UCLO', 'FNEW',
    'TNEW', 'TDUP', 'GGET', 'GSET', 'TGETV', 'TGETS', 'TGETB',
    'TSETV', 'TSETS', 'TSETB', 'TSETM',
    'CALLM', 'CALL', 'CALLMT', 'CALLT', 'ITERC', 'ITERN', 'VARG', 'ISNEXT',
    'RETM', 'RET', 'RET0', 'RET1',
    'FORI', 'JFORI', 'FORL', 'IFORL', 'JFORL', 'ITERL', 'IITERL', 'JITERL',
    'LOOP', 'ILOOP', 'JLOOP', 'JMP',
    'FUNCF', 'IFUNCF', 'JFUNCF', 'FUNCV', 'IFUNCV', 'JFUNCV', 'FUNCC', 'FUNCCW',
]

# opcodes whose D operand indexes the GC-constant table (kgc)
D_KGC = {'KSTR', 'KCDATA', 'FNEW', 'TDUP'}
# opcodes whose D operand indexes the number-constant table (knum)
D_KNUM = {'KNUM'}
# opcodes whose D operand is a primitive literal / jump
D_LIT = {'KSHORT', 'KPRI', 'KNIL', 'JMP'}


def kidx(pt, i):
    """Constant index i -> position in the prototype's kgc list.

    Verified empirically over the whole corpus (tools/check_const_mapping.py):
    index i lives at file position len(kgc)-1-i (100% kind-match), for both the
    D operand (KSTR/FNEW/TDUP/GGET/GSET) and the C operand (TGETS/TSETS keys).
    """
    pos = len(pt.kgc) - 1 - i
    if 0 <= pos < len(pt.kgc):
        return pt.kgc[pos]
    return None


def decode(ins, pt):
    op = ins & 0xff
    a = (ins >> 8) & 0xff
    b = (ins >> 24) & 0xff
    c = (ins >> 16) & 0xff
    d = (ins >> 16) & 0xffff
    name = OPS[op] if op < len(OPS) else 'OP_%d' % op
    extra = ''
    if name in ('TGETS', 'TSETS'):
        v = kidx(pt, c)
        extra = '   ; [%r]' % _short(v) if v is not None else '   ; [C=%d oob]' % c
        return name, a, 'B=%-3d C=%-3d' % (b, c), extra
    if name in D_KGC:
        v = kidx(pt, d)
        extra = '   ; %r' % _short(v) if v is not None else '   ; D=%d oob' % d
    elif name in D_KNUM:
        pos = len(pt.knum) - 1 - d
        extra = '   ; %r' % pt.knum[pos] if 0 <= pos < len(pt.knum) else ''
    elif name == 'KSHORT':
        extra = '   ; %d' % d
    return name, a, d, extra


def _short(v):
    if isinstance(v, str):
        return v if len(v) <= 40 else v[:37] + '...'
    return v


def disasm(pt, start=0, count=40):
    for i in range(start, min(start + count, len(pt.bc))):
        name, a, d, extra = decode(pt.bc[i], pt)
        if isinstance(d, str):
            print('  %4d  %-7s A=%-3d %s%s' % (i, name, a, d, extra))
        else:
            print('  %4d  %-7s A=%-3d D=%-6d%s' % (i, name, a, d, extra))


def main():
    apk, member = sys.argv[1], sys.argv[2]
    idx = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    start = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    count = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    z = zipfile.ZipFile(apk)
    r = Reader(z.read(member))
    r.parse()
    pt = r.protos[idx]
    print('=== %s proto #%d  bc=%d kgc=%d params=%d flags=0x%02x ==='
          % (member, idx, len(pt.bc), len(pt.kgc), pt.numparams, pt.flags))
    print('kgc:', ', '.join(('#%d' % i) + repr(c)[:34] for i, c in enumerate(pt.kgc[:60])))
    print('--- code ---')
    disasm(pt, start, count)


if __name__ == '__main__':
    main()