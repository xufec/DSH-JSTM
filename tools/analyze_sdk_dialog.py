#!/usr/bin/env python3
"""Spawn the game under Frida and dump the stack that creates the blocking dialog.

usage: python tools/analyze_sdk_dialog.py [seconds]
"""
import sys
import time

import frida

PKG = 'com.shiyue.dldl.ewan.baidu2'
JS = 'tools/analyze_sdk_dialog_hook.js'


def on_message(msg, data):
    if msg['type'] == 'send':
        print(msg['payload'], flush=True)
    elif msg['type'] == 'error':
        print('!! ERROR:', msg.get('stack') or msg.get('description'), flush=True)


def main():
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    with open(JS, 'r', encoding='utf-8') as f:
        src = f.read()
    dev = frida.get_usb_device(timeout=10)
    pid = dev.spawn([PKG])
    print('spawned pid', pid, flush=True)
    sess = dev.attach(pid)
    # v8 supports the ES-module `import` of frida-java-bridge; qjs does not.
    script = sess.create_script(src, runtime='v8')
    script.on('message', on_message)
    script.load()
    dev.resume(pid)
    print('resumed; collecting for %ds' % secs, flush=True)
    time.sleep(secs)
    try:
        dev.kill(pid)
    except Exception:
        pass
    print('done')


if __name__ == '__main__':
    main()
