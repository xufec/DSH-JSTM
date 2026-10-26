#!/usr/bin/env python3
"""Search every .luac in an APK for a substring and print the owning file.

Handles this client's GBK-encoded Chinese string constants.

usage:
  python tools/find_luac_text.py 初始化失败
  python tools/find_luac_text.py --all          # list candidate files for known terms
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import parse_bytes  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def raw(s):
    """LuaJIT constant -> original bytes."""
    return s.encode('latin1', 'replace') if isinstance(s, str) else s


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    terms = [t.encode('gbk', 'replace') for t in args]
    if not terms:
        print(__doc__)
        return 2
    z = zipfile.ZipFile(APK)
    total = 0
    for n in z.namelist():
        if not n.endswith('.luac'):
            continue
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        found = {}
        for pt in r.protos:
            for s in pt.strings:
                b = raw(s)
                for t in terms:
                    if t in b:
                        found[b] = None
        if found:
            total += 1
            print('==== %s' % n)
            for b in list(found)[:8]:
                print('   ', b.decode('gbk', 'replace')[:110])
    print('files matched:', total)
    return 0


if __name__ == '__main__':
    sys.exit(main())
