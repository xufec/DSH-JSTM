"""1.4.9 私服 —— 游戏服务端看门狗（轻量、自分离、防重启风暴）。

## 为什么需要它（实测现象）

本项目里 mock_server 出现过**两次无人干预的自消失**：
  - 通过 harness 后台 job 起时：包装进程结束后 python 变孤儿，之后也没了；
  - 通过可靠脚本起时：stderr 为空（**不是崩溃**），但进程就是没了。
所以「端口有服务」这件事本身不可靠，需要一个持续探活的守护。

## 它做什么

每 `--interval` 秒做一次**真的健康检查**（不是只看端口在听）：

    TCP 连上 9000 → 发一帧 1199 心跳 → 等回包 → 校验 cmd==1199

不健康就：
    1) 杀掉残留的 mock_server（含孤儿）
    2) 等待 9000/8080 释放
    3) 分离启动一个新的
    4) 等它就绪并复检

## 防重启风暴

- 连续失败时**指数退避**（interval → ×2，封顶 300s）
- 每 10 分钟窗口内最多重启 `--max-restarts` 次（默认 12），超出则只告警不重启
- 每次动作都写 `server/logs/watchdog.log`

## 用法

    python tools/server_watchdog.py --once        # 只检查一次（不重启），退出码 0/1
    python tools/server_watchdog.py --status      # 看守护进程 + 服务端状态
    python tools/server_watchdog.py --daemonize   # 分离启动守护进程（推荐）
    python tools/server_watchdog.py --run         # 前台跑循环（调试用）
    python tools/server_watchdog.py --stop        # 停止守护进程
"""
import argparse
import os
import socket
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGDIR = os.path.join(ROOT, 'server', 'logs')
PIDFILE = os.path.join(LOGDIR, 'watchdog.pid')
WLOG = os.path.join(LOGDIR, 'watchdog.log')
SERVER = os.path.join(ROOT, 'server', 'mock_server.py')

HOST = '127.0.0.1'
PORT = 9000
HTTP_PORT = 8080
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000


def log(msg):
    os.makedirs(LOGDIR, exist_ok=True)
    line = '[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg)
    try:
        with open(WLOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass
    print(line, flush=True)


# ---------------------------------------------------------------------------
# 健康检查：TCP 连上 + 1199 心跳往返
# ---------------------------------------------------------------------------

def healthy(timeout=3.0):
    """返回 (ok, detail)。"""
    try:
        s = socket.create_connection((HOST, PORT), timeout=timeout)
    except Exception as e:
        return False, 'connect_failed:%r' % (e,)
    try:
        s.settimeout(timeout)
        body = struct.pack('>I', int(time.time()) & 0xFFFFFFFF)
        payload = struct.pack('>H', 1199) + body
        s.sendall(struct.pack('>I', len(payload)) + payload)
        hdr = b''
        while len(hdr) < 4:
            c = s.recv(4 - len(hdr))
            if not c:
                return False, 'no_header'
            hdr += c
        ln = struct.unpack('>I', hdr)[0]
        buf = b''
        while len(buf) < ln:
            c = s.recv(ln - len(buf))
            if not c:
                break
            buf += c
        if len(buf) < 2:
            return False, 'short_body'
        cmd = struct.unpack('>H', buf[:2])[0]
        if cmd != 1199:
            return False, 'bad_cmd:%d' % cmd
        return True, 'ok'
    except Exception as e:
        return False, 'hb_failed:%r' % (e,)
    finally:
        try:
            s.close()
        except Exception:
            pass


def port_listening(port):
    try:
        s = socket.create_connection((HOST, port), timeout=1.0)
        s.close()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 进程管理
# ---------------------------------------------------------------------------

def kill_servers():
    """杀掉所有 mock_server 进程（含孤儿）。返回被杀 PID 列表。"""
    killed = []
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -like '*mock_server.py*' } | "
             "ForEach-Object { $_.ProcessId }"],
            capture_output=True, text=True, timeout=30).stdout
    except Exception as e:
        log('  !! 枚举进程失败: %r' % (e,))
        return killed
    for tok in out.split():
        if tok.isdigit():
            pid = int(tok)
            try:
                subprocess.run(['taskkill', '/PID', str(pid), '/F'],
                               capture_output=True, timeout=15)
                killed.append(pid)
            except Exception:
                pass
    return killed


def start_server():
    """分离启动服务端。返回新进程 PID。"""
    out = open(os.path.join(LOGDIR, 'stdout.log'), 'ab')
    err = open(os.path.join(LOGDIR, 'stderr.log'), 'ab')
    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    p = subprocess.Popen([sys.executable, SERVER], cwd=ROOT,
                         stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                         creationflags=flags, close_fds=True)
    return p.pid


