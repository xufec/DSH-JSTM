import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('c')+b'\x00'*4)); time.sleep(0.2)
    s.sendall(frame(cmd, body))
    s.settimeout(8); buf=b''; got=[]
    try:
        while True:
            d=s.recv(262144)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                c=struct.unpack_from('>H',buf,4)[0]; b2=buf[6:4+ln]; buf=buf[4+ln:]
                got.append((c,b2))
                if c==cmd: s.close(); return got
    except socket.timeout: pass
    s.close(); return got
def bag():
    con=sqlite3.connect(r"server\state\roles.db")
    r=[tuple(x) for x in con.execute("SELECT bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")]; con.close(); return r
b=call(11710, bytes([101]))
for c,x in b:
    if c==11710: print("  SC_11710 type=%d get_times=%d" % (x[0], x[1]))
print("  抽取前背包:", bag())
b=call(11712, bytes([101, 3]))
for c,x in b:
    if c==11712:
        code=x[0]; t=x[1]; ml=struct.unpack_from('>H',x,2)[0]; off=4+ml
        n=struct.unpack_from('>H',x,off)[0]; off+=2
        items=[]
        for _ in range(n):
            bid=struct.unpack_from('>I',x,off)[0]; num=x[off+4]; off+=5
            items.append((bid,num))
        print("  SC_11712 code=%d type=%d Items=%s" % (code,t,items))
    if c==10500: print("    ← 收到 10500 背包推送")
print("  抽取后背包:", bag())
