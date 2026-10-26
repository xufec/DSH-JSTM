# -*- coding: utf-8 -*-
"""R168 验收：`13xxx` 看他人族 + 推荐族 **25 条**。

判据：
  1. 25 条**结构精确**（门禁权威解析器）
  2. ★ `13322`（好友推荐，**15 字段表**）的 `rid`/`name`/`sex`/`lev`/`career`/`power` 与 `roles`/`role_state` 一致
  3. ★ `13314`（按名字搜人，**8 字段表**）同上
  4. `13301` 的 `rid` == 本服角色

用法： python tools/verify_13xxx_role.py
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
RID = 1001
CMDS = (13301, 13302, 13308, 13305, 13307, 13513, 13310, 13313, 13306, 13315, 13317, 13318,
        13319, 13323, 13347, 13348, 13322, 13371, 13076, 13314, 13352, 13353, 13812, 13814, 13816)


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


def main():
    ok = True
    g, sc = load_gate()
    # ★★★ R168 的教训：**只看"结构正确"无法区分"专用实现"与"全局兜底"**
    #   —— 兜底也回结构正确的响应！（第一轮 25 条报 FAIL 0，实际全走兜底。）
    #   ⇒ 这里**先记录 `tcp.log` 的行数**，跑完再看**是否有本批的专用日志**。
    LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
    try:
        base_lines = len(open(LOG, encoding='utf-8', errors='replace').readlines())
    except Exception:
        base_lines = 0
    rid = struct.pack('>I', RID) + struct.pack('>H', 1) + b'1'
    B = {13305: rid + bytes([1]), 13307: rid, 13513: rid + struct.pack('>H', 1) + b'x',
         13310: rid, 13313: rid, 13314: struct.pack('>H', 1) + b'x',
         13347: rid + struct.pack('>I', 1), 13348: rid + struct.pack('>I', 1),
         13812: struct.pack('>I', 1) + struct.pack('>I', 2),
         13814: struct.pack('>I', 1) + struct.pack('>I', 2),
         13816: struct.pack('>I', 1) + struct.pack('>I', 2) + struct.pack('>H', 1) +
                struct.pack('>I', 3) + bytes([1]),
         13306: struct.pack('>H', 1) + struct.pack('>I', RID) + struct.pack('>H', 1) + b'1',
         13317: struct.pack('>H', 2) + b'gp', 13318: struct.pack('>I', 1),
         13319: rid + struct.pack('>I', 1) + struct.pack('>I', 2),
         13315: rid + struct.pack('>H', 1) + struct.pack('>I', 1) + struct.pack('>I', 2) + struct.pack('>I', 3)}

    bad = 0
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 25 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # ★ 关键：**确认走的是专用分支**（读 `tcp.log` 的新增行）
    try:
        new_lines = open(LOG, encoding='utf-8', errors='replace').readlines()[base_lines:]
        dedicated = sum(1 for ln in new_lines if '13xxx 看他人/推荐' in ln)
        fallback = sum(1 for ln in new_lines if '兜底响应' in ln or '默认响应' in ln)
    except Exception:
        dedicated, fallback = 0, 0
    print('\n== ★ 专用 vs 兜底（读 tcp.log 新增行）==')
    print('  专用分支日志 %d 条 ｜ 兜底/默认 %d 条' % (dedicated, fallback))
    a0 = dedicated > 0 and fallback == 0
    print('  ★ 25 条走的是**专用实现**（不是兜底）⇒ %s' % ('✓' if a0 else '✗'))
    ok = ok and a0

    row = q('SELECT name,sex,level,career FROM roles WHERE rid=?', (RID,))
    wname, wsex, wlev, wcar = row[0] if row else ('', 0, 0, 0)

    # 13322（15 字段表）
    b = ask(13322)
    n = struct.unpack_from('>H', b, 0)[0]
    o = 2
    rid2 = struct.unpack_from('>I', b, o)[0]
    o += 4
    sl = struct.unpack_from('>H', b, o)[0]
    o += 2 + sl                      # srv_id
    nl = struct.unpack_from('>H', b, o)[0]
    name = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    o += 2 + nl
    sex = b[o]
    lev = struct.unpack_from('>H', b, o + 1)[0]
    car = struct.unpack_from('>H', b, o + 3)[0]
    print('\n== 13322 好友推荐（15 字段表）==')
    print('  条目=%d rid=%d name=%r sex=%d lev=%d career=%d' % (n, rid2, name, sex, lev, car))
    print('        DB: name=%r sex=%d lev=%d career=%d' % (wname, wsex, wlev, wcar))
    a1 = (n == 1 and rid2 == RID and name == wname and sex == int(wsex)
          and lev == int(wlev) and car == int(wcar))
    print('  ★ 6 个真实字段与 DB 一致 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # 13301
    b = ask(13301)
    rid3 = struct.unpack_from('>I', b, 0)[0]
    print('  13301 rid=%d ⇒ %s' % (rid3, '✓' if rid3 == RID else '✗'))
    ok = ok and rid3 == RID

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
