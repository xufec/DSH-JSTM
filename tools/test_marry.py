# -*- coding: utf-8 -*-
"""结婚（183xx）PHASE 2 测试。

覆盖：18300 诚实失败（单角色）、18318 状态、18313 离婚检查、18321 婚戒进阶、
18322 婚戒技能、18314 发起离婚、18316 离婚应答。
由于 18300 需要第二角色，测试用 **DB 夹具**先写入婚姻状态再驱动后续命令。

用法：python tools/test_marry.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")

def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p

class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10); self.buf = b''
    def call(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))
        while len(self.buf) < 4:
            self.buf += self.s.recv(65536)
        ln = struct.unpack('>I', self.buf[:4])[0]
        while len(self.buf) < 4 + ln:
            self.buf += self.s.recv(65536)
        pay = self.buf[4:4+ln]; self.buf = self.buf[4+ln:]
        return struct.unpack('>H', pay[:2])[0], pay[2:]

class R:
    def __init__(self, b): self.b = b; self.o = 0
    def u8(self): v = self.b[self.o]; self.o += 1; return v
    def u16(self):
        v = struct.unpack_from('>H', self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from('>I', self.b, self.o)[0]; self.o += 4; return v
    def s(self):
        n = self.u16(); v = self.b[self.o:self.o+n].decode('utf-8', 'replace'); self.o += n; return v

F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c: F.append(n)

def seed(state, spouse_rid=0, spouse_name='', ring_lev=0, ring_skill=0):
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS role_marry (rid INTEGER PRIMARY KEY, spouse_rid INTEGER, '
                'spouse_name TEXT, state INTEGER, marry_time INTEGER, ring_lev INTEGER, '
                'ring_skill INTEGER, qifen INTEGER)')
    con.execute('INSERT OR REPLACE INTO role_marry VALUES (?,?,?,?,?,?,?,?)',
                (1001, spouse_rid, spouse_name, state, 0, ring_lev, ring_skill, 0))
    con.commit(); con.close()

def read(rid=1001):
    con = sqlite3.connect(DB)
    r = con.execute('SELECT state,spouse_name,ring_lev,ring_skill FROM role_marry WHERE rid=?',
                    (rid,)).fetchone()
    con.close(); return r

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191); a = ap.parse_args()
    seed(0)                                    # 干净起点
    c = C(a.host, a.port)
    print('connected %s:%d' % (a.host, a.port))

    print('\n[1] 18300 发起求婚（单角色 ⇒ 诚实失败）')
    cmd, b = c.call(18300); r = R(b); code = r.u8(); msg = r.s()
    ck('18300 code=0（不编造）', code == 0, 'code=%d msg=%r' % (code, msg))

    print('\n[2] 18318 未婚状态')
    cmd, b = c.call(18318); r = R(b); st = r.u8(); nm = r.s()
    ck('18318 state=0', st == 0, 'state=%d name=%r' % (st, nm))

    print('\n[3] 夹具：写入已婚状态 (spouse=测试妻)')
    seed(1, spouse_rid=2002, spouse_name='测试妻')
    ck('DB 已写入 state=1', (read() or [None])[0] == 1)

    print('\n[4] 18318 已婚状态')
    cmd, b = c.call(18318); r = R(b); st = r.u8(); nm = r.s()
    ck('18318 state=1', st == 1, 'state=%d' % st)
    ck('18318 spouse_name=测试妻', nm == '测试妻', 'name=%r' % nm)

    print('\n[5] 18313 离婚条件检查')
    cmd, b = c.call(18313); r = R(b); ret = r.u8()
    ck('18313 ret=1', ret == 1, 'ret=%d' % ret)

    print('\n[6] 18321 婚戒装备进阶')
    cmd, b = c.call(18321); r = R(b); code = r.u8(); msg = r.s()
    ck('18321 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('DB ring_lev=1', (read() or [0]*4)[2] == 1, 'ring_lev=%s' % ((read() or [0]*4)[2],))

    print('\n[7] 18322 婚戒技能升级 skill_id=12345')
    cmd, b = c.call(18322, struct.pack('>I', 12345)); r = R(b); code = r.u8(); msg = r.s(); nid = r.u32()
    ck('18322 code=1', code == 1, 'code=%d' % code)
    ck('18322 new_skill_id=12345', nid == 12345, 'nid=%d' % nid)
    ck('DB ring_skill=12345', (read() or [0]*4)[3] == 12345, 'ring_skill=%s' % ((read() or [0]*4)[3],))

    print('\n[8] 18314 发起离婚 → state=2')
    cmd, b = c.call(18314, struct.pack('>B', 1)); r = R(b); code = r.u8(); msg = r.s()
    ck('18314 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('DB state=2', (read() or [None])[0] == 2, 'state=%s' % ((read() or [None])[0],))

    print('\n[9] 18313 离婚中 ⇒ ret=0')
    cmd, b = c.call(18313); r = R(b); ret = r.u8()
    ck('18313 ret=0', ret == 0, 'ret=%d' % ret)

    print('\n[10] 18316 同意离婚 → state=0')
    cmd, b = c.call(18316, struct.pack('>B', 1)); r = R(b); code = r.u8(); msg = r.s()
    ck('18316 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('DB state=0', (read() or [None])[0] == 0, 'state=%s' % ((read() or [None])[0],))
    cmd, b = c.call(18318); r = R(b); st = r.u8(); nm = r.s()
    ck('18318 离婚后 state=0', st == 0, 'state=%d' % st)

    seed(0)                                    # 清理
    try:
        _c = sqlite3.connect(DB); _c.execute('DELETE FROM role_marry'); _c.commit(); _c.close()
    except Exception:
        pass
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    sys.exit(main())
