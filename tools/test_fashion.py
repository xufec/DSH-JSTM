# -*- coding: utf-8 -*-
"""时装（10573-10578）PHASE 2.7 测试。

用法：python tools/test_fashion.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")
GOOD_BID = 43264          # config_fashion 里的真实时装（夏日冰淇淋）
OTHER_BID = 43263         # 另一件（用于"未激活"用例）
BAD_BID = 999999

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
    def settle(self, rounds=8):
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

def cleanup():
    con = sqlite3.connect(DB)
    try: con.execute('DELETE FROM role_fashion')
    except Exception: pass
    con.commit(); con.close()

def rows():
    con = sqlite3.connect(DB)
    try:
        r = con.execute('SELECT bid,active,worn,star FROM role_fashion ORDER BY bid').fetchall()
    except Exception:
        r = []
    con.close(); return r

F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c: F.append(n)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191); a = ap.parse_args()
    cleanup()
    c = C(a.host, a.port); c.settle()
    print('connected %s:%d' % (a.host, a.port))

    print('\n[1] 10573 激活无效时装的 bid ⇒ 拒绝')
    cmd, b = c.call(10573, struct.pack('>I', BAD_BID)); r = R(b)
    code = r.u8(); bid = r.u32(); msg = r.s()
    ck('10573 无效 bid code=0', code == 0, 'code=%d msg=%r' % (code, msg))
    ck('10573 回显 bid', bid == BAD_BID, 'bid=%d' % bid)

    print('\n[2] 10573 激活真实时装 bid=%d ⇒ 成功并落库' % GOOD_BID)
    cmd, b = c.call(10573, struct.pack('>I', GOOD_BID)); r = R(b)
    code = r.u8(); bid = r.u32(); msg = r.s()
    ck('10573 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('DB 已激活', any(x[0] == GOOD_BID and x[1] == 1 for x in rows()), 'rows=%s' % (rows(),))

    print('\n[3] 10574 穿戴（未激活的 id ⇒ 拒绝；已激活 ⇒ 成功）')
    cmd, b = c.call(10574, struct.pack('>I', OTHER_BID)); r = R(b)
    code = r.u8(); _id = r.u32(); msg = r.s()
    ck('10574 未激活 code=0', code == 0, 'code=%d msg=%r' % (code, msg))
    cmd, b = c.call(10574, struct.pack('>I', GOOD_BID)); r = R(b)
    code = r.u8(); _id = r.u32()
    ck('10574 code=1', code == 1, 'code=%d' % code)
    ck('DB worn=1', any(x[0] == GOOD_BID and x[2] == 1 for x in rows()), 'rows=%s' % (rows(),))

    print('\n[4] 10575 升星 → star+1')
    cmd, b = c.call(10575, struct.pack('>I', GOOD_BID)); r = R(b); code = r.u8(); _id = r.u32()
    ck('10575 code=1', code == 1, 'code=%d' % code)
    ck('DB star=1', any(x[0] == GOOD_BID and x[3] == 1 for x in rows()), 'rows=%s' % (rows(),))

    print('\n[5] 10576 脱下 → worn=0')
    cmd, b = c.call(10576, struct.pack('>I', GOOD_BID)); r = R(b); code = r.u8(); _id = r.u32()
    ck('10576 code=1', code == 1, 'code=%d' % code)
    ck('DB worn=0', any(x[0] == GOOD_BID and x[2] == 0 for x in rows()), 'rows=%s' % (rows(),))

    print('\n[6] 10578 使用物品激活另一件时装')
    cmd, b = c.call(10578, struct.pack('>I', OTHER_BID)); r = R(b); code = r.u8(); msg = r.s()
    ck('10578 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('DB 两件已激活', sum(1 for x in rows() if x[1] == 1) == 2, 'rows=%s' % (rows(),))

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    try: sys.exit(main())
    finally:
        try: cleanup()
        except Exception: pass
