import socket, struct, time
def w_u16(v): return struct.pack('>H', v & 0xffff)
def w_u32(v): return struct.pack('>I', v & 0xffffffff)
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body

def read_frames(s, want, timeout=5):
    s.settimeout(timeout); buf=b''; out=[]
    try:
        while True:
            d=s.recv(65536)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                cmd=struct.unpack_from('>H',buf,4)[0]; body=buf[6:4+ln]
                out.append((cmd, body)); buf=buf[4+ln:]
                if cmd in want: return out
    except socket.timeout: pass
    return out

s=socket.create_connection(('127.0.0.1',9000),timeout=6)
s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.3)

for cmd, hdr in ((12801, True), (12802, True), (12803, False)):
    s.sendall(frame(cmd))
    for c, body in read_frames(s, {cmd}):
        if c != cmd: continue
        off = 0
        if cmd == 12801:
            g, = struct.unpack_from('>I', body, 0); off = 4
            print("SC_12801 guild_shop_lev=%d" % g)
        elif cmd == 12802:
            cid, = struct.unpack_from('>H', body, 0); off = 2
            print("SC_12802 id=%d" % cid)
        n, = struct.unpack_from('>H', body, off); off += 2
        print("   n=%d" % n)
        for _ in range(n):
            if cmd == 12803:
                ib, pr = struct.unpack_from('>II', body, off); off += 8
                print("      item_bid=%d price=%d" % (ib, pr))
            else:
                iid, ib, bind, pay = struct.unpack_from('>HIBB', body, off); off += 8
                op, pr = struct.unpack_from('>II', body, off); off += 8
                tp, ic = struct.unpack_from('>BB', body, off); off += 2
                lt, cb = struct.unpack_from('>IH', body, off); off += 6
                print("      id=%d item_bid=%d bind=%d **pay_type=%d** price=%d cbn=%d"
                      % (iid, ib, bind, pay, pr, cb))
        break
s.close()
