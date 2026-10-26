# -*- coding: utf-8 -*-
"""R148 验收：`13361`（空间装扮）+ `18307`（结拜/婚宴状态）。

判据：
  1. `13361` 的 `zone_list`/`head_list` 条数与 bid **与配置逐条一致**
     （`FriendZoneSkinBid`(type2) → zone；`FriendZoneSkin`(type1) → head）
  2. `18307` 结构精确（无结拜 ⇒ 空名，真话）
  3. 全部用门禁权威解析器

用法： python tools/verify_zone_jiebai.py
"""
import io
import json
import os
import socket
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


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
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_friend_zone_data.json'),
                         encoding='utf-8'))
    want_zone = sorted(int(k) for k in cfg['FriendZoneSkinBid'])
    want_head = sorted(int(k) for k in cfg['FriendZoneSkin'])

    b = ask(13361)
    r = g.audit_body(sc['13361'], b, 13361)
    z = struct.unpack_from('>H', b, 0)[0]
    zone = [struct.unpack_from('>H', b, 2 + 2 * i)[0] for i in range(z)]
    off = 2 + 2 * z
    h = struct.unpack_from('>H', b, off)[0]
    head = [struct.unpack_from('>H', b, off + 2 + 2 * i)[0] for i in range(h)]
    print('\n== 13361 空间装扮 ==')
    print('  len=%d 消耗=%d err=%s zone=%d head=%d' % (r['len'], r['consumed'], r['err'], z, h))
    a1 = r['consumed'] == r['len'] and not r['err']
    a2 = zone == want_zone and head == want_head
    print('  ★ 结构精确 ⇒ %s' % ('✓' if a1 else '✗'))
    print('  ★ zone/head 的 bid **逐条**与配置一致 ⇒ %s' % ('✓' if a2 else '✗'))
    if not a2:
        print('     zone 回包 %s vs 配置 %s' % (zone, want_zone))
        print('     head 回包 %s vs 配置 %s' % (head, want_head))
    ok = ok and a1 and a2

    b = ask(18307)
    r = g.audit_body(sc['18307'], b, 18307)
    print('\n== 18307 结拜/婚宴状态 ==')
    print('  len=%d 消耗=%d err=%s' % (r['len'], r['consumed'], r['err']))
    a3 = r['consumed'] == r['len'] and not r['err']
    print('  ★ 结构精确（无结拜 ⇒ 空名，真话）⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
