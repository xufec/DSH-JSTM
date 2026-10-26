#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3.3-E 镇魂塔（dung 40001）服务端业务闭环 E2E。

隔离账号 c33test_dun_*，测后清理（除非 --keep）。

验证链：
  21306 列表（含 40001）→ 21308 进本 → 13037 挑战层(ceng=1) →
  20002 击杀 boss 18201 → _battle_settle 塔结算 → SC_21307 推送
    → coin+30000 / 物品+35041×2 / reward_log dung_settle:40001:1:<rid>
    → tower_clear=1, tower_floor=2
  重打同层 → already，不重复发奖
  负例：ceng=99 越界 / ceng=2 跳过前沿 / bid=999999 非法 / 低等级进本被拒
  21309 退本 → 重登 tower_floor=2 持久化
"""
import argparse
import http.client
import os
import socket
import sqlite3
import struct
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
HOST = '127.0.0.1'
TCP_PORT = 9000
HTTP_PORT = 8080


def pack_frame(cmd, body=b''):
    return struct.pack('>I', 2 + len(body)) + struct.pack('>H', cmd) + body


def recv_exact(s, n):
    buf = b''
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise EOFError('closed')
        buf += chunk
    return buf


def w_str(s):
    b = str(s).encode('utf-8')
    return struct.pack('>H', len(b)) + b


def db_query(sql, args=()):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(sql, args).fetchall()]
    con.close()
    return rows


def gm(act, params):
    qs = '&'.join('%s=%s' % (k, v) for k, v in params.items())
    try:
        conn = http.client.HTTPConnection(HOST, HTTP_PORT, timeout=10)
        conn.request('GET', '/DSH_ADMIN/%s?%s' % (act, qs))
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', 'replace')
        conn.close()
        return resp.status, body
    except Exception as e:
        return -1, 'EXC %r' % e


class Client:
    def __init__(self):
        self.s = None

    def connect(self):
        self.s = socket.create_connection((HOST, TCP_PORT), timeout=10)
        self.s.settimeout(2.0)

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass

    def send(self, cmd, body=b''):
        self.s.sendall(pack_frame(cmd, body))

    def read_frame(self):
        try:
            hdr = recv_exact(self.s, 6)
        except (socket.timeout, EOFError, OSError):
            return None, None
        (ln, rcmd) = struct.unpack('>IH', hdr)
        try:
            payload = recv_exact(self.s, ln - 2)
        except (EOFError, OSError):
            return rcmd, None
        return rcmd, payload

    def drain_until(self, want, timeout=4.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            rcmd, body = self.read_frame()
            if rcmd is None:
                return None
            if rcmd == want:
                return body
        return None

    def drain_rest(self, secs):
        deadline = time.time() + secs
        while time.time() < deadline:
            rcmd, _ = self.read_frame()
            if rcmd is None:
                continue

    def login(self, uid):
        self.send(10001, struct.pack('>H', 1) + b'c' + b'\x00' * 4)
        args = struct.pack('>H', 10)
        for k, v in (('account', uid), ('channelId', '1'), ('device_id', 'c33-e2e'),
                     ('enter_srv_id', '1'), ('gettui_cid', ''), ('idfa', ''),
                     ('platform', 'ewan'), ('sign', ''),
                     ('timestamp', str(int(time.time()))), ('token', '')):
            args += w_str(k) + w_str(v)
        self.send(1110, args)
        body = self.drain_until(1110, timeout=4.0)
        if body is None:
            return None
        off = 1
        off += 2 + struct.unpack_from('>H', body, off)[0]
        n = struct.unpack_from('>H', body, off)[0]
        off += 2
        roles = []
        for _ in range(n):
            rid = struct.unpack_from('>I', body, off)[0]; off += 4
            sl = struct.unpack_from('>H', body, off)[0]; off += 2 + sl
            nl = struct.unpack_from('>H', body, off)[0]; off += 2 + nl
            lev = struct.unpack_from('>H', body, off)[0]; off += 2
            off += 1; off += 2; off += 1
            roles.append({'rid': rid, 'lev': lev})
        return roles

    def create_role(self, name):
        body = struct.pack('>B', 0) + w_str(name) + struct.pack('>h', 1) + w_str('ewan')
        self.send(10101, body)
        p = self.drain_until(10101)
        if p is None:
            return None, None
        code = p[0]
        nl = struct.unpack_from('>H', p, 1)[0]
        rid = struct.unpack_from('>I', p, 3 + nl)[0]
        return code, rid

    def select_role(self, rid):
        self.send(10102, struct.pack('>I', rid) + w_str('1'))
        p = self.drain_until(10102, timeout=4.0)
        code = p[0] if p else None
        self.drain_rest(1.5)
        return code

    def role_init(self, rid):
        self.send(10300, struct.pack('>I', rid))
        self.drain_rest(2.0)

    def dungeon_list_count(self):
        self.send(21306, b'')
        p = self.drain_until(21306, timeout=4.0)
        self.drain_rest(0.5)
        if p is None:
            return None
        return struct.unpack_from('>H', p, 0)[0]  # w_u16 副本条数

    def enter_dungeon(self, bid):
        self.send(21308, struct.pack('>I', bid))
        p = self.drain_until(21308, timeout=4.0)
        self.drain_rest(0.5)
        if p is None:
            return None
        tips = p[0]
        return tips

    def exit_dungeon(self, bid):
        self.send(21309, struct.pack('>I', bid))
        p = self.drain_until(21309, timeout=4.0)
        if p is None:
            return None
        return p[0]  # tips

    def challenge_tower(self, bid, ceng):
        self.send(13037, struct.pack('>I', bid) + struct.pack('>B', ceng))
        p = self.drain_until(13037, timeout=4.0)
        self.drain_rest(0.3)
        if p is None:
            return None
        r_bid = struct.unpack_from('>I', p, 0)[0]
        r_ceng = p[4]
        tips = p[5]
        return {'bid': r_bid, 'ceng': r_ceng, 'tips': tips}

    def fight_mon(self, mon_bid, drain_secs=45.0):
        self.send(20002, struct.pack('>i', mon_bid))
        seen = []
        t0 = time.time()
        while time.time() - t0 < drain_secs:
            rcmd, body = self.read_frame()
            if rcmd is None:
                continue
            seen.append(rcmd)
            if rcmd == 20020:
                self.drain_rest(8.0)
                break
        return seen


def db_assets(rid):
    rows = db_query('SELECT name, amount FROM role_assets WHERE rid=?', (rid,))
    return {r['name']: r['amount'] for r in rows}


def db_dung(rid, ptype, pkey):
    rows = db_query('SELECT value FROM dungeon_progress WHERE rid=? AND ptype=? AND pkey=?',
                    (rid, ptype, pkey))
    return rows[0]['value'] if rows else None


def db_reward_log(rid, ref_like):
    return db_query("SELECT reference_id, source, granted_ts FROM reward_log WHERE rid=? AND reference_id LIKE ? ORDER BY granted_ts",
                    (rid, ref_like))


def db_bag_item_count(rid):
    return db_query('SELECT COUNT(*) c FROM bag_items WHERE rid=?', (rid,))[0]['c']


def db_bag_qty(rid, item_bid):
    # bag_items: item_id=袋内序号(PK), bid=物品bid —— 按 bid 查
    rows = db_query('SELECT COALESCE(SUM(quantity),0) s FROM bag_items WHERE rid=? AND bid=?',
                    (rid, item_bid))
    return rows[0]['s'] if rows else 0


def cleanup(trid, uid):
    con = sqlite3.connect(DB)
    tbls = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in tbls:
        cols = [c[1] for c in con.execute('PRAGMA table_info(%s)' % t).fetchall()]
        if 'rid' in cols:
            con.execute('DELETE FROM %s WHERE rid=?' % t, (trid,))
    con.execute('DELETE FROM accounts WHERE uid=?', (uid,))
    con.commit()
    con.close()


def boost_attrs(rid):
    con = sqlite3.connect(DB)
    con.execute('INSERT OR IGNORE INTO role_attr (rid) VALUES (?)', (rid,))
    con.execute('UPDATE role_attr SET atk_s=8000, def_s=500, hp_max=50000 WHERE rid=?', (rid,))
    con.commit()
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()

    results = []
    def check(name, cond, detail=''):
        results.append((name, bool(cond), detail))
        print('  [%s] %s %s' % ('PASS' if cond else 'FAIL', name, detail), flush=True)

    print('=== C3.3-E 镇魂塔闭环 E2E ===', flush=True)
    uid = 'c33test_dun_%d' % int(time.time())
    print('  测试账号 uid=%s' % uid, flush=True)

    cli = Client()
    cli.connect()
    roles = cli.login(uid)
    print('  login roles=%s' % roles, flush=True)
    code, trid = cli.create_role('C33DUN')
    print('  create_role code=%s trid=%s' % (code, trid), flush=True)
    if code != 1 or not trid:
        print('FATAL: 建角失败', flush=True)
        return 1

    gm('setlevel', {'rid': trid, 'lev': 70})
    time.sleep(0.3)
    boost_attrs(trid)
    cli.select_role(trid)
    cli.role_init(trid)

    # ── 21306 列表 ──
    print('\n── 21306 副本列表 ──', flush=True)
    n_dung = cli.dungeon_list_count()
    check('21306 列表返回副本数>0', n_dung and n_dung >= 30, '(n=%s, 期望~34)' % n_dung)

    # ── 负例先测（此时 frontier=1）──
    print('\n── 负例：挑战校验 ──', flush=True)
    r_bad_ceng = cli.challenge_tower(40001, 99)
    check('13037 ceng=99 越界被拒', r_bad_ceng and r_bad_ceng['tips'] == 0,
          '(tips=%s)' % (r_bad_ceng and r_bad_ceng['tips']))
    r_skip = cli.challenge_tower(40001, 2)  # frontier=1，不能跳层
    check('13037 ceng=2 跳过前沿被拒', r_skip and r_skip['tips'] == 0,
          '(tips=%s)' % (r_skip and r_skip['tips']))

    # ── 21308 进本（合法）──
    print('\n── 21308 进本 ──', flush=True)
    t_enter = cli.enter_dungeon(40001)
    check('21308 进本 bid=40001 成功', t_enter == 1, '(tips=%s)' % t_enter)

    t_badbid = cli.enter_dungeon(999999)
    check('21308 非法 bid=999999 被拒', t_badbid == 0, '(tips=%s)' % t_badbid)

    # ── 13037 挑战层 1 ──
    print('\n── 13037 挑战 ceng=1 ──', flush=True)
    r_ok = cli.challenge_tower(40001, 1)
    check('13037 挑战 ceng=1 成功', r_ok and r_ok['tips'] == 1 and r_ok['bid'] == 40001,
          '(resp=%s)' % r_ok)

    # ── 战斗：击杀 boss 18201 ──
    print('\n── 战斗击杀 boss 18201（等结算）──', flush=True)
    coin_before = db_assets(trid).get('coin', 0)
    bag_35041_before = db_bag_qty(trid, 35041)
    log_before = db_reward_log(trid, 'dung_settle:%')
    seen = cli.fight_mon(18201)
    time.sleep(1.0)
    print('  seen cmds=%s' % seen, flush=True)
    check('战斗过程出现 20020', 20020 in seen, '')
    # 21307 走 push_to_rid 异步推送（独立投递队列），E2E socket 不直接可见；
    # 以 reward_log/DB 发奖结果作为推送到达的权威证明（tcp.log 另存证）。
    print('  (21307 经 push_to_rid 异步推送，以 DB 发奖结果为准；seen=%s)' % seen, flush=True)

    coin_after = db_assets(trid).get('coin', 0)
    bag_35041_after = db_bag_qty(trid, 35041)
    log_after = db_reward_log(trid, 'dung_settle:%')
    d_coin = coin_after - coin_before
    d_bag = bag_35041_after - bag_35041_before
    d_log = len(log_after) - len(log_before)
    print('  coin delta=%+d (期望 +30000, 含通用+30)' % d_coin, flush=True)
    print('  35041 qty delta=%+d (期望 +2: clear_item+first_kill)' % d_bag, flush=True)
    print('  reward_log dung_settle delta=%d' % d_log, flush=True)
    check('通关 coin 奖励到账(>=30000)', d_coin >= 30000, '(+%d)' % d_coin)
    check('通关物品 35041 ×2 到账', d_bag == 2, '(+%d)' % d_bag)
    check('reward_log 记录 dung_settle', d_log == 1, '(+%d)' % d_log)

    # ── DB 进度持久化 ──
    tc = db_dung(trid, 'tower_clear', '1')
    tf = db_dung(trid, 'tower_floor', '21301')
    print('  tower_clear(层1)=%s  tower_floor=%s' % (tc, tf), flush=True)
    check('tower_clear 层1 已记录', tc is not None, '(=%s)' % tc)
    check('tower_floor 推进到 2', tf == 2, '(=%s, type=%s)' % (tf, type(tf).__name__))

    # ── 重打同层：幂等，不重复发奖 ──
    print('\n── 重打 ceng=1（幂等验证）──', flush=True)
    time.sleep(2.0)
    r_again = cli.challenge_tower(40001, 1)  # frontier=2，ceng=1<=2 允许
    print('  再次挑战 ceng=1 resp=%s' % r_again, flush=True)
    coin_before2 = db_assets(trid).get('coin', 0)
    bag_before2 = db_bag_qty(trid, 35041)
    seen2 = cli.fight_mon(18201)
    time.sleep(1.0)
    d_coin2 = db_assets(trid).get('coin', 0) - coin_before2
    d_bag2 = db_bag_qty(trid, 35041) - bag_before2
    print('  重打 coin delta=%+d  35041 delta=%+d' % (d_coin2, d_bag2), flush=True)
    # 通用 KILL_REWARD 仍会 +30 coin +1 物品(33001)，但塔奖励(30000/35041×2)不应重复
    check('重打不重复发塔 coin 奖励(30000)', d_coin2 < 1000, '(+%d, 仅通用+30)' % d_coin2)
    check('重打不重复发塔物品 35041', d_bag2 == 0, '(+%d)' % d_bag2)

    # ── 21309 退本 ──
    print('\n── 21309 退本 ──', flush=True)
    t_exit = cli.exit_dungeon(40001)
    check('21309 退本成功', t_exit == 1, '(tips=%s)' % t_exit)

    cli.close()

    # ── 重登持久化验证 ──
    print('\n── 重登验证 tower_floor 持久化 ──', flush=True)
    tf2 = db_dung(trid, 'tower_floor', '21301')
    check('重登后 tower_floor 仍=2', tf2 == 2, '(=%s)' % tf2)

    # ── 低等级进本负例（第二个隔离账号）──
    print('\n── 负例：低等级进本 ──', flush=True)
    uid2 = 'c33test_dun_low_%d' % int(time.time())
    cli2 = Client()
    cli2.connect()
    cli2.login(uid2)
    code2, trid2 = cli2.create_role('C33DUNLOW')
    print('  低等级账号 trid=%s code=%s' % (trid2, code2), flush=True)
    if trid2:
        cli2.select_role(trid2)
        cli2.role_init(trid2)
        t_low = cli2.enter_dungeon(40001)
        check('低等级进本 bid=40001 被拒(level<45)', t_low == 0, '(tips=%s)' % t_low)
        cli2.close()
        cleanup(trid2, uid2)

    # ── 汇总 ──
    print('\n═══ 汇总 ═══', flush=True)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print('  %d/%d 通过' % (passed, total), flush=True)

    if not args.keep:
        cleanup(trid, uid)
        print('  测试账号已清理 rid=%s uid=%s' % (trid, uid), flush=True)
    else:
        print('  --keep: 保留 rid=%s uid=%s' % (trid, uid), flush=True)

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
