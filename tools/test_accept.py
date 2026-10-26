import socket, struct, time
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_u16(v): return struct.pack('>H', v & 0xffff)
def call(cmd):
    s=socket.create_connection(('127.0.0.1',9000),timeout=8)
    s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.25)
    s.sendall(frame(cmd))
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
                    s.close(); return b2
    except socket.timeout: pass
    s.close(); return None
def bids(body):
    n=struct.unpack_from('>H',body,0)[0]; off=2; out=[]
    for _ in range(n):
        b,=struct.unpack_from('>I',body,off)
        st=body[off+4]
        out.append((b,st)); off+=34
    return out
b=call(12400); print("  SC_12400 (\u8fdb\u884c\u4e2d):  ", bids(b) if b else None)
b=call(12409); print("  SC_12409 (\u53ef\u63a5\u53d6):  ", bids(b) if b else None)
b=call(12407); print("  SC_12407 (add):     ", bids(b) if b else None)
b=call(12408); print("  SC_12408 (delete):  n=%d" % struct.unpack_from('>H',b,0)[0] if b else None)
