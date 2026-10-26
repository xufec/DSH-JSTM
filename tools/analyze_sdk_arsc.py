#!/usr/bin/env python3
"""Dump resources.arsc string-pool entries around a byte offset / by needle.

The blocking dialog's text ("初始化失败,请检查网络" / "重新连接" / "退出游戏") is
not a standalone literal anywhere in the APK, so we need the resource strings
that feed it and the resource ids that own them.

usage:
  python tools/analyze_sdk_arsc.py around <file_offset> [radius]
  python tools/analyze_sdk_arsc.py needle <\\uXXXX-escaped-needle>
  python tools/analyze_sdk_arsc.py block <start> <end>
  python tools/analyze_sdk_arsc.py all
"""
import os
import struct
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm_142165.apk')
RES_STRING_POOL = 0x0001
RES_TABLE = 0x0002
RES_TABLE_PACKAGE = 0x0200
RES_TABLE_TYPE = 0x0201


def unesc(s):
    return s.encode('ascii', 'surrogateescape').decode('unicode_escape')


def read_pool(d, off):
    typ, hsz, sz = struct.unpack_from('<HHI', d, off)
    if typ != RES_STRING_POOL:
        raise ValueError('not a string pool at %d (0x%04x)' % (off, typ))
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
            out.append((p, d[p:p + n].decode('utf-8', 'replace')))
        else:
            n = struct.unpack_from('<H', d, p)[0]; p += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from('<H', d, p)[0]; p += 2
            out.append((p, d[p:p + n * 2].decode('utf-16-le', 'replace')))
    return out, utf8


def collect(d):
    """-> list of (pool_kind, pool_off, [(data_off, text)])"""
    pools = []
    typ, hsz, sz = struct.unpack_from('<HHI', d, 0)
    gp, _ = read_pool(d, hsz)
    pools.append(('global', hsz, gp))
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
                        tp, _ = read_pool(d, p2 + h2)
                        pools.append(('pkg=%s(0x%02x) type=0x%02x' % (pkg_name, pkg_id, tid),
                                      p2 + h2, tp))
                    except Exception:
                        pass
                p2 += s2
        pos += csz
    return pools


def main():
    d = zipfile.ZipFile(APK).read('resources.arsc')
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    pools = collect(d)

    if cmd == 'all':
        for kind, poff, ents in pools:
            print('== pool %s @%d (%d strings)' % (kind, poff, len(ents)))
            for off, s in ents:
                if s:
                    print('   %7d %r' % (off, s))
        return 0

    if cmd == 'around':
        target = int(sys.argv[2])
        radius = int(sys.argv[3]) if len(sys.argv) > 3 else 200
        for kind, poff, ents in pools:
            for off, s in ents:
                if abs(off - target) <= radius:
                    print('   %s %7d %r' % (kind, off, s))
        return 0

    if cmd == 'block':
        lo, hi = int(sys.argv[2]), int(sys.argv[3])
        for kind, poff, ents in pools:
            for off, s in ents:
                if lo <= off <= hi:
                    print('   %s %7d %r' % (kind, off, s))
        return 0

    if cmd == 'needle':
        needles = [unesc(x) if '\\u' in x else x for x in sys.argv[2:]]
        for kind, poff, ents in pools:
            for off, s in ents:
                if any(n in s for n in needles):
                    print('   %s %7d %r' % (kind, off, s))
        return 0

    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
