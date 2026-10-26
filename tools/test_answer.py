# -*- coding: utf-8 -*-
"""答题活动（16100~16103）测试。

覆盖：次数查询 → 开始 → 判题（对/错）→ 逐题推进 → 结算发奖（按 AnswerAward 阈值）→ 幂等。
★ 依赖 `server/answer_key.json`（项目推导键，非原版数据）。

用法：python tools/test_answer.py [--port 9000]
"""
import socket, struct, sys, argparse, json, os, sqlite3

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "server", "state", "roles.db")
KEY = os.path.join(ROOT, "server", "answer_key.json")
RID = 1001
OPT = ('a', 'b', 'c', 'd')


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10)
        self.buf = b''
    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))
    def recv(self):
        while len(self.buf) < 4:
            d = self.s.recv(65536)
            if not d:
                raise RuntimeError('closed')
            self.buf += d
        ln = struct.unpack('>I', self.buf[:4])[0]
        while len(self.buf) < 4 + ln:
            self.buf += self.s.recv(65536)
        pay = self.buf[4:4 + ln]
        self.buf = self.buf[4 + ln:]
        return struct.unpack('>H', pay[:2])[0], pay[2:]
    def call(self, cmd, body=b'', maxskip=60):
        self.send(cmd, body)
        for _ in range(maxskip):
            c, b = self.recv()
            if c == cmd:
                return c, b
        raise RuntimeError('no reply %d' % cmd)
    def settle(self, rounds=12):
        self.s.settimeout(0.4)
        try:
            for _ in range(rounds):
                self.recv()
        except Exception:
            pass
        finally:
            self.s.settimeout(3)


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


def bag_count(rid, bid):
    con = sqlite3.connect(DB)
    try:
        n = con.execute('SELECT COALESCE(SUM(quantity),0) FROM bag_items WHERE rid=? AND bid=?',
                        (rid, bid)).fetchone()[0]
    except Exception:
        n = 0
    con.close()
    return int(n or 0)


# ★ 本测试跑在**真实角色 1001** 上，发奖会真入包 ⇒ 必须**快照并还原**，
#   否则会污染在线的 DSH 存档（2026-10-06 首次跑就发生过一次，已手动还原）。
SNAP = {}


def snapshot():
    SNAP['bag'] = {bid: bag_count(RID, bid) for bid in (36500, 25300)}


def _set_bag(rid, bid, target):
    con = sqlite3.connect(DB)
    rows = con.execute('SELECT item_id,quantity FROM bag_items WHERE rid=? AND bid=? ORDER BY item_id',
                       (rid, bid)).fetchall()
    cur = sum(int(r[1]) for r in rows)
    if cur == target:
        con.close(); return
    if cur < target:                     # 缺 ⇒ 补到最后一个（或新建）
        if rows:
            con.execute('UPDATE bag_items SET quantity=quantity+? WHERE rid=? AND item_id=?',
                        (target - cur, rid, rows[-1][0]))
        con.commit(); con.close(); return
    need = cur - target                  # 多 ⇒ 从后往前扣
    for item_id, qty in reversed(rows):
        if need <= 0:
            break
        take = min(int(qty), need)
        left = int(qty) - take
        if left <= 0:
            con.execute('DELETE FROM bag_items WHERE rid=? AND item_id=?', (rid, item_id))
        else:
            con.execute('UPDATE bag_items SET quantity=? WHERE rid=? AND item_id=?',
                        (left, rid, item_id))
        need -= take
    con.commit(); con.close()


def cleanup():
    con = sqlite3.connect(DB)
    try:
        con.execute('DELETE FROM role_answer')
    except Exception:
        pass
    try:                                  # 撤销本测试发出的奖励记录
        con.execute("DELETE FROM reward_log WHERE rid=? AND source='answer'", (RID,))
    except Exception:
        pass
    con.commit(); con.close()
    for bid, want in (SNAP.get('bag') or {}).items():   # 背包还原到测试前
        _set_bag(RID, bid, want)


F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c:
        F.append(n)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000); a = ap.parse_args()
    if not os.path.exists(KEY):
        print('!! 缺少 %s（答案键未生成）' % KEY); return 2
    key = (json.load(open(KEY, encoding='utf-8')) or {}).get('answers') or {}
    print('answer key entries = %d' % len(key))

    snapshot()
    cleanup()
    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', RID)); c.settle()
    print('connected %s:%d rid=%d' % (a.host, a.port, RID))

    print('\n[1] 16100 查询今日次数')
    cmd, b = c.call(16100); r = R(b); n = r.u8()
    ck('16100 cmd', cmd == 16100)
    ck('16100 count>0', n > 0, 'count=%d' % n)

    print('\n[2] 16101 开始答题')
    cmd, b = c.call(16101); r = R(b)
    code = r.u8(); msg = r.s(); lt = r.u32(); idx = r.u8(); cum = r.u8(); qid = r.u32()
    ck('16101 code=1', code == 1, 'code=%d msg=%r' % (code, msg))
    if code != 1:
        # 时段外/次数用完等 ⇒ 优雅退出（不崩），并明确说明原因，便于 RUN_TESTS 判 SKIP
        print('\n[SKIP] 无法开始答题：%s（时段外需以 DSH_ANSWER_OPEN=1 启动 mock_server）' % msg)
        cleanup()
        return 0
    ck('16101 第 1 题', idx == 1, 'idx=%d' % idx)
    ck('16101 有题干 qid', qid != 0, 'qid=%d' % qid)
    ck('16101 有答案键', str(qid) in key, 'qid=%d' % qid)

    print('\n[3] 16102 提交【正确】答案')
    ci = OPT.index(key[str(qid)])
    cmd, b = c.call(16102, struct.pack('>I', qid) + struct.pack('>B', ci))
    r = R(b); i2 = r.u8(); cum2 = r.u8(); ca = r.u8(); q2 = r.u32()
    ck('16102 回正确序号', ca == ci, 'correct_answer=%d expect=%d' % (ca, ci))
    ck('16102 累计对=1', cum2 == 1, 'cum=%d' % cum2)

    print('\n[4] 再答 7 题（全对）⇒ 累计对=8 ⇒ 应触发 AnswerAward 第 1 档(36500×3)')
    before = bag_count(RID, 36500)
    for k in range(7):
        cmd, b = c.call(16101); r = R(b)
        _code = r.u8(); _m = r.s(); r.u32(); _idx = r.u8(); _cum = r.u8(); _q = r.u32()
        if _q == 0:
            ck('第 %d 题存在' % (k + 2), False, 'qid=0'); break
        _ci = OPT.index(key.get(str(_q), 'a'))
        cmd, b = c.call(16102, struct.pack('>I', _q) + struct.pack('>B', _ci))
        r = R(b); r.u8(); _cum2 = r.u8(); r.u8(); r.u32()
    ck('累计对=8', _cum2 == 8, 'cum=%d' % _cum2)

    print('\n[5] 16103 结算（超时上交 correct_num）')
    cmd, b = c.call(16103, struct.pack('>B', 8)); r = R(b); fin = r.u8()
    ck('16103 回 correct_num=8', fin == 8, 'fin=%d' % fin)
    after = bag_count(RID, 36500)
    ck('奖励已发放 36500 +3', after - before == 3, 'before=%d after=%d' % (before, after))

    print('\n[6] 幂等：重复结算不再发')
    cmd, b = c.call(16103, struct.pack('>B', 8)); r = R(b)
    after2 = bag_count(RID, 36500)
    ck('重复结算不重复发', after2 == after, 'after=%d after2=%d' % (after, after2))

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
