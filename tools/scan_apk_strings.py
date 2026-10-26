"""在 1.4.9 APK 的所有 assets/src/**/*.luac 字符串池里检索关键字。

用于定位 "某个全局表/字段到底定义在哪个 lua 文件"（例如 Config.MapMon、Config.Mon）。

用法：
    python tools/scan_apk_strings.py MapMon Mon MapElem
    python tools/scan_apk_strings.py --apk anzbao/jstm.apk --pat "config_mon"
"""
import argparse
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402

APK_149 = r'anzbao\jstm.apk'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('words', nargs='*')
    ap.add_argument('--apk', default=APK_149)
    ap.add_argument('--prefix', default='assets/src/')
    args = ap.parse_args()

    want = set(args.words)
    z = zipfile.ZipFile(args.apk)
    names = [n for n in z.namelist()
             if n.startswith(args.prefix) and n.endswith('.luac')]
    print('扫描 %d 个 .luac (来自 %s)' % (len(names), args.apk))

    hits = {}
    for n in names:
        try:
            data = z.read(n)
            r = parse_bytes(data)
        except Exception:
            continue
        found = set()
        for pt in r.protos:
            for s in pt.strings:
                if s in want:
                    found.add(s)
        if found:
            hits[n] = found

    for n in sorted(hits):
        print('  %-62s %s' % (n, sorted(hits[n])))

    # 汇总：每个关键字出现在哪些文件
    print()
    for w in sorted(want):
        files = [n for n, f in hits.items() if w in f]
        print('%-14s -> %d 个文件: %s' % (w, len(files), files[:8]))


if __name__ == '__main__':
    main()
