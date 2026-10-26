# -*- coding: utf-8 -*-
"""R45 反向测试：10102 请求非法 rid 时的安全性。

必须满足：
  1. 请求**不存在**的 rid ⇒ 不切换（仍是自己的角色）、**不得在 roles 表建行**；
  2. 请求**属于别的账号**的 rid ⇒ 不切换（防越权）；
  3. 玩家正常登录（rid == 自己的角色）⇒ 行为与改动前一致。

用法：python tools/verify_role_switch_guard.py
"""
import os
import socket
import sqlite3
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_live import pack_frame, recv_exact  # noqa: E402

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def rd(s, cmd, timeout=2.0):
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


def login_account(s, account):
    body = struct.pack('>H', 1) + w_str('account') + w_str(account)
    s.sendall(pack_frame(1110, body))
    return rd(s, 1110)


def pick_role(s, rid):
    s.sendall(pack_frame(10102, struct.pack('>I', rid) + w_str('1')))
    return rd(s, 10102)


def whoami(s):
    """用 10304 取当前连接实际生效的 rid。"""
    s.sendall(pack_frame(10304, b''))
    p = rd(s, 10304, 3.0)
    return struct.unpack_from('>I', p, 0)[0] if p else None


def rows():
    con = sqlite3.connect(DB)
    try:
        return sorted(r[0] for r in con.execute('SELECT rid FROM roles'))
    finally:
        con.close()


def main():
    ok = True
    before = rows()
    print('初始 roles:', before)

    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    login_account(s, 'dsh_local')
    print('  登录后 whoami =', whoami(s))

    # ---- 1) 不存在的 rid ----
    pick_role(s, 99999)
    me = whoami(s)
    print('  请求 rid=99999 后 whoami =', me)
    if me != 1001:
        print('   !! 竟然切走了'); ok = False
    if rows() != before:
        print('   !! roles 表被建了新行:', rows()); ok = False
    else:
        print('   ✓ 未切换、未建行')

    # ---- 2) 伪造：把别人的 rid 拿来（用一个临时账号造一个角色）----
    con = sqlite3.connect(DB)
    con.execute('INSERT OR IGNORE INTO accounts (uid,name,create_ts) VALUES (?,?,0)', ('guard_test', 'g'))
    con.execute('INSERT OR IGNORE INTO roles (rid,uid,name,level) VALUES (?,?,?,?)', (3001, 'guard_test', 'G', 5))
    con.commit(); con.close()
    pick_role(s, 3001)
    me = whoami(s)
    print('  请求别人的 rid=3001 后 whoami =', me)
    if me != 1001:
        print('   !! 越权切换成功（严重）'); ok = False
    else:
        print('   ✓ 拒绝越权（仍是自己的角色）')

    # 清理
    con = sqlite3.connect(DB)
    for t in ('roles', 'role_attr', 'role_assets', 'bag_items', 'equip_items',
              'store_items', 'missions', 'mall_bought', 'dungeon_progress'):
        try:
            con.execute('DELETE FROM %s WHERE rid=?' % t, (3001,))
        except Exception:
            pass
    con.execute("DELETE FROM accounts WHERE uid='guard_test'")
    con.commit(); con.close()
    print('  已清理 3001 与 guard_test')

    # ---- 3) 正常登录（自己的 rid）----
    pick_role(s, 1001)
    me = whoami(s)
    print('  正常登录 rid=1001 后 whoami =', me)
    if me != 1001:
        print('   !! 正常路径异常'); ok = False
    else:
        print('   ✓ 正常路径无变化')

    s.close()
    print()
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
