import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_u16(v): return struct.pack('>H', v & 0xffff)
def aset():
    con=sqlite3.connect(r"server\state\roles.db")
    d={r[0]:r[1] for r in con.execute("SELECT name,amount FROM role_assets WHERE rid=1001")}
    con.close(); return d
def bag():
    con=sqlite3.connect(r"server\state\roles.db")
    r=list(con.execute("SELECT bid,quantity FROM bag_items WHERE rid=1001")); con.close(); return r
def buy(key, num=1):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.25)
    s.sendall(frame(12805, w_u16(key)+w_u16(num)))
    s.settimeout(8); buf=b''
    try:
        while True:
            d=s.recv(65536)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                cmd=struct.unpack_from('>H',buf,4)[0]; body=buf[6:4+ln]; buf=buf[4+ln:]
                if cmd==12805:
                    code=body[0]; l=struct.unpack_from('>H',body,1)[0]
                    s.close()
                    return code, body[3:3+l].decode('utf-8','ignore')
    except socket.timeout: pass
    s.close(); return None,'timeout'
print("  买前 gold=%s bag=%s" % (aset().get('gold'), bag()))
c,m = buy(2001, 1);   print("  ① 按商品 id=2001  : code=%s msg=%r" % (c,m))
print("     买后 gold=%s bag=%s" % (aset().get('gold'), bag()))
c,m = buy(25890, 1);  print("  ② 按 item_bid=25890: code=%s msg=%r" % (c,m))
print("     买后 gold=%s bag=%s" % (aset().get('gold'), bag()))
c,m = buy(9999, 1);   print("  ③ 不存在的 id=9999 : code=%s msg=%r  (应 code=0 + 非空 msg)" % (c,m))
