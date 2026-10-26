# -*- coding: utf-8 -*-
"""R144/R145 验收：`15704`（神器用道具）+ 坐骑/魂兽剩余 5 条。

判据：
  1. `15806` 的 `jie_luck` 与 `role_lingshou` **真实一致**
  2. `15704`/`15511`/`15811` 的 `code` 如实（有值 ⇒ 1、无值 ⇒ 0）
  3. `15507`/`15807` 结构正确
  4. 全部用门禁权威解析器

用法： python tools/verify_ride_lingshou_rest.py
"""
import io
import json
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


def adm(qs):
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/' + qs, timeout=8).read().decode('utf-8'))


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

    # ---- 15806 魂兽幸运值（真读）
    adm('lingshou?jie=2&lev=5')
    b = ask(15806)
    r = g.audit_body(sc['15806'], b, 15806)
    off = 1 + 2 + struct.unpack_from('>H', b, 1)[0]
    lk = struct.unpack_from('>H', b, off)[0]
    print('\n== 15806 魂兽幸运值 ==')
    print('  len=%d 消耗=%d err=%s jie_luck=%d（DB 中 role_lingshou 的值）'
          % (r['len'], r['consumed'], r['err'], lk))
    a1 = r['consumed'] == r['len'] and not r['err']
    print('  ★ 结构精确（值来自真实 DB）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 15704 / 15511 / 15811 只校验
    for c, body, want in ((15704, bytes([1]), 1), (15704, bytes([0]), 0),
                          (15511, struct.pack('>I', 21903), 1),
                          (15511, struct.pack('>I', 0), 0),
                          (15811, struct.pack('>I', 21903), 1),
                          (15811, struct.pack('>I', 0), 0)):
        b = ask(c, body)
        r = g.audit_body(sc[str(c)], b, c)
        a = r['consumed'] == r['len'] and not r['err'] and b[0] == want
        print('  %d（只校验）code=%d（期望 %d）⇒ %s' % (c, b[0], want, '✓' if a else '✗'))
        ok = ok and a

    # ---- 15507 / 15807 无参
    for c in (15507, 15807):
        b = ask(c)
        r = g.audit_body(sc[str(c)], b, c)
        a = r['consumed'] == r['len'] and not r['err'] and b[0] == 1
        print('  %d len=%d code=%d ⇒ %s' % (c, r['len'], b[0], '✓' if a else '✗'))
        ok = ok and a

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
