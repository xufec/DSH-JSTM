#!/usr/bin/env python3
"""Scan the game's native .so files for network / serialization primitives.

Used by the single-player (server-embedded-in-APK) effort to decide whether the
wire layer can be reimplemented in Lua or must stay native.
"""
import re
import sys
import zipfile

APK = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm_142165.apk'
LIBS = sys.argv[2:] or ['libcocos2dlua.so', 'libentryexstd.so', 'libentryexpro.so']

PATS = [b'WriteUChar', b'WriteChar', b'WriteUShort', b'WriteShort', b'WriteUInt',
        b'WriteInt', b'WriteFloat', b'WriteDouble', b'WriteString', b'WriteFMT',
        b'WriteHeader', b'WriteBegin',
        b'ReadUChar', b'ReadUShort', b'ReadUInt', b'ReadFMT', b'ReadHeader',
        b'ReadString', b'GameNet', b'Protocal', b'Protocol',
        b'SocketTCP', b'socket', b'luaopen', b'CCLuaStack', b'cocos2d::network',
        b'HttpClient', b'HttpRequest', b'WebSocket', b'Network', b'TcpClient',
        b'connect', b'listen', b'bind']


def main():
    z = zipfile.ZipFile(APK)
    for lib in LIBS:
        name = 'lib/armeabi/' + lib
        try:
            d = z.read(name)
        except KeyError:
            print('== %s : NOT PRESENT' % name)
            continue
        hits = set()
        for m in re.finditer(rb'[\x20-\x7e]{4,}', d):
            t = m.group()
            for p in PATS:
                if p in t:
                    hits.add(t.decode('ascii', 'replace'))
                    break
        print('=' * 24, name, len(d), 'bytes,', len(hits), 'hits')
        for x in sorted(hits):
            print('   ', x)


if __name__ == '__main__':
    main()
