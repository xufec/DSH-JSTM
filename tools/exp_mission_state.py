# -*- coding: utf-8 -*-
"""R59 实验：把 `missions` 里 10010 的状态改成「进行中」，看客户端/`SC_12400` 是否就认得它。

背景：`ghost_mon` proto#4 的反汇编显示 `CS_15402` 的发送条件是
      `mis_key == <某线> and <该任务在途>`；而真机上点完 4019（`15400`）之后
      客户端并不发 `15402`。我们库里 10010 的 `mission_status=3`（= 不在途）。
本脚本只改这一行，并把原值打印出来以便回滚。**不做真机操作**。

用法：
    python tools/exp_mission_state.py            # 只读，打印当前状态
    python tools/exp_mission_state.py --set 2    # 改成 2 并复读
    python tools/exp_mission_state.py --restore 3
"""
import io
import sqlite3
import struct
import sys
import socket
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from audit_sc_live import pack_frame, recv_exact  # noqa: E402

DB = r'server\state\roles.db'
RID, BID = 1001, 10010


def show():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for r in con.execute('SELECT * FROM missions WHERE rid=? AND mission_bid=?', (RID, BID)):
        d = dict(r)
        print('  10010:', {k: d[k] for k in ('mission_status', 'process_status', 'commit_num',
                                             'loop_count', 'loop_num', 'target', 'value')})
    con.close()


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def q12400():
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(5.0)
    s.sendall(pack_frame(1110, struct.pack('>H', 1) + w_str('account') + w_str('dsh_local')))
    rid = None
    while True:
        hdr = recv_exact(s, 6)
        ln, rc = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]
            off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]
            off += 2
            rid = struct.unpack_from('>I', p, off)[0] if cnt else None
            break
    if rid:
        s.sendall(pack_frame(10102, struct.pack('>I', rid) + w_str('1')))
        s.settimeout(2.0)
        try:
            while True:
                hdr = recv_exact(s, 6)
                ln, rc = struct.unpack('>IH', hdr)
                recv_exact(s, ln - 2)
                if rc == 10102:
                    break
        except socket.timeout:
            pass
    s.settimeout(5.0)
    s.sendall(pack_frame(12400, b''))
    while True:
        hdr = recv_exact(s, 6)
        ln, rc = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == 12400:
            break
    s.close()
    cnt = struct.unpack_from('>H', p, 0)[0]
    off = 2
    bids = []
    for _ in range(cnt):
        # mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16,
        # loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32, value:u32
        mb = struct.unpack_from('>I', p, off)[0]
        st = p[off + 4]
        bids.append((mb, st))
        off += 4 + 1 + 2 + 2 + 2 + 1 + 1 + 4 + 4 + 4
    return cnt, bids


print('当前 missions：')
show()
cnt, bids = q12400()
print('SC_12400 mission_list=%d → %s' % (cnt, bids))

if '--set' in sys.argv:
    v = int(sys.argv[sys.argv.index('--set') + 1])
    con = sqlite3.connect(DB)
    con.execute('UPDATE missions SET mission_status=? WHERE rid=? AND mission_bid=?', (v, RID, BID))
    con.commit()
    con.close()
    print('\n已把 10010.mission_status 改为', v)
    show()
    print('  （真机保持不动，需重启客户端才会重新拉 12400）')
