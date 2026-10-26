import socket, struct, time, sqlite3, sys
sys.path.insert(0, r"server")
import mock_server as m
# \u627e\u4e00\u4e2a\u5728 gift \u8868\u91cc\u3001\u4e14\u80fd\u5165\u5305\u7684\u793c\u5305
d=m.gift_contents
cands=[]
for gb, lst in (m._GIFT_CFG or {}).items():
    if lst and all(m.is_valid_item(b) for b,_ in lst[:2]):
        cands.append((int(gb), lst[:3]))
        if len(cands)>=3: break
print("  候选礼包:", cands)
if not cands:
    print("  (无可验证礼包)"); raise SystemExit
gb, lst = cands[0]
con=sqlite3.connect(r"server\state\roles.db")
con.execute("INSERT INTO bag_items (rid,bag_code,item_id,bid,pos,quantity,ctime) VALUES (1001,1,(SELECT COALESCE(MAX(item_id),0)+1 FROM bag_items WHERE rid=1001 AND bag_code=1),?,(SELECT COALESCE(MAX(pos),0)+1 FROM bag_items WHERE rid=1001 AND bag_code=1),1,0)", (gb,))
con.commit()
iid=con.execute("SELECT item_id FROM bag_items WHERE rid=1001 AND bid=? ORDER BY item_id DESC LIMIT 1",(gb,)).fetchone()[0]
before=[tuple(x) for x in con.execute("SELECT bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")]
con.close()
print("  使用礼包 bid=%d (item_id=%d)，其内容=%s" % (gb, iid, lst))
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
s=socket.create_connection(('127.0.0.1',9000),timeout=8)
s.sendall(frame(10001, w_str('c')+b'\x00'*4)); time.sleep(0.25)
s.sendall(frame(10505, struct.pack('>B',0)+struct.pack('>I',iid)+struct.pack('>H',1)+struct.pack('>I',0)+struct.pack('>I',gb)))
s.settimeout(8); buf=b''; seen=[]
try:
    while True:
        x=s.recv(262144)
        if not x: break
        buf+=x
        while len(buf)>=6:
            ln=struct.unpack_from('>I',buf,0)[0]
            if len(buf)<4+ln: break
            c=struct.unpack_from('>H',buf,4)[0]; b2=buf[6:4+ln]; buf=buf[4+ln:]
            seen.append(c)
            if c==10505: raise SystemExit
except socket.timeout: pass
