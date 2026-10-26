#!/usr/bin/env python3
"""Definitive raw byte scan: which APK entry contains each candidate string?

Earlier scans were ambiguous because the console mangles CJK.  This writes a
hex-labelled report to tools/_sdk_string_scan.txt so nothing depends on the
console codepage.

usage: python tools/analyze_sdk_scan.py [apk]
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'anzbao', 'jstm_142165.apk')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sdk_string_scan.txt')

# label -> chinese text
NEEDLES = {
    'full_msg': '初始化失败,请检查网络',
    'full_msg_fw': '初始化失败，请检查网络',
    'init_fail': '初始化失败',
    'check_net': '请检查网络',
    'reconnect': '重新连接',
    'exit_game': '退出游戏',
    'retry': '重试',
    'tip': '提示',
    'net_err': '网络异常',
    'sdk_inited': '超级SDK初始化失败',
    'init_in': 'ewan_init_in',
    'sdkCallFunc': 'sdkCallFunc',
    'device_class': 'cc/Device',
}


def main():
    z = zipfile.ZipFile(APK)
    lines = ['apk=%s' % APK, 'entries=%d' % len(z.namelist()), '']
    for name in z.namelist():
        try:
            data = z.read(name)
        except Exception as e:
            lines.append('!! %s: %r' % (name, e))
            continue
        hits = []
        for label, text in NEEDLES.items():
            for enc, tag in (('utf-8', 'u8'), ('utf-16-le', 'u16')):
                nb = text.encode(enc)
                idxs, i = [], data.find(nb)
                while i >= 0 and len(idxs) < 6:
                    idxs.append(i)
                    i = data.find(nb, i + 1)
                if idxs:
                    hits.append('%s/%s=%s' % (label, tag, idxs))
        if hits:
            lines.append('%-46s %s' % (name, '  '.join(hits)))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', OUT, len(lines), 'lines')
    for ln in lines[:200]:
        print(ln)


if __name__ == '__main__':
    main()
