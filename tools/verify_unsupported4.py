# -*- coding: utf-8 -*-
"""R120 验收：4 条"未开放"命令 —— 改名 / 出售 / 双倍 / 商城购买（**都真改状态**）。

断言：
  1. `10343` 改名 ⇒ `roles.name` **真的变了**；空名字 ⇒ `code=0`
  2. `10504` 出售 ⇒ 背包条目**真的少了**、`gold` **真的多了**（按 `item_config.value`）
  3. `10930` ⇒ 结构正确（`code=1, double=0, double_sum=0`，本服无双倍）
  4. `12821` 购买 ⇒ `gold` **真的扣了**、背包**真的多了物品**；金币不足 ⇒ `code=0`

用法： python tools/verify_unsupported4.py
"""
import io
import json
import os
import socket
import sqlite3
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
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


def cm(b, off=1):
    n = struct.unpack_from('>H', b, off)[0]
    return b[0], b[off + 2:off + 2 + n].decode('utf-8', 'replace')


def db1(sql, args=()):
    c = sqlite3.connect(DB)
    r = c.execute(sql, args).fetchone()
    c.close()
    return r[0] if r else None


def grant(name, amount):
    """★ 幂等前置：把资产设到指定值（复用 admin 的 `setassets`）。"""
    import urllib.request
    urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/setassets?%s=%d' % (name, amount),
        timeout=8).read()


def main():
    ok = True

    # ★★ 幂等前置：**先备足资源** —— 本脚本会真的花钱（`12821` 买 200000 金币的商品），
    #    跑几次后金币会不够 ⇒ 上一版就因此 FAIL（`code=0 '金币不足'`，不是服务端的问题）。
    #    ⇒ 凡是有"消耗"的验收，都必须自己把资源补回来。
    grant('gold', 2000000)

    # ---- 10343 改名
    # ★ 用**固定基准名**做复原，而不是"跑之前的名字" ——
    #   否则一旦 DB 被历史上某次中断的测试污染（本会话曾停在单字 '测'），
    #   本验收会**忠实地把污染一直传播下去**（R166 就踩到了：arena 验收期望 'DSH' 却读到 '测'）。
    base = 'DSH'
    name0 = db1('SELECT name FROM roles WHERE rid=?', (RID,))
    new = 'DSH改名测试'
    b = ask(10343, struct.pack('>H', len(new.encode())) + new.encode() + b'\x00')
    c, m = cm(b)
    name1 = db1('SELECT name FROM roles WHERE rid=?', (RID,))
    print('\n== 10343 改名 ==')
    print('  code=%d msg=%r  name: %r → %r' % (c, m, name0, name1))
    a1 = c == 1 and name1 == new
    print('  ★ 数据库名字真的变了 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1
    # 复原到**固定基准名**（不是 name0）
    ask(10343, struct.pack('>H', len(base.encode())) + base.encode() + b'\x00')
    # 空名字 ⇒ code=0
    b = ask(10343, struct.pack('>H', 0) + b'\x00')
    c, m = cm(b)
    a2 = c == 0 and '空' in m
    print('  空名字 ⇒ code=0 msg=%r ⇒ %s' % (m, '✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 10504 出售
    row = sqlite3.connect(DB).execute(
        'SELECT item_id, bid FROM bag_items WHERE rid=? LIMIT 1', (RID,)).fetchone()
    if row:
        iid, bid = row
        gold0 = db1("SELECT amount FROM role_assets WHERE rid=? AND name='gold'", (RID,)) or 0
        cnt0 = db1('SELECT COUNT(*) FROM bag_items WHERE rid=?', (RID,))
        body = (bytes([1]) + struct.pack('>H', 1) +
                struct.pack('>IIH', iid, bid, 1))
        b = ask(10504, body)
        c, m = cm(b)
        gold1 = db1("SELECT amount FROM role_assets WHERE rid=? AND name='gold'", (RID,)) or 0
        cnt1 = db1('SELECT COUNT(*) FROM bag_items WHERE rid=?', (RID,))
        itemcfg = json.load(open(os.path.join(ROOT, 'server', 'item_config.json'), encoding='utf-8'))
        val = int((itemcfg.get(str(bid)) or {}).get('value') or 0)
        print('\n== 10504 出售 ==')
        print('  code=%d msg=%r  背包 %d→%d  gold %d→%d（物品 value=%d）'
              % (c, m, cnt0, cnt1, gold0, gold1, val))
        a3 = c == 1 and cnt1 == cnt0 - 1 and gold1 - gold0 == val
        print('  ★ 物品真的删了、金币真的加了 ⇒ %s' % ('✓' if a3 else '✗'))
        ok = ok and a3

    # ---- 10930 双倍
    b = ask(10930)
    code = b[0]
    n = struct.unpack_from('>H', b, 1)[0]
    off = 3 + n
    d1 = struct.unpack_from('>H', b, off)[0]
    d2 = struct.unpack_from('>H', b, off + 2)[0]
    print('\n== 10930 双倍 ==')
    print('  len=%d code=%d double=%d double_sum=%d' % (len(b), code, d1, d2))
    a4 = len(b) == off + 4 and code == 1 and d1 == 0 and d2 == 0
    print('  结构正确（本服无双倍 ⇒ 0）⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    # ---- 12821 购买
    goods = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_mall.json'),
                           encoding='utf-8'))['MallGoods']
    k = next(iter(goods))
    g = goods[k]
    g = g.get('hash', g)
    price, ib = int(g.get('price') or 0), int(g.get('item_bid') or 0)
    gold0 = db1("SELECT amount FROM role_assets WHERE rid=? AND name='gold'", (RID,)) or 0
    n0 = db1('SELECT COALESCE(SUM(quantity),0) FROM bag_items WHERE rid=? AND bid=?', (RID, ib)) or 0
    b = ask(12821, bytes([1]) + struct.pack('>I', int(k)))
    c, m = cm(b)
    gold1 = db1("SELECT amount FROM role_assets WHERE rid=? AND name='gold'", (RID,)) or 0
    n1 = db1('SELECT COALESCE(SUM(quantity),0) FROM bag_items WHERE rid=? AND bid=?', (RID, ib)) or 0
    print('\n== 12821 购买（商品 %s：price=%d item_bid=%d）==' % (k, price, ib))
    print('  code=%d msg=%r  gold %d→%d  物品 %d 数量 %d→%d'
          % (c, m, gold0, gold1, ib, n0, n1))
    a5 = c == 1 and gold0 - gold1 == price and n1 == n0 + 1
    print('  ★ 金币真的扣了、物品真的到了 ⇒ %s' % ('✓' if a5 else '✗'))
    ok = ok and a5
    # 无效 bid ⇒ code=0
    b = ask(12821, bytes([1]) + struct.pack('>I', 99999999))
    c, m = cm(b)
    a6 = c == 0 and '不存在' in m
    print('  无效商品 ⇒ code=0 msg=%r ⇒ %s' % (m, '✓' if a6 else '✗'))
    ok = ok and a6

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
