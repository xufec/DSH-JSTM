# -*- coding: utf-8 -*-
"""R146 验收：装备家族 `214xx` 剩余 6 条 + `21400` 重构回归。

判据：
  1. **`21400` 重构后仍正确**（改用全局 `encode_eqm_list`）
  2. `21414`（看他人装备）用**真实** `role_eqm` + `role_power`，且**与 `21400` 的 `role_eqm` 一致**
  3. `21407`/`21410`/`21412`/`21413`/`21404` 结构精确
  4. 全部用门禁权威解析器

用法： python tools/verify_equip_family.py
"""
import io
import os
import socket
import struct
import sys

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

    # ---- 21400 重构回归 + 取它的 role_eqm 条目数
    b0 = ask(21400)
    r0 = g.audit_body(sc['21400'], b0, 21400)
    n_role0 = struct.unpack_from('>H', b0, 0)[0]
    print('\n== 21400（重构后）==')
    print('  len=%d 消耗=%d err=%s role_eqm=%d' % (r0['len'], r0['consumed'], r0['err'], n_role0))
    a1 = r0['consumed'] == r0['len'] and not r0['err']
    print('  ★ 重构后仍结构精确 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 21414 看他人（=自己），role_eqm 应与 21400 一致
    b = ask(21414, struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1')
    r = g.audit_body(sc['21414'], b, 21414)
    off = 4 + 2 + 1                      # rid + srv_id
    n14 = struct.unpack_from('>H', b, off)[0]
    # ★ 每件 39 字节 —— 见 `encode_eqm_list` 的 16 个字段：
    #   4+4+4+1+1+2+2+4+4+2+1 + 2+2+2+2+2 = 39
    #   （第一版写死 66 ⇒ 一旦真有几件装备就偏移越界。）
    EQ_ITEM_BYTES = 39
    off += 2 + n14 * EQ_ITEM_BYTES
    pw = struct.unpack_from('>I', b, off)[0]
    print('\n== 21414 看他人（=自己）==')
    print('  len=%d 消耗=%d err=%s role_eqm=%d role_power=%d' % (r['len'], r['consumed'], r['err'], n14, pw))
    a2 = r['consumed'] == r['len'] and not r['err'] and n14 == n_role0
    print('  ★ 与 21400 的 role_eqm 条目数一致（%d）⇒ %s' % (n_role0, '✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 其余 5 条
    for c, body in ((21407, b''), (21410, b''), (21412, b''), (21413, b''),
                    (21404, struct.pack('>H', 0))):
        b = ask(c, body)
        r = g.audit_body(sc[str(c)], b, c)
        a = r['consumed'] == r['len'] and not r['err']
        print('  %d len=%d 消耗=%d err=%s ⇒ %s' % (c, r['len'], r['consumed'], r['err'], '✓' if a else '✗'))
        ok = ok and a

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
