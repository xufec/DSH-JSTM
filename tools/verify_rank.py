# -*- coding: utf-8 -*-
"""验证排行榜组（12901/12902/12911/12912/12931）：
按 AutoConstruct 规格逐字节解析服务端应答，并核对"自己是第 1 名"的真实性。

用法：python tools/verify_rank.py
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_conformance import parse_full  # noqa: E402
from audit_sc_live import pack_frame, recv_exact, login  # noqa: E402
import socket  # noqa: E402

with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
    FIELDS = json.load(f)

RANK_CMDS = [12901, 12902, 12911, 12912, 12931]


def sc_spec(cmd):
    for k, v in FIELDS.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def main():
    ok = True
    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    login(s)
    s.settimeout(3)

    for cmd in RANK_CMDS:
        # 真机 CS：ord=0 num=5 flag=1 + 4 字节缓冲区残留
        body = bytes([0, 5, 1]) + b'\x56\x03\xe9\x00'
        s.sendall(pack_frame(cmd, body))
        got = None
        while True:
            hdr = recv_exact(s, 6)
            (ln, rcmd) = struct.unpack('>IH', hdr)
            payload = recv_exact(s, ln - 2)
            if rcmd == cmd:
                got = payload
                break
        spec = sc_spec(cmd)
        off, errs, unver = parse_full(got, spec)
        good = (not errs) and off == len(got)
        print('SC_%-6d len=%-4d 解析消耗=%-4d %s'
              % (cmd, len(got), off, 'PASS' if good else 'FAIL ' + str(errs)))
        if not good:
            ok = False
        # 语义核对
        my_ord = got[0]
        my_val = struct.unpack_from('>I', got, 1)[0]
        print('        my_ord=%d my_val=%d %s'
              % (my_ord, my_val,
                 '(空榜=指标未取证)' if cmd in (12902, 12911, 12912) else '(第 1 名 + 真实数值)'))
    s.close()
    print()
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
