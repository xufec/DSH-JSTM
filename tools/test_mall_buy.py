import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_u16(v): return struct.pack('>H', v & 0xffff)
def aset(rid=1001):
    con=sqlite3.connect(r"server\state\roles.db")
    d={r[0]:r[1] for r in con.execute("SELECT name,amount FROM role_assets WHERE rid=?",(rid,))}
    con.close(); return d
print("   \u4e70\u524d coin=%s coupon=%s" % (aset().get('coin'), aset().get('coupon')))
s=socket.create_connection(('127.0.0.1',9000),timeout=8)
s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.3)
s.sendall(frame(12805, w_u16(25890)+w_u16(1)))
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
                code=body[0]; l=struct.unpack_from('>H',body,1)[0]
                off=3+l; iid,num,price=struct.unpack_from('>HHI',body,off)
                print("   code=%d msg=%r id=%d num=%d price=%d" % (code, body[3:3+l].decode('utf-8','ignore'), iid,num,price))
                raise SystemExit
except socket.timeout:
    print("   (\u8d85\u65f6)")
