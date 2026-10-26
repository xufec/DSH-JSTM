# -*- coding: utf-8 -*-
"""R47 验证：荣耀竞技场（`11300` / `11307` / `11308`）。

核对四件事：
  1. 三条应答按权威规格**精确解析**（`11300` 含 `pk_show` 与 `pk_record` 两个子表）；
  2. **状态真实**：写 DB(`arena_state`) 后查询随之变化（trophy/times/win_times/state）；
  3. **战绩真实**：写 DB(`arena_record`) 后 `11300.pk_record` 与 `11307` 都能列出；
  4. **多角色隔离** + `pk_show` 为空（无诚实来源，不编对手）。

★ 玩家角色（`dsh_local`/1001）只读；测试数据落在临时角色上并在结束时清理。

用法：python tools/verify_arena.py [--keep]
"""
import argparse
import json
import os
import socket
import sqlite3
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_conformance import parse_full  # noqa: E402
from audit_sc_live import pack_frame, recv_exact  # noqa: E402

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
PLAYER_UID, TEST_UID = 'dsh_local', 'r47_test'

with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
    FIELDS = json.load(f)


def sc_spec(cmd):
    for k, v in FIELDS.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def login(s, account, rid=None):
    s.sendall(pack_frame(1110, struct.pack('>H', 1) + w_str('account') + w_str(account)))
    got = None
    while True:
        hdr = recv_exact(s, 6)
        (ln, rc) = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]; off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]; off += 2
            got = struct.unpack_from('>I', p, off)[0] if cnt else None
            break
    want = rid or got
    if want:
        s.sendall(pack_frame(10102, struct.pack('>I', want) + w_str('1')))
        s.settimeout(2.0)
        try:
            while True:
                hdr = recv_exact(s, 6)
                (ln, rc) = struct.unpack('>IH', hdr)
                recv_exact(s, ln - 2)
                if rc == 10102:
                    break
        except Exception:
            pass
        s.settimeout(5)
    return want


def call(s, cmd, body=b'', timeout=3.0):
    s.sendall(pack_frame(cmd, body))
    old = s.gettimeout()
    s.settimeout(timeout)
    try:
        while True:
            hdr = recv_exact(s, 6)
            (ln, rc) = struct.unpack('>IH', hdr)
            p = recv_exact(s, ln - 2)
            if rc == cmd:
                return p
    except Exception:
        return None
    finally:
        s.settimeout(old)


