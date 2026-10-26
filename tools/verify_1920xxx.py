# -*- coding: utf-8 -*-
"""R187 验收：**`20xxx` + `19xxx` 共 69 条**（专用分支 1036 → 1105）。

★★ 本批的**方法要点**（吸取 R179–R186 的 4 次"截断"教训）：
   1. SC 全部取自**权威解析器**（纪律第 28 条）
   2. 打印时**带 `n=`**（纪律第 29 条）
   3. ★ **打底用 `_build_default_sc(cmd, 1, '')`** —— 按权威 SC **递归**生成
      ⇒ **结构不可能越界**（本会话最稳的一条路）
   4. 对"回显型"额外发真值

判据：
  1. 69 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **回显**：`19002`（`id`）、`19120`（`surface_id`）、`20310`（`id`/`msrv_id`）
  4. ★ **真实值**：`19509` 的 `second_name` = DB 角色名

用法： python tools/verify_1920xxx.py
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
RID = 1001

B = {19002: struct.pack('>I', 21903), 19120: struct.pack('>H', 21903),
     19199: struct.pack('>I', 21903), 19516: struct.pack('>I', 21903),
     19522: bytes([7]), 19601: struct.pack('>I', 21903) + bytes([1, 2]),
     19604: bytes([7]), 20201: struct.pack('>I', 21903), 20203: b'',
     20212: b'', 20303: b'',
     20310: struct.pack('>I', 21903) + struct.pack('>H', 1) + b'1',
     20505: struct.pack('>I', 21903), 20707: struct.pack('>H', 1) + b'a',
     20725: bytes([7]), 19509: b'', 19527: b'', 19528: b'', 19101: b''}


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
    gaps = sorted(int(x.strip()) for x in
                  open(os.path.join(ROOT, 'analysis', '1.4.9', '_unhandled_cs_sc.txt'),
                       encoding='utf-8') if x.strip().isdigit())
    CMDS = [c for c in gaps if 19000 <= c < 21000]
    print('\n  ★ 本批 %d 条' % len(CMDS))
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())

    bad = 0
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== %d 条结构精确性 ==  失败 %d 条 ⇒ %s'
          % (len(CMDS), bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '19-20xxx（' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= len(CMDS) and fb == 0) else '✗'))
    ok = ok and ded >= len(CMDS) and fb == 0

    # ★ 回显：19002（{code,msg,id,dtime}）
    b = ask(19002, struct.pack('>I', 21903))
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  19002 回显 id=%d ⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903

    # ★ 回显：20310（{code,msg,id,msrv_id}）
    b = ask(20310, B[20310])
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  20310 回显 id=%d ⇒ %s' % (got, '✓' if got == 21903 else '✗'))
    ok = ok and got == 21903

    # ★ 真实值：19509（{code,msg,second_name}）
    row = q('SELECT name FROM roles WHERE rid=?', (RID,))
    wname = row[0][0] if row else ''
    b = ask(19509)
    m = struct.unpack_from('>H', b, 1)[0]
    nm, o = rd_str(b, 1 + 2 + m)
    print('  19509 second_name=%r（DB %r）⇒ %s'
          % (nm, wname, '✓' if nm == wname else '✗'))
    ok = ok and nm == wname

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
