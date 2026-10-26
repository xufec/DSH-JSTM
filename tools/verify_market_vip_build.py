# -*- coding: utf-8 -*-
"""R140 验收：`13806`（摆摊）+ `16706`（VIP 道具）+ `13741`（建筑技能）。

判据（都以**数据库/真实状态**为准）：
  1. `13806` 未上架 ⇒ `goods_list` 0 条；上架后 ⇒ **与 DB 一致**
  2. `16706` `status` 随 `roles.vip_level` 变化（0 ⇒ 0；>0 ⇒ 1）
  3. `13741` `lev`/`learn_list` 与 DB 一致

用法： python tools/verify_market_vip_build.py
"""
import io
import json
import os
import socket
import sqlite3
import struct
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), 'server', 'state', 'roles.db')
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


def adm(qs):
    return urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/' + qs, timeout=8).read().decode('utf-8')


def ex(sql, args=()):
    """容错执行：**表还不存在**时（服务端首次调用才建表）静默跳过。"""
    c = sqlite3.connect(DB)
    try:
        c.execute(sql, args)
        c.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        c.close()


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

    # ---- 13806 摆摊
    ex('DELETE FROM role_market_goods WHERE rid=?', (RID,))
    b = ask(13806)
    r = g.audit_body(sc['13806'], b, 13806)
    n0 = struct.unpack_from('>H', b, 1)[0]
    adm('marketgoods?market_id=1&item_bid=21903&item_num=2&price=500')
    b = ask(13806)
    r2 = g.audit_body(sc['13806'], b, 13806)
    n1 = struct.unpack_from('>H', b, 1)[0]
    ib = struct.unpack_from('>I', b, 3 + 4)[0] if n1 else 0
    print('\n== 13806 摆摊 ==')
    print('  未上架: len=%d err=%s 条目=%d' % (r['len'], r['err'], n0))
    print('  上架后: len=%d 消耗=%d err=%s 条目=%d item_bid=%d'
          % (r2['len'], r2['consumed'], r2['err'], n1, ib))
    a1 = n0 == 0 and n1 == 1 and ib == 21903 and r2['consumed'] == r2['len']
    print('  ★ 空/上架都能真实反映 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 16706 VIP
    ex('UPDATE roles SET vip_level=0 WHERE rid=?', (RID,))
    s0 = ask(16706)[0]
    ex('UPDATE roles SET vip_level=3 WHERE rid=?', (RID,))
    b = ask(16706)
    r3 = g.audit_body(sc['16706'], b, 16706)
    s1 = b[0]
    print('\n== 16706 VIP ==')
    print('  vip=0 ⇒ status=%d ｜ vip=3 ⇒ status=%d（len=%d err=%s）'
          % (s0, s1, r3['len'], r3['err']))
    a2 = s0 == 0 and s1 == 1 and r3['consumed'] == r3['len']
    print('  ★ status 随真实 VIP 等级变化 ⇒ %s' % ('✓' if a2 else '✗'))
    ok = ok and a2
    ex('UPDATE roles SET vip_level=0 WHERE rid=?', (RID,))

    # ---- 13741 建筑
    ex('DELETE FROM role_build WHERE rid=?', (RID,))
    ex('DELETE FROM role_build_learn WHERE rid=?', (RID,))
    b = ask(13741)
    r4 = g.audit_body(sc['13741'], b, 13741)
    lv0 = b[0]
    n0 = struct.unpack_from('>H', b, 1)[0]
    adm('build?lev=5')
    adm('build?learn=30001')
    adm('build?learn=30002')
    b = ask(13741)
    r5 = g.audit_body(sc['13741'], b, 13741)
    lv1 = b[0]
    n1 = struct.unpack_from('>H', b, 1)[0]
    print('\n== 13741 建筑技能 ==')
    print('  未学: lev=%d 列表=%d ｜ 学习后: lev=%d 列表=%d（len=%d 消耗=%d err=%s）'
          % (lv0, n0, lv1, n1, r5['len'], r5['consumed'], r5['err']))
    a3 = lv1 == 5 and n1 == 2 and r5['consumed'] == r5['len']
    print('  ★ lev/learn_list 与 DB 一致 ⇒ %s' % ('✓' if a3 else '✗'))
    ok = ok and a3

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
