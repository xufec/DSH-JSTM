#!/usr/bin/env python3
"""Dump the opcode stream of chosen LuaJIT protos, showing globals/constants they use.

Purpose: find *who* calls a given global (e.g. getToken / sdkCallFunc) without a
full decompiler. Prints, per prototype, the GGET/GSET/TSET/GETT targets so the
responsible module and function index are obvious.

usage:
  python tools/who_uses_global.py <member.luac> <GlobalName> [moreGlobals...]
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import parse_bytes, TableConst  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def kgc_at(pt, idx):
    if 0 <= idx < len(pt.kgc):
        return pt.kgc[idx]
    return None


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    member, names = args[0], set(args[1:])
    z = zipfile.ZipFile(APK)
    if member not in z.namelist():
        member = 'assets/src/' + member.lstrip('/')
    r = parse_bytes(z.read(member))
    print('== %s : %d protos' % (member, len(r.protos)))
    for i, pt in enumerate(r.protos):
        used = set()
        # constants referenced anywhere in this proto's kgc are candidates
        for c in pt.kgc:
            if isinstance(c, str):
                if c in names:
                    used.add(c)
            elif isinstance(c, TableConst):
                for k, v in c.items:
                    if isinstance(k, str) and k in names:
                        used.add(k)
                    if isinstance(v, str) and v in names:
                        used.add(v)
        if used:
            print('  proto#%-3d %s  -> %s' % (i, pt, sorted(used)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
