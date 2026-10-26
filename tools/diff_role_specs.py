"""逐字段 diff 1.4.9 与 1.4.11 的 sc/10301 与 sc/10302。"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

WANT = {10301: 'sc', 10302: 'sc'}


def specs(apk):
    z = zipfile.ZipFile(os.path.join(ROOT, apk))
    out = {}
    for n in z.namelist():
        if 'cmd_resolve_' not in n or not n.endswith('.luac'):
            continue
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        for p in r.protos:
            for sp, w in enumerate(p.bc):
                if OPS[w & 0xff] != 'TDUP':
                    continue
                v = kidx(p, (w >> 16) & 0xffff)
                if not (isinstance(v, TableConst) and v.array):
                    continue
                arr = [x for x in v.array if isinstance(x, str)]
                if not arr:
                    continue
                kind = cmd = None
                for j in range(max(0, sp - 16), sp):
                    o = OPS[p.bc[j] & 0xff]
                    d = (p.bc[j] >> 16) & 0xffff
                    if o == 'KSTR':
                        vv = kidx(p, d)
                        if vv in ('cs', 'sc'):
                            kind = vv
                    elif o == 'KSHORT':
                        cmd = d
                if kind and cmd in WANT and kind == WANT[cmd]:
                    out[cmd] = ' | '.join(arr)
    return out


a = specs('anzbao/jstm.apk')
b = specs('anzbao/jstm_142165.apk')

for cmd in (10301, 10302):
    fa = [x.strip() for x in a.get(cmd, '').split('|')]
    fb = [x.strip() for x in b.get(cmd, '').split('|')]
    print('=== sc/%d  1.4.9 %d 字段 ｜ 1.4.11 %d 字段 ===' % (cmd, len(fa), len(fb)))
    for i in range(max(len(fa), len(fb))):
        x = fa[i] if i < len(fa) else '(无)'
        y = fb[i] if i < len(fb) else '(无)'
        mark = '  ' if x == y else '★ '
        if x != y:
            print('%s[%2d] 1.4.9=%-28s 1.4.11=%s' % (mark, i, x, y))
    if fa == fb:
        print('  （字段序列完全一致）')
    print()
