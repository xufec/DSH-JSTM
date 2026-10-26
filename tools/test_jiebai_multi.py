# -*- coding: utf-8 -*-
"""结拜多人（19524 邀请 → 19511 通知 → 19512 确认 → 19513 结果）双连接测试。

用法：python tools/test_jiebai_multi.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")
ACC_B = 'dsh_jiebai_test_b'

def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p

class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10); self.buf = b''
    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))
    def _need(self, n):
        while len(self.buf) < n:
            d = self.s.recv(65536)
            if not d: raise RuntimeError('closed')
            self.buf += d
    def recv(self):
        self._need(4)
        ln = struct.unpack('>I', self.buf[:4])[0]
        self._need(4+ln)
        pay = self.buf[4:4+ln]; self.buf = self.buf[4+ln:]
        return struct.unpack('>H', pay[:2])[0], pay[2:]
    def call(self, cmd, body=b'', maxskip=60):
        self.send(cmd, body)
        for _ in range(maxskip):
            c, b = self.recv()
            if c == cmd:
                return c, b
        raise RuntimeError('no reply for %d' % cmd)
    def collect(self, cmd, body, want, rounds=16):
        """发送并收集 want 里的帧（返回 {cmd: body}），同时保证 cmd 的应答也拿到。"""
        self.send(cmd, body)
        got = {}
        for _ in range(rounds):
            c, b = self.recv()
            if c in want and c not in got:
                got[c] = b
            if cmd in got and all(w in got for w in want):
                break
        return got
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

def args_login(account):
    pairs = [('account', account), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out

def cleanup():
    con = sqlite3.connect(DB)
    for sql, params in (('DELETE FROM roles WHERE uid=?', (ACC_B,)),
                        ('DELETE FROM accounts WHERE uid=?', (ACC_B,)),
                        ('DELETE FROM role_jiebai', ())):
        try: con.execute(sql, params)
        except Exception: pass
    con.commit(); con.close()

F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c: F.append(n)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191); a = ap.parse_args()
    cleanup()
    A = C(a.host, a.port); B = C(a.host, a.port)
    print('connected x2 -> %s:%d' % (a.host, a.port))

    A.call(1110, args_login('dsh_local')); A.call(10102, struct.pack('>I', 1001)); A.settle()
    B.call(1110, args_login(ACC_B))
    nb = '结拜B测试'.encode()
    cmd, b = B.call(10101, struct.pack('>B', 1) + struct.pack('>H', len(nb)) + nb + struct.pack('>h', 1))
    r = R(b); r.u8(); r.s(); ridB = r.u32()
    B.call(10102, struct.pack('>I', ridB)); B.settle()
    print('A rid=1001  B rid=%d' % ridB)

    print('\n[1] A 发起结拜（1 人）')
    cmd, b = A.call(19505); r = R(b); code = r.u8(); msg = r.s()
    ck('19505 code=1', code == 1, 'code=%d msg=%r' % (code, msg))

    print('\n[2] A 邀请 B（19524）→ B 收到 19511')
    cmd, b = A.call(19524, struct.pack('>I', ridB) + struct.pack('>H', 0))
    r = R(b); code = r.u8(); msg = r.s(); rid_r = r.u32(); srv_r = r.s()
    ck('19524 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    got = B.collect(19511, b'', (19511,), rounds=6)
    ck('B 收到 19511 通知', 19511 in got)

    print('\n[3] B 确认结拜（19512 flag=1）')
    got = B.collect(19512, struct.pack('>B', 1), (19512, 19513))
    ck('B 收到 19512 应答', 19512 in got)
    if 19512 in got:
        r = R(got[19512]); code = r.u8(); msg = r.s()
        ck('19512 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('B 收到 19513 结果', 19513 in got)
    if 19513 in got:
        r = R(got[19513]); code = r.u8(); msg = r.s()
        ck('19513 全场确认(code=1)', code == 1, 'code=%d msg=%r' % (code, msg))

    print('\n[4] A 侧成员列表应为 2 人')
    cmd, b = A.call(19530); r = R(b); n = r.u16(); et = r.u32()
    ck('19530 成员数=2', n == 2, 'n=%d' % n)
    cmd, b = A.call(19514); r = R(b)
    jid = r.u32(); r.s(); r.s(); mlen = r.u8()
    ck('19514 member_len=2', mlen == 2, 'mlen=%d' % mlen)

    print('\n[5] B 侧也能看到结拜（同 jid）')
    cmd, b = B.call(19514); r = R(b); jidB = r.u32()
    ck('B 同一结拜', jidB == jid and jid != 0, 'jidA=%d jidB=%d' % (jid, jidB))

    print('\n[6] A 取消结拜')
    cmd, b = A.call(19533); r = R(b); code = r.u8()
    ck('19533 code=1', code == 1, 'code=%d' % code)
    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    try: sys.exit(main())
    finally:
        try: cleanup()
        except Exception: pass
