#!/usr/bin/env python3
"""Find which resource id owns a string in resources.arsc (minimal ARSC reader).

We need to know whether the "初始化失败" dialog is the game's own string or an
SDK string resource, and which one, before touching the dex.

usage:
  python tools/arsc_find.py 初始化失败
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
RES_STRING_POOL = 0x0001
RES_TABLE = 0x0002
RES_TABLE_PACKAGE = 0x0200
RES_TABLE_TYPE = 0x0201
RES_TABLE_TYPE_SPEC = 0x0202


def read_pool(d, off):
    typ, hsz, sz = struct.unpack_from('<HHI', d, off)
    assert typ == RES_STRING_POOL, 'expected string pool, got 0x%04x' % typ
    count, style_count, flags, str_start = struct.unpack_from('<IIII', d, off + 8)
    offsets = struct.unpack_from('<%dI' % count, d, off + 28)
    utf8 = bool(flags & (1 << 8))
    base = off + str_start
    out = []
    for o in offsets:
        p = base + o
        if utf8:
            n1 = d[p]; p += 1
            if n1 & 0x80: p += 1
            n = d[p]; p += 1
            if n & 0x80:
                n = ((n & 0x7F) << 8) | d[p]; p += 1
            out.append(d[p:p + n].decode('utf-8', 'replace'))
        else:
            n = struct.unpack_from('<H', d, p)[0]; p += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from('<H', d, p)[0]; p += 2
            out.append(d[p:p + n * 2].decode('utf-16-le', 'replace'))
    return out, sz


def main():
    terms = sys.argv[1:] or ['初始化失败']
    terms_b = [t.encode('utf-8') for t in terms]
    d = zipfile.ZipFile(APK).read('resources.arsc')
    print('arsc bytes:', len(d))
    typ, hsz, sz = struct.unpack_from('<HHI', d, 0)
    pool, _ = read_pool(d, hsz)
    print('global strings:', len(pool))
    hits = [(i, s) for i, s in enumerate(pool)
            if any(t in s.encode('utf-8', 'replace') for t in terms_b)]
    for i, s in hits[:20]:
        print('  global[%d] = %r' % (i, s[:80]))

    # walk packages/types looking for the value in the type pool
    pos = hsz
    while pos + 8 <= len(d):
        ctyp, chsz, csz = struct.unpack_from('<HHI', d, pos)
        if csz <= 0:
            break
        if ctyp == RES_TABLE_PACKAGE:
            pkg_id = struct.unpack_from('<I', d, pos + 8)[0]
            name_off = struct.unpack_from('<I', d, pos + 12)[0]
            try:
                pkg_name = d[pos + name_off:pos + name_off + 64].decode('utf-16-le').split('\x00')[0]
            except Exception:
                pkg_name = '?'
            p2 = pos + chsz
            while p2 + 8 <= pos + csz:
                t2, h2, s2 = struct.unpack_from('<HHI', d, p2)
                if s2 <= 0:
                    break
                if t2 == RES_TABLE_TYPE:
                    tid = d[p2 + 8]
                    try:
                        tpool, _s = read_pool(d, p2 + h2)
                    except Exception:
                        tpool = []
                    for i, s in enumerate(tpool):
                        if any(t in s.encode('utf-8', 'replace') for t in terms_b):
                            print('  pkg=%s(0x%02x) type=0x%02x entry_string[%d] = %r'
                                  % (pkg_name, pkg_id, tid, i, s[:80]))
                p2 += s2
        pos += csz
    return 0


if __name__ == '__main__':
    sys.exit(main())
