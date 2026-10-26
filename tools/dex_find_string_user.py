#!/usr/bin/env python3
"""Find which DEX method references given string(s) via const-string.

Fast path for "who shows this dialog": const-string (0x1A) and
const-string/jumbo (0x1B) carry a string index in the following code unit.

usage:
  python tools/dex_find_string_user.py 初始化失败
  python tools/dex_find_string_user.py --class cn/ewan 初始化失败
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
WIDTH = {0x1A: 2, 0x1B: 3}


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


class Dex:
    def __init__(self, d):
        self.d = d
        for nm, off in (('string_ids', 56), ('type_ids', 64), ('method_ids', 88),
                        ('class_defs', 96)):
            s, o = struct.unpack_from('<II', d, off)
            setattr(self, nm + '_size', s)
            setattr(self, nm + '_off', o)

    def string(self, i):
        if not (0 <= i < self.string_ids_size):
            return '?'
        off = struct.unpack_from('<I', self.d, self.string_ids_off + i * 4)[0]
        n, p = uleb(self.d, off)
        return self.d[p:p + n].decode('utf-8', 'replace')

    def type_name(self, i):
        if not (0 <= i < self.type_ids_size):
            return '?'
        return self.string(struct.unpack_from('<I', self.d, self.type_ids_off + i * 4)[0])

    def method_parts(self, i):
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, self.method_ids_off + i * 8)
        return self.type_name(cidx), self.string(nidx)

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
    cls_filter = ''
    if '--class' in args:
        i = args.index('--class')
        cls_filter = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 2
    terms = args

    d = zipfile.ZipFile(APK).read('classes.dex')
    dex = Dex(d)

    targets = {i: dex.string(i) for i in range(dex.string_ids_size)
               if any(t in dex.string(i) for t in terms)}
    print('target strings:', list(targets.items())[:8], '... total', len(targets))
    if not targets:
        return 1

    hits = 0
    for ci in range(dex.class_defs_size):
        off = dex.class_defs_off + ci * 32
        cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', d, off)
        cname = dex.type_name(cidx)
        if cls_filter and cls_filter not in cname:
            continue
        if not cls_off:
            continue
        try:
            ms = dex.methods_of(cls_off)
        except Exception:
            continue
        for midx, coff in ms:
            insns = struct.unpack_from('<I', d, coff + 12)[0]
            start = coff + 16
            p = start
            end = start + insns * 2
            found = False
            while p + 2 <= end:
                w0 = d[p] | (d[p + 1] << 8)
                op = w0 & 0xFF
                if op == 0x1A and p + 4 <= end:
                    sidx = d[p + 2] | (d[p + 3] << 8)
                    if sidx in targets:
                        found = True
                        break
                    p += 4
                    continue
                if op == 0x1B and p + 6 <= end:
                    sidx = struct.unpack_from('<I', d, p + 2)[0]
                    if sidx in targets:
                        found = True
                        break
                    p += 6
                    continue
                # width table for the rest
                from collections import defaultdict
                p += 2 * _width(op)
            if found:
                owner, mname = dex.method_parts(midx)
                print('  %s->%s' % (owner, mname))
                hits += 1
    print('methods referencing the string:', hits)
    return 0


_W = None


def _width(op):
    """instruction width in code units (see dex spec table)."""
    global _W
    if _W is None:
        _W = {}
        one = set(range(0x01, 0x0D)) | set(range(0x12, 0x1D)) | set(range(0x1E, 0x22)) | \
            {0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43} | \
            set(range(0x73, 0x79)) | set(range(0x7B, 0x90)) | set(range(0xB0, 0xD0)) | \
            {0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF, 0x00}
        two = {0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x1D, 0x22, 0x23, 0x2D, 0x2E, 0x2F, 0x30, 0x31,
               0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D} | \
              set(range(0x44, 0x6E)) | {0x79, 0x7A} | set(range(0x90, 0xB0)) | \
              set(range(0xD0, 0xE3))
        three = {0x24, 0x25, 0x26, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x1B}
        for o in one:
            _W[o] = 1
        for o in two:
            _W[o] = 2
        for o in three:
            _W[o] = 3
    return _W.get(op, 1)


if __name__ == '__main__':
    sys.exit(main())
