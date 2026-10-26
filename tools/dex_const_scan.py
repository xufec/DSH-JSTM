#!/usr/bin/env python3
"""Fast byte-pattern scan for const-string references to given DEX string ids.

const-string is `1A <reg8> <idx16>`: the first code unit's low byte is 0x1A and
the string index sits in the *next* 16-bit unit. Scanning the raw bytes for that
word is O(n) with a tight loop — seconds instead of minutes.

usage:
  python tools/dex_const_scan.py 54570 55320 54706
"""
import os
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


def dstr(d, soff, i, n_strings):
    if i < 0 or i >= n_strings:
        return '?'
    off = struct.unpack_from('<I', d, soff + i * 4)[0]
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
        out.append(chr(cp)); units += 1
    return ''.join(out)


class Dex:
    def __init__(self, d):
        self.d = d
        self.ssize, self.soff = struct.unpack_from('<II', d, 56)
        self.tsize, self.toff = struct.unpack_from('<II', d, 64)
        self.msize, self.moff = struct.unpack_from('<II', d, 88)
        self.csize, self.coff = struct.unpack_from('<II', d, 96)

    def tname(self, i):
        if i < 0 or i >= self.tsize:
            return '?'
        s = struct.unpack_from('<I', self.d, self.toff + i * 4)[0]
        return dstr(self.d, self.soff, s, self.ssize)

    def mname(self, i):
        if i < 0 or i >= self.msize:
            return '?', '?'
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, self.moff + i * 8)
        return self.tname(cidx), dstr(self.d, self.soff, nidx, self.ssize)

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
    targets = set(int(a, 0) for a in sys.argv[1:]) or {54570}
    d = zipfile.ZipFile(APK).read('classes.dex')
    dx = Dex(d)

    # 1) locate raw byte patterns: 0x1A in low byte, index in next unit
    positions = []
    for t in targets:
        pat = struct.pack('<H', t)
        start = 0
        while True:
            i = d.find(pat, start)
            if i < 0:
                break
            # preceding code unit must have low byte 0x1A (const-string) or 0x1B
            if i >= 2:
                prev = d[i - 2] | (d[i - 1] << 8)
                if (prev & 0xFF) == 0x1A:
                    positions.append((i, t))
            start = i + 1
    print('const-string hits:', len(positions), 'for ids', sorted(targets))

    # 2) map position -> owning method by locating the containing code_item
    owner_of = {}
    for ci in range(dx.csize):
        off = dx.coff + ci * 32
        cidx = struct.unpack_from('<I', d, off)[0]
        cls_off = struct.unpack_from('<I', d, off + 24)[0]
        if not cls_off:
            continue
        cname = dx.tname(cidx)
        try:
            for midx, coff in dx.methods_of(cls_off):
                n = struct.unpack_from('<I', d, coff + 12)[0]
                owner_of[coff] = (coff, coff + 16 + n * 2, cname, midx)
        except Exception:
            continue

    starts = sorted(owner_of)
    import bisect
    counts = {}
    for pos, t in positions:
        k = bisect.bisect_right(starts, pos) - 1
        if k < 0:
            continue
        coff, end, cname, midx = owner_of[starts[k]]
        if pos >= end:
            continue
        owner, mn = dx.mname(midx)
        counts[(owner, mn, t)] = counts.get((owner, mn, t), 0) + 1
    for (owner, mn, t), c in sorted(counts.items()):
        print('  %-56s %-24s id=%d x%d' % (owner, mn, t, c))
    print('owners:', len(counts))
    return 0


if __name__ == '__main__':
    sys.exit(main())
