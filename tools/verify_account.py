# -*- coding: utf-8 -*-
"""R44 验证：最小账号层 + `1110` 查表 + `10101` 真建角色。

核对四件事：
  1. `1110`（`dsh_local`）返回的角色列表**来自 DB**，含既有角色 rid=1001；
  2. **账号隔离**：另一个账号名下查不到 `dsh_local` 的角色；
  3. `10101` **真建角色**（原为桩），且新角色挂在当前账号名下；
  4. 同一账号下可建到 **2 个**角色并在 `1110` 里都列出来。

★ 全程用**独立测试账号** `r44_test`，不写玩家账号（`dsh_local`）的数据；
  默认测试结束**清理**测试角色（`--keep` 可保留）。

用法：python tools/verify_account.py [--keep]
"""
import argparse
import json
import os
import socket
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_live import pack_frame, recv_exact  # noqa: E402

PLAYER_UID = 'dsh_local'
TEST_UID = 'r44_test'
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def login_body(account):
    """CS_1110 = args:table(key:string, val:string)。"""
    kv = [('account', account), ('platform', 'ewan'), ('token', 'dsh_token')]
    out = struct.pack('>H', len(kv))
    for k, v in kv:
        out += w_str(k) + w_str(v)
    return out


def create_body(name, sex, career):
    """CS_10101 = {sex:u8, name:string, career:int16, playform:string}。"""
    return struct.pack('>B', sex) + w_str(name) + struct.pack('>h', career) + w_str('ewan')


def send(s, cmd, body=b''):
    s.sendall(pack_frame(cmd, body))
    while True:
        hdr = recv_exact(s, 6)
        (ln, rcmd) = struct.unpack('>IH', hdr)
        payload = recv_exact(s, ln - 2)
        if rcmd == cmd:
            return payload


def parse_1110(p):
    """-> (code, [(rid,name,lev,sex,career,online)])"""
    code = p[0]
    off = 1
    n = struct.unpack_from('>H', p, off)[0]; off += 2 + n      # msg
    cnt = struct.unpack_from('>H', p, off)[0]; off += 2
    rows = []
    for _ in range(cnt):
        rid = struct.unpack_from('>I', p, off)[0]; off += 4
        sl = struct.unpack_from('>H', p, off)[0]; off += 2 + sl
        nl = struct.unpack_from('>H', p, off)[0]
        nm = p[off + 2:off + 2 + nl].decode('utf-8', 'replace'); off += 2 + nl
        lev = struct.unpack_from('>H', p, off)[0]; off += 2
        sex = p[off]; off += 1
        car = struct.unpack_from('>H', p, off)[0]; off += 2
        on = p[off]; off += 1
        rows.append((rid, nm, lev, sex, car, on))
    return code, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()
    ok = True

    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    s.settimeout(5)

    # ---- 1) 玩家账号：应含既有角色 1001 ----
    code, rows = parse_1110(send(s, 1110, login_body(PLAYER_UID)))
    print('1110(%s): code=%d roles=%s' % (PLAYER_UID, code, rows))
    if code != 1 or not any(r[0] == 1001 for r in rows):
        print('   !! 玩家账号没查到既有角色 1001（会不会变孤儿？）')
        ok = False

    # ---- 2) 测试账号：应为空（账号隔离）----
    code, rows_t = parse_1110(send(s, 1110, login_body(TEST_UID)))
    print('1110(%s): code=%d roles=%s' % (TEST_UID, code, rows_t))
    if rows_t:
        print('   !! 测试账号不该有角色（数据残留？）')
        ok = False

    # ---- 3) 建 2 个角色 ----
    rids = []
    for i, (nm, sx, cr) in enumerate((('R44甲', 0, 1), ('R44乙', 1, 2))):
        p = send(s, 10101, create_body(nm, sx, cr))
        c = p[0]
        off = 1
        ml = struct.unpack_from('>H', p, off)[0]; off += 2 + ml
        rid = struct.unpack_from('>I', p, off)[0]
        print('10101 建角#%d: code=%d rid=%d name=%s' % (i + 1, c, rid, nm))
        if c != 1 or rid == 0:
            print('   !! 建角失败')
            ok = False
        else:
            rids.append(rid)

    # ---- 4) 测试账号应能看到 2 个角色 ----
    code, rows2 = parse_1110(send(s, 1110, login_body(TEST_UID)))
    print('1110(%s) 再次: code=%d roles=%s' % (TEST_UID, code, rows2))
    got = sorted(r[0] for r in rows2)
    if got != sorted(rids):
        print('   !! 期望 %s，实际 %s' % (sorted(rids), got))
        ok = False

    # ---- 5) 玩家账号仍只看到自己的角色（隔离）----
    code, rows3 = parse_1110(send(s, 1110, login_body(PLAYER_UID)))
    print('1110(%s) 复查: roles=%s' % (PLAYER_UID, rows3))
    if any(r[0] in rids for r in rows3):
        print('   !! 测试角色串到玩家账号里了')
        ok = False
    s.close()

    # ---- 清理测试角色（默认）----
    if rids and not args.keep:
        import sqlite3
        con = sqlite3.connect(DB)
        for rid in rids:
            for t in ('roles', 'role_attr', 'role_assets', 'bag_items',
                      'equip_items', 'store_items', 'missions', 'mall_bought'):
                try:
                    key = 'rid' if t != 'mall_bought' else 'rid'
                    con.execute('DELETE FROM %s WHERE %s=?' % (t, key), (rid,))
                except Exception:
                    pass
        con.execute('DELETE FROM accounts WHERE uid=?', (TEST_UID,))
        con.commit()
        con.close()
        print('已清理测试角色 %s 与测试账号 %s' % (rids, TEST_UID))

    print()
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
