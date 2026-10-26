#!/usr/bin/env python3
"""Probe: how are protocol field rules stored as constants?

Prints, for one .luac member, every prototype's string constants and its
table constants expanded in full, so the field-rule layout can be inferred.
"""
import sys, os, zipfile, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader, TableConst, ChildRef

CLS = re.compile(r'^(CS|SC)[A-Za-z0-9_]*_\d+$')


def fmt(v, depth=0, maxdepth=4):
    if isinstance(v, str):
        s = v if len(v) <= 48 else v[:45] + '...'
        return repr(s)
    if isinstance(v, ChildRef):
        return '<fn#%d>' % v.index
    if isinstance(v, TableConst):
        if depth >= maxdepth:
            return '{..%d/%d..}' % (len(v.array), len(v.hash))
        parts = []
        for x in v.array:
            if x is not None:
                parts.append(fmt(x, depth + 1, maxdepth))
        for k, x in v.hash:
            parts.append('%s=%s' % (fmt(k, depth + 1, maxdepth), fmt(x, depth + 1, maxdepth)))
        return '{' + ','.join(parts) + '}'
    return repr(v)


def main():
    apk, member = sys.argv[1], sys.argv[2]
    max_protos = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    show_tables = '--tables' in sys.argv
    z = zipfile.ZipFile(apk)
    r = Reader(z.read(member))
    r.parse()
    print('=== %s : protos=%d ===' % (member, len(r.protos)))
    for i, pt in enumerate(r.protos[:max_protos]):
        strs = [s for s in pt.strings if not CLS.match(s)]
        cls = [s for s in pt.strings if CLS.match(s)]
        print('--- #%d bc=%d kgc=%d params=%d flags=0x%02x' %
              (i, len(pt.bc), len(pt.kgc), pt.numparams, pt.flags))
        if cls:
            print('    class :', ', '.join(cls))
        if strs:
            print('    strings:', ', '.join(repr(s) for s in strs))
        if show_tables and pt.tables:
            for t in pt.tables:
                print('    table :', fmt(t, 0, 4))


if __name__ == '__main__':
    main()