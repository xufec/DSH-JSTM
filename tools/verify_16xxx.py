# -*- coding: utf-8 -*-
"""R178 验收：`16xxx` **22 条**。

判据：
  1. 22 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **回显**：`16401`（`bid`）、`16202`（`mon_bid`）、`16502`（`type`+`val`）
  4. ★ `16301` 的 `rid` 回显 + 校验是本服角色

用法： python tools/verify_16xxx.py
"""
import io
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
RID = 1001
CMDS = (16000, 16001, 16002, 16100, 16101, 16102, 16110, 16111, 16112, 16202,
        16300, 16301, 16302, 16303, 16304, 16401, 16404, 16501, 16502, 16604, 16610, 16611)

B = {16102: struct.pack('>I', 1) + bytes([2]),
     16112: struct.pack('>I', 1) + struct.pack('>H', 1) + struct.pack('>H', 2),
     16202: struct.pack('>I', 21903), 16300: struct.pack('>I', 1),
     16301: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1',
     16401: struct.pack('>I', 21903), 16404: struct.pack('>I', 1),
     16501: bytes([1]), 16502: bytes([1]) + struct.pack('>H', 5),
     16302: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1',
     16604: struct.pack('>I', 1) + struct.pack('>I', 1) + struct.pack('>I', 1)}


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
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())

    bad = 0
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 22 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '16xxx' in ln and '<<' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 22 and fb == 0) else '✗'))
    ok = ok and ded >= 22 and fb == 0

    # ★ 回显：16401 / 16202
    b = ask(16401, struct.pack('>I', 21903))
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  16401 回显 bid=%d ⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903
    b = ask(16202, struct.pack('>I', 21903))
    got = struct.unpack_from('>I', b, 0)[0]
    print('  16202 回显 mon_bid=%d ⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903

    # ★ 16502 回显 type + val（★ 布局：tips:u16(0-1) + msg:string(2..) + type:u8 + val:u16）
    b = ask(16502, bytes([7]) + struct.pack('>H', 55))
    m = struct.unpack_from('>H', b, 2)[0]
    o = 2 + 2 + m
    ty = b[o]
    val = struct.unpack_from('>H', b, o + 1)[0]
    print('  16502 回显 type=%d val=%d ⇒ %s' % (ty, val, '✓' if (ty == 7 and val == 55) else '✗'))
    ok = ok and ty == 7 and val == 55

    # ★ 16301 rid 回显 + 校验
    b = ask(16301, struct.pack('>I', RID) + struct.pack('>H', 1) + b'1')
    got = struct.unpack_from('>I', b, 4)[0]       # water_count(2) + code(1) + … → rid 在 3?
    # 布局：water_count:u16(0) + code:u8(2) + rid:u32(3)
    got = struct.unpack_from('>I', b, 3)[0]
    print('  16301 回显 rid=%d ⇒ %s' % (got, '✓' if got == RID else '✗'))
    ok = ok and got == RID
    b0 = ask(16301, struct.pack('>I', 9999) + struct.pack('>H', 1) + b'1')
    print('  16301 他人 rid ⇒ code=%d ⇒ %s' % (b0[2], '✓' if b0[2] == 0 else '✗'))
    ok = ok and b0[2] == 0

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
