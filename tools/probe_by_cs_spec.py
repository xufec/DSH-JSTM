# -*- coding: utf-8 -*-
"""按 `fields.json` 的 **CS 规格精确构造**请求，复探"疑桩"。

为什么需要它：上一轮"手工猜参数"复探得到了**第二次假象**（`CS_15203` 其实是**空消息**）。
本工具严格按 `CS_<cmd>` 的字段序/类型编码（数值 0、string 空、table 0 行），
得到**结构合法**的请求 ⇒ 再看回包，才能分清"真缺口"与"探针假象"。

用法：python tools/probe_by_cs_spec.py [--port 9000] [cmds...]
"""
import socket, struct, sys, argparse, os, json, io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "server"))

from protocol.fields import _cs_fields  # noqa: E402

DEFAULT = [15203, 10527, 10532, 10560, 11300, 11301, 10924, 16605, 16903, 10923,
           13369, 17200, 14009, 13401, 14901, 10331, 11700]


def w_u8(v): return struct.pack('>B', int(v) & 0xff)
def w_u16(v): return struct.pack('>H', int(v) & 0xffff)
def w_u32(v): return struct.pack('>I', int(v) & 0xffffffff)
def w_str(s):
    b = (s or '').encode('utf-8')
    return w_u16(len(b)) + b


def _w(tp):
    tp = (tp or '').lower()
    if tp.startswith('uint8') or tp in ('int8', 'bool'):
        return 1
    if tp.startswith('uint16') or tp.startswith('int16'):
        return 2
    if tp.startswith('uint32') or tp.startswith('int32'):
        return 4
    return 0


def encode_cs(fields):
    """按 CS 规格编码：数值 0、string 空、table 0 行（结构合法）。"""
    out = b''
    for f in (fields or []):
        if not isinstance(f, dict):
            continue
        tp = (f.get('type') or '').lower()
        if tp.startswith('string'):
            out += w_str('')
        elif tp == 'table':
            out += w_u16(0)
        elif tp.startswith('struct'):
            out += encode_cs(f.get('items') or [])
        else:
            w = _w(tp)
            out += (w_u8(0) if w == 1 else w_u16(0) if w == 2 else w_u32(0) if w == 4 else b'')
    return out


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    ap.add_argument('cmds', nargs='*', type=int)
    a = ap.parse_args()
    cmds = a.cmds or DEFAULT
    names = json.load(open(os.path.join(ROOT, 'protocol', 'cmd_table.json'), encoding='utf-8'))

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.send(10102, struct.pack('>I', 1001)); c.settle()

    out = io.StringIO()
    out.write('%-7s %-9s %-11s %-13s %s\n' % ('cmd', 'CS规格', 'CS长度', '回包判定', '名称'))
    out.write('-' * 92 + '\n')
    for cmd in cmds:
        fs = _cs_fields(cmd)
        csn = len(fs or [])
        body = encode_cs(fs)
        b = c.call(cmd, body)
        if b is None:
            v = 'NO-REPLY'
        elif not any(b):
            v = '空/全零'
        else:
            v = '有真值'
        out.write('%-7d %-9s %-11d %-13s %s\n' % (cmd, '%d 字段' % csn, len(body), v,
                                                  str(names.get(str(cmd), ''))[:26]))
    txt = out.getvalue()
    open(os.path.join(ROOT, 'analysis', 'probe_by_cs_spec.txt'), 'w', encoding='utf-8').write(txt)
    print(txt)
    c.s.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
