# -*- coding: utf-8 -*-
"""R137 验收：`13331`（勇气值 / 魅力值 + 排名）。

判据：资产读**真实 DB**（用 `/DSH_ADMIN/setassets` 精确置值后核对）；
排名按 R130 的"**榜上有我**"（有值 ⇒ 1，为 0 ⇒ 0）。

用法： python tools/verify_courage.py
"""
import io
import os
import socket
import struct
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


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


def seta(qs):
    return urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/setassets?' + qs, timeout=8).read().decode('utf-8')


def load_gate():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def main():
    ok = True
    g, sc = load_gate()

    seta('courage=0&charm=0')
    b = ask(13331)
    r = g.audit_body(sc['13331'], b, 13331)
    cg = struct.unpack_from('>I', b, 0)[0]
    cm = struct.unpack_from('>I', b, 4)[0]
    print('\n== 13331（全 0）==')
    print('  len=%d 消耗=%d err=%s courage=%d charm=%d rank=(%d,%d)'
          % (r['len'], r['consumed'], r['err'], cg, cm, b[8], b[9]))
    a1 = r['consumed'] == r['len'] and not r['err'] and cg == 0 and cm == 0 and b[8] == 0 and b[9] == 0
    print('  结构精确 + 全 0 + rank=(0,0)（未上榜是真话）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    seta('courage=123&charm=456')
    b = ask(13331)
    r = g.audit_body(sc['13331'], b, 13331)
    cg = struct.unpack_from('>I', b, 0)[0]
    cm = struct.unpack_from('>I', b, 4)[0]
    print('\n== 13331（courage=123 charm=456）==')
    print('  courage=%d charm=%d rank=(%d,%d)' % (cg, cm, b[8], b[9]))
    a2 = cg == 123 and cm == 456 and b[8] == 1 and b[9] == 1
    print('  ★ 读的是真实资产 + 榜上有我（rank=1）⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    seta('courage=0&charm=0')      # 复原
    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
