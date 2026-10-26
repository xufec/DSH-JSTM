#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decode captured game-server TCP frames.

Framing derived from the client's own traffic (see server_list_protocol.md /
进服 notes):

    [u32 BE payload_len][u16 BE cmd][body ...]
    payload_len = 2 (cmd) + len(body)

Inside the body, strings are [u16 BE len][bytes].
(Confirmed on cmd 10001: 00 0b 'game_client'.)

usage: python tools/decode_frames.py server/logs/tcp_1.bin [...]
"""
import glob
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from proto_defs import BY_CMD          # noqa: E402
except Exception:
    BY_CMD = {}


def names(cmd):
    v = BY_CMD.get(cmd)
    if not v:
        return ''
    try:
        return ','.join(v)[:70]
    except Exception:
        return str(v)[:70]


def decode(data):
    """Yield (offset, cmd, body) frames; stop at the first truncated frame."""
    off = 0
    out = []
    while off + 6 <= len(data):
        ln = struct.unpack_from('>I', data, off)[0]
        cmd = struct.unpack_from('>H', data, off + 4)[0]
        if ln < 2 or off + 4 + ln > len(data):
            out.append((off, None, data[off:], ln))
            break
        body = data[off + 6:off + 4 + ln]
        out.append((off, cmd, body))
        off += 4 + ln
    return out


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = sorted(glob.glob(os.path.join('server', 'logs', 'tcp_*.bin')))
    for p in paths:
        if not os.path.exists(p):
            continue
        data = open(p, 'rb').read()
        print('=== %s (%d bytes) ===' % (p, len(data)))
        for off, cmd, body, *rest in decode(data):
            if cmd is None:
                ln = rest[0] if rest else '?'
                print('  @%04x  !! truncated: declared len=%s, have %d bytes'
                      % (off, ln, len(body)))
                print('        %s' % body[:48].hex(' '))
                continue
            print('  @%04x  cmd=%-6d %-38s body(%d)=%s'
                  % (off, cmd, names(cmd), len(body), body[:40].hex(' ')))
            # best-effort string preview: [u16 len][bytes]
            if len(body) >= 2:
                sl = struct.unpack_from('>H', body, 0)[0]
                if 0 < sl <= len(body) - 2:
                    s = body[2:2 + sl]
                    print('          first string len=%d %r' % (sl, s))


if __name__ == '__main__':
    main()
