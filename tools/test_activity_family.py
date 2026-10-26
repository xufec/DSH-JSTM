# -*- coding: utf-8 -*-
"""活动族（16605 / 10923 / 16602 / 16664）回归测试。

覆盖本会话（PHASE 2.18~2.21）对活动族的改动：
  · 16605：按 `bid_list` 逐条回 {bid, code=1, end_time=0}（客户端语义：code!=0=开启）
  · 10923：status 按 `config_function[id]` 门槛（is_open==1 且 open_lev<=lev）
  · 16602：`can_get_num` 对 id 505（成长目标）接真值（未领取天数）
  · 16664：msg/status/rate/bid 取自 `config_holiday_util`（无源字段保持 0/空）

★ 跑在真实角色 1001 上 ⇒ 快照并还原 `role_gt`。
用法：python tools/test_activity_family.py [--port 9000]
"""
import socket
import struct
import sys
import argparse
import sqlite3
import os
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "server", "state", "roles.db")
CFG_FUNC = os.path.join(ROOT, "server", "cfg", "config_function.json")
RID = 1001


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10)
        self.buf = b''
    def call(self, cmd, body=b'', maxskip=80):
        self.s.sendall(frame(cmd, body))
        for _ in range(maxskip):
            while len(self.buf) < 4:
                self.buf += self.s.recv(65536)
            ln = struct.unpack('>I', self.buf[:4])[0]
            while len(self.buf) < 4 + ln:
                self.buf += self.s.recv(65536)
            pay = self.buf[4:4 + ln]
            self.buf = self.buf[4 + ln:]
            c = struct.unpack('>H', pay[:2])[0]
            if c == cmd:
                return pay[2:]
        raise RuntimeError('no reply %d' % cmd)


