# -*- coding: utf-8 -*-
"""R155 验收：装备家族 `105xx` 批量 13 条。

判据：
  1. 全部**结构精确**（门禁权威解析器）
  2. `10516` 的 `code` 随"该装备是否存在"如实
  3. `10573`/`10574` 的回显字段与请求一致
  4. `10590` 的 `ItemIdList` 原样回传

用法： python tools/verify_equip_batch.py
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
CMDS = (10516, 10547, 10507, 10555, 10573, 10578, 10574, 10575, 10576,
        10586, 10590, 10572, 10518)


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

    # ★ 幂等前置：保证有一件装备可校验
    c = sqlite3.connect(DB)
    try:
        c.execute('DELETE FROM equip_items WHERE rid=?', (RID,))
        c.execute('INSERT INTO equip_items (rid,item_id,bid,hero_bid,slot,ctime) '
                  'VALUES (?,?,?,?,?,?)', (RID, 90001, 21903, 0, 0, 0))
        c.commit()
    except sqlite3.OperationalError:
        pass
    c.close()

    # 各命令用的请求体（有装备的用 90001；纯 id/bid 用非零值）
    bodies = {
        10516: bytes([1]) + struct.pack('>I', 90001),
        10547: struct.pack('>I', 90001),
        10507: struct.pack('>I', 21903),
        10555: struct.pack('>I', 1),
        10573: struct.pack('>I', 21903),
        10578: struct.pack('>I', 21903),
        10574: struct.pack('>I', 7),
        10575: struct.pack('>I', 7),
        10576: struct.pack('>I', 7),
        10586: struct.pack('>H', 1) + struct.pack('>I', 21903),
        10590: struct.pack('>H', 0),
        10572: struct.pack('>I', 1) + struct.pack('>H', 0) + struct.pack('>H', 1),
        10518: struct.pack('>H', 0),
    }

    bad = 0
    for cmd in CMDS:
        b = ask(cmd, bodies[cmd])
        r = g.audit_body(sc[str(cmd)], b, cmd)
        good = r['consumed'] == r['len'] and not r['err']
        if not good:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (cmd, r['len'], r['consumed'], r['err']))
    print('\n== 13 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10516：有装备 ⇒ code=1；不存在 ⇒ code=0
    c1 = ask(10516, bytes([1]) + struct.pack('>I', 90001))[0]
    c0 = ask(10516, bytes([1]) + struct.pack('>I', 12345678))[0]
    print('  10516 有装备 code=%d ｜ 无装备 code=%d ⇒ %s'
          % (c1, c0, '✓' if (c1 == 1 and c0 == 0) else '✗'))
    ok = ok and c1 == 1 and c0 == 0

    # 10573 / 10574 回显
    b = ask(10573, struct.pack('>I', 21903))
    bid = struct.unpack_from('>I', b, 1)[0]
    print('  10573 回显 bid=%d（请求 21903）⇒ %s' % (bid, '✓' if bid == 21903 else '✗'))
    ok = ok and bid == 21903
    b = ask(10574, struct.pack('>I', 7))
    iid = struct.unpack_from('>I', b, 1)[0]
    print('  10574 回显 id=%d（请求 7）⇒ %s' % (iid, '✓' if iid == 7 else '✗'))
    ok = ok and iid == 7

    # 10590：ItemIdList 原样回传
    # ★ 布局：code:u8(0) + msg:string(1..1+2+n) + ItemIdList:table
    #   ⇒ 计数在 **1 + 2 + len(msg)** 处 —— 别漏了 string 的**长度前缀 2 字节**
    #     （纪律第 9 条；这是本会话第 N 次栽在这一条上）。
    b = ask(10590, struct.pack('>H', 2) + struct.pack('>I', 11) + struct.pack('>I', 22))
    _ml = struct.unpack_from('>H', b, 1)[0]
    _o = 1 + 2 + _ml
    m = struct.unpack_from('>H', b, _o)[0]
    a = struct.unpack_from('>I', b, _o + 2)[0]
    b2 = struct.unpack_from('>I', b, _o + 2 + 4)[0]
    print('  10590 回传列表 %d 项 [%d, %d] ⇒ %s' % (m, a, b2, '✓' if (m == 2 and a == 11 and b2 == 22) else '✗'))
    ok = ok and m == 2 and a == 11 and b2 == 22

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
