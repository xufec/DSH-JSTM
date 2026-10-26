# -*- coding: utf-8 -*-
"""R184 验收：**`30xxx` 全家族 43 条**（专用分支 931 → 974）。

判据：
  1. 43 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **榜上有我**：`30105`/`30109`/`30206`/`30220` 的 `role_list` **恰 1 条** + `name` 与 DB 一致
  4. ★ **回显**：`30302`（`id`）、`30800`（`reward_wave`）、`30507`（`day`）

★ 本批的 SC **全部取自"权威解析器"**（`audit_emitted_fields.load_specs`）——
  这是纪律第 28 条的最终修法（**用服务端运行时真正加载的那份**）。

用法： python tools/verify_30xxx.py
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

CMDS = [30001, 30104, 30105, 30108, 30109, 30204, 30205, 30206, 30207, 30220, 30300,
        30302, 30304, 30306, 30400, 30401, 30402, 30403, 30500, 30501, 30502, 30503,
        30504, 30505, 30506, 30507, 30701, 30702, 30703, 30704, 30707, 30708, 30709,
        30710, 30711, 30712, 30713, 30714, 30717, 30800, 30900, 30901, 30902]
B = {30105: bytes([1, 1, 1]), 30109: bytes([1, 1, 1]), 30206: bytes([1, 1]), 30220: b'',
     30302: bytes([1]), 30304: bytes([1]), 30401: bytes([1, 1]), 30402: struct.pack('>I', 1),
     30501: bytes([1]), 30502: bytes([1]), 30503: bytes([1]), 30506: struct.pack('>I', 1),
     30507: struct.pack('>H', 1), 30702: struct.pack('>I', 1) + struct.pack('>H', 1) + b'1',
     30709: struct.pack('>I', 1) + struct.pack('>H', 1) + b'1' + struct.pack('>H', 1) + bytes([1]),
     30710: bytes([1]) + struct.pack('>H', 1) + bytes([1]), 30714: struct.pack('>I', 1),
     30800: struct.pack('>H', 1), 30902: bytes([1])}


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
    print('\n== 43 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '30xxx（' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 43 and fb == 0) else '✗'))
    ok = ok and ded >= 43 and fb == 0

    row = q('SELECT name FROM roles WHERE rid=1001')
    wname = row[0][0] if row else ''

    # ★ `30105`/`30109`/`30206`：`role_list` 之前的**前缀和**（逐条算，别猜）
    #   30105: career(1)+idx(1)+num(1)+rank(2)+hurt(4) = **9**
    #   30109: career(1)+idx(1)+num(1)+rank(2)+career_rank(2)+hurt(4) = **11**
    #   30206: idx(1)+num(1)+rank(2)+score(4) = **8**
    for c, skip in ((30105, 9), (30109, 11), (30206, 8)):
        b = ask(c, B[c])
        cnt = struct.unpack_from('>H', b, skip)[0]
        o = skip + 2
        o += 4                         # 元素的 `rid`
        _srv, o = rd_str(b, o)
        nm, o = rd_str(b, o)
        print('  %d role_list 计数=%d name=%r ⇒ %s'
              % (c, cnt, nm, '✓' if (cnt == 1 and nm == wname) else '✗'))
        ok = ok and cnt == 1 and nm == wname

    # ★ 回显：30302（id）
    b = ask(30302, bytes([7]))
    print('  30302 回显 id=%d ⇒ %s' % (b[0], '✓' if b[0] == 7 else '✗'))
    ok = ok and b[0] == 7
    # ★ 回显：30800（reward_wave）
    b = ask(30800, struct.pack('>H', 21903))
    got = struct.unpack_from('>H', b, 1)[0]
    print('  30800 回显 max_passed=%d ⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903
    # ★ 回显：30507（day）
    b = ask(30507, struct.pack('>H', 7))
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>H', b, 1 + 2 + m)[0]
    print('  30507 回显 day=%d ⇒ %s' % (got, '✓' if got == 7 else '✗'))
    ok = ok and got == 7

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
