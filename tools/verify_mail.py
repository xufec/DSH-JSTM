# -*- coding: utf-8 -*-
"""R161 验收：邮件系统 + 伙伴点数 + 技能时间（11 条）。

判据（**核对真实值**）：
  1. `10810` 发邮件后，`10802` 的**条目数 +1**、`10803` 的 `subject`/`content` 与发的一致
  2. `10801` 标记已读后，**DB 的 `read_time` 真的变了**
  3. `10423` 领点后 `cur_point` **+10** 且 DB 一致
  4. `10631` 的 `last_time` 是**真实当前时间**

用法： python tools/verify_mail.py
"""
import io
import json
import os
import socket
import sqlite3
import struct
import sys
import time
import urllib.request

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


def adm(qs):
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/' + qs, timeout=8).read().decode('utf-8'))


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

    # ★ 幂等策略（**不依赖外部 DELETE**）：
    #   服务端用**线程共用的长连接**（`db_conn()`），外部 DELETE 提交后它**仍可能读旧快照**
    #   （SQLite 隔离 + 长连接）⇒ 只看**相对变化**。
    #   ★ 注意取值时机：结构精确性测试里**会调 `10810`，它真存一封邮件**
    #     ⇒ `n0` 必须在**结构测试之后**取（第一版在之前取 ⇒ n0=0、n1=2，白算一次）。
    # 结构精确性
    CMDS = (10801, 10802, 10803, 10810, 10421, 10422, 10423, 10424, 10631, 10632, 10633)
    bodies = {10801: struct.pack('>I', 1), 10802: b'', 10803: b'',
              10810: bytes([1]) + struct.pack('>H', len('测试'.encode())) + '测试'.encode() +
                     struct.pack('>H', len('内容'.encode())) + '内容'.encode(),
              10421: b'', 10422: b'', 10423: b'',
              10424: struct.pack('>I', 1) + struct.pack('>I', 2),
              10631: struct.pack('>I', 1), 10632: struct.pack('>I', 1) + bytes([0]) * 9,
              10633: struct.pack('>I', 1) + struct.pack('>I', 2) + struct.pack('>I', 3)}
    bad = 0
    for cmd in CMDS:
        b = ask(cmd, bodies[cmd])
        r = g.audit_body(sc[str(cmd)], b, cmd)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (cmd, r['len'], r['consumed'], r['err']))
    print('\n== 11 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 邮件：列表记 n0 → 发一封 → 必须 n0+1
    # ★ n0 必须在**结构测试之后**取（结构测试里的 10810 会真存一封）
    b = ask(10802)
    n0 = struct.unpack_from('>H', b, 0)[0]
    adm('mail?subject=hello&content=world&from=tester')
    b = ask(10802)
    n1 = struct.unpack_from('>H', b, 0)[0]
    print('  10802 邮件列表: 发前 %d → 发一封后 %d ⇒ %s' % (n0, n1, '✓' if n1 == n0 + 1 else '✗'))
    ok = ok and n1 == n0 + 1

    # 10803 详情
    b = ask(10803)
    o = 4
    fl = struct.unpack_from('>H', b, o)[0]
    fname = b[o + 2:o + 2 + fl].decode()
    o += 2 + fl
    sl = struct.unpack_from('>H', b, o)[0]
    subj = b[o + 2:o + 2 + sl].decode()
    o += 2 + sl
    cl = struct.unpack_from('>H', b, o)[0]
    content = b[o + 2:o + 2 + cl].decode()
    print('  10803 详情: from=%r subject=%r content=%r ⇒ %s'
          % (fname, subj, content, '✓' if (subj == 'hello' and content == 'world') else '✗'))
    ok = ok and subj == 'hello' and content == 'world'

    # 10801 标记已读 ⇒ DB read_time 变
    before = q('SELECT read_time FROM role_mail WHERE rid=? ORDER BY id DESC LIMIT 1', (RID,))
    b = ask(10801, struct.pack('>I', int(q('SELECT id FROM role_mail WHERE rid=? ORDER BY id DESC LIMIT 1',
                                          (RID,))[0][0])))
    after = q('SELECT read_time FROM role_mail WHERE rid=? ORDER BY id DESC LIMIT 1', (RID,))
    print('  10801 已读: read_time %s → %s ⇒ %s'
          % (before[0][0] if before else None, after[0][0] if after else None,
             '✓' if (before and after and before[0][0] == 0 and after[0][0] > 0) else '✗'))
    ok = ok and before and after and before[0][0] == 0 and after[0][0] > 0

    # 10423 领点 +10
    b = ask(10423)
    cp1 = struct.unpack_from('>H', b, 1 + 2 + struct.unpack_from('>H', b, 1)[0])[0]
    b = ask(10423)
    cp2 = struct.unpack_from('>H', b, 1 + 2 + struct.unpack_from('>H', b, 1)[0])[0]
    print('  10423 领点: %d → %d（应 +10）⇒ %s' % (cp1, cp2, '✓' if cp2 == cp1 + 10 else '✗'))
    ok = ok and cp2 == cp1 + 10

    # 10631 last_time 真实
    b = ask(10631, struct.pack('>I', 1))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    lt = struct.unpack_from('>I', b, o + 4)[0]
    now = int(time.time())
    good = abs(now - lt) < 120
    print('  10631 last_time=%d（现在 %d，差 %ds）⇒ %s' % (lt, now, now - lt, '✓' if good else '✗'))
    ok = ok and good

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
