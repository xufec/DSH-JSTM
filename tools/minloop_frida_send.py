#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 frida 在**系统调用层**看客户端到底有没有把字节写出去。

背景（本项目已确证的实情）：
  MuMu 里的真实 1.4.9 APK 与我们自建服之间的 TCP **连得上**，但服务端在**字节级**日志下
  仍然是 `-- recv 0`。同时客户端 Lua 侧：
    · `ctrl:SendProtocal(mgr:GetPrototype(cmd))` 返回 true
    · `proto:Encode()` 返回 true
    · `net_manager:Update()` / `GameNet:doOneMsg()` 都返回 true
   ⇒ Lua 侧"全部成功"，但字节没上线。到底是"Lua 侧写空"还是"原生写了但没上 TCP"，
     只能在 syscall 层看 —— 这正是本脚本要回答的唯一问题。

用法（需先起 frida-server + adb forward）：
  adb -s 127.0.0.1:16384 shell "/data/local/tmp/frida-server &"
  adb -s 127.0.0.1:16384 forward tcp:27042 tcp:27042
  python tools/minloop_frida_send.py --seconds 60
"""
from __future__ import annotations

import argparse
import sys
import time

# Windows 控制台 GBK 会直接抛 UnicodeEncodeError（同 min_loop_server 的坑）
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

JS = r"""
var HITS = 0, SOCK = 0;

function preview(ptr, n) {
  try {
    var m = Memory.readByteArray(ptr, Math.min(n, 32));
    var u = new Uint8Array(m);
    var s = '';
    for (var i = 0; i < u.length; i++) {
      s += ('0' + u[i].toString(16)).slice(-2) + ' ';
    }
    return s;
  } catch (e) { return '<err>'; }
}

function hook(name) {
  var p = Module.findExportByName(null, name);
  if (p === null) { send({t: 'nofunc', name: name}); return; }
  Interceptor.attach(p, {
    onEnter: function (args) {
      var n = args[2].toInt32();
      if (n <= 0) return;
      HITS++;
      SOCK++;
      var buf = args[1];
      send({ t: 'write', fn: name, n: n, hex: preview(buf, n) });
    }
  });
  send({ t: 'hooked', name: name });
}

['send', 'sendto', 'write', 'writev', 'sendmsg'].forEach(hook);
send({ t: 'ready' });
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1:27042')
    ap.add_argument('--pkg', default='com.shiyue.dldl.ewan.qihoo')
    ap.add_argument('--seconds', type=int, default=60)
    ap.add_argument('--pid', type=int, default=0,
                    help='直接指定主进程 pid（frida 枚举在本模拟器上会漏掉主进程，推荐用这个）')
    args = ap.parse_args()

    import frida
    dev = frida.get_device_manager().add_remote_device(args.host)
    print('device:', dev)
    # ★ 必须精确匹配主进程：`:PushClient` / `:pushservice` 是子进程，
    #   挂到它们身上一个游戏帧都看不到（本次就踩了，误报"0 写事件"）。
    #   另外 frida-server 在本模拟器上**枚举不到主进程**（adb ps 看得到、frida 列表里没有）
    #   ⇒ 支持 --pid 直连。
    pid = args.pid
    if not pid:
        procs = [p for p in dev.enumerate_processes() if p.name == args.pkg]
        if procs:
            pid = procs[0].pid
    if not pid:
        print('frida 未枚举到主进程 %s，请用 --pid 指定（adb shell ps -A | grep %s）'
              % (args.pkg, args.pkg))
        return 2
    print('attach pid=%d' % pid)
    session = dev.attach(pid)
    writes = []
    ready = {'v': False}

    def on_message(msg, data):
        if msg.get('type') != 'send':
            return
        p = msg['payload']
        if p.get('t') == 'write':
            writes.append(p)
            if len(writes) <= 40:
                print('  write %-7s n=%-5d %s' % (p['fn'], p['n'], p['hex']))
        elif p.get('t') == 'ready':
            ready['v'] = True
            print('  hooks ready')
        else:
            print('  %s' % (p,))

    script = session.create_script(JS)
    script.on('message', on_message)
    script.load()
    print('采集 %d 秒（请在模拟器里操作/等待客户端发包）…' % args.seconds)
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        time.sleep(1)
    print('\n──── 结果 ────')
    print('syscall 层写事件总数：%d' % len(writes))
    if writes:
        tot = sum(w['n'] for w in writes)
        print('写出字节合计：%d' % tot)
        print('前 5 条：')
        for w in writes[:5]:
            print('   %s n=%d %s' % (w['fn'], w['n'], w['hex']))
    else:
        print('★ 客户端在 syscall 层**一个字节都没写** ⇒ 不是"服务端漏读"，'
              '也不是"TCP 半开"，而是**客户端根本没调用写**（Lua 侧的 true 是假的成功）')
    script.unload()
    session.detach()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
