# -*- coding: utf-8 -*-
"""R87 验收：`SC_11215`（伙伴列表）的形态 —— 修"伙伴界面综合页显示图鉴 / 阵型列表为空"。

断言（都有出处）：
  1. `partner_list` = **全部伙伴**（`config_partner_base` 53 个）—— 图鉴要全量；
  2. `type ∈ {1, 2}`：来自 `hero_constants.luac` 的
     `TableConst(hash=[('Common',1),('ShenJiang',2)])`，且被
     `partner_atlas_container/atlas_view` 用于**图鉴分组**
     ⇒ 必须与 `Config.Partner[bid].is_deity` 对应（is_deity=1 ⇒ 2）；
  3. **已拥有的 `id != 0`**（用 bid）、**未拥有的 `id == 0`** —— `id` 是元素首字段，
     阵型侧据此筛"已拥有"（否则阵型列表为空）。

用法： python tools/verify_partner_list.py
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


def parse_list(b):
    """SC_11215{partner_list:table(...)}；只解需要的 id/bid/type。"""
    n = struct.unpack_from('>H', b, 0)[0]
    off = 2
    rows = []
    for _ in range(n):
        id_ = struct.unpack_from('>I', b, off)[0]
        bid = struct.unpack_from('>I', b, off + 4)[0]
        typ = b[off + 8]
        color = b[off + 9]
        off += 10
        off += 4 + 1 + 4 + 2 + 4 + 1 + 1 + 1     # lifttime lev exp grow score stage rebirth acc
        pa = struct.unpack_from('>H', b, off)[0]
        off += 2 + pa * 4                         # partner_attr（code:u16,value:u32）
        off += 4                                  # power
        apt = struct.unpack_from('>H', b, off)[0]
        off += 2 + apt * 4                        # aptitude
        off += 4                                  # innate_skill
        for _2 in range(3):                       # skill / jindan / talisman（u16 计数）
            cnt = struct.unpack_from('>H', b, off)[0]
            off += 2 + cnt * 4
        ext = struct.unpack_from('>H', b, off)[0]  # ext（u16 计数）
        off += 2 + ext * 4
        rows.append({'id': id_, 'bid': bid, 'type': typ, 'color': color})
    return rows, off, len(b)


def main():
    base = json.load(open(os.path.join(ROOT, 'server', '_partner_base.json'),
                          encoding='utf-8'))
    deity = {int(p['bid']) for p in base if int(p.get('is_deity') or 0) == 1}

    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(10.0)
    print('login rid =', login(s))
    s.sendall(pack_frame(11215, b''))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        body = recv_exact(s, ln - 2)
        if rc == 11215:
            break
    s.close()

    rows, used, total = parse_list(body)
    print('\n== SC_11215 ==')
    print('  partner_list=%d  解析 %d/%d 字节  PASS=%s'
          % (len(rows), used, total, used == total))
    ok = used == total

    print('\n== ① 全量（图鉴需要）==')
    print('  伙伴表 %d 个，收到 %d 个  PASS=%s' % (len(base), len(rows), len(rows) == len(base)))
    if len(rows) != len(base):
        ok = False

    print('\n== ② type 与 is_deity 对应 ==')
    bad = [r for r in rows
           if r['type'] != (2 if r['bid'] in deity else 1)]
    n2 = sum(1 for r in rows if r['type'] == 2)
    n1 = sum(1 for r in rows if r['type'] == 1)
    print('  type=1(普通) %d 个 ／ type=2(神将) %d 个 ／ 与 is_deity 不符 %d 个'
          % (n1, n2, len(bad)))
    print('  神将表应有 %d 个 ⇒ PASS=%s' % (len(deity), n2 == len(deity) and not bad))
    if bad or n2 != len(deity):
        ok = False

    print('\n== ③ id：已拥有非 0 / 未拥有为 0 ==')
    own = [r for r in rows if r['id'] != 0]
    print('  id!=0（已拥有）%d 个 ⇒ 阵型列表应有这么多' % len(own))
    badid = [r for r in own if r['id'] != r['bid']]
    print('  id 与 bid 不一致的 %d 个' % len(badid))
    if badid:
        ok = False
    print('  样例:', [(r['bid'], r['id'], r['type']) for r in rows[:3]])

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
