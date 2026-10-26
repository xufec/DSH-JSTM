# -*- coding: utf-8 -*-
"""frida 探针 v2：在 32 位 houdini 进程里做**内存扫描**（模块表看不到 ARM 库时的备用通道）。

扫描目标字符串：
  · 'SkillXiulian' / 'config_skill_xiulian'  → 客户端是否把修炼配置载入内存
  · '拥有活力' / '????'                       → 日常面板字串表的落点
  · 'huoli_list' / 'total_val'                → 面板数据键
用法：D:\\Anaconda3\\python.exe tools\\frida_mem_scan.py <pid>
"""
import sys
import time

import frida

TARGET = sys.argv[1] if len(sys.argv) > 1 else '19238'

JS = r"""
(function () {
    function scan(tag, needle) {
        var res = [];
        try {
            var ranges = Process.enumerateRanges('r--');
            for (var i = 0; i < ranges.length && res.length < 5; i++) {
                var r = ranges[i];
                try {
                    var m = Memory.scanSync(r.base, r.size, needle);
                    for (var j = 0; j < m.length && res.length < 5; j++) {
                        res.push(m[j].address.toString());
                    }
                } catch (e2) { /* 单段失败继续 */ }
            }
        } catch (e) { res.push('ERR:' + e); }
        send({ tag: 'scan', what: tag, hits: res });
    }
    scan('SkillXiulian', '53 6b 69 6c 6c 58 69 75 6c 69 61 6e');   // ASCII
    scan('config_skill_xiulian', '63 6f 6e 66 69 67 5f 73 6b 69 6c 6c 5f 78 69 75 6c 69 61 6e');
    scan('huoli_list', '68 75 6f 6c 69 5f 6c 69 73 74');
    scan('total_val', '74 6f 74 61 6c 5f 76 61 6c');
    // UTF-8: 拥有活力
    scan('拥有活力(utf8)', 'e6 8b a5 e6 9c 89 e6 b4 bb e5 8a 9b');
    send({ tag: 'done' });
})();
"""


def main():
    dev = frida.get_usb_device(timeout=10)
    pid = int(TARGET)
    session = dev.attach(pid)
    done = {'scan': 0, 'end': False}

    def on_msg(msg, data):
        if msg.get('type') == 'send':
            p = msg['payload']
            if p.get('tag') == 'scan':
                print('[scan] %-24s hits=%s' % (p['what'], p['hits']))
                done['scan'] += 1
            elif p.get('tag') == 'done':
                done['end'] = True
        else:
            print('frida:', msg)

    script = session.create_script(JS)
    script.on('message', on_msg)
    script.load()
    for _ in range(120):
        if done['end']:
            break
        time.sleep(0.5)
    session.detach()
    print('done, scans=%d' % done['scan'])


if __name__ == '__main__':
    main()
