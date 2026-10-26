# -*- coding: utf-8 -*-
"""验证 13402（134xx 限购商店购买）：端到端做一次真实购买，三向核对。

核对项：
  1. 应答按 SC_13402 规格精确解析（id/type/buy_num/new_price/code/msg）；
  2. **扣费真实发生**（DB 里对应资产减少 = 单价 × 数量）；
  3. **发货真实发生**（背包里 item_bid 数量 +N）；
  4. **限购计数真实更新**（再次查 13401，buy_num 增加）。

⚠ 会真实扣费/发货 ⇒ 运行前请备份 server/state/roles.db。

用法：python tools/verify_13402.py
"""
import json
import os
import sqlite3
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import socket  # noqa: E402
from audit_sc_live import pack_frame, recv_exact, login  # noqa: E402

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
RID = 1001
MTYPE = 5


def sc_spec(cmd):
    with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
        d = json.load(f)
    for k, v in d.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def q(sql, args=()):
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(sql, args)
        return cur.fetchall()
    finally:
        con.close()


def coin():
    r = q('SELECT amount FROM role_assets WHERE rid=? AND name=?', (RID, 'coin'))
    return int(r[0][0]) if r else 0


def bag_qty(bid):
    r = q('SELECT SUM(quantity) FROM bag_items WHERE rid=? AND bid=?', (RID, bid))
    return int(r[0][0] or 0) if r else 0


def send(s, cmd, body):
    s.sendall(pack_frame(cmd, body))
    while True:
        hdr = recv_exact(s, 6)
        (ln, rcmd) = struct.unpack('>IH', hdr)
        payload = recv_exact(s, ln - 2)
        if rcmd == cmd:
            return payload


def main():
    ok = True
    mall = json.load(open(os.path.join(ROOT, 'server', 'mall_config.json'),
                          encoding='utf-8'))
    goods = [g for g in mall if int(g.get('type', -1)) == MTYPE]
    assert goods, 'type=%d 无商品' % MTYPE
    g = goods[0]
    gid, item_bid, price = int(g['id']), int(g['item_bid']), int(g['price'])

    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    login(s)
    s.settimeout(5)

    c0, b0 = coin(), bag_qty(item_bid)
    print('购买前: coin=%d  item_bid=%d x%d' % (c0, item_bid, b0))

    # 先查 13401 拿 buy_num（应来自服务端自己的 id 空间）
    p = send(s, 13401, bytes([MTYPE]))
    t = p[0]
    n = struct.unpack_from('>H', p, 1)[0]
    ids = [struct.unpack_from('>HH', p, 3 + 4 * i) for i in range(n)]
    print('13401: type=%d 条目 %d 个，首个 id=%d buy_num=%d' % (t, n, ids[0][0], ids[0][1]))
    if ids[0][0] != gid:
        print('   !! 13401 首个 id 与 mall_config 不一致（%d vs %d）' % (ids[0][0], gid))
        ok = False

    # 购买
    num = 1
    p = send(s, 13402, struct.pack('>HH', gid, num) + b'\x04\x00\x01\x00')
    (r_id, r_type) = struct.unpack_from('>HB', p, 0)
    r_buy = struct.unpack_from('>H', p, 3)[0]
    r_price = struct.unpack_from('>I', p, 5)[0]
    r_code = p[9]
    mlen = struct.unpack_from('>H', p, 10)[0]
    r_msg = p[12:12 + mlen].decode('utf-8', 'replace')
    print('13402: id=%d type=%d buy_num=%d new_price=%d code=%d msg=%r'
          % (r_id, r_type, r_buy, r_price, r_code, r_msg))
    if r_id != gid or r_code != 1:
        print('   !! 应答异常')
        ok = False
    if r_price != price:
        print('   !! new_price 与配置单价不符（%d vs %d）' % (r_price, price))
        ok = False

    c1, b1 = coin(), bag_qty(item_bid)
    print('购买后: coin=%d (差 %d)  item_bid=%d x%d (差 %d)'
          % (c1, c1 - c0, item_bid, b1, b1 - b0))

    if c0 - c1 != price * num:
        print('   !! 扣费不等于 单价×数量 (%d != %d)' % (c0 - c1, price * num))
        ok = False
    else:
        print('   ✓ 扣费正确 = %d' % (price * num))
    if b1 - b0 != num:
        print('   !! 发货数量不符')
        ok = False
    else:
        print('   ✓ 发货正确 = %d' % num)

    # 再查 13401：buy_num 应 +1
    p = send(s, 13401, bytes([MTYPE]))
    n2 = struct.unpack_from('>H', p, 1)[0]
    d2 = {struct.unpack_from('>HH', p, 3 + 4 * i)[0]:
          struct.unpack_from('>HH', p, 3 + 4 * i)[1] for i in range(n2)}
    print('再查 13401: gid=%d buy_num=%d' % (gid, d2.get(gid, -1)))
    if d2.get(gid, -1) != ids[0][1] + num:
        print('   !! 限购计数未更新')
        ok = False
    else:
        print('   ✓ 限购计数已更新')

    s.close()
    print()
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
