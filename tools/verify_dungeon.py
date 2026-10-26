# -*- coding: utf-8 -*-
"""R45 验证：副本 / 爬塔进度快照。

核对四件事：
  1. 7 条命令（`13005/13034/13036/13045/13052/13058/21301`）应答**按权威规格精确解析**；
  2. **进度落库真实**：改 DB 里的层数后重新查询，返回值随之变化（不是写死的常量）；
  3. **多角色隔离**（R44 协同）：两个账号的角色各有独立进度，互不串数据；
  4. `13036` **不再回包**（回零值会让客户端 `key==0 → openView()` 死循环，
     实测风暴 22434 次/时 → 8 次/时）。

★ 玩家角色（`dsh_local` / rid=1001）**只读不写**；进度写入测试全部落在临时角色上并在结束时清理。

用法：python tools/verify_dungeon.py [--keep]
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
PLAYER_UID, TEST_UID = 'dsh_local', 'r45_test'
CMDS = [13005, 13034, 13035, 13036, 13038, 13042, 13045, 13052, 13058, 21301]

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
    """1110 账号登录 →（可选）10102 选角 → 返回该账号首个角色 rid。

    ★ 10102 必须发：角色切换就发生在这里（R45 修复点）。
    """
    body = struct.pack('>H', 1) + w_str('account') + w_str(account)
    s.sendall(pack_frame(1110, body))
    got = None
    while True:
        hdr = recv_exact(s, 6)
        (ln, rcmd) = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rcmd == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]; off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]; off += 2
            if not cnt:
                return None
            got = struct.unpack_from('>I', p, off)[0]
            break
    want = rid or got
    # CS_10102{rid:u32, srv_id:string}
    s.sendall(pack_frame(10102, struct.pack('>I', want) + w_str('1')))
    s.settimeout(2.0)
    try:
        while True:
            hdr = recv_exact(s, 6)
            (ln, rcmd) = struct.unpack('>IH', hdr)
            recv_exact(s, ln - 2)
            if rcmd == 10102:
                break
    except Exception:
        pass
    s.settimeout(5)
    return want


def call(s, cmd, body=b'', timeout=2.0):
    s.sendall(pack_frame(cmd, body))
    old = s.gettimeout()
    s.settimeout(timeout)
    try:
        while True:
            hdr = recv_exact(s, 6)
            (ln, rcmd) = struct.unpack('>IH', hdr)
            p = recv_exact(s, ln - 2)
            if rcmd == cmd:
                return p
    except Exception:
        return None
    finally:
        s.settimeout(old)


def q(sql, args=()):
    con = sqlite3.connect(DB)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()
    ok = True

    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    s.settimeout(5)
    rid = login(s, PLAYER_UID)
    print('玩家角色 rid=%s（全程只读）' % rid)

    # ---- 1) 7 条命令按规格解析 ----
    print('\n== 规格一致性（玩家角色）==')
    for c in CMDS:
        body = b''
        if c == 13005:
            body = struct.pack('>I', 40001) + b'\x04'
        elif c == 13034:
            body = struct.pack('>I', 40001)
        elif c in (13035, 13038):
            body = struct.pack('>I', 40002) + b'\x09'      # {Bid/dung_bid, ceng=9}
        elif c == 13036:
            body = struct.pack('>I', 40001) + b'\x04\x00'
        elif c == 13045:
            body = struct.pack('>I', 1)
        elif c == 13058:
            body = struct.pack('>I', 40001)
        p = call(s, c, body)
        if p is None:
            if c == 13036:
                print('  SC_%-6d 无应答 —— 期望如此（见 §4）' % c)
                continue
            print('  SC_%-6d !! 无应答' % c)
            ok = False
            continue
        off, errs, un = parse_full(p, sc_spec(c))
        good = (not errs) and off == len(p)
        print('  SC_%-6d len=%-4d 解析=%-4d %s' % (c, len(p), off, 'PASS' if good else 'FAIL ' + str(errs)))
        if not good:
            ok = False

    # ---- 2) 进度真实：在测试角色上写 DB，再查 ----
    print('\n== 进度落库真实性（测试角色）==')
    s2 = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    s2.settimeout(5)
    login(s2, TEST_UID)          # ensure account
    p = call(s2, 10101, struct.pack('>B', 0) + w_str('R45测') + struct.pack('>h', 1) + w_str('ewan'))
    off = 1
    ml = struct.unpack_from('>H', p, off)[0]; off += 2 + ml
    trid = struct.unpack_from('>I', p, off)[0]
    print('  测试角色 rid=%d' % trid)

    con = sqlite3.connect(DB)
    con.execute('INSERT OR REPLACE INTO dungeon_progress (rid,ptype,pkey,value) VALUES (?,?,?,?)',
                (trid, 'tower_floor', '21301', 7))
    for f in (1, 2, 3):
        con.execute('INSERT OR REPLACE INTO dungeon_progress (rid,ptype,pkey,value) VALUES (?,?,?,?)',
                    (trid, 'tower_clear', str(f), 1))
    con.commit()
    con.close()

    s3 = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    s3.settimeout(5)
    rid3 = login(s3, TEST_UID, trid)
    p3 = call(s3, 21301, b'')
    floor3 = struct.unpack_from('>I', p3, 4)[0]      # tower_id 后的 floor
    # 玩家角色的层数（应不同）
    p1 = call(s, 21301, b'')
    floor1 = struct.unpack_from('>I', p1, 4)[0]

    # ---- 13042 必须与 21301 **同源**（口径一致）----
    p42 = call(s3, 13042, b'')
    hi42 = struct.unpack_from('>I', p42, 0)[0]
    off = 4 + 2                       # high_floor + ceng_list(count=0)
    off += 1 + 1 + 4                  # status + cur_ceng + left_time
    nclear = struct.unpack_from('>H', p42, off)[0]; off += 2
    clears = [p42[off + i] for i in range(nclear)]
    print('  13042: high_floor=%d cur_ceng=%d clear_list=%s'
          % (hi42, p42[7], clears))
    if hi42 != floor3:
        print('   !! 13042.high_floor(%d) != 21301.floor(%d) ⇒ 两处口径不一致'
              % (hi42, floor3))
        ok = False
    else:
        print('   ✓ 13042 与 21301 同源（都取 tower_floor）')
    if clears != [1, 2, 3]:
        print('   !! clear_list 期望 [1,2,3]，实际 %s' % clears)
        ok = False
    else:
        print('   ✓ clear_list 来自 DB（tower_clear）')

    print('  测试角色(%d) floor=%d ｜ 玩家角色(%d) floor=%d' % (rid3, floor3, rid, floor1))
    if floor3 != 7:
        print('   !! 测试角色没读到落库的 7 ⇒ 进度没走 DB')
        ok = False
    else:
        print('   ✓ 进度来自 DB（写了 7 就读到 7）')
    if floor1 == 7:
        print('   !! 两个角色串数据了')
        ok = False
    else:
        print('   ✓ 多角色隔离（玩家角色仍是 %d）' % floor1)

    # ---- 3) 清理 ----
    if not args.keep:
        con = sqlite3.connect(DB)
        for t in ('roles', 'role_attr', 'role_assets', 'bag_items', 'equip_items',
                  'store_items', 'missions', 'mall_bought', 'dungeon_progress'):
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
