import socket, struct, time, sqlite3, sys
sys.path.insert(0, r"server")
import mock_server as m
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('game_client')+b'\x00'*4)); time.sleep(0.2)
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
def show():
    con=sqlite3.connect(r"server\state\roles.db")
    b=list(con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos"))
    st=list(con.execute("SELECT item_id,bid,quantity FROM store_items WHERE rid=1001 ORDER BY pos"))
    con.close(); return b, st
b,st = show()
print("  移动前  背包:", b)
print("          仓库:", st)
if b:
    iid, bid, q = b[0]
    r = call(10554, bytes([1,4]) + struct.pack('>I', iid))
    if r:
        code=r[0]; ml=struct.unpack_from('>H',r,1)[0]
        print("  SC_10554 code=%d msg=%r from=%d to=%d" % (code, r[3:3+ml].decode('utf-8','ignore'), r[3+ml], r[4+ml]))
b,st = show()
print("  移动后  背包:", b)
print("          仓库:", st)
print()
print("=== 验证 10512（卸下装备）与 12421（已完成任务）===")
con=sqlite3.connect(r"server\state\roles.db")
eq=list(con.execute("SELECT slot,item_id,bid FROM equip_items WHERE rid=1001")); con.close()
if eq:
    slot, iid, bid = eq[0]
    r = call(10512, struct.pack('>IIBI', iid, bid, 1, 0))
    if r: print("  SC_10512 code=%d" % r[0])
con=sqlite3.connect(r"server\state\roles.db")
print("  卸下后装备栏:", list(con.execute("SELECT slot,bid FROM equip_items WHERE rid=1001"))); con.close()
r = call(12421)
if r: print("  SC_12421 finish_task_list=%d" % struct.unpack_from('>H',r,0)[0])
