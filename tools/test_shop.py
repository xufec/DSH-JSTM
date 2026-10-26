import socket, struct, time, sys, json, sqlite3

HOST, PORT = '127.0.0.1', 9000

def w_str(s):
    b = s.encode('utf-8') if isinstance(s, str) else s
    return struct.pack('>H', len(b)) + b
def w_u8(v):  return struct.pack('>B', v & 0xff)
def w_u16(v): return struct.pack('>H', v & 0xffff)
def w_u32(v): return struct.pack('>I', v & 0xffffffff)

def frame(cmd, body=b''):
    return struct.pack('>I', 2 + len(body)) + struct.pack('>H', cmd) + body

def recv_frames(s, want, timeout=6):
    s.settimeout(timeout)
    buf = b''
    out = []
    try:
        while True:
            d = s.recv(65536)
            if not d: break
            buf += d
            while len(buf) >= 6:
                ln = struct.unpack_from('>I', buf, 0)[0]
                if len(buf) < 4 + ln: break
                cmd = struct.unpack_from('>H', buf, 4)[0]
                body = buf[6:4+ln]
                out.append((cmd, body))
                buf = buf[4+ln:]
                if cmd in want: return out
    except socket.timeout:
        pass
    return out

def assets(rid=1001):
    con = sqlite3.connect(r"server\state\roles.db")
    names = {r[0]: r[1] for r in con.execute("SELECT name, amount FROM role_assets WHERE rid=?", (rid,))}
    con.close()
    return names

print("== 购买前 ==")
print("   coupon =", assets().get('coupon'))

s = socket.create_connection((HOST, PORT), timeout=6)
s.sendall(frame(10001, w_str('game_client') + b'\x00\x00\x00\x00'))
time.sleep(0.3)

# 12803 商品列表
s.sendall(frame(12803))
for cmd, body in recv_frames(s, {12803}):
    if cmd == 12803:
        n = struct.unpack_from('>H', body, 0)[0]
        items = []
        off = 2
        for _ in range(n):
            ib, pr = struct.unpack_from('>II', body, off); off += 8
            items.append({'item_bid': ib, 'price': pr})
        print("== SC_12803 商品列表 ==")
        print("   n =", n, items)
        break

# 12805 购买 item_bid=33001 x1
s.sendall(frame(12805, w_u16(33001) + w_u16(1)))
got = recv_frames(s, {12805})
for cmd, body in got:
    if cmd == 12805:
        code = body[0]
        ln = struct.unpack_from('>H', body, 1)[0]
        msg = body[3:3+ln].decode('utf-8', 'ignore')
        off = 3 + ln
        iid, num, price = struct.unpack_from('>HHI', body, off)
        print("== SC_12805 购买应答 ==")
        print("   code=%d msg=%r id=%d num=%d price=%d" % (code, msg, iid, num, price))
        break
s.close()

print("== 购买后 ==")
print("   coupon =", assets().get('coupon'))

con = sqlite3.connect(r"server\state\roles.db")
rows = list(con.execute("SELECT bid, quantity FROM bag_items WHERE rid=1001"))
con.close()
print("== 背包 ==")
print("   ", rows)
