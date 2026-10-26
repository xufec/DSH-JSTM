# -*- coding: utf-8 -*-
"""R121 验收：`13500`（建宗门）/ `13803`（摆摊）/ `18600`（坐骑地图态）/ `13020`（进镇魔塔）。

断言（都以**数据库真实状态**为准）：
  1. `13500` 建宗门 ⇒ `role_guild` 有行；再建一次 ⇒ `code=0 '已经创建过宗门'`；空名 ⇒ `code=0`
  2. `13803` ⇒ `role_market.on_state` **真的写入**（type=0 ⇒ 0，其余 ⇒ 1）
  3. `18600` ⇒ **有坐骑才 `map_state=1`**（用 `/DSH_ADMIN/ride` 前后对比）
  4. `13020` ⇒ `dungeon_progress` 里出现 `ptype='dung_enter'` 且 `pkey=dung_bid`

用法： python tools/verify_unsupported4b.py
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


def cm(b, off=1):
    n = struct.unpack_from('>H', b, off)[0]
    return b[0], b[off + 2:off + 2 + n].decode('utf-8', 'replace')


def q(sql, args=()):
    c = sqlite3.connect(DB)
    r = c.execute(sql, args).fetchall()
    c.close()
    return r


def ride(jie, lev=1):
    urllib.request.urlopen('http://127.0.0.1:8080/DSH_ADMIN/ride?jie=%d&lev=%d'
                           % (jie, lev), timeout=8).read()


def main():
    ok = True

    # ---- 13500 建宗门（先清掉已有）
    c = sqlite3.connect(DB)
    try:
        c.execute('DELETE FROM role_guild WHERE rid=?', (RID,))
        c.commit()
    except sqlite3.OperationalError:
        pass
    c.close()
    name = 'DSH测试宗门'
    b = ask(13500, struct.pack('>H', len(name.encode())) + name.encode())
    code, msg = cm(b)
    rows = q('SELECT name FROM role_guild WHERE rid=?', (RID,))
    print('\n== 13500 建宗门 ==')
    print('  code=%d msg=%r  role_guild 行=%s' % (code, msg, rows))
    a1 = code == 1 and rows and rows[0][0] == name
    print('  ★ 宗门真的建了 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1
    b = ask(13500, struct.pack('>H', len(name.encode())) + name.encode())
    code, msg = cm(b)
    print('  重复创建 ⇒ code=%d msg=%r' % (code, msg))
    a2 = code == 0 and '已经创建' in msg
    ok = ok and a2
    b = ask(13500, struct.pack('>H', 0))
    code, msg = cm(b)
    print('  空名 ⇒ code=%d msg=%r' % (code, msg))
    a3 = code == 0 and '空' in msg
    ok = ok and a3

    # ---- 13803 摆摊
    b = ask(13803, struct.pack('>H', 1))
    code, msg = cm(b)
    on1 = q('SELECT on_state FROM role_market WHERE rid=?', (RID,))
    b = ask(13803, struct.pack('>H', 0))
    code0, msg0 = cm(b)
    on0 = q('SELECT on_state FROM role_market WHERE rid=?', (RID,))
    print('\n== 13803 摆摊 ==')
    print('  type=1 ⇒ code=%d，表里 on_state=%s' % (code, on1))
    print('  type=0 ⇒ code=%d，表里 on_state=%s' % (code0, on0))
    a4 = code == 1 and on1 and on1[0][0] == 1 and code0 == 1 and on0 and on0[0][0] == 0
    print('  ★ 开关真的落库 ⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    # ---- 18600 坐骑地图态
    ride(0)
    b = ask(18600)
    code, msg = cm(b)
    off = 1
    n = struct.unpack_from('>H', b, off)[0]
    off += 2 + n
    ms0, st0 = b[off], b[off + 1]
    ride(1, 10)
    b = ask(18600)
    code1, msg1 = cm(b)
    off = 1
    n = struct.unpack_from('>H', b, off)[0]
    off += 2 + n
    ms1, st1 = b[off], b[off + 1]
    print('\n== 18600 坐骑地图态 ==')
    print('  没坐骑 ⇒ map_state=%d status=%d' % (ms0, st0))
    print('  有坐骑 ⇒ map_state=%d status=%d' % (ms1, st1))
    a5 = code == 1 and code1 == 1 and ms0 == 0 and ms1 == 1
    print('  ★ 有坐骑才 map_state=1（真实 DB 驱动）⇒ %s' % ('✓' if a5 else '✗'))
    ok = ok and a5

    # ---- 13020 进镇魔塔
    c = sqlite3.connect(DB)
    try:
        c.execute("DELETE FROM dungeon_progress WHERE rid=? AND ptype='dung_enter'", (RID,))
        c.commit()
    except sqlite3.OperationalError:
        pass
    c.close()
    b = ask(13020, struct.pack('>I', 40001) + struct.pack('>H', 1) + bytes([1, 5]))
    tips = struct.unpack_from('>H', b, 0)[0]
    rows = q("SELECT pkey,value FROM dungeon_progress WHERE rid=? AND ptype='dung_enter'", (RID,))
    print('\n== 13020 进镇魔塔 ==')
    print('  tips=%d  dungeon_progress(dung_enter) 行=%s' % (tips, rows))
    a6 = tips == 0 and rows and rows[0][0] == '40001'
    print('  ★ 进入记录真的落库 ⇒ %s' % ('✓' if a6 else '✗'))
    ok = ok and a6

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
