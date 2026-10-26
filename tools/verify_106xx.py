# -*- coding: utf-8 -*-
"""R162 验收：`106xx` 收尾 4 条（`10601`/`10610`/`10622`/`10651`）。

判据：
  1. 全部**结构精确**（门禁权威解析器）
  2. `10622` 的 `code` 随 `bid` 非零如实；`skill_list` 为空（登记理由）
  3. `10601` 的 `hero_list` 为空（22 个战斗属性本服无源）

用法： python tools/verify_106xx.py
"""
import io
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CMDS = (10601, 10610, 10622, 10651)


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
    bodies = {
        10601: struct.pack('>I', 1),
        10610: struct.pack('>H', 0) + struct.pack('>H', 0) + struct.pack('>I', 30),
        10622: struct.pack('>I', 101),
        10651: b'',
    }
    bad = 0
    for cmd in CMDS:
        b = ask(cmd, bodies[cmd])
        r = g.audit_body(sc[str(cmd)], b, cmd)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (cmd, r['len'], r['consumed'], r['err']))
    print('\n== 4 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # 10622：code 如实 + skill_list 空
    b = ask(10622, struct.pack('>I', 101))
    m = struct.unpack_from('>H', b, 1)[0]
    o = 1 + 2 + m
    n = struct.unpack_from('>H', b, o)[0]
    print('  10622 code=%d skill_list=%d（config_skill 解构失败 ⇒ 空）⇒ %s'
          % (b[0], n, '✓' if (b[0] == 1 and n == 0) else '✗'))
    ok = ok and b[0] == 1 and n == 0
    b0 = ask(10622, struct.pack('>I', 0))
    print('  10622 bid=0 ⇒ code=%d ⇒ %s' % (b0[0], '✓' if b0[0] == 0 else '✗'))
    ok = ok and b0[0] == 0

    # ★★★ R213：`10601` 的 `hero_list` **不再为空** ——
    #   旧断言（R162）是"22 个战斗属性本服无源 ⇒ 空"，
    #   但 **R204 建了 `role_attr` 通路** ⇒ 现可填 **18/22**（13 同名 + 5 别名）。
    #   ★ 新断言：**hero_list == 1**，且**至少 `atk_s`/`atk_p`/`hp_max` 有值**（来自 `role_attr`）。
    b = ask(10601, struct.pack('>I', 1))
    hl = struct.unpack_from('>H', b, 12)[0]
    # hero_list 元素：atk_s(4) atk_p(4) def_s(4) def_p(4) hp_max(4) …
    _vals = {}
    if hl:
        o = 14
        for _nm in ('atk_s', 'atk_p', 'def_s', 'def_p', 'hp_max'):
            _vals[_nm] = struct.unpack_from('>I', b, o)[0]
            o += 4
    _nonz = sum(1 for v in _vals.values() if v)
    print('  10601 hero_list=%d ｜ atk_s=%s atk_p=%s hp_max=%s（应来自 role_attr，≥1 个非零）⇒ %s'
          % (hl, _vals.get('atk_s'), _vals.get('atk_p'), _vals.get('hp_max'),
             '✓' if (hl == 1 and _nonz >= 1) else '✗'))
    ok = ok and hl == 1 and _nonz >= 1

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
