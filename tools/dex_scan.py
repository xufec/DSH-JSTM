#!/usr/bin/env python3
"""Method-level DEX scanner: who invokes a given class's methods.

Correctly decodes class_data_item (method_idx_diff is a *delta*) and every
instruction width, so the reported call sites and their owners are trustworthy.
That correctness is what the earlier quick-and-dirty scans got wrong.

usage:
  python tools/dex_scan.py xrefs <class-substring> [method-substring]
  python tools/dex_scan.py classes <substring>
  python tools/dex_scan.py methods <class-substring> [method-substring]
"""
import os
import struct
import sys
import zipfile

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')

INVOKE = {0x6E, 0x6F, 0x70, 0x71, 0x72}
WIDTH = {
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
        for nm, off in (('string_ids', 56), ('type_ids', 64), ('proto_ids', 72),
                        ('field_ids', 80), ('method_ids', 88), ('class_defs', 96)):
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
        return self.type_name(cidx), self.string(nidx), pidx

    def iter_classes(self):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i * 32
            cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', self.d, off)
            yield self.type_name(cidx), cls_off

    def methods_of(self, cls_off):
        """-> [(method_idx, code_off)] with method_idx_diff accumulated."""
        d = self.d
        _, p = uleb(d, cls_off)          # static fields
        _, p = uleb(d, p)                # instance fields
        nd, p = uleb(d, p)               # direct methods
        nv, p = uleb(d, p)               # virtual methods
        out = []
        idx = 0
        for _ in range(nd + nv):
            diff, p = uleb(d, p)
            idx += diff
            _, p = uleb(d, p)            # access_flags
            coff, p = uleb(d, p)
            out.append((idx, coff))
        return out


def units_of(dex, coff):
    n = struct.unpack_from('<I', dex.d, coff + 12)[0]
    return struct.unpack_from('<%dH' % n, dex.d, coff + 16)


def walk(units):
    i = 0
    n = len(units)
    while i < n:
        op = units[i] & 0xFF
        if op == 0x00 and i + 1 < n:
            ident = (units[i + 1] >> 8) & 0xFF
            if ident == 1:
                sz = (units[i + 1] & 0xFF) * 2 + 4
            elif ident == 2:
                sz = (units[i + 1] & 0xFF) * 4 + 2
            elif ident == 3:
                sz = ((units[i + 1] & 0xFF) * 2 + 1 + 3) // 2 * 2 + 4
            else:
                sz = 1
        else:
            sz = WIDTH.get(op, 1)
        yield i, op, sz
        i += sz


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    dex = Dex(zipfile.ZipFile(APK).read('classes.dex'))

    if cmd == 'classes':
        pat = sys.argv[2]
        for name, off in dex.iter_classes():
            if pat in name:
                print('%-72s data_off=%d' % (name, off))
        return 0

    if cmd == 'methods':
        pat = sys.argv[2]
        npat = sys.argv[3] if len(sys.argv) > 3 else ''
        for name, off in dex.iter_classes():
            if pat in name and off:
                try:
                    for midx, coff in dex.methods_of(off):
                        owner, mname, _ = dex.method_parts(midx)
                        if npat in mname:
                            print('%-60s %-22s code=%d' % (owner, mname, coff))
                except Exception as e:
                    print('%s: %r' % (name, e))
        return 0

    if cmd == 'xrefs':
        cpat = sys.argv[2]
        mpat = sys.argv[3] if len(sys.argv) > 3 else ''
        targets = set()
        tnames = {}
        for i in range(dex.method_ids_size):
            owner, mname, _ = dex.method_parts(i)
            if cpat in owner and mpat in mname:
                targets.add(i)
                tnames[i] = '%s->%s' % (owner, mname)
        print('target methods: %d' % len(targets))
        for t in sorted(tnames)[:12]:
            print('   ', tnames[t])
        if not targets:
            return 1
        hits = 0
        for cname, cls_off in dex.iter_classes():
            if not cls_off:
                continue
            try:
                ms = dex.methods_of(cls_off)
            except Exception:
                continue
            for midx, coff in ms:
                if not coff:
                    continue
                try:
                    u = units_of(dex, coff)
                except Exception:
                    continue
                for i, op, sz in walk(u):
                    if op in INVOKE and i + 1 < len(u) and u[i + 1] in targets:
                        owner, mname, _ = dex.method_parts(midx)
                        print('  %s->%s calls %s' % (owner, mname, tnames[u[i + 1]]))
                        hits += 1
        print('xrefs:', hits)
        return 0

    if cmd == 'strings':
        pat = sys.argv[2]
        for i in range(dex.string_ids_size):
            s = dex.string(i)
            if pat in s:
                print('%6d %s' % (i, s[:120]))
        return 0

    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
