#!/usr/bin/env python3
"""Fast-iteration channel: push a modified config.luac into the app's private
files dir, which the engine's search path consults BEFORE the packaged assets.

Why this works (verified from main.luac proto#1 `initSearchPath`):
    cc.FileUtils:getInstance():setSearchPaths({})
    addSearchPath(writable .. 'tryver/assets/res')
    addSearchPath(writable .. 'tryver/assets/src')
    addSearchPath(writable .. 'assets/res')
    addSearchPath(writable .. 'assets/src')   <-- before the packaged ones
    addSearchPath('res')
    addSearchPath('src')
`fullPathForFilename` returns the FIRST search path that contains the file, so a
config.luac placed under the writable dir shadows assets/src/config.luac inside
the APK. That lets us iterate on the injected Lua without rebuilding a 280 MB APK.

usage:
    python tools/push_config_luac.py probe          # distinct marker per candidate path
    python tools/push_config_luac.py push --marker M --is-platform-login false
    python tools/push_config_luac.py read           # pull back the winner
"""
import argparse
import os
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = 'com.shiyue.dldl.ewan.baidu2'
APK_DEFAULT = os.path.join(ROOT, 'patched', 'jstm_solo.apk')
MEMBER = 'assets/src/config.luac'
WRITABLE = '/data/data/%s/files' % PKG

# Candidate locations, in the order the engine would search them.
CANDIDATES = [
    'assets/src/config.luac',
    'assets/res/config.luac',
    'tryver/assets/src/config.luac',
    'tryver/assets/res/config.luac',
    'assets/src/src/config.luac',
    'config.luac',
]


def sh(cmd, check=True):
    p = subprocess.run(cmd, shell=isinstance(cmd, str),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and p.returncode != 0:
        raise SystemExit('cmd failed (%d): %s\n%s' % (p.returncode, cmd, p.stderr))
    return (p.stdout or '') + (p.stderr or '')


def extract(apk):
    with zipfile.ZipFile(apk) as z:
        return z.read(MEMBER)


def patch_is_platform_login(data, value):
    """Replace only the real assignment line, never the comments we injected."""
    out, hits = [], 0
    for line in data.split(b'\n'):
        s = line.strip()
        if s.startswith(b'IS_PLATFORM_LOGIN') and b'=' in s and not s.startswith(b'--'):
            line = b'IS_PLATFORM_LOGIN = ' + value.encode()
            hits += 1
        out.append(line)
    return b'\n'.join(out), hits


def append_marker(data, marker):
    block = ('\n-- [[DSH_PUSH]] pushed config marker\n'
             '_G.__dsh_pushmark = %r\n'
             'print("[DSH_PUSH] loaded pushed config.luac marker=" .. tostring(_G.__dsh_pushmark))\n'
             '-- ]] DSH_PUSH\n' % marker).encode('utf-8')
    return data + block


def uid_of():
    out = sh('adb shell "stat -c %%u:%%g /data/data/%s"' % PKG).strip()
    return out if ':' in out else 'u0_a56:u0_a56'


def push(local, remote, owner):
    d = os.path.dirname(remote)
    sh('adb shell "mkdir -p %s"' % d)
    sh('adb push "%s" "%s"' % (local, remote))
    sh('adb shell "chown %s %s; chmod 660 %s"' % (owner, remote, remote))
    return sh('adb shell "ls -l %s"' % remote).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['probe', 'push', 'read', 'clean'])
    ap.add_argument('--apk', default=APK_DEFAULT)
    ap.add_argument('--marker', default='DSH_MARK')
    ap.add_argument('--is-platform-login', default='false',
                    choices=['false', 'true', 'keep'])
    a = ap.parse_args()

    if a.mode == 'clean':
        for c in CANDIDATES:
            sh('adb shell "rm -f %s/%s"' % (WRITABLE, c), check=False)
        print('removed all pushed config.luac candidates')
        return

    if a.mode == 'read':
        for c in CANDIDATES:
            out = sh('adb shell "ls -l %s/%s 2>/dev/null; md5sum %s/%s 2>/dev/null"'
                     % (WRITABLE, c, WRITABLE, c), check=False).strip()
            print('--- %s\n%s' % (c, out or '   (absent)'))
        return

    base = extract(a.apk)
    owner = uid_of()
    tmpdir = os.path.join(ROOT, 'patched', '_push')
    os.makedirs(tmpdir, exist_ok=True)

    if a.mode == 'probe':
        # One distinct marker per candidate, so logcat tells us which path wins.
        for i, c in enumerate(CANDIDATES):
            data = append_marker(base, 'CAND%d:%s' % (i, c))
            lp = os.path.join(tmpdir, 'cand%d.luac' % i)
            with open(lp, 'wb') as f:
                f.write(data)
            print(push(lp, '%s/%s' % (WRITABLE, c), owner))
        print('\nprobe pushed %d candidates; restart the app and grep logcat for DSH_PUSH'
              % len(CANDIDATES))
        return

    data = base
    if a.is_platform_login != 'keep':
        data, hits = patch_is_platform_login(data, a.is_platform_login)
        print('IS_PLATFORM_LOGIN assignment lines rewritten: %d -> %s'
              % (hits, a.is_platform_login))
    data = append_marker(data, a.marker)
    lp = os.path.join(tmpdir, 'config.luac')
    with open(lp, 'wb') as f:
        f.write(data)
    print('built %s (%d bytes)' % (lp, len(data)))
    for c in CANDIDATES[:4]:
        print(push(lp, '%s/%s' % (WRITABLE, c), owner))


if __name__ == '__main__':
    main()
