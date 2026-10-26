# -*- coding: utf-8 -*-
"""R157 验收：`105xx` 收尾 15 条。

判据（★ 全部用门禁权威解析器做结构断言 —— 手写偏移只用于取值）：
  1. 15 条**结构精确**
  2. `10525`（无 code/msg）的 `uniq_id`/`item_id` 回显一致
  3. `10561` 的 `key`（**u16**）原样回
  4. `10537`/`10571` 回显 `item_id`

用法： python tools/verify_equip_batch3.py
"""
import io
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CMDS = (10506, 10517, 10523, 10524, 10525, 10526, 10531, 10533,
        10536, 10537, 10561, 10571, 10587, 10588, 10592)


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
        10506: struct.pack('>I', 1) + struct.pack('>I', 30800),
        10517: b'',
        10523: struct.pack('>I', 21903) + bytes([0, 0]),
        10524: struct.pack('>I', 21903) + struct.pack('>I', 0),
        10525: bytes([1]) + struct.pack('>I', 90001),
        10526: struct.pack('>H', 1) + b'1' + struct.pack('>I', 5),
        10531: struct.pack('>H', 0),
        10533: bytes([1]) + struct.pack('>I', 30800),
        10536: struct.pack('>I', 21903) + struct.pack('>I', 1),
        10537: struct.pack('>I', 21903),
        10561: struct.pack('>H', 7) + struct.pack('>H', 0),
        10571: struct.pack('>I', 21903) + bytes([0]),
        10587: struct.pack('>I', 1) + struct.pack('>I', 90001) + struct.pack('>I', 0),
        10588: struct.pack('>I', 90001) + struct.pack('>I', 1) + bytes([0]) + struct.pack('>I', 0),
        10592: b'',
    }

    bad = 0
    for cmd in CMDS:
        b = ask(cmd, bodies[cmd])
        r = g.audit_body(sc[str(cmd)], b, cmd)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (cmd, r['len'], r['consumed'], r['err']))
    print('\n== 15 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10525：无 code/msg，直接是 uniq_id/from_code/item_id
    b = ask(10525, bytes([1]) + struct.pack('>I', 90001))
    uni = struct.unpack_from('>I', b, 0)[0]
    fc = b[4]
    it = struct.unpack_from('>I', b, 5)[0]
    print('  10525 uniq_id=%d from_code=%d item_id=%d ⇒ %s'
          % (uni, fc, it, '✓' if (fc == 1 and it == 90001) else '✗'))
    ok = ok and fc == 1 and it == 90001

    # 10561：key 是 u16
    b = ask(10561, struct.pack('>H', 7) + struct.pack('>H', 0))
    k = struct.unpack_from('>H', b, 0)[0]
    print('  10561 key=%d（请求 7，u16）⇒ %s' % (k, '✓' if k == 7 else '✗'))
    ok = ok and k == 7

    # 10537：回显 item_id
    b = ask(10537, struct.pack('>I', 21903))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    ib = struct.unpack_from('>I', b, o)[0]
    print('  10537 回显 item_id=%d ⇒ %s' % (ib, '✓' if ib == 21903 else '✗'))
    ok = ok and ib == 21903

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
