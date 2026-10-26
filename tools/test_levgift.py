import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('game_client')+b'\x00'*4)); time.sleep(0.2)
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
    r=[tuple(x) for x in con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")]; con.close(); return r

g = call(14600)
for c,b in g:
    if c==14600:
        days=struct.unpack_from('>H',b,0)[0]; n=struct.unpack_from('>H',b,2)[0]
        types=[b[4+i] for i in range(n)]
        print("  SC_14600 days=%d get_day(可领)=%s" % (days, types))
print("  领取前背包:", bag())
print()
print("  领取 序号=1（10级礼包 30010）…")
g = call(14601, bytes([1]))
for c,b in g:
    if c==10500: print("    ← 收到 10500 背包推送")
    if c==14601:
        tips=struct.unpack_from('>H',b,0)[0]; ml=struct.unpack_from('>H',b,2)[0]
        print("    SC_14601 tips=%d msg=%r days=%d" % (tips, b[4:4+ml].decode('utf-8','ignore'), b[4+ml]))
print("  领取后背包:", bag())
print()
print("  重复领取（应拒绝）…")
g = call(14601, bytes([1]))
for c,b in g:
    if c==14601:
        tips=struct.unpack_from('>H',b,0)[0]; ml=struct.unpack_from('>H',b,2)[0]
        print("    SC_14601 tips=%d msg=%r" % (tips, b[4:4+ml].decode('utf-8','ignore')))
