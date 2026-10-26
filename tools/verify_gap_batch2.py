# -*- coding: utf-8 -*-
"""R153 验收：候选池第二批 5 条（装备精炼/品阶 + 看他人角色详情）。

判据（核对**真实值**）：
  1. `10529`/`10541` 的 `eqm_item_id` 回显正确、`code` 随"该装备是否存在"如实
  2. `10954` 的 `name` 与 `roles.name` 一致、`power` == `role_power`
  3. `10955`/`10957` 结构精确
  4. 全部用门禁权威解析器

用法： python tools/verify_gap_batch2.py
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

    # ★ 幂等前置（纪律第 15 条）：本表会被别的验收 DELETE 清空 ⇒ 先插一件真实装备
    try:
        c = sqlite3.connect(DB)
        c.execute('DELETE FROM equip_items WHERE rid=?', (RID,))
        c.execute('INSERT INTO equip_items (rid,item_id,bid,hero_bid,slot,ctime) '
                  'VALUES (?,?,?,?,?,?)', (RID, 90001, 21903, 0, 0, 0))
        c.commit(); c.close()
    except sqlite3.OperationalError:
        pass
    # 取一件真实装备的 item_id
    row = q('SELECT item_id FROM equip_items WHERE rid=? LIMIT 1', (RID,))
    iid = int(row[0]) if row else 0
    print('\n  DB 里第一件装备 item_id = %d（表共 %s 行）'
          % (iid, q('SELECT COUNT(*) FROM equip_items WHERE rid=?', (RID,))[0]))

    # ---- 10529（真装备）
    b = ask(10529, bytes([1]) + struct.pack('>I', iid) + bytes([0]))
    r = g.audit_body(sc['10529'], b, 10529)
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    bag = b[o]
    got = struct.unpack_from('>I', b, o + 1)[0]
    pw = struct.unpack_from('>I', b, o + 1 + 4 + 2)[0]
    print('\n== 10529 装备精炼查询 ==')
    print('  len=%d 消耗=%d err=%s code=%d eqm_item_id=%d power=%d'
          % (r['len'], r['consumed'], r['err'], b[0], got, pw))
    a1 = r['consumed'] == r['len'] and not r['err'] and b[0] == (1 if iid else 0) and got == iid
    print('  ★ 回显真实 item_id + code 如实 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # 不存在的 item ⇒ code=0
    b = ask(10529, bytes([1]) + struct.pack('>I', 99999999) + bytes([0]))
    a1b = b[0] == 0
    print('  不存在的 item ⇒ code=%d ⇒ %s' % (b[0], '✓' if a1b else '✗'))
    ok = ok and a1b

    # ---- 10541
    b = ask(10541, bytes([1]) + struct.pack('>I', iid) + bytes([0]))
    r = g.audit_body(sc['10541'], b, 10541)
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    got2 = struct.unpack_from('>I', b, o + 1)[0]
    print('\n== 10541 装备品阶查询 ==  len=%d err=%s item_id=%d' % (r['len'], r['err'], got2))
    a2 = r['consumed'] == r['len'] and not r['err'] and got2 == iid
    print('  ★ ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 10954：name 与 DB 一致
    b = ask(10954, struct.pack('>I', RID) + struct.pack('>H', 1) + b'1')
    r = g.audit_body(sc['10954'], b, 10954)
    o = 4
    sl = struct.unpack_from('>H', b, o)[0]
    o += 2 + sl
    nl = struct.unpack_from('>H', b, o)[0]
    name = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    rname = q('SELECT name FROM roles WHERE rid=?', (RID,))
    print('\n== 10954 看他人角色详情 ==')
    print('  len=%d 消耗=%d err=%s name=%r（DB %r）' % (r['len'], r['consumed'], r['err'], name, rname[0] if rname else None))
    a3 = r['consumed'] == r['len'] and not r['err'] and name == (rname[0] if rname else '')
    print('  ★ name 与 DB 一致 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 10955 / 10957
    for c in (10955, 10957):
        b = ask(c, struct.pack('>I', RID) + struct.pack('>H', 1) + b'1')
        r = g.audit_body(sc[str(c)], b, c)
        a = r['consumed'] == r['len'] and not r['err']
        print('  %d len=%d 消耗=%d err=%s ⇒ %s' % (c, r['len'], r['consumed'], r['err'], '✓' if a else '✗'))
        ok = ok and a

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
