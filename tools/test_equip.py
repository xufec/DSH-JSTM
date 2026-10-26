import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def bag():
    con=sqlite3.connect(r"server\state\roles.db")
    r=list(con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")); con.close(); return r
def eq():
    con=sqlite3.connect(r"server\state\roles.db")
    try: r=list(con.execute("SELECT slot,item_id,bid,hero_bid FROM equip_items WHERE rid=1001 ORDER BY slot"))
    except Exception: r=[]
    con.close(); return r
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('game_client')+b'\x00'*4)); time.sleep(0.25)
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

print("  穿戴前 bag:", bag())
print("  穿戴前 eq :", eq())
iid = bag()[0][0]; bid = bag()[0][1]
b = call(10511, struct.pack('>III', iid, 0, 0))
if b:
    code=b[0]; ml=struct.unpack_from('>H',b,1)[0]; off=3+ml
    ia, ie, np_, hb = struct.unpack_from('>IIBI', b, off)
    print("  SC_10511: code=%d is_auto=%d bag_item_id=%d eqm_item_id=%d eqm_new_pos=%d hero=%d"
          % (code, b[off-1], ia, ie, np_, hb))
print("  穿戴后 bag:", bag())
print("  穿戴后 eq :", eq())
print()
print("  --- 换装：穿另一件，应把旧的换回背包 ---")
iid2 = bag()[0][0] if bag() else 0
if iid2:
    b2 = call(10511, struct.pack('>III', iid2, iid, 0))
    print("  换装后 bag:", bag())
    print("  换装后 eq :", eq())
else:
    print("  (背包空了，跳过)")
