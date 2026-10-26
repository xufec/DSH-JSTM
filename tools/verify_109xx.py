# -*- coding: utf-8 -*-
"""R164+R165 验收：`109xx`（看他人详情族）**20 条**。

判据：
  1. 12 条**结构精确**（门禁权威解析器）
  2. `10947` 的 `name`/`lev`/`career`/`sex` 与 `roles` 一致；`vip_lev` 与 DB 一致
  3. `10948`/`10958` 的 `rid` 回显 + 装备列表结构正确
  4. `10998` 的 `cli_ver` = 10409（1.4.9）

用法： python tools/verify_109xx.py
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
CMDS = (10947, 10948, 10958, 10951, 10952, 10995, 10998, 10931, 10933, 10934, 10942, 10953,
        # ★ R165 收尾 8 条
        10900, 10901, 10902, 10910, 10945, 10946, 10949, 10950)


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
    rid_body = struct.pack('>I', RID) + struct.pack('>H', 1) + b'1'
    bodies = {10947: rid_body, 10948: rid_body, 10958: rid_body, 10951: rid_body,
              10952: rid_body, 10953: rid_body, 10995: b'', 10998: b'',
              10931: b'', 10933: b'', 10934: b'', 10942: bytes([1]),
              # ★ R165 收尾 8 条
              10900: rid_body + struct.pack('>I', 1) + struct.pack('>H', 1) + b'x',
              10901: rid_body + struct.pack('>I', 1) + struct.pack('>H', 1) + b'x',
              10902: rid_body + struct.pack('>H', 1) + b'x',
              10910: b'', 10945: struct.pack('>H', 2) + b'AB', 10946: b'',
              10949: rid_body, 10950: rid_body}

    bad = 0
    for c in CMDS:
        b = ask(c, bodies[c])
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 20 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10947 关键字段
    row = q('SELECT name,level,career,sex,vip_level FROM roles WHERE rid=?', (RID,))
    wname, wlev, wcar, wsex, wvip = row[0] if row else ('', 0, 0, 0, 0)
    b = ask(10947, rid_body)
    o = 4
    sl = struct.unpack_from('>H', b, o)[0]
    o += 2 + sl                       # srv_id
    nl = struct.unpack_from('>H', b, o)[0]
    name = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    o += 2 + nl
    lev = struct.unpack_from('>H', b, o)[0]
    car = struct.unpack_from('>H', b, o + 2)[0]
    sex = b[o + 4]
    isvip = b[o + 5]
    vlev = b[o + 6]
    print('\n== 10947 看他人角色详情 ==')
    print('  name=%r lev=%d career=%d sex=%d vip=%d/%d' % (name, lev, car, sex, isvip, vlev))
    print('        DB: name=%r lev=%d career=%d sex=%d vip=%d' % (wname, wlev, wcar, wsex, wvip))
    a1 = (name == wname and lev == int(wlev) and car == int(wcar) and sex == int(wsex)
          and vlev == int(wvip))
    print('  ★ 与 DB 一致 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # 10998 cli_ver
    b = ask(10998)
    ver = struct.unpack_from('>H', b, 0)[0]
    print('  10998 cli_ver=%d ⇒ %s' % (ver, '✓' if ver == 10409 else '✗'))
    ok = ok and ver == 10409

    # 10948 rid 回显
    b = ask(10948, rid_body)
    rid2 = struct.unpack_from('>I', b, 0)[0]
    print('  10948 rid=%d ⇒ %s' % (rid2, '✓' if rid2 == RID else '✗'))
    ok = ok and rid2 == RID

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
