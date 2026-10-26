# -*- coding: utf-8 -*-
"""R133 验收：神器 `15703`/`15702` + 法宝 `18906`/`18901`（**都真改状态**）。

用法： python tools/verify_growth2.py
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

    # ---- 15703 神器升级
    adm('shenqi?id=10001&lev=3&star=2')
    b = ask(15703, struct.pack('>I', 10001))
    db = q('SELECT lev FROM role_shenqi WHERE rid=? AND sid=?', (RID, 10001))
    print('\n== 15703 神器升级 ==')
    print('  result=%d id=%d new_lev=%d new_star=%d   DB lev=%s'
          % (b[0], struct.unpack_from('>I', b, 3)[0],
             struct.unpack_from('>H', b, 7)[0], struct.unpack_from('>H', b, 9)[0],
             db[0] if db else None))
    a1 = db is not None and db[0] == 4 and b[0] == 1
    print('  ★ lev 真的 3→4 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1
    # 无效 id ⇒ result=0
    b = ask(15703, struct.pack('>I', 99999999))
    a2 = b[0] == 0
    print('  无效 id ⇒ result=%d ⇒ %s' % (b[0], '✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 15702 切换使用中的神器
    adm('shenqi?id=10002&lev=1&star=0')
    b = ask(15702, struct.pack('>I', 10002))
    st1 = q('SELECT status FROM role_shenqi WHERE rid=? AND sid=?', (RID, 10001))
    st2 = q('SELECT status FROM role_shenqi WHERE rid=? AND sid=?', (RID, 10002))
    print('\n== 15702 切换神器 ==')
    print('  result=%d new_use_id=%d   status: 10001=%s 10002=%s'
          % (b[0], struct.unpack_from('>I', b, 3 + struct.unpack_from('>H', b, 1)[0])[0],
             st1[0] if st1 else None, st2[0] if st2 else None))
    a3 = st1 and st2 and st1[0] == 0 and st2[0] == 1
    print('  ★ status 真的从 10001 切到 10002 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 18906 法宝升级
    adm('fabao?id=1&bid=20001&level=5&stage=2')
    b = ask(18906, struct.pack('>I', 20001) + bytes([0]) + struct.pack('>H', 1))
    db = q('SELECT level FROM role_fabao WHERE rid=? AND bid=?', (RID, 20001))
    print('\n== 18906 法宝升级 ==')
    print('  result=%d bid=%d pre=%d post=%d   DB level=%s'
          % (b[0], struct.unpack_from('>I', b, 1)[0],
             struct.unpack_from('>H', b, 5)[0], struct.unpack_from('>H', b, 7)[0],
             db[0] if db else None))
    a4 = db is not None and db[0] == 6 and b[0] == 1
    print('  ★ level 真的 5→6 ⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    # ---- 18901 法宝装备
    b = ask(18901, struct.pack('>I', 20001))
    db = q('SELECT pos FROM role_fabao WHERE rid=? AND bid=?', (RID, 20001))
    print('\n== 18901 法宝装备 ==')
    print('  result=%d bid=%d   DB pos=%s' % (b[0], struct.unpack_from('>I', b, 1)[0],
                                              db[0] if db else None))
    a5 = db is not None and db[0] == 1 and b[0] == 1
    print('  ★ pos 真的置 1 ⇒ %s' % ('✓' if a5 else '✗'))
    ok = ok and a5

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
