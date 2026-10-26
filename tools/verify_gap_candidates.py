# -*- coding: utf-8 -*-
"""R152 验收：从 1144 条潜在缺口里精准挖出的 4 条。

判据（都核对**真实值**，不只看 code）：
  1. `18400` 的 `tar_val` == `config_group_control.GroupControl[1].tar_val`
  2. `13326` 的 `courage`/`charm` == 刚用 `/DSH_ADMIN/setassets` 置进去的值
  3. `12414` 回显 `mission_bid`/`npc_bid` + `code` 如实
  4. `14204` 回真实 `mission_bid`

用法： python tools/verify_gap_candidates.py
"""
import io
import json
import os
import socket
import struct
import sys
import urllib.request

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


def seta(qs):
    return urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/setassets?' + qs, timeout=8).read().decode('utf-8')


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

    # ---- 18400：tar_val 来自配置
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_group_control.json'),
                         encoding='utf-8'))
    want = int(cfg['GroupControl']['1']['hash']['tar_val'])
    b = ask(18400)
    r = g.audit_body(sc['18400'], b, 18400)
    is_open = b[0]
    # ★ 布局：is_open:u8(0) + merge_index:u8(1) + step:u8(2) + status:u8(3)
    #         + val:u16(4) + tar_val:u16(6)  ⇒ 共 8 字节
    tar = struct.unpack_from('>H', b, 6)[0]
    print('\n== 18400 合服/世界进程 ==')
    print('  len=%d 消耗=%d err=%s is_open=%d tar_val=%d（配置 %d）'
          % (r['len'], r['consumed'], r['err'], is_open, tar, want))
    a1 = r['consumed'] == r['len'] and not r['err'] and tar == want
    print('  ★ tar_val 与配置一致 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 13326：courage/charm 来自真实资产
    seta('courage=321&charm=654')
    b = ask(13326, struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1')
    r = g.audit_body(sc['13326'], b, 13326)
    rid = struct.unpack_from('>I', b, 0)[0]
    sl = struct.unpack_from('>H', b, 4)[0]
    o = 6 + sl
    nl = struct.unpack_from('>H', b, o)[0]
    name = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
    o += 2 + nl
    car = struct.unpack_from('>H', b, o)[0]
    on = b[o + 2]
    cg = struct.unpack_from('>I', b, o + 3)[0]
    cm = struct.unpack_from('>I', b, o + 7)[0]
    print('\n== 13326 看他人社交（=看自己）==')
    print('  len=%d err=%s rid=%d name=%r career=%d online=%d courage=%d charm=%d'
          % (r['len'], r['err'], rid, name, car, on, cg, cm))
    a2 = r['consumed'] == r['len'] and not r['err'] and cg == 321 and cm == 654
    print('  ★ courage/charm 与真实资产一致 ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2
    seta('courage=0&charm=0')

    # ---- 12414：回显 + 校验
    b = ask(12414, struct.pack('>I', 1) + struct.pack('>I', 23001) + struct.pack('>I', 80001))
    r = g.audit_body(sc['12414'], b, 12414)
    mb = struct.unpack_from('>I', b, 0)[0]
    nb = struct.unpack_from('>I', b, 4)[0]
    print('\n== 12414 NPC 对话校验 ==')
    print('  len=%d err=%s mission_bid=%d npc_bid=%d code=%d' % (r['len'], r['err'], mb, nb, b[8]))
    a3 = r['consumed'] == r['len'] and not r['err'] and mb == 23001 and nb == 80001
    print('  ★ 回显正确 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 14204：真实 mission_bid
    b = ask(14204, struct.pack('>I', 23001))
    r = g.audit_body(sc['14204'], b, 14204)
    mb4 = struct.unpack_from('>I', b, 0)[0]
    print('\n== 14204 任务奖励预览 ==')
    print('  len=%d err=%s mission_bid=%d' % (r['len'], r['err'], mb4))
    a4 = r['consumed'] == r['len'] and not r['err'] and mb4 == 23001
    print('  ★ 回真实 mission_bid ⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
