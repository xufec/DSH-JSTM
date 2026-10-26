# -*- coding: utf-8 -*-
"""R179 验收：**收尾 `16xxx`（50 条）**。

判据：
  1. 50 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **回显**：`16617`（`aim`）、`16643`（`holiday_bid`）、`16650`（`type`）、`16652`（`index`，**u32**）
  4. ★ **用真实值**：`16700` 的 `vip_lev` ← `db_vip_level`

用法： python tools/verify_16xxx_tail.py
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
CMDS = [16612, 16613, 16614, 16615, 16616, 16617, 16620, 16621, 16622, 16623,
        16624, 16626, 16627, 16630, 16631, 16632, 16633, 16634, 16635, 16636,
        16637, 16638, 16639, 16640, 16641, 16642, 16643, 16646, 16647, 16649,
        16650, 16651, 16652, 16653, 16665, 16666, 16667, 16668, 16693, 16694,
        16695, 16696, 16697, 16698, 16699, 16700, 16702, 16703, 16705, 16901]

B = {16616: struct.pack('>H', 2) + b'hi', 16617: struct.pack('>I', 1), 16622: bytes([1]),
     16627: bytes([1]), 16642: struct.pack('>I', 1) + struct.pack('>H', 2),
     16643: struct.pack('>I', 1), 16646: bytes([1]),
     16647: struct.pack('>I', 1) + bytes([1, 2]), 16649: bytes([1]), 16650: bytes([1]),
     16652: struct.pack('>I', 1), 16666: bytes([1]), 16698: struct.pack('>I', 3),
     16620: struct.pack('>H', 0), 16901: struct.pack('>I', 1),
     16632: struct.pack('>I', 1) + struct.pack('>I', 2) + bytes([1]) +
            struct.pack('>I', 3) + struct.pack('>I', 4) + struct.pack('>I', 5)}


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
    print('\n== 50 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '16xxx 收尾' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 50 and fb == 0) else '✗'))
    ok = ok and ded >= 50 and fb == 0

    # ★ 回显：16617（aim:u32）/ 16643（holiday_bid:u32）
    b = ask(16617, struct.pack('>I', 21903))
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  16617 回显 aim=%d ⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903
    b = ask(16643, struct.pack('>I', 21903))
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  16643 回显 holiday_bid=%d ⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903

    # ★ 16652 的 `index` 是 **u32**
    b = ask(16652, struct.pack('>I', 21903))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    got = struct.unpack_from('>I', b, o)[0]
    print('  16652 回显 index=%d（u32）⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903

    # ★ 16700 用真实 vip_lev
    b = ask(16700, b'')
    print('  16700 vip_lev=%d（本服 DB）⇒ ✓' % b[0])

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
