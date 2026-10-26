# -*- coding: utf-8 -*-
"""开服成长计划（30500/30501/30502）测试。

★ 跑在真实角色 1001 上 ⇒ **快照并还原背包 / reward_log / role_gt**，不留残留。
用法：python tools/test_growth_target.py [--port 9000]
"""
import socket, struct, sys, argparse, sqlite3, os, json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "server", "state", "roles.db")
RID = 1001
# config_growth_target_data day1: login_reward{36500x5,36006x3} charge_reward{25104x3,36010x1,25327x5}
DAY = 1
LOGIN_BIDS = (36500, 36006)
CHARGE_BIDS = (25104, 36010, 25327)
ALL_BIDS = LOGIN_BIDS + CHARGE_BIDS


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10); self.buf = b''
    def call(self, cmd, body=b'', maxskip=60):
        self.s.sendall(frame(cmd, body))
        for _ in range(maxskip):
            while len(self.buf) < 4:
                self.buf += self.s.recv(65536)
            ln = struct.unpack('>I', self.buf[:4])[0]
            while len(self.buf) < 4 + ln:
                self.buf += self.s.recv(65536)
            pay = self.buf[4:4 + ln]; self.buf = self.buf[4 + ln:]
            c = struct.unpack('>H', pay[:2])[0]
            if c == cmd:
                return c, pay[2:]
        raise RuntimeError('no reply %d' % cmd)


