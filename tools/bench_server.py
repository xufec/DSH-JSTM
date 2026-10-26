import socket, struct, time, statistics

HOST, PORT = '127.0.0.1', 9000
def frame(cmd, body=b''):
    return struct.pack('>I', 2+len(body)) + struct.pack('>H', cmd) + body
def w_str(s):
    b=s.encode(); return struct.pack('>H',len(b))+b

def read_one(s, want, timeout=5):
    s.settimeout(timeout); buf=b''
    try:
        while True:
            d = s.recv(262144)
            if not d: return None
            buf += d
            while len(buf) >= 6:
                ln = struct.unpack_from('>I', buf, 0)[0]
                if len(buf) < 4+ln: break
                cmd = struct.unpack_from('>H', buf, 4)[0]
                body = buf[6:4+ln]; buf = buf[4+ln:]
                if cmd == want: return body
    except socket.timeout:
        return None

def bench(cmd, body=b'', n=20, label=None):
    times=[]
    fails=0
    for i in range(n):
        try:
            t0=time.perf_counter()
            s=socket.create_connection((HOST,PORT),timeout=5)
            s.sendall(frame(10001, w_str('game_client')+b'\x00'*4))
            s.sendall(frame(cmd, body))
            r=read_one(s, cmd if cmd not in (12407,12409) else cmd, timeout=5)
            t1=time.perf_counter()
            s.close()
            if r is None: fails+=1
            else: times.append((t1-t0)*1000)
        except Exception:
            fails+=1
    if times:
        print("  %-34s n=%-3d 失败=%-2d  最小 %6.1f ms  中位 %6.1f ms  最大 %6.1f ms"
              % (label or cmd, n, fails, min(times), statistics.median(times), max(times)))
    else:
        print("  %-34s n=%-3d 失败=%-2d  (全部超时)" % (label or cmd, n, fails))

print("=== 服务端应答延迟（含 TCP 连接 + 首包，单位 ms）===")
bench(10301, label='10301 角色基础信息')
bench(10302, label='10302 角色数值')
bench(10303, label='10303 属性大表')
bench(12400, label='12400 任务列表（进行中）')
bench(12409, label='12409 任务列表（可接取）')
bench(12801, label='12801 商城列表（134 件）')
bench(12803, label='12803 商城简表')

print()
print("=== 服务端内部处理耗时（不经网络，直接调函数）===")
import sys, time
sys.path.insert(0, r"server")
import mock_server as m
cfg = m.load_config() if hasattr(m,'load_config') else None
import json
cfg = json.load(open(r"server\config.json", encoding="utf-8"))
for name, fn in (
    ("mission_cfg() 首载", None),
):
    pass
t0=time.perf_counter(); mc=m.mission_cfg(); t1=time.perf_counter()
print("  mission_cfg() 加载 846 条        : %6.1f ms" % ((t1-t0)*1000))
t0=time.perf_counter(); mall=m.mall_cfg(); t1=time.perf_counter()
print("  mall_cfg() 加载 134 件           : %6.1f ms" % ((t1-t0)*1000))
t0=time.perf_counter(); rows=m.mission_rows(cfg,1001); t1=time.perf_counter()
print("  mission_rows()（含状态归一）     : %6.1f ms" % ((t1-t0)*1000))
t0=time.perf_counter(); acc=m.accept_mission_rows(cfg,1001); t1=time.perf_counter()
print("  accept_mission_rows()            : %6.1f ms" % ((t1-t0)*1000))
t0=time.perf_counter(); st=m.role_state(cfg); b=m.build_10303(st, cfg.get('skills',[]), cfg.get('attr')); t1=time.perf_counter()
print("  build_10303()                    : %6.1f ms" % ((t1-t0)*1000))
t0=time.perf_counter()
for _ in range(20): m.mission_rows(cfg,1001)
t1=time.perf_counter()
print("  mission_rows() x20 平均          : %6.1f ms" % ((t1-t0)/20*1000))
