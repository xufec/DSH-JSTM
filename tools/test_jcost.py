import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('c')+b'\x00'*4)); time.sleep(0.2)
    s.sendall(frame(cmd, body))
    s.settimeout(8); buf=b''
    try:
        while True:
            d=s.recv(262144)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                c=struct.unpack_from('>H',buf,4)[0]; b2=buf[6:4+ln]; buf=buf[4+ln:]
                if c==cmd: s.close(); return b2
    except socket.timeout: pass
    s.close(); return None
def gold():
    con=sqlite3.connect(r"server\state\roles.db")
    v=con.execute("SELECT amount FROM role_assets WHERE rid=1001 AND name='gold'").fetchone()
    con.close(); return v[0] if v else 0
print("  抽取前 钻石(gold) =", gold())
b=call(11712, bytes([101, 2]))
if b:
    code=b[0]; t=b[1]; ml=struct.unpack_from('>H',b,2)[0]
    print("  SC_11712 code=%d type=%d msg=%r" % (code, t, b[4:4+ml].decode('utf-8','ignore')))
print("  抽取后 钻石(gold) =", gold(), " (抽了 2 次 × 100 = 应减 200)")
