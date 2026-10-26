#!/usr/bin/env python3
"""Locate dialog strings across all candidate APKs (dex + resources.arsc).

Throwaway analysis helper for the SDK-init blocker. Read-only.

usage: python tools/analyze_sdk_strings.py
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APKS = ['anzbao/dldlJl.apk', 'anzbao/jstm_142165.apk', 'anzbao/jstm.apk']
NEEDLES = ['初始化失败', '请检查网络', '重新连接', '退出游戏', '初始化', 'sdkCallFunc',
           'supersdk', 'SuperSDK', 'init']


def find_all(hay, needle, limit=8):
    out = []
    i = hay.find(needle)
    while i >= 0 and len(out) < limit:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def main():
    for rel in APKS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print('!! missing', rel)
            continue
        z = zipfile.ZipFile(p)
        print('===', rel)
        for name in z.namelist():
            if not (name.endswith('.dex') or name.endswith('.arsc')
                    or name == 'AndroidManifest.xml'):
                continue
            data = z.read(name)
            for needle in NEEDLES:
                nb = needle.encode('utf-8')
                # utf8 form
                hits8 = find_all(data, nb)
                # utf-16le form (arsc global pool / manifest)
                hits16 = find_all(data, needle.encode('utf-16-le'))
                if hits8 or hits16:
                    print('  %-22s %-14s utf8=%s utf16le=%s'
                          % (name, needle, hits8, hits16))


if __name__ == '__main__':
    main()
