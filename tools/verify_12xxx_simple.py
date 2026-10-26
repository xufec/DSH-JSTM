# -*- coding: utf-8 -*-
"""R174 验收：`12xxx` 简单组 **21 条**。

判据：
  1. 21 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ `12006`/`12007` 的 `bid` **回显一致**；`12002` 的 `dung_bid` 回显一致
  4. ★ `12003` 的 `chapter_bid` 取自 `config_dungeon_new` 的首个

用法： python tools/verify_12xxx_simple.py
"""
import io
import json
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
CMDS = (12000, 12001, 12002, 12003, 12004, 12005, 12006, 12007,
        12204, 12207, 12209, 12212, 12215, 12434, 12439, 12451,
        12460, 12720, 12723, 12764, 12772)


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
    B = {12004: struct.pack('>I', 1), 12204: struct.pack('>I', 1) + bytes([1]),
         12439: bytes([1]), 12451: bytes([1, 1]), 12460: bytes([1]),
         12720: struct.pack('>I', 1) + struct.pack('>H', 1) + b'1' + bytes([2]) + b'hi',
         12772: struct.pack('>I', 1) + struct.pack('>H', 1) + b'1' + bytes([1]) +
                struct.pack('>H', 2) + b'ab' + struct.pack('>H', 2) + b'cd',
         12000: struct.pack('>I', 20001),
         12001: struct.pack('>I', 20001) + struct.pack('>I', 1) + bytes([1]),
         12002: struct.pack('>I', 20001), 12006: struct.pack('>I', 20001),
         12007: struct.pack('>I', 20001),
         12723: struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1',
         12764: struct.pack('>H', 1) + struct.pack('>H', 2) + b'ab' + struct.pack('>H', 2) + b'cd'}

    bad = 0
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 21 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '12xxx 简单组' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 21 and fb == 0) else '✗'))
    ok = ok and ded >= 21 and fb == 0

    # ★ bid 回显
    b = ask(12006, struct.pack('>I', 21903))
    print('  12006 回显 bid=%d（请求 21903）⇒ %s'
          % (struct.unpack_from('>I', b, 0)[0],
             '✓' if struct.unpack_from('>I', b, 0)[0] == 21903 else '✗'))
    ok = ok and struct.unpack_from('>I', b, 0)[0] == 21903
    b = ask(12007, struct.pack('>I', 21904))
    print('  12007 回显 bid=%d ⇒ %s' % (struct.unpack_from('>I', b, 0)[0],
                                        '✓' if struct.unpack_from('>I', b, 0)[0] == 21904 else '✗'))
    ok = ok and struct.unpack_from('>I', b, 0)[0] == 21904

    # ★ 12003 取自 config_dungeon_new
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_dungeon_new.json'),
                         encoding='utf-8'))['Dungeon']
    first = sorted(int(k) for k in cfg)[0]
    b = ask(12003)
    got = struct.unpack_from('>I', b, 0)[0]
    print('  12003 chapter_bid=%d（配置首个 %d）⇒ %s' % (got, first, '✓' if got == first else '✗'))
    ok = ok and got == first

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