class R:
    def __init__(self, b):
        self.b = b
        self.o = 0
    def u8(self):
        v = self.b[self.o]; self.o += 1; return v
    def u16(self):
        v = struct.unpack_from('>H', self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from('>I', self.b, self.o)[0]; self.o += 4; return v
    def s(self):
        n = self.u16()
        v = self.b[self.o:self.o + n].decode('utf-8', 'replace')
        self.o += n
        return v


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


def role_gt_rows():
    con = sqlite3.connect(DB)
    try:
        r = con.execute('SELECT login_day,charge_day,total_charge FROM role_gt WHERE rid=?',
                        (RID,)).fetchall()
    except Exception:
        r = []
    con.close()
    return r


def set_login_day(d):
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS role_gt (rid INTEGER PRIMARY KEY, login_day INTEGER, '
                'charge_day INTEGER, total_charge INTEGER)')
    con.execute('INSERT OR IGNORE INTO role_gt VALUES (?,0,0,0)', (RID,))
    con.execute('UPDATE role_gt SET login_day=? WHERE rid=?', (int(d), RID))
    con.commit(); con.close()


SNAP = {}


def snapshot():
    SNAP['gt'] = role_gt_rows()


def cleanup():
    con = sqlite3.connect(DB)
    try:
        con.execute('DELETE FROM role_gt WHERE rid=?', (RID,))
    except Exception:
        pass
    con.commit(); con.close()
    for row in (SNAP.get('gt') or []):
        con = sqlite3.connect(DB)
        con.execute('INSERT OR REPLACE INTO role_gt VALUES (?,?,?,?)', (RID, row[0], row[1], row[2]))
        con.commit(); con.close()
        break


F = []


def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c:
        F.append(n)


def parse_16602(b):
    r = R(b)
    t = r.u8()
    n = r.u16()
    out = []
    for _ in range(n):
        bid = r.u32(); cgn = r.u8()
        out.append((bid, cgn))
    return t, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    a = ap.parse_args()
    snapshot()

    func = json.load(open(CFG_FUNC, encoding='utf-8')).get('Function') or {}
    open_id, closed_id = 0, 0
    for k, v in func.items():
        h = (v.get('hash') if isinstance(v, dict) else v) or {}
        if not str(k).isdigit():
            continue
        if int(h.get('is_open') or 0) == 1 and int(h.get('open_lev') or 0) <= 70 and not open_id:
            open_id = int(k)
        if int(h.get('is_open') or 0) == 0 and not closed_id:
            closed_id = int(k)
    print('参照 id：is_open=1 -> %d ；is_open=0 -> %d' % (open_id, closed_id))

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', RID))
    print('connected %s:%d rid=%d' % (a.host, a.port, RID))

    print('\n[1] 16605：按 bid_list 逐条回 code=1')
    bids = [open_id, closed_id, 5007]
    body = struct.pack('>H', len(bids)) + b''.join(struct.pack('>I', x) for x in bids)
    b = c.call(16605, body)
    r = R(b)
    n = r.u16()
    got = []
    for _ in range(n):
        got.append((r.u32(), r.u8(), r.u32()))
    ck('16605 条数 == 请求数', n == len(bids), 'n=%d' % n)
    ck('16605 每条 code=1', all(g[1] == 1 for g in got), 'got=%s' % got)
    ck('16605 回显 bid 一致', [g[0] for g in got] == bids, 'got=%s' % [g[0] for g in got])

    print('\n[2] 10923：status 按 config_function 门槛')
    b = c.call(10923, struct.pack('>H', open_id)); r = R(b)
    i1 = r.u16(); s1 = r.u8(); n1 = r.u16()
    ck('10923 合格 id ⇒ status=1', s1 == 1 and i1 == open_id,
       'id=%d status=%d int_args=%d' % (i1, s1, n1))
    b = c.call(10923, struct.pack('>H', closed_id)); r = R(b)
    i2 = r.u16(); s2 = r.u8()
    ck('10923 未开 id ⇒ status=0', s2 == 0 and i2 == closed_id,
       'id=%d status=%d' % (i2, s2))
    b = c.call(10923, struct.pack('>H', 65000)); r = R(b)
    r.u16(); s3 = r.u8()
    ck('10923 未知 id ⇒ status=0', s3 == 0, 'status=%d' % s3)

    print('\n[3] 16602：can_get_num 对 id 505 接真值')
    set_login_day(0)
    _, lst0 = parse_16602(c.call(16602, struct.pack('>B', 0)))
    cgn_a = dict(lst0).get(505)
    set_login_day(1)
    _, lst1 = parse_16602(c.call(16602, struct.pack('>B', 0)))
    cgn_b = dict(lst1).get(505)
    ck('16602 含 id 505', cgn_a is not None, 'n=%d' % len(lst0))
    ck('16602 can_get_num 随已领天数递减', cgn_a is not None and cgn_b == cgn_a - 1,
       'login_day=0 -> %s ; =1 -> %s' % (cgn_a, cgn_b))
    ck('16602 其余条目 can_get_num=0', all(v == 0 for k, v in lst0 if k != 505),
       'non505非零=%s' % [(k, v) for k, v in lst0 if k != 505 and v][:3])

    print('\n[4] 16664：msg/status/rate/bid 取自 config_holiday_util')
    b = c.call(16664, struct.pack('>B', 0)); r = R(b)
    msg = r.s(); bid = r.u32(); rem = r.u32(); status = r.u32(); et = r.u32(); rate = r.u32()
    cr = r.s()
    ck('16664 status=1（charge_return_rule_switch）', status == 1, 'status=%d' % status)
    ck('16664 rate=500（charge_return_active_rate）', rate == 500, 'rate=%d' % rate)
    ck('16664 bid=62（module_flag=charge_double）', bid == 62, 'bid=%d' % bid)
    ck('16664 msg 非空（TipsConstant 文案）', len(msg) > 0, 'len(msg)=%d' % len(msg))
    ck('16664 无源字段保持 0/空', rem == 0 and et == 0 and cr == '',
       'remain=%d end=%d cr=%r' % (rem, et, cr))

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        try:
            cleanup()
        except Exception:
            pass
