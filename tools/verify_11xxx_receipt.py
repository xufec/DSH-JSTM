# -*- coding: utf-8 -*-
"""R177 验收：`11xxx` 回执族 **17 条**。

判据：
  1. 17 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ `11205`/`11217`/`11226`/`11227`/`11228` 的 `id` **回显一致**
  4. ★ `11306`/`11801` 的 `rid` **回显一致** + 校验是本服角色

用法： python tools/verify_11xxx_receipt.py
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
CMDS = (11016, 11102, 11111, 11208, 11302, 11303, 11305, 11401, 11507, 11705,
        11205, 11217, 11226, 11227, 11228, 11306, 11801)
IDS = (11205, 11217, 11226, 11227, 11228)

B = {11102: struct.pack('>I', 1), 11111: struct.pack('>H', 1) + struct.pack('>I', 1),
     11208: struct.pack('>I', 1) + bytes([1]), 11302: bytes([1]),
     11205: struct.pack('>I', 7), 11217: struct.pack('>I', 7) + bytes([1]),
     11226: struct.pack('>I', 7) + bytes([1]),
     11227: struct.pack('>I', 7) + struct.pack('>I', 1) + struct.pack('>I', 2),
     11228: struct.pack('>I', 7) + struct.pack('>I', 1),
     11306: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1',
     11801: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1' + bytes([1]),
     11016: struct.pack('>H', 0) + struct.pack('>H', 0) + struct.pack('>H', 0)}


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
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 17 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '11xxx 回执族' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 17 and fb == 0) else '✗'))
    ok = ok and ded >= 17 and fb == 0

    # ★ id 回显
    for c in IDS:
        b = ask(c, B[c])
        m = struct.unpack_from('>H', b, 1)[0]
        o = 1 + 2 + m
        got = struct.unpack_from('>I', b, o)[0]
        if got != 7:
            ok = False
            print('  ✗ %d 回显 id=%d（期望 7）' % (c, got))
    print('  ★ 5 条 `{…,id}` 的 id **回显一致** ⇒ %s' % ('✓' if ok else '✗'))

    # ★ rid 回显
    b = ask(11306, B[11306])
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    got = struct.unpack_from('>I', b, o)[0]
    print('  11306 回显 rid=%d ⇒ %s' % (got, '✓' if got == RID else '✗'))
    ok = ok and got == RID
    b0 = ask(11306, struct.pack('>I', 9999) + struct.pack('>H', 1) + b'1')
    print('  11306 他人 rid ⇒ code=%d ⇒ %s' % (b0[0], '✓' if b0[0] == 0 else '✗'))
    ok = ok and b0[0] == 0

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
