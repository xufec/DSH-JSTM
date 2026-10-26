#!/usr/bin/env python3
"""Compare the three APKs' DEX for SDK entry points and app Activity classes.

Focus: which SDK actually drives startup init (the thing that blocked the
standalone build), and how each package wires it.

usage:
  python tools/apk_dex_compare.py
"""
import os
import re
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANZ = os.path.join(HERE, 'anzbao')

PROBES = {
    'SuperPlatform (ewan)': rb'cn/ewan/supersdk/open/SuperPlatform',
    'SuperSDK via JNI': rb'com/bangcle/andJni',
    'shiyue EWanSdk': rb'com/shiyue/sdk/EWanSdk',
    'Cocos2dxActivity': rb'org/cocos2dx/lib/Cocos2dxActivity',
    'qihoo sdk': rb'com/qihoo',
    'baidu gamesdk': rb'com/baidu/gamesdk',
    'cw platform (91cw)': rb'com/cw/platform',
    'duoku platform': rb'com/duoku/platform',
    'SuperInitListener': rb'cn/ewan/supersdk/open/SuperInitListener',
}


def main():
    rows = []
    for name in sorted(os.listdir(ANZ)):
        if not name.endswith('.apk'):
            continue
        z = zipfile.ZipFile(os.path.join(ANZ, name))
        dex = z.read('classes.dex')
        row = {'apk': name, 'dexMB': round(len(dex) / 1048576, 1)}
        for label, pat in PROBES.items():
            row[label] = 'yes' if pat in dex else '-'
        # does the app's own Activity class exist and is it the manifest launcher?
        mf = z.read('AndroidManifest.xml')
        row['launcher=cocos AppActivity'] = (
            'yes' if b'org.cocos2dx.lua.AppActivity' in mf or
                     b'org.cocos2dx.lua.AppActivity' in dex else '-')
        rows.append(row)

    labels = ['apk', 'dexMB'] + list(PROBES.keys()) + ['launcher=cocos AppActivity']
    for r in rows:
        print('=' * 74)
        for k in labels:
            print('  %-26s %s' % (k, r.get(k, '')))


if __name__ == '__main__':
    main()
