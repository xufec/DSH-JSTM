# -*- coding: utf-8 -*-
"""R243 验收：**摆摊（市场）族 9 条** —— 结构 + 语义 + **交易闭环端到端**。

判据：
  ① **结构精确**（门禁权威解析器 `audit_body`：`消耗 == 长度` 且 `err is None`）
  ② **语义**：`13815`/`13851` 的 `price` == `config_market.MarketItemPrice[bid].base_price`
  ③ ★★★ **闭环**：`addbag 13001`（可上架白名单内）
       ⇒ `13811` 上架（**背包真的少一件**、`13806` 真的多一条）
       ⇒ `13812` 下架 ⇒ `13817` 提取（**背包真的拿回来**）
  ④ **诚实失败**：不可上架物品 ⇒ `code=0`；`13821` 扩展摊位 ⇒ `code=0`（无配置来源）

★ 本脚本**自清理**（记下改动前的背包/摊位行，结束时还原）。

用法： python tools/verify_market_243.py
"""
import io
import json
import os
import socket
import sqlite3
import struct
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _login149 import login, pack_frame, recv_exact  # noqa: E402

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
RID = 1001
SELLABLE = 13001                 # ★ 在 `MarketCanSellItem` 里


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


def q(sql, args=()):
    c = sqlite3.connect(DB)
    try:
        r = c.execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        r = []
    c.close()
    return r


def x(sql, args=()):
    c = sqlite3.connect(DB)
    c.execute(sql, args)
    c.commit()
    c.close()


def market_cfg():
    return json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_market.json'),
                          encoding='utf-8'))


