# -*- coding: utf-8 -*-
"""Verify the server PUSHES SC_10305 after login, carrying practice_exp(label=9)=35.

Usage: python tools/verify_10305_push.py [--host 127.0.0.1] [--port 9000]
Login sequence: 1110 (account) -> 10102 (role rid=1001) -> collect frames.
"""
import socket, struct, sys, argparse

def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p

def args_login(account):
    pairs = [('account', account), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out

class Conn:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10)
        self.buf = b''
    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))
    def frames(self, seconds=3.0):
        """Collect frames until timeout."""
        self.s.settimeout(seconds)
        out = []
        try:
            while True:
                while len(self.buf) < 4:
                    d = self.s.recv(65536)
                    if not d:
                        return out
                    self.buf += d
                ln = struct.unpack('>I', self.buf[:4])[0]
                while len(self.buf) < 4 + ln:
                    d = self.s.recv(65536)
                    if not d:
                        return out
                    self.buf += d
                cmd = struct.unpack('>H', self.buf[4:6])[0]
                out.append((cmd, self.buf[6:4 + ln]))
                self.buf = self.buf[4 + ln:]
        except Exception:
            return out
    def close(self):
        try: self.s.close()
        except Exception: pass

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()
    c = Conn(a.host, a.port)

    c.send(1110, args_login('dsh_local'))
    f1 = c.frames(2.0)
    print('after 1110  : cmds =', [x for x, _ in f1])

    c.send(10102, struct.pack('>I', 1001))
    f2 = c.frames(3.0)
    print('after 10102 : cmds =', [x for x, _ in f2])

    allf = f1 + f2
    got = [b for cmd, b in allf if cmd == 10305]
    if not got:
        print('\n*** FAIL: SC_10305 NOT pushed ***')
        c.close()
        return 1
    body = got[-1]
    n = struct.unpack('>H', body[:2])[0]
    off = 2
    assets = {}
    for _ in range(n):
        lb = body[off]
        val = struct.unpack('>I', body[off + 1:off + 5])[0]
        assets[lb] = val
        off += 5
    print('\n*** SC_10305 PUSHED: %d asset rows ***' % n)
    print('    ', dict(sorted(assets.items())))
    pe = assets.get(9)
    print('*** label9 (practice_exp) = %s  (expect 35) ***' % pe)
    c.close()
    return 0 if pe == 35 else 1

if __name__ == '__main__':
    sys.exit(main())
