#!/usr/bin/env python3
"""诊断：打印 config.luac 里注入锚点的真实位置与上下文（ASCII 安全输出）。"""
import sys
import zipfile

apk = sys.argv[1] if len(sys.argv) > 1 else r'patched\jstm_solo.apk'
raw = zipfile.ZipFile(apk).read('assets/src/config.luac')
text = raw.decode('utf-8', errors='replace')

print('len(chars)=%d len(bytes)=%d' % (len(text), len(raw)))

for needle in ['injected by DSH private server',
               '---- DSH url observer',
               'local __dsh_srv_src = [====[',
               ']====]',
               'DSH_FALLBACK_BEGIN']:
    pos, allpos = 0, []
    while True:
        p = text.find(needle, pos)
        if p < 0:
            break
        allpos.append(p)
        pos = p + 1
    print('%-32s %s' % (needle, allpos))

for needle in ['injected by DSH private server', 'DSH_FALLBACK_BEGIN']:
    p = text.find(needle)
    if p >= 0:
        ctx = text[max(0, p - 40):p + 90]
        print('\n--- context @%d (%s) ---' % (p, needle))
        print(ascii(ctx))
