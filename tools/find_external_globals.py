#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive the *config contract*: which globals must be supplied by
assets/src/config.luac and by the CDN-downloaded url_config_ewan.lua.

Method (static, bytecode-level):
  1. Scan the whole .luac corpus for GSET  -> globals the client itself defines.
  2. Scan for GGET followed by use as a call target (CALL whose base register
     is still the register the global was loaded into) -> globals the client
     CALLS.
  3. Report globals that are CALLED but never defined anywhere in the client.
     Those can only come from the injected/ downloaded configuration, and each
     one MUST therefore be a Lua function.

This is what turns "whack-a-mole runtime errors" into one static list.

usage: python tools/find_external_globals.py <apk>
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes      # noqa: E402
from luajit_dis import OPS            # noqa: E402

# opcodes that assign to register A (so a loaded global in A is dead afterwards)
WRITE_A = {
    'MOV', 'NOT', 'UNM', 'LEN',
    'ADDVN', 'SUBVN', 'MULVN', 'DIVVN', 'MODVN',
    'ADDNV', 'SUBNV', 'MULNV', 'DIVNV', 'MODNV',
    'ADDVV', 'SUBVV', 'MULVV', 'DIVVV', 'MODVV',
    'POW', 'CAT',
    'KSTR', 'KCDATA', 'KSHORT', 'KNUM', 'KPRI', 'KNIL',
    'UGET', 'FNEW', 'TNEW', 'TDUP',
    'GGET', 'TGETV', 'TGETS', 'TGETB',
    'CALL', 'CALLM', 'CALLMT', 'CALLT',
    'ITERC', 'ITERN', 'VARG', 'ISNEXT',
    'FORI', 'FORL', 'ITERL', 'LOOP',
}


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def main():
    apk = sys.argv[1]
    z = zipfile.ZipFile(apk)
    names = sorted(n for n in z.namelist() if n.endswith('.luac'))

    defined = set()
    called = {}      # name -> first site

    for n in names:
        data = z.read(n)
        if data[:3] != b'\x1bLJ':
            continue
        try:
            r = parse_bytes(data)
        except Exception:
            continue
        for pt in r.protos:
            bc = pt.bc
            for i, w in enumerate(bc):
                op = OPS[w & 0xff]
                if op == 'GSET':
                    v = kidx(pt, (w >> 16) & 0xffff)
                    if isinstance(v, str):
                        defined.add(v)
                elif op == 'GGET':
                    v = kidx(pt, (w >> 16) & 0xffff)
                    if not isinstance(v, str):
                        continue
                    reg = (w >> 8) & 0xff
                    # is this register later used as a CALL base, before being
                    # overwritten by another write to the same register?
                    for j in range(i + 1, min(i + 25, len(bc))):
                        wj = bc[j]
                        opj = OPS[wj & 0xff]
                        aj = (wj >> 8) & 0xff
                        if opj == 'CALL' and aj == reg:
                            called.setdefault(v, '%s proto[%d] @%d' % (n, pt.index, i))
                            break
                        if aj == reg and opj in WRITE_A:
                            break
    ext = sorted(k for k in called if k not in defined)
    print('globals defined by client : %d' % len(defined))
    print('globals called by client  : %d' % len(called))
    print('called but NOT defined    : %d  <-- config contract (must be functions)'
          % len(ext))
    print('-' * 72)
    for k in ext:
        print('  %-24s  %s' % (k, called[k]))


if __name__ == '__main__':
    main()
