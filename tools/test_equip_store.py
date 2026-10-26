import socket, struct, time, sqlite3, sys
sys.path.insert(0, r"server")
import mock_server as m
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('c')+b'\x00'*4)); time.sleep(0.2)
    s.sendall(frame(cmd, body))
    s.settimeout(8); buf=b''; seen=[]
    try:
        while True:
            d=s.recv(262144)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                c=struct.unpack_from('>H',buf,4)[0]; b2=buf[6:4+ln]; buf=buf[4+ln:]
                seen.append((c,b2))
                if c==cmd: s.close(); return seen
    except socket.timeout: pass
    s.close(); return seen
def show():
    con=sqlite3.connect(r"server\state\roles.db")
    bag=list(con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos"))
    st =list(con.execute("SELECT item_id,bid,quantity FROM store_items WHERE rid=1001 ORDER BY pos"))
    eq =list(con.execute("SELECT slot,item_id,bid FROM equip_items WHERE rid=1001 ORDER BY slot"))
    con.close(); return bag,st,eq
bag,st,eq = show()
print("  初始 背包:", bag)
print("       装备:", eq)
print("       仓库:", st)
if not eq:
    print("  (装备栏空，先把背包里一件装备穿上)")
    for iid,bid,q in bag:
        if m.item_type_of(bid) in (100,103,104,105,106,107):
            call(10511, struct.pack('>III', iid, 0, 0)); break
    bag,st,eq = show()
    print("  穿上后装备:", eq)
if eq:
    slot, iid, bid = eq[0]
    print("  --- 装备(囊2) → 仓库(囊4)：item_id=%d bid=%d ---" % (iid,bid))
    r = call(10554, bytes([2,4]) + struct.pack('>I', iid))
    for c,b2 in r:
        if c==10554: print("     SC_10554 code=%d" % b2[0])
        if c in (10500,10503): print("     推送 %d" % c)
    bag,st,eq = show()
    print("     装备栏:", eq)
    print("     仓库  :", st)
    if st:
        iid2 = st[0][0]
        print("  --- 仓库(囊4) → 装备(囊2)：item_id=%d ---" % iid2)
        r = call(10554, bytes([4,2]) + struct.pack('>I', iid2))
        for c,b2 in r:
            if c==10554: print("     SC_10554 code=%d" % b2[0])
        bag,st,eq = show()
        print("     装备栏:", eq)
        print("     仓库  :", st)
