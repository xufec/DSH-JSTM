#!/usr/bin/env python3
"""Find call sites of a method in a DEX by scanning invoke opcodes (no decompiler).

Scope: `invoke-*` opcodes (0x6e-0x72) carry a method index as their second
code unit. We walk every class_data_item's encoded methods and map each
instruction back to its owner method, so we can answer "who calls
Lcn/ewan/supersdk/open/SuperPlatform;->init(...)".

usage:
  python tools/dex_invoke_xref.py "Lcn/ewan/supersdk/open/SuperPlatform;" init
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')
NO_INDEX = 0xFFFFFFFF


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
        self.proto_ids_size, self.proto_ids_off = struct.unpack_from('<II', d, 72)
        self.method_ids_size, self.method_ids_off = struct.unpack_from('<II', d, 88)
        self.class_defs_size, self.class_defs_off = struct.unpack_from('<II', d, 96)

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

    def method(self, i):
        if not (0 <= i < self.method_ids_size):
            return None
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, self.method_ids_off + i * 8)
        return self.type_name(cidx), self.string(nidx)


def read_class_data(dex, off):
    d = dex.d
    static_fields, p = uleb(d, off)
    instance_fields, p = uleb(d, p)
    direct_methods, p = uleb(d, p)
    virtual_methods, p = uleb(d, p)
    methods = []
    for _ in range(direct_methods + virtual_methods):
        midx, p = uleb(d, p)
        acc, p = uleb(d, p)
        code_off, p = uleb(d, p)
        methods.append((midx, code_off))
    return methods


def instructions(code):
    """Yield (offset, opcode, units) for a 16-bit dex code array."""
    n = len(code) // 2
    i = 0
    while i < n:
        op = code[i * 2] & 0xFF
        # instruction sizes (in code units) for the opcodes we care about
        if op in (0x6E, 0x6F, 0x70, 0x71, 0x72):      # invoke-kind
            size = 3
        elif op == 0x00:                                # nop / payload
            size = 2 if i + 1 < n else 1
        elif 0x0A <= op <= 0x0D or op in (0x0E, 0x0F, 0x10, 0x11, 0x12, 0x17, 0x18, 0x19,
                                          0x1A, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22,
                                          0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A,
                                          0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32,
                                          0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A,
                                          0x3B, 0x3C, 0x3D):
            size = 1
        elif op in (0x01, 0x04, 0x07):
            size = 2
        elif op in (0x02, 0x05, 0x08):
            size = 3
        elif op in (0x03, 0x06, 0x09):
            size = 5
        elif 0x44 <= op <= 0x51 or 0x52 <= op <= 0x5F or 0x60 <= op <= 0x6D:
            size = 2
        elif 0x73 <= op <= 0x78:
            size = 2 if op in (0x73, 0x74, 0x75, 0x76, 0x77, 0x78) else 2
        elif 0x79 <= op <= 0x7A:
            size = 2
        elif 0x7B <= op <= 0x8F:
            size = 1
        elif 0x90 <= op <= 0xAF:
            size = 2
        elif 0xB0 <= op <= 0xCF:
            size = 1
        elif 0xD0 <= op <= 0xD7:
            size = 2
        elif 0xD8 <= op <= 0xE2:
            size = 2
        elif op in (0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF):
            size = 1
        else:
            size = 1
        yield i, op, size
        i += size


def main():
    owner = sys.argv[1] if len(sys.argv) > 1 else 'Lcn/ewan/supersdk/open/SuperPlatform;'
    name = sys.argv[2] if len(sys.argv) > 2 else 'init'
    z = zipfile.ZipFile(APK)
    dex = Dex(z.read('classes.dex'))

    # target method indices
    targets = set()
    for i in range(dex.method_ids_size):
        m = dex.method(i)
        if m and m[0] == owner and m[1] == name:
            targets.add(i)
    print('target method ids:', sorted(targets))
    if not targets:
        return 1

    hits = 0
    for ci in range(dex.class_defs_size):
        off = dex.class_defs_off + ci * 32
        cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', dex.d, off)
        if cls_off == 0:
            continue
        try:
            methods = read_class_data(dex, cls_off)
        except Exception:
            continue
        for midx, code_off in methods:
            if code_off == 0:
                continue
            insns_size = struct.unpack_from('<I', dex.d, code_off + 12)[0]
            start = code_off + 16
            raw = dex.d[start:start + insns_size * 2]
            code = struct.unpack_from('<%dH' % insns_size, raw, 0)
            for i, op, size in instructions(code):
                if op in (0x6E, 0x6F, 0x70, 0x71, 0x72) and i + 1 < insns_size:
                    mi = code[i * 2 + 1]
                    if mi in targets:
                        caller = dex.method(midx)
                        print('  caller %s->%s  (class#%d) at code_off=%d'
                              % (caller[0], caller[1], ci, code_off))
                        hits += 1
    print('xrefs found:', hits)
    return 0


if __name__ == '__main__':
    sys.exit(main())
