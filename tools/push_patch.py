#!/usr/bin/env python3
"""Push a Lua hot patch into the app's writable dir (loaded by the APK bootstrap).

The injected config.luac contains a fixed bootstrap that reads
    <writable>/dsh_patch.lua
via io.open and executes it with loadstring. Because the engine's search path
puts the packaged "assets/" FIRST (verified from logcat printSearchPaths), the
writable dir cannot shadow packaged files -- but an absolute-path io.open can
read anything the app owns, which is what we exploit here.

usage:
    python tools/push_patch.py server/dsh_patch.lua
    python tools/push_patch.py --remove
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PKG = 'com.shiyue.dldl.ewan.baidu2'
REMOTE = '/data/data/%s/files/dsh_patch.lua' % PKG
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return (p.stdout or '') + (p.stderr or '')


def main():
    if '--remove' in sys.argv:
        print(sh('adb shell "rm -f %s"' % REMOTE).strip())
        return
    local = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'server', 'dsh_patch.lua')
    uid = sh('adb shell "stat -c %%u:%%g /data/data/%s"' % PKG).strip() or 'u0_a56:u0_a56'
    print(sh('adb push "%s" "%s"' % (local, REMOTE)).strip())
    print(sh('adb shell "chown %s %s; chmod 660 %s; ls -l %s"'
             % (uid, REMOTE, REMOTE, REMOTE)).strip())


if __name__ == '__main__':
    main()
