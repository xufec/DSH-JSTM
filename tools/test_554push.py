import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
con=sqlite3.connect(r"server\state\roles.db")
bag=list(con.execute("SELECT item_id,bid FROM bag_items WHERE rid=1001 ORDER BY pos")); con.close()
print("  移动前背包:", bag)
if not bag:
    print("  (背包空，跳过)"); raise SystemExit
iid,bid = bag[0]
s=socket.create_connection(('127.0.0.1',9000),timeout=8)
s.sendall(frame(10001, w_str('c')+b'\x00'*4)); time.sleep(0.25)
s.sendall(frame(10554, bytes([1,4]) + struct.pack('>I', iid) + b'----'))
s.settimeout(8); buf=b''; seen=[]
t0=time.time()
try:
    while time.time()-t0 < 4:
        d=s.recv(262144)
        if not d: break
        buf+=d
        while len(buf)>=6:
            ln=struct.unpack_from('>I',buf,0)[0]
            if len(buf)<4+ln: break
            c=struct.unpack_from('>H',buf,4)[0]; b2=buf[6:4+ln]; buf=buf[4+ln:]
            seen.append(c)
            if c==10554:
                print("  SC_10554 code=%d" % b2[0])
except socket.timeout: pass
s.close()
print("  收到的推送:", [x for x in seen if x in (10500,10501,10502,10503,10554)])
con=sqlite3.connect(r"server\state\roles.db")
print("  移动后背包:", list(con.execute("SELECT item_id,bid FROM bag_items WHERE rid=1001 ORDER BY pos")))
print("  移动后仓库:", list(con.execute("SELECT item_id,bid FROM store_items WHERE rid=1001 ORDER BY pos")))
con.close()
