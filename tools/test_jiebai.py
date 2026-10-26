# -*- coding: utf-8 -*-
"""结拜/金兰（195xx）PHASE 2 测试 —— 直连 TCP，逐帧严格解析。
用法：python tools/test_jiebai.py [--port 9191]
"""
import socket, struct, sys, argparse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191); a = ap.parse_args()
    c = C(a.host, a.port)
    print('connected %s:%d' % (a.host, a.port))

    # 清理：若已结拜，先取消
    _, b = c.call(19514); r = R(b); jid = r.u32()
    if jid: c.call(19533)

    print('\n[1] 19505 发起结拜')
    cmd, b = c.call(19505); r = R(b); code = r.u8(); msg = r.s()
    ck('19505 code=1', code == 1, 'code=%d msg=%r' % (code, msg))

    print('\n[2] 19514 打开结拜空间')
    cmd, b = c.call(19514); r = R(b)
    jid = r.u32(); jsrv = r.s(); front = r.s(); mlen = r.u8(); end = r.s(); lev = r.u8()
    lead = r.s(); exp = r.u32(); notice = r.s(); n = r.u16()
    ck('19514 cmd', cmd == 19514)
    ck('19514 jid 非 0', jid != 0, 'jid=%d' % jid)
    ck('19514 member_len=1', mlen == 1, 'mlen=%d' % mlen)
    ck('19514 member_list=1', n == 1, 'n=%d' % n)
    print('        front=%r end=%r lev=%d leader=%r' % (front, end, lev, lead))
    if n >= 1:
        rid = r.u32(); srv = r.s(); nm = r.s(); sort = r.u8(); sex = r.u8(); car = r.u8()
        sec = r.s(); tro = r.u32(); mlev = r.u8(); jy = r.u32(); jyt = r.u32(); on = r.u8(); off = r.u32()
        ck('19514 成员名非空', bool(nm), 'name=%r second=%r' % (nm, sec))

    print('\n[3] 19530 成员列表')
    cmd, b = c.call(19530); r = R(b); n = r.u16(); et = r.u32()
    ck('19530 cmd', cmd == 19530)
    ck('19530 成员数=1', n == 1, 'n=%d' % n)

    print('\n[4] 19536 提升结拜空间等级')
    cmd, b = c.call(19536); r = R(b); code = r.u8(); msg = r.s(); jlev = r.u8()
    ck('19536 code=1', code == 1, 'code=%d jlev=%d' % (code, jlev))
    ck('19536 jlev=2', jlev == 2, 'jlev=%d' % jlev)

    print('\n[5] 19533 取消结拜')
    cmd, b = c.call(19533); r = R(b); code = r.u8(); msg = r.s()
    ck('19533 code=1', code == 1, 'code=%d msg=%r' % (code, msg))

    print('\n[6] 19514 取消后应为空（jid=0）')
    cmd, b = c.call(19514); r = R(b); jid = r.u32()
    ck('19514 jid=0', jid == 0, 'jid=%d' % jid)

    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0

if __name__ == '__main__':
    sys.exit(main())
