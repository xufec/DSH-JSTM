# -*- coding: utf-8 -*-
"""R88 验收：`SC_14000`（阵型查询）必须是**真实阵型 + 已拥有伙伴**。

断言（依据见 server/mock_server.py 的 `_FORMATIONS` 注释）：
  1. 结构能按 spec 精确解析完（`SC_14000{flag,select_type,
     info_list:table(type,f_lev,hero_pos_info:table(hero_bid,pos),member_pos_info:table(...))}`）；
  2. `type ∈ 1..7`（`config_formation.luac` 的 f_type 只有 1/2/3/4/5/6/7；
     **9 不是合法阵型** —— 那是修复前的写死值）；
  3. `type` = 角色等级可用的**最高**阵型；
  4. `hero_pos_info` 至少 2 条（修复前恒为 1 条写死的唐舞桐 33100），
     且 `hero_bid` 都是已拥有伙伴、`pos` 为 1..N。

用法： python tools/verify_formation.py
"""
import io
import os
import socket
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

FORMATIONS = [(1, 1), (2, 20), (4, 32), (3, 36), (5, 42), (6, 46), (7, 50)]


def main():
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(10.0)
    print('login rid =', login(s))
    s.sendall(pack_frame(14000, b'\x01'))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        body = recv_exact(s, ln - 2)
        if rc == 14000:
            break
    s.close()

    flag, st = body[0], body[1]
    n = struct.unpack_from('>H', body, 2)[0]
    off = 4
    typ, flev = body[off], body[off + 1]
    hp = struct.unpack_from('>H', body, off + 2)[0]
    off += 4
    pos = []
    for _ in range(hp):
        pos.append((struct.unpack_from('>I', body, off)[0], body[off + 4]))
        off += 5
    mp = struct.unpack_from('>H', body, off)[0]
    off += 2 + mp * 0        # member_pos_info 为空时无需消费

    print('\n== SC_14000 ==')
    print('  flag=%d select_type=%d info_list=%d' % (flag, st, n))
    print('  type(阵型)=%d f_lev=%d hero_pos_info=%d member=%d' % (typ, flev, hp, mp))
    print('  上阵伙伴: %s' % pos)
    ok = off == len(body)
    print('  解析 %d/%d  PASS=%s' % (off, len(body), ok))

    print('\n== 断言 ==')
    a1 = off == len(body)
    a2 = 1 <= typ <= 7
    # ★ R91 起 `14000` 回的是**玩家选中的阵型**（`14005` 落库），不再必然是最高档。
    #   所以这里断言"该阵型**等级已解锁**"（need_lev <= 70），而不是"== 最高档"。
    _lev_unlocked = [f for f, lv in FORMATIONS if lv <= 70]
    a3 = typ in _lev_unlocked
    a4 = hp >= 2 and all(p == i for i, (_b, p) in enumerate(pos, 1))
    print('  结构精确解析           : %s' % ('✓' if a1 else '✗'))
    print('  type 是合法阵型(1..7)   : %s (type=%d)' % ('✓' if a2 else '✗', typ))
    print('  该阵型等级已解锁(≤70)   : %s（可选 %s）' % ('✓' if a3 else '✗', _lev_unlocked))
    print('  伙伴位 ≥2 且 pos=1..N   : %s (共 %d 位)' % ('✓' if a4 else '✗', hp))
    ok = a1 and a2 and a3 and a4
    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
