#!/usr/bin/env python3
"""Minimal DEX string/method index — locate SDK classes and their methods fast.

Full decompilers are slow on this 8.4 MB dex; for "which class declares init()"
we only need the string/type/method-id/class-def tables.

usage:
  python tools/dex_index.py --classes cn.ewan.supersdk.open
  python tools/dex_index.py --method init
  python tools/dex_index.py --grep SuperSDK
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


class Dex:
    def __init__(self, d):
        self.d = d
        self.string_ids_size, self.string_ids_off = struct.unpack_from('<II', d, 56)
        self.type_ids_size, self.type_ids_off = struct.unpack_from('<II', d, 64)
        self.proto_ids_size, self.proto_ids_off = struct.unpack_from('<II', d, 72)
        self.field_ids_size, self.field_ids_off = struct.unpack_from('<II', d, 80)
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
        sid = struct.unpack_from('<I', self.d, self.type_ids_off + i * 4)[0]
        return self.string(sid)

    def method(self, i):
        """-> (class_type_idx, name, proto_idx)"""
        if not (0 <= i < self.method_ids_size):
            return None
        cidx, pidx, nidx = struct.unpack_from('<HHI', self.d, self.method_ids_off + i * 8)
        return cidx, self.string(nidx), pidx

    def classes(self):
        out = []
        for i in range(self.class_defs_size):
            off = self.class_defs_off + i * 32
            cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', self.d, off)
            out.append((i, cidx, cls_off))
        return out


def main():
    args = sys.argv[1:]
    z = zipfile.ZipFile(APK)
    dex = Dex(z.read('classes.dex'))

    def show_prefix(prefix):
        for i, cidx, cls_off in dex.classes():
            name = dex.type_name(cidx)
            if prefix in name:
                print('class#%d %s  data_off=%d' % (i, name, cls_off))

    if '--classes' in args:
        show_prefix(args[args.index('--classes') + 1])
    elif '--grep' in args:
        pat = args[args.index('--grep') + 1]
        seen = set()
        for i in range(dex.string_ids_size):
            s = dex.string(i)
            if pat in s and s not in seen:
                seen.add(s)
                print(s)
            if len(seen) > 120:
                break
    elif '--method' in args:
        pat = args[args.index('--method') + 1]
        hits = 0
        for i in range(dex.method_ids_size):
            cidx, name, pidx = dex.method(i)
            if name == pat:
                print('%-70s %s' % (dex.type_name(cidx), name))
                hits += 1
                if hits > 80:
                    break
        print('methods named %r: %d' % (pat, hits))
    else:
        print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main())
