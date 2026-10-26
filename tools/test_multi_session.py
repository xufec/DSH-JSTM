# -*- coding: utf-8 -*-
"""多会话隔离验证（PHASE 2.4）—— 两条连接、两个角色。

验证：
  1) 每个连接可用 10102 绑定自己的角色（实例级 cfg，互不串号）；
  2) A 建的队伍，B 在组队大厅能看到，但 B 自己的队伍信息为空；
  3) 两个角色的队伍状态互不干扰。

用法：python tools/test_multi_session.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")
ACC_B = 'dsh_multi_test_b'

def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p

class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10); self.buf = b''
        self.s.settimeout(3)
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
        """发送并读到**期望 cmd** 的应答（跳过服务端主动推送的帧）。"""
        self.send(cmd, body)
        for _ in range(maxskip):
            c, b = self.recv()
            if c == cmd:
                return c, b
        raise RuntimeError('no reply for cmd=%d' % cmd)
    def settle(self, rounds=8):
        """把服务端主动推送的帧读干净。"""
        self.s.settimeout(0.4)
        try:
            for _ in range(rounds):
                self.recv()
        except Exception:
            pass
        finally:
            self.s.settimeout(3)

class R:
    def __init__(self, b): self.b = b; self.o = 0
    def u8(self): v = self.b[self.o]; self.o += 1; return v
    def u16(self):
        v = struct.unpack_from('>H', self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from('>I', self.b, self.o)[0]; self.o += 4; return v
    def s(self):
        n = self.u16(); v = self.b[self.o:self.o+n].decode('utf-8', 'replace'); self.o += n; return v

def args_login(account):
    pairs = [('account', account), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb = k.encode(); vb = v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out

def create_role_cs(sex, name, career):
    nb = name.encode()
    return struct.pack('>B', sex) + struct.pack('>H', len(nb)) + nb + struct.pack('>h', career)

def cleanup():
    con = sqlite3.connect(DB)
    con.execute('DELETE FROM roles WHERE uid=?', (ACC_B,))
    con.execute('DELETE FROM accounts WHERE uid=? OR name=?', (ACC_B, ACC_B))
    con.execute('DELETE FROM role_team')
    try: con.execute('DELETE FROM role_team_invite')
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

    print('\n[1] A 登录账号 dsh_local，绑定角色 1001')
    A.call(1110, args_login('dsh_local'))
    A.call(10102, struct.pack('>I', 1001)); A.settle()
    cmd, b = A.call(13200); r = R(b); r.s(); tidA = r.u32()
    ck('A 初始无队伍', tidA == 0, 'tidA=%d' % tidA)

    print('\n[2] B 登录新账号并建角')
    B.call(1110, args_login(ACC_B))
    cmd, b = B.call(10101, create_role_cs(1, '小B测试', 1))
    r = R(b); code = r.u8(); msg = r.s(); ridB = r.u32()
    ck('B 建角成功', code == 1 and ridB != 0, 'code=%d rid=%d' % (code, ridB))
    B.call(10102, struct.pack('>I', ridB)); B.settle()
    ck('B 的 rid != 1001', ridB != 1001, 'ridB=%d' % ridB)

    print('\n[3] B 初始无队伍（证明不与 A 串号）')
    cmd, b = B.call(13200); r = R(b); r.s(); tidB = r.u32()
    ck('B 初始无队伍', tidB == 0, 'tidB=%d' % tidB)

    print('\n[4] A 建队 → A 有队')
    cmd, b = A.call(13201); r = R(b); tips = r.u16()
    ck('A 建队 tips=1', tips == 1, 'tips=%d' % tips)
    cmd, b = A.call(13200); r = R(b); r.s(); tidA = r.u32(); r.s(); lidA = r.u32(); r.s(); r.u32(); nA = r.u16()
    ck('A 有队伍', tidA != 0, 'tidA=%d members=%d' % (tidA, nA))
    ck('A 队长=1001', lidA == 1001, 'lidA=%d' % lidA)

    print('\n[5] B 仍无队伍（隔离）')
    cmd, b = B.call(13200); r = R(b); r.s(); tidB = r.u32()
    ck('B 仍无队伍', tidB == 0, 'tidB=%d' % tidB)

    print('\n[6] B 在组队大厅能看到 A 的队伍（跨玩家可见）')
    cmd, b = B.call(13218); r = R(b); tn = r.u16()
    ck('大厅队伍数>=1', tn >= 1, 'teams=%d' % tn)
    seen = []
    for _ in range(tn):
        t_id = r.u32(); t_srv = r.s(); t_lid = r.u32(); t_lsrv = r.s(); t_lname = r.s()
        t_llev = r.u8(); t_lcar = r.u16(); t_lsex = r.u16(); t_mn = r.u8(); t_mm = r.u8()
        seen.append((t_id, t_lid, t_lname))
    ck('大厅含 A 的队伍', any(t[0] == tidA for t in seen), 'seen=%s' % (seen,))
    ck('大厅队长名非空', any(t[2] for t in seen), 'seen=%s' % (seen,))
    print('        大厅条目: %s' % (seen,))

    print('\n[7] B 查看 A 的队伍（13237）')
    cmd, b = B.call(13237, struct.pack('>I', 1001) + struct.pack('>H', 0))
    r = R(b); t37 = r.u32()
    ck('13237 查到 A 的队伍', t37 == tidA, 't37=%d tidA=%d' % (t37, tidA))

    print('\n[8] A 邀请 B 入队（13202）→ B 收到 13203 推送')
    cmd, b = A.call(13202, struct.pack('>I', ridB) + struct.pack('>H', 0))
    r = R(b); tips = r.u16(); msg = r.s()
    ck('13202 邀请 tips=1', tips == 1, 'tips=%d msg=%r' % (tips, msg))
    got3 = None
    B.s.settimeout(3)
    for _ in range(10):
        try:
            c3, b3 = B.recv()
        except Exception:
            break
        if c3 == 13203:
            got3 = b3
            break
    ck('B 收到 13203 邀请推送', got3 is not None)
    if got3:
        r3 = R(got3)
        lid3 = r3.u32(); lsrv3 = r3.s(); lname3 = r3.s(); llev3 = r3.u8(); lcar3 = r3.u8()
        tid3 = r3.u32(); tsrv3 = r3.s(); tn3 = r3.u8(); tm3 = r3.u8(); inv3 = r3.u8()
        ck('13203 来自 A(rid=1001)', lid3 == 1001, 'lid=%d' % lid3)
        ck('13203 invite_flag=1', inv3 == 1, 'inv=%d' % inv3)

    print('\n[9] B 接受邀请（13204）→ A/B 均为 2 人同队')
    cmd, b = B.call(13204, struct.pack('>B', 1) + struct.pack('>I', 1001) + struct.pack('>H', 0))
    r = R(b); tips = r.u8(); msg = r.s(); _id = r.u32(); _srv = r.s()
    ck('13204 接受 tips=1', tips == 1, 'tips=%d msg=%r' % (tips, msg))
    cmd, b = A.call(13200); r = R(b)
    r.s(); tidA2 = r.u32(); r.s(); r.u32(); r.s(); r.u32(); nA2 = r.u16()
    ck('A 队伍 2 人', nA2 == 2, 'n=%d' % nA2)
    cmd, b = B.call(13200); r = R(b)
    r.s(); tidB2 = r.u32(); r.s(); r.u32(); r.s(); r.u32(); nB2 = r.u16()
    ck('B 在队中(2 人)', nB2 == 2, 'n=%d tid=%d' % (nB2, tidB2))
    ck('A/B 同一队伍', tidA2 == tidB2 and tidA2 != 0, 'tidA=%d tidB=%d' % (tidA2, tidB2))

    print('\n[10] 清理：A 解散')
    cmd, b = A.call(13226); r = R(b); tips = r.u16()
    ck('A 解散 tips=1', tips == 1, 'tips=%d' % tips)
    cmd, b = B.call(13200); r = R(b); r.s(); tidB3 = r.u32()
    ck('B 队伍已解散', tidB3 == 0, 'tid=%d' % tidB3)
    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        try: cleanup()
        except Exception: pass

