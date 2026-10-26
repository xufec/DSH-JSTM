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
                if c==cmd: s.close(); return len(b2)
    except socket.timeout: pass
    s.close(); return None
for c,body,lb in ((10401,b'','10401 \u4f19\u4f34\u5217\u8868'),(10402,struct.pack('>I',1),'10402'),(10403,struct.pack('>I',1),'10403'),(10404,struct.pack('>I',1),'10404')):
    n=call(c,body); print("  %-18s -> %s" % (lb, ("%d \u5b57\u8282"%n) if n else "\u65e0\u5e94\u7b54"))
