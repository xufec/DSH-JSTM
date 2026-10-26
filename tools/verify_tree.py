# -*- coding: utf-8 -*-
"""R138 验收：`13579`（摇钱树 / 膜拜）—— `strength_rest`/`strength_name` 来自**真实配置**。

判据：
  1. `strength_rest == StaticData.attr_delay.val`（配置里写死 48）
  2. `strength_name` 随 `tree_lev` 变化（取自 `WorshipType[].type_name`）
  3. 结构精确解析（门禁权威解析器）

用法： python tools/verify_tree.py
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


def ask(cmd):
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(8.0)
    login(s)
    s.sendall(pack_frame(cmd, b''))
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
    spec = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def parse(b):
    lv = b[0]
    rest = struct.unpack_from('>I', b, 1)[0]
    n = struct.unpack_from('>H', b, 5)[0]
    nm = b[7:7 + n].decode('utf-8', 'replace')
    return lv, rest, nm


def main():
    ok = True
    g, sc = load_gate()
    cfg = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_guild_tree_data.json'),
                         encoding='utf-8'))
    want_rest = int(cfg['StaticData']['hash']['attr_delay']['hash']['val'])

    adm('tree?lev=0')
    b = ask(13579)
    r = g.audit_body(sc['13579'], b, 13579)
    lv, rest, nm = parse(b)
    print('\n== 13579（lev=0）==')
    print('  len=%d 消耗=%d err=%s tree_lev=%d strength_rest=%d name=%r'
          % (r['len'], r['consumed'], r['err'], lv, rest, nm))
    a1 = (r['consumed'] == r['len'] and not r['err'] and rest == want_rest)
    print('  ★ strength_rest 与配置 `attr_delay.val`(%d) 一致 ⇒ %s' % (want_rest, '✓' if a1 else '✗'))
    ok = ok and a1

    adm('tree?lev=4')
    b = ask(13579)
    r = g.audit_body(sc['13579'], b, 13579)
    lv4, rest4, nm4 = parse(b)
    print('\n== 13579（lev=4）==')
    print('  tree_lev=%d name=%r' % (lv4, nm4))
    a2 = lv4 == 4 and nm4 != nm and nm4 != ''
    print('  ★ 膜拜类型随等级变化（%r → %r）⇒ %s' % (nm, nm4, '✓' if a2 else '✗'))
    ok = ok and a2

    adm('tree?lev=0')
    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
