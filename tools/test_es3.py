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
                    ml=struct.unpack_from('>H',b2,1)[0] if c==10554 else 0
                    s.close(); return (b2[0], b2[3:3+ml].decode('utf-8','ignore') if ml else '')
    except socket.timeout: pass
    s.close(); return (None,'')
def show():
    con=sqlite3.connect(r"server\state\roles.db")
    bag=[(a,b) for a,b in con.execute("SELECT item_id,bid FROM bag_items WHERE rid=1001 ORDER BY pos")]
    st =[(a,b) for a,b in con.execute("SELECT item_id,bid FROM store_items WHERE rid=1001 ORDER BY pos")]
    eq =[(s,a,b) for s,a,b in con.execute("SELECT slot,item_id,bid FROM equip_items WHERE rid=1001 ORDER BY slot")]
    con.close(); return bag,st,eq
bag,st,eq = show()
print("  初始: 装备=%s 仓库=%s" % ([x[2] for x in eq],[x[1] for x in st]))
if eq:
    slot,iid,bid = eq[0]
    code,msg = call(10554, bytes([2,4]) + struct.pack('>I', iid))
    bag,st,eq = show()
    print("  ② 装备(囊2)->仓库(囊4) code=%s  ⇒ 装备=%s 仓库=%s" % (code,[x[2] for x in eq],[x[1] for x in st]))
if st:
    iid2,bid2 = st[-1]
    code,msg = call(10554, bytes([4,2]) + struct.pack('>I', iid2))
    bag,st,eq = show()
    print("  ③ 仓库(囊4)->装备(囊2) code=%s  ⇒ 装备=%s 仓库=%s" % (code,[x[2] for x in eq],[x[1] for x in st]))
print()
print("  最终: 背包=%s" % [x[1] for x in bag])
print("        装备=%s" % [(x[0],x[2]) for x in eq])
print("        仓库=%s" % [x[1] for x in st])
