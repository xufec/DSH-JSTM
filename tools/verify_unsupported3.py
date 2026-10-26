# -*- coding: utf-8 -*-
"""R122 验收：`30201`（宗门秘境）/ `13359`（发朋友圈）/ `12762`（频道发言）。

断言（全部读 DB 前后对比）：
  1. `30201` **没宗门 ⇒ code=0**；建宗门后 ⇒ **code=1**（真实状态驱动）
  2. `13359` 发帖 ⇒ `role_moments` **多一行且内容一致**；空内容 ⇒ `code=0`
  3. `12762` 发言 ⇒ `role_chat` **多一行**（`channel`/`msg` 一致）；空内容 ⇒ `code=0`

用法： python tools/verify_unsupported3.py
"""
import io
import os
import socket
import sqlite3
import struct
import sys

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


def ex(sql, args=(), fetch=True):
    c = sqlite3.connect(DB)
    try:
        r = c.execute(sql, args).fetchall()
        c.commit()
        return r if fetch else None
    except sqlite3.OperationalError:
        return []
    finally:
        c.close()


def main():
    ok = True

    # ---- 30201 宗门秘境（先清宗门）
    ex('DELETE FROM role_guild WHERE rid=?', (RID,), fetch=False)
    b = ask(30201)
    c0, m0 = cm(b)
    ex('INSERT OR REPLACE INTO role_guild VALUES (?,?,?)', (RID, 'DSH测试宗门', 0), fetch=False)
    b = ask(30201)
    c1, m1 = cm(b)
    print('\n== 30201 宗门秘境 ==')
    print('  没宗门 ⇒ code=%d msg=%r' % (c0, m0))
    print('  有宗门 ⇒ code=%d msg=%r' % (c1, m1))
    a1 = c0 == 0 and c1 == 1
    print('  ★ 真实状态驱动（0→1）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 13359 发朋友圈
    ex('DELETE FROM role_moments WHERE rid=?', (RID,), fetch=False)
    txt = 'R122朋友圈测试'
    b = ask(13359, struct.pack('>H', len(txt.encode())) + txt.encode())
    c, m = cm(b)
    rows = ex('SELECT content FROM role_moments WHERE rid=?', (RID,))
    print('\n== 13359 发朋友圈 ==')
    print('  code=%d msg=%r  role_moments 行=%s' % (c, m, rows))
    a2 = c == 1 and rows and rows[0][0] == txt
    print('  ★ 内容真的存下来了 ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2
    b = ask(13359, struct.pack('>H', 0))
    c, m = cm(b)
    a3 = c == 0 and '空' in m
    print('  空内容 ⇒ code=%d msg=%r ⇒ %s' % (c, m, '✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 12762 频道发言
    ex('DELETE FROM role_chat WHERE rid=?', (RID,), fetch=False)
    msg = 'R122发言测试'
    b = ask(12762, struct.pack('>H', 3) + bytes([len(msg.encode())]) + msg.encode())
    c, m = cm(b)
    rows = ex('SELECT channel, msg FROM role_chat WHERE rid=?', (RID,))
    print('\n== 12762 频道发言 ==')
    print('  code=%d msg=%r  role_chat 行=%s' % (c, m, rows))
    a4 = c == 1 and rows and rows[0][0] == 3 and rows[0][1] == msg
    print('  ★ 消息真的存下来了（channel/msg 一致）⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4
    b = ask(12762, struct.pack('>H', 3) + bytes([0]))
    c, m = cm(b)
    a5 = c == 0 and '空' in m
    print('  空内容 ⇒ code=%d msg=%r ⇒ %s' % (c, m, '✓' if a5 else '✗'))
    ok = ok and a5

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
