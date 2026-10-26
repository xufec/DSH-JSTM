import socket, struct, time
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def call(cmd, body=b''):
    s=socket.create_connection(('127.0.0.1',9000),timeout=6)
    s.sendall(frame(10001, w_str('c')+b'\x00'*4)); time.sleep(0.2)
    s.sendall(frame(cmd, body))
    s.settimeout(6); buf=b''
    try:
        while True:
            d=s.recv(65536)
            if not d: break
            buf+=d
            while len(buf)>=6:
                ln=struct.unpack_from('>I',buf,0)[0]
                if len(buf)<4+ln: break
                c=struct.unpack_from('>H',buf,4)[0]; b2=buf[6:4+ln]; buf=buf[4+ln:]
                if c==cmd: s.close(); return b2
    except socket.timeout: pass
    s.close(); return None
b=call(11200)
if b: print("  SC_11200 volume=%d volume_open=%d partner_bag=%d (%d 字节)" % (b[0], b[1], struct.unpack_from('>H',b,2)[0], len(b)))
b=call(10552, bytes([1,0,0]))
if b:
    ml=struct.unpack_from('>H',b,1)[0]; off=3+ml
    print("  SC_10552 bag_code=%d old=%d new=%d" % (b[off], struct.unpack_from('>H',b,off+1)[0], struct.unpack_from('>H',b,off+3)[0]))
b=call(10552, bytes([4,0,0]))
if b:
    ml=struct.unpack_from('>H',b,1)[0]; off=3+ml
    print("  SC_10552(仓库) bag_code=%d old=%d new=%d" % (b[off], struct.unpack_from('>H',b,off+1)[0], struct.unpack_from('>H',b,off+3)[0]))
