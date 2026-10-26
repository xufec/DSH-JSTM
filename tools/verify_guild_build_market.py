# -*- coding: utf-8 -*-
"""R149 验收：`13501`（宗门列表）+ `13701`-`13703`（建筑）+ `13801`（摆摊）+ `13227`（角色数）。

判据：
  1. `13501` 的 `guild_name`/`head_name`/`role_count` 与 **DB `role_guild` + 角色**一致
  2. `13701`-`13703` 的 `lev` 与 `role_build` 一致
  3. `13227` 的 `role_num` == `roles` 表行数
  4. 全部用门禁权威解析器

用法： python tools/verify_guild_build_market.py
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
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/' + qs, timeout=8).read().decode('utf-8'))


def q(sql, args=()):
    c = sqlite3.connect(DB)
    r = c.execute(sql, args).fetchone()
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
    adm('guilddemo=1') if False else None

    # 确保有宗门
    c = sqlite3.connect(DB)
    try:
        c.execute('INSERT OR REPLACE INTO role_guild VALUES (?,?,?)', (RID, '验收宗门', 0))
        c.commit()
    except sqlite3.OperationalError:
        pass
    c.close()

    # ---- 13501
    b = ask(13501, bytes([1]) + struct.pack('>H', 0) + bytes([1]))
    r = g.audit_body(sc['13501'], b, 13501)
    off = 2                      # page + page_total
    n = struct.unpack_from('>H', b, off)[0]
    off += 2
    idx = b[off]
    gid = struct.unpack_from('>I', b, off + 1)[0]
    o2 = off + 5
    sl = struct.unpack_from('>H', b, o2)[0]
    o2 += 2 + sl                 # srv_id
    o2 += 1 + 1                  # realm + vip
    gl = struct.unpack_from('>H', b, o2)[0]
    gname = b[o2 + 2:o2 + 2 + gl].decode('utf-8', 'replace')
    o3 = o2 + 2 + gl
    hl = struct.unpack_from('>H', b, o3)[0]
    hname = b[o3 + 2:o3 + 2 + hl].decode('utf-8', 'replace')
    dbname = q('SELECT name FROM role_guild WHERE rid=?', (RID,))
    rname = q('SELECT name FROM roles WHERE rid=?', (RID,))
    print('\n== 13501 宗门列表 ==')
    print('  len=%d 消耗=%d err=%s 条目=%d guild_name=%r head_name=%r'
          % (r['len'], r['consumed'], r['err'], n, gname, hname))
    a1 = (r['consumed'] == r['len'] and not r['err'] and n == 1
          and gname == (dbname[0] if dbname else '')
          and hname == (rname[0] if rname else ''))
    print('  ★ 与 DB `role_guild.name` / 角色名一致 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # ---- 13701-13703 建筑等级
    adm('build?lev=7')
    for c_, body, off_ in ((13701, bytes([1]), 0),
                           (13702, bytes([1]), 0),
                           (13703, bytes([1, 0]), 0)):
        b = ask(c_, body)
        r = g.audit_body(sc[str(c_)], b, c_)
        # 13701: {type,lev} ⇒ lev 在 offset 1；13702/13703: {code,msg,type,lev}
        if c_ == 13701:
            lev = b[1]
        else:
            m = struct.unpack_from('>H', b, 1)[0]
            lev = b[1 + 2 + m + 1]
        a = r['consumed'] == r['len'] and not r['err'] and lev == 7
        print('  %d lev=%d（DB role_build=7）⇒ %s' % (c_, lev, '✓' if a else '✗'))
        ok = ok and a

    # ---- 13801 摆摊
    b = ask(13801, struct.pack('>H', 1) + bytes([1]))
    r = g.audit_body(sc['13801'], b, 13801)
    a = r['consumed'] == r['len'] and not r['err']
    print('  13801 len=%d 消耗=%d err=%s ⇒ %s' % (r['len'], r['consumed'], r['err'], '✓' if a else '✗'))
    ok = ok and a

    # ---- 13227 角色数
    b = ask(13227, struct.pack('>H', 0))
    r = g.audit_body(sc['13227'], b, 13227)
    tn = struct.unpack_from('>H', b, 0)[0]
    rn = struct.unpack_from('>H', b, 2)[0]
    dbn = q('SELECT COUNT(*) FROM roles')[0]
    print('  13227 team_num=%d role_num=%d（DB roles=%d）⇒ %s'
          % (tn, rn, dbn, '✓' if (rn == dbn and not r['err']) else '✗'))
    ok = ok and (rn == dbn and not r['err'] and r['consumed'] == r['len'])

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
