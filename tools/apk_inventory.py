#!/usr/bin/env python3
"""Inventory the three shipped APKs: package, version, SDK flavour, asset layout.

Goal: decide how to combine them for a single standalone build (which client is
the best host, what each one carries that the others lack).

usage:
  python tools/apk_inventory.py
"""
import os
import re
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANZ = os.path.join(HERE, 'anzbao')


def text_strs(d, minlen=5):
    return set(m.group().decode('utf-8', 'replace')
               for m in re.finditer(rb'[\x20-\x7e]{%d,}' % minlen, d))


def main():
    for name in sorted(os.listdir(ANZ)):
        if not name.endswith('.apk'):
            continue
        path = os.path.join(ANZ, name)
        z = zipfile.ZipFile(path)
        mf = z.read('AndroidManifest.xml')
        s = text_strs(mf, 4)
        pkgs = sorted(x for x in s if x.startswith('com.') and x.count('.') >= 2)

        # SDK hints from libs + dex strings
        libs = sorted(set(n.split('/')[2] for n in z.namelist()
                          if n.startswith('lib/') and n.count('/') >= 2))
        dex = z.read('classes.dex') if 'classes.dex' in z.namelist() else b''
        hints = []
        for tag, pat in (('ewan-supersdk', b'cn/ewan/supersdk'),
                         ('qihoo360', b'com/qihoo'),
                         ('baidu', b'com/baidu'),
                         ('91cw', b'com/cw/platform'),
                         ('duoku', b'com/duoku')):
            if pat in dex:
                hints.append(tag)

        cfg = None
        for c in ('assets/src/config.luac', 'assets/src/config.lua'):
            if c in z.namelist():
                raw = z.read(c)
                cfg = raw.decode('gbk', 'replace')
                break
        keys = {}
        if cfg:
            for k in ('GAME_NAME', 'PLATFORM_NAME', 'NOW_VERSION', 'BUILD_VERSION',
                      'IS_PLATFORM_LOGIN', 'MUTIL_LOGIN', 'URL_LUA_CONFIG'):
                m = re.search(k + r'\s*=\s*([^\n\r]+)', cfg)
                if m:
                    keys[k] = m.group(1).strip()[:60]

        nluac = sum(1 for n in z.namelist() if n.endswith('.luac'))
        has_sock = b'luaopen_socket_core' in z.read('lib/armeabi/libcocos2dlua.so') \
            if 'lib/armeabi/libcocos2dlua.so' in z.namelist() else False

        print('=' * 78)
        print('%-24s %8.1f MB  luac=%d  lua-socket=%s' %
              (name, os.path.getsize(path) / 1048576, nluac, has_sock))
        print('  packages : %s' % (pkgs[:3] or '(binary pool only)'))
        print('  sdk      : %s' % (', '.join(hints) or '-'))
        print('  libs     : %s' % ', '.join(libs[:12]))
        for k, v in keys.items():
            print('  %-16s %s' % (k, v))


if __name__ == '__main__':
    main()
