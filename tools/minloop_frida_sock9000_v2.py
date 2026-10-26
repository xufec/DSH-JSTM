#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frida 版 **v4：可信观测 + 只看游戏服 socket**（把 v2 与 v3 合并）

背景（三轮踩坑换来的纪律）：
  · v1 只挂“第一个 send” ⇒ 报 0 写，而同期客户端写了 1575 条 HTTP ⇒ **瞎**，结论作废；
  · v2 改成**遍历所有模块、逐模块逐导出挂钩**（120 个钩子）⇒ 采到 14568 次写，
    同期服务端收到 546 条探针上报 ⇒ **挂钩有效（自证通过）**；
  · v3 只挂 `libc.so` 的 5 个导出 ⇒ 又变瞎（全部写=0，而服务端 551 条上报）
    ⇒ 说明在本环境（MuMu + ARM 翻译）里 `Module.findExportByName('libc.so', ...)`
    解析到的地址**并不是**实际被调用的那个。

v4 = v2 的“全模块挂钩”（已自证） + v3 的“fd → peer 端口过滤”（内核判据），并且：
  · **内置自证**：同时统计“全部写”和“发往 :9000 的写”。若 `全部写=0` 而服务端同期有探针上报
    ⇒ 直接判 **INCONCLUSIVE（钩子瞎）**，绝不输出“客户端没写过”的结论；
  · 失败也要看：`onLeave` 里 `retval < 0` ⇒ 写了但被拒（另一类根因）。

用法：
  adb -s 127.0.0.1:16384 shell "nohup /data/local/tmp/frida-server >/dev/null 2>&1 &"
  adb -s 127.0.0.1:16384 forward tcp:27042 tcp:27042
  python tools/minloop_frida_sock9000_v2.py --pid <主进程pid> --seconds 60 --probe-log <服务端日志>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

JS = r"""
var ALL = 0, TO9000 = 0, BYTES9000 = 0, FAIL9000 = 0, LOGGED = 0, FDS = {};
var HADDR = {};

function peerPort(fd) {
  try {
    var a = Socket.peerAddress(fd);
    if (a === null) return -1;
    return a.port;
  } catch (e) { return -2; }
}

function hookAddr(p, key) {
  if (HADDR[key]) return;
  HADDR[key] = 1;
  try {
    Interceptor.attach(p, {
      onEnter: function (args) {
        try { this.fd = args[0].toInt32(); this.n = args[2].toInt32(); }
        catch (e) { this.fd = -1; this.n = -1; }
        this.game = false;
        ALL++;
        FDS[this.fd] = (FDS[this.fd] || 0) + 1;
        var port = peerPort(this.fd);
        if (port === 9000) {
          this.game = true;
          TO9000++;
          if (this.n > 0) BYTES9000 += this.n;
          if (LOGGED < 10) { LOGGED++; send({ t: 'g', k: key, fd: this.fd, n: this.n }); }
        }
      },
      onLeave: function (ret) {
        if (!this.game) return;
        var r = 0;
        try { r = ret.toInt32(); } catch (e) { r = 0; }
        if (r < 0) { FAIL9000++; send({ t: 'gfail', k: key, fd: this.fd, n: this.n, r: r }); }
      }
    });
    send({ t: 'hooked', k: key });
  } catch (e) {
    send({ t: 'hookerr', k: key, e: '' + e });
  }
}

// ★ 全模块挂（v2 已验证有效）。逐处单独包 try：
//   frida 17 的 Module.findExportByName(模块名, 符号) 在模块不存在时会**抛异常**，
//   一旦抛在 forEach 外层，整段脚本会中止（表现为“attach 成功却一条消息都没有”，v3 首版就栽在这）。
var MODS = Process.enumerateModules();
var NH = 0;
MODS.forEach(function (m) {
  ['send', 'sendto', 'write', 'writev', 'sendmsg'].forEach(function (e) {
    var p = null;
    try { p = m.findExportByName(e); } catch (err) { p = null; }
    if (p) { hookAddr(p, m.name + ':' + e); NH++; }
  });
});
send({ t: 'mods', n: MODS.length, hooks: Object.keys(HADDR).length });

setInterval(function () {
  send({ t: 'stats', all: ALL, to9000: TO9000, bytes9000: BYTES9000, fail9000: FAIL9000,
         fds: Object.keys(FDS).length });
}, 5000);

if (Java.available) {
  Java.perform(function () {
    try {
      var OS = Java.use('java.io.OutputStream');
      OS.write.overload('[B').implementation = function (b) {
        ALL++;
        if (b && b.length > 0) send({ t: 'java', n: b.length });
        return this.write(b);
      };
      send({ t: 'hooked', k: 'java:OutputStream.write' });
    } catch (e) { send({ t: 'hookerr', k: 'java:OutputStream', e: '' + e }); }
  });
}
send({ t: 'ready' });
"""


