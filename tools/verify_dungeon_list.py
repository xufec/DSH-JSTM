# -*- coding: utf-8 -*-
"""R147 验收：`21306`（副本列表）+ `21312`（一键扫荡列表）—— **34 条真实配置**。

判据：
  1. 条目数 == `config_dungeon_new.Dungeon` 的项数（**34**）
  2. `21306` 的每条 `bid`/`enter_count` 与配置**逐条一致**
  3. 全部用门禁权威解析器

用法： python tools/verify_dungeon_list.py
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
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_dungeon_new.json'),
                         encoding='utf-8'))['Dungeon']
    want = sorted((int(k), int(v.get('hash', v).get('count') or 0)) for k, v in cfg.items())

    b = ask(21306)
    r = g.audit_body(sc['21306'], b, 21306)
    n = struct.unpack_from('>H', b, 0)[0]
    got = []
    off = 2
    for _ in range(n):
        bid = struct.unpack_from('>I', b, off)[0]
        cnt = struct.unpack_from('>H', b, off + 4)[0]
        got.append((bid, cnt))
        off += 4 + 2 + 2 + 4 + 1        # bid+enter_count+buy_count+time+is_finish = 13
    print('\n== 21306 副本列表 ==')
    print('  len=%d 消耗=%d err=%s 条目=%d（配置 %d）' % (r['len'], r['consumed'], r['err'], n, len(cfg)))
    a1 = r['consumed'] == r['len'] and not r['err'] and n == len(cfg)
    a2 = got == want
    print('  ★ 条目数与配置一致 ⇒ %s' % ('✓' if a1 else '✗'))
    print('  ★ 逐条 bid/count 与配置一致 ⇒ %s' % ('✓' if a2 else '✗'))
    if not a2:
        for a, w in list(zip(got, want))[:4]:
            print('     回包 %s vs 配置 %s' % (a, w))
    ok = ok and a1 and a2

    b = ask(21312)
    r = g.audit_body(sc['21312'], b, 21312)
    n2 = struct.unpack_from('>H', b, 0)[0]
    ids = [struct.unpack_from('>I', b, 2 + 4 * i)[0] for i in range(n2)]
    print('\n== 21312 一键扫荡列表 ==')
    print('  len=%d 消耗=%d err=%s 条目=%d' % (r['len'], r['consumed'], r['err'], n2))
    a3 = r['consumed'] == r['len'] and not r['err'] and n2 == len(cfg) and ids == [x[0] for x in want]
    print('  ★ 34 条 bid 与配置一致 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
