# -*- coding: utf-8 -*-
"""静默命令探针：对运行中的服务端逐条发命令，看**到底有没有回包**。

背景（2026-10-17）：命令覆盖审计（tools/audit_cmd_coverage.py）从日志统计出 36 个
"客户端请求了但服务端没回包"的命令。日志只能证明"没写 `<< cmd=N` 这行"，不能证明
"没发包"（也可能 handler 走了别的日志格式）⇒ 需要**实测**。

本探针：临时建号 → 登录 1 区 → 建角 → 进场景 → 逐条发命令 → 收包 → **清理**。
每一行输出 `cmd / 是否回包 / 回包字节数 / 前 16 字节`。

用法：
    python tools/probe_silent_cmds.py                 # 默认探针集合
    python tools/probe_silent_cmds.py 16400 11206     # 指定命令
    python tools/probe_silent_cmds.py --zone 1
"""
import argparse
import os
import socket
import sqlite3
import struct
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST, PORT = '127.0.0.1', 9000
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
UID = 'probe_%d' % int(time.time())
PWD = 'probe123456'

DEFAULT_CMDS = [16400, 19400, 19406, 13042, 14000, 11700, 11300, 11301,
                11206, 10528, 10534, 20028, 20500, 20504, 20002, 30715, 15405]


def frame(cmd, body=b''):
    return struct.pack('>IH', len(body) + 2, cmd) + body


def read_frames(buf, timeout=2.5):
    """收一小段时间，返回 [(cmd, body), ...]（尽量把已有数据读干）。"""
    out = []
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = _sock.recv(65536)
        except socket.timeout:
            break
        except Exception:
            break
        if not r:
            break
        buf += r
        while len(buf) >= 6:
            ln = struct.unpack_from('>I', buf, 0)[0]
            if len(buf) < 4 + ln:
                break
            cmd = struct.unpack_from('>H', buf, 4)[0]
            out.append((cmd, buf[6:4 + ln]))
            buf = buf[4 + ln:]
    return out, buf


def send_cs(cmd, body=b''):
    global _sock
    _sock.sendall(frame(cmd, body))


def tlv(**kv):
    """CS 的 table<k,v>/字符串对（u16 计数 + (u16 len,bytes) 对）。"""
    b = struct.pack('>H', len(kv))
    for k, v in kv.items():
        v = str(v).encode()
        b += struct.pack('>H', len(k)) + k.encode() + struct.pack('>H', len(v)) + v
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmds', nargs='*', type=int)
    ap.add_argument('--zone', default='1')
    ap.add_argument('--wait', type=float, default=2.0)
    a = ap.parse_args()
    cmds = a.cmds or DEFAULT_CMDS

    global _sock
    print('== 探针账号 %s（zone %s）==' % (UID, a.zone))
    _sock = socket.create_connection((HOST, PORT), timeout=8)

    # 1) 登录（幂等：首次登录绑定密码）
    send_cs(1110, tlv(account=UID, token=PWD, enter_srv_id=a.zone))
    got, _ = read_frames(b'', a.wait)
    code = next((b[0] for c, b in got if c == 1110), None)
    print('  1110 登录 code=%s' % code)
    if code != 1:
        print('  !! 登录失败，探针中止'); return 2

    # 2) 取角色（没有就建一个）
    rid = None
    for c, b in got:
        if c == 1110 and len(b) >= 4:
            pass
    send_cs(10102, struct.pack('>I', 0)[:0])   # 占位，不用
    # 直接从 DB 读（探针自己建的号，读库最快）
    con = sqlite3.connect(DB, timeout=10)
    row = con.execute('SELECT rid FROM roles WHERE uid=? AND srv_id=?', (UID, str(a.zone))).fetchone()
    if row:
        rid = int(row[0])
    else:
        nm = UID[-8:]
        send_cs(10101, struct.pack('>B', 1) + struct.pack('>B', len(nm)) + nm.encode()
                + struct.pack('>B', 1) + struct.pack('>H', 1001))
        got2, _ = read_frames(b'', a.wait)
        c10101 = next((b for c, b in got2 if c == 10101), None)
        print('  10101 建角 code=%s' % (c10101[0] if c10101 else None))
        row = con.execute('SELECT rid FROM roles WHERE uid=? AND srv_id=?', (UID, str(a.zone))).fetchone()
        rid = int(row[0]) if row else None
    con.close()
    if rid is None:
        print('  !! 没拿到 rid，探针中止'); return 2
    print('  rid = %d' % rid)

    # 3) 进角色：CS_10102 = rid(u32) + 区服字节（真机编码）
    send_cs(10102, struct.pack('>I', rid) + struct.pack('>B', int(a.zone)))
    got3, _ = read_frames(b'', a.wait)
    c10102 = next((b for c, b in got3 if c == 10102), None)
    print('  10102 进角色 code=%s（随后推送 %d 帧）'
          % (c10102[0] if c10102 else None, len(got3)))
    time.sleep(1.0)
    read_frames(b'', 1.0)          # 把推送读干净

    # 4) 逐条探针
    print('\n== 逐条探针（等待 %.1fs）==' % a.wait)
    silent = []
    for cmd in cmds:
        send_cs(cmd)
        got, _ = read_frames(b'', a.wait)
        mine = [b for c, b in got if c == cmd]
        if mine:
            body = mine[0]
            print('  %-6d 回包 ✔  %4d 字节  %s' % (cmd, len(body), body[:16].hex(' ')))
        else:
            other = sorted(set(c for c, _ in got))
            print('  %-6d 无回包 ✘  （期间收到其它帧: %s）' % (cmd, other or '无'))
            silent.append(cmd)

    # 5) 清理
    try:
        con = sqlite3.connect(DB, timeout=10)
        rids = [int(r[0]) for r in con.execute('SELECT rid FROM roles WHERE uid=?', (UID,))]
        for t in ('roles', 'role_attr', 'role_assets', 'missions', 'bag_items', 'equip_items',
                  'store_items', 'role_heros', 'role_buffs', 'dungeon_progress', 'chengjiu_progress'):
            for r in rids:
                try:
                    con.execute('DELETE FROM %s WHERE rid=?' % t, (r,))
                except Exception:
                    pass
        con.execute('DELETE FROM accounts WHERE uid=?', (UID,))
        con.commit(); con.close()
        print('\n  清理完成（删账号 %s 与 %d 个角色行）' % (UID, len(rids)))
    except Exception as e:
        print('\n  !! 清理失败: %r' % (e,))

    print('\n结论: %d/%d 条回包 ｜ 静默: %s' % (len(cmds) - len(silent), len(cmds), silent or '无'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
