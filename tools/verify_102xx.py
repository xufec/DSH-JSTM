# -*- coding: utf-8 -*-
"""R159 验收：`102xx` 家族 10 条。

判据：
  1. 全部**结构精确**（门禁权威解析器）
  2. `10216`/`10233` 回显 `id`；`10233` 的 `time` 是**真实当前时间**
  3. `10299` 的 `args` **原样回传**
  4. `10211` 的线路表 1 条

用法： python tools/verify_102xx.py
"""
import io
import os
import socket
import struct
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CMDS = (10211, 10296, 10297, 10210, 10216, 10233, 10299, 10222, 10232, 10207)


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
    bodies = {
        10211: struct.pack('>I', 1), 10296: b'', 10297: b'', 10210: bytes([1]),
        10216: struct.pack('>I', 77), 10233: struct.pack('>I', 88),
        10299: struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1' +
               struct.pack('>H', 2) + struct.pack('>I', 11) + struct.pack('>I', 22),
        10222: struct.pack('>I', 1) + struct.pack('>I', 10) + struct.pack('>I', 20),
        10232: struct.pack('>I', 80001) + struct.pack('>I', 1),
        10207: b'',
    }
    bad = 0
    for cmd in CMDS:
        b = ask(cmd, bodies[cmd])
        r = g.audit_body(sc[str(cmd)], b, cmd)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (cmd, r['len'], r['consumed'], r['err']))
    print('\n== 10 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10216 回显 id
    b = ask(10216, struct.pack('>I', 77))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    i1 = struct.unpack_from('>I', b, o)[0]
    print('  10216 回显 id=%d（请求 77）⇒ %s' % (i1, '✓' if i1 == 77 else '✗'))
    ok = ok and i1 == 77

    # 10233 回显 id + time 真实
    b = ask(10233, struct.pack('>I', 88))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    i2 = struct.unpack_from('>I', b, o)[0]
    t2 = struct.unpack_from('>I', b, o + 4)[0]
    now = int(time.time())
    good = i2 == 88 and abs(now - t2) < 120
    print('  10233 id=%d time=%d（现在 %d，差 %ds）⇒ %s'
          % (i2, t2, now, now - t2, '✓' if good else '✗'))
    ok = ok and good

    # 10299 的 args 是**两层嵌套表**（`args[].list[].list2`）⇒ 本服无该数据 ⇒ 空表
    body = (struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1' +
            struct.pack('>H', 2) + struct.pack('>H', 11) + struct.pack('>H', 22))
    b = ask(10299, body)
    n = struct.unpack_from('>H', b, 0)[0]
    print('  10299 args 条目=%d（嵌套表，本服无源 ⇒ 空）⇒ %s' % (n, '✓' if n == 0 else '✗'))
    ok = ok and n == 0

    # 10211 线路表
    b = ask(10211, struct.pack('>I', 1))
    n = struct.unpack_from('>H', b, 0)[0]
    print('  10211 all_line_status 条目=%d ⇒ %s' % (n, '✓' if n == 1 else '✗'))
    ok = ok and n == 1

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
