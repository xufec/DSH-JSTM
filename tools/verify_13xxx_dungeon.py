# -*- coding: utf-8 -*-
"""R170 验收：`13xxx` 副本/排行族 **20 条**。

判据：
  1. 20 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` 新增行 —— 纪律第 22 条）
  3. ★ `13080` 的 `list` == `config_dungeon_new.Dungeon` 的项数（**34**）
  4. ★ `13028` 的 `dung_list` 同样是 34 个真实 bid
  5. `13085` 的 `rank_list` 用**真实角色**（name/lev/sex/career）

用法： python tools/verify_13xxx_dungeon.py
"""
import io
import json
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
RID = 1001
CMDS = (13010, 13011, 13015, 13017, 13018, 13022, 13028, 13037, 13055, 13066,
        13073, 13079, 13080, 13084, 13085, 13087, 13088, 13096, 13097, 13098)


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
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())
    B = {13037: struct.pack('>I', 1) + bytes([1]), 13098: struct.pack('>I', 1) + bytes([1]),
         13066: struct.pack('>I', 80001) + struct.pack('>I', 1) + struct.pack('>I', 1),
         13079: struct.pack('>I', 20001), 13097: struct.pack('>I', 20001),
         13085: bytes([1]) + struct.pack('>H', 1) + struct.pack('>H', 5),
         13018: bytes([1, 0]), 13055: struct.pack('>I', 1)}

    bad = 0
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 20 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # ★ 走专用分支？（纪律第 22 条）
    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '13xxx 副本/排行' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 20 and fb == 0) else '✗'))
    ok = ok and ded >= 20 and fb == 0

    # ★ 13080 / 13028 与 config_dungeon_new 一致
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_dungeon_new.json'),
                         encoding='utf-8'))['Dungeon']
    want = sorted(int(k) for k in cfg)
    b = ask(13080)
    n = struct.unpack_from('>H', b, 0)[0]
    bids = []
    o = 2
    for _ in range(n):
        bids.append(struct.unpack_from('>I', b, o)[0])
        o += 13
    print('\n== 13080 副本列表 ==  %d 条（配置 %d）' % (n, len(cfg)))
    a1 = n == len(cfg) and bids == want
    print('  ★ 与 config_dungeon_new **逐项一致** ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    b = ask(13028)
    c2 = b[0]
    n2 = struct.unpack_from('>H', b, 1)[0]
    ids2 = [struct.unpack_from('>I', b, 3 + 4 * i)[0] for i in range(n2)]
    print('  13028 count=%d dung_list=%d ⇒ %s' % (c2, n2, '✓' if (n2 == len(cfg) and ids2 == want) else '✗'))
    ok = ok and n2 == len(cfg) and ids2 == want

    # ★ 13085 真实角色
    row = q('SELECT name,level,sex,career FROM roles WHERE rid=?', (RID,))
    wname, wlev, wsex, wcar = row[0] if row else ('', 0, 0, 0)
    b = ask(13085, bytes([1]) + struct.pack('>H', 1) + struct.pack('>H', 5))
    # 布局：type:u8(0) + rank_list 计数:u16(1) + [rank:u16(3) + rid:**u32**(5) + srv_id + name + …]
    n = struct.unpack_from('>H', b, 1)[0]
    o = 3 + 2 + 4                               # 跳过 rank_list 计数 + rank(u16) + rid(u32)
    sl = struct.unpack_from('>H', b, o)[0]
    o += 2 + sl                                 # srv_id
    nl = struct.unpack_from('>H', b, o)[0]
    name = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    o += 2 + nl
    lev = b[o]
    sex = b[o + 1]
    car = b[o + 2]
    print('  13085 rank_list=%d name=%r lev=%d sex=%d career=%d（DB %r/%d/%d/%d）⇒ %s'
          % (n, name, lev, sex, car, wname, int(wlev), int(wsex), int(wcar),
             '✓' if (n == 1 and name == wname and lev == int(wlev) and sex == int(wsex)
                     and car == int(wcar)) else '✗'))
    ok = ok and n == 1 and name == wname and lev == int(wlev) and sex == int(wsex) and car == int(wcar)

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
