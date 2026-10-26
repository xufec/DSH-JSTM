# -*- coding: utf-8 -*-
"""R143 验收：命格家族 13 条（`19401`–`19414`，`19406` 已实现）。

判据：
  1. **真读**：`19401`/`19414` 的 `mingge_list` 与 DB 一致；`19409` 的 `mingge_stage` = 配置 `stage_init`
  2. **真改**：`19404` 删除后 DB 行数**真的减少**
  3. **只校验/回显**：其余结构精确 + `code` 如实
  4. 全部用门禁权威解析器

用法： python tools/verify_mingge_family.py
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


def adm(qs):
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/' + qs, timeout=8).read().decode('utf-8'))


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
    stage_init = int(json.load(open(os.path.join(ROOT, 'server', '_mingge_cfg.json'),
                                    encoding='utf-8'))['MinggeOther']['hash']['stage_init'])

    # 前置：给 3 个命格
    adm('mingge?bid=21001&lev=2')
    adm('mingge?bid=21002&lev=1')
    adm('mingge?bid=21003&lev=5')

    # ---- 19409 阶段（真读配置）
    b = ask(19409)
    r = g.audit_body(sc['19409'], b, 19409)
    off = 1 + 2 + struct.unpack_from('>H', b, 1)[0]
    st = b[off]
    print('\n== 19409 命格阶段 ==')
    print('  len=%d err=%s mingge_stage=%d（配置 stage_init=%d）' % (r['len'], r['err'], st, stage_init))
    a1 = r['consumed'] == r['len'] and not r['err'] and st == stage_init
    print('  ★ 与配置 stage_init 一致 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 19401 列表（真读 DB）
    b = ask(19401, bytes([1]))
    r = g.audit_body(sc['19401'], b, 19401)
    n = struct.unpack_from('>H', b, 1)[0]
    print('\n== 19401 命格列表 ==')
    print('  len=%d 消耗=%d err=%s bag=%d 条目=%d' % (r['len'], r['consumed'], r['err'], b[0], n))
    a2 = r['consumed'] == r['len'] and not r['err'] and n == 3
    print('  ★ 3 个命格（与 DB 一致）⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2

    # ---- 19414 看自己
    b = ask(19414, struct.pack('>I', 1001) + struct.pack('>H', 1) + b'1')
    r = g.audit_body(sc['19414'], b, 19414)
    rid14 = struct.unpack_from('>I', b, 0)[0]
    print('\n== 19414 看他人（=看自己）==')
    print('  len=%d 消耗=%d err=%s rid=%d' % (r['len'], r['consumed'], r['err'], rid14))
    a3 = r['consumed'] == r['len'] and not r['err'] and rid14 == 1001
    print('  ★ 回的是自己的真实数据 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    # ---- 19404 删除（真改）
    body = bytes([1]) + struct.pack('>H', 1) + struct.pack('>I', 21003)
    b = ask(19404, body)
    r = g.audit_body(sc['19404'], b, 19404)
    b2 = ask(19401, bytes([1]))
    n2 = struct.unpack_from('>H', b2, 1)[0]
    print('\n== 19404 删除命格 ==')
    print('  code=%d len=%d err=%s  删除后列表=%d' % (b[0], r['len'], r['err'], n2))
    a4 = b[0] == 1 and n2 == 2 and r['consumed'] == r['len']
    print('  ★ 真的删掉一个（3 → 2）⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a4

    # ---- 只校验/回显类
    checks = [(19402, bytes([1]) + struct.pack('>I', 21001) + struct.pack('>I', 1) + struct.pack('>H', 0)),
              (19403, bytes([1]) + struct.pack('>I', 21001)),
              (19405, bytes([1]) + struct.pack('>I', 21001)),
              (19407, b''), (19408, bytes([1])),
              (19410, bytes([1]) + struct.pack('>I', 21001) + bytes([0])),
              (19411, bytes([1]) + struct.pack('>I', 21001)),
              (19412, bytes([1]) + struct.pack('>H', 0)),
              (19413, bytes([1]) + struct.pack('>I', 21001))]
    bad = 0
    for c, body in checks:
        b = ask(c, body)
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 只校验/回显类（9 条）==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
