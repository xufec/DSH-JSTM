#!/usr/bin/env python3
"""Locate invoke-kind references to a method id by scanning DEX code words.

Approach: invoke-kind instructions are `AAAA BBBB` where the second word is the
method index; the first word's low byte encodes the opcode and the low nibble of
the high byte encodes the argument-register count. We scan the whole data
section for the target method index at 2-byte alignment and validate the
preceding word, which is far cheaper than walking every class_data_item.

usage:
  python tools/dex_find_invoke.py <class-descriptor> <method-name>
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
INVOKE_OPS = {0x6E, 0x6F, 0x70, 0x71, 0x72}


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
        self.string_ids_size, self.string_ids_off = struct.unpack_from('<II', d, 56)
        self.type_ids_size, self.type_ids_off = struct.unpack_from('<II', d, 64)
        self.method_ids_size, self.method_ids_off = struct.unpack_from('<II', d, 88)
        self.class_defs_size, self.class_defs_off = struct.unpack_from('<II', d, 96)
        self.data_size, self.data_off = struct.unpack_from('<II', d, 104)

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
        return self.type_name(cidx), self.string(nidx), pidx

    def class_defs(self):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i * 32
            cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', self.d, off)
            yield self.type_name(cidx), cls_off


def class_methods(dex, cls_off):
    d = dex.d
    _, p = uleb(d, cls_off)
    _, p = uleb(d, p)
    direct, p = uleb(d, p)
    virtual, p = uleb(d, p)
    out = []
    for _ in range(direct + virtual):
        midx, p = uleb(d, p)
        _, p = uleb(d, p)
        coff, p = uleb(d, p)
        out.append((midx, coff))
    return out


def main():
    cls = sys.argv[1] if len(sys.argv) > 1 else 'Lcn/ewan/supersdk/open/SuperPlatform;'
    name = sys.argv[2] if len(sys.argv) > 2 else 'init'
    dex = Dex(zipfile.ZipFile(APK).read('classes.dex'))

    targets = {}
    for i in range(dex.method_ids_size):
        owner, mname, pidx = dex.method_parts(i)
        if owner == cls and mname == name:
            targets[i] = pidx
    print('targets:', dict(targets))
    if not targets:
        return 1

    # reverse map code_off -> (class, method) for owner reporting
    owners = {}
    for cname, cls_off in dex.class_defs():
        if cls_off == 0:
            continue
        try:
            for midx, coff in class_methods(dex, cls_off):
                if coff:
                    owners[coff] = (cname, dex.method_parts(midx)[1])
        except Exception:
            continue
    print('code items indexed:', len(owners))

    d = dex.d
    print('scanning data section (%d bytes)...' % dex.data_size)
    hits = 0
    for off in range(dex.data_off, min(len(d) - 4, dex.data_off + dex.data_size), 2):
        midx = struct.unpack_from('<H', d, off)[0]
        if midx not in targets:
            continue
        op = d[off - 2] & 0xFF
        if op not in INVOKE_OPS:
            continue
        # walk back to find the owning code_item (code item header is 16 bytes,
        # so the method whose [code_off, code_off+size) contains this offset)
        owner = None
        for coff, om in owners.items():
            if coff <= off - 2:
                # cheap upper bound check
                try:
                    size = struct.unpack_from('<I', d, coff + 12)[0]
                except Exception:
                    continue
                if off - 2 < coff + 16 + size * 2:
                    owner = (coff, om)
                    break
        if owner:
            coff, (cname, mname) = owner
            print('  %s->%s  (code_item@%d)' % (cname, mname, coff))
            hits += 1
    print('invoke hits:', hits)
    return 0


if __name__ == '__main__':
    sys.exit(main())
