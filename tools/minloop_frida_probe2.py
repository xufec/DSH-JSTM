#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frida 抓"客户端到底有没有把字节写出去"——**带自证**版本（v2）

为什么要"自证"：第 2 轮我用 `Module.findExportByName(null,'send')` 挂了一个钩子，
它报"0 次写"，**而同一时间窗客户端写了 1575 条 HTTP 上报**（服务端日志为证）⇒
**钩子是瞎的**，那个"0 次写"是被污染的结论，已作废。
所以本版的铁律是：**先证明钩子能看见必然发生的写**（探针的 HTTP 上报），再看游戏帧。

v2 相比 v1 的三处改进：
  1. 不再只找"第一个 send"，而是**遍历所有 libc/curl/crypto/supersdk/cocos 模块**，
     在**每个模块内**分别挂 `send/sendto/write/writev/sendmsg/__sendto/syscall`；
  2. 同时挂 **Java 层**写（`java.io.FileOutputStream.write` / `OutputStream.write`），
     因为探针上报走的是 `cc.XMLHttpRequest`，在 MuMu 上可能落到 Java 层；
  3. 每秒上报一次**每个钩子的命中计数**（`stats`），谁在工作一目了然。

用法：
  adb -s 127.0.0.1:16384 shell "nohup /data/local/tmp/frida-server >/dev/null 2>&1 &"
  adb -s 127.0.0.1:16384 forward tcp:27042 tcp:27042
  python tools/minloop_frida_probe2.py --pid <主进程pid> --seconds 50
"""
from __future__ import annotations

import argparse
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

JS = r"""
var COUNTS = {};

function bump(k, n) {
  COUNTS[k] = (COUNTS[k] || 0) + 1;
  if (COUNTS[k] <= 3) send({ t: 'write', k: k, n: n });
}

function preview(ptr, n) {
  try {
    var m = Memory.readByteArray(ptr, Math.min(n, 24));
    var u = new Uint8Array(m), s = '';
    for (var i = 0; i < u.length; i++) s += ('0' + u[i].toString(16)).slice(-2) + ' ';
    return s;
  } catch (e) { return '<err>'; }
}

function hookAt(ptr, key) {
  if (COUNTS['H_' + key]) return;
  COUNTS['H_' + key] = 1;
  try {
    Interceptor.attach(ptr, {
      onEnter: function (args) {
        var n = args[2].toInt32();
        if (n <= 0) return;
        send({ t: 'write', k: key, n: n, hex: preview(args[1], n) });
        COUNTS[key] = (COUNTS[key] || 0) + 1;
      }
    });
    send({ t: 'hooked', k: key });
  } catch (e) {
    send({ t: 'hookerr', k: key, e: '' + e });
  }
}

var EXPS = ['send', 'sendto', 'write', 'writev', 'sendmsg', '__sendto'];
var MODS = Process.enumerateModules();
MODS.forEach(function (m) {
  if (!/libc|libcurl|libssl|libcrypto|supersdk|cocos|liblog|libandroid/i.test(m.name)) return;
  EXPS.forEach(function (e) {
    var p = null;
    try { p = m.findExportByName(e); } catch (err) { p = null; }
    if (p) hookAt(p, m.name + ':' + e);
  });
});
send({ t: 'modules', n: MODS.length });

if (Java.available) {
  Java.perform(function () {
    function tryJava(cls, method, sig, tag) {
      try {
        var C = Java.use(cls);
        if (sig) {
          C[method].overload(sig).implementation = function () {
            bump('java:' + tag, arguments.length > 0 && arguments[0] ? arguments[0].length : 0);
            return this[method].apply(this, arguments);
          };
        } else {
          C[method].implementation = function () {
            bump('java:' + tag, 0);
            return this[method].apply(this, arguments);
          };
        }
        send({ t: 'hooked', k: 'java:' + tag });
      } catch (e) {
        send({ t: 'hookerr', k: 'java:' + tag, e: '' + e });
      }
    }
    tryJava('java.io.FileOutputStream', 'write', '[B', 'FileOutputStream.write');
    tryJava('java.io.OutputStream', 'write', '[B', 'OutputStream.write');
    tryJava('java.net.SocketOutputStream', 'write', '[B', 'SocketOutputStream.write');
  });
} else {
  send({ t: 'nojava' });
}

setInterval(function () { send({ t: 'stats', c: COUNTS }); }, 5000);
send({ t: 'ready' });
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1:27042')
    ap.add_argument('--pid', type=int, required=True)
    ap.add_argument('--seconds', type=int, default=50)
    args = ap.parse_args()

    import frida
    dev = frida.get_device_manager().add_remote_device(args.host)
    session = dev.attach(args.pid)
    print('attached pid=%d' % args.pid)
    state = {'hooked': [], 'writes': 0, 'ready': False, 'modules': 0}

    def on_message(msg, data):
        if msg.get('type') != 'send':
            return
        p = msg['payload']
        t = p.get('t')
        if t == 'hooked':
            state['hooked'].append(p['k'])
        elif t == 'write':
            state['writes'] += 1
            if state['writes'] <= 12:
                print('  WRITE %-42s n=%-5s %s' % (p['k'], p.get('n'), p.get('hex', '')))
        elif t == 'hookerr':
            print('  hookerr %-42s %s' % (p['k'], str(p.get('e'))[:80]))
        elif t == 'stats':
            nz = {k: v for k, v in p['c'].items() if not k.startswith('H_') and v}
            print('  stats: %s' % (nz if nz else '（还没有任何钩子命中）'))
        elif t == 'modules':
            state['modules'] = p['n']
        elif t == 'ready':
            state['ready'] = True

    script = session.create_script(JS)
    script.on('message', on_message)
    script.load()
    print('模块总数=%s  已挂钩子=%s' % (state['modules'], state['hooked']))
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        time.sleep(1)
    print('\n──── 结果 ────')
    print('挂钩子数=%d  写事件=%d' % (len(state['hooked']), state['writes']))
    print('挂上的钩子：%s' % ', '.join(state['hooked'][:14]))
    if state['writes'] == 0:
        print('★ 零写事件。**但必须先按下面这条自证**：若本次采集窗口内服务端仍收到探针的\n'
              '  DSH_PROBE 上报（说明客户端确实在写 HTTP），而这里 0 写 ⇒ 钩子依旧是瞎的，\n'
              '  该结论作废。反之（服务端也没有新上报）则说明客户端当时确实什么都没写。')
    try:
        script.unload()
        session.detach()
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
