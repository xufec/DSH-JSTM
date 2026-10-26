# -*- coding: utf-8 -*-
"""刮刮乐（16651/16652）测试。

★ 跑在真实角色 1001 上 ⇒ 快照并还原：背包(28031) / 钻石(gold) / role_scratch* / reward_log(scratch)。
用法：python tools/test_scratch.py [--port 9000]
"""
import socket, struct, sys, argparse, sqlite3, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "server", "state", "roles.db")
RID = 1001
ITEM = 28031
TIERS = {100, 200, 300, 500, 1000, 2000}


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


def q1(sql, p=()):
    con = sqlite3.connect(DB)
    try:
        r = con.execute(sql, p).fetchone()
    except Exception:
        r = None
    con.close(); return r


def bag(rid, bid):
    r = q1('SELECT COALESCE(SUM(quantity),0) FROM bag_items WHERE rid=? AND bid=?', (rid, bid))
    return int(r[0] or 0) if r else 0


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
        else:
            nid = con.execute('SELECT COALESCE(MAX(item_id),0)+1 FROM bag_items WHERE rid=?',
                              (rid,)).fetchone()[0]
            pos = con.execute('SELECT COALESCE(MAX(pos),0)+1 FROM bag_items WHERE rid=?',
                              (rid,)).fetchone()[0]
            con.execute('INSERT INTO bag_items (rid,bag_code,item_id,bid,pos,quantity,ctime) '
                        'VALUES (?,1,?,?,?,?,0)', (rid, int(nid), bid, int(pos), target))
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


def gold(rid):
    r = q1('SELECT COALESCE(amount,0) FROM role_assets WHERE rid=? AND name=?', (rid, 'gold'))
    return int(r[0] or 0) if r else 0


def set_gold(rid, amount):
    con = sqlite3.connect(DB)
    con.execute('INSERT OR REPLACE INTO role_assets (rid,name,amount) VALUES (?,?,?)',
                (rid, 'gold', int(amount)))
    con.commit(); con.close()


SNAP = {}


def snapshot():
    SNAP['item'] = bag(RID, ITEM)
    SNAP['gold'] = gold(RID)


def cleanup():
    con = sqlite3.connect(DB)
    for sql in ('DELETE FROM role_scratch', 'DELETE FROM role_scratch_tier'):
        try:
            con.execute(sql)
        except Exception:
            pass
    try:
        con.execute("DELETE FROM reward_log WHERE rid=? AND source='scratch'", (RID,))
    except Exception:
        pass
    con.commit(); con.close()
    set_bag(RID, ITEM, SNAP.get('item', 0))
    set_gold(RID, SNAP.get('gold', 0))


F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c:
        F.append(n)


def parse_16651(b):
    r = R(b)
    code = r.u8(); msg = r.s(); remain = r.u32(); cash = r.u32()
    n = r.u16(); cards = []
    for _ in range(n):
        cards.append((r.u32(), r.u32(), r.u32(), r.u8()))   # index, card_id, gold, status
    r.u16(); r.u16()                                        # item_list / item_effect_list
    cli = r.s()
    return {'code': code, 'msg': msg, 'cash': cash, 'cards': cards, 'client_reward': cli}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()
    snapshot()
    # 造 3 个刮卡道具（并保证有钻石基线的快照）
    set_bag(RID, ITEM, 3)
    d0 = gold(RID)

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', RID))
    for _ in range(10):
        try:
            c.s.settimeout(0.3); c.buf += c.s.recv(65536)
        except Exception:
            break
    c.s.settimeout(3)
    print('connected %s:%d rid=%d（item=%d 已备 3 个）' % (a.host, a.port, RID, ITEM))

    print('\n[1] 16651 初始（无盘面）')
    cmd, b = c.call(16651); d = parse_16651(b)
    ck('16651 code=1', d['code'] == 1)
    ck('初始无盘面 cards=0', len(d['cards']) == 0, 'cards=%d' % len(d['cards']))
    ck('初始 cash_reward=0', d['cash'] == 0)

    print('\n[2] 16652 刮第 0 格 ⇒ 开新盘并消耗 1 个道具')
    cmd, b = c.call(16652, struct.pack('>I', 0)); r = R(b)
    res = r.u8(); msg = r.s(); ix = r.u32(); st = r.u8()
    ck('16652 code=1', res == 1, 'res=%d msg=%r' % (res, msg))
    ck('16652 回显 index=0', ix == 0)
    ck('16652 status=1', st == 1, 'status=%d' % st)
    ck('道具 -1（剩 2）', bag(RID, ITEM) == 2, 'item=%d' % bag(RID, ITEM))

    print('\n[3] 16651 应见 3 张【同卡】盘面')
    cmd, b = c.call(16651); d = parse_16651(b)
    ck('cards=3', len(d['cards']) == 3, 'cards=%d' % len(d['cards']))
    ids = {x[1] for x in d['cards']}
    ck('3 张 card_id 相同（规则：必出 3 张相同）', len(ids) == 1, 'ids=%s' % ids)
    golds = {x[2] for x in d['cards']}
    ck('奖励值一致且合法', len(golds) == 1 and list(golds)[0] in TIERS, 'golds=%s' % golds)
    ck('已刮 1 格', sum(1 for x in d['cards'] if x[3]) == 1)

    print('\n[4] 刮完第 1、2 格')
    dg = gold(RID)          # ★ 必须在"最后一格刮开之前"采样：开奖在那一刻发生
    for i in (1, 2):
        cmd, b = c.call(16652, struct.pack('>I', i)); r = R(b)
        res = r.u8(); r.s(); ix = r.u32(); st = r.u8()
        ck('16652 index=%d code=1 status=1' % i, res == 1 and st == 1, 'res=%d st=%d' % (res, st))

    print('\n[5] 16651 开奖：cash_reward=档位钻石，且钻石真入账')
    cmd, b = c.call(16651); d = parse_16651(b)
    ck('cash_reward 合法档位', d['cash'] in TIERS, 'cash=%d' % d['cash'])
    ck('钻石 +cash', gold(RID) - dg == d['cash'],
       'before=%d after=%d cash=%d' % (dg, gold(RID), d['cash']))
    ck('开奖后盘面清空', len(d['cards']) == 0, 'cards=%d' % len(d['cards']))

    print('\n[6] 再开一盘：道具不足时应拒绝')
    set_bag(RID, ITEM, 0)
    cmd, b = c.call(16652, struct.pack('>I', 0)); r = R(b)
    res = r.u8(); msg = r.s()
    ck('无道具 ⇒ code=0', res == 0, 'res=%d msg=%r' % (res, msg))

    cleanup()
    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    _ = d0
    return 1 if F else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        try:
            cleanup()
        except Exception:
            pass
