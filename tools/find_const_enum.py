"""在 1.4.9 APK 的所有 .luac 里找出"某前缀常量定义在哪个文件"。

用法：python tools/find_const_enum.py MIS_
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402

APK = r'anzbao\jstm.apk'


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else 'MIS_'
    z = zipfile.ZipFile(APK)
    names = [n for n in z.namelist()
             if n.startswith('assets/src/') and n.endswith('.luac')]
    hits = []
    for n in names:
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        found = set()
        for pt in r.protos:
            for s in pt.strings:
                if s.startswith(prefix):
                    found.add(s)
        if found:
            hits.append((len(found), n, sorted(found)))
    hits.sort(reverse=True)
    for cnt, n, ss in hits[:12]:
        print('%-3d  %-60s %s' % (cnt, n, ss[:40]))


if __name__ == '__main__':
    main()
