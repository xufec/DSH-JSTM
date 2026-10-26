#!/usr/bin/env python3
"""Structural analysis of one .luac member: child-function map + annotated disasm.

LuaJIT branch convention used here (verified empirically against `a or b` /
`a and b` codegen in this corpus):

    <IS cond>      ; if cond holds -> take the following JMP; else fall through
    JMP  -> L

So the JMP is taken WHEN THE CONDITION HOLDS.

usage:
  python tools/analyze_flow.py <member>                 # child map of every proto
  python tools/analyze_flow.py <member> <protoIdx>      # annotated disasm
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes, TableConst, ChildRef  # noqa: E402

OPS = None
from luajit_dis import OPS  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')

JMP_D = {'JMP', 'FORI', 'FORL', 'ITERL', 'LOOP', 'JFORI', 'JFORL', 'JITERL',
         'JLOOP', 'IFORL', 'ILOOP'}


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def s(v, n=90):
    if isinstance(v, str):
        return v if len(v) <= n else v[:n - 3] + '...'
    if isinstance(v, ChildRef):
        return '<proto#%d>' % v.index
    if isinstance(v, TableConst):
        return 'TAB(arr=%r hash=%r)' % (v.array[:6], v.hash[:6])
    return repr(v)


def load(member, apk=APK):
    z = zipfile.ZipFile(apk)
    key = member if member in z.namelist() else 'assets/src/' + member.lstrip('/')
    return parse_bytes(z.read(key)), key


def child_map(r):
    """Return {proto_index: global export name} for the root's FNEW/GSET pairs."""
    exports = {}
    root = r.protos[-1]
    pending = None
    for w in root.bc:
        op = w & 0xff
        a = (w >> 8) & 0xff
        d = (w >> 16) & 0xffff
        nm = OPS[op]
        if nm == 'FNEW':
            v = kidx(root, d)
            pending = v.index if isinstance(v, ChildRef) else None
        elif nm == 'GSET' and pending is not None:
            v = kidx(root, d)
            if isinstance(v, str):
                exports[pending] = v
            pending = None
    return exports


def annotate(r, idx):
    pt = r.protos[idx]
    out = []
    for i, w in enumerate(pt.bc):
        op = w & 0xff
        a = (w >> 8) & 0xff
        b = (w >> 24) & 0xff
        c = (w >> 16) & 0xff
        d = (w >> 16) & 0xffff
        nm = OPS[op] if op < len(OPS) else 'OP_%d' % op
        note = ''
        if nm in ('GGET', 'GSET', 'KSTR', 'FNEW', 'TDUP', 'KCDATA'):
            note = s(kidx(pt, d))
        elif nm == 'KNUM':
            pos = len(pt.knum) - 1 - d
            note = repr(pt.knum[pos]) if 0 <= pos < len(pt.knum) else 'oob'
        elif nm in ('TGETS', 'TSETS'):
            note = '[k=%s]' % s(kidx(pt, c))
        elif nm in ('TGETV', 'TSETV', 'TGETB', 'TSETB'):
            note = '[B=%d C=%d]' % (b, c)
        elif nm == 'KSHORT':
            note = '%d' % (d if d < 0x8000 else d - 0x10000)
        elif nm in ('IST', 'ISF'):
            note = 'cond=r%d ; JMP taken when %s' % (a, 'TRUE' if nm == 'IST' else 'FALSE')
        elif nm in ('ISLT', 'ISGE', 'ISLE', 'ISGT'):
            sym = {'ISLT': '<', 'ISGE': '>=', 'ISLE': '<=', 'ISGT': '>'}[nm]
            note = 'r%d %s D=%d ; JMP taken when cond holds' % (a, sym, d)
        elif nm in ('ISEQV', 'ISNEV', 'ISEQS', 'ISNES', 'ISEQN', 'ISNEN', 'ISEQP', 'ISNEP'):
            op2 = {'ISEQV': '==', 'ISNEV': '~=', 'ISEQS': '==', 'ISNES': '~=',
                   'ISEQN': '==', 'ISNEN': '~=', 'ISEQP': '==', 'ISNEP': '~='}[nm]
            rhs = ''
            if nm in ('ISEQS', 'ISNES'):
                rhs = s(kidx(pt, d))
            elif nm in ('ISEQN', 'ISNEN'):
                pos = len(pt.knum) - 1 - d
                rhs = repr(pt.knum[pos]) if 0 <= pos < len(pt.knum) else 'oob'
            elif nm in ('ISEQP', 'ISNEP'):
                rhs = repr(d)
            note = 'r%d %s B=r%d %s ; JMP taken when cond holds' % (a, op2, b, rhs)
        elif nm in JMP_D:
            off = d - 0x8000
            note = '-> %d' % (i + 1 + off)
        elif nm in ('CALL', 'CALLM'):
            note = 'args=%d res=%d (func r%d)' % (b - 1 if b else 0, c - 1 if c else 0, a)
        elif nm == 'RET0':
            note = 'return'
        out.append('  %4d  %-7s A=%-3d B=%-3d C=%-3d D=%-5d %s' % (i, nm, a, b, c, d, note))
    return pt, out


def main():
    member = sys.argv[1]
    r, key = load(member)
    exports = child_map(r)
    if len(sys.argv) > 2:
        idx = int(sys.argv[2])
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        end = int(sys.argv[4]) if len(sys.argv) > 4 else len(r.protos[idx].bc)
        pt, lines = annotate(r, idx)
        print('==== %s proto #%d %s  params=%d fs=%d uv=%d bc=%d kgc=%d'
              % (key, idx, exports.get(idx, ''), pt.numparams, pt.framesize,
                 pt.numuv, len(pt.bc), len(pt.kgc)))
        print('  uv table:', pt.uv)
        for i, c in enumerate(pt.kgc):
            print('    kgc[opidx %2d] = %s' % (len(pt.kgc) - 1 - i, s(c)))
        print('--- code %d..%d ---' % (start, end))
        for ln in lines[start:end]:
            print(ln)
        return
    print('==== %s protos=%d' % (key, len(r.protos)))
    for i, pt in enumerate(r.protos):
        kids = ['%d%s' % (k.index, '(%s)' % exports[k.index] if k.index in exports else '')
                for k in pt.children]
        print('[%2d]%s bc=%-4d params=%d uv=%-2d kgc=%-3d kids=%s'
              % (i, (' %-22s' % exports[i]) if i in exports else ' ' * 23,
                 len(pt.bc), pt.numparams, pt.numuv, len(pt.kgc), ','.join(kids)))
        strs = pt.strings
        if strs:
            print('       strings: %s' % ', '.join(repr(x)[:44] for x in strs[:14]))


if __name__ == '__main__':
    main()
