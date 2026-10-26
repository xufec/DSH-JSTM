# -*- coding: utf-8 -*-
"""组队（132xx）PHASE 2 测试 —— 直连 TCP，逐帧严格解析。

用法：
    python tools/test_team.py [--host 127.0.0.1] [--port 9191]
前置：一个 mock_server 实例监听在 --port（默认 9191）。
"""
import socket, struct, sys, argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def frame(cmd, body=b''):
    payload = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(payload)) + payload

class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10)
        self.buf = b''
    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))
    def recv(self):
        while len(self.buf) < 4:
            d = self.s.recv(65536)
            if not d: raise RuntimeError('closed')
            self.buf += d
        ln = struct.unpack('>I', self.buf[:4])[0]
        while len(self.buf) < 4 + ln:
            d = self.s.recv(65536)
            if not d: raise RuntimeError('closed')
            self.buf += d
        payload = self.buf[4:4+ln]
        self.buf = self.buf[4+ln:]
        return struct.unpack('>H', payload[:2])[0], payload[2:]
    def call(self, cmd, body=b''):
        self.send(cmd, body)
        return self.recv()

class R:
    def __init__(self, b): self.b = b; self.o = 0
    def u8(self):
        v = self.b[self.o]; self.o += 1; return v
    def u16(self):
        v = struct.unpack_from('>H', self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from('>I', self.b, self.o)[0]; self.o += 4; return v
    def s(self):
        n = self.u16(); v = self.b[self.o:self.o+n].decode('utf-8', 'replace'); self.o += n; return v

FAILS = []
def check(name, cond, extra=''):
    print(('  PASS  ' if cond else '  FAIL  ') + name + (('  ' + extra) if extra else ''))
    if not cond: FAILS.append(name)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9191)
    a = ap.parse_args()

    c = C(a.host, a.port)
    print('connected %s:%d' % (a.host, a.port))

    # 起始状态：确保干净（若已在队，先解散/离队）
    _, b = c.call(13200)
    r = R(b); r.s(); tid = r.u32()
    if tid:
        c.call(13226)
        c.call(13210)

    print('\n[1] 13201 创建队伍')
    cmd, b = c.call(13201)
    r = R(b); tips = r.u16(); msg = r.s()
    check('13201 返回 cmd=13201', cmd == 13201, 'cmd=%d' % cmd)
    check('13201 tips=1（成功）', tips == 1, 'tips=%d msg=%r' % (tips, msg))

    print('\n[2] 13200 队伍信息（应有 1 名成员）')
    cmd, b = c.call(13200)
    r = R(b); _msg = r.s(); tid = r.u32(); tsrv = r.s(); lid = r.u32(); lsrv = r.s()
    spd = r.u32(); n = r.u16()
    check('13200 cmd', cmd == 13200)
    check('13200 team_id 非 0', tid != 0, 'tid=%d' % tid)
    check('13200 成员数=1', n == 1, 'n=%d' % n)
    if n >= 1:
        mid = r.u32(); msrv = r.s(); mname = r.s(); mlev = r.u8(); mca = r.u16()
        msex = r.u8(); mface = r.u32(); mmode = r.u8(); mhp = r.u32(); mhpmax = r.u32(); mpw = r.u32()
        check('13200 队长=本人', lid == mid, 'leader=%d member=%d' % (lid, mid))
        print('        member name=%r lev=%d career=%d power=%d' % (mname, mlev, mca, mpw))

    print('\n[3] 13218 组队大厅（应含本队）')
    cmd, b = c.call(13218)
    r = R(b); tn = r.u16()
    check('13218 cmd', cmd == 13218)
    check('13218 队伍数>=1', tn >= 1, 'teams=%d' % tn)

    print('\n[4] 13226 解散队伍（队长）')
    cmd, b = c.call(13226)
    r = R(b); tips = r.u16(); msg = r.s()
    check('13226 tips=1', tips == 1, 'tips=%d msg=%r' % (tips, msg))

    print('\n[5] 13200 解散后应为空队')
    cmd, b = c.call(13200)
    r = R(b); r.s(); tid = r.u32(); r.s(); r.u32(); r.s(); r.u32(); n = r.u16()
    check('13200 team_id=0', tid == 0, 'tid=%d' % tid)
    check('13200 成员数=0', n == 0, 'n=%d' % n)

    print('\n[6] 13201 建队 → 13210 离队（最后一人 ⇒ 解散）')
    _, b = c.call(13201)
    r = R(b); tips = r.u16()
    check('13201 二次建队 tips=1', tips == 1, 'tips=%d' % tips)
    _, b = c.call(13210)
    r = R(b); tips = r.u16(); msg = r.s()
    check('13210 离队 tips=1', tips == 1, 'tips=%d msg=%r' % (tips, msg))
    _, b = c.call(13200)
    r = R(b); r.s(); tid = r.u32()
    check('13210 后队伍已解散（tid=0）', tid == 0, 'tid=%d' % tid)

    print('\n[7] 13237 查看不存在玩家的队伍')
    _, b = c.call(13237, struct.pack('>I', 999999) + struct.pack('>H', 0))
    r = R(b); tid = r.u32()
    check('13237 未找到 ⇒ tid=0', tid == 0, 'tid=%d' % tid)

    print('\n==== %s ====' % ('ALL PASS' if not FAILS else ('FAILED: %s' % FAILS)))
    return 1 if FAILS else 0

if __name__ == '__main__':
    sys.exit(main())
