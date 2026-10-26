# -*- coding: utf-8 -*-
"""R186 验收：**`18xxx` 批次 34 条**（专用分支 1002 → 1036）。

判据：
  1. 34 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **真实角色**：`18002` 的 `name` 与 DB 一致
  4. ★ **回显 + 校验**：`18001` 的 `rid`/`srv` 与请求一致

★ 本批 `18604` 的 SC 有 **10 个字段**（我打印时截断只看到 6 个）⇒ 纪律第 29 条第 4 次兑现。

用法： python tools/verify_18xxx_b.py
"""
import io
import os
import socket
import sqlite3
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')

CMDS = [18001, 18002, 18003, 18004, 18007, 18011, 18012, 18026, 18100, 18101, 18200,
        18201, 18301, 18303, 18308, 18309, 18311, 18313, 18315, 18317, 18318, 18319,
        18322, 18401, 18402, 18403, 18502, 18601, 18604, 18606, 18608, 18611, 18612, 18613]
B = {18001: bytes([1]) + struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1',
     18007: bytes([1]), 18011: struct.pack('>I', 1), 18012: struct.pack('>I', 1),
     18026: struct.pack('>I', 1) + bytes([1]), 18101: bytes([1]),
     18311: bytes([1]) + struct.pack('>H', 2) + b'ab', 18322: struct.pack('>I', 1),
     18401: bytes([1]), 18403: bytes([1]), 18502: struct.pack('>I', 1),
     18606: struct.pack('>h', 1)}


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


def q(sql, args=()):
    c = sqlite3.connect(DB)
    try:
        r = c.execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        r = []
    c.close()
    return r


def load_gate():
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def rd_str(b, o):
    n = struct.unpack_from('>H', b, o)[0]
    return b[o + 2:o + 2 + n].decode('utf-8', 'replace'), o + 2 + n


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
    print('\n== 34 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '18xxx-B（' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 34 and fb == 0) else '✗'))
    ok = ok and ded >= 34 and fb == 0

    row = q('SELECT name FROM roles WHERE rid=1001')
    wname = row[0][0] if row else ''

    # ★ 18002：{star:u8, rid:u32, srv:string, name:string}
    b = ask(18002)
    star = b[0]
    rid = struct.unpack_from('>I', b, 1)[0]
    _srv, o = rd_str(b, 5)
    nm, o = rd_str(b, o)
    print('\n  18002 star=%d rid=%d srv=%r name=%r ⇒ %s'
          % (star, rid, _srv, nm, '✓' if (rid == 1001 and nm == wname) else '✗'))
    ok = ok and rid == 1001 and nm == wname

    # ★ 18001：回显 rid/srv
    b = ask(18001, B[18001])
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    o += 1 + 1                      # star + rest_times
    got_rid = struct.unpack_from('>I', b, o)[0]
    o += 4
    got_srv, o = rd_str(b, o)
    print('  18001 回显 rid=%d srv=%r ⇒ %s'
          % (got_rid, got_srv, '✓' if (got_rid == 1001 and got_srv == '1') else '✗'))
    ok = ok and got_rid == 1001 and got_srv == '1'

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
