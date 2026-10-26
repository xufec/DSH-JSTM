# -*- coding: utf-8 -*-
"""R56 验证：**等级口径一致性** —— 同一角色的等级在多条应答里必须相同。

事由：`13340`（个人名片）原先读 `config.json` 的静态 role 模板，
而 `10301/10302/10303` 读 DB 真源 ⇒ admin `/setlevel` 之后两处**各说各话**
（实测 `10302 lev=9` 而 `13340 lev=70`）。与 R43「战力口径统一」同一类问题。

断言：下列命令给出的等级必须一致
    10301.lev(u16) / 10302.lev(u8) / 13340.lev(u8)

用法：python tools/verify_level_consistency.py
"""
import json
import os
import socket
import struct
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_live import pack_frame, recv_exact  # noqa: E402


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def login(s):
    _args = struct.pack('>H', 10)
    for _k, _v in (('account', 'dsh_local'), ('channelId', '1'),
                   ('device_id', 'dsh-probe'), ('enter_srv_id', '1'),
                   ('gettui_cid', ''), ('idfa', ''), ('platform', 'ewan'),
                   ('sign', ''), ('timestamp', '0'), ('token', '')):
        _kb = _k.encode(); _vb = _v.encode()
        _args += struct.pack('>H', len(_kb)) + _kb + struct.pack('>H', len(_vb)) + _vb
    s.sendall(pack_frame(1110, _args))
    rid = None
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


def skip_str(b, off):
    n = struct.unpack_from('>H', b, off)[0]
    return off + 2 + n


s = socket.create_connection(('127.0.0.1', 9000), 5)
s.settimeout(5.0)
rid = login(s)

# 10302: 资产/等级包 —— 首字段是 **lev:uint16**（不是 u8；踩过一次）
b = q(s, 10302)
levs = {'10302': struct.unpack_from('>H', b, 0)[0]}
b3 = q(s, 13340)
o = skip_str(b3, 0)               # 13340 首字段是 name:string，其后紧跟 lev:u8
levs['13340'] = b3[o]
s.close()

admin = json.loads(urllib.request.urlopen(
    'http://127.0.0.1:8080/DSH_ADMIN/status').read())['role']['level']

print('== 等级口径 ==')
print('  DB(admin /status) :', admin)
for k in ('10301', '10302', '13340'):
    print('  %-6s            : %s' % (k, levs.get(k)))
vals = set(levs.values()) | {int(admin)}
ok = len(vals) == 1
print('\n  一致: %s' % ('是' if ok else '否 → %s' % sorted(vals)))
print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
