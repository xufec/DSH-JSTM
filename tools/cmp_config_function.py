"""对比 1.4.9 与 1.4.11 的 config_function（功能开放表）。"""
import io
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402


def load(apk):
    z = zipfile.ZipFile(os.path.join(ROOT, apk))
    r = parse_bytes(z.read('assets/src/config/config_function.luac'))
    out = {}
    for p in r.protos:
        for w in p.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            v = kidx(p, (w >> 16) & 0xffff)
            if not isinstance(v, TableConst) or not v.hash:
                continue
            h = {str(k): vv for k, vv in v.hash}
            if 'id' in h:
                out[int(h['id'])] = h
    return out


a = load('anzbao/jstm.apk')            # 1.4.9
b = load('anzbao/jstm_142165.apk')     # 1.4.11
print('1.4.9  config_function 条目: %d' % len(a))
print('1.4.11 config_function 条目: %d' % len(b))
ka, kb = set(a), set(b)
print('共同 id: %d ｜ 仅 1.4.9: %s ｜ 仅 1.4.11: %s'
      % (len(ka & kb), sorted(ka - kb)[:12], sorted(kb - ka)[:12]))

# module_flag 集合对比
fa = {str(h.get('module_flag')) for h in a.values()}
fb = {str(h.get('module_flag')) for h in b.values()}
print('module_flag 仅 1.4.9: %s' % sorted(fa - fb)[:10])
print('module_flag 仅 1.4.11: %s' % sorted(fb - fa)[:10])

# is_open 统计
oa = sum(1 for h in a.values() if int(h.get('is_open') or 0) == 1)
ob = sum(1 for h in b.values() if int(h.get('is_open') or 0) == 1)
print('is_open=1 的数量: 1.4.9=%d  1.4.11=%d' % (oa, ob))
