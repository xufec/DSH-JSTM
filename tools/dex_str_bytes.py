#!/usr/bin/env python3
"""Find DEX methods that const-string a *specific byte sequence*.

Arguments are matched as bytes (UTF-8 of the literal), so Chinese text survives
a GBK console. Then const-string/const-string-jumbo targets the resolved string
indices and reports the owning class->method.

usage:
  python tools/dex_str_bytes.py <utf8-literal>
  python tools/dex_str_bytes.py --class cn/ewan <utf8-literal>
"""
import struct
import sys
import zipfile
import os

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


class Dex:
    def __init__(self, d):
        self.d = d
        for nm, off in (('string_ids', 56), ('type_ids', 64), ('method_ids', 88),
                        ('class_defs', 96)):
            s, o = struct.unpack_from('<II', d, off)
            setattr(self, nm + '_size', s)
            setattr(self, nm + '_off', o)

    def string(self, i):
        off = struct.unpack_from('<I', self.d, self.string_ids_off + i * 4)[0]
        n, p = uleb(self.d, off)
        return self.d[p:p + n].decode('utf-8', 'replace')

    def string_off(self, i):
        return struct.unpack_from('<I', self.d, self.string_ids_off + i * 4)[0]

    def type_name(self, i):
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


W1 = set(range(0x01, 0x0D)) | set(range(0x12, 0x1D)) | set(range(0x1E, 0x22)) | \
    {0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43} | \
    set(range(0x73, 0x79)) | set(range(0x7B, 0x90)) | set(range(0xB0, 0xD0)) | \
    {0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF}
W3 = {0x24, 0x25, 0x26, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x1B}


def width(op):
    if op in W3:
        return 3
    if op in W1:
        return 1
    if op == 0x00:
        return 1
    return 2


def main():
    args = sys.argv[1:]
    cf = ''
    if '--class' in args:
        i = args.index('--class')
        cf = args[i + 1]
        del args[i:i + 2]
    term = args[0].encode('utf-8') if args else b''
    d = zipfile.ZipFile(APK).read('classes.dex')
    dex = Dex(d)

    targets = set()
    for i in range(dex.string_ids_size):
        try:
            if term in dex.string(i).encode('utf-8', 'replace'):
                targets.add(i)
        except Exception:
            pass
    print('matching string ids:', sorted(targets)[:10], 'total', len(targets))
    if not targets:
        return 1

    hits = 0
    for ci in range(dex.class_defs_size):
        off = dex.class_defs_off + ci * 32
        cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', d, off)
        cname = dex.type_name(cidx)
        if cf and cf not in cname:
            continue
        if not cls_off:
            continue
        try:
            ms = dex.methods_of(cls_off)
        except Exception:
            continue
        for midx, coff in ms:
            n = struct.unpack_from('<I', d, coff + 12)[0]
            p = coff + 16
            end = p + n * 2
            while p + 2 <= end:
                w0 = d[p] | (d[p + 1] << 8)
                op = w0 & 0xFF
                sidx = None
                if op == 0x1A and p + 4 <= end:
                    sidx = d[p + 2] | (d[p + 3] << 8)
                elif op == 0x1B and p + 6 <= end:
                    sidx = struct.unpack_from('<I', d, p + 2)[0]
                if sidx is not None and sidx in targets:
                    owner, mname = dex.method_parts(midx)
                    print('  %s->%s' % (owner, mname))
                    hits += 1
                    break
                p += 2 * width(op)
    print('methods:', hits)
    return 0


if __name__ == '__main__':
    sys.exit(main())
