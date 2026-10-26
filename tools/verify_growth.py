# -*- coding: utf-8 -*-
"""R132 验收：`11601`（翅膀升级）/ `11603`（翅膀升星）/ `20802`（座椅升阶）
—— **都真改状态**，判据以数据库为准。

用法： python tools/verify_growth.py
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

    # ---- 11601 翅膀升级：wing_id 应推进到 WingUpstar 序列的下一档
    adm('wing?wing_id=0&star=0&color=0&power=0')
    b = ask(11601, bytes([0]))
    wid1 = struct.unpack_from('>I', b, 3)[0]
    db1 = q('SELECT wing_id FROM role_wing WHERE rid=?', (RID,))
    print('\n== 11601 翅膀升级 ==')
    print('  回包 wing_id=%d  star=%d   DB wing_id=%s' % (wid1, b[7], db1[0] if db1 else None))
    b = ask(11601, bytes([0]))
    wid2 = struct.unpack_from('>I', b, 3)[0]
    print('  再升一次 wing_id=%d' % wid2)
    a1 = db1 is not None and db1[0] == wid1 and wid1 > 0
    print('  ★ 数据库 wing_id 真的被推进（且回包一致）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 11603 翅膀升星：star +1（★ 本命令 star 是 u16）
    adm('wing?wing_id=8801&star=3&color=2&power=999')
    b = ask(11603, bytes([1]))
    star = struct.unpack_from('>H', b, 4)[0]
    db2 = q('SELECT star FROM role_wing WHERE rid=?', (RID,))
    print('\n== 11603 翅膀升星 ==')
    print('  回包 color=%d star=%d   DB star=%s' % (b[3], star, db2[0] if db2 else None))
    a2 = db2 is not None and db2[0] == 4 and star == 4
    print('  ★ star 真的 +1（3→4）⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2
    # is_buy=0 ⇒ 不升
    b = ask(11603, bytes([0]))
    db3 = q('SELECT star FROM role_wing WHERE rid=?', (RID,))
    a3 = db3 is not None and db3[0] == 4
    print('  is_buy=0 ⇒ 不升（star 仍 %s）⇒ %s' % (db3[0] if db3 else None, '✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 20802 座椅升阶：stage 设为请求值
    adm('chair?stage=1')
    b = ask(20802, bytes([5]))
    db4 = q('SELECT stage FROM role_chair WHERE rid=?', (RID,))
    print('\n== 20802 座椅升阶 ==')
    print('  result=%d 回包 stage=%d   DB stage=%s' % (b[0], b[3 + struct.unpack_from('>H', b, 1)[0]], db4[0] if db4 else None))
    a4 = db4 is not None and db4[0] == 5 and b[0] == 1
    print('  ★ stage 真的从 1 变成 5 ⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
