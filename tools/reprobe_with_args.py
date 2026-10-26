# -*- coding: utf-8 -*-
"""按 §6.1-B「空 CS 假象」复探：用**真参数**重发，区分"真缺口"与"探针假象"。

用法：python tools/reprobe_with_args.py [--port 9000]
"""
import socket, struct, sys, argparse, json, os, sqlite3

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "server", "state", "roles.db")


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
    def call(self, cmd, body=b'', maxskip=60):
        self.send(cmd, body)
        for _ in range(maxskip):
            try:
                c, b = self.recv()
            except Exception:
                return None
            if c == cmd:
                return b
        return None
    def settle(self, rounds=15):
        self.s.settimeout(0.4)
        try:
            for _ in range(rounds): self.recv()
        except Exception: pass
        finally: self.s.settimeout(3)


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


def verdict(b):
    if b is None:
        return 'NO-REPLY'
    if not any(b):
        return '空/全零（len=%d）' % len(b)
    return '有真值（len=%d）' % len(b)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()

    # 真参数：NPC bid（地图 NPC 配置）+ 背包实例 id
    npcs = []
    for p in ('server/_mapnpc_10001.json', 'server/_npcs_10001.json'):
        fp = os.path.join(ROOT, p)
        if os.path.exists(fp):
            try:
                j = json.load(open(fp, encoding='utf-8'))
                arr = j if isinstance(j, list) else (j.get('npcs') or list(j.values()))
                for x in (arr or [])[:3]:
                    if isinstance(x, dict) and x.get('bid'):
                        npcs.append(int(x['bid']))
                    elif isinstance(x, (int, str)) and str(x).isdigit():
                        npcs.append(int(x))
            except Exception:
                pass
        if npcs:
            break
    con = sqlite3.connect(DB)
    items = [r[0] for r in con.execute(
        'SELECT item_id FROM bag_items WHERE rid=1001 ORDER BY item_id LIMIT 3').fetchall()]
    con.close()
    print('真参数：npc_bids=%s  bag item_ids=%s\n' % (npcs or '(无)', items or '(无)'))

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.send(10102, struct.pack('>I', 1001)); c.settle()

    print('=== 用【空 CS】复测（对照） ===')
    for cmd in (15203, 10527, 10532, 10560, 11300, 11301):
        b = c.call(cmd)
        print('  %-6d 空CS      → %s' % (cmd, verdict(b)))

    print('\n=== 用【真参数】复测 ===')
    # 15203 NPC 交互：CS{bid:u32}
    for nb in (npcs or [0])[:3]:
        b = c.call(15203, struct.pack('>I', nb))
        print('  15203 npc=%-6d → %s' % (nb, verdict(b)))
    # 105xx 家族：CS 常以 item_id 开头（10527/10532/10560 属装备/背包族）
    for it in (items or [0])[:3]:
        for cmd in (10527, 10532, 10560):
            b = c.call(cmd, struct.pack('>I', it))
            print('  %-6d item=%-5d → %s' % (cmd, it, verdict(b)))
    # 11300/11301：CS{type:u8} 猜测（各试 0/1）
    for cmd in (11300, 11301):
        for t in (0, 1):
            b = c.call(cmd, struct.pack('>B', t))
            print('  %-6d type=%-4d → %s' % (cmd, t, verdict(b)))
    c.s.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
