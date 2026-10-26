# -*- coding: utf-8 -*-
"""R134 验收：法宝家族 `18904`（真升阶）/`18910`（真分解）/`18908` + `18902`/`18903`/`18905`（诚实校验）。

用法： python tools/verify_fabao_family.py
"""
import io
import json
import os
import socket
import sqlite3
import struct
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), 'server', 'state', 'roles.db')
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


def adm(qs):
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/' + qs, timeout=8).read().decode('utf-8'))


def q(sql, args=()):
    c = sqlite3.connect(DB)
    r = c.execute(sql, args).fetchall()
    c.close()
    return r


def main():
    ok = True

    # ---- 18904 真升阶
    adm('fabao?id=7&bid=20007&level=1&stage=0')
    b = ask(18904, struct.pack('>I', 20007) + bytes([3]))
    db = q('SELECT stage FROM role_fabao WHERE rid=? AND bid=?', (RID, 20007))
    print('\n== 18904 法宝升阶 ==')
    print('  result=%d bid=%d   DB stage=%s' % (b[0], struct.unpack_from('>I', b, 1)[0],
                                               db[0][0] if db else None))
    a1 = db and db[0][0] == 3 and b[0] == 1
    print('  ★ stage 真的 0→3 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1
    b = ask(18904, struct.pack('>I', 99999999) + bytes([1]))
    a2 = b[0] == 0
    print('  无效 bid ⇒ result=%d ⇒ %s' % (b[0], '✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 18910 真分解
    adm('fabao?id=8&bid=20008&level=1')
    n0 = len(q('SELECT id FROM role_fabao WHERE rid=?', (RID,)))
    b = ask(18910, struct.pack('>I', 8) + struct.pack('>H', 1))
    n1 = len(q('SELECT id FROM role_fabao WHERE rid=?', (RID,)))
    print('\n== 18910 法宝分解 ==')
    print('  result=%d id=%d count=%d   行数 %d→%d'
          % (b[0], struct.unpack_from('>I', b, 1)[0],
             struct.unpack_from('>H', b, 5)[0], n0, n1))
    a3 = b[0] == 1 and n1 == n0 - 1
    print('  ★ 法宝真的被删掉 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 18902/18903/18905 诚实校验（存在 ⇒ result=1；不存在 ⇒ 0）
    adm('fabao?id=9&bid=20009&level=1')
    r1 = ask(18902, struct.pack('>I', 20009))[0]
    r0 = ask(18902, struct.pack('>I', 99999999))[0]
    r3 = ask(18903, struct.pack('>I', 20009))[0]
    r5 = ask(18905, struct.pack('>I', 20009))[0]
    print('\n== 18902/18903/18905（诚实校验）==')
    print('  18902 存在=%d 不存在=%d ；18903=%d ；18905=%d' % (r1, r0, r3, r5))
    a4 = r1 == 1 and r0 == 0 and r3 == 1 and r5 == 1
    print('  ★ 存在 ⇒ 1、不存在 ⇒ 0 ⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    # ---- 18908 用道具（未接消耗，只校验）
    b = ask(18908, struct.pack('>I', 21903) + struct.pack('>H', 1))
    print('\n== 18908 用道具 ==')
    print('  result=%d item_bid=%d' % (b[0], struct.unpack_from('>I', b, 1)[0]))
    a5 = b[0] == 1
    print('  ★ 结构正确且 result=1 ⇒ %s' % ('✓' if a5 else '✗'))
    ok = ok and a5

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
