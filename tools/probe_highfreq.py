# -*- coding: utf-8 -*-
"""核对高频"已闭环"命令是否真闭环：回包是**真值**还是**空表/全零**。

判据（保守）：
  · body 极短（如 2~5 字节）且内容为 "0000…" ⇒ **可疑空表**
  · body 里含非零数据 ⇒ **可能真值**（仍需按 spec 解码确认）
用法：python tools/probe_highfreq.py [--port 9000]
"""
import socket, struct, sys, argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 客户端高频、HANDOFF 标"已闭环"或未定性的命令
TARGETS = [16605, 16903, 16904, 16400, 16500, 10922, 10923, 10924, 17800,
           20809, 13300, 13321, 17100, 16601, 10925, 12901, 12931]


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10)
        self.buf = b''
    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))
    def recv(self):
        while len(self.buf) < 4:
            d = self.s.recv(65536)
            if not d:
                raise RuntimeError('closed')
            self.buf += d
        ln = struct.unpack('>I', self.buf[:4])[0]
        while len(self.buf) < 4 + ln:
            self.buf += self.s.recv(65536)
        pay = self.buf[4:4 + ln]
        self.buf = self.buf[4 + ln:]
        return struct.unpack('>H', pay[:2])[0], pay[2:]
    def call(self, cmd, body=b'', maxskip=80):
        self.send(cmd, body)
        for _ in range(maxskip):
            c, b = self.recv()
            if c == cmd:
                return c, b
        return None, None
    def settle(self, rounds=12):
        self.s.settimeout(0.4)
        try:
            for _ in range(rounds):
                self.recv()
        except Exception:
            pass
        finally:
            self.s.settimeout(3)


def judge(body):
    if body is None:
        return 'NO-REPLY'
    if len(body) <= 6 and not any(body):
        return '*** 空表/全零（疑桩）'
    if not any(body):
        return '全零（长度 %d）' % len(body)
    return '有非零数据（长度 %d）' % len(body)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()
    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', 1001))
    c.settle()
    print('connected %s:%d（已登录 rid=1001）\n' % (a.host, a.port))
    print('%-7s %-8s %-34s %s' % ('cmd', 'len', '前 24 字节', '判定'))
    print('-' * 88)
    for cmd in TARGETS:
        c2, b = c.call(cmd)
        if c2 is None:
            print('%-7d %-8s %-34s %s' % (cmd, '-', '-', 'NO-REPLY'))
            continue
        hexs = b[:24].hex(' ')
        print('%-7d %-8d %-34s %s' % (cmd, len(b), hexs, judge(b)))
    c.s.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
