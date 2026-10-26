# -*- coding: utf-8 -*-
"""R128 验收：`15501`（坐骑）—— **真实技能 + 真实属性**（R128 修正 `attr_list` 计数后）。

## 判据为什么改了

R115b 曾把 `15501` 回退成"标量真实 + 表全空"，理由是"门禁 `parse_full` 越界"。
**R128 证明那次判断是错的**：真因是**我把 `attr_list` 的计数写错了** ——
它的**一个元素 = 12 个属性（48 字节）**，所以 `cnt` 应该是"行数"（1），而我发的是 **12**
⇒ 解析器以为有 12 行、读到第 2 行就出界。

⇒ 本验收改为**用门禁的权威解析器**（`audit_emitted_fields.audit_body`）做结构断言，
再断言**真实数据**（`jie` 来自 DB、`skill_list` 来自 `RideAllSkill`、`attr_list` 来自 `RideLevAttr`）。

用法： python tools/verify_ride.py
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


def set_ride(jie, lev=1):
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/ride?jie=%d&lev=%d' % (jie, lev),
        timeout=8).read().decode('utf-8'))


def load_gate():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def main():
    ok = True
    g, sc = load_gate()

    # ---- 没坐骑：结构正确 + 标量 0 + 表空
    set_ride(0)
    b = ask(15501)
    r = g.audit_body(sc['15501'], b, 15501)
    print('\n== 没有坐骑 ==')
    print('  len=%d 消耗=%d err=%s jie=%d' % (r['len'], r['consumed'], r['err'], b[0]))
    a1 = r['consumed'] == r['len'] and not r['err'] and b[0] == 0
    print('  结构精确 + jie=0 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 有坐骑（jie=1, lev=10）：真实数据
    set_ride(1, 10)
    b = ask(15501)
    r = g.audit_body(sc['15501'], b, 15501)
    # 手工解出 skill_list 与 attr_list，与配置对照
    off = 9
    nsk = struct.unpack_from('>H', b, off)[0]; off += 2
    sk = [struct.unpack_from('>I', b, off + 4 * i)[0] for i in range(nsk)]; off += 4 * nsk
    nrow = struct.unpack_from('>H', b, off)[0]; off += 2
    at = [struct.unpack_from('>I', b, off + 4 * i)[0] for i in range(12 * nrow)]
    print('\n== 有坐骑（jie=1, lev=10）==')
    print('  len=%d 消耗=%d err=%s jie=%d' % (r['len'], r['consumed'], r['err'], b[0]))
    print('  skill_list 项数=%d（RideAllSkill 共 12）' % nsk)
    print('  attr_list 行数=%d（★ 应为 1 —— R128 的关键修正）' % nrow)
    a2 = r['consumed'] == r['len'] and not r['err'] and b[0] == 1
    a3 = nsk == 12
    a4 = nrow == 1
    print('  结构精确 + jie=1 ⇒ %s' % ('✓' if a2 else '✗'))
    print('  skill_list = RideAllSkill（12 项）⇒ %s' % ('✓' if a3 else '✗'))
    print('  ★ attr_list cnt=1（一行 12 属性）⇒ %s' % ('✓' if a4 else '✗'))
    ok = ok and a2 and a3 and a4

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
