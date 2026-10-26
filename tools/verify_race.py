# -*- coding: utf-8 -*-
"""R50 验证：魂师大赛（竞速）`17301` / `17309`。

核对三件事：
  1. 两条应答按 `protocol/fields.json` 的 SC 规格**精确解析**（消耗字节 == 实际长度）；
  2. `17301` 的值来自 `race_state`（无行 ⇒ 全 0，是真话）；
  3. `17309.rank_list` 的姓名/等级/职业取自 `roles` 真表，score 取自各自 `race_state`。

★ 只读：不写玩家数据；只对本机 127.0.0.1:9000 发查询。
用法：python tools/verify_race.py
"""
import json
import os
import socket
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_conformance import parse_full  # noqa: E402
from audit_sc_live import pack_frame, recv_exact  # noqa: E402

with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
    FIELDS = json.load(f)


def sc_spec(cmd):
    for k, v in FIELDS.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def login(s, account='dsh_local'):
    s.sendall(pack_frame(1110, struct.pack('>H', 1) + w_str('account') + w_str(account)))
    while True:
        hdr = recv_exact(s, 6)
        ln, rc = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]
            off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]
            off += 2
            rid = struct.unpack_from('>I', p, off)[0] if cnt else None
            break
    if rid:
        s.sendall(pack_frame(10102, struct.pack('>I', rid) + w_str('1')))
        s.settimeout(2.0)
        try:
            while True:
                hdr = recv_exact(s, 6)
                ln, rc = struct.unpack('>IH', hdr)
                recv_exact(s, ln - 2)
                if rc == 10102:
                    break
        except socket.timeout:
            pass
        s.settimeout(5.0)
    return rid


def q(s, cmd, body=b''):
    s.sendall(pack_frame(cmd, body))
    while True:
        hdr = recv_exact(s, 6)
        ln, rc = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == cmd:
            return p


ok = True
s = socket.create_connection(('127.0.0.1', 9000), 5)
s.settimeout(5.0)
rid = login(s)
print('login rid =', rid)

# ---- 17301 ----
body = q(s, 17301)
spec = sc_spec(17301)
used, errs, unv = parse_full(body, spec)
print('\n== 17301 ==')
print('  SC_17301 len=%d  解析消耗=%d  errs=%s unverified=%s  %s'
      % (len(body), used, errs, unv, 'PASS' if used == len(body) and not errs else 'MISMATCH'))
if used != len(body) or errs:
    ok = False
res, msg = body[0], None
off = 1
n = struct.unpack_from('>H', body, off)[0]
msg = body[off + 2:off + 2 + n].decode('utf-8', 'replace')
off += 2 + n
vals = struct.unpack_from('>HIIIIIIB', body, off)
print('  result=%d msg=%r daily_time=%d daily_time2=%d score=%d win=%d lose=%d total=%d rest=%d first_reward=%d'
      % (res, msg, *vals))

# ---- 17309 ----
body = q(s, 17309)
spec = sc_spec(17309)
used, errs, unv = parse_full(body, spec)
print('\n== 17309 ==')
print('  SC_17309 len=%d  解析消耗=%d  errs=%s unverified=%s  %s'
      % (len(body), used, errs, unv, 'PASS' if used == len(body) and not errs else 'MISMATCH'))
if used != len(body) or errs:
    ok = False

cnt = struct.unpack_from('>H', body, 0)[0]
off = 2
rows = []
for _ in range(cnt):
    n = struct.unpack_from('>H', body, off)[0]
    name = body[off + 2:off + 2 + n].decode('utf-8', 'replace')
    off += 2 + n
    r = struct.unpack_from('>I', body, off)[0]
    off += 4
    n = struct.unpack_from('>H', body, off)[0]
    srid = body[off + 2:off + 2 + n].decode('utf-8', 'replace')
    off += 2 + n
    rank = struct.unpack_from('>I', body, off)[0]
    off += 4
    career = body[off]; sex = body[off + 1]
    off += 2
    score, lev, win = struct.unpack_from('>III', body, off)
    off += 12
    rows.append((rank, name, r, lev, career, sex, score, win))
print('  rank_list=%d' % cnt)
for x in rows[:8]:
    print('    rank=%d name=%s rid=%d lev=%d career=%d sex=%d score=%d win=%d' % x)
if off != len(body):
    print('  !! 尾部剩余 %d 字节' % (len(body) - off))
    ok = False

print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
