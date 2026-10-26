# -*- coding: utf-8 -*-
"""统一属性汇总（PHASE 2.10）验证：10304/10306 面板与战力应**跟随 role_attr 表**。

用法：python tools/test_attr_unify.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")
RID = 1001
ATTR_ORDER = ['strength', 'intellect', 'armor', 'constiution', 'atk_s', 'atk_p', 'def_s', 'def_p',
              'hp_max', 'atk_speed', 'hit', 'dodge', 'crit', 'tenacity', 'red_def_s', 'red_def_p',
              'atk_abs', 'def_abs', 'reduce', 'hurt', 'hit_rate_show', 'dodge_rate_show',
              'crit_rate_show', 'tenacity_rate_show']

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

def db_attr(rid=RID):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT * FROM role_attr WHERE rid=?', (rid,)).fetchone()
    con.close()
    return dict(r) if r else {}

def set_db_attr(rid, name, val):
    con = sqlite3.connect(DB)
    con.execute('UPDATE role_attr SET %s=? WHERE rid=?' % name, (val, rid))
    con.commit(); con.close()

def parse_10304(b):
    """返回 (power, {attr: val})。布局见 mock_server 的 10304 编码器。"""
    r = R(b)
    rid = r.u32(); srv = r.s(); name = r.s()
    lev = r.u16(); vipf = r.u8(); viplev = r.u8(); sex = r.u8(); career = r.u16()
    for _ in range(6):      # volume/store_volume/store_partner_volume/open ×2
        r.u8()
    r.u16()                 # attr_point
    r.u16()                 # skill_list 空
    power = r.u32()
    for _ in range(12):     # exp..arena_cent
        r.u32()
    cnt = r.u16()
    vals = {}
    if cnt:
        for i, k in enumerate(ATTR_ORDER):
            vals[k] = r.u16() if i < 4 else r.u32()
    return power, vals

F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c: F.append(n)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191); a = ap.parse_args()
    before = db_attr()
    if not before:
        print('!! role_attr 无 1001 行，跳过'); return 0
    c = C(a.host, a.port); c.settle()
    print('connected %s:%d' % (a.host, a.port))
    try:
        print('\n[1] 10304 面板属性应等于 DB role_attr')
        cmd, b = c.call(10304)
        pw, vals = parse_10304(b)
        ck('10304 cmd', cmd == 10304)
        ck('atk_s 与 DB 一致', vals.get('atk_s') == before.get('atk_s'),
           'panel=%s db=%s' % (vals.get('atk_s'), before.get('atk_s')))
        ck('hp_max 与 DB 一致', vals.get('hp_max') == before.get('hp_max'),
           'panel=%s db=%s' % (vals.get('hp_max'), before.get('hp_max')))
        ck('power > 0', pw > 0, 'power=%d' % pw)

        print('\n[2] 改 DB atk_s ⇒ 10304 与战力应随之变化（证明统一汇总）')
        set_db_attr(RID, 'atk_s', int(before.get('atk_s') or 0) + 5000)
        cmd, b2 = c.call(10304)
        pw2, vals2 = parse_10304(b2)
        ck('atk_s 跟随 DB(+5000)', vals2.get('atk_s') == int(before.get('atk_s') or 0) + 5000,
           'panel=%s' % vals2.get('atk_s'))
        ck('战力随之变化', pw2 != pw, 'before=%d after=%d' % (pw, pw2))

        print('\n[3] 10306（同步小包，无前缀）也应跟随（同一入口）')
        cmd, b3 = c.call(10306)
        ck('10306 cmd', cmd == 10306)
        r = R(b3)
        cnt = r.u16()
        vals306 = {}
        if cnt:
            for i, k in enumerate(ATTR_ORDER):
                vals306[k] = r.u16() if (i < 4 or 16 <= i < 20) else r.u32()
        ck('10306 atk_s 跟随 DB', vals306.get('atk_s') == int(before.get('atk_s') or 0) + 5000,
           'panel=%s' % vals306.get('atk_s'))
        mspd306 = r.u16(); pw306 = r.u32()
        ck('10306 power 跟随 DB', pw306 != pw, 'before=%d after=%d' % (pw, pw306))
    finally:
        set_db_attr(RID, 'atk_s', int(before.get('atk_s') or 0))
        print('\n(已还原 DB atk_s=%s)' % before.get('atk_s'))

    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    sys.exit(main())
