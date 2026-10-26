# -*- coding: utf-8 -*-
"""R154 验收：候选池第三批 3 条（伙伴详情 / 魂兽详情 / 阵法位）。

判据（核对**真实值**）：
  1. `11201` 的 `bid`/`color`/`lev` 与 `role_heros` 第一行一致
  2. `12602` 回真实 `demon_bid` + 该伙伴的 `chip`
  3. `11412` 的 `state` 与 `role_heros` 一致
  4. 全部用门禁权威解析器

用法： python tools/verify_gap_batch3.py
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


def q(sql, args=()):
    c = sqlite3.connect(DB)
    r = c.execute(sql, args).fetchone()
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

    # ---- 11201：与 role_heros 第一行一致（ORDER BY bid，见 db_hero_list）
    row = q('SELECT bid,color,lev,exp,state,chip FROM role_heros WHERE rid=? ORDER BY bid LIMIT 1',
            (RID,))
    wbid, wcolor, wlev = (int(row[0]), int(row[1]), int(row[2])) if row else (0, 0, 1)
    b = ask(11201)
    r = g.audit_body(sc['11201'], b, 11201)
    o = 0
    idv = struct.unpack_from('>I', b, o)[0]; o += 4
    bid = struct.unpack_from('>I', b, o)[0]; o += 4 + 1     # bid + type
    color = b[o]; o += 1
    o += 4                                                   # lifttime
    lev = b[o]
    print('\n== 11201 伙伴详情 ==')
    print('  len=%d 消耗=%d err=%s id=%d bid=%d color=%d lev=%d（DB bid=%d color=%d lev=%d）'
          % (r['len'], r['consumed'], r['err'], idv, bid, color, lev, wbid, wcolor, wlev))
    a1 = (r['consumed'] == r['len'] and not r['err']
          and bid == wbid and color == wcolor and lev == wlev)
    print('  ★ bid/color/lev 与 role_heros 一致 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 12602：chip 与 DB 一致
    b = ask(12602, struct.pack('>I', wbid))
    r = g.audit_body(sc['12602'], b, 12602)
    got_bid = struct.unpack_from('>I', b, 0)[0]
    got_chip = struct.unpack_from('>H', b, 4 + 3)[0]
    wchip = int(row[5]) if row else 0
    print('\n== 12602 魂兽详情 ==')
    print('  len=%d 消耗=%d err=%s bid=%d chip=%d（DB chip=%d）'
          % (r['len'], r['consumed'], r['err'], got_bid, got_chip, wchip))
    a2 = r['consumed'] == r['len'] and not r['err'] and got_bid == wbid and got_chip == wchip
    print('  ★ 回真实 bid + chip ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 11412
    b = ask(11412)
    r = g.audit_body(sc['11412'], b, 11412)
    got_state = b[2]
    wstate = int(row[4]) if row else 0
    print('\n== 11412 阵法位 ==   len=%d 消耗=%d err=%s state=%d（DB state=%d）'
          % (r['len'], r['consumed'], r['err'], got_state, wstate))
    a3 = r['consumed'] == r['len'] and not r['err'] and got_state == wstate
    print('  ★ state 与 role_heros 一致 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
