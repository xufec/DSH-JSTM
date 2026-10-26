import socket, struct, time
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_u16(v): return struct.pack('>H', v & 0xffff)
s=socket.create_connection(('127.0.0.1',9000),timeout=8)
s.sendall(frame(10001, w_u16(11)+b'game_client'+b'\x00'*4)); time.sleep(0.3)
s.sendall(frame(12801))
s.settimeout(8); buf=b''
try:
    while True:
        d=s.recv(262144)
        if not d: break
        buf+=d
        while len(buf)>=6:
            ln=struct.unpack_from('>I',buf,0)[0]
            if len(buf)<4+ln: break
            cmd=struct.unpack_from('>H',buf,4)[0]; body=buf[6:4+ln]; buf=buf[4+ln:]
            if cmd==12801:
                g,=struct.unpack_from('>I',body,0); off=4
                n,=struct.unpack_from('>H',body,off); off+=2
                print("   guild_shop_lev=%d  xs_list=%d  (\u5171 %d \u5b57\u8282)" % (g,n,len(body)))
                for k in range(min(4,n)):
                    iid,ib,bind,pay=struct.unpack_from('>HIBB',body,off); off+=8
                    op,pr=struct.unpack_from('>II',body,off); off+=8
                    tp,ic=struct.unpack_from('>BB',body,off); off+=2
                    lt,cb=struct.unpack_from('>IH',body,off); off+=6
                    print("      id=%-6d item_bid=%-7d bind=%d pay_type=%-3d price=%-8d type=%d"
                          % (iid,ib,bind,pay,pr,tp))
                raise SystemExit
except socket.timeout:
    print("   (\u8d85\u65f6)")
