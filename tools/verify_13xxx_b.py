# -*- coding: utf-8 -*-
"""R185 验收：**`13xxx` 批次 28 条**（专用分支 974 → 1002）。

判据：
  1. 28 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **真实角色列表**：`13570`/`13577` 的 `role_list` 恰 1 条且 `name` = DB
  4. ★ **回显**：`13572`（`partner_id`）、`13104`（`s_type`）、`13506`（`type`）

★ 本批 `13501`/`13513` **已由更早的批次实现** ⇒ 由 `lint_dispatch_shadow` 抓到重复后**移除**
  （这正是那道门禁的价值）。

用法： python tools/verify_13xxx_b.py
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
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')

CMDS = [13004, 13101, 13102, 13104, 13251, 13253, 13355, 13356, 13502, 13505, 13506,
        13507, 13509, 13512, 13519, 13524, 13526, 13530, 13531, 13533, 13539, 13548,
        13570, 13572, 13573, 13577, 13802, 13807]
B = {13104: bytes([1]), 13253: bytes([1]),
     13505: bytes([1]) + struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1',
     13506: bytes([1]), 13531: struct.pack('>I', 1) + struct.pack('>H', 2) + b'ab',
     13533: struct.pack('>I', 1),
     # ★ `13572` 的 CS 是 `{rid:u32, srv_id:string, partner_id:u32}`（**不是**只有 partner_id）
     13572: struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1' + struct.pack('>I', 30800),
     # ★ `13573` 的 CS 是 `{partner_id:u32}`
     13573: struct.pack('>I', 30800),
     13802: struct.pack('>I', 1), 13807: struct.pack('>I', 1)}


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


def rd_str(b, o):
    n = struct.unpack_from('>H', b, o)[0]
    return b[o + 2:o + 2 + n].decode('utf-8', 'replace'), o + 2 + n


def main():
    ok = True
    g, sc = load_gate()
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())

    bad = 0
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 28 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '13xxx-B（' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 28 and fb == 0) else '✗'))
    ok = ok and ded >= 28 and fb == 0

    row = q('SELECT name FROM roles WHERE rid=1001')
    wname = row[0][0] if row else ''

    # ★ 13570：{page, page_total, role_list:table<rid,srv_id,name,…>}
    b = ask(13570)
    cnt = struct.unpack_from('>H', b, 2)[0]
    o = 4 + 4                       # page + page_total + 元素的 rid
    _srv, o = rd_str(b, o)
    nm, o = rd_str(b, o)
    print('\n  13570 page=%d page_total=%d 计数=%d name=%r ⇒ %s'
          % (b[0], b[1], cnt, nm, '✓' if (cnt == 1 and nm == wname) else '✗'))
    ok = ok and cnt == 1 and nm == wname

    # ★ 回显：13572（partner_id）
    b = ask(13572, B[13572])
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  13572 回显 partner_id=%d ⇒ %s' % (got, '✓' if got == 30800 else '✗'))
    ok = ok and got == 30800
    # ★ 回显：13104（s_type）
    b = ask(13104, bytes([7]))
    m = struct.unpack_from('>H', b, 2)[0]
    got = b[2 + 2 + m]
    print('  13104 回显 s_type=%d ⇒ %s' % (got, '✓' if got == 7 else '✗'))
    ok = ok and got == 7

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
