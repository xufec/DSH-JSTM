#!/usr/bin/env python3
"""Validate tools/luajit_bc.py against every .luac inside the game APK."""
import sys, os, zipfile, re, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import Reader, BCError, TableConst, ChildRef


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    z = zipfile.ZipFile(apk)
    names = sorted(n for n in z.namelist() if n.endswith('.luac'))
    print('luac files:', len(names))
    ok = 0
    fails = []
    nproto = 0
    nstr = 0
    ntab = 0
    ver = collections.Counter()
    for n in names:
        data = z.read(n)
        try:
            r = Reader(data)
            r.parse()
            ok += 1
            nproto += len(r.protos)
            ver[(r.version, r.flags)] += 1
            for pt in r.protos:
                for c in pt.kgc:
                    if isinstance(c, str):
                        nstr += 1
                    elif isinstance(c, TableConst):
                        ntab += 1
        except BCError as e:
            fails.append((n, str(e)))
        except Exception as e:
            fails.append((n, '%s: %s' % (type(e).__name__, e)))
    print('parsed OK   : %d / %d  (%.2f%%)' % (ok, len(names), 100.0 * ok / max(1, len(names))))
    print('prototypes  : %d' % nproto)
    print('string consts: %d   table consts: %d' % (nstr, ntab))
    print('version/flags seen:', dict(ver))
    if fails:
        print('failures: %d' % len(fails))
        for n, e in fails[:20]:
            print('   ', n, '->', e)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())