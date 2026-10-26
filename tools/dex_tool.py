#!/usr/bin/env python3
"""Small, careful DEX reader: list classes/methods and find invoke xrefs.

Purpose: locate the exact call site that initialises the ewan SuperSDK
(the standalone build must neutralise it), without a full decompiler.

usage:
  python tools/dex_tool.py classes <substring>
  python tools/dex_tool.py methods <class-substring> [name-substring]
  python tools/dex_tool.py xrefs <class> <method>
  python tools/dex_tool.py strings <substring>
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')

INVOKE_OPS = {0x6E: 3, 0x6F: 3, 0x70: 3, 0x71: 3, 0x72: 3}
# full instruction width table (dex 035), values in 16-bit code units
WIDTHS = {
    0x00: 1, 0x01: 1, 0x02: 1, 0x03: 1, 0x04: 1, 0x05: 1, 0x06: 1, 0x07: 1, 0x08: 1, 0x09: 1,
    0x0A: 1, 0x0B: 1, 0x0C: 1, 0x0D: 1, 0x0E: 1, 0x0F: 1, 0x10: 1, 0x11: 1, 0x12: 1, 0x13: 1,
    0x14: 1, 0x15: 1, 0x16: 1, 0x17: 1, 0x18: 1, 0x19: 1, 0x1A: 1, 0x1B: 1, 0x1C: 1, 0x1D: 2,
    0x1E: 1, 0x1F: 1, 0x20: 1, 0x21: 1, 0x22: 2, 0x23: 2, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 1,
    0x28: 1, 0x29: 1, 0x2A: 1, 0x2B: 1, 0x2C: 1, 0x2D: 2, 0x2E: 2, 0x2F: 2, 0x30: 2, 0x31: 2,
    0x32: 2, 0x33: 2, 0x34: 2, 0x35: 2, 0x36: 2, 0x37: 2, 0x38: 2, 0x39: 2, 0x3A: 2, 0x3B: 2,
    0x3C: 2, 0x3D: 2, 0x3E: 1, 0x3F: 1, 0x40: 1, 0x41: 1, 0x42: 1, 0x43: 1, 0x44: 2, 0x45: 2,
    0x46: 2, 0x47: 2, 0x48: 2, 0x49: 2, 0x4A: 2, 0x4B: 2, 0x4C: 2, 0x4D: 2, 0x4E: 2, 0x4F: 2,
    0x50: 2, 0x51: 2, 0x52: 2, 0x53: 2, 0x54: 2, 0x55: 2, 0x56: 2, 0x57: 2, 0x58: 2, 0x59: 2,
    0x5A: 2, 0x5B: 2, 0x5C: 2, 0x5D: 2, 0x5E: 2, 0x5F: 2, 0x60: 2, 0x61: 2, 0x62: 2, 0x63: 2,
    0x64: 2, 0x65: 2, 0x66: 2, 0x67: 2, 0x68: 2, 0x69: 2, 0x6A: 2, 0x6B: 2, 0x6C: 2, 0x6D: 2,
    0x6E: 3, 0x6F: 3, 0x70: 3, 0x71: 3, 0x72: 3, 0x73: 1, 0x74: 1, 0x75: 1, 0x76: 1, 0x77: 1,
    0x78: 1, 0x79: 2, 0x7A: 2, 0x7B: 1, 0x7C: 1, 0x7D: 1, 0x7E: 1, 0x7F: 1, 0x80: 1, 0x81: 1,
    0x82: 1, 0x83: 1, 0x84: 1, 0x85: 1, 0x86: 1, 0x87: 1, 0x88: 1, 0x89: 1, 0x8A: 1, 0x8B: 1,
    0x8C: 1, 0x8D: 1, 0x8E: 1, 0x8F: 1, 0x90: 2, 0x91: 2, 0x92: 2, 0x93: 2, 0x94: 2, 0x95: 2,
    0x96: 2, 0x97: 2, 0x98: 2, 0x99: 2, 0x9A: 2, 0x9B: 2, 0x9C: 2, 0x9D: 2, 0x9E: 2, 0x9F: 2,
    0xA0: 2, 0xA1: 2, 0xA2: 2, 0xA3: 2, 0xA4: 2, 0xA5: 2, 0xA6: 2, 0xA7: 2, 0xA8: 2, 0xA9: 2,
    0xAA: 2, 0xAB: 2, 0xAC: 2, 0xAD: 2, 0xAE: 2, 0xAF: 2, 0xB0: 1, 0xB1: 1, 0xB2: 1, 0xB3: 1,
    0xB4: 1, 0xB5: 1, 0xB6: 1, 0xB7: 1, 0xB8: 1, 0xB9: 1, 0xBA: 1, 0xBB: 1, 0xBC: 1, 0xBD: 1,
    0xBE: 1, 0xBF: 1, 0xC0: 1, 0xC1: 1, 0xC2: 1, 0xC3: 1, 0xC4: 1, 0xC5: 1, 0xC6: 1, 0xC7: 1,
    0xC8: 1, 0xC9: 1, 0xCA: 1, 0xCB: 1, 0xCC: 1, 0xCD: 1, 0xCE: 1, 0xCF: 1, 0xD0: 2, 0xD1: 2,
    0xD2: 2, 0xD3: 2, 0xD4: 2, 0xD5: 2, 0xD6: 2, 0xD7: 2, 0xD8: 2, 0xD9: 2, 0xDA: 2, 0xDB: 2,
    0xDC: 2, 0xDD: 2, 0xDE: 2, 0xDF: 2, 0xE0: 2, 0xE1: 2, 0xE2: 2, 0xFA: 1, 0xFB: 1, 0xFC: 1,
    0xFD: 1, 0xFE: 1, 0xFF: 1,
}


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
        for name, off_hdr in (('string_ids', 56), ('type_ids', 64), ('proto_ids', 72),
                              ('field_ids', 80), ('method_ids', 88), ('class_defs', 96)):
            size, off = struct.unpack_from('<II', d, off_hdr)
            setattr(self, name + '_size', size)
            setattr(self, name + '_off', off)

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
            return ('?', '?')
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, self.method_ids_off + i * 8)
        return self.type_name(cidx), self.string(nidx)

    def class_defs(self):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i * 32
            cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', self.d, off)
            yield i, self.type_name(cidx), cls_off

    def class_methods(self, cls_off):
        """-> [(method_idx, code_off)]"""
        d = self.d
        _, p = uleb(d, cls_off)                 # static_fields
        _, p = uleb(d, p)                       # instance_fields
        direct, p = uleb(d, p)
        virtual, p = uleb(d, p)
        out = []
        for _ in range(direct + virtual):
            midx, p = uleb(d, p)
            _, p = uleb(d, p)                   # access_flags
            code_off, p = uleb(d, p)
            out.append((midx, code_off))
        return out


def code_units(dex, code_off):
    insns_size = struct.unpack_from('<I', dex.d, code_off + 12)[0]
    start = code_off + 16
    return struct.unpack_from('<%dH' % insns_size, dex.d, start)


def walk(units):
    """Yield (index, opcode) honouring instruction widths; payloads are skipped."""
    i = 0
    n = len(units)
    while i < n:
        op = units[i] & 0xFF
        if op == 0x00 and i + 1 < n:
            ident = (units[i + 1] >> 8) & 0xFF
            if ident == 0x01:      # packed-switch payload
                size = (units[i + 1] & 0xFF) * 2 + 4
            elif ident == 0x02:    # sparse-switch payload
                size = (units[i + 1] & 0xFF) * 4 + 2
            elif ident == 0x03:    # fill-array-data payload
                size = ((units[i + 1] & 0xFF) * 2 + 1 + 3) // 2 * 2 + 4
            else:
                size = 1
        else:
            size = WIDTHS.get(op, 1)
        yield i, op
        i += size


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    z = zipfile.ZipFile(APK)
    dex = Dex(z.read('classes.dex'))

    if cmd == 'strings':
        pat = sys.argv[2]
        n = 0
        for i in range(dex.string_ids_size):
            s = dex.string(i)
            if pat in s:
                print('%6d  %s' % (i, s[:120]))
                n += 1
                if n > 60:
                    break
        return 0

    if cmd == 'classes':
        pat = sys.argv[2]
        for i, name, off in dex.class_defs():
            if pat in name:
                print('%-70s data_off=%d' % (name, off))
        return 0

    if cmd == 'methods':
        cpat = sys.argv[2]
        npat = sys.argv[3] if len(sys.argv) > 3 else ''
        for i, name, off in dex.class_defs():
            if cpat not in name or off == 0:
                continue
            try:
                ms = dex.class_methods(off)
            except Exception as e:
                print('%s: class_data read failed: %r' % (name, e))
                continue
            for midx, coff in ms:
                owner, mname = dex.method(midx)
                if npat in mname:
                    print('%-64s %-24s code_off=%d' % (owner, mname, coff))
        return 0

    if cmd == 'xrefs':
        owner, name = sys.argv[2], sys.argv[3]
        targets = {i for i in range(dex.method_ids_size)
                   if dex.method(i) == (owner, name)}
        print('target ids:', sorted(targets))
        hits = 0
        for ci, cname, cls_off in dex.class_defs():
            if cls_off == 0:
                continue
            try:
                ms = dex.class_methods(cls_off)
            except Exception:
                continue
            for midx, coff in ms:
                if coff == 0:
                    continue
                try:
                    units = code_units(dex, coff)
                except Exception:
                    continue
                for i, op in walk(units):
                    if op in INVOKE_OPS and i + 1 < len(units):
                        if units[i + 1] in targets:
                            print('  %s->%s  (in %s)' % (dex.method(midx)[0],
                                                         dex.method(midx)[1], cname))
                            hits += 1
        print('xrefs:', hits)
        return 0

    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
