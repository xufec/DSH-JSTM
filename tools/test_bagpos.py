import socket, struct, time, sqlite3
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_u16(v): return struct.pack('>H', v & 0xffff)
def bag():
    con=sqlite3.connect(r"server\state\roles.db"); con.row_factory=sqlite3.Row
    r=[dict(x) for x in con.execute("SELECT item_id,bid,pos,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")]
    con.close(); return r
def call(cmd, body=b'', want=None):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.25)
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
                if c==(want or cmd):
                    s.close(); return c,b2
    except socket.timeout: pass
    s.close(); return None,None
print("  买前:", [(x['bid'],x['pos']) for x in bag()])
call(12805, w_u16(2003)+w_u16(1))     # 买 id=2003(item 36500)
print("  买后:", [(x['bid'],x['pos']) for x in bag()])
c,b = call(10502, bytes([1]))
if b:
    n=struct.unpack_from('>H',b,1)[0]
    print("  SC_10502 bag_code=%d items=%d   (0基 pos 应为 0..%d)" % (b[0], n, n-1))
