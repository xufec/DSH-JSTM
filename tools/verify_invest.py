# -*- coding: utf-8 -*-
"""R117 验收：`17200`（投资天数/状态）+ `16503`（领取信息）。

流程：
  1. 清空投资 ⇒ `17200` day=0 status=0；`16503{7}` 两个列表都空（真话）
  2. `GET /DSH_ADMIN/invest?type=7&day=3` ⇒ `17200` day=3 status=1（有可领）
  3. `16503{7}` ⇒ `get_info` 应为 `DayInvest[7]` 里 ≤3 的天数、`can_get_info` 为其中未领的
  4. 用 `geted` 位图标记已领 ⇒ `16503` 的 `can_get_info` 相应减少

用法： python tools/verify_invest.py
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


def admin(qs):
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/invest?' + qs, timeout=8).read().decode('utf-8'))


def main():
    ok = True
    admin('type=0')                       # 清空

    b = ask(17200)
    day = struct.unpack_from('>I', b, 0)[0]
    st = b[4]
    print('\n== 没有投资 ==')
    print('  SC_17200 len=%d day=%d status=%d' % (len(b), day, st))
    a1 = len(b) == 5 and day == 0 and st == 0
    print('  day=0 status=0（真话）⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    b = ask(16503, bytes([7]))
    t = b[0]
    off = 1
    n1 = struct.unpack_from('>H', b, off)[0]; off += 2
    g = [b[off + i] for i in range(n1)]; off += n1
    n2 = struct.unpack_from('>H', b, off)[0]; off += 2
    c = [b[off + i] for i in range(n2)]; off += n2
    print('\n== 没有投资时的 16503{7} ==')
    print('  type=%d get_info=%s can_get_info=%s 解析=%d/%d' % (t, g, c, off, len(b)))
    a2 = off == len(b) and not g and not c
    print('  两个列表都空 ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    r = admin('type=7&day=3')
    ms = r.get('milestones') or []
    b = ask(17200)
    day = struct.unpack_from('>I', b, 0)[0]
    st = b[4]
    print('\n== 发放投资 type=7 day=3 ==')
    print('  管理端里程碑=%s' % ms)
    print('  SC_17200 day=%d status=%d' % (day, st))
    a3 = day == 3 and st == 1
    print('  day=3 且 status=1（有可领）⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    b = ask(16503, bytes([7]))
    off = 1
    n1 = struct.unpack_from('>H', b, off)[0]; off += 2
    g = [b[off + i] for i in range(n1)]; off += n1
    n2 = struct.unpack_from('>H', b, off)[0]; off += 2
    c = [b[off + i] for i in range(n2)]; off += n2
    print('\n== 有进度后的 16503{7} ==')
    print('  get_info=%s  can_get_info=%s  解析=%d/%d' % (g, c, off, len(b)))
    want_got = [m for m in ms if m <= 3]
    a4 = off == len(b) and g == want_got and c == want_got
    print('  get_info 与配置里程碑(≤3)一致、can_get=全部未领 ⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    # 标记第 1 个里程碑已领 ⇒ can_get 应减少 1
    admin('type=7&day=3&geted=1')
    b = ask(16503, bytes([7]))
    off = 1
    n1 = struct.unpack_from('>H', b, off)[0]; off += 2
    g = [b[off + i] for i in range(n1)]; off += n1
    n2 = struct.unpack_from('>H', b, off)[0]; off += 2
    c = [b[off + i] for i in range(n2)]; off += n2
    print('\n== 标记首位已领后 ==')
    print('  get_info=%s  can_get_info=%s' % (g, c))
    a5 = len(c) == max(0, len(g) - 1)
    print('  can_get_info 少了 1 个 ⇒ %s' % ('✓' if a5 else '✗'))
    ok = ok and a5

    admin('type=0')                       # 复原
    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
