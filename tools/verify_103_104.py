# -*- coding: utf-8 -*-
"""R160 验收：`103xx` + `104xx`（伙伴）13 条。

判据（**核对真实值**）：
  1. `10305` 的 `assets` 与 `role_assets` **逐项一致**（label 由 `CodeToAssets` 映射）
  2. `10334` 的 `coin` == `role_assets.gold`
  3. `10409` 的 `exp` == `role_heros.exp`；`10413` 的条目 == 18、`state` 与 DB 一致
  4. `10405` 的 `color`/`chip` 与 DB 一致
  5. 全部结构精确

用法： python tools/verify_103_104.py
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
RID = 1001
CMDS = (10305, 10334, 10325, 10332, 10320, 10321, 10327, 10348,
        10405, 10406, 10409, 10411, 10413)


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
    r = c.execute(sql, args).fetchall()
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

    bodies = {
        10305: b'', 10334: b'', 10325: b'', 10332: b'', 10320: b'', 10321: b'',
        10327: struct.pack('>H', 10107), 10348: struct.pack('>H', 10107),
        10405: struct.pack('>I', 30800), 10406: struct.pack('>I', 30800),
        10409: struct.pack('>I', 30800), 10411: struct.pack('>I', 30800),
        10413: b'',
    }
    bad = 0
    for cmd in CMDS:
        b = ask(cmd, bodies[cmd])
        r = g.audit_body(sc[str(cmd)], b, cmd)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (cmd, r['len'], r['consumed'], r['err']))
    print('\n== 13 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10305 资产逐项核对
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_game_data.json'),
                         encoding='utf-8'))
    arr = cfg.get('CodeToAssets') or []
    lbl = {str(v): i for i, v in enumerate(arr) if v}
    db_as = {k: int(v) for k, v in q('SELECT name,amount FROM role_assets WHERE rid=?', (RID,))}
    b = ask(10305)
    n = struct.unpack_from('>H', b, 0)[0]
    got = {}
    o = 2
    for _ in range(n):
        lb = b[o]
        vl = struct.unpack_from('>I', b, o + 1)[0]
        got[lb] = vl
        o += 5
    exp = {lbl[k]: v for k, v in db_as.items() if k in lbl}
    print('  10305 assets=%d 项  回包=%s' % (n, got))
    print('        DB(映射后)=%s' % exp)
    a1 = got == exp and n == len(exp)
    print('  ★ 与 role_assets 逐项一致 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # 10334 金币
    b = ask(10334)
    coin = struct.unpack_from('>I', b, 0)[0]
    dbgold = int((q('SELECT amount FROM role_assets WHERE rid=? AND name=?', (RID, 'gold'))
                  or [(0,)])[0][0])
    print('  10334 coin=%d（DB gold=%d）⇒ %s' % (coin, dbgold, '✓' if coin == dbgold else '✗'))
    ok = ok and coin == dbgold

    # 10409 exp / 10405 color,chip
    row = q('SELECT color,lev,exp,state,chip FROM role_heros WHERE rid=? AND bid=30800', (RID,))
    wcolor, wlev, wexp, wstate, wchip = (int(x) for x in row[0]) if row else (0, 1, 0, 0, 0)
    b = ask(10409, struct.pack('>I', 30800))
    exp2 = struct.unpack_from('>I', b, 4)[0]
    print('  10409 exp=%d（DB exp=%d）⇒ %s' % (exp2, wexp, '✓' if exp2 == wexp else '✗'))
    ok = ok and exp2 == wexp
    b = ask(10405, struct.pack('>I', 30800))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    c2 = b[o + 4]
    chip2 = struct.unpack_from('>H', b, o + 5)[0]
    print('  10405 color=%d chip=%d（DB color=%d chip=%d）⇒ %s'
          % (c2, chip2, wcolor, wchip, '✓' if (c2 == wcolor and chip2 == wchip) else '✗'))
    ok = ok and c2 == wcolor and chip2 == wchip

    # 10413 条目数与 state
    b = ask(10413)
    n = struct.unpack_from('>H', b, 0)[0]
    states = {}
    o = 2
    for _ in range(n):
        hb = struct.unpack_from('>I', b, o)[0]
        states[hb] = b[o + 4]
        o += 5
    dbn = q('SELECT COUNT(*) FROM role_heros WHERE rid=?', (RID,))[0][0]
    dbstates = {int(r[0]): int(r[1]) for r in q('SELECT bid,state FROM role_heros WHERE rid=?', (RID,))}
    print('  10413 hero_states=%d（DB %d）⇒ %s' % (n, dbn, '✓' if n == dbn else '✗'))
    print('        state 一致 ⇒ %s' % ('✓' if states == dbstates else '✗'))
    ok = ok and n == dbn and states == dbstates

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
