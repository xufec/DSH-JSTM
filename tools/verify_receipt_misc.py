# -*- coding: utf-8 -*-
"""R180 验收：**跨家族 `{code,msg}` 族 44 条**（专用分支 750 → 795）。

判据：
  1. 44 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **回显**：`14213`/`18022`（`id`）、`13367`（`rid`）
  4. ★ **真校验**：`17520` 的 `rid` 非本服 ⇒ `code=0`

用法： python tools/verify_receipt_misc.py
"""
import io
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
RID = 1001

A = [11709, 11721, 11800, 12855, 14200, 14205, 14216, 14301, 14401, 14402, 14404,
     14500, 14504, 14507, 14807, 15001, 15003, 15012, 15015, 15102, 15206, 15300,
     15302, 15420, 15421, 15422, 15512, 15518, 15519, 15606, 15611, 15812, 15818,
     15819, 15821, 17199, 17405, 17508, 17511, 17514, 17521]
B = [14213, 18022]
C = [13367]
ALL = A + B + C

BODY = {14213: struct.pack('>I', 7), 18022: struct.pack('>I', 7),
        13367: bytes([1]) + struct.pack('>I', 1) + struct.pack('>I', RID) +
               struct.pack('>H', 1) + b'1' + struct.pack('>H', 1) + b'a' +
               struct.pack('>H', 1) + b'b' + struct.pack('>H', 1) + b'c',
        17520: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1' + struct.pack('>I', 1),
        14301: struct.pack('>I', 1), 14401: bytes([1]), 14402: bytes([1]),
        14504: struct.pack('>I', 1), 15003: struct.pack('>I', 1),
        15012: struct.pack('>I', 1) + struct.pack('>I', 2),
        15015: struct.pack('>I', 1) + struct.pack('>I', 2),
        15206: bytes([1, 1]), 15302: struct.pack('>I', 1), 15421: bytes([1]),
        15512: struct.pack('>I', 1), 15518: struct.pack('>I', 1) + struct.pack('>H', 0),
        15519: struct.pack('>I', 1), 15606: bytes([1]), 15812: struct.pack('>I', 1),
        15818: struct.pack('>I', 1) + struct.pack('>H', 0), 15819: struct.pack('>I', 1),
        15821: struct.pack('>I', 1), 17199: struct.pack('>I', 1),
        17405: struct.pack('>I', 1) + struct.pack('>H', 1) + b'1' + struct.pack('>I', 1) +
               struct.pack('>H', 1) + b'1' + bytes([1]),
        17514: struct.pack('>H', 1) + bytes([1]) + struct.pack('>H', 2) + b'hi'}


def ask(cmd, body=b''):
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(8.0)
    login(s)
    s.sendall(pack_frame(cmd, body))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        b = recv_exact(s, ln - 2)
        if rc == cmd:
            break
    s.close()
    return b


def load_gate():
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def main():
    ok = True
    g, sc = load_gate()
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())

    bad = 0
    for c in ALL:
        b = ask(c, BODY.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 44 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '回执族-C' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 44 and fb == 0) else '✗'))
    ok = ok and ded >= 44 and fb == 0

    # ★ 回显 id（B 组）
    for c in B:
        b = ask(c, struct.pack('>I', 7))
        m = struct.unpack_from('>H', b, 1)[0]
        got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
        if got != 7:
            ok = False
            print('  ✗ %d 回显 id=%d' % (c, got))
    print('  ★ B 组 2 条 `{…,id}` 回显一致 ⇒ %s' % ('✓' if ok else '✗'))

    # ★ 回显 rid（C 组）
    b = ask(13367, BODY[13367])
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  13367 回显 rid=%d ⇒ %s' % (got, '✓' if got == RID else '✗'))
    ok = ok and got == RID

    # ★ 真校验：17520 的 rid
    b1 = ask(17520, BODY[17520])
    b0 = ask(17520, struct.pack('>I', 9999) + struct.pack('>H', 1) + b'1' + struct.pack('>I', 1))
    print('  17520 本服 rid ⇒ code=%d ｜ 他人 ⇒ code=%d ⇒ %s'
          % (b1[0], b0[0], '✓' if (b1[0] == 1 and b0[0] == 0) else '✗'))
    ok = ok and b1[0] == 1 and b0[0] == 0

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
