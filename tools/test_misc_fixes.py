# -*- coding: utf-8 -*-
"""零散修复项的回归测试（14901 称号 / 16900 累计充值 / GM setcharge）。

覆盖本会话（PHASE 2.16~2.17）的三处改动：
  · 14901：读 `role_title` 真值（原先硬编码 0/空表）
  · 16900：`charge` 读 `role_gt.total_charge`（原先硬编码 0）
  · GM `GET /DSH_ADMIN/setcharge?n=`：走 `growth_target.service` 写 `role_gt`

★ 跑在真实角色 1001 上 ⇒ 快照并还原 `role_title` / `role_gt`。
用法：python tools/test_misc_fixes.py [--port 9000] [--http 8080]
"""
import socket
import struct
import sys
import argparse
import sqlite3
import os
import json
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "server", "state", "roles.db")
RID = 1001


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10)
        self.buf = b''
    def call(self, cmd, body=b'', maxskip=80):
        self.s.sendall(frame(cmd, body))
        for _ in range(maxskip):
            while len(self.buf) < 4:
                self.buf += self.s.recv(65536)
            ln = struct.unpack('>I', self.buf[:4])[0]
            while len(self.buf) < 4 + ln:
                self.buf += self.s.recv(65536)
            pay = self.buf[4:4 + ln]
            self.buf = self.buf[4 + ln:]
            c = struct.unpack('>H', pay[:2])[0]
            if c == cmd:
                return pay[2:]
        raise RuntimeError('no reply %d' % cmd)


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


def _tbl(sql, p=()):
    con = sqlite3.connect(DB)
    try:
        r = con.execute(sql, p).fetchall()
    except Exception:
        r = []
    con.close()
    return r


def titles():
    return [(int(x[0]), int(x[1])) for x in
            _tbl('SELECT bid, ctime FROM role_title WHERE rid=? ORDER BY bid', (RID,))]


def set_titles(rows):
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS role_title (rid INTEGER, bid INTEGER, ctime INTEGER, '
                'PRIMARY KEY (rid, bid))')
    con.execute('DELETE FROM role_title WHERE rid=?', (RID,))
    for bid, ct in (rows or []):
        con.execute('INSERT OR REPLACE INTO role_title VALUES (?,?,?)', (RID, int(bid), int(ct)))
    con.commit(); con.close()


def gt_rows():
    return _tbl('SELECT login_day,charge_day,total_charge FROM role_gt WHERE rid=?', (RID,))


def set_gt(rows):
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS role_gt (rid INTEGER PRIMARY KEY, login_day INTEGER, '
                'charge_day INTEGER, total_charge INTEGER)')
    con.execute('DELETE FROM role_gt WHERE rid=?', (RID,))
    for r in (rows or []):
        con.execute('INSERT OR REPLACE INTO role_gt VALUES (?,?,?,?)',
                    (RID, int(r[0]), int(r[1]), int(r[2])))
    con.commit(); con.close()


SNAP = {}


def snapshot():
    SNAP['title'] = titles()
    SNAP['gt'] = gt_rows()


def cleanup():
    set_titles(SNAP.get('title') or [])
    set_gt(SNAP.get('gt') or [])


F = []


def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c:
        F.append(n)


def http_get(url):
    with urllib.request.urlopen(url, timeout=8) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    ap.add_argument('--http', type=int, default=8080)
    a = ap.parse_args()
    snapshot()

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', RID))
    print('connected %s:%d rid=%d' % (a.host, a.port, RID))

    print('\n[1] 14901 称号列表：空表 ⇒ titles=0')
    set_titles([])
    b = c.call(14901)
    cur = struct.unpack_from('>H', b, 0)[0]
    n = struct.unpack_from('>H', b, 2)[0]
    ck('14901 无称号 ⇒ 0 条', n == 0, 'cur_bid=%d titles=%d' % (cur, n))

    print('\n[2] 14901 写入 2 个称号（与 GM 同一条写入路径）⇒ titles=2')
    set_titles([(1001, 0), (1002, 0)])
    b = c.call(14901)
    n = struct.unpack_from('>H', b, 2)[0]
    got = []
    o = 4
    for _ in range(n):
        got.append((struct.unpack_from('>H', b, o)[0], struct.unpack_from('>I', b, o + 2)[0]))
        o += 6
    ck('14901 有称号 ⇒ 2 条且 bid 正确', got == [(1001, 0), (1002, 0)], 'got=%s' % got)

    print('\n[3] 16900 累计充值：读 role_gt.total_charge（非硬编码 0）')
    set_gt([(0, 0, 123)])
    b = c.call(16900)
    chg = struct.unpack_from('>I', b, 0)[0]
    ck('16900 charge == role_gt.total_charge', chg == 123, 'charge=%d' % chg)

    print('\n[4] GM setcharge 走 Service 写 role_gt，并反映到 16900')
    url = 'http://127.0.0.1:%d/DSH_ADMIN/setcharge?n=456' % a.http
    j = http_get(url)
    ck('setcharge 返回 ok', bool(j.get('ok')), 'resp=%s' % j)
    ck('setcharge 回 total_charge=456', j.get('total_charge') == 456, 'resp=%s' % j)
    rows = _tbl('SELECT total_charge FROM role_gt WHERE rid=?', (RID,))
    ck('role_gt 落库 456', rows and int(rows[0][0]) == 456, 'rows=%s' % rows)
    b = c.call(16900)
    chg = struct.unpack_from('>I', b, 0)[0]
    ck('16900 反映 456', chg == 456, 'charge=%d' % chg)

    print('\n[5] GM setcharge 清零（还原）')
    j = http_get('http://127.0.0.1:%d/DSH_ADMIN/setcharge?n=0' % a.http)
    ck('清零 ok', bool(j.get('ok')) and j.get('total_charge') == 0, 'resp=%s' % j)

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        try:
            cleanup()
        except Exception:
            pass
