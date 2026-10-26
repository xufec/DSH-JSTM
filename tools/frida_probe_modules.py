# -*- coding: utf-8 -*-
"""frida 探针 v1：attach 游戏进程 → 枚举 lua/cocos 模块与关键导出符号。
目的：判断在 MuMu(houdini 翻译 ARM 代码) 下能否挂原生钩，并找到 lua_getfield 等符号。

用法（Anaconda 的 frida 17.18.0）：
    D:\\Anaconda3\\python.exe tools\\frida_probe_modules.py [进程名或PID]
"""
import sys
import time

import frida

TARGET = sys.argv[1] if len(sys.argv) > 1 else 'com.shiyue.dldl.ewan.baidu2'

JS = r"""
(function () {
    var out = { mods: [], hits: {} };
    var mods = Process.enumerateModules();
    out.total = mods.length;
    out.sample = mods.map(function (m) { return m.name; });
    var re = /lua|cocos|il2cpp|unity|houdini|nemu|nb|dldl|entry|super|jni|arm/i;
    mods.forEach(function (m) {
        if (re.test(m.name)) out.mods.push(m.name + '  base=' + m.base + ' size=' + m.size);
    });
    var wants = ['lua_getfield', 'lua_getglobal', 'lua_gettable', 'lua_rawget',
                 'luaL_loadbuffer', 'luaL_loadbufferx', 'lua_pcall', 'lua_pushnumber',
                 'lua_call', 'luaD_call', 'lua_load'];
    mods.forEach(function (m) {
        var got = [];
        m.enumerateExports().forEach(function (e) {
            if (wants.indexOf(e.name) >= 0) got.push(e.name + '@' + e.address);
        });
        if (got.length) out.hits[m.name] = got;
    });
    send({ tag: 'probe', data: out });
})();
"""


def main():
    dev = frida.get_usb_device(timeout=10)
    print('device:', dev)
    # ★ MuMu/houdini：游戏是 32 位进程，frida 读到的**进程名是乱码**，
    #   按名字 get_process 会失败 ⇒ 支持直接传 PID。
    try:
        if str(TARGET).isdigit():
            pid = int(TARGET)
        else:
            pid = dev.get_process(TARGET).pid
    except Exception as e:
        print('!! 定位进程失败 %s: %s' % (TARGET, e))
        return 2
    print('attach pid', pid)
    session = dev.attach(pid)
    done = {'ok': False}

    def on_msg(msg, data):
        if msg.get('type') == 'send':
            p = msg['payload']
            if p.get('tag') == 'probe':
                d = p['data']
                print('模块总数:', d.get('total'));
                names = d.get('sample') or []
                print('全部模块名（%d）:' % len(names));
                for s in names: print('   ', s);
                print('--- 匹配模块 (%d) ---' % len(d['mods']))
                for m in d['mods']:
                    print('   ', m)
                print('--- 关键导出符号 ---')
                if not d['hits']:
                    print('    （无）')
                for mod, syms in d['hits'].items():
                    print('  ', mod)
                    for s in syms:
                        print('      ', s)
                done['ok'] = True
        else:
            print('frida:', msg)

    script = session.create_script(JS)
    script.on('message', on_msg)
    script.load()
    for _ in range(50):
        if done['ok']:
            break
        time.sleep(0.2)
    time.sleep(0.5)
    session.detach()
    return 0 if done['ok'] else 3


if __name__ == '__main__':
    sys.exit(main())

