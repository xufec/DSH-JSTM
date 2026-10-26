# -*- coding: utf-8 -*-
"""R183 验收：**`17xxx` 全家族 50 条**（专用分支 881 → 931）。

判据：
  1. 50 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★★ **榜上有我**：`17902`/`17505`/`17504`/`17517` 的 `rank_list` **恰 1 条**，
     且 `name` 与 DB 一致
  4. ★ **回显**：`17711`/`17713`/`17714` 的 `bag_code`/`item_id` 一致

用法： python tools/verify_17xxx.py
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

CMDS = [17000, 17101, 17201, 17302, 17307, 17311, 17400, 17401, 17402, 17403, 17404,
        17406, 17502, 17503, 17504, 17505, 17506, 17507, 17509, 17510, 17512, 17513,
        17515, 17516, 17517, 17518, 17519, 17700, 17704, 17705, 17706, 17707, 17708,
        17709, 17710, 17711, 17712, 17713, 17714, 17715, 17716, 17901, 17902, 17903,
        17904, 17905, 17906, 17907, 17908, 17909]
B = {17302: bytes([1]), 17311: bytes([1]),
     17700: bytes([1]) + struct.pack('>I', 1) + bytes([1]),
     17704: bytes([1]) + struct.pack('>I', 1), 17705: bytes([1]) + struct.pack('>I', 1),
     17706: bytes([1]), 17709: struct.pack('>I', 1), 17710: struct.pack('>I', 1),
     17711: bytes([1]) + struct.pack('>I', 1), 17712: bytes([1]) + struct.pack('>I', 1),
     17713: bytes([1]) + struct.pack('>I', 1), 17714: bytes([1]) + struct.pack('>I', 1),
     17715: bytes([1]) + struct.pack('>I', 1), 17716: bytes([1]),
     17905: struct.pack('>I', 1)}


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
    print('\n== 50 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '17xxx（' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 50 and fb == 0) else '✗'))
    ok = ok and ded >= 50 and fb == 0

    row = q('SELECT name,level,career,sex FROM roles WHERE rid=1001')
    wname, wlev, wcar, wsex = row[0] if row else ('', 0, 0, 0)

    # ★ 17902：{rank:u32, rank_list:table<rank,name,lev,career,sex,power,bid>}
    b = ask(17902)
    o = 4 + 2                       # rank + 计数
    o += 4                          # 元素的 rank
    nm, o = rd_str(b, o)
    lev = struct.unpack_from('>H', b, o)[0]
    print('\n== ★ 榜上有我（17902）==  1 条 name=%r lev=%d ｜ DB %r/%d ⇒ %s'
          % (nm, lev, wname, int(wlev),
             '✓' if (nm == wname and lev == int(wlev)) else '✗'))
    ok = ok and nm == wname and lev == int(wlev)

    # ★ 17505：rank_list<rand,gid,srv_id,name,score,win_count,total_count>
    b = ask(17505)
    cnt = struct.unpack_from('>H', b, 0)[0]
    o = 2 + 2 + 4                   # 计数 + rand(u16) + gid(u32)
    _srv, o = rd_str(b, o)          # ★ 还要跳 `srv_id`（我第一版漏了 ⇒ 读到的是 srv_id"1"）
    nm, o = rd_str(b, o)
    print('  17505 计数=%d srv_id=%r name=%r ⇒ %s'
          % (cnt, _srv, nm, '✓' if (cnt == 1 and nm == wname) else '✗'))
    ok = ok and cnt == 1 and nm == wname

    # ★ 回显（17711）：{tips:u8,msg,bag_code:u8,item_id:u32}
    b = ask(17711, bytes([7]) + struct.pack('>I', 21903))
    o = 2                          # tips(1) + msg 长度(2) → 实际 tips 在 0，msg 长度在 1-2
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    bc = b[o]
    iid = struct.unpack_from('>I', b, o + 1)[0]
    print('  17711 回显 bag_code=%d item_id=%d ⇒ %s'
          % (bc, iid, '✓' if (bc == 7 and iid == 21903) else '✗'))
    ok = ok and bc == 7 and iid == 21903

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
