#!/usr/bin/env python3
"""Byte-level search across APK members (dex, .so, assets) for a GBK/ASCII phrase.

The earlier string-pool search missed the SDK/Java side, so this scans raw bytes.

usage:
  python tools/find_apk_text.py 初始化失败
"""
import os
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def main():
    terms = [t.encode('gbk', 'replace') for t in sys.argv[1:]]
    ascii_terms = [t.encode('utf-8', 'replace') for t in sys.argv[1:]]
    if not terms:
        print(__doc__)
        return 2
    z = zipfile.ZipFile(APK)
    for n in z.namelist():
        if n.endswith('/'):
            continue
        try:
            d = z.read(n)
        except Exception:
            continue
        hits = []
        for t in list(terms) + list(ascii_terms):
            p = d.find(t)
            if p >= 0:
                hits.append((t, p))
        if hits:
            print('==== %-60s %d bytes' % (n, len(d)))
            for t, p in hits[:4]:
                print('     at %d: %r' % (p, t[:40]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
