# -*- coding: utf-8 -*-
"""R139 验收：`13580`（膜拜列表）+ `12903`（伙伴榜）。

判据：
  1. `13580` 的 5 条**逐字段**与 `config_guild_tree_data.WorshipType` 一致
  2. `12903` 是"榜上有我"（my_ord=1、rank_list 1 条）
  3. 结构精确解析（门禁权威解析器）

用法： python tools/verify_worship_rank.py
"""
import io
import json
import os
import socket
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def ask(cmd, body=b''):
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(8.0)
    login(s)
    s.sendall(pack_frame(cmd, body))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        b = recv_exact(s, ln - 2)
        if rc == cmd:
            break
    s.close()
    return b


def load_gate():
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def main():
    ok = True
    g, sc = load_gate()
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_guild_tree_data.json'),
                         encoding='utf-8'))['WorshipType']

    b = ask(13580)
    r = g.audit_body(sc['13580'], b, 13580)
    n = struct.unpack_from('>H', b, 0)[0]
    print('\n== 13580 膜拜列表 ==')
    print('  len=%d 消耗=%d err=%s 条目=%d（配置 %d 项）'
          % (r['len'], r['consumed'], r['err'], n, len(cfg)))
    a1 = r['consumed'] == r['len'] and not r['err'] and n == len(cfg)
    off = 2
    same = True
    for k in sorted(cfg.keys(), key=lambda x: int(x)):
        h = cfg[k].get('hash', cfg[k])
        t = b[off]
        lv = struct.unpack_from('>H', b, off + 1)[0]
        e = struct.unpack_from('>I', b, off + 3)[0]
        u = b[off + 7]
        off += 8
        if (t, lv, e, u) != (h['type'], h['lev'], h['exp'], h['use']):
            same = False
            print('  ✗ [%s] 回包(%d,%d,%d,%d) != 配置(%d,%d,%d,%d)'
                  % (k, t, lv, e, u, h['type'], h['lev'], h['exp'], h['use']))
    print('  ★ 每条逐字段与配置一致 ⇒ %s' % ('✓' if same else '✗'))
    ok = ok and a1 and same

    b = ask(12903, bytes([1, 10, 0]))
    r = g.audit_body(sc['12903'], b, 12903)
    print('\n== 12903 伙伴榜 ==')
    print('  len=%d 消耗=%d err=%s my_ord=%d partner_bid=%d'
          % (r['len'], r['consumed'], r['err'], b[0], struct.unpack_from('>I', b, 5)[0]))
    a2 = r['consumed'] == r['len'] and not r['err'] and b[0] == 1
    print('  ★ 榜上有我（my_ord=1）+ 结构精确 ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
