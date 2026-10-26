"""直连 TCP 回归测试：商城购买 → 扣币 → 入包 → 背包推送(10500, 覆盖所有 bag_code) → 12831 已购数量。

用途：不依赖客户端 UI，直接验证 mock_server 的 12805/10500/12831 代码路径。
用法：先启动服务端，再 `python tools/_shop_buy_test.py`
"""
import socket
import struct
import sys
import time

HOST, PORT = '127.0.0.1', 9000
GOODS_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 2003   # 2003 = 洗髓丹礼盒?? 价 5 / pay_type=1


def frame(cmd, body=b''):
    payload = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(payload)) + payload


def read_frames(sock, seconds=2.5):
    """读若干帧，返回 [(cmd, body)]。"""
    sock.settimeout(0.6)
    buf = b''
    out = []
    end = time.time() + seconds
    while time.time() < end:
        try:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
        except socket.timeout:
            if out:
                break
            continue
        while len(buf) >= 6:
            ln = struct.unpack_from('>I', buf, 0)[0]
            if len(buf) < 4 + ln:
                break
            cmd = struct.unpack_from('>H', buf, 4)[0]
            body = buf[6:4 + ln]
            out.append((cmd, body))
            buf = buf[4 + ln:]
    return out


s = socket.create_connection((HOST, PORT), timeout=5)
print('已连接 %s:%d' % (HOST, PORT))

# 1) 先请求两个不同 bag_code 的背包（模拟客户端多页请求）→ 让本连接记录 bag_codes_seen
for bc in (1, 7, 12):
    s.sendall(frame(10502, bytes([bc])))
    time.sleep(0.15)
r = read_frames(s, 1.5)
print('① 10502 回包: %s' % [(c, len(b)) for c, b in r])

# 2) 购买
s.sendall(frame(12805, struct.pack('>HH', GOODS_ID, 1)))
r = read_frames(s, 2.5)
print('② 购买后收到:')
code = None
for c, b in r:
    if c == 10500:
        print('   SC_10500 背包推送 bag_code=%d items=%d (body %d 字节)'
              % (b[0], struct.unpack_from('>H', b, 1)[0], len(b)))
    elif c == 12805:
        code = b[0]
        # SC_12805{code:u8, msg:string(u16 len + bytes), id:u16, num:u16, price:u32}
        msg_len = struct.unpack_from('>H', b, 1)[0]
        off = 3 + msg_len
        gid, num, price = struct.unpack_from('>HHI', b, off)
        print('   SC_12805 code=%d id=%d num=%d price=%d' % (code, gid, num, price))
    elif c in (10301, 10302, 10303):
        print('   SC_%d 角色刷新 (%d 字节)' % (c, len(b)))
    else:
        print('   cmd=%d (%d 字节)' % (c, len(b)))

# 3) 12831：已购数量
s.sendall(frame(12831))
r = read_frames(s, 2.0)
for c, b in r:
    if c == 12831:
        n = struct.unpack_from('>H', b, 0)[0]
        pairs = [struct.unpack_from('>HH', b, 2 + i * 4) for i in range(n)]
        hit = [p for p in pairs if p[0] == GOODS_ID]
        print('③ SC_12831 id_list=%d, 商品 %d 的 has_buy_num=%s'
              % (n, GOODS_ID, hit[0][1] if hit else '未找到'))
        print('   非零已购商品: %s' % [p for p in pairs if p[1]][:10])
    else:
        print('③ 其它回包 cmd=%d (%d 字节)' % (c, len(b)))

s.close()
print('完成（购买返回 code=%s）' % code)
