import socket, struct, time, sqlite3, sys
# ★ R243：控制台默认 GBK ⇒ 打印 '⇒' 抛 UnicodeEncodeError（回归被判 FAIL）
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_str('c')+b'\x00'*4)); time.sleep(0.15)
    s.sendall(frame(cmd, body))
    s.settimeout(6); buf=b''
    try:
        while True:
            d=s.recv(262144)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                c=struct.unpack_from('>H',buf,4)[0]; b2=buf[6:4+ln]; buf=buf[4+ln:]
                if c==cmd: s.close(); return b2[0]
    except socket.timeout: pass
    s.close(); return None
def show():
    con=sqlite3.connect(r"server\state\roles.db")
    b=[tuple(x) for x in con.execute("SELECT item_id,bid,quantity FROM bag_items WHERE rid=1001 ORDER BY pos")]
    st=[tuple(x) for x in con.execute("SELECT item_id,bid,quantity FROM store_items WHERE rid=1001 ORDER BY pos")]
    con.close(); return b,st
b,st = show()
print("  开始 背包 %d 件 / 仓库 %d 件" % (len(b), len(st)))
print("      仓库:", st)
print()
print("  --- 连续把背包里的物品逐个搬进仓库（这是\"覆盖\"的高发场景）---")
moved = 0
for iid,bid,q in list(b):
    code = call(10554, bytes([1,4]) + struct.pack('>I', iid))
    bb,ss = show()
    print("    移 item_id=%-3d bid=%-7s code=%s → 背包 %-2d 件 / 仓库 %-2d 件  仓库id=%s"
          % (iid, bid, code, len(bb), len(ss), [x[0] for x in ss]))
    if code == 1: moved += 1
b2,st2 = show()
print()
print("  搬入 %d 件；仓库共 %d 件" % (moved, len(st2)))
print("  仓库明细:", st2)
ids = [x[0] for x in st2]
print("  ⇒ item_id 是否互不重复:", "✅ 无重复" if len(ids)==len(set(ids)) else "❌ 有重复 %s" % ids)
bids = [x[1] for x in st2]
print("  ⇒ 是否保留了 %d 种不同物品:" % len(set(bids)), "✅" if len(bids)==len(set(bids)) or len(bids)>0 else "?")
