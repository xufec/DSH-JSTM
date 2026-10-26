#!/usr/bin/env python3
"""Compare the three APKs' asset payloads: which one can actually go standalone.

A standalone build must carry ALL game content locally (no CDN). So we compare
how many .luac modules and config/data assets each package ships.

usage:
  python tools/compare_assets.py
"""
import os
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANZ = os.path.join(HERE, 'anzbao')


def main():
    apks = [n for n in sorted(os.listdir(ANZ)) if n.endswith('.apk')]
    data = {}
    for name in apks:
        z = zipfile.ZipFile(os.path.join(ANZ, name))
        names = z.namelist()
        d = {
            'total entries': len(names),
            'assets/src luac': sum(1 for n in names if n.startswith('assets/src') and n.endswith('.luac')),
            'assets/res': sum(1 for n in names if n.startswith('assets/res')),
            'config/*.luac': sum(1 for n in names if '/config/' in n and n.endswith('.luac')),
            'game/**/*.luac': sum(1 for n in names if '/game/' in n and n.endswith('.luac')),
            'sys/*.luac': sum(1 for n in names if '/sys/' in n and n.endswith('.luac')),
            'asset bytes MB': round(sum(z.getinfo(n).file_size for n in names
                                        if n.startswith('assets')) / 1048576, 1),
        }
        # key files that a standalone build depends on
        for key in ('assets/src/config.luac', 'assets/src/file_update.luac',
                    'assets/src/game_start.luac', 'assets/src/sys/gamenet.luac',
                    'assets/src/game/login/denglu_ctrl.luac'):
            d[key.split('/')[-1]] = 'yes' if key in names else '-'
        data[name] = d

    keys = list(next(iter(data.values())).keys())
    print('%-22s %s' % ('metric', ' | '.join('%-18s' % a for a in apks)))
    for k in keys:
        print('%-22s %s' % (k, ' | '.join('%-18s' % data[a].get(k) for a in apks)))


if __name__ == '__main__':
    main()
