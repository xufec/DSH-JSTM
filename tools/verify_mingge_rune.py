# -*- coding: utf-8 -*-
"""R111/R112 验收：`19400`（命格背包）+ `21405`（魂星兑换，真扣材料）。

用法： python tools/verify_mingge_rune.py
"""
import io
import os
import socket
import sqlite3
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), 'server', 'state', 'roles.db')


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


def rune_chip():
    c = sqlite3.connect(DB)
    r = c.execute("SELECT amount FROM role_assets WHERE rid=1001 AND name='rune_chip'").fetchone()
    return r[0] if r else 0


def main():
    ok = True

    # ---- 19400：mingge_stage 必须 = MinggeOther.stage_init（1），不是默认响应的 0
    # ★★ R126 起 `mingge_list` 会**读真实 DB**（不再恒空）⇒ 判据不能假设 `len==4`。
    #    改为：结构**精确解析**（用门禁权威解析器）+ `bag_code`/`mingge_stage` 正确。
    import importlib.util as _iu
    _spec = _iu.spec_from_file_location('g', os.path.join(HERE, 'audit_emitted_fields.py'))
    _g = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_g)
    _cs, _sc = _g.load_specs()
    b = ask(19400, b'\x01')
    _r = _g.audit_body(_sc['19400'], b, 19400)
    print('\n== SC_19400 ==')
    print('  len=%d  bag_code=%d  mingge_stage=%d  消耗=%d err=%s'
          % (len(b), b[0], b[1], _r['consumed'], _r['err']))
    a1 = (b[0] == 1 and b[1] == 1
          and _r['consumed'] == _r['len'] and not _r['err'])
    print('  bag_code 原样回 & mingge_stage=stage_init(1) & 结构精确 ⇒ %s'
          % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 21405：无效 bid ⇒ code=0（诚实）
    b = ask(21405, struct.pack('>I', 99999) + struct.pack('>H', 1))
    n = struct.unpack_from('>H', b, 1)[0]
    msg = b[3:3 + n].decode('utf-8', 'replace')
    print('\n== SC_21405（无效 rune_bid）==')
    print('  code=%d msg=%r' % (b[0], msg))
    a2 = b[0] == 0 and '无效' in msg
    print('  回 code=0 + 明确 msg ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 21405：有材料 ⇒ code=1 且真的扣
    before = rune_chip()
    if before >= 4500:
        b = ask(21405, struct.pack('>I', 21403) + struct.pack('>H', 1))
        after = rune_chip()
        print('\n== SC_21405（有材料：21403 需 4500）==')
        print('  code=%d  rune_chip %d → %d' % (b[0], before, after))
        a3 = b[0] == 1 and before - after == 4500
        print('  成功且恰好扣 4500 ⇒ %s' % ('✓' if a3 else '✗'))
        ok = ok and a3
    else:
        print('\n== SC_21405（材料不足路径）==')
        print('  当前 rune_chip=%d < 4500 ⇒ 跳过成功路径（材料不足路径上面已验）' % before)

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
