#!/usr/bin/env python3
"""Byte-level DEX analysis for the ewan SuperSDK init blocker.

Read-only throwaway helper. Maps string constants -> string_ids -> the
methods that load them (const-string), and can disassemble a method and
follow invoke xrefs, so we can name the exact call chain without jadx.

usage:
  python tools/analyze_sdk_dex.py strfind <needle>...
  python tools/analyze_sdk_dex.py users <string_idx>
  python tools/analyze_sdk_dex.py callers <class> <method>
  python tools/analyze_sdk_dex.py callees <class> <method>
  python tools/analyze_sdk_dex.py disasm <class> <method>
  python tools/analyze_sdk_dex.py methodof <file_offset>     (offset in classes.dex)
"""
import os
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dex_tool import Dex, code_units, walk, uleb  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm_142165.apk')

INVOKE_OPS = {0x6E: 'invoke-virtual', 0x6F: 'invoke-super', 0x70: 'invoke-direct',
              0x71: 'invoke-static', 0x72: 'invoke-interface'}


def read_string(d, off):
    """Correct string_data_item reader.

    dex_tool.Dex.string() uses the uleb128 (UTF-16 code-unit count) as a byte
    count, which truncates every non-ASCII constant and makes Chinese string
    matching fail.  MUTF-8 never contains a raw 0x00, so read to the terminator.
    """
    n, p = uleb(d, off)
    end = d.find(b'\x00', p)
    if end < 0:
        end = len(d)
    return d[p:end].decode('utf-8', 'replace')


class Dex2(Dex):
    def string(self, i):
        if not (0 <= i < self.string_ids_size):
            return '?'
        off = struct.unpack_from('<I', self.d, self.string_ids_off + i * 4)[0]
        return read_string(self.d, off)


def load(apk=APK):
    z = zipfile.ZipFile(apk)
    return Dex2(z.read('classes.dex'))


def all_strings(dex):
    return [dex.string(i) for i in range(dex.string_ids_size)]


def str_off(dex, i):
    return struct.unpack_from('<I', dex.d, dex.string_ids_off + i * 4)[0]


def iter_methods(dex):
    """Yield (class_name, method_name, method_idx, code_off)."""
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
            yield cname, dex.method(midx)[1], midx, coff


def str_refs(units):
    """Yield (insn_index, string_idx) for const-string / const-string/jumbo."""
    for i, op in walk(units):
        if op == 0x1A and i + 1 < len(units):
            yield i, units[i + 1]
        elif op == 0x1B and i + 2 < len(units):
            yield i, units[i + 1] | (units[i + 2] << 16)


def unesc(s):
    """Decode \\uXXXX escapes so Chinese never has to cross the console."""
    return s.encode('ascii', 'surrogateescape').decode('unicode_escape')


def cmd_strgrep(dex, needles):
    """Substring search over the real (correctly decoded) string table."""
    needles = [unesc(n) if '\\u' in n else n for n in needles]
    for i in range(dex.string_ids_size):
        s = dex.string(i)
        for n in needles:
            if n in s:
                print('   id=%-6d %r' % (i, s))
                break


def cmd_strfind(dex, needles):
    for needle in needles:
        if '\\u' in needle:
            needle = unesc(needle)
        nb = needle.encode('utf-8')
        print('== needle %r' % needle)
        hits = 0
        for i in range(dex.string_ids_size):
            off = str_off(dex, i)
            n, p = uleb(dex.d, off)
            if dex.d[p:p + n] == nb:
                print('   string_idx=%d data_off=%d prefix_off=%d' % (i, p, off))
                hits += 1
        if not hits:
            print('   (none)')


def cmd_users(dex, sidx):
    print('== methods loading string_idx=%d %r' % (sidx, dex.string(sidx)))
    for cname, mname, midx, coff in iter_methods(dex):
        try:
            units = code_units(dex, coff)
        except Exception:
            continue
        for i, idx in str_refs(units):
            if idx == sidx:
                print('   %s->%s  insn@%d code_off=%d' % (cname, mname, i, coff))
                break


