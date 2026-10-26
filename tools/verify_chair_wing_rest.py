# -*- coding: utf-8 -*-
"""R142 验收：座椅 + 翅膀的剩余 12 条（`11602`/`20803`-`20809`/`11604`-`11607`）。

判据（按 R134 的处置细则）：
  · **真读**：`11602` ⇒ `wing_id` 与 `role_wing` 一致
  · **回显**：`20805`/`20809`/`11606`/`11607` ⇒ 参数原样回
  · **只校验**：`20803`/`20804`/`20806`/`20807`/`20808`/`11604`/`11605` ⇒ 结构正确 + `code` 如实
  · 全部用门禁权威解析器做结构断言

用法： python tools/verify_chair_wing_rest.py
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
    urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/wing?wing_id=8801&star=6&color=2&power=777',
        timeout=8).read()

    # 1) 真读：11602
    b = ask(11602)
    r = g.audit_body(sc['11602'], b, 11602)
    wid = struct.unpack_from('>I', b, 3)[0]
    print('\n== 11602（真读）==')
    print('  len=%d 消耗=%d err=%s wing_id=%d' % (r['len'], r['consumed'], r['err'], wid))
    a1 = r['consumed'] == r['len'] and not r['err'] and wid == 8801
    print('  ★ wing_id 与 role_wing 一致（8801）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # 2) 回显类
    echo = [(20805, struct.pack('>H', 101), 'surface_id', 'H', 101),
            (20809, bytes([1]), 'flag', 'B', 1),
            (11607, struct.pack('>H', 202), 'surface_id', 'H', 202)]
    for c, body, nm, fmt, want in echo:
        b = ask(c, body)
        r = g.audit_body(sc[str(c)], b, c)
        # ★ `SC{code, msg:string, <字段>}` ⇒ 该字段在 `1 + 2 + len(msg)` 处
        #   —— 别漏了 string 的**长度前缀 2 字节**（第一版就漏了，回显读成 0）。
        off = 1 + 2 + struct.unpack_from('>H', b, 1)[0]
        got = struct.unpack_from('>' + fmt, b, off)[0]
        a = r['consumed'] == r['len'] and not r['err'] and got == want
        print('  %d 回显 %s=%d（期望 %d）⇒ %s' % (c, nm, got, want, '✓' if a else '✗'))
        ok = ok and a

    # 3) 11606：animate 无配置字段 ⇒ 回 0，但结构正确
    b = ask(11606, struct.pack('>H', 101))
    r = g.audit_body(sc['11606'], b, 11606)
    off = 1 + 2 + struct.unpack_from('>H', b, 1)[0]
    an = struct.unpack_from('>H', b, off)[0]
    a = r['consumed'] == r['len'] and not r['err'] and an == 0
    print('  11606 animate=%d（无配置字段 ⇒ 0）⇒ %s' % (an, '✓' if a else '✗'))
    ok = ok and a

    # 4) 只校验类
    val = [(20803, struct.pack('>I', 21903)), (20804, struct.pack('>I', 21903)),
           (20806, struct.pack('>I', 25870)), (20807, struct.pack('>I', 25870)),
           (11604, struct.pack('>I', 25870)), (11605, struct.pack('>I', 25870))]
    for c, body in val:
        b = ask(c, body)
        r = g.audit_body(sc[str(c)], b, c)
        a = r['consumed'] == r['len'] and not r['err'] and b[0] == 1
        print('  %d（只校验）code=%d ⇒ %s' % (c, b[0], '✓' if a else '✗'))
        ok = ok and a
    # 无效值 ⇒ code=0
    b = ask(20803, struct.pack('>I', 0))
    a = b[0] == 0
    print('  20803 无效 ⇒ code=%d ⇒ %s' % (b[0], '✓' if a else '✗'))
    ok = ok and a

    # 5) 20808 批量
    b = ask(20808, struct.pack('>I', 1) + struct.pack('>H', 0))
    r = g.audit_body(sc['20808'], b, 20808)
    a = r['consumed'] == r['len'] and not r['err']
    print('  20808（批量）len=%d err=%s ⇒ %s' % (r['len'], r['err'], '✓' if a else '✗'))
    ok = ok and a

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
