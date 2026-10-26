# -*- coding: utf-8 -*-
"""R163 验收：`107xx` 家族 **26 条**。

判据：
  1. 全部 26 条**结构精确**（门禁权威解析器）
  2. `10706` 的 `npc_list` 与 **`config_map_npc.MapNpc` 去重后逐项一致**
  3. `10734`/`10762` 的 `gold` == 真实金币
  4. `10702` 的 `all_building` 的 `lev` 与 `role_build` 一致

★ 本批的教训（已记入报告）：**按号段一刀切 ≠ 逐条按 spec**
—— `107xx` 有 17 种 SC 模式，`else` 分支只覆盖 `{code,msg}` 型，导致 8 条越界。

用法： python tools/verify_107xx.py
"""
import io
import json
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
    gaps = sorted(int(x.strip()) for x in
                  open(os.path.join(ROOT, 'analysis', '1.4.9', '_unhandled_cs_sc.txt'),
                       encoding='utf-8') if x.strip().isdigit())
    fams = [c for c in gaps if 10700 <= c < 10800]
    print('\n  107xx 家族共 %d 条' % len(fams))

    bad = 0
    for c in fams:
        body = bytes([1]) if c == 10701 else b''
        b = ask(c, body)
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 26 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10706 NPC 列表逐项
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_map_npc.json'),
                         encoding='utf-8'))
    want = sorted({int(v[1]) for v in cfg['MapNpc'].values()
                   if isinstance(v, list) and len(v) >= 2})
    b = ask(10706)
    n = struct.unpack_from('>H', b, 0)[0]
    ids = [struct.unpack_from('>I', b, 2 + 4 * i)[0] for i in range(n)]
    print('\n== 10706 NPC 列表 ==  %d 条（配置 %d）' % (n, len(want)))
    a1 = ids == want
    print('  ★ 与 config_map_npc 去重后**逐项一致** ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # 10734/10762 gold
    gold = int((q('SELECT amount FROM role_assets WHERE rid=? AND name=?', (RID, 'gold'))
                or [(0,)])[0][0])
    for c in (10734, 10762):
        b = ask(c)
        m = struct.unpack_from('>H', b, 1)[0]
        o = 1 + 2 + m
        gv = struct.unpack_from('>I', b, o)[0]
        a = gv == gold
        print('  %d gold=%d（DB %d）⇒ %s' % (c, gv, gold, '✓' if a else '✗'))
        ok = ok and a

    # 10702 all_building lev
    lev = 0
    try:
        r = q('SELECT lev FROM role_build WHERE rid=?', (RID,))
        lev = int(r[0][0]) if r else 0
    except Exception:
        lev = 0
    b = ask(10702)
    n = struct.unpack_from('>H', b, 0)[0]
    got_lev = b[2 + 1] if n else 0
    print('  10702 all_building=%d lev=%d（DB %d）⇒ %s'
          % (n, got_lev, lev, '✓' if (n == 1 and got_lev == lev) else '✗'))
    ok = ok and n == 1 and got_lev == lev

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
