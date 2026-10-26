# -*- coding: utf-8 -*-
"""Verify SC_10304 carries practice_exp (gap #5, server-side half).

Layout per server/attribute/handler.py handle_10304.
Usage: python tools/verify_practice_exp.py [--port 9000]
"""
import socket, struct, sys, argparse

def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p

class R:
    def __init__(self, b): self.b = b; self.o = 0
    def u8(self): v = self.b[self.o]; self.o += 1; return v
    def u16(self):
        v = struct.unpack_from('>H', self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from('>I', self.b, self.o)[0]; self.o += 4; return v
    def s(self):
        n = self.u16(); v = self.b[self.o:self.o+n].decode('utf-8', 'replace'); self.o += n; return v

ATTR = ['strength','intellect','armor','constiution','atk_s','atk_p','def_s','def_p','hp_max',
        'atk_speed','hit','dodge','crit','tenacity','red_def_s','red_def_p','atk_abs','def_abs',
        'reduce','hurt','hit_rate_show','dodge_rate_show','crit_rate_show','tenacity_rate_show']

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()
    s = socket.create_connection((a.host, a.port), timeout=10)
    s.sendall(frame(10304))
    buf = b''
    while len(buf) < 4:
        buf += s.recv(65536)
    ln = struct.unpack('>I', buf[:4])[0]
    while len(buf) < 4 + ln:
        buf += s.recv(65536)
    cmd = struct.unpack('>H', buf[4:6])[0]
    body = buf[6:4+ln]
    print('reply cmd = %d  body = %d bytes' % (cmd, len(body)))
    if cmd != 10304:
        print('!! unexpected cmd'); return 2
    r = R(body)
    rid = r.u32(); srv = r.s(); name = r.s(); lev = r.u16()
    for _ in range(3): r.u8()          # is_vip, vip_lev, sex
    career = r.u16()
    for _ in range(6): r.u8()          # volume x6
    r.u16()                            # attr_point
    r.u16()                            # skill_list
    power = r.u32()
    assets = {}
    for k in ('exp','gold','coin','gold_acc','sinew','experience','coupon','vitality',
              'guild_contrib','practice_exp','tower_cent','arena_cent'):
        assets[k] = r.u32()
    cnt = r.u16(); attrs = {}
    if cnt:
        for i, k in enumerate(ATTR):
            attrs[k] = r.u16() if (i < 4 or 16 <= i < 20) else r.u32()
    mspd = r.u16(); r.u16(); vip_exp = r.u32()
    try:
        jt = r.s(); jl = r.u8()
    except Exception as e:
        jt, jl = '<tail-parse-skipped: %s>' % e, -1
    print('rid=%s name=%s lev=%d career=%d power=%d' % (rid, name, lev, career, power))
    print('assets:', assets)
    print('attrs : atk_s=%s hp_max=%s' % (attrs.get('atk_s'), attrs.get('hp_max')))
    print('mspd=%d vip_exp=%d jiebai=%r/%s' % (mspd, vip_exp, jt, jl))
    print('')
    print('*** practice_exp = %s  (expect 35) ***' % assets.get('practice_exp'))
    s.close()

    # ---- SC_10302 (client actually requests this; has practice_exp field) ----
    s2 = socket.create_connection((a.host, a.port), timeout=10)
    s2.sendall(frame(10302, b'\x00\x0a\x00\x07'))
    buf = b''
    while len(buf) < 4:
        buf += s2.recv(65536)
    ln = struct.unpack('>I', buf[:4])[0]
    while len(buf) < 4 + ln:
        buf += s2.recv(65536)
    c2 = struct.unpack('>H', buf[4:6])[0]
    b2 = buf[6:4+ln]
    r2 = R(b2)
    lev2 = r2.u16()
    f10302 = ['exp','gold','gold_acc','coin','sinew','experience','coupon','vitality',
              'guild_contrib','practice_exp','tower_cent','arena_cent']
    vals = {}
    for k in f10302:
        vals[k] = r2.u32()
    print('')
    print('SC_10302 reply cmd=%d len=%d lev=%d' % (c2, len(b2), lev2))
    print('  10302 assets:', vals)
    print('*** 10302 practice_exp = %s  (expect 35) ***' % vals.get('practice_exp'))
    s2.close()
    return 0 if vals.get('practice_exp') == 35 else 1

if __name__ == '__main__':
    sys.exit(main())
