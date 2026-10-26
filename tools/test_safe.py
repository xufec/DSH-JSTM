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
                if c==cmd:
                    ml=struct.unpack_from('>H',b2,1)[0]
                    s.close(); return (b2[0], b2[3:3+ml].decode('utf-8','ignore'))
    except socket.timeout: pass
    s.close(); return (None,'')
def counts():
    con=sqlite3.connect(r"server\state\roles.db")
    r=(con.execute("SELECT COUNT(*) FROM bag_items WHERE rid=1001").fetchone()[0],
       con.execute("SELECT COUNT(*) FROM equip_items WHERE rid=1001").fetchone()[0],
       con.execute("SELECT COUNT(*) FROM store_items WHERE rid=1001").fetchone()[0])
    con.close(); return r
def show():
    con=sqlite3.connect(r"server\state\roles.db")
    r=(list(con.execute("SELECT bid FROM bag_items WHERE rid=1001 ORDER BY pos")),
       list(con.execute("SELECT bid FROM equip_items WHERE rid=1001 ORDER BY slot")),
       list(con.execute("SELECT bid FROM store_items WHERE rid=1001 ORDER BY pos")))
    con.close(); return r
before = counts()
con=sqlite3.connect(r"server\state\roles.db")
eq=list(con.execute("SELECT item_id,bid FROM equip_items WHERE rid=1001 ORDER BY slot")); con.close()
print("  ① 装备(囊2) -> 仓库(囊4)：item_id=%d" % eq[0][0])
code,msg = call(10554, bytes([2,4]) + struct.pack('>I', eq[0][0]))
print("     code=%s msg=%r %s" % (code, msg, "✅ 已拦截，未动数据" if code==0 else "❌"))
after = counts()
print("     条数 before=%s after=%s  %s" % (before, after, "✅ 无丢失" if before==after else "❌ 有变化!"))
print()
print("  ② 背包(囊1) <-> 仓库(囊4) 应仍可用")
con=sqlite3.connect(r"server\state\roles.db")
bag=list(con.execute("SELECT item_id,bid FROM bag_items WHERE rid=1001 ORDER BY pos")); con.close()
code,msg = call(10554, bytes([1,4]) + struct.pack('>I', bag[0][0]))
print("     背包->仓库 code=%s" % code)
b,e,s = show()
print("     背包=%s 装备=%s 仓库=%s" % ([x[0] for x in b],[x[0] for x in e],[x[0] for x in s]))
# \u8fd8\u539f
con=sqlite3.connect(r"server\state\roles.db")
st=list(con.execute("SELECT item_id,bid,quantity FROM store_items WHERE rid=1001"))
for iid,bid,q in st:
    nxt=con.execute("SELECT COALESCE(MAX(item_id),0)+1 FROM bag_items WHERE rid=1001 AND bag_code=1").fetchone()[0]
    pos=con.execute("SELECT COALESCE(MAX(pos),0)+1 FROM bag_items WHERE rid=1001 AND bag_code=1").fetchone()[0]
    con.execute("INSERT INTO bag_items (rid,bag_code,item_id,bid,pos,quantity,ctime) VALUES (1001,1,?,?,?,?,0)",(nxt,bid,pos,q))
con.execute("DELETE FROM store_items WHERE rid=1001"); con.commit(); con.close()
