# -*- coding: utf-8 -*-
"""好友系统（13300/13321/13303/13305）双角色测试。

用法：python tools/test_friend.py [--port 9000]
"""
import socket, struct, sys, argparse, sqlite3, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "server", "state", "roles.db")
ACC_B = 'dsh_friend_test_b'


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
        while len(self.buf) < 4 + ln:
            self.buf += self.s.recv(65536)
        pay = self.buf[4:4 + ln]; self.buf = self.buf[4 + ln:]
        return struct.unpack('>H', pay[:2])[0], pay[2:]
    def call(self, cmd, body=b'', maxskip=80):
        self.send(cmd, body)
        for _ in range(maxskip):
            c, b = self.recv()
            if c == cmd:
                return c, b
        raise RuntimeError('no reply %d' % cmd)
    def wait_for(self, cmd, rounds=12):
        """等服务端**主动推送**的某帧（跳过其它帧）。"""
        self.s.settimeout(3)
        for _ in range(rounds):
            try:
                c, b = self.recv()
            except Exception:
                return None
            if c == cmd:
                return b
        return None
    def settle(self, rounds=12):
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
        n = self.u16(); v = self.b[self.o:self.o + n].decode('utf-8', 'replace')
        self.o += n; return v


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


def parse_friends(b):
    r = R(b)
    n = r.u16(); out = []
    for _ in range(n):
        out.append({'rid': r.u32(), 'srv': r.s(), 'name': r.s(), 'sex': r.u8(),
                    'lev': r.u16(), 'career': r.u16(), 'power': r.u32(),
                    'login_time': r.u32(), 'face_id': r.u8(), 'online': r.u8(),
                    'group': r.u32(), 'intimacy': r.u32(), 'grid': r.u32(),
                    'gsrv': r.s(), 'guild': r.s()})
    return out


def cleanup():
    con = sqlite3.connect(DB)
    rids = [x[0] for x in con.execute('SELECT rid FROM roles WHERE uid=?', (ACC_B,)).fetchall()]
    for sql, p in (('DELETE FROM role_friend', ()), ('DELETE FROM role_friend_req', ()),
                   ('DELETE FROM roles WHERE uid=?', (ACC_B,)),
                   ('DELETE FROM accounts WHERE uid=?', (ACC_B,))):
        try: con.execute(sql, p)
        except Exception: pass
    for rid in rids:
        for t in ('role_assets', 'bag_items', 'role_attr'):
            try: con.execute('DELETE FROM %s WHERE rid=?' % t, (rid,))
            except Exception: pass
    con.commit(); con.close()


