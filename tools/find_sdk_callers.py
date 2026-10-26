#!/usr/bin/env python3
"""Find every Lua proto that calls sdkCallFunc, across the whole client.

The ewan SDK is driven from Lua through the native bridge
`cc.Device:sdkCallFunc(cmd, ...)`. We need to know which command names the game
sends (init? login? pay? exit?) to decide whether the SDK can be short-circuited
from an injected script.

usage:
  python tools/find_sdk_callers.py
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import parse_bytes  # noqa: E402

APK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'anzbao', 'jstm_142165.apk')


def main():
    z = zipfile.ZipFile(APK)
    for n in z.namelist():
        if not n.endswith('.luac'):
            continue
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        for i, pt in enumerate(r.protos):
            ss = pt.strings
            if not any('sdkCallFunc' in s for s in ss):
                continue
            if not any('Device' in s for s in ss):
                continue
            print('==== %s proto#%d  params=%d' % (n, i, pt.numparams))
            for s in ss[:45]:
                print('     ', s[:110])
            print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
