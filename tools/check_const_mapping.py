#!/usr/bin/env python3
"""Determine the constant-index mapping empirically.

For each instruction whose D operand indexes the GC-constant table, the LuaJIT
semantics require a specific constant kind:
    KSTR   -> string        FNEW -> function(ChildRef)
    TDUP   -> table         GGET -> string (global name)
If we resolve the index with the wrong mapping, the kind-match rate collapses.
We tally both candidate mappings over the whole corpus and report the winner.
"""
import sys, os, zipfile, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader, TableConst, ChildRef

EXPECT = {'KSTR': 'str', 'FNEW': 'fn', 'TDUP': 'tab', 'GGET': 'str', 'GSET': 'str',
          'TGETS': 'str', 'TSETS': 'str'}
OPS = {37: 'KSTR', 49: 'FNEW', 51: 'TDUP', 52: 'GGET', 53: 'GSET',
       55: 'TGETS', 58: 'TSETS'}


def kind(c):
    if isinstance(c, str):
        return 'str'
    if isinstance(c, ChildRef):
        return 'fn'
    if isinstance(c, TableConst):
        return 'tab'
    return 'num'


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.endswith('.luac')]
    step = max(1, len(names) // 300)
    names = names[::step]
    stats = {'direct': collections.Counter(), 'reversed': collections.Counter(),
             'rev_B': collections.Counter(), 'rev_C': collections.Counter()}
    files_ok = 0
    for n in names:
        try:
            r = Reader(z.read(n))
            r.parse()
        except Exception:
            continue
        files_ok += 1
        for pt in r.protos:
            L = len(pt.kgc)
            for ins in pt.bc:
                op = ins & 0xff
                nm = OPS.get(op)
                if not nm:
                    continue
                d = (ins >> 16) & 0xffff
                b = (ins >> 24) & 0xff
                c = (ins >> 16) & 0xff
                exp = EXPECT[nm]
                cands = [('direct', d), ('reversed', L - 1 - d)]
                if nm in ('TGETS', 'TSETS'):
                    cands = [('rev_B', L - 1 - b), ('rev_C', L - 1 - c),
                             ('direct', d)]
                for label, idx in cands:
                    if 0 <= idx < L:
                        stats[label][(nm, kind(pt.kgc[idx]) == exp)] += 1
                    else:
                        stats[label][(nm, 'oob')] += 1
    print('files parsed:', files_ok)
    for label in ('direct', 'reversed', 'rev_B', 'rev_C'):
        tot = sum(v for k, v in stats[label].items() if isinstance(k[1], bool))
        if not tot:
            continue
        good = sum(v for k, v in stats[label].items() if k[1] is True)
        print('\n%-9s : %d/%d kind-match (%.1f%%)'
              % (label, good, tot, 100.0 * good / max(1, tot)))
        for (nm, ok), v in sorted(stats[label].items(), key=lambda x: -x[1])[:8]:
            print('     %-5s %-6s %d' % (nm, ok, v))


if __name__ == '__main__':
    main()