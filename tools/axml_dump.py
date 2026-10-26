#!/usr/bin/env python3
"""Minimal Android binary XML (AXML) decoder — enough to read AndroidManifest.xml.

Why: the APK's manifest is binary XML. We need to know which activity is the
launcher (and which one initialises the ewan SDK) to make the standalone build
safe, and pulling a whole apktool for one manifest is overkill.

usage:
  python tools/axml_dump.py                       # dump AndroidManifest.xml
  python tools/axml_dump.py <member-in-apk>
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')

# resource id -> attribute name (only the ones we care about)
ATTRS = {
    0x0101021B: 'versionCode', 0x0101021C: 'versionName',
    0x01010003: 'name', 0x01010000: 'theme', 0x01010001: 'label',
    0x01010002: 'icon', 0x01010010: 'exported', 0x01010018: 'authorities',
    0x0101001D: 'targetActivity', 0x0101001E: 'launchMode',
    0x0101020C: 'minSdkVersion', 0x01010270: 'targetSdkVersion',
    0x0101021D: 'sharedUserId', 0x010102B0: 'usesCleartextTraffic',
    0x01010271: 'maxSdkVersion', 0x0101032F: 'debuggable',
}


class Reader:
    def __init__(self, d):
        self.d = d
        self.strings = []
        self.p = 0

    def u16(self, off=None):
        return struct.unpack_from('<H', self.d, self.p if off is None else off)[0]

    def u32(self, off=None):
        return struct.unpack_from('<I', self.d, self.p if off is None else off)[0]

    def parse_pool(self, off):
        typ, hsz, sz = struct.unpack_from('<HHI', self.d, off)
        assert typ == 0x0001, 'not a string pool (got 0x%04x at %d)' % (typ, off)
        count, style_count, flags, str_start = struct.unpack_from('<IIII', self.d, off + 8)
        offsets = struct.unpack_from('<%dI' % count, self.d, off + 28)
        utf8 = bool(flags & (1 << 8))
        base = off + str_start
        out = []
        for o in offsets:
            p = base + o
            if utf8:
                # varint utf16 length, then varint byte length
                n1 = self.d[p]
                p += 1
                if n1 & 0x80:
                    p += 1
                n = self.d[p]
                p += 1
                if n & 0x80:
                    n = ((n & 0x7F) << 8) | self.d[p]
                    p += 1
                out.append(self.d[p:p + n].decode('utf-8', 'replace'))
            else:
                n = struct.unpack_from('<H', self.d, p)[0]
                p += 2
                if n & 0x8000:
                    n = ((n & 0x7FFF) << 16) | struct.unpack_from('<H', self.d, p)[0]
                    p += 2
                out.append(self.d[p:p + n * 2].decode('utf-16-le', 'replace'))
        self.strings = out
        return out

    def dump(self):
        d = self.d
        typ, hsz, sz = struct.unpack_from('<HHI', d, 0)
        assert typ == 0x0003, 'not binary XML'
        # AXML header is 8 bytes; the string pool chunk starts immediately after,
        # so parse it at offset 8 (there is no separate offset field here).
        self.parse_pool(8)
        def s(i):
            return self.strings[i] if 0 <= i < len(self.strings) else '?'

        pos = hsz
        depth = 0
        while pos < len(d):
            typ, hsz2, sz2 = struct.unpack_from('<HHI', d, pos)
            if typ == 0x0102:  # START_ELEMENT
                ns, name = struct.unpack_from('<ii', d, pos + 16)
                attr_start, attr_size, attr_count = struct.unpack_from('<HHH', d, pos + 24)
                line = ['  ' * depth + '<' + s(name)]
                for i in range(attr_count):
                    ao = pos + 16 + attr_start + i * attr_size
                    ans, anm, araw, atype, adata = struct.unpack_from('<iiiII', d, ao)
                    key = ATTRS.get(anm, 'attr_%08x' % anm)
                    if atype == 0x03:
                        val = s(araw) if araw >= 0 else s(adata)
                    elif atype == 0x12:
                        val = 'true' if adata else 'false'
                    elif atype == 0x10:
                        val = str(adata)
                    else:
                        val = s(araw) if araw >= 0 else str(adata)
                    if key == 'name' or key in ('exported', 'authorities', 'launchMode',
                                                'targetSdkVersion', 'minSdkVersion',
                                                'usesCleartextTraffic', 'versionName',
                                                'versionCode', 'theme', 'label',
                                                'debuggable'):
                        line.append('%s=%r' % (key, val))
                print(' '.join(line) + '>')
                depth += 1
            elif typ == 0x0103:  # END_ELEMENT
                depth -= 1
                ns, name = struct.unpack_from('<ii', d, pos + 16)
                print('  ' * depth + '</' + s(name) + '>')
            pos += sz2
            if sz2 == 0:
                break


def main():
    member = sys.argv[1] if len(sys.argv) > 1 else 'AndroidManifest.xml'
    Reader(zipfile.ZipFile(APK).read(member)).dump()


if __name__ == '__main__':
    main()