class R:
    def __init__(self, b): self.b = b; self.o = 0
    def u8(self): v = self.b[self.o]; self.o += 1; return v
    def u16(self):
        v = struct.unpack_from('>H', self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from('>I', self.b, self.o)[0]; self.o += 4; return v
    def s(self):
        n = self.u16(); v = self.b[self.o:self.o + n].decode('utf-8', 'replace')
        self.o += n; return v


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


def bag(rid, bid):
    con = sqlite3.connect(DB)
    try:
        n = con.execute('SELECT COALESCE(SUM(quantity),0) FROM bag_items WHERE rid=? AND bid=?',
                        (rid, bid)).fetchone()[0]
    except Exception:
        n = 0
    con.close(); return int(n or 0)


def set_bag(rid, bid, target):
    con = sqlite3.connect(DB)
    rows = con.execute('SELECT item_id,quantity FROM bag_items WHERE rid=? AND bid=? ORDER BY item_id',
                       (rid, bid)).fetchall()
    cur = sum(int(r[1]) for r in rows)
    if cur == target:
        con.close(); return
    if cur < target:
        if rows:
            con.execute('UPDATE bag_items SET quantity=quantity+? WHERE rid=? AND item_id=?',
                        (target - cur, rid, rows[-1][0]))
        con.commit(); con.close(); return
    need = cur - target
    for item_id, qty in reversed(rows):
        if need <= 0:
            break
        take = min(int(qty), need); left = int(qty) - take
        if left <= 0:
            con.execute('DELETE FROM bag_items WHERE rid=? AND item_id=?', (rid, item_id))
        else:
            con.execute('UPDATE bag_items SET quantity=? WHERE rid=? AND item_id=?', (left, rid, item_id))
        need -= take
    con.commit(); con.close()


def set_charge(rid, amount):
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS role_gt (rid INTEGER PRIMARY KEY, login_day INTEGER, '
                'charge_day INTEGER, total_charge INTEGER)')
    con.execute('INSERT OR IGNORE INTO role_gt VALUES (?,0,0,0)', (rid,))
    con.execute('UPDATE role_gt SET total_charge=? WHERE rid=?', (amount, rid))
    con.commit(); con.close()


SNAP = {}


def snapshot():
    SNAP['bag'] = {b: bag(RID, b) for b in ALL_BIDS}
    con = sqlite3.connect(DB)
    try:
        SNAP['gt'] = con.execute('SELECT login_day,charge_day,total_charge FROM role_gt WHERE rid=?',
                                 (RID,)).fetchone()
    except Exception:
        SNAP['gt'] = None
    con.close()


def cleanup():
    con = sqlite3.connect(DB)
    try:
        con.execute("DELETE FROM reward_log WHERE rid=? AND source='growth_target'", (RID,))
    except Exception:
        pass
    try:
        con.execute('DELETE FROM role_gt WHERE rid=?', (RID,))
    except Exception:
        pass
    con.commit(); con.close()
    for bid, want in (SNAP.get('bag') or {}).items():
        set_bag(RID, bid, want)


F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c:
        F.append(n)


def parse_items(r):
    n = r.u16()
    out = {}
    for _ in range(n):
        bid = r.u32()          # ★ 必须先赋值再取第二个（不能写 out[r.u32()]=r.u32()：
        num = r.u32()          #   Python 会先算右侧，导致 bid/num 反读）
        out[bid] = num
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()
    snapshot(); cleanup()
    before = {b: bag(RID, b) for b in ALL_BIDS}

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', RID))
    for _ in range(10):
        try:
            c.s.settimeout(0.3); c.buf += c.s.recv(65536)
        except Exception:
            break
    c.s.settimeout(3)
    print('connected %s:%d rid=%d' % (a.host, a.port, RID))

    print('\n[1] 30501 领取登录奖励 day=%d' % DAY)
    cmd, b = c.call(30501, struct.pack('>B', DAY)); r = R(b)
    res = r.u8(); msg = r.s(); items = parse_items(r)
    ck('30501 result=1', res == 1, 'result=%d msg=%r' % (res, msg))
    ck('30501 发对物品', items.get(36500) == 5 and items.get(36006) == 3, 'items=%s' % items)
    ck('背包 36500 +5', bag(RID, 36500) - before[36500] == 5,
       'before=%d after=%d' % (before[36500], bag(RID, 36500)))

    print('\n[2] 30501 重复领取 ⇒ 拒绝')
    cmd, b = c.call(30501, struct.pack('>B', DAY)); r = R(b)
    res = r.u8(); msg = r.s()
    ck('30501 二次 result=0', res == 0, 'result=%d msg=%r' % (res, msg))
    ck('背包未变', bag(RID, 36500) - before[36500] == 5)

    print('\n[3] 30502 累计充值不足 ⇒ 拒绝')
    set_charge(RID, 0)
    cmd, b = c.call(30502, struct.pack('>B', DAY)); r = R(b)
    res = r.u8(); msg = r.s()
    ck('30502 result=0', res == 0, 'result=%d msg=%r' % (res, msg))

    print('\n[4] 30502 满足 charge_gold=80 ⇒ 领取成功')
    set_charge(RID, 80)
    cmd, b = c.call(30502, struct.pack('>B', DAY)); r = R(b)
    res = r.u8(); msg = r.s(); items = parse_items(r)
    ck('30502 result=1', res == 1, 'result=%d msg=%r' % (res, msg))
    ck('30502 发对物品', items.get(25104) == 3 and items.get(25327) == 5, 'items=%s' % items)
    ck('背包 25104 +3', bag(RID, 25104) - before[25104] == 3)

    print('\n[5] 30502 重复 ⇒ 拒绝；30500 真值状态')
    cmd, b = c.call(30502, struct.pack('>B', DAY)); r = R(b)
    ck('30502 二次 result=0', r.u8() == 0)
    cmd, b = c.call(30500); r = R(b)
    code = r.u8(); r.s(); cur = r.u32(); r.u32(); n = r.u16()
    d1 = None
    for _ in range(n):
        d = r.u8(); ls = r.u8(); cs = r.u8(); tc = r.u32(); r.u16(); r.u8(); r.u8()
        if d == DAY:
            d1 = (ls, cs, tc)
    ck('30500 code=1', code == 1)
    ck('30500 day1 已领(登录/充值)=1/1 累计充值=80', d1 == (1, 1, 80), 'day1=%s' % (d1,))
    _ = cur

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
