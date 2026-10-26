# -*- coding: utf-8 -*-
"""R113 验收：`21405` 兑换**真的给符文** + `21406` 符文升级。

流程（真机语义）：
  1. 给足 `rune_chip` 与 `rune_exp`
  2. `CS_21405{21403, 1}` ⇒ `code=1`，且**背包里多出物品 21403**
  3. 取该物品的 `item_id` ⇒ `CS_21406{bag_code=1, id}` ⇒ `code=1`，`role_runes` 等级 1→2
  4. 再升一次仍应成功（材料够）；材料耗尽应回 `code=0`

用法： python tools/verify_rune_upgrade.py
"""
import io
import os
import socket
import sqlite3
import struct
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), 'server', 'state', 'roles.db')
RID = 1001
RUNE_BID = 21403


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


def bag_item_id(bid):
    c = sqlite3.connect(DB)
    r = c.execute('SELECT item_id FROM bag_items WHERE rid=? AND bid=? ORDER BY item_id DESC',
                  (RID, bid)).fetchone()
    return r[0] if r else None


def bag_count(bid):
    """★ 判"是否真的拿到符文"要数 **`quantity` 总和**，不是行数 ——
    `db_bag_add(..., merge=True)` 对已存在的物品是**数量 +1、不新增行**，
    数行数会得出"没变化"的假结论（这条判据我改了三次：先 `max(item_id)`、
    再 `COUNT(*)`、最后才是 `SUM(quantity)`）。"""
    c = sqlite3.connect(DB)
    r = c.execute('SELECT COALESCE(SUM(quantity),0) FROM bag_items '
                  'WHERE rid=? AND bid=?', (RID, bid)).fetchone()
    return int(r[0]) if r else 0


def asset(name):
    c = sqlite3.connect(DB)
    r = c.execute('SELECT amount FROM role_assets WHERE rid=? AND name=?', (RID, name)).fetchone()
    return r[0] if r else 0


def rune_lev(bid):
    c = sqlite3.connect(DB)
    try:
        r = c.execute('SELECT lev FROM role_runes WHERE rid=? AND rune_bid=?',
                      (RID, bid)).fetchone()
    except sqlite3.OperationalError:
        # 表还没建（第一次 21406 调用时才建）⇒ 与实现一致：默认等级 1
        return 1
    return r[0] if r else 1


def grant(name, amount):
    urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/setassets?%s=%d' % (name, amount), timeout=8).read()


def reset_rune_lev():
    """★★ 幂等前置：把符文的等级**重置为 1**。

    为什么必须做：本验收会**每次升一级**，反复跑会把符文升到 **50 级（满级）**
    ⇒ 之后 `21406` 只会回「已满级或该符文无升级配置」⇒ 验收恒定 FAIL。
    （这是本会话第 4 次"验收不幂等"：前三次是 `verify_ride` 表未建、
     `verify_unsupported4` 金币花光、`verify_rune_equip` 装备残留。）
    """
    c = sqlite3.connect(DB)
    try:
        c.execute('UPDATE role_runes SET lev=1 WHERE rid=?', (RID,))
        c.commit()
    except sqlite3.OperationalError:
        pass          # 表还没建（首次）⇒ 默认等级就是 1
    finally:
        c.close()


def main():
    ok = True
    grant('rune_chip', 50000)
    grant('rune_exp', 50000)
    reset_rune_lev()          # ★★ 幂等前置：反复跑会把符文升到满级 ⇒ 必须重置
    print('前置：rune_chip=%d  rune_exp=%d' % (asset('rune_chip'), asset('rune_exp')))

    # ---- 21405：兑换应真的给符文
    before = bag_count(RUNE_BID)
    chip0 = asset('rune_chip')
    b = ask(21405, struct.pack('>I', RUNE_BID) + struct.pack('>H', 1))
    c, m = code_msg(b)
    after_cnt = bag_count(RUNE_BID)      # ★ 用**数量**判"是否真的拿到"（幂等）
    after = bag_item_id(RUNE_BID)
    chip1 = asset('rune_chip')
    print('\n== CS_21405{21403,1} ==')
    print('  code=%d msg=%r  rune_chip %d→%d  背包里 21403 数量: %s→%s'
          % (c, m, chip0, chip1, before, after_cnt))
    a1 = c == 1 and chip0 - chip1 == 4500 and after_cnt == before + 1
    print('  扣 4500 且**真的拿到符文**（数量 +1）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 21406：升级
    if after is None:
        print('\n!! 没拿到符文，21406 无法测')
        print('\n=== 结果: FAIL ===')
        return 1
    lev0 = rune_lev(RUNE_BID)
    exp0 = asset('rune_exp')
    b = ask(21406, bytes([1]) + struct.pack('>I', after))
    c, m = code_msg(b)
    lev1 = rune_lev(RUNE_BID)
    exp1 = asset('rune_exp')
    print('\n== CS_21406{bag_code=1, id=%d} ==' % after)
    print('  code=%d msg=%r  等级 %d→%d  rune_exp %d→%d' % (c, m, lev0, lev1, exp0, exp1))
    a2 = c == 1 and lev1 == lev0 + 1 and exp0 - exp1 > 0
    print('  升级成功且扣了 rune_exp ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 材料耗尽 ⇒ code=0
    grant('rune_exp', 0)
    b = ask(21406, bytes([1]) + struct.pack('>I', after))
    c, m = code_msg(b)
    print('\n== CS_21406（rune_exp=0）==')
    print('  code=%d msg=%r' % (c, m))
    a3 = c == 0 and '不足' in m
    print('  回 code=0 + 材料不足 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