def _find_method(dex, cpat, mpat):
    for cname, mname, midx, coff in iter_methods(dex):
        if cpat in cname and mpat == mname:
            yield cname, mname, coff


def cmd_callers(dex, cpat, mpat):
    targets = set()
    for cname, mname, coff in iter_methods(dex):
        if cpat in cname and mname == mpat:
            targets.add(dex_method_id(dex, cname, mname))
    print('== %s.%s method_ids=%s' % (cpat, mpat, sorted(targets)))
    n = 0
    for cname, mname, midx, coff in iter_methods(dex):
        try:
            units = code_units(dex, coff)
        except Exception:
            continue
        for i, op in walk(units):
            if op in INVOKE_OPS and i + 1 < len(units) and units[i + 1] in targets:
                print('   %s->%s (insn@%d)' % (cname, mname, i))
                n += 1
    print('   total %d' % n)


def dex_method_id(dex, owner, name):
    for i in range(dex.method_ids_size):
        if dex.method(i) == (owner, name):
            return i
    return None


def cmd_callees(dex, cpat, mpat):
    for cname, mname, coff in _find_method(dex, cpat, mpat):
        units = code_units(dex, coff)
        print('== %s.%s' % (cname, mname))
        for i, op in walk(units):
            if op in INVOKE_OPS and i + 1 < len(units):
                owner, nm = dex.method(units[i + 1])
                print('   insn@%-5d %-18s %s->%s' % (i, INVOKE_OPS[op], owner, nm))


def cmd_disasm(dex, cpat, mpat):
    for cname, mname, coff in _find_method(dex, cpat, mpat):
        units = code_units(dex, coff)
        print('== %s.%s  code_off=%d units=%d' % (cname, mname, coff, len(units)))
        for i, op in walk(units):
            extra = ''
            if op == 0x1A and i + 1 < len(units):
                extra = '  ; %r' % dex.string(units[i + 1])
            elif op == 0x1B and i + 2 < len(units):
                extra = '  ; %r' % dex.string(units[i + 1] | (units[i + 2] << 16))
            elif op in INVOKE_OPS and i + 1 < len(units):
                o, nm = dex.method(units[i + 1])
                extra = '  ; %s->%s' % (o, nm)
            elif op in (0x39, 0x38, 0x3A, 0x3B, 0x3C, 0x3D):  # if-*
                extra = '  ; raw=%04x %04x' % (units[i], units[i + 1] if i + 1 < len(units) else 0)
            print('   %-5d %04x%s' % (i, units[i], extra))


def cmd_methodof(dex, off):
    print('== methods whose code range contains file offset %d' % off)
    for cname, mname, midx, coff in iter_methods(dex):
        try:
            units = code_units(dex, coff)
        except Exception:
            continue
        end = coff + 16 + len(units) * 2
        if coff <= off < end:
            print('   %s->%s code_off=%d end=%d' % (cname, mname, coff, end))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    argv = [a for a in sys.argv if not a.startswith('--apk=')]
    apk = APK
    for a in sys.argv:
        if a.startswith('--apk='):
            apk = a.split('=', 1)[1]
    cmd = argv[1]
    dex = load(apk)
    if cmd == 'strfind':
        cmd_strfind(dex, argv[2:])
    elif cmd == 'strgrep':
        cmd_strgrep(dex, argv[2:])
    elif cmd == 'users':
        cmd_users(dex, int(argv[2]))
    elif cmd == 'callers':
        cmd_callers(dex, argv[2], argv[3])
    elif cmd == 'callees':
        cmd_callees(dex, argv[2], argv[3])
    elif cmd == 'disasm':
        cmd_disasm(dex, argv[2], argv[3])
    elif cmd == 'methodof':
        cmd_methodof(dex, int(argv[2]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
