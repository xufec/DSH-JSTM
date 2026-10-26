#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frida 版 v3：**只看游戏服那个 socket**（fd → peer 端口 9000）

为什么要有 v3：v2 已经**自证有效**（采集窗口内 14568 次写事件 + 服务端 546 条探针上报），
所以"客户端确实在写 HTTP"这件事已经成立。剩下的唯一问题是：
    **它到底有没有往游戏服（:9000）那个 socket 上写过哪怕一个字节？**
v2 看不到这个，因为写事件混在一起、预览内存还失败（ARM 翻译层）。
v3 的判据来自内核而不是内存：用 `Socket.peerAddress(fd)` 把 fd 解成对端地址/端口，
于是可以精确统计"**发给 :9000 的写次数 / 字节数 / 失败次数**"。

读法：
  · sent_to_9000 = 0            ⇒ 客户端**从来没往游戏服 socket 写过**（帧根本没到 socket 层）
  · sent_to_9000 > 0 且 failed>0 ⇒ 写了但**被拒**（例如 fd 已断/未就绪）⇒ 另一类根因
  · sent_to_9000 > 0 且 failed=0 ⇒ 字节确实出去了，那问题就在网络层/我的服务端
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
var ALL = 0, TO9000 = 0, BYTES9000 = 0, FAIL9000 = 0, LOGGED = 0;
var HITP = {};

function peerPort(fd) {
  try {
    var a = Socket.peerAddress(fd);
    if (a === null) return -1;
    return a.port;
  } catch (e) { return -2; }
}

function hookOne(name) {
  // ★ 踩坑记录：frida 17 的 `Module.findExportByName('不存在的模块', x)` 会**抛异常**。
  //   v3 第一版把 forEach(hookOne) 写在 try 外 ⇒ 一次抛异常就整段脚本中止，
  //   表现是"attach 成功但一条消息都没有"。所以这里每一处查找都单独包 try。
  var p = null;
  try { p = Module.findExportByName('libc.so', name); } catch (e) { p = null; }
  if (!p) { try { p = Module.findExportByName(null, name); } catch (e) { p = null; } }
  if (!p) { send({ t: 'nofunc', k: name }); return; }
  var key = name + '@' + p;
  if (HITP[key]) return;
  HITP[key] = 1;
  try {
    Interceptor.attach(p, {
      onEnter: function (args) {
        this.fd = args[0].toInt32();
        this.n = args[2].toInt32();
        this.isGame = false;
        ALL++;
        var port = peerPort(this.fd);
        if (port === 9000) {
          this.isGame = true;
          TO9000++;
          if (this.n > 0) BYTES9000 += this.n;
          if (LOGGED < 8) {
            LOGGED++;
            send({ t: 'g', fn: name, fd: this.fd, n: this.n });
          }
        }
      },
      onLeave: function (ret) {
        if (this.isGame) {
          var r = ret.toInt32();
          if (r < 0) {
            FAIL9000++;
            send({ t: 'gfail', fn: name, fd: this.fd, n: this.n, r: r });
          }
        }
      }
    });
    send({ t: 'hooked', k: name + ':' + p });
  } catch (e) {
    send({ t: 'hookerr', k: name, e: '' + e });
  }
}

send({ t: 'boot' });
['send', 'sendto', 'write', 'writev', 'sendmsg'].forEach(function (n) {
  try { hookOne(n); } catch (e) { send({ t: 'hookerr', k: n, e: '' + e }); }
});
send({ t: 'ready', libc: !!Process.findModuleByName('libc.so') });
setInterval(function () {
  send({ t: 'stats', all: ALL, to9000: TO9000, bytes9000: BYTES9000, fail9000: FAIL9000 });
}, 5000);
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1:27042')
    ap.add_argument('--pid', type=int, required=True)
    ap.add_argument('--seconds', type=int, default=60)
    args = ap.parse_args()

    import frida
    dev = frida.get_device_manager().add_remote_device(args.host)
    session = dev.attach(args.pid)
    print('attached pid=%d（libc 地址解析已内置）' % args.pid)

    def on_message(msg, data):
        if msg.get('type') != 'send':
            return
        p = msg['payload']
        t = p.get('t')
        if t == 'hooked':
            print('  hook %s' % p['k'])
        elif t == 'boot':
            print('  script boot')
        elif t == 'nofunc':
            print('  nofunc %s' % p['k'])
        elif t == 'g':
            print('  ★ WRITE→:9000 %-6s fd=%-3s n=%s' % (p['fn'], p['fd'], p['n']))
        elif t == 'gfail':
            print('  ★ FAIL→:9000  %-6s fd=%-3s n=%s ret=%s' % (p['fn'], p['fd'], p['n'], p['r']))
        elif t == 'hookerr':
            print('  hookerr %s %s' % (p['k'], str(p.get('e'))[:70]))
        elif t == 'stats':
            print('  stats: 全部写=%-7d 发往:9000 次数=%-4d 字节=%-7d 失败=%d'
                  % (p['all'], p['to9000'], p['bytes9000'], p['fail9000']))

    script = session.create_script(JS)
    script.on('message', on_message)
    script.load()
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        time.sleep(1)
    print('\n──── 判读 ────')
    print('发往 :9000 的写次数 / 字节 / 失败，见上面最后一条 stats。')
    print('  to9000=0            ⇒ 客户端从未往游戏服 socket 写过（帧没到 socket 层）')
    print('  to9000>0 fail>0     ⇒ 写了但被拒（fd 未就绪/已断）')
    print('  to9000>0 fail=0     ⇒ 字节确实发出，问题在网络层或服务端')
    try:
        script.unload()
        session.detach()
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
