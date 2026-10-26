"""对比 1.4.9 与 1.4.11 的关键角色消息规格（含 lev 的那几条）。

动机：功能按钮按 `config_function.open_lev` 做等级门禁。
若客户端**认为等级为 0/异常**，所有功能按钮都会被隐藏 —— 且**不报错**，
与"能进主城、功能 UI 为空、日志无异常"完全吻合。
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

WANT = {10301, 10302, 10303, 10304, 10305, 10306}
APKS = [('1.4.9', 'anzbao/jstm.apk'), ('1.4.11', 'anzbao/jstm_142165.apk')]


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
                if kind and cmd in WANT:
                    out[(cmd, kind)] = ' | '.join(arr)
    return out


data = {}
for label, apk in APKS:
    data[label] = specs(apk)
    print('%s: 命中 %d 条' % (label, len(data[label])))

allk = sorted(set(data['1.4.9']) | set(data['1.4.11']))
print()
print('%-10s %s' % ('key', '是否一致'))
print('-' * 70)
for k in allk:
    a = data['1.4.9'].get(k, '(无)')
    b = data['1.4.11'].get(k, '(无)')
    flag = '一致' if a == b else '★ 不同'
    print('%s/%s  %s' % (k[1], k[0], flag))
    if a != b:
        print('   1.4.9 : %s' % a[:150])
        print('   1.4.11: %s' % b[:150])
