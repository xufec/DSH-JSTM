#!/usr/bin/env python3
"""Dump an APK's AndroidManifest.xml fully (attributes + values) using AXML parsing.

Fixed string-pool handling: AXML in this APK uses UTF-16 pools, and attribute
values can be string refs, resource ids, or typed ints/bools.

usage:
  python tools/manifest_dump.py [member]
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
ATTRS = {
    0x01010003: 'name', 0x01010000: 'theme', 0x01010001: 'label', 0x01010002: 'icon',
    0x01010010: 'exported', 0x01010018: 'authorities', 0x0101001D: 'targetActivity',
    0x0101001E: 'launchMode', 0x0101020C: 'minSdkVersion', 0x01010270: 'targetSdkVersion',
    0x0101021B: 'versionCode', 0x0101021C: 'versionName', 0x010102B0: 'usesCleartextTraffic',
    0x0101032F: 'debuggable', 0x0101001C: 'configChanges', 0x0101001F: 'screenOrientation',
    0x0101021E: 'process', 0x0101000E: 'permission',
}


def read_pool(d, off):
    typ, hsz, sz = struct.unpack_from('<HHI', d, off)
    assert typ == 1, 'not a string pool: 0x%04x' % typ
    count, style_count, flags, str_start = struct.unpack_from('<IIII', d, off + 8)
    offs = struct.unpack_from('<%dI' % count, d, off + 28)
    utf8 = bool(flags & (1 << 8))
    base = off + str_start
    out = []
    for o in offs:
        p = base + o
        if utf8:
            n = d[p]; p += 1
            if n & 0x80:
                n = ((n & 0x7F) << 8) | d[p]; p += 1
            n2 = d[p]; p += 1
            if n2 & 0x80:
                n2 = ((n2 & 0x7F) << 8) | d[p]; p += 1
            out.append(d[p:p + n2].decode('utf-8', 'replace'))
        else:
            n = struct.unpack_from('<H', d, p)[0]; p += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from('<H', d, p)[0]; p += 2
            out.append(d[p:p + n * 2].decode('utf-16-le', 'replace'))
    return out


def main():
    member = sys.argv[1] if len(sys.argv) > 1 else 'AndroidManifest.xml'
    d = zipfile.ZipFile(APK).read(member)
    strings = read_pool(d, 8)

    pos = 8
    while pos + 8 <= len(d):
        typ, hsz, sz = struct.unpack_from('<HHI', d, pos)
        if typ == 0x0102:      # START_ELEMENT
            ns, name = struct.unpack_from('<ii', d, pos + 16)
            attr_start, attr_size, attr_count = struct.unpack_from('<HHH', d, pos + 24)
            attrs = []
            for i in range(attr_count):
                ao = pos + 16 + attr_start + i * attr_size
                ans, anm, araw, atype, adata = struct.unpack_from('<iiiII', d, ao)
                key = ATTRS.get(anm)
                if key is None:
                    # fall back to the attribute-name string in the pool
                    key = strings[anm] if 0 <= anm < len(strings) else ('attr_%08x' % anm)
                if atype == 0x03:
                    val = strings[adata] if 0 <= adata < len(strings) else '?'
                elif atype == 0x12:
                    val = 'true' if adata else 'false'
                elif atype == 0x10:
                    val = str(adata)
                elif atype == 0x01:
                    val = '0x%08x' % adata
                else:
                    val = strings[araw] if 0 <= araw < len(strings) else str(adata)
                attrs.append('%s=%s' % (key, val))
            nm = strings[name] if 0 <= name < len(strings) else '?'
            print('<%s %s>' % (nm, ' '.join(attrs)))
        pos += sz
        if sz == 0:
            break
    return 0


if __name__ == '__main__':
    sys.exit(main())
