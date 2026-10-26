import socket, struct, time
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
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
b=call(10552, bytes([1,10,0]))
print("  10552 扩容(volume=10):", "code=%d bag_code=%d old=%d new=%d" % (b[0], b[2], struct.unpack_from('>H',b,3)[0], struct.unpack_from('>H',b,5)[0]) if b else None)
b=call(10534, struct.pack('>I',33001));  print("  10534:", "val=%d" % b[0] if b else None)
b=call(10551, struct.pack('>I',33001));  print("  10551:", "val=%d" % struct.unpack_from('>I',b,0)[0] if b else None)
b=call(10528, bytes([1,0])); print("  10528:", "code=%d lev=%d state_list=%d" % (b[0], b[3], struct.unpack_from('>H',b,4)[0]) if b else None)
print("  10570 批量删除 item_id=6:")
b=call(10570, bytes([1]) + struct.pack('>H',1) + struct.pack('>I',6))
print("        ", "bag_code=%d code=%d" % (b[0], b[1]) if b else None)
import sqlite3
con=sqlite3.connect(r"server\state\roles.db")
print("  删除后背包:", list(con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")))
con.close()
