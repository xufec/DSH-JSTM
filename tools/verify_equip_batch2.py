# -*- coding: utf-8 -*-
"""R156 验收：装备家族第二批 12 条。

判据：
  1. 全部**结构精确**（门禁权威解析器）
  2. `10519`/`10520`/`10513` 的 `code` 随"装备是否存在"如实
  3. `10553`（移动）四个参数**原样回**；`10591`/`10593` 回显
  4. `10558` 的 `suit_lev` 与真实装备件数一致

用法： python tools/verify_equip_batch2.py
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
DB = os.path.join(os.path.dirname(HERE), 'server', 'state', 'roles.db')
RID = 1001
CMDS = (10519, 10520, 10513, 10521, 10530, 10545, 10546, 10558, 10544, 10591, 10593, 10553)


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

    # ★ 幂等前置：保证有一件真实装备
    c = sqlite3.connect(DB)
    try:
        c.execute('DELETE FROM equip_items WHERE rid=?', (RID,))
        c.execute('INSERT INTO equip_items (rid,item_id,bid,hero_bid,slot,ctime) '
                  'VALUES (?,?,?,?,?,?)', (RID, 90001, 21903, 0, 0, 0))
        c.commit()
    except sqlite3.OperationalError:
        pass
    c.close()

    bodies = {
        10519: bytes([1]) + struct.pack('>I', 90001) + bytes([0]),
        10520: bytes([1]) + struct.pack('>I', 90001) + struct.pack('>H', 1) + bytes([0]),
        10513: bytes([1]) + struct.pack('>I', 90001) + bytes([0]),
        10521: bytes([1]) + struct.pack('>I', 90001) + struct.pack('>I', 1),
        10530: bytes([1]) + struct.pack('>I', 90001) + bytes([0]) + bytes([0]),
        10545: struct.pack('>I', 90001) + struct.pack('>I', 90002),
        10546: struct.pack('>I', 90001) + bytes([0]),
        10558: b'',
        10544: b'',
        10591: struct.pack('>I', 21903) + bytes([5]),
        10593: struct.pack('>I', 42),
        10553: bytes([1]) + struct.pack('>I', 90001) + bytes([2]) + struct.pack('>I', 90002),
    }

    bad = 0
    for cmd in CMDS:
        b = ask(cmd, bodies[cmd])
        r = g.audit_body(sc[str(cmd)], b, cmd)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (cmd, r['len'], r['consumed'], r['err']))
    print('\n== 12 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10519 code 如实
    c1 = ask(10519, bytes([1]) + struct.pack('>I', 90001) + bytes([0]))[0]
    c0 = ask(10519, bytes([1]) + struct.pack('>I', 12345678) + bytes([0]))[0]
    print('  10519 有装备 code=%d ｜ 无装备 code=%d ⇒ %s' % (c1, c0, '✓' if (c1 == 1 and c0 == 0) else '✗'))
    ok = ok and c1 == 1 and c0 == 0

    # 10553 四个参数原样回
    b = ask(10553, bytes([1]) + struct.pack('>I', 90001) + bytes([2]) + struct.pack('>I', 90002))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    fc = b[o]
    fi = struct.unpack_from('>I', b, o + 1)[0]
    tc = b[o + 5]
    ti = struct.unpack_from('>I', b, o + 6)[0]
    print('  10553 回显 from=(%d,%d) to=(%d,%d) ⇒ %s'
          % (fc, fi, tc, ti, '✓' if (fc == 1 and fi == 90001 and tc == 2 and ti == 90002) else '✗'))
    ok = ok and fc == 1 and fi == 90001 and tc == 2 and ti == 90002

    # 10591 回显 item_bid/use_num
    b = ask(10591, struct.pack('>I', 21903) + bytes([5]))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    ib = struct.unpack_from('>I', b, o)[0]
    un = b[o + 4]                # ★ use_num 是 uint8（不是 u16）
    print('  10591 回显 item_bid=%d use_num=%d ⇒ %s' % (ib, un, '✓' if (ib == 21903 and un == 5) else '✗'))
    ok = ok and ib == 21903 and un == 5

    # 10558 suit_lev 与真实件数一致
    c = sqlite3.connect(DB)
    n = c.execute('SELECT COUNT(*) FROM equip_items WHERE rid=?', (RID,)).fetchone()[0]
    c.close()
    b = ask(10558)
    sl = struct.unpack_from('>H', b, 0)[0]     # ★ suit_lev 是 uint16
    print('  10558 suit_lev=%d（真实件数 %d）⇒ %s' % (sl, n, '✓' if sl == n else '✗'))
    ok = ok and sl == n

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
