#!/usr/bin/env python3
"""Find the DEX string index for a literal, then report classes whose const-string
or code references that index.

The literal is embedded here (UTF-8) so a GBK console cannot mangle it.

usage:
  python tools/dex_find_exact.py
"""
import os
import re
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
LITERALS = [
    '初始化失败',
    '初始化失败！',
    '初始化失败,请检查网络',
    '请检查网络',
    '重新连接',
    '退出游戏',
]


def uleb(d, p):
    r = 0
    sh = 0
    while True:
        b = d[p]
        p += 1
        r |= (b & 0x7F) << sh
        if not (b & 0x80):
            return r, p
        sh += 7


def main():
    d = zipfile.ZipFile(APK).read('classes.dex')
    ssize, soff = struct.unpack_from('<II', d, 56)

    def dstr(i):
        """Decode a DEX string_item. The ULEB128 prefix counts UTF-16 code units
        (not bytes), and the payload is MUTF-8 — so we must walk sequences and
        stop after that many units (decoding `n` bytes truncates CJK text)."""
        off = struct.unpack_from('<I', d, soff + i * 4)[0]
        n, p = uleb(d, off)
        units = 0
        out = []
        while units < n and p < len(d):
            b0 = d[p]
            if b0 == 0:
                break
            try:
                if b0 < 0x80:
                    cp = b0
                    p += 1
                elif b0 & 0xE0 == 0xC0:
                    cp = ((b0 & 0x1F) << 6) | (d[p + 1] & 0x3F)
                    p += 2
                elif b0 & 0xF0 == 0xE0:
                    cp = ((b0 & 0x0F) << 12) | ((d[p + 1] & 0x3F) << 6) | (d[p + 2] & 0x3F)
                    p += 3
                elif b0 & 0xF8 == 0xF0:
                    cp = ((b0 & 0x07) << 18) | ((d[p + 1] & 0x3F) << 12) | \
                         ((d[p + 2] & 0x3F) << 6) | (d[p + 3] & 0x3F)
                    p += 4
                    out.append(chr(0xD800 + ((cp - 0x10000) >> 10)))
                    out.append(chr(0xDC00 + ((cp - 0x10000) & 0x3FF)))
                    units += 2
                    continue
                else:
                    p += 1
                    continue
            except IndexError:
                break
            out.append(chr(cp))
            units += 1
        return ''.join(out)

    print('string count:', ssize)
    idx = {}
    for i in range(ssize):
        s = dstr(i)
        for lit in LITERALS:
            if lit == s:
                idx.setdefault(lit, []).append(i)
    for lit in LITERALS:
        print('%-28r -> %s' % (lit, idx.get(lit, [])))

    # Any string merely *containing* the terms (catches concatenation sources)
    for lit in ('初始化失败', '请检查网络'):
        found = [(i, dstr(i)) for i in range(ssize) if lit in dstr(i)]
        print('\ncontains %r: %d' % (lit, len(found)))
        for i, s in found[:12]:
            print('   %6d %r' % (i, s[:80]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
