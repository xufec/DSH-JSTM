"""验证 pay_type → 币种 是否与客户端同源表一致：买指定商品，看**哪个资产被扣**。

用法：python tools/shop_paytype_test.py            # 默认买 3001(pay_type=24) 与 4001(pay_type=2)
      python tools/shop_paytype_test.py 3001 4001
"""
import json
import socket
import struct
import sys
import time
import urllib.request

HOST, PORT = '127.0.0.1', 9000
ADMIN = 'http://127.0.0.1:8080/DSH_ADMIN'
DEFAULT = [3001, 4001]


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


def read_frames(sock, seconds=2.5):
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


def assets():
    with urllib.request.urlopen(ADMIN + '/getassets?rid=1001', timeout=8) as r:
        return json.load(r)


def buy(sock, gid):
    sock.sendall(frame(12805, struct.pack('>HH', gid, 1)))
    got = []
    for c, b in read_frames(sock):
        if c == 12805:
            code = b[0]
            mlen = struct.unpack_from('>H', b, 1)[0]
            msg = b[3:3 + mlen].decode('utf-8', 'replace')
            off = 3 + mlen
            _id, num, price = struct.unpack_from('>HHI', b, off)
            got.append('SC_12805 code=%d id=%d num=%d price=%d msg=%r'
                       % (code, _id, num, price, msg))
        elif c == 12831:
            got.append('SC_12831（已购数已刷新，%d 字节）' % len(b))
        elif c == 10500:
            got.append('SC_10500 bag push bag_code=%d' % b[0])
    return got


before = assets()
print('购买前资产:', json.dumps(before, ensure_ascii=False))
s = socket.create_connection((HOST, PORT), timeout=5)
for gid in (sys.argv[1:] or DEFAULT):
    print('\n--- 买 id=%s ---' % gid)
    for line in buy(s, int(gid)):
        print('   ', line)
    time.sleep(0.3)
s.close()
after = assets()
print('\n购买后资产:', json.dumps(after, ensure_ascii=False))
print('\n差额:')
keys = set(before.get('assets', {})) | set(after.get('assets', {}))
for k in sorted(keys):
    b0 = before.get('assets', {}).get(k, 0)
    a0 = after.get('assets', {}).get(k, 0)
    if b0 != a0:
        print('    %-16s %d -> %d  (%+d)' % (k, b0, a0, a0 - b0))
