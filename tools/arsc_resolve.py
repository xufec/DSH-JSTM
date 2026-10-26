#!/usr/bin/env python3
"""Find a string in the global ARSC pool and resolve it to a resource id + type/entry.

Minimal ARSC walker: locates the entry whose value data points at the target
global string, which gives us the resource id (package/type/entry) — enough to
find the owning layout/class in the dex.

usage:
  python tools/arsc_resolve.py 初始化失败
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
RES_STRING_POOL = 0x0001
RES_TABLE_PACKAGE = 0x0200
RES_TABLE_TYPE = 0x0201


def read_pool(d, off):
    typ, hsz, sz = struct.unpack_from('<HHI', d, off)
    assert typ == RES_STRING_POOL
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
    return out


def main():
    term = sys.argv[1] if len(sys.argv) > 1 else '初始化失败'
    d = zipfile.ZipFile(APK).read('resources.arsc')
    typ, hsz, sz = struct.unpack_from('<HHI', d, 0)
    pool = read_pool(d, hsz)
    targets = {i for i, s in enumerate(pool) if term in s}
    print('global pool hits:', {i: pool[i] for i in targets})

    pos = hsz
    while pos + 8 <= len(d):
        ctyp, chsz, csz = struct.unpack_from('<HHI', d, pos)
        if csz <= 0:
            break
        if ctyp == RES_TABLE_PACKAGE:
            pkg_id = struct.unpack_from('<I', d, pos + 8)[0]
            name_off = struct.unpack_from('<I', d, pos + 12)[0]
            try:
                pkg_name = d[pos + name_off:pos + name_off + 128].decode('utf-16-le').split('\x00')[0]
            except Exception:
                pkg_name = '?'
            p2 = pos + chsz
            while p2 + 8 <= pos + csz:
                t2, h2, s2 = struct.unpack_from('<HHI', d, p2)
                if s2 <= 0:
                    break
                if t2 == RES_TABLE_TYPE:
                    tid = d[p2 + 8]
                    entry_count = struct.unpack_from('<I', d, p2 + 12)[0]
                    entries_start = struct.unpack_from('<I', d, p2 + 16)[0]
                    ebase = p2 + entries_start
                    for e in range(entry_count):
                        eoff = struct.unpack_from('<I', d, ebase + e * 4)[0]
                        if eoff == 0xFFFFFFFF:
                            continue
                        ep = ebase + eoff
                        esz, eflags, ekey = struct.unpack_from('<HHI', d, ep)
                        if eflags & 1:
                            continue
                        valoff = ep + esz
                        vsize, vres0, vtype = struct.unpack_from('<HBB', d, valoff)
                        vdata = struct.unpack_from('<I', d, valoff + 4)[0]
                        if vtype == 0x03 and vdata in targets:
                            rid = (pkg_id << 24) | (tid << 16) | e
                            print('  RES 0x%08x  pkg=%s type=0x%02x entry=0x%04x  -> %r'
                                  % (rid, pkg_name, tid, e, pool[vdata]))
                p2 += s2
        pos += csz
    return 0


if __name__ == '__main__':
    sys.exit(main())
