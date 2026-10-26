# -*- coding: utf-8 -*-
"""R135 验收：座椅 `20801`、翅膀 `11698`/`11699`、神器 `15701`。

判据：查询型以**数据库真实值**为准；`15701` 以 `status` 变化为准。

用法： python tools/verify_queries.py
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
    r = c.execute(sql, args).fetchone()
    c.close()
    return r


def main():
    ok = True

    # ---- 20801 查座椅阶
    adm('chair?stage=0')
    b0 = ask(20801)
    adm('chair?stage=7&power=555&luck=3&res_stage=1&grow=99')
    b1 = ask(20801)
    db = q('SELECT stage FROM role_chair WHERE rid=?', (RID,))
    print('\n== 20801 查座椅阶 ==')
    print('  无座椅 result=%d stage=%d ｜ 有座椅 result=%d stage=%d（DB=%s）'
          % (b0[0], b0[3 + struct.unpack_from('>H', b0, 1)[0]],
             b1[0], b1[3 + struct.unpack_from('>H', b1, 1)[0]], db[0] if db else None))
    a1 = b0[0] == 0 and b1[0] == 1 and db and db[0] == 7
    print('  ★ 读的是真实 DB 值（0 阶→result 0；7 阶→result 1）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 11698 / 11699 查翅膀
    adm('wing?wing_id=8801&star=6&color=2&power=1234')
    b8 = ask(11698)
    b9 = ask(11699)
    wid8 = struct.unpack_from('>I', b8, 0)[0]
    st8 = b8[4]
    pw8 = struct.unpack_from('>I', b8, 5)[0]
    wid9 = struct.unpack_from('>I', b9, 3 + struct.unpack_from('>H', b9, 1)[0])[0]
    off9 = 3 + struct.unpack_from('>H', b9, 1)[0] + 4
    st9 = b9[off9]
    print('\n== 11698 / 11699 查翅膀 ==')
    print('  11698: wing_id=%d ★star=%d power=%d' % (wid8, st8, pw8))
    print('  11699: wing_id=%d ★star=%d code=%d' % (wid9, st9, b9[0]))
    a2 = wid8 == 8801 and st8 == 6 and pw8 == 1234 and wid9 == 8801 and st9 == 6
    print('  ★ 与 DB 一致（wing_id=8801 star=6 power=1234）⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 15701 神器装备
    adm('shenqi?id=10001&lev=1&star=0')
    adm('shenqi?id=10002&lev=1&star=0')
    b = ask(15701, struct.pack('>I', 10002))
    st = q('SELECT status FROM role_shenqi WHERE rid=? AND sid=?', (RID, 10001))
    st2 = q('SELECT status FROM role_shenqi WHERE rid=? AND sid=?', (RID, 10002))
    print('\n== 15701 神器装备 ==')
    print('  result=%d   status: 10001=%s 10002=%s'
          % (b[0], st[0] if st else None, st2[0] if st2 else None))
    a3 = b[0] == 1 and st and st2 and st2[0] == 1
    print('  ★ status 真的置 1 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3
    b = ask(15701, struct.pack('>I', 99999999))
    a4 = b[0] == 0
    print('  无效 id ⇒ result=%d ⇒ %s' % (b[0], '✓' if a4 else '✗'))
    ok = ok and a4

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
