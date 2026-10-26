#!/usr/bin/env python3
"""Pretty-printer / structure exporter for the game's LuaJIT bytecode.

Usage:
  python tools/bc_dump.py <apk> <member-path> [--tables] [--limit N] [--proto IDX]
"""
import sys, os, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import Reader, TableConst, ChildRef, BCError


def fmt(v, depth=0, maxdepth=3):
    if isinstance(v, str):
        s = v if len(v) <= 60 else v[:57] + '...'
        return repr(s)
    if isinstance(v, ChildRef):
        return '<function #%d>' % v.index
    if isinstance(v, TableConst):
        if depth >= maxdepth:
            return '{...%d+%d...}' % (len(v.array), len(v.hash))
        parts = []
        for i, x in enumerate(v.array):
            if x is None:
                continue
            parts.append(fmt(x, depth + 1, maxdepth))
        for k, x in v.hash:
            parts.append('%s = %s' % (fmt(k, depth + 1, maxdepth), fmt(x, depth + 1, maxdepth)))
        return '{' + ', '.join(parts) + '}'
    return repr(v)


def dump(data, member, tables_only=False, limit=20, proto_idx=None):
    r = Reader(data)
    r.parse()
    print('=== %s ===' % member)
    print('version=%d flags=0x%02x protos=%d' % (r.version, r.flags, len(r.protos)))
    for i, pt in enumerate(r.protos):
        if proto_idx is not None and i != proto_idx:
            continue
        print('--- proto #%d  bc=%d uv=%d params=%d framesize=%d kgc=%d knum=%d flags=0x%02x'
              % (i, len(pt.bc), pt.numuv, pt.numparams, pt.framesize, len(pt.kgc),
                 len(pt.knum), pt.flags))
        strs = pt.strings
        if strs:
            show = strs[:limit]
            print('    strings(%d): %s' % (len(strs), ', '.join(repr(s) for s in show)))
        tabs = pt.tables
        if tabs:
            print('    tables(%d):' % len(tabs))
            for t in tabs[:limit]:
                print('       %s' % fmt(t, 0, 3))
        kids = pt.children
        if kids:
            print('    children: %s' % ', '.join('#%d' % k.index for k in kids))
        if pt.knum and not tables_only:
            print('    knum(%d): %s' % (len(pt.knum), pt.knum[:limit]))
    return r


def main():
    apk = sys.argv[1]
    member = sys.argv[2]
    opts = sys.argv[3:]
    z = zipfile.ZipFile(apk)
    data = z.read(member)
    tables_only = '--tables' in opts
    limit = 20
    proto_idx = None
    if '--limit' in opts:
        limit = int(opts[opts.index('--limit') + 1])
    if '--proto' in opts:
        proto_idx = int(opts[opts.index('--proto') + 1])
    if '--all-protos' in opts:
        proto_idx = None
    dump(data, member, tables_only, limit, proto_idx)


if __name__ == '__main__':
    main()