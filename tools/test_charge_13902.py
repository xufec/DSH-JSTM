# -*- coding: utf-8 -*-
"""充值（13901 商品列表 / 13902 充值发钻石）回归测试。PHASE 2.33。

需求（用户）：**不需要外接充值接口，直接点击充值档位获得对应钻石。**
数据源：`server/cfg/config_charge.json` 的 `ChargeList`（9 档）。
  val=元 ｜ gold=基础钻石 ｜ add=常驻赠送 ｜ first_add=该档首次购买加赠
副作用：充值成功后**累加 `role_gt.total_charge`**（驱动 `16900` 与 `30502`）。
★ 跑在真实角色 1001 上 ⇒ 快照并还原 `role_assets.gold` / `role_gt` / `dungeon_progress(charged)`。
"""
import socket
import struct
import sys
import argparse
import sqlite3
import os
import json

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
        self.buf = bytearray()
    def call(self, cmd, body=b'', maxskip=80):
        self.s.sendall(frame(cmd, body))
        for _ in range(maxskip):
            while len(self.buf) < 4:
                self.buf.extend(self.s.recv(65536))
            ln = struct.unpack('>I', bytes(self.buf[:4]))[0]
            while len(self.buf) < 4 + ln:
                self.buf.extend(self.s.recv(65536))
            pay = bytes(self.buf[4:4 + ln])
            del self.buf[:4 + ln]
            if struct.unpack('>H', pay[:2])[0] == cmd:
                return pay[2:]
        return None


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


def q1(sql, p=()):
    con = sqlite3.connect(DB)
    try:
        r = con.execute(sql, p).fetchone()
    except Exception:
        r = None
    con.close()
    return r


def gold():
    r = q1("SELECT COALESCE(amount,0) FROM role_assets WHERE rid=? AND name='gold'", (RID,))
    return int(r[0] or 0) if r else 0


def total_charge():
    r = q1('SELECT COALESCE(total_charge,0) FROM role_gt WHERE rid=?', (RID,))
    return int(r[0] or 0) if r else 0


SNAP = {}


def snapshot():
    SNAP['gold'] = gold()
    con = sqlite3.connect(DB)
    try:
        SNAP['gt'] = con.execute('SELECT login_day,charge_day,total_charge FROM role_gt '
                                 'WHERE rid=?', (RID,)).fetchall()
    except Exception:
        SNAP['gt'] = []
    try:
        SNAP['charged'] = con.execute("SELECT key,value FROM dungeon_progress WHERE rid=? "
                                      "AND kind='charged'", (RID,)).fetchall()
    except Exception:
        SNAP['charged'] = []
    con.close()


def cleanup():
    con = sqlite3.connect(DB)
    for sql in ('DELETE FROM role_gt WHERE rid=?', "DELETE FROM dungeon_progress WHERE rid=? AND kind='charged'"):
        try:
            con.execute(sql, (RID,))
        except Exception:
            pass
    try:
        con.execute("DELETE FROM reward_log WHERE rid=? AND source='charge'", (RID,))
    except Exception:
        pass
    con.commit()
    for row in (SNAP.get('gt') or []):
        con.execute('INSERT OR REPLACE INTO role_gt VALUES (?,?,?,?)',
                    (RID, row[0], row[1], row[2]))
        break
    for k, v in (SNAP.get('charged') or []):
        con.execute("INSERT OR REPLACE INTO dungeon_progress (rid,kind,key,value) VALUES (?,?,?,?)",
                    (RID, 'charged', k, v))
    con.execute('UPDATE role_assets SET amount=? WHERE rid=? AND name=?', (SNAP['gold'], RID, 'gold'))
    con.commit()
    con.close()


F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c:
        F.append(n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    a = ap.parse_args()
    snapshot(); cleanup()

    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_charge.json'),
                         encoding='utf-8')).get('ChargeList') or {}
    rows = {}
    for k, v in cfg.items():
        h = v.get('hash') or {}
        rows[int(h.get('val') or k)] = h
    print('config_charge 档位数 = %d：%s' % (len(rows), sorted(rows)))

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', RID))
    print('connected %s:%d rid=%d' % (a.host, a.port, RID))

    print('\n[1] 13901 商品列表 = config_charge 的档位')
    b = c.call(13901, b'')
    o = 4
    n = struct.unpack_from('>H', b, o)[0]; o += 2
    got = []
    for _ in range(n):
        uv = struct.unpack_from('>I', b, o)[0]
        gv = struct.unpack_from('>I', b, o + 4)[0]
        av = struct.unpack_from('>I', b, o + 8)[0]
        o += 12 + 3
        got.append((uv, gv, av))
    ck('13901 档位数 == 配置档位数', n == len(rows), 'n=%d cfg=%d' % (n, len(rows)))
    exp = [(v * 100, int(h.get('gold') or 0), int(h.get('add') or 0))
           for v, h in sorted(rows.items())]
    ck('13901 档位内容与配置一致', sorted(got) == sorted(exp), 'got=%s' % got[:3])

    print('\n[2] 13902 充值 6 元 ⇒ 钻石 +120（60 基础 + 60 首充加赠）')
    g0 = gold(); t0 = total_charge()
    b = c.call(13902, struct.pack('>H', 6))
    code = b[0]
    sl = struct.unpack_from('>H', b, 1)[0]
    msg = b[3:3 + sl].decode('utf-8', 'replace')
    ck('13902 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    d = gold() - g0
    ck('钻石 +120', d == 120, 'delta=%d（before=%d after=%d）' % (d, g0, gold()))

    print('\n[3] 重复充值 6 元 ⇒ 只发 60（首充加赠只给一次）')
    g1 = gold()
    b = c.call(13902, struct.pack('>H', 6))
    d2 = gold() - g1
    ck('第二次 +60', d2 == 60, 'delta=%d' % d2)

    print('\n[4] 13902 顺带累加 total_charge（驱动 16900 / 30502）')
    ck('total_charge = 12（6+6）', total_charge() - t0 == 12, 't0=%d now=%d' % (t0, total_charge()))

    print('\n[5] 未知档位 ⇒ 拒绝')
    b = c.call(13902, struct.pack('>H', 7))
    ck('13902 rmb=7 ⇒ code=0', b[0] == 0, 'code=%d' % b[0])

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
