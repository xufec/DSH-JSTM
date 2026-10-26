# -*- coding: utf-8 -*-
"""结婚求婚闭环（18300 → 18301 → 18302 → 18303）双连接测试。

★ 说明：`CS_18300` 是**空消息**（客户端不上传求婚对象）⇒ 目标由服务端**意向表**
  `role_marry_propose` 决定。本测试用 DB 夹具写入意向，再驱动 18300。

用法：python tools/test_marry_propose.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")
ACC_B = 'dsh_marry_test_b'

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
    def wait_for(self, cmd, rounds=12):
        self.s.settimeout(3)
        for _ in range(rounds):
            try: c, b = self.recv()
            except Exception: return None
            if c == cmd: return b
        return None
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
                        ('DELETE FROM role_marry', ()),
                        ('DELETE FROM role_marry_propose', ())):
        try: con.execute(sql, params)
        except Exception: pass
    con.commit(); con.close()

def propose_set(fr, to):
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS role_marry_propose (from_rid INTEGER PRIMARY KEY, '
                'to_rid INTEGER, ctime INTEGER)')
    con.execute('INSERT OR REPLACE INTO role_marry_propose VALUES (?,?,0)', (fr, to))
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
    cmd, b = B.call(10101, struct.pack('>B', 1) + struct.pack('>H', len('求婚B测试'.encode()))
                    + '求婚B测试'.encode() + struct.pack('>h', 1))
    r = R(b); r.u8(); r.s(); ridB = r.u32()
    B.call(10102, struct.pack('>I', ridB)); B.settle()
    print('A rid=1001  B rid=%d' % ridB)

    print('\n[1] 双方初始未婚')
    for nm, cn in (('A', A), ('B', B)):
        cmd, b = cn.call(18318); r = R(b); st = r.u8(); sp = r.s()
        ck('%s 未婚' % nm, st == 0, 'state=%d spouse=%r' % (st, sp))

    print('\n[2] A 无意向时求婚 ⇒ 诚实失败')
    cmd, b = A.call(18300); r = R(b); code = r.u8(); msg = r.s()
    ck('18300 code=0（无意向）', code == 0, 'code=%d msg=%r' % (code, msg))

    print('\n[3] 夹具写入意向 A→B，A 发起求婚')
    propose_set(1001, ridB)
    cmd, b = A.call(18300); r = R(b); code = r.u8(); msg = r.s()
    ck('18300 code=1', code == 1, 'code=%d msg=%r' % (code, msg))

    print('\n[4] B 收到 18301 求婚推送')
    p = B.wait_for(18301)
    ck('B 收到 18301', p is not None)
    if p:
        r = R(p); ss = r.u8(); ps = r.u8(); boy = r.s(); gril = r.s(); oid = r.u32(); osrv = r.s()
        ck('18301 obj_rid=1001(A)', oid == 1001, 'obj_rid=%d' % oid)
        print('        self_state=%d spouse_state=%d boy=%r gril=%r' % (ss, ps, boy, gril))

    print('\n[5] B 同意（18302 ret=1）')
    # 注意：服务端在**回 18302 之前**就把 18303 推给了双方 ⇒ 这里同时收集两种帧
    B.send(18302, struct.pack('>B', 1))
    code = None; got3 = None
    for _ in range(14):
        c, bb = B.recv()
        if c == 18302:
            code = R(bb).u8()
        elif c == 18303:
            got3 = bb
        if code is not None and got3 is not None:
            break
    ck('18302 code=1', code == 1, 'code=%s' % code)
    ck('B 收到 18303 结果推送', got3 is not None)
    if got3:
        r3 = R(got3); s3 = r3.u8(); p3 = r3.u8(); m3 = r3.s()
        ck('18303 结果为已婚(state=1)', s3 == 1, 'self=%d spouse=%d msg=%r' % (s3, p3, m3))

    print('\n[6] 双方已婚且配偶互指')
    cmd, b = A.call(18318); r = R(b); stA = r.u8(); spA = r.s()
    cmd, b = B.call(18318); r = R(b); stB = r.u8(); spB = r.s()
    ck('A state=1', stA == 1, 'state=%d spouse=%r' % (stA, spA))
    ck('B state=1', stB == 1, 'state=%d spouse=%r' % (stB, spB))
    ck('A 配偶名 = B', spA == '求婚B测试', 'spouse=%r' % spA)
    ck('B 配偶名 = A', spB == 'DSH', 'spouse=%r' % spB)

    print('\n[7] A 离婚检查 ret=1')
    cmd, b = A.call(18313); r = R(b); ret = r.u8()
    ck('18313 ret=1', ret == 1, 'ret=%d' % ret)

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    try: sys.exit(main())
    finally:
        try: cleanup()
        except Exception: pass
