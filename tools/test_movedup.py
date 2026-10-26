import socket, struct, time, sqlite3, sys
# ★ R243：控制台默认 GBK ⇒ 打印 '⇒' 抛 UnicodeEncodeError（回归被判 FAIL）
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
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
                if c==cmd: s.close(); return b2
    except socket.timeout: pass
    s.close(); return None
def show():
    con=sqlite3.connect(r"server\state\roles.db")
    b=[tuple(x) for x in con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")]
    st=[tuple(x) for x in con.execute("SELECT item_id,bid,quantity FROM store_items WHERE rid=1001 ORDER BY pos")]
    con.close(); return b,st
b,st = show()
print("  移动前 背包:", b)
print("        仓库:", st)
if b:
    iid,bid,q = b[0]
    print("  --- 移动 item_id=%d bid=%d 到仓库 ---" % (iid,bid))
    r = call(10554, bytes([1,4]) + struct.pack('>I', iid))
    if r: print("     SC_10554 code=%d" % r[0])
    b2,st2 = show()
    print("  移动后 背包:", b2)
    print("        仓库:", st2)
    print()
    print("  ⇒ 仓库原有条目是否还在:", "是 ✅" if all(x[0] in [y[0] for y in st2] for x in st) else "否 ❌")
    moved = [y for y in st2 if y[1]==bid]
    print("  ⇒ 移入的条目 item_id =", [y[0] for y in moved], "（原 id=%d）" % iid)
