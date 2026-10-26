#!/usr/bin/env python3
"""Print, per proto, the string constants used near sdkCallFunc calls.

This client initialises the ewan SDK from Lua via `cc.Device:sdkCallFunc(...)`.
To neutralise that we must know which Lua module issues which command
(init/login/...), so this lists the constants of every proto that mentions
sdkCallFunc.

usage:
  python tools/dump_sdk_calls.py assets/src/file_update.luac
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import parse_bytes  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def main():
    members = sys.argv[1:] or ['assets/src/file_update.luac',
                               'assets/src/game_start.luac',
                               'assets/src/sdk_function.luac']
    z = zipfile.ZipFile(APK)
    for m in members:
        try:
            r = parse_bytes(z.read(m))
        except Exception as e:
            print('!! %s: %r' % (m, e))
            continue
        print('==== %s (%d protos)' % (m, len(r.protos)))
        for i, pt in enumerate(r.protos):
            ss = pt.strings
            if not any('sdkCallFunc' in s for s in ss):
                continue
            print('  proto#%d %s' % (i, pt))
            for s in ss[:40]:
                print('      ', s[:110])


if __name__ == '__main__':
    main()
