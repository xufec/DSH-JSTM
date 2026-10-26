#!/usr/bin/env python3
"""Compare config.luac across the three APKs, and check how each wires SDK init.

The older dldlJl package has no Bangcle JNI (libsupersdkjni.so absent), so its
SDK init path may be simpler to neutralise — that matters for picking the host
package of the combined standalone build.

usage:
  python tools/compare_configs.py
"""
import os
import re
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANZ = os.path.join(HERE, 'anzbao')
KEYS = ['GAME_NAME', 'PLATFORM_NAME', 'IS_PLATFORM_LOGIN', 'MUTIL_LOGIN',
        'NOW_VERSION', 'BUILD_VERSION', 'MAIN_VERSION', 'IS_ANDROID_VERIFY',
        'IS_REQUIRE_RES', 'URL_LUA_CONFIG', 'CHANGE_ACCOUNT_ENABLE',
        'IS_TEST_SERVER', 'IS_NEW_COLLECT_DATA']


def read_cfg(z):
    for c in ('assets/src/config.luac', 'assets/src/config.lua'):
        if c in z.namelist():
            return z.read(c).decode('gbk', 'replace')
    return ''


def main():
    apks = [n for n in sorted(os.listdir(ANZ)) if n.endswith('.apk')]
    cfgs = {}
    for name in apks:
        z = zipfile.ZipFile(os.path.join(ANZ, name))
        cfgs[name] = read_cfg(z)

    print('%-22s %s' % ('key', ' | '.join('%-18s' % a for a in apks)))
    for k in KEYS:
        vals = []
        for a in apks:
            m = re.search(k + r'\s*=\s*([^\n\r]+)', cfgs[a])
            v = m.group(1).strip() if m else '(absent)'
            v = re.sub(r'--.*$', '', v).strip()
            vals.append('%-18s' % v[:18])
        print('%-22s %s' % (k, ' | '.join(vals)))

    print()
    print('config.luac size:', {a: len(cfgs[a]) for a in apks})
    # global names present in each
    for a in apks:
        names = sorted(set(re.findall(r'^([A-Z_][A-Z0-9_]{2,})\s*=', cfgs[a], re.M)))
        print('\n%s globals (%d): %s' % (a, len(names), ', '.join(names[:40])))


if __name__ == '__main__':
    main()
