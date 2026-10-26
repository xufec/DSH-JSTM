import socket, struct, time, threading, statistics
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b
def worker(results, idx, n=10):
    ok=0; times=[]
    for _ in range(n):
        try:
            t0=time.perf_counter()
            s=socket.create_connection(('127.0.0.1',9000),timeout=8)
            s.sendall(frame(10001, w_str('game_client')+b'\x00'*4))
            s.sendall(frame(12400))
            s.settimeout(8); buf=b''; got=False
            while True:
                d=s.recv(65536)
                if not d: break
                buf+=d
                while len(buf)>=6:
                    ln=struct.unpack_from('>I',buf,0)[0]
                    if len(buf)<4+ln: break
                    c=struct.unpack_from('>H',buf,4)[0]; buf=buf[4+ln:]
                    if c==12400: got=True; break
                if got: break
            t1=time.perf_counter(); s.close()
            if got: ok+=1; times.append((t1-t0)*1000)
        except Exception: pass
    results[idx]=(ok, times)
res=[None]*20
ths=[threading.Thread(target=worker,args=(res,i)) for i in range(20)]
t0=time.perf_counter()
for t in ths: t.start()
for t in ths: t.join()
t1=time.perf_counter()
allt=[x for r in res if r for x in r[1]]
ok=sum(r[0] for r in res if r)
print("  20 线程 × 10 请求 = 200 次；成功 %d 次；总耗时 %.2f s" % (ok, t1-t0))
if allt:
    print("  单次延迟: 中位 %.1f ms  最大 %.1f ms" % (statistics.median(allt), max(allt)))
