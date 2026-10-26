#!/usr/bin/env python3
"""在 1.4.9 APK 的全部 assets/src/**/*.luac 中搜索指定全局名字（如 'Drop'、'DropItem'）
出现的位置，用于定位“谁读取 Config.Drop”。

【硬约束】只读 anzbao/jstm.apk（1.4.9）。绝不读取 jstm_142165.apk。

用法：
    python tools/find_luac_global.py Drop DropItem
    python tools/find_luac_global.py --all          # 列出所有出现的字符串全局名
"""
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402

APK = os.path.join(os.path.dirname(HERE), 'anzbao', 'jstm.apk')
BANNED = ('142165', 'dldlJl')


def main():
    z = zipfile.ZipFile(APK)
    wanted = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = [n for n in z.namelist() if n.endswith('.luac')]
    hits = {}
    for n in names:
        if any(b in n for b in BANNED):
            continue
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        for i, pt in enumerate(r.protos):
            ss = set(pt.strings)
            for w in wanted:
                if w in ss:
                    # 只报“该 proto 同时引用了 Config 或 AutoConstruct”这类可疑点
                    hits.setdefault(w, []).append((n, i))
    for w in wanted:
        lst = hits.get(w, [])
        print('=== %r: %d 个 proto 命中 ===' % (w, len(lst)))
        for n, i in lst[:120]:
            print('   %s proto#%d' % (n, i))


if __name__ == '__main__':
    main()
