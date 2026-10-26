#!/usr/bin/env python3
"""Corrected LuaJIT 2.0 bytecode annotator (branch/operand semantics verified).

Semantics taken from LuaJIT master src/lj_bc.h BCDEF() operand modes and
verified against this corpus:
  * bc_a = bits 8-15, bc_c = bits 16-23, bc_b = bits 24-31, bc_d = bits 16-31
  * IST/ISF  : Amode ___, Dmode var  -> tested register is in D
  * ISEQV/ISNEV/ISLT/... : Amode var, Dmode var/str/num/pri -> compare A with D
    (or with kgc[D] / knum[D] for the S/N forms)
  * The JMP that always follows an IS* op is TAKEN WHEN THE CONDITION HOLDS
    (verified: `x and A or B`, `if not x then x=0 end`, `local b = (x == y)`,
     `if v then ... else ... end` in get_version_info / update_finish / proto5)
  * CALL/CALLM : C(bits16) = nargs+1, B(bits24) = nresults+1 (0 = multiple)
  * CALLM      : nargs is stored in the D field of the PRECEDING word
  * RET A D    : returns D-1 values from A

usage: python tools/analyze_flow2.py <member> <idx> [start] [end]
       python tools/analyze_flow2.py <member> --map
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes, TableConst, ChildRef  # noqa: E402
from luajit_dis import OPS  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
PRI = {0: 'nil', 1: 'false', 2: 'true'}
JUMP = {'JMP', 'UCLO', 'FORI', 'FORL', 'ITERL', 'LOOP', 'JFORI', 'JFORL',
        'JITERL', 'JLOOP', 'IFORL', 'ILOOP', 'ISNEXT'}
CMP = {'ISLT': '<', 'ISGE': '>=', 'ISLE': '<=', 'ISGT': '>',
       'ISEQV': '==', 'ISNEV': '~=', 'ISEQS': '==', 'ISNES': '~=',
       'ISEQN': '==', 'ISNEN': '~=', 'ISEQP': '==', 'ISNEP': '~='}


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def s(v, n=100):
    if isinstance(v, str):
        return v if len(v) <= n else v[:n - 3] + '...'
    if isinstance(v, ChildRef):
        return '<proto#%d>' % v.index
    if isinstance(v, TableConst):
        return 'TAB(arr=%r hash=%r)' % (v.array[:6], v.hash[:6])
    return repr(v)


def kneg(pt, i):
    pos = len(pt.knum) - 1 - i
    return pt.knum[pos] if 0 <= pos < len(pt.knum) else None


def decode_at(pt, i):
    """Return a human-readable single-line annotation for instruction i."""
    w = pt.bc[i]
    op = w & 0xff
    a = (w >> 8) & 0xff
    b = (w >> 24) & 0xff
    c = (w >> 16) & 0xff
    d = (w >> 16) & 0xffff
    nm = OPS[op] if op < len(OPS) else 'OP_%d' % op
    note = ''
    if nm in ('GGET', 'GSET'):
        note = s(kidx(pt, d))
    elif nm in ('KSTR', 'KCDATA', 'FNEW', 'TDUP'):
        note = s(kidx(pt, d))
    elif nm == 'KNUM':
        note = repr(kneg(pt, d))
    elif nm == 'KSHORT':
        note = '%d' % (d if d < 0x8000 else d - 0x10000)
    elif nm == 'KPRI':
        note = PRI.get(d, '?%d' % d)
    elif nm in ('TGETS', 'TSETS'):
        note = '[k=%s]' % s(kidx(pt, c))
    elif nm in ('TGETV', 'TSETV'):
        note = '[r%d]' % c
    elif nm == 'TGETB':
        note = '[%d]' % c
    elif nm in ('IST', 'ISF'):
        note = 'TEST r%d -> if %s then JMP' % (d, 'truthy' if nm == 'IST' else 'falsy')
    elif nm in CMP:
        rhs = ''
        if nm in ('ISEQS', 'ISNES'):
            rhs = s(kidx(pt, d))
        elif nm in ('ISEQN', 'ISNEN'):
            rhs = repr(kneg(pt, d))
        elif nm in ('ISEQP', 'ISNEP'):
            rhs = PRI.get(d, '?%d' % d)
        else:
            rhs = 'r%d' % d
        note = 'if r%d %s %s then JMP' % (a, CMP[nm], rhs)
    elif nm in JUMP:
        off = d - 0x8000
        note = '-> %d' % (i + 1 + off)
    elif nm in ('CALL', 'CALLM'):
        note = 'r%d<-r%d(%d args, %d res)' % (a, a, c - 1, b - 1)
        if nm == 'CALLM' and i > 0:
            note += '  [nargs=%d from prev D]' % ((pt.bc[i - 1] >> 16) & 0xffff)
    elif nm in ('RET', 'RET0', 'RET1'):
        note = 'return %d vals from r%d' % (d - 1, a)
    elif nm == 'KNIL':
        note = 'r%d..r%d = nil' % (a, d - 1)
    elif nm == 'MOV':
        note = 'r%d = r%d' % (a, d)
    elif nm in ('ADDVN', 'SUBVN', 'MULVN', 'DIVVN', 'MODVN'):
        note = 'r%d = r%d %s %r' % (a, d, nm[0:3].lower(), kneg(pt, c))
    elif nm == 'UGET':
        note = 'r%d = uv%d' % (a, d)
    return nm, a, b, c, d, note


def dump(pt, start=0, end=None):
    end = len(pt.bc) if end is None else end
    for i in range(start, min(end, len(pt.bc))):
        nm, a, b, c, d, note = decode_at(pt, i)
        print('  %4d  %-7s A=%-3d B=%-3d C=%-3d D=%-5d %s' % (i, nm, a, b, c, d, note))


def exports_of(r):
    ex, pend = {}, None
    root = r.protos[-1]
    for w in root.bc:
        op = w & 0xff
        nm = OPS[op]
        d = (w >> 16) & 0xffff
        if nm == 'FNEW':
            v = kidx(root, d)
            pend = v.index if isinstance(v, ChildRef) else None
        elif nm == 'GSET' and pend is not None:
            v = kidx(root, d)
            if isinstance(v, str):
                ex[pend] = v
            pend = None
    return ex


def main():
    member = sys.argv[1]
    z = zipfile.ZipFile(APK)
    key = member if member in z.namelist() else 'assets/src/' + member.lstrip('/')
    r = parse_bytes(z.read(key))
    ex = exports_of(r)
    if len(sys.argv) > 2 and sys.argv[2] == '--map':
        print('==== %s protos=%d' % (key, len(r.protos)))
        for i, pt in enumerate(r.protos):
            kids = ','.join(str(k.index) for k in pt.children)
            print('[%2d] %-24s bc=%-4d params=%d uv=%-2d base=%d kids=[%s]'
                  % (i, ('GLOBAL:' + ex[i]) if i in ex else '', len(pt.bc),
                     pt.numparams, pt.numuv, (pt.flags >> 3) & 1, kids))
            if pt.strings:
                print('      %s' % ', '.join(repr(x)[:40] for x in pt.strings[:16]))
        return
    idx = int(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    end = int(sys.argv[4]) if len(sys.argv) > 4 else None
    pt = r.protos[idx]
    print('==== %s proto #%d %s params=%d framesize=%d uv=%d bc=%d'
          % (key, idx, ex.get(idx, ''), pt.numparams, pt.framesize, pt.numuv, len(pt.bc)))
    print('  uvt: uv=%s (raw u16; hi bits = kind)' % pt.uv)
    for i, cpt in enumerate(pt.kgc):
        print('   kgc[opidx %3d] = %s' % (len(pt.kgc) - 1 - i, s(cpt)))
    dump(pt, start, end)


if __name__ == '__main__':
    main()
