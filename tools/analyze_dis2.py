#!/usr/bin/env python3
"""Richer LuaJIT 2.0 disassembler for the startup/update analysis.

Adds over tools/luajit_dis.py:
  * resolves GGET/GSET (D = kgc index) to the global name
  * resolves TGETV/TSETV, TGETS/TSETS, CALL/CALLM, JMP targets
  * prints uv (upvalue) table and flags

usage:
  python tools/analyze_dis2.py <member> <protoIdx> [start] [count]
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


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    if 0 <= pos < len(pt.kgc):
        return pt.kgc[pos]
    return None


def short(v):
    if isinstance(v, str):
        return v if len(v) <= 120 else v[:117] + '...'
    if isinstance(v, TableConst):
        return 'TAB(arr=%r hash=%r)' % (v.array[:8], v.hash[:8])
    if isinstance(v, ChildRef):
        return 'CHILD#%d' % v.index
    return repr(v)


def fmt(ins, pt, i):
    op = ins & 0xff
    a = (ins >> 8) & 0xff
    b = (ins >> 24) & 0xff
    c = (ins >> 16) & 0xff
    d = (ins >> 16) & 0xffff
    name = OPS[op] if op < len(OPS) else 'OP_%d' % op
    note = ''
    if name in ('GGET', 'GSET', 'KSTR', 'FNEW', 'TDUP', 'KCDATA'):
        note = repr(short(kidx(pt, d)))
    elif name == 'KNUM':
        pos = len(pt.knum) - 1 - d
        note = repr(pt.knum[pos]) if 0 <= pos < len(pt.knum) else 'oob'
    elif name in ('TGETS', 'TSETS'):
        note = '[key=%s]' % repr(short(kidx(pt, c)))
    elif name == 'KSHORT':
        note = '%d' % (d if d < 0x8000 else d - 0x10000)
    elif name in ('KPRI', 'KNIL'):
        note = '%d' % d
    elif name in ('JMP', 'FORI', 'FORL', 'ITERL', 'LOOP', 'JFORI', 'JFORL', 'JITERL', 'JLOOP'):
        tgt = i + 1 + (d if d < 0x8000 else d - 0x10000)
        note = '-> %d' % tgt
    return '  %4d  %-7s A=%-3d B=%-3d C=%-3d D=%-6d %s' % (i, name, a, b, c, d, note)


def dump(pt, start=0, count=100000):
    print('--- proto #%d  flags=0x%02x params=%d fs=%d uv=%d bc=%d ---'
          % (pt.index, pt.flags, pt.numparams, pt.framesize, pt.numuv, len(pt.bc)))
    print('  uv:', pt.uv)
    for i in range(start, min(start + count, len(pt.bc))):
        print(fmt(pt.bc[i], pt, i))


def load(member, apk=APK):
    z = zipfile.ZipFile(apk)
    key = member if member in z.namelist() else 'assets/src/' + member.lstrip('/')
    return parse_bytes(z.read(key)), key


def main():
    ap, idx = sys.argv[1], int(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 100000
    r, key = load(ap)
    print('==== %s protos=%d' % (key, len(r.protos)))
    dump(r.protos[idx], start, count)


if __name__ == '__main__':
    main()