def wait_ready(timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        if port_listening(PORT) and port_listening(HTTP_PORT):
            ok, _ = healthy()
            if ok:
                return True
        time.sleep(0.5)
    return False


def restart_once(reason):
    log('检测到服务端异常（%s）→ 开始重启' % reason)
    killed = kill_servers()
    if killed:
        log('  已终止残留进程: %s' % killed)
    end = time.time() + 25
    while time.time() < end and (port_listening(PORT) or port_listening(HTTP_PORT)):
        time.sleep(0.5)
    if port_listening(PORT) or port_listening(HTTP_PORT):
        log('  !! 端口未释放，放弃本次重启')
        return False
    pid = start_server()
    log('  已分离启动 mock_server，PID=%d' % pid)
    if wait_ready(30):
        log('  ✅ 服务端已就绪')
        return True
    log('  ❌ 启动后仍未就绪')
    return False


# ---------------------------------------------------------------------------
# 模式
# ---------------------------------------------------------------------------

def mode_once():
    ok, detail = healthy()
    print('server healthy=%s detail=%s' % (ok, detail))
    return 0 if ok else 1


def mode_status():
    alive = False
    pid = None
    if os.path.exists(PIDFILE):
        try:
            pid = int(open(PIDFILE).read().strip())
            out = subprocess.run(['tasklist', '/FI', 'PID eq %d' % pid],
                                 capture_output=True, text=True, timeout=15).stdout
            alive = ('python' in out.lower())
        except Exception:
            alive = False
    ok, detail = healthy()
    print('watchdog: %s%s' % ('RUNNING' if alive else 'not running',
                              (' (pid=%d)' % pid) if pid else ''))
    print('server  : %s (%s)' % ('HEALTHY' if ok else 'DOWN', detail))
    return 0 if (alive and ok) else 1


def mode_stop():
    if not os.path.exists(PIDFILE):
        print('watchdog: 未在运行（无 pid 文件）')
        return 0
    pid = int(open(PIDFILE).read().strip())
    try:
        subprocess.run(['taskkill', '/PID', str(pid), '/F'],
                       capture_output=True, timeout=15)
        print('watchdog: 已停止 pid=%d' % pid)
    except Exception as e:
        print('watchdog: 停止失败 %r' % (e,))
    try:
        os.remove(PIDFILE)
    except Exception:
        pass
    return 0


def mode_daemonize():
    if os.path.exists(PIDFILE):
        try:
            pid = int(open(PIDFILE).read().strip())
            out = subprocess.run(['tasklist', '/FI', 'PID eq %d' % pid],
                                 capture_output=True, text=True, timeout=15).stdout
            if 'python' in out.lower():
                print('watchdog 已在运行 pid=%d' % pid)
                return 0
        except Exception:
            pass
    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    outf = open(WLOG, 'ab')
    p = subprocess.Popen([sys.executable, os.path.abspath(__file__), '--run'],
                         cwd=ROOT, stdout=outf, stderr=outf,
                         stdin=subprocess.DEVNULL, creationflags=flags,
                         close_fds=True)
    with open(PIDFILE, 'w') as f:
        f.write(str(p.pid))
    print('watchdog 已分离启动 pid=%d' % p.pid)
    time.sleep(3)
    return mode_status()


def mode_run(interval, max_restarts):
    with open(PIDFILE, 'w') as f:
        f.write(str(os.getpid()))
    log('=== watchdog 启动 pid=%d interval=%ds max_restarts=%d/%dh ==='
        % (os.getpid(), interval, max_restarts, 1))
    backoff = interval
    window_start = time.time()
    restarts = 0
    fails = 0
    while True:
        ok, detail = healthy()
        if ok:
            if fails:
                log('服务端已恢复（此前连续失败 %d 次）' % fails)
            fails = 0
            backoff = interval
            time.sleep(interval)
            continue
        fails += 1
        # 重启配额（滑动 10 分钟窗口）
        if time.time() - window_start > 600:
            window_start = time.time()
            restarts = 0
        if restarts >= max_restarts:
            log('!! 10 分钟内已重启 %d 次，超出配额；本次只告警不重启（%s）'
                % (restarts, detail))
            time.sleep(interval)
            continue
        if restart_once(detail):
            restarts += 1
            backoff = interval
            time.sleep(interval)
        else:
            backoff = min(300, backoff * 2)
            log('重启未成功，退避到 %ds' % backoff)
            time.sleep(backoff)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--stop', action='store_true')
    ap.add_argument('--daemonize', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--interval', type=int, default=20)
    ap.add_argument('--max-restarts', type=int, default=12)
    a = ap.parse_args()
    if a.once:
        return mode_once()
    if a.status:
        return mode_status()
    if a.stop:
        return mode_stop()
    if a.daemonize:
        return mode_daemonize()
    if a.run:
        return mode_run(a.interval, a.max_restarts)
    ap.print_help()
    return 0


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    sys.exit(main() or 0)
