import socket, struct, time, sqlite3
def w_u16(v): return struct.pack('>H', v & 0xffff)
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def aset(rid=1001):
    con=sqlite3.connect(r"server\state\roles.db")
    d={r[0]:r[1] for r in con.execute("SELECT name,amount FROM role_assets WHERE rid=?", (rid,))}
    con.close(); return d
def buy(bid, num=1):
    s=socket.create_connection(('127.0.0.1',9000),timeout=6)
    s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.25)
    s.sendall(frame(12805, w_u16(bid)+w_u16(num)))
    s.settimeout(6); buf=b''
    try:
        while True:
            d=s.recv(65536)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                cmd=struct.unpack_from('>H',buf,4)[0]; body=buf[6:4+ln]; buf=buf[4+ln:]
                if cmd==12805:
                    s.close()
                    l=struct.unpack_from('>H',body,1)[0]
                    return body[0], body[3:3+l].decode('utf-8','ignore')
    except socket.timeout: pass
    s.close(); return None, 'timeout'

print("  购买前:", {k: aset().get(k) for k in ('coin','coupon')})
c,m = buy(33001, 1); print("  买 33001(pay_type=1): code=%d msg=%r" % (c,m))
print("  购买后:", {k: aset().get(k) for k in ('coin','coupon')})
c,m = buy(33002, 1); print("  买 33002(pay_type=2): code=%d msg=%r" % (c,m))
print("  购买后:", {k: aset().get(k) for k in ('coin','coupon')})
