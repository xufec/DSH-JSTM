import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def bag():
    con=sqlite3.connect(r"server\state\roles.db")
    r=list(con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")); con.close(); return r
def use(item_id, bid, num=1):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('game_client')+b'\x00'*4)); time.sleep(0.25)
    body = struct.pack('>B', 0) + struct.pack('>I', item_id) + struct.pack('>H', num) + struct.pack('>I', 0) + struct.pack('>I', bid)
    s.sendall(frame(10505, body))
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
                if c in (10505,10501,10503):
                    got.append((c,b2))
                    if c==10505: 
                        s.close(); return got
    except socket.timeout: pass
    s.close(); return got
print("  使用前:", bag())
got = use(1, 33001, 1)
for c,b2 in got:
    if c==10505:
        code=b2[0]; l=struct.unpack_from('>H',b2,1)[0]
        ib=struct.unpack_from('>I',b2,3+l)[0]
        print("  SC_10505: code=%d msg=%r item_bid=%d" % (code, b2[3:3+l].decode('utf-8','ignore'), ib))
    elif c==10501:
        print("  SC_10501 数量更新: code=%d n=%d item_id=%d new_qty=%d"
              % (b2[0], struct.unpack_from('>H',b2,1)[0],
                 struct.unpack_from('>I',b2,3)[0], struct.unpack_from('>H',b2,7)[0]))
    elif c==10503:
        print("  SC_10503 删除: code=%d n=%d item_id=%d"
              % (b2[0], struct.unpack_from('>H',b2,1)[0], struct.unpack_from('>I',b2,3)[0]))
print("  使用后:", bag())
print()
print("  --- 用完即删的场景（bid=40001 数量 1）---")
got = use(7, 40001, 1)
for c,b2 in got:
    if c==10505:
        code=b2[0]; l=struct.unpack_from('>H',b2,1)[0]
        print("  SC_10505: code=%d msg=%r" % (code, b2[3:3+l].decode('utf-8','ignore')))
    elif c==10503:
        print("  SC_10503 删除: item_id=%d" % struct.unpack_from('>I',b2,3)[0])
print("  使用后:", bag())
