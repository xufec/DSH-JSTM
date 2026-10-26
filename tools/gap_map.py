# -*- coding: utf-8 -*-
"""按真实流量生成"缺口地图"：客户端发过的命令 → 回包是真值还是空表。

用法：python tools/gap_map.py [--port 9000] [--top 60]
输出：analysis/gap_map.txt（按客户端调用次数排序，标注空表/真值/无应答）
"""
import socket, struct, sys, argparse, re, collections, os, io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "server", "logs", "tcp.log")


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
    def call(self, cmd, body=b'', maxskip=60):
        self.send(cmd, body)
        for _ in range(maxskip):
            try:
                c, b = self.recv()
            except Exception:
                return None          # 超时/断线 ⇒ 视为"无应答"
            if c == cmd:
                return b
        return None
    def settle(self, rounds=15):
        self.s.settimeout(0.4)
        try:
            for _ in range(rounds): self.recv()
        except Exception: pass
        finally: self.s.settimeout(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    ap.add_argument('--top', type=int, default=60)
    a = ap.parse_args()

    sent = collections.Counter()
    for line in open(LOG, encoding='utf-8', errors='ignore'):
        m = re.search(r'>> cmd=(\d+)', line)
        if m:
            sent[int(m.group(1))] += 1
    cmds = [c for c, _ in sent.most_common(a.top) if c != 1199]
    import json
    names = json.load(open(os.path.join(ROOT, 'protocol', 'cmd_table.json'), encoding='utf-8'))

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.send(10102, struct.pack('>I', 1001)); c.settle()

    out = io.StringIO()
    out.write('cmd     发次   回包长  判定                          名称\n')
    out.write('-' * 96 + '\n')
    empty, real, noreply = [], [], []
    for cmd in cmds:
        b = c.call(cmd)
        nm = str(names.get(str(cmd), ''))[:28]
        if b is None:
            verdict = 'NO-REPLY'
            noreply.append(cmd)
        elif not any(b):
            verdict = '空/全零' if len(b) > 6 else '空表(疑桩)'
            empty.append(cmd)
        else:
            verdict = '有真值'
            real.append(cmd)
        out.write('%-8d %-6d %-7d %-30s %s\n' % (cmd, sent[cmd], len(b) if b is not None else -1,
                                                 verdict, nm))
    out.write('\n=== 汇总 ===\n')
    out.write('探针命令数 = %d\n' % len(cmds))
    out.write('有真值 %d 条：%s\n' % (len(real), real))
    out.write('空/全零 %d 条：%s\n' % (len(empty), empty))
    out.write('无应答 %d 条：%s\n' % (len(noreply), noreply))
    open(os.path.join(ROOT, 'analysis', 'gap_map.txt'), 'w', encoding='utf-8').write(out.getvalue())
    print(out.getvalue()[-1500:])
    print('\nwrote analysis/gap_map.txt')
    c.s.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
