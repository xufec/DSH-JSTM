#!/usr/bin/env python3
"""Correct DEX class_data parser -> code_item file offsets for patch targeting.

tools/dex_tool.py's class_methods() never skips the field entries that precede
the method entries in a class_data_item, and it treats method_idx_diff as an
absolute index.  Both are wrong for any class that has fields, so its
class/method attribution is unusable.  This is a small, correct replacement
used only to compute the exact byte offsets of the methods we may patch.

usage:
  python tools/analyze_sdk_codeoff.py find <class-substr> [method-substr]
  python tools/analyze_sdk_codeoff.py dump <class-substr> <method-substr>
"""
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dex_tool import Dex, uleb  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm_142165.apk')


def class_data_methods(d, cls_off):
    """-> [(method_idx, access_flags, code_off)] with correct diff/gap handling.

    The encoded method_idx_diff is relative to the previous element *in the same
    list*; the first element of the direct list and of the virtual list each
    start from zero.  (Verified empirically: accumulating continuously across the
    direct/virtual boundary yields out-of-range method ids for this dex.)
    """
    p = cls_off
    sf, p = uleb(d, p)
    inf, p = uleb(d, p)
    dm, p = uleb(d, p)
    vm, p = uleb(d, p)
    for _ in range(sf + inf):                      # skip field entries
        _, p = uleb(d, p)
        _, p = uleb(d, p)
    out = []
    for count in (dm, vm):
        idx = 0
        for _ in range(count):
            diff, p = uleb(d, p)
            idx += diff
            acc, p = uleb(d, p)
            code_off, p = uleb(d, p)
            out.append((idx, acc, code_off))
    return out


def load():
    z = zipfile.ZipFile(APK)
    return Dex(z.read('classes.dex'))


def main():
    dex = load()
    d = dex.d
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'find'
    cpat = sys.argv[2] if len(sys.argv) > 2 else ''
    mpat = sys.argv[3] if len(sys.argv) > 3 else ''

    n = 0
    for i in range(dex.class_defs_size):
        off = dex.class_defs_off + i * 32
        cidx, acc, sup, ifo, src, ano, cls_off, _ = struct.unpack_from('<IIIIIIII', d, off)
        cname = dex.type_name(cidx)
        if cpat and cpat not in cname:
            continue
        if cls_off == 0:
            print('%-52s (no class_data)' % cname)
            continue
        ms = class_data_methods(d, cls_off)
        if cmd == 'find':
            print('%-52s methods=%d class_data_off=%d' % (cname, len(ms), cls_off))
        for midx, macc, code_off in ms:
            owner, mname = dex.method(midx)
            if mpat and mpat != mname:
                continue
            insns = ''
            if code_off:
                size = struct.unpack_from('<I', d, code_off + 12)[0]
                first = struct.unpack_from('<H', d, code_off + 16)[0] if size else 0
                insns = 'insns_size=%-5d first_insn=0x%04x @%d' % (size, first, code_off + 16)
            print('   %-52s %-26s acc=0x%04x code_off=%-9d %s'
                  % (owner, mname, macc, code_off, insns))
            n += 1
        if cmd == 'dump' and mpat:
            break
    print('-- %d methods' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