def parse_11300(p):
    """-> (trophy, times, index_state, shows, recs)

    shows: [(id, rid, name, lev, career, trophy)]
    recs : [(type, rid, name, result, trophy, counter)]
    """
    trophy = struct.unpack_from('>I', p, 0)[0]
    times, idx = p[4], p[5]
    n_show = struct.unpack_from('>H', p, 6)[0]
    off = 8
    shows = []
    for _ in range(n_show):
        sid = p[off]; off += 1
        srid = struct.unpack_from('>I', p, off)[0]; off += 4
        sl = struct.unpack_from('>H', p, off)[0]; off += 2 + sl
        nl = struct.unpack_from('>H', p, off)[0]
        nm = p[off + 2:off + 2 + nl].decode('utf-8', 'replace'); off += 2 + nl
        lev = struct.unpack_from('>H', p, off)[0]; off += 2
        car = struct.unpack_from('>H', p, off)[0]; off += 2
        off += 1                                   # sex
        tro = struct.unpack_from('>I', p, off)[0]; off += 4
        np_ = struct.unpack_from('>H', p, off)[0]; off += 2
        for _j in range(np_):                      # partner_list（本服为空）
            off += 4
            sl2 = struct.unpack_from('>H', p, off)[0]; off += 2 + sl2
            off += 4 + 4 + 1 + 1
        off += 1                                   # arena_soul
        shows.append((sid, srid, nm, lev, car, tro))
    n_rec = struct.unpack_from('>H', p, off)[0]; off += 2
    recs = []
    for _ in range(n_rec):
        typ = p[off]; off += 1
        rid = struct.unpack_from('>I', p, off)[0]; off += 4
        sl = struct.unpack_from('>H', p, off)[0]; off += 2 + sl
        nl = struct.unpack_from('>H', p, off)[0]
        nm = p[off + 2:off + 2 + nl].decode('utf-8', 'replace'); off += 2 + nl
        res = p[off]; off += 1
        tro = struct.unpack_from('>I', p, off)[0]; off += 4
        counter = p[off]; off += 1
        rl = struct.unpack_from('>H', p, off)[0]; off += 2 + rl
        recs.append((typ, rid, nm, res, tro, counter))
    return trophy, times, idx, shows, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()
    ok = True

    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    s.settimeout(5)
    rid = login(s, PLAYER_UID)
    print('玩家角色 rid=%s（只读）' % rid)

    # ---- 1) 规格一致性 ----
    print('\n== 规格一致性 ==')
    groups = {}
    for c in (11300, 11307, 11308):
        p = call(s, c, b'')
        if p is None:
            print('  SC_%-6d !! 无应答' % c)
            ok = False
            continue
        off, errs, un = parse_full(p, sc_spec(c))
        good = (not errs) and off == len(p)
        print('  SC_%-6d len=%-4d 解析=%-4d %s' % (c, len(p), off, 'PASS' if good else 'FAIL ' + str(errs)))
        if not good:
            ok = False
        groups[c] = p
    tr, tm, ix, shows, recs = parse_11300(groups[11300])
    print('  11300: trophy=%d times=%d index_state=%d pk_show=%s pk_record=%d'
          % (tr, tm, ix, [(s[1], s[2]) for s in shows], len(recs)))

    # ---- 2) 状态真实 + 战绩真实（测试角色）----
    print('\n== 状态/战绩落库真实性（测试角色）==')
    s2 = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    s2.settimeout(5)
    login(s2, TEST_UID)
    p = call(s2, 10101, struct.pack('>B', 0) + w_str('R47测') + struct.pack('>h', 1) + w_str('ewan'))
    off = 1
    ml = struct.unpack_from('>H', p, off)[0]; off += 2 + ml
    trid = struct.unpack_from('>I', p, off)[0]
    print('  测试角色 rid=%d' % trid)

    con = sqlite3.connect(DB)
    con.execute('INSERT OR REPLACE INTO arena_state '
                '(rid,trophy,times,index_state,win_times,state,updated_at) '
                'VALUES (?,?,?,?,?,?,0)', (trid, 1234, 5, 1, 7, 2))
    con.execute('INSERT OR REPLACE INTO arena_record '
                '(rid,seq,type,opp_rid,opp_srv,opp_name,result,trophy,'
                ' is_counterattack,reply_id,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,0)',
                (trid, 1, 3, 9001, '1', '对手甲', 1, 12, 0, ''))
    con.commit()
    con.close()

    s3 = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    s3.settimeout(5)
    rid3 = login(s3, TEST_UID, trid)
    p0 = call(s3, 11300, b'')
    t0, tm0, ix0, shows0, recs0 = parse_11300(p0)
    p8 = call(s3, 11308, b'')
    wt, stt = p8[0], p8[1]
    p7 = call(s3, 11307, b'')
    t7 = struct.unpack_from('>I', p7, 0)[0]
    n7 = struct.unpack_from('>H', p7, 4)[0]
    first0 = recs0[0] if recs0 else None
    print('  11300: trophy=%d times=%d index_state=%d records=%d 首条=%s'
          % (t0, tm0, ix0, len(recs0), first0))
    print('  11307: trophy=%d records=%d' % (t7, n7))
    print('  11308: win_times=%d state=%d' % (wt, stt))
    for label, got, want in (('trophy', t0, 1234), ('times', tm0, 5),
                             ('win_times', wt, 7), ('state', stt, 2),
                             ('记录数', len(recs0), 1), ('11307 记录数', n7, 1)):
        if got != want:
            print('   !! %s 期望 %s 实际 %s' % (label, want, got))
            ok = False
    if first0 and first0[2] == '对手甲' and first0[3] == 1:
        print('   ✓ 战绩来自 DB（对手甲 / 胜）')
    else:
        print('   !! 战绩内容不符 %s' % (first0,))
        ok = False

    # ---- ★ 对手源 = 本服已有角色（项目方决策 A）----
    print('\n== 对手源：本服已有角色（决策 A）==')
    p_pl = call(s, 11300, b'')
    _, _, _, shows_pl, _ = parse_11300(p_pl)
    print('  玩家(1001) 看到的对手: %s' % [(x[1], x[2], x[3], x[4]) for x in shows_pl])
    print('  测试(2001) 看到的对手: %s' % [(x[1], x[2], x[3], x[4]) for x in shows0])
    if not any(x[1] == trid and x[2] == 'R47测' for x in shows_pl):
        print('   !! 玩家没把测试角色看成对手')
        ok = False
    else:
        print('   ✓ 玩家(1001) 的对手里含测试角色(2001)「R47测」（真实角色数据）')
    if not any(x[1] == rid and x[2] == 'DSH' for x in shows0):
        print('   !! 测试角色没把玩家看成对手')
        ok = False
    else:
        print('   ✓ 测试角色(2001) 的对手里含玩家(1001)「DSH」')
    if any(x[1] == trid for x in shows0):
        print('   !! 对手列表里出现了自己')
        ok = False
    else:
        print('   ✓ 对手列表不含自己')

    # ---- 3) 玩家角色隔离 ----
    p1 = call(s, 11300, b'')
    t1 = struct.unpack_from('>I', p1, 0)[0]
    _, _, _, _, recs1 = parse_11300(p1)
    print('  玩家角色 11300: trophy=%d records=%d' % (t1, len(recs1)))
    if t1 == 1234 or len(recs1) != 0:
        print('   !! 测试数据串到玩家角色了')
        ok = False
    else:
        print('   ✓ 多角色隔离')

    # ---- 4) 清理 ----
    if not args.keep:
        con = sqlite3.connect(DB)
        for t in ('roles', 'role_attr', 'role_assets', 'bag_items', 'equip_items',
                  'store_items', 'missions', 'mall_bought', 'dungeon_progress',
                  'arena_state', 'arena_record'):
            try:
                con.execute('DELETE FROM %s WHERE rid=?' % t, (trid,))
            except Exception:
                pass
        con.execute('DELETE FROM accounts WHERE uid=?', (TEST_UID,))
        con.commit()
        con.close()
        print('\n  已清理测试角色 %d 与测试账号 %s' % (trid, TEST_UID))

    for x in (s, s2, s3):
        try:
            x.close()
        except Exception:
            pass
    print()
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
