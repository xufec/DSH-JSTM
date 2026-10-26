#!/usr/bin/env python3
"""Locate the DEX string(s) containing the SDK init-failure dialog text and
report which methods const-string them.

The term is embedded in this file (UTF-8 source), so it never touches a
GBK console argument path.
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')

TERMS = ['初始化失败', '请检查网络', '重新连接', '退出游戏']


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


W3 = {0x24, 0x25, 0x26, 0x6E, 0x6F, 0x70, 0x71, 0x72, 0x1B}
W1 = set(range(0x01, 0x0D)) | set(range(0x12, 0x1D)) | set(range(0x1E, 0x22)) | \
    {0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43} | \
    set(range(0x73, 0x79)) | set(range(0x7B, 0x90)) | set(range(0xB0, 0xD0)) | \
    {0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF}


def width(op):
    if op in W3:
        return 3
    if op in W1 or op == 0:
        return 1
    return 2


def main():
    d = zipfile.ZipFile(APK).read('classes.dex')
    dex = Dex(d)
    targets = {}
    for i in range(dex.string_ids_size):
        s = dex.string(i)
        for t in TERMS:
            if t in s:
                targets[i] = (t, s)
    print('string ids:', {k: v[0] for k, v in targets.items()})
    if not targets:
        return 1

    hits = {}
    for ci in range(dex.class_defs_size):
        off = dex.class_defs_off + ci * 32
        cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', d, off)
        cname = dex.type_name(cidx)
        if not cls_off:
            continue
        if not (cname.startswith('Lcn/ewan') or cname.startswith('Lcom/example/supersdk200')
                or 'shiyue' in cname or 'cocos2dx' in cname):
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
                if sidx in targets:
                    owner, mname = dex.method_parts(midx)
                    key = (owner, mname, targets[sidx][0])
                    hits[key] = hits.get(key, 0) + 1
                p += 2 * width(op)
    for (owner, mname, term), c in sorted(hits.items()):
        print('  %-58s %-22s  uses %r x%d' % (owner, mname, term, c))
    print('methods:', len(hits))
    return 0


if __name__ == '__main__':
    sys.exit(main())