F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c: F.append(n)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()
    cleanup()
    A = C(a.host, a.port); B = C(a.host, a.port)
    A.call(1110, args_login('dsh_local'))
    A.call(10102, struct.pack('>I', 1001)); A.settle()
    B.call(1110, args_login(ACC_B))
    nb = '好友B测试'.encode()
    cmd, b = B.call(10101, struct.pack('>B', 1) + struct.pack('>H', len(nb)) + nb + struct.pack('>h', 1))
    r = R(b); r.u8(); r.s(); ridB = r.u32()
    B.call(10102, struct.pack('>I', ridB)); B.settle()
    print('A rid=1001  B rid=%d' % ridB)

    print('\n[1] 初始：双方好友列表与申请列表均为空')
    cmd, b = A.call(13300); fa = parse_friends(b)
    cmd, b = B.call(13300); fb = parse_friends(b)
    cmd, b = B.call(13321); rq = parse_friends(b)
    ck('A 好友=0', len(fa) == 0, 'n=%d' % len(fa))
    ck('B 好友=0', len(fb) == 0, 'n=%d' % len(fb))
    ck('B 申请=0', len(rq) == 0, 'n=%d' % len(rq))

    print('\n[2] A 申请加 B（13303）')
    cmd, b = A.call(13303, struct.pack('>I', ridB) + struct.pack('>H', 1) + b'1')
    r = R(b); code = r.u8(); msg = r.s()
    ck('13303 code=1', code == 1, 'code=%d msg=%r' % (code, msg))

    print('\n[3] B 应看到申请（13321，含 A 的名字）')
    cmd, b = B.call(13321); rq = parse_friends(b)
    ck('B 申请=1', len(rq) == 1, 'n=%d' % len(rq))
    if rq:
        ck('申请来自 A(1001)', rq[0]['rid'] == 1001, 'rid=%d' % rq[0]['rid'])
        ck('申请带真名 DSH', rq[0]['name'] == 'DSH', 'name=%r' % rq[0]['name'])
        ck('带等级/战力真值', rq[0]['lev'] > 0 and rq[0]['power'] > 0,
           'lev=%d power=%d' % (rq[0]['lev'], rq[0]['power']))

    print('\n[4] B 同意（13305 agreed=1）⇒ 建立双向好友')
    cmd, b = B.call(13305, struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1' + struct.pack('>B', 1))
    r = R(b); _rid = r.u32(); _srv = r.s(); code = r.u8(); msg = r.s()
    ck('13305 code=1', code == 1, 'code=%d msg=%r' % (code, msg))

    print('\n[5] 双方 13300 应互为好友')
    cmd, b = A.call(13300); fa = parse_friends(b)
    cmd, b = B.call(13300); fb = parse_friends(b)
    ck('A 好友=1 且是 B', len(fa) == 1 and fa[0]['rid'] == ridB,
       'fa=%s' % [(x['rid'], x['name']) for x in fa])
    ck('B 好友=1 且是 A', len(fb) == 1 and fb[0]['rid'] == 1001,
       'fb=%s' % [(x['rid'], x['name']) for x in fb])
    ck('B 申请列表已清', len(parse_friends(B.call(13321)[1])) == 0)

    print('\n[6] 重复申请 ⇒ 拒绝')
    cmd, b = A.call(13303, struct.pack('>I', ridB) + struct.pack('>H', 1) + b'1')
    r = R(b); code = r.u8(); msg = r.s()
    ck('已是好友 ⇒ code=0', code == 0, 'code=%d msg=%r' % (code, msg))

    print('\n[7] A 主动删友（13307）⇒ 双向删除，且 B 收到 13308 推送')
    cmd, b = A.call(13307, struct.pack('>I', ridB) + struct.pack('>H', 1) + b'1')
    got8 = B.wait_for(13308)
    r = R(b); _r = r.u32(); _s = r.s(); code = r.u8(); msg = r.s()
    ck('13307 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('A 好友=0', len(parse_friends(A.call(13300)[1])) == 0)
    ck('B 好友=0（双向已删）', len(parse_friends(B.call(13300)[1])) == 0)
    ck('B 收到 13308 被动删友推送', got8 is not None)

    print('\n[8] 再申请 ⇒ B 收到 13304 推送；13323 一键清空申请')
    A.send(13303, struct.pack('>I', ridB) + struct.pack('>H', 1) + b'1')
    got4 = B.wait_for(13304)
    ck('B 收到 13304（A 想加好友）', got4 is not None)
    if got4:
        r = R(got4); fr = r.u32(); fs = r.s(); fname = r.s(); fsex = r.u8(); flev = r.u8()
        ck('13304 带 A 的 rid/名字', fr == 1001 and fname == 'DSH', 'rid=%d name=%r' % (fr, fname))
    ck('B 申请=1', len(parse_friends(B.call(13321)[1])) == 1)
    cmd, b = B.call(13323)
    r = R(b); code = r.u8(); s = r.s()
    ck('13323 code=1', code == 1, 'code=%d' % code)
    ck('清空后 B 申请=0', len(parse_friends(B.call(13321)[1])) == 0)

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0
    return 1 if F else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        try:
            cleanup()
        except Exception:
            pass
