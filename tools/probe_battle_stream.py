# -*- coding: utf-8 -*-
"""战斗链逐帧观察：20002 开战后 12 秒内把**每一帧**带时间打出来。

用途：确认"服务端定时器推回合"是否真的到达客户端（自检工具曾报"回合推进停住"，
而服务端日志显示确实在推 ⇒ 需要逐帧看，判断是工具漏收还是真没到）。

用法：python tools/probe_battle_stream.py
"""
import os
import socket
import sqlite3
import struct
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'server'))
HOST, PORT = '127.0.0.1', 9000
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
UID = 'bst_%d' % int(time.time())
WATCH = 12.0


def frame(cmd, body=b''):
    return struct.pack('>IH', len(body) + 2, cmd) + body


def tlv(**kv):
    b = struct.pack('>H', len(kv))
    for k, v in kv.items():
        v = str(v).encode()
        b += struct.pack('>H', len(k)) + k.encode() + struct.pack('>H', len(v)) + v
    return b


def drain(sock, buf, seconds):
    out, end = [], time.time() + seconds
    sock.settimeout(0.5)
    while time.time() < end:
        try:
            d = sock.recv(65536)
        except socket.timeout:
            continue
        except Exception as e:
            print('   !! recv: %r' % (e,)); break
        if not d:
            print('   !! 连接被关闭'); break
        buf += d
        while len(buf) >= 6:
            ln = struct.unpack_from('>I', buf, 0)[0]
            if len(buf) < 4 + ln:
                break
            cmd = struct.unpack_from('>H', buf, 4)[0]
            body = buf[6:4 + ln]
            out.append((cmd, body, time.time()))
            buf = buf[4 + ln:]
    return out, buf


def main():
    s = socket.create_connection((HOST, PORT), timeout=8)
    s.sendall(frame(1110, tlv(account=UID, token='bst123456', enter_srv_id='1')))
    drain(s, b'', 1.5)
    con = sqlite3.connect(DB, timeout=10)
    row = con.execute('SELECT rid FROM roles WHERE uid=?', (UID,)).fetchone()
    con.close()
    if not row:
        nm = UID[-8:]
        s.sendall(frame(10101, struct.pack('>B', 1) + struct.pack('>B', len(nm)) + nm.encode()
                        + struct.pack('>B', 1) + struct.pack('>H', 1001)))
        drain(s, b'', 1.5)
        con = sqlite3.connect(DB, timeout=10)
        row = con.execute('SELECT rid FROM roles WHERE uid=?', (UID,)).fetchone()
        con.close()
    rid = int(row[0])
    s.sendall(frame(10102, struct.pack('>I', rid) + struct.pack('>B', 1)))
    drain(s, b'', 2.0)
    print('== 账号 %s rid=%d 开战 ==' % (UID, rid))

    t0 = time.time()
    s.sendall(frame(20002, struct.pack('>i', 20001)))
    frames, buf = drain(s, b'', WATCH)
    print('== %.1fs 内收到 %d 帧 ==' % (WATCH, len(frames)))
    for cmd, body, ts in frames:
        print('  +%5.2fs  cmd=%-6d %4d 字节  %s'
              % (ts - t0, cmd, len(body), body[:14].hex(' ')))
    codes = {}
    for cmd, _, _ in frames:
        codes[cmd] = codes.get(cmd, 0) + 1
    print('== 按命令计数:', dict(sorted(codes.items())))

    try:
        con = sqlite3.connect(DB, timeout=10)
        rids = [int(r[0]) for r in con.execute('SELECT rid FROM roles WHERE uid=?', (UID,))]
        for t in ('roles', 'role_attr', 'role_assets', 'missions', 'bag_items', 'equip_items',
                  'role_heros', 'role_buffs', 'role_skills', 'dungeon_progress', 'chengjiu_progress'):
            for r in rids:
                try:
                    con.execute('DELETE FROM %s WHERE rid=?' % t, (r,))
                except Exception:
                    pass
        con.execute('DELETE FROM accounts WHERE uid=?', (UID,))
        con.commit(); con.close()
        print('== 清理完成 ==')
    except Exception as e:
        print('!! 清理失败: %r' % (e,))
    return 0


if __name__ == '__main__':
    sys.exit(main())
