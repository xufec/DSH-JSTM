# -*- coding: utf-8 -*-
"""R114 验收：`21401`（装备格容量）+ `21402`（穿上）+ `21403`（卸下）。

流程（真实往返）：
  1. `21401` ⇒ eqm_grid（来自 `bag_volume` bag_code=2）
  2. 取背包里一件装备的 item_id ⇒ `21402{eqm_pos}` ⇒ code=1
     ⇒ 断言：`bag_items` 少一条、`equip_items` 多一条（**真的搬过去了**）
  3. `21403{eqm_item_id}` ⇒ code=1
     ⇒ 断言：`equip_items` 少一条、`bag_items` 该 bid 数量回来
  4. `21402` 用不存在的 bag_item_id ⇒ code=0（诚实）

用法： python tools/verify_rune_equip.py
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


def code_msg(b):
    n = struct.unpack_from('>H', b, 1)[0]
    return b[0], b[3:3 + n].decode('utf-8', 'replace')


def bag_rows():
    c = sqlite3.connect(DB)
    return [dict(zip(['item_id', 'bid', 'quantity'], r)) for r in
            c.execute('SELECT item_id, bid, quantity FROM bag_items WHERE rid=?', (RID,))]


def eqp_rows():
    c = sqlite3.connect(DB)
    return [dict(zip(['slot', 'item_id', 'bid'], r)) for r in
            c.execute('SELECT slot, item_id, bid FROM equip_items WHERE rid=?', (RID,))]


def main():
    ok = True
    # ★★ 幂等前置：**清空装备表** —— 否则前几次测试留下的装备行会让
    #    "穿上/卸下"的行数判据不成立（本会话第 2 次踩幂等坑）。
    _c = sqlite3.connect(DB)
    _c.execute('DELETE FROM equip_items WHERE rid=?', (RID,))
    _c.commit()
    _c.close()

    # ---- 21401
    b = ask(21401)
    print('\n== SC_21401 ==')
    print('  eqm_grid=%d' % b[0])
    a1 = len(b) == 1
    print('  结构正确 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 21402 穿一件
    bag0, eqp0 = bag_rows(), eqp_rows()
    if not bag0:
        print('\n!! 背包空，无法测 21402')
        print('\n=== 结果: FAIL ===')
        return 1
    target = bag0[0]
    used_slots = {e['slot'] for e in eqp0}
    free_slot = next((s for s in range(1, 20) if s not in used_slots), 1)
    body = (struct.pack('>I', target['item_id']) + struct.pack('>I', 0) +
            bytes([free_slot]) + struct.pack('>I', 0))
    b = ask(21402, body)
    c, m = code_msg(b)
    bag1, eqp1 = bag_rows(), eqp_rows()
    print('\n== CS_21402{bag_item_id=%d, eqm_pos=%d} ==' % (target['item_id'], free_slot))
    print('  code=%d msg=%r  bag %d→%d  equip %d→%d'
          % (c, m, len(bag0), len(bag1), len(eqp0), len(eqp1)))
    a2 = (c == 1 and len(bag1) == len(bag0) - 1 and len(eqp1) == len(eqp0) + 1)
    print('  物品**真的从背包搬到装备** ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 21403 卸下刚穿的那件
    moved = [e for e in eqp1 if e['item_id'] == target['item_id']]
    if not moved:
        print('\n!! 没找到刚穿上的装备，21403 无法测')
        print('\n=== 结果: FAIL ===')
        return 1
    body = struct.pack('>I', target['item_id']) + struct.pack('>I', 0) + bytes([0]) + struct.pack('>I', 0)
    b = ask(21403, body)
    c, m = code_msg(b)
    bag2, eqp2 = bag_rows(), eqp_rows()
    print('\n== CS_21403{eqm_item_id=%d} ==' % target['item_id'])
    print('  code=%d msg=%r  bag %d→%d  equip %d→%d'
          % (c, m, len(bag1), len(bag2), len(eqp1), len(eqp2)))
    back = any(r['bid'] == target['bid'] for r in bag2)
    a3 = (c == 1 and len(eqp2) == len(eqp1) - 1 and back)
    print('  装备**真的卸回背包** ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 21402 无效 id ⇒ code=0
    body = struct.pack('>I', 99999999) + struct.pack('>I', 0) + bytes([free_slot]) + struct.pack('>I', 0)
    b = ask(21402, body)
    c, m = code_msg(b)
    print('\n== CS_21402{bag_item_id=99999999} ==')
    print('  code=%d msg=%r' % (c, m))
    a4 = c == 0 and '找不到' in m
    print('  回 code=0 + 明确 msg ⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
