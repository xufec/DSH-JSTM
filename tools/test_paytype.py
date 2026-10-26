import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_u16(v): return struct.pack('>H', v & 0xffff)
def aset():
    con=sqlite3.connect(r"server\state\roles.db")
    d={r[0]:r[1] for r in con.execute("SELECT name,amount FROM role_assets WHERE rid=1001")}
    con.close(); return d
def buy(bid, num=1):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.25)
    s.sendall(frame(12805, w_u16(bid)+w_u16(num)))
    s.settimeout(8); buf=b''
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
                    s.close(); return body[0]
    except socket.timeout: pass
    s.close(); return None
print("  买前:", {k: aset().get(k) for k in ('gold','coin','coupon')})
print("  买 id=2001(item 25890, pay_type=1, price=99): code=%s" % buy(25890,1))
print("  买后:", {k: aset().get(k) for k in ('gold','coin','coupon')})
print("  买 id=2002(item 25301, pay_type=1, price=250): code=%s" % buy(25301,1))
print("  买后:", {k: aset().get(k) for k in ('gold','coin','coupon')})
