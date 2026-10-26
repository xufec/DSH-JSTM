#!/usr/bin/env python3
"""Probe the game's own Lua runtime capabilities from the client's .luac files.

Used by the single-player effort: we need to know (a) what the plain-text
config.luac looks like as an injection point, and (b) which in-game Lua APIs
exist for scheduling (scheduler/timer) and sockets, so the embedded local
server can run without a separate process.
"""
import re
import sys
import zipfile

APK = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm_142165.apk'

# candidate Lua API names to look for inside the bytecode string tables
API_PATS = [
    b'schedule', b'unschedule', b'scheduler', b'performWithDelay', b'scheduleUpdate',
    b'Director', b'getScheduler', b'socket', b'require', b'coroutine', b'select',
    b'setTimeout', b'Timer', b'CCScheduler', b'cc.Director',
    b'GameNet', b'Send', b'SendProtocal', b'OnRecvMsg', b'Connect', b'CreateSocket',
    b'config', b'IS_PLATFORM_LOGIN', b'PLATFORM_NAME',
]


def main():
    z = zipfile.ZipFile(APK)
    names = z.namelist()

    print('=' * 30, 'config.luac (plain-text injection point)')
    raw = z.read('assets/src/config.luac')
    print('size', len(raw), 'head:', raw[:24])
    try:
        text = raw.decode('gbk')
    except Exception:
        text = raw.decode('utf-8', 'replace')
    print('---- first 3000 chars ----')
    print(text[:3000])
    print('---- last 1500 chars ----')
    print(text[-1500:])

    print()
    print('=' * 30, 'API availability across all .luac string tables')
    hits = {p: [] for p in API_PATS}
    for n in names:
        if not n.endswith('.luac'):
            continue
        d = z.read(n)
        for m in re.finditer(rb'[\x20-\x7e]{3,}', d):
            t = m.group()
            for p in API_PATS:
                if p in t and len(hits[p]) < 6:
                    hits[p].append((n, t.decode('ascii', 'replace')))
    for p in API_PATS:
        v = hits[p]
        print('%-22s %d  %s' % (p.decode(), len(v),
                               '; '.join('%s:%s' % (a.split("/")[-1], b) for a, b in v[:3])))


if __name__ == '__main__':
    main()
