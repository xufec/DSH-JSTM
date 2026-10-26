#!/usr/bin/env python3
"""Locate the wire-framing code: scan all .luac for packing/networking keywords
and report which files/prototypes contain them."""
import sys, os, re, zipfile, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader

KEYS = ['WriteUShort', 'ReadUShort', 'WriteUInt', 'WriteUChar', 'WriteString',
        'WriteFMT', 'ReadFMT', 'WriteUByte', 'WriteInt', 'WriteLong',
        'pack', 'unpack', 'GameNet', 'OnNetRecv', 'OnNetSend', 'SendProtocal',
        'sendData', 'recvData', 'm_msg_type', 'm_value_names', 'm_format',
        'setConnectionTimeout', 'socket', 'Socket', 'tcp', 'sendMsg', 'byte2',
        'headLen', 'header', 'msgid', 'msgId', 'GetPrototype']


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.endswith('.luac')]
    hits = collections.defaultdict(set)
    proto_hits = []
    for n in names:
        try:
            r = Reader(z.read(n))
            r.parse()
        except Exception:
            continue
        for pt in r.protos:
            found = {k for k in KEYS if k in pt.strings}
            if len(found) >= 2:
                hits[n].update(found)
                proto_hits.append((len(found), n, pt.index, sorted(found)))
    print('--- files with >=2 framing keywords ---')
    for n, ks in sorted(hits.items(), key=lambda x: -len(x[1])):
        print('%-70s %s' % (n, ','.join(sorted(ks))))
    print()
    print('--- top prototypes ---')
    for cnt, n, idx, ks in sorted(proto_hits, reverse=True)[:15]:
        print('%2d  %-60s proto#%-4d %s' % (cnt, n.split('/')[-1], idx, ','.join(ks)))


if __name__ == '__main__':
    main()