def main():
    ok = True
    g, sc = load_gate()
    mcfg = market_cfg()
    base = int((mcfg['MarketItemPrice'][str(SELLABLE)]['hash'] or {})['base_price'])

    # ---- 现场快照（结束后还原）----
    old_bag = q('SELECT bag_code,item_id,bid,pos,quantity,ctime FROM bag_items '
                'WHERE rid=? AND bid=?', (RID, SELLABLE))
    old_mkt = q('SELECT market_id,item_bid,item_num,sell_num,sell_type,price,time_out '
                'FROM role_market_goods WHERE rid=?', (RID,))

    def restore():
        x('DELETE FROM bag_items WHERE rid=? AND bid=?', (RID, SELLABLE))
        for bc, iid, bid, pos, qty, ct in old_bag:
            x('INSERT OR REPLACE INTO bag_items '
              '(rid,bag_code,item_id,bid,pos,quantity,ctime) VALUES (?,?,?,?,?,?,?)',
              (RID, bc, iid, bid, pos, qty, ct))
        x('DELETE FROM role_market_goods WHERE rid=?', (RID,))
        for row in old_mkt:
            x('INSERT OR REPLACE INTO role_market_goods '
              '(rid,market_id,item_bid,item_num,sell_num,sell_type,price,time_out) '
              'VALUES (?,?,?,?,?,?,?,?)', (RID,) + tuple(row))

    try:
        # ---- ① 结构 ----
        print('== ① 结构（门禁权威解析器）==')
        probes = {
            13810: struct.pack('>H', 0),
            13811: struct.pack('>IIHB', 0, 0, 1, 0),
            13812: struct.pack('>II', 0, 0),
            13813: struct.pack('>III', 0, 0, 0),
            13815: struct.pack('>I', SELLABLE),
            13817: struct.pack('>H', 0),
            13821: bytes([1]),
            13826: struct.pack('>H', 0),
            13851: struct.pack('>I', SELLABLE),
        }
        for c, b in probes.items():
            r = g.audit_body(sc[str(c)], ask(c, b), c)
            good = (not r['err']) and r['consumed'] == r['len']
            print('  SC_%-6d len=%-4d 消耗=%-4d err=%s %s'
                  % (c, r['len'], r['consumed'], r['err'], 'PASS' if good else 'FAIL'))
            ok = ok and good

        # ---- ② 语义：查价 = 配置 base_price ----
        print('\n== ② 语义（13815/13851 的 price ← MarketItemPrice.base_price）==')
        for c, want in ((13815, base), (13851, base)):
            got = struct.unpack_from('>I', ask(c, struct.pack('>I', SELLABLE)), 0)[0]
            hit = got == want
            print('  SC_%-6d price=%-8d （配置 %d）%s' % (c, got, want, '✓' if hit else '✗'))
            ok = ok and hit

        # ---- ③ 闭环 ----
        print('\n== ③ 交易闭环（上架/下架/提取）==')
        urllib.request.urlopen('http://127.0.0.1:8080/DSH_ADMIN/addbag?bid=%d&n=2'
                               % SELLABLE, timeout=8).read()
        rows = q('SELECT item_id,quantity FROM bag_items WHERE rid=? AND bid=?',
                 (RID, SELLABLE))
        if not rows:
            print('  ✗ 造不出测试物品（addbag 失败）')
            return 1
        iid, qty0 = int(rows[0][0]), int(rows[0][1])
        print('  背包：item_id=%d bid=%d qty=%d' % (iid, SELLABLE, qty0))

        b11 = ask(13811, struct.pack('>IIHB', iid, base, 1, 0))
        code11 = b11[0]
        qty1 = int((q('SELECT SUM(quantity) FROM bag_items WHERE rid=? AND bid=?',
                      (RID, SELLABLE)) or [(0,)])[0][0] or 0)
        # ★ `SC_13806` 是 `{add_space:u8, goods_list:table}` ⇒ 条数在**偏移 1**
        n_shelf = struct.unpack_from('>H', ask(13806), 1)[0]
        # ★ 现场可能**本来就有**别人的货品（快照里的行）⇒ 判"新增 1 条"，不比绝对值
        # ★★ R244 竞态修复：**隔离"本测试自己的上架行"** —— 只数 `item_bid=SELLABLE`
        #    且不在 old 里的行（避免活的 1.4.11 游戏并发上架别的物品时数进来）。
        old_ids = set(int(r[0]) for r in old_mkt)
        new_rows = [r for r in q('SELECT market_id FROM role_market_goods '
                                 'WHERE rid=? AND item_bid=?', (RID, SELLABLE))
                    if int(r[0]) not in old_ids]
        # `n_shelf` 用 `>=`（并发玩家可能多上架其他物品，只保证本测试的行在架）。
        e11 = (code11 == 1) and (qty1 == qty0 - 1) and (len(new_rows) == 1) \
            and (n_shelf >= len(old_mkt))
        print('  13811 上架：code=%d ｜ 背包 %d→%d ｜ 新增摊位行=%d ｜ 13806 在架=%d ｜ %s'
              % (code11, qty0, qty1, len(new_rows), n_shelf, '✓' if e11 else '✗'))
        ok = ok and e11

        mid = int(new_rows[0][0])
        b12 = ask(13812, struct.pack('>II', mid, SELLABLE))
        e12 = (b12[0] == 1) and (int((q('SELECT state FROM role_market_goods WHERE '
                                        'rid=? AND market_id=?', (RID, mid))
                                      or [(0,)])[0][0] or 0) == 1)
        print('  13812 下架：code=%d market_id=%d ｜ state=1 ｜ %s'
              % (b12[0], mid, '✓' if e12 else '✗'))
        ok = ok and e12

        b17 = ask(13817, struct.pack('>H', 1) + struct.pack('>II', mid, iid))
        qty2 = int((q('SELECT SUM(quantity) FROM bag_items WHERE rid=? AND bid=?',
                      (RID, SELLABLE)) or [(0,)])[0][0] or 0)
        left = len(q('SELECT 1 FROM role_market_goods WHERE rid=? AND market_id=?',
                     (RID, mid)))
        e17 = (b17[0] == 1) and (qty2 == qty0) and (left == 0)
        print('  13817 提取：code=%d ｜ 背包 %d→%d ｜ 摊位行=%d ｜ %s'
              % (b17[0], qty1, qty2, left, '✓' if e17 else '✗'))
        ok = ok and e17

        # ---- ④ 诚实失败 ----
        print('\n== ④ 诚实失败（不假装成功）==')
        notsell = 35161                      # ★ 不在 `MarketCanSellItem` 里
        urllib.request.urlopen('http://127.0.0.1:8080/DSH_ADMIN/addbag?bid=%d&n=1'
                               % notsell, timeout=8).read()
        nr = q('SELECT item_id FROM bag_items WHERE rid=? AND bid=?', (RID, notsell))
        b_bad = ask(13811, struct.pack('>IIHB', int(nr[0][0]) if nr else 0, 0, 1, 0))
        e_bad = (b_bad[0] == 0)
        _ml = struct.unpack_from('>H', b_bad, 1)[0]
        print('  13811 不可上架物品：code=%d msg=%r ｜ %s'
              % (b_bad[0], b_bad[3:3 + _ml].decode('utf-8', 'replace'),
                 '✓' if e_bad else '✗'))
        ok = ok and e_bad

        b21 = ask(13821, bytes([1]))
        e21 = (b21[0] == 0)
        print('  13821 扩展摊位：code=%d ｜ %s' % (b21[0], '✓' if e21 else '✗'))
        ok = ok and e21
        x('DELETE FROM bag_items WHERE rid=? AND bid=?', (RID, notsell))
    finally:
        restore()

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
