#!/usr/bin/env python3
"""Corpus-wide search for global/string references inside .luac bytecode.

usage:
  python tools/analyze_corpus_grep.py <regex>            # search string consts
  python tools/analyze_corpus_grep.py --imports <mod>    # find require('mod') sites
"""
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import OPS  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def main():
    pat = re.compile(sys.argv[1], re.I)
    want_bytes = '--bytes' in sys.argv
    z = zipfile.ZipFile(APK)
    names = sorted(n for n in z.namelist() if n.endswith('.luac'))
    for n in names:
        data = z.read(n)
        if not data[:3] == b'\x1bLJ':
            if want_bytes is False:
                # plain-text lua: just grep raw text
                txt = data.decode('utf-8', 'replace')
                for i, line in enumerate(txt.splitlines(), 1):
                    if pat.search(line):
                        print('%s:%d: %s' % (n, i, line[:160]))
            continue
        try:
            r = parse_bytes(data)
        except Exception as e:
            print('!! %s: %r' % (n, e))
            continue
        hits = []
        for pt in r.protos:
            for s in pt.strings:
                if isinstance(s, str) and pat.search(s):
                    hits.append((pt.index, s))
            for w in pt.bc:
                op = w & 0xff
                if OPS[op] in ('GGET', 'GSET'):
                    v = kidx(pt, (w >> 16) & 0xffff)
                    if isinstance(v, str) and pat.search(v):
                        hits.append((pt.index, 'GLOBAL:' + v))
        if hits:
            seen = []
            for pi, s in hits:
                if (pi, s) not in seen:
                    seen.append((pi, s))
            print('==== %s' % n)
            for pi, s in seen[:40]:
                print('    proto[%d] %s' % (pi, s))


if __name__ == '__main__':
    main()
