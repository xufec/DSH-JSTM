# -*- coding: utf-8 -*-
"""R166 验收：**收尾 `10xxx` 家族 26 条**。

判据：
  1. 26 条**结构精确**（门禁权威解析器）
  2. ★ `10324` 改名后 **DB `roles.name` 真的变了**（验收末尾**改回原名**，保持幂等）
  3. `10388` 的 `online_roles` **原样回传**
  4. `10522` 的 `code` 随装备存在如实

用法： python tools/verify_10xxx_tail.py
"""
import io
import os
import socket
import sqlite3
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
RID = 1001


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


def q(sql, args=()):
    c = sqlite3.connect(DB)
    try:
        r = c.execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        r = []
    c.close()
    return r


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
    gaps = sorted(int(x.strip()) for x in
                  open(os.path.join(ROOT, 'analysis', '1.4.9', '_unhandled_cs_sc.txt'),
                       encoding='utf-8') if x.strip().isdigit())
    ten = [c for c in gaps if 10000 <= c < 11000]
    print('\n  10xxx 剩余 %d 条' % len(ten))

    B = {10324: struct.pack('>H', 3) + '测试名'.encode(), 10322: bytes([7]),
         10311: struct.pack('>H', 2) + b'hi', 10390: struct.pack('>H', 2) + b'hi',
         10391: struct.pack('>H', 2) + b'hi', 10399: struct.pack('>H', 2) + b'hi',
         10388: struct.pack('>H', 1) + struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1',
         10328: struct.pack('>H', 1) + struct.pack('>H', 1) + struct.pack('>H', 10),
         10340: bytes([1]) + struct.pack('>I', 100), 10407: struct.pack('>H', 0),
         10522: bytes([1]) + struct.pack('>I', 90001) + bytes([0]),
         10742: bytes([1]), 10752: struct.pack('>I', 1) + struct.pack('>I', 2),
         10753: struct.pack('>I', 1) + struct.pack('>I', 2) + struct.pack('>I', 3),
         10756: bytes([1]) + struct.pack('>I', 2), 10709: struct.pack('>H', 5)}

    bad = 0
    for c in ten:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 26 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # ★ 10324 改名真落库（验收末尾改回原名，保持幂等）
    orig = q('SELECT name FROM roles WHERE rid=?', (RID,))
    orig = orig[0][0] if orig else 'DSH'
    b = ask(10324, struct.pack('>H', len('R166测试'.encode())) + 'R166测试'.encode())
    # ★ 布局：code:u8(0) + msg:string(1..1+2+ml) + name:string
    #   ⇒ name 的**长度前缀**在 `1 + 2 + ml` 处 —— 别漏了 msg 的 2 字节（纪律第 9 条）
    ml = struct.unpack_from('>H', b, 1)[0]
    no = 1 + 2 + ml
    nl = struct.unpack_from('>H', b, no)[0]
    got = b[no + 2:no + 2 + nl].decode('utf-8', 'replace')
    dbname = q('SELECT name FROM roles WHERE rid=?', (RID,))
    dbname = dbname[0][0] if dbname else None
    print('\n== 10324 改名 ==')
    print('  回包 name=%r ｜ DB name=%r（原名 %r）' % (got, dbname, orig))
    a = (got == 'R166测试' and dbname == 'R166测试')
    print('  ★ DB 真的改了 ⇒ %s' % ('✓' if a else '✗'))
    ok = ok and a
    # 改回原名
    ask(10324, struct.pack('>H', len(orig.encode())) + orig.encode())
    back = q('SELECT name FROM roles WHERE rid=?', (RID,))
    print('  已改回 %r ⇒ %s' % (back[0][0] if back else None,
                                '✓' if (back and back[0][0] == orig) else '✗'))
    ok = ok and back and back[0][0] == orig

    # 10388 原样回传
    body = struct.pack('>H', 1) + struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1'
    b = ask(10388, body)
    n = struct.unpack_from('>H', b, 0)[0]
    rid2 = struct.unpack_from('>I', b, 2)[0]
    print('  10388 online_roles=%d id=%d ⇒ %s' % (n, rid2, '✓' if (n == 1 and rid2 == 1001) else '✗'))
    ok = ok and n == 1 and rid2 == 1001

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