def count_probe(path):
    """服务端日志里 DSH_PROBE 的行数（用作“客户端确实在写”的基准）。"""
    if not path or not os.path.exists(path):
        return -1
    n = 0
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if 'DSH_PROBE' in line:
                    n += 1
    except OSError:
        return -1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1:27042')
    ap.add_argument('--pid', type=int, default=0)
    ap.add_argument('--spawn', default='', help='包名：用 spawn 模式（先把钩子装好再放行进程，'
                                                '消除"挂晚了"这个竞态）')
    ap.add_argument('--seconds', type=int, default=60)
    ap.add_argument('--probe-log', default='')
    args = ap.parse_args()

    import frida
    dev = frida.get_device_manager().add_remote_device(args.host)

    before = count_probe(args.probe_log)
    spawned = False
    if args.spawn:
        pid = dev.spawn([args.spawn])
        spawned = True
        print('spawn %s pid=%d（已挂起，先装钩子再放行）' % (args.spawn, pid))
    else:
        if not args.pid:
            print('需要 --pid 或 --spawn')
            return 2
        pid = args.pid
        print('attached pid=%d' % pid)

    session = dev.attach(pid)
    last = {'all': 0, 'to9000': 0, 'bytes9000': 0, 'fail9000': 0, 'fds': 0}

    def on_message(msg, data):
        if msg.get('type') != 'send':
            return
        p = msg['payload']
        t = p.get('t')
        if t == 'mods':
            print('  模块=%s 钩子地址数=%s' % (p['n'], p['hooks']))
        elif t == 'hooked':
            pass
        elif t == 'g':
            print('  ★ WRITE→:9000  %-40s fd=%-4s n=%s' % (p['k'], p['fd'], p['n']))
        elif t == 'gfail':
            print('  ★ FAIL→:9000   %-40s fd=%-4s n=%s ret=%s' % (p['k'], p['fd'], p['n'], p['r']))
        elif t == 'stats':
            last.update(p)
            print('  stats: 全部写=%-7d fds=%-3s | 发往:9000 次数=%-4d 字节=%-6d 失败=%d'
                  % (p['all'], p.get('fds'), p['to9000'], p['bytes9000'], p['fail9000']))

    script = session.create_script(JS)
    script.on('message', on_message)
    script.load()
    if spawned:
        dev.resume(pid)
        print('已放行进程，采集 %d 秒' % args.seconds)
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        time.sleep(1)
    after = count_probe(args.probe_log)

    print('\n──── 判读 ────')
    print('全部写=%d（fd 数=%s）｜ 发往:9000 次数=%d 字节=%d 失败=%d'
          % (last['all'], last.get('fds'), last['to9000'], last['bytes9000'], last['fail9000']))
    if args.probe_log:
        print('自证基准：同期服务端 DSH_PROBE 增加 %d 条' % (after - before))
    delta = after - before
    if last['all'] == 0 and delta <= 0:
        # ★ 本次修正：客户端当时**根本没在写**（探针也没上报）⇒ 这一轮什么都没发生，
        #   既不能证明钩子有效，也不能说"客户端没写过 :9000"。
        print('结论：**INCONCLUSIVE（空窗）** —— 客户端与探针在整个窗口内都没有写，')
        print('      本轮不构成任何证据。要下结论必须挑"探针正在上报"的窗口（启动后 ~40 秒内）。')
    elif last['all'] == 0 and delta > 0:
        print('结论：**INCONCLUSIVE（钩子瞎）** —— 客户端明显在写（服务端有上报）而钩子 0 命中，')
        print('      本条不得用于“客户端没写过 :9000”的结论。')
    elif last['to9000'] == 0:
        print('结论：**可信** —— 钩子看得见写（全部写=%d），且**发往 :9000 的写为 0**' % last['all'])
        print('      ⇒ 游戏帧根本没到 socket 层（问题在客户端 Lua→原生这一段的发送路径）。')
    elif last['fail9000'] > 0:
        print('结论：写了但**被拒**（失败 %d 次）⇒ 按 fd 状态/连接状态继续查。' % last['fail9000'])
    else:
        print('结论：字节确实发往 :9000（%d 字节 / %d 次）⇒ 问题在网络层或服务端。'
              % (last['bytes9000'], last['to9000']))
    try:
        script.unload()
        session.detach()
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
