# -*- coding: utf-8 -*-
"""R43 验证：属性/战力口径统一 + 10306 条目结构订正。

核对三件事：
  1. `SC_10306` / `SC_10304` / `SC_20100` 的应答都**按规格精确解析**（字节数恰好）；
  2. 三处报出的**战力数值完全一致**（口径统一）；
  3. `SC_10306` 的长度等于规格推导值 —— **88 字节**
     （attr 表 2 + 条目 80 + mspd 2 + power 4），
     而不是误用 10304 切分时的 96 字节。

用法：python tools/verify_attr_power.py
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
from audit_sc_live import pack_frame, recv_exact, login  # noqa: E402

with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
    FIELDS = json.load(f)


def sc_spec(cmd):
    for k, v in FIELDS.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def send(s, cmd, body=b''):
    s.sendall(pack_frame(cmd, body))
    while True:
        hdr = recv_exact(s, 6)
        (ln, rcmd) = struct.unpack('>IH', hdr)
        payload = recv_exact(s, ln - 2)
        if rcmd == cmd:
            return payload


def attr_table_len(cmd):
    """按规格算 attr 表字节数：2 + 条目。"""
    for f in sc_spec(cmd):
        if f.get('name') == 'attr' and f.get('items'):
            w = {'uint16': 2, 'uint32': 4, 'int16': 2, 'int32': 4}
            return 2 + sum(w.get(x['type'], 0) for x in f['items'])
    return 0


def main():
    ok = True
    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    login(s)
    s.settimeout(5)

    got = {}
    for cmd in (10304, 10306, 20100):
        p = send(s, cmd)
        spec = sc_spec(cmd)
        off, errs, unver = parse_full(p, spec)
        good = (not errs) and off == len(p)
        print('SC_%-6d len=%-5d 解析消耗=%-5d %s'
              % (cmd, len(p), off, 'PASS' if good else 'FAIL ' + str(errs)))
        if not good:
            ok = False
        got[cmd] = p

    # ---- 10306 长度必须等于规格推导值 ----
    want = attr_table_len(10306) + 2 + 4          # attr 表 + mspd + power
    print()
    print('SC_10306 期望长度 = %d（attr 表 %d + mspd 2 + power 4）；实际 = %d'
          % (want, attr_table_len(10306), len(got[10306])))
    if len(got[10306]) != want:
        print('   !! 长度不符（若为 %d，即是误用了 10304 的切分）' % (want + 8))
        ok = False

    # ---- 三处战力必须一致 ----
    def power_of_10304(p):
        # 跳过 rid/srv_id/name/lev/is_vip/vip_lev/sex/career/volume×3/volume_open×3
        off = 4
        for _ in range(2):
            n = struct.unpack_from('>H', p, off)[0]
            off += 2 + n
        off += 2 + 1 + 1 + 1 + 2 + 1 + 1 + 1 + 1 + 1 + 1 + 2 + 2  # 到 skill_list 之后
        return struct.unpack_from('>I', p, off)[0]

    def power_of_10306(p):
        return struct.unpack_from('>I', p, len(p) - 4)[0]

    def power_of_20100(p):
        n = struct.unpack_from('>H', p, 0)[0]
        # 第一项 {code:u8, val:u32} ⇒ val 在偏移 3
        return struct.unpack_from('>I', p, 3)[0] if n else 0

    p4, p6, p0 = power_of_10304(got[10304]), power_of_10306(got[10306]), power_of_20100(got[20100])
    print()
    print('战力（三处）: 10304=%d  10306=%d  20100=%d' % (p4, p6, p0))
    if not (p4 == p6 == p0):
        print('   !! 三处战力不一致 ⇒ 口径未统一')
        ok = False
    else:
        print('   ✓ 口径统一（三处一致）')

    s.close()
    print()
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
