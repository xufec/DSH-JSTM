# -*- coding: utf-8 -*-
"""拍卖行（18020/18021/18022）PHASE 2.9 测试。

★ 用**新建的一次性账号/角色**驱动，避免动到 1001 的资产与背包。
用法：python tools/test_auction.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")
ACC = 'dsh_auction_test'
GOODS_ID = 1050          # config_auction_data: item_bid=21904, assets=guild_contrib, buy_price=3000

def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p

class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10); self.buf = b''
    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))
    def recv(self):
        while len(self.buf) < 4:
            d = self.s.recv(65536)
            if not d: raise RuntimeError('closed')
            self.buf += d
        ln = struct.unpack('>I', self.buf[:4])[0]
        while len(self.buf) < 4+ln:
            self.buf += self.s.recv(65536)
        pay = self.buf[4:4+ln]; self.buf = self.buf[4+ln:]
        return struct.unpack('>H', pay[:2])[0], pay[2:]
    def call(self, cmd, body=b'', maxskip=60):
        self.send(cmd, body)
        for _ in range(maxskip):
            c, b = self.recv()
            if c == cmd:
                return c, b
        raise RuntimeError('no reply %d' % cmd)
    def settle(self, rounds=10):
        self.s.settimeout(0.4)
        try:
            for _ in range(rounds): self.recv()
        except Exception: pass
        finally: self.s.settimeout(3)

class R:
    def __init__(self, b): self.b = b; self.o = 0
    def u8(self): v = self.b[self.o]; self.o += 1; return v
    def u16(self):
        v = struct.unpack_from('>H', self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from('>I', self.b, self.o)[0]; self.o += 4; return v
    def s(self):
        n = self.u16(); v = self.b[self.o:self.o+n].decode('utf-8','replace'); self.o += n; return v

def args_login(account):
    pairs = [('account', account), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out

_rid = [0]
def cleanup():
    con = sqlite3.connect(DB)
    try:
        r = con.execute('SELECT rid FROM roles WHERE uid=?', (ACC,)).fetchall()
        for (rid,) in r:
            con.execute('DELETE FROM role_assets WHERE rid=?', (rid,))
            con.execute('DELETE FROM bag_items WHERE rid=?', (rid,))
        con.execute('DELETE FROM roles WHERE uid=?', (ACC,))
        con.execute('DELETE FROM accounts WHERE uid=?', (ACC,))
    except Exception: pass
    con.commit(); con.close()

def seed_asset(rid, name, amount):
    con = sqlite3.connect(DB)
    con.execute('INSERT OR REPLACE INTO role_assets (rid,name,amount) VALUES (?,?,?)',
                (rid, name, amount))
    con.commit(); con.close()

def get_asset(rid, name):
    con = sqlite3.connect(DB)
    r = con.execute('SELECT amount FROM role_assets WHERE rid=? AND name=?', (rid, name)).fetchone()
    con.close(); return int(r[0]) if r else 0

def bag_has(rid, bid):
    con = sqlite3.connect(DB)
    n = con.execute('SELECT COUNT(*) FROM bag_items WHERE rid=? AND bid=?', (rid, bid)).fetchone()[0]
    con.close(); return n

F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c: F.append(n)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191); a = ap.parse_args()
    cleanup()
    c = C(a.host, a.port); c.settle()
    c.call(1110, args_login(ACC))
    nb = '拍卖测试'.encode()
    cmd, b = c.call(10101, struct.pack('>B', 1) + struct.pack('>H', len(nb)) + nb + struct.pack('>h', 1))
    r = R(b); code = r.u8(); r.s(); rid = r.u32()
    _rid[0] = rid
    c.call(10102, struct.pack('>I', rid)); c.settle()
    print('connected %s:%d  test rid=%d' % (a.host, a.port, rid))

    print('\n[1] 18020 打开拍卖行 ⇒ 真实商品列表')
    cmd, b = c.call(18020); r = R(b)
    code = r.u8(); msg = r.s(); bl = r.u16(); nl = r.u16(); n = r.u16()
    ck('18020 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('18020 商品数 > 0', n > 0, 'items=%d' % n)
    first = None
    if n > 0:
        first = (r.u32(), r.u32(), r.u32(), r.u8(), r.u8(), r.u32(), r.u32(),
                 r.u8(), r.u32(), r.u32(), r.s())
        ck('首件 item_bid 非 0', first[1] != 0, 'first=%s' % (first[:7],))
        print('        首件 id=%d item_bid=%d price_assets=%d init=%d buy=%d'
              % (first[0], first[1], first[4], first[5], first[6]))

    print('\n[2] 18021 拍卖物品列表')
    cmd, b = c.call(18021); r = R(b)
    tp = r.u8(); n2 = r.u16()
    ck('18021 商品数 > 0', n2 > 0, 'items=%d' % n2)

    print('\n[3] 18022 货币不足 ⇒ 拒绝')
    seed_asset(rid, 'guild_contrib', 0)
    cmd, b = c.call(18022, struct.pack('>I', GOODS_ID)); r = R(b)
    code = r.u8(); msg = r.s(); _id = r.u32()
    ck('18022 code=0（不足）', code == 0, 'code=%d msg=%r' % (code, msg))

    print('\n[4] 18022 补足货币 ⇒ 购买成功（真扣费 + 真入包）')
    seed_asset(rid, 'guild_contrib', 5000)
    before = get_asset(rid, 'guild_contrib')
    cmd, b = c.call(18022, struct.pack('>I', GOODS_ID)); r = R(b)
    code = r.u8(); msg = r.s(); _id = r.u32()
    ck('18022 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    after = get_asset(rid, 'guild_contrib')
    ck('扣除 3000 资产', before - after == 3000, 'before=%d after=%d' % (before, after))
    ck('物品已入包 bid=21904', bag_has(rid, 21904) >= 1, 'bag=%d' % bag_has(rid, 21904))

    print('\n[5] 18022 不存在的商品 ⇒ 拒绝')
    cmd, b = c.call(18022, struct.pack('>I', 999999)); r = R(b)
    code = r.u8(); msg = r.s(); _id = r.u32()
    ck('18022 code=0（不存在）', code == 0, 'code=%d msg=%r' % (code, msg))

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    try: sys.exit(main())
    finally:
        try: cleanup()
        except Exception: pass
