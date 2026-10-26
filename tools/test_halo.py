# -*- coding: utf-8 -*-
"""光环（19100/19103/19104）PHASE 2.8 测试。

用法：python tools/test_halo.py [--port 9191]
"""
import socket, struct, sys, argparse, sqlite3, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "state", "roles.db")
BAG_ITEM = 308            # 真实背包物品（bid=28514）
BAD_ITEM = 999999

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

def cleanup():
    con = sqlite3.connect(DB)
    for sql, params in (('DELETE FROM role_halo', ()), ('DELETE FROM role_halo_equip', ())):
        try: con.execute(sql, params)
        except Exception: pass
    con.commit(); con.close()

def equip_rows():
    con = sqlite3.connect(DB)
    try: r = con.execute('SELECT item_id,bid FROM role_halo_equip').fetchall()
    except Exception: r = []
    con.close(); return r

F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c: F.append(n)

def parse_19100(b):
    r = R(b)
    stage = r.u8(); power = r.u32(); luck = r.u16(); res_stage = r.u8(); grow = r.u16()
    sk = r.u16()                       # skill_list 计数
    items = r.u16()                    # items 计数
    return {'stage': stage, 'power': power, 'luck': luck, 'res_stage': res_stage,
            'grow': grow, 'skills': sk, 'items': items}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191); a = ap.parse_args()
    cleanup()
    c = C(a.host, a.port); c.settle()
    print('connected %s:%d' % (a.host, a.port))

    print('\n[1] 19100 初始光环信息')
    cmd, b = c.call(19100)
    ck('19100 cmd', cmd == 19100)
    d = parse_19100(b)
    ck('19100 stage=0', d['stage'] == 0, str(d))
    ck('19100 items=0', d['items'] == 0, str(d))

    print('\n[2] 19103 穿戴不存在的物品 ⇒ 拒绝')
    cmd, b = c.call(19103, struct.pack('>I', BAD_ITEM)); r = R(b); code = r.u8(); msg = r.s()
    ck('19103 code=0', code == 0, 'code=%d msg=%r' % (code, msg))

    print('\n[3] 19103 穿戴真实背包物品 item_id=%d' % BAG_ITEM)
    cmd, b = c.call(19103, struct.pack('>I', BAG_ITEM)); r = R(b); code = r.u8(); msg = r.s()
    ck('19103 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('DB 已记录装备位', any(x[0] == BAG_ITEM for x in equip_rows()), 'rows=%s' % (equip_rows(),))

    print('\n[4] 19100 应含 1 件光环装备')
    cmd, b = c.call(19100)
    d = parse_19100(b)
    ck('19100 items=1', d['items'] == 1, str(d))

    print('\n[5] 19104 卸下')
    cmd, b = c.call(19104, struct.pack('>I', BAG_ITEM)); r = R(b); code = r.u8(); msg = r.s()
    ck('19104 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    ck('DB 装备位已清空', equip_rows() == [], 'rows=%s' % (equip_rows(),))
    cmd, b = c.call(19100)
    d = parse_19100(b)
    ck('19100 items=0', d['items'] == 0, str(d))

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    try: sys.exit(main())
    finally:
        try: cleanup()
        except Exception: pass
