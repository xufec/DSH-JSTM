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
def p10511(b):
    code=b[0]; ml=struct.unpack_from('>H',b,1)[0]; msg=b[3:3+ml].decode('utf-8','ignore')
    off=3+ml; is_auto=b[off]; off+=1
    ia,ie=struct.unpack_from('>II',b,off); off+=8
    pos=b[off]
    return code,msg,ia,ie,pos
con=sqlite3.connect(r"server\state\roles.db")
bag=[tuple(x) for x in con.execute("SELECT item_id,bid FROM bag_items WHERE rid=1001 ORDER BY pos")]
con.close()
gift=[(i,b) for i,b in bag if m.item_type_of(b)==6]
print("① 穿礼包（type=6，应被拒绝）")
if gift:
    i,b = gift[0]
    code,msg,ia,ie,pos = p10511(call(10511, struct.pack('>III', i,0,0)))
    print("   bid=%d -> code=%d  msg=%r  ⇒ %s" % (b, code, msg, "✅ 拒绝" if code==0 else "❌ 未拒绝"))
else:
    print("   (背包里没有礼包)")
print()
print("② 按部位穿装备（每个部位应落到各自的固定槽）")
for i,b in bag:
    t = m.item_type_of(b)
    if t in (100,103,104,105,106,107,108,109,110):
        code,msg,ia,ie,pos = p10511(call(10511, struct.pack('>III', i,0,0)))
        print("   bid=%-7s type=%-5s -> code=%d eqm_new_pos=%-3d %s" % (b, t, code, pos, m.item_name(b)))
con=sqlite3.connect(r"server\state\roles.db")
print()
print("  最终装备栏:", [tuple(x) for x in con.execute("SELECT slot,bid FROM equip_items WHERE rid=1001 ORDER BY slot")])
con.close()
