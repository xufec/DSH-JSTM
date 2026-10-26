"""直连 TCP 验证背包「整理」(10509) 与「删除物品」(10557)。

用法：python tools/bag_test.py [要删除的 item_id ...]   # 默认删最后一格
"""
import socket
import struct
import sys
import time

HOST, PORT = '127.0.0.1', 9000


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


def read_frames(sock, seconds=2.0):
    sock.settimeout(0.6)
    buf, out, end = b'', [], time.time() + seconds
    while time.time() < end:
        try:
            c = sock.recv(65536)
            if not c:
                break
            buf += c
        except socket.timeout:
            if out:
                break
            continue
        while len(buf) >= 6:
            ln = struct.unpack_from('>I', buf, 0)[0]
            if len(buf) < 4 + ln:
                break
            out.append((struct.unpack_from('>H', buf, 4)[0], buf[6:4 + ln]))
            buf = buf[4 + ln:]
    return out


def parse_bag(body):
    """SC_10502{bag_code:u8, items:table(...16 字段)} → [(item_id, bid, pos, qty)]

    一条记录 39 字节（按 build_bag_items 的字段顺序）：
      4+4+4+1+1+2+2+4+4+2+1+2+2+2+2+2 = 39
    """
    n = struct.unpack_from('>H', body, 1)[0]
    off, rows = 3, []
    for _ in range(n):
        iid = struct.unpack_from('>I', body, off)[0]
        bid = struct.unpack_from('>I', body, off + 4)[0]
        pos = struct.unpack_from('>H', body, off + 14)[0]
        qty = struct.unpack_from('>H', body, off + 16)[0]
        rows.append((iid, bid, pos, qty))
        off += 39
    return rows


def sc_code_msg(body):
    code = body[0]
    mlen = struct.unpack_from('>H', body, 1)[0]
    return code, body[3:3 + mlen].decode('utf-8', 'replace')


def bag(s):
    s.sendall(frame(10502, bytes([1])))
    for c, b in read_frames(s, 1.5):
        if c == 10502:
            return parse_bag(b)
    return []


s = socket.create_connection((HOST, PORT), timeout=5)
rows = bag(s)
print('① 当前背包 %d 件: %s' % (len(rows), [(r[0], r[1], r[2]) for r in rows]))

targets = [int(x) for x in sys.argv[1:]] or ([rows[-1][0]] if rows else [])
print('\n② 删除 item_id=%s（10557）' % targets)
args = struct.pack('>H', len(targets)) + b''.join(struct.pack('>I', t) for t in targets)
s.sendall(frame(10557, bytes([1]) + args))
for c, b in read_frames(s, 2.5):
    if c == 10557:
        print('    SC_10557 code=%d msg=%r' % sc_code_msg(b))
    elif c == 10500:
        print('    SC_10500 bag push bag_code=%d items=%d'
              % (b[0], struct.unpack_from('>H', b, 1)[0]))

rows2 = bag(s)
print('③ 删除后 %d 件: %s' % (len(rows2), [(r[0], r[1]) for r in rows2]))
assert all(t not in [r[0] for r in rows2] for t in targets), '删除未生效！'

print('\n④ 整理（10509）')
s.sendall(frame(10509, bytes([1])))
for c, b in read_frames(s, 2.5):
    if c == 10509:
        print('    SC_10509 code=%d msg=%r' % sc_code_msg(b))
    elif c == 10500:
        print('    SC_10500 bag push bag_code=%d items=%d'
              % (b[0], struct.unpack_from('>H', b, 1)[0]))

rows3 = bag(s)
print('⑤ 整理后 pos: %s' % [r[2] for r in rows3])
s.close()
print('\n完成')
