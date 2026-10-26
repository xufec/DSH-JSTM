#!/usr/bin/env python3
"""Extract UTF-8 and ASCII strings from an APK member around a byte offset.

usage:
  python tools/dex_around.py classes.dex 1648899 2000
"""
import sys
import zipfile

APK = r'anzbao\jstm_142165.apk'


def main():
    member = sys.argv[1] if len(sys.argv) > 1 else 'classes.dex'
    off = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    span = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
    d = zipfile.ZipFile(APK).read(member)
    chunk = d[max(0, off - span):off + span]
    out = []
    cur = bytearray()
    for b in chunk:
        if 0x20 <= b < 0x7f:
            cur.append(b)
        else:
            if len(cur) >= 5:
                out.append(cur.decode('ascii'))
            cur = bytearray()
    if len(cur) >= 5:
        out.append(cur.decode('ascii'))
    for s in out:
        print(s[:160])


if __name__ == '__main__':
    main()
