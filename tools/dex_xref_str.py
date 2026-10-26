#!/usr/bin/env python3
"""Find which class/method const-strings given DEX string ids (MUTF-8 aware).

usage:
  python tools/dex_xref_str.py 54570
  python tools/dex_xref_str.py --menu        # 初始化失败 / 退出游戏 ids
"""
import os
import re
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


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


def dex_str(d, soff, i):
    # guard: valid string ids only (a bad delta in class_data would otherwise
    # read past EOF and raise IndexError/struct.error mid-scan)
    if i < 0 or soff + i * 4 + 4 > len(d):
        return '?'
    off = struct.unpack_from('<I', d, soff + i * 4)[0]
    if off <= 0 or off >= len(d):
        return '?'
    n, p = uleb(d, off)
    units = 0
    out = []
    while units < n and p < len(d):
        b0 = d[p]
        if b0 == 0:
            break
        if b0 < 0x80:
            cp = b0; p += 1
        elif b0 & 0xE0 == 0xC0:
            cp = ((b0 & 0x1F) << 6) | (d[p + 1] & 0x3F); p += 2
        elif b0 & 0xF0 == 0xE0:
            cp = ((b0 & 0x0F) << 12) | ((d[p + 1] & 0x3F) << 6) | (d[p + 2] & 0x3F); p += 3
        else:
            cp = ord('?'); p += 1
        out.append(chr(cp))
        units += 1
    return ''.join(out)


class Dex:
    def __init__(self, d):
        self.d = d
        self.ssize, self.soff = struct.unpack_from('<II', d, 56)
        self.tsize, self.toff = struct.unpack_from('<II', d, 64)
        self.msize, self.moff = struct.unpack_from('<II', d, 88)
        self.csize, self.coff = struct.unpack_from('<II', d, 96)

    def tname(self, i):
        s = struct.unpack_from('<I', self.d, self.toff + i * 4)[0]
        return dex_str(self.d, self.soff, s)

    def mname(self, i):
        if i < 0 or self.moff + i * 8 + 8 > len(self.d):
            return '?', '?'
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, self.moff + i * 8)
        return self.tname(cidx), dex_str(self.d, self.soff, nidx)

    def methods_of(self, cls_off):
        d = self.d
        _, p = uleb(d, cls_off)
        _, p = uleb(d, p)
        nd, p = uleb(d, p)
        nv, p = uleb(d, p)
        out = []
        idx = 0
        for _ in range(nd + nv):
            diff, p = uleb(d, p)
            idx += diff
            _, p = uleb(d, p)
            coff, p = uleb(d, p)
            if coff:
                out.append((idx, coff))
        return out


def main():
    args = sys.argv[1:]
    if '--menu' in args:
        args = [a for a in args if a != '--menu']
        args += ['54570', '55320', '54706']
    targets = set(int(a) for a in args)
    d = zipfile.ZipFile(APK).read('classes.dex')
    dx = Dex(d)

    for t in sorted(targets):
        print('target %d = %r' % (t, dex_str(d, dx.soff, t)))

    hits = {}
    for ci in range(dx.csize):
        off = dx.coff + ci * 32
        cidx = struct.unpack_from('<I', d, off)[0]
        cls_off = struct.unpack_from('<I', d, off + 24)[0]
        cname = dx.tname(cidx)
        if not cls_off:
            continue
        try:
            ms = dx.methods_of(cls_off)
        except Exception:
            continue
        for midx, coff in ms:
            n = struct.unpack_from('<I', d, coff + 12)[0]
            p = coff + 16
            end = p + n * 2
            while p + 2 <= end and p + 1 < len(d):
                w = d[p] | (d[p + 1] << 8)
                op = w & 0xFF
                if op == 0x1A:
                    sidx = d[p + 2] | (d[p + 3] << 8)
                    if sidx in targets:
                        owner, mn = dx.mname(midx)
                        hits.setdefault((owner, mn), set()).add(sidx)
                if op == 0x1B and p + 6 <= end:
                    sidx = struct.unpack_from('<I', d, p + 2)[0]
                    if sidx in targets:
                        owner, mn = dx.mname(midx)
                        hits.setdefault((owner, mn), set()).add(sidx)
                # advance using width table (reuse simple approximation)
                p += 2 * _w(op)
    for (owner, mn), s in sorted(hits.items()):
        print('  %-58s %-24s ids=%s' % (owner, mn, sorted(s)))
    print('methods:', len(hits))
    return 0


_W1 = set(range(0x01, 0x0D)) | set(range(0x12, 0x1D)) | set(range(0x1E, 0x22)) | \
    {0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43} | \
    set(range(0x73, 0x79)) | set(range(0x7B, 0x90)) | set(range(0xB0, 0xD0)) | \
    {0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF}
_W3 = {0x24, 0x25, 0x26, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x1B}


def _w(op):
    if op in _W3:
        return 3
    if op in _W1 or op == 0:
        return 1
    return 2


if __name__ == '__main__':
    sys.exit(main())
