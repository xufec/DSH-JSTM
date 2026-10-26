import socket, struct, time, sys
# ★ R243：控制台默认 GBK ⇒ 打印 '⇒' 抛 UnicodeEncodeError（回归被判 FAIL）
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_u16(v): return struct.pack('>H', v & 0xffff)
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b

s=socket.create_connection(('127.0.0.1',9000),timeout=8)
s.sendall(frame(10001, w_str('game_client')+b'\x00'*4)); time.sleep(0.3)
print("  → 发送 CS_12805 id=2004 num=1")
s.sendall(frame(12805, w_u16(2004)+w_u16(1)))
s.settimeout(8); buf=b''; got={}
try:
    while len(got) < 2:
        d=s.recv(262144)
        if not d: break
        buf += d
        while len(buf) >= 6:
            ln = struct.unpack_from('>I', buf, 0)[0]
            if len(buf) < 4+ln: break
            cmd = struct.unpack_from('>H', buf, 4)[0]
            body = buf[6:4+ln]; buf = buf[4+ln:]
            if cmd == 12805:
                code = body[0]; l = struct.unpack_from('>H', body, 1)[0]
                iid, n, pr = struct.unpack_from('>HHI', body, 3+l)
                print("  收到 SC_12805: code=%d msg=%r id=%d num=%d price=%d" % (code, body[3:3+l].decode('utf-8','ignore'), iid, n, pr))
                got['12805']=1
            elif cmd == 10500:
                bc = body[0]; cnt = struct.unpack_from('>H', body, 1)[0]
                print("  收到 SC_10500 ★ 背包推送: bag_code=%d items=%d  (%d 字节)" % (bc, cnt, len(body)))
                got['10500']=1
except socket.timeout:
    pass
s.close()
print("  ⇒ 结果:", "✅ 购买后有 10500 背包推送" if got.get('10500') else "❌ 未收到 10500")
