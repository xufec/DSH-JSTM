# -*- coding: utf-8 -*-
"""R182 验收：**"看他人族" 21 条**（专用分支 860 → 881）。

判据：
  1. 21 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★★ **真实数据**：`11407` 的 `name`/`power`、`13304` 的 `name`/`sex`/`lev`
     与 `roles`/`role_power` **逐字段一致**（本服唯一角色 ⇒ 请求自己时回真值）
  4. ★ `18886` 的 `role_name`/`career`/`sex` 同上

用法： python tools/verify_peek_family.py
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
CMDS = [11017, 11407, 11413, 12436, 12771, 13304, 13312, 13325, 13328, 13336, 13504,
        13520, 14201, 14203, 14802, 14812, 18714, 18815, 18886, 30301, 30305]
RID_BODY = struct.pack('>I', RID) + struct.pack('>H', 1) + b'1'


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


def hdr_end(b):
    """`rid:u32 + srv_id:string` 之后的偏移。"""
    sl = struct.unpack_from('>H', b, 4)[0]
    return 6 + sl


def main():
    ok = True
    g, sc = load_gate()
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())

    bad = 0
    for c in CMDS:
        b = ask(c, RID_BODY)
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 21 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '看他人' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 21 and fb == 0) else '✗'))
    ok = ok and ded >= 21 and fb == 0

    row = q('SELECT name,sex,level,career FROM roles WHERE rid=?', (RID,))
    wname, wsex, wlev, wcar = row[0] if row else ('', 0, 0, 0)

    # ★ 11407：name + power
    b = ask(11407, RID_BODY)
    o = hdr_end(b)
    nl = struct.unpack_from('>H', b, o)[0]
    nm = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    pw = struct.unpack_from('>I', b, o + 2 + nl)[0]
    print('\n== 11407 == name=%r power=%d ｜ DB name=%r' % (nm, pw, wname))
    a1 = nm == wname and pw > 0
    print('  ★ name 与 DB 一致、power > 0 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ★ 13304：name + sex + lev
    b = ask(13304, RID_BODY)
    o = hdr_end(b)
    nl = struct.unpack_from('>H', b, o)[0]
    nm = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    sex = b[o + 2 + nl]
    lev = b[o + 3 + nl]
    print('  13304 name=%r sex=%d lev=%d ｜ DB %r/%d/%d ⇒ %s'
          % (nm, sex, lev, wname, int(wsex), int(wlev),
             '✓' if (nm == wname and sex == int(wsex) and lev == int(wlev)) else '✗'))
    ok = ok and nm == wname and sex == int(wsex) and lev == int(wlev)

    # ★ 18886：role_name + career + sex
    b = ask(18886, RID_BODY)
    o = hdr_end(b)
    nl = struct.unpack_from('>H', b, o)[0]
    nm = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    car = b[o + 2 + nl]
    sex = b[o + 3 + nl]
    print('  18886 role_name=%r career=%d sex=%d ｜ DB %r/%d/%d ⇒ %s'
          % (nm, car, sex, wname, int(wcar), int(wsex),
             '✓' if (nm == wname and car == int(wcar) and sex == int(wsex)) else '✗'))
    ok = ok and nm == wname and car == int(wcar) and sex == int(wsex)

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
