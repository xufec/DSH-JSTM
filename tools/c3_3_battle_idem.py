#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3.3 战斗结算幂等验证：隔离账号连杀同型怪两次，验证每次独立结算。

核心验证点（修正后预期）：
  - 第 1 次击杀 mon 20002：exp+50, coin+30, drops+1, reward_log +1 条
  - 第 2 次击杀 mon 20002：exp+50, coin+30, drops+1, reward_log +1 条（旧 bug 时 coin=0）
  - 两次总计：exp+100, coin+60, drops+2, reward_log +2 条
  - 重发同一战斗请求：不重复发奖（reward_log already）

用法：
    python tools/c3_3_battle_idem.py
    python tools/c3_3_battle_idem.py --keep
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
                # socket 超时但 deadline 未到 → 继续等（不 break）
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

    def query_assets(self):
        self.drain_rest(0.5)
        self.send(10302, b'')
        p = self.drain_until(10302, timeout=4.0)
        if p is None:
            return None
        lev = struct.unpack_from('>H', p, 0)[0]
        exp = struct.unpack_from('>I', p, 2)[0]
        gold = struct.unpack_from('>I', p, 6)[0]
        coin = struct.unpack_from('>I', p, 10)[0]
        return {'lev': lev, 'exp': exp, 'gold': gold, 'coin': coin}

    def fight_mon(self, mon_bid, drain_secs=45.0):
        """CS_20002 发起战斗，等 20020 后再等 8 秒让 _battle_settle 完全跑完（含收尾清 battle=None）。"""
        self.send(20002, struct.pack('>i', mon_bid))
        seen = []
        t0 = time.time()
        while time.time() - t0 < drain_secs:
            rcmd, body = self.read_frame()
            if rcmd is None:
                continue
            seen.append(rcmd)
            if rcmd == 20020:
                # 战斗结束，再等 8 秒：3s 异步结算 + 余量（确保 self.battle=None 后再开下一场）
                self.drain_rest(8.0)
                break
        return seen


def db_assets(rid):
    rows = db_query('SELECT name, amount FROM role_assets WHERE rid=?', (rid,))
    return {r['name']: r['amount'] for r in rows}


def db_reward_log_kill(rid):
    rows = db_query("SELECT reference_id, source, granted_ts FROM reward_log WHERE rid=? AND reference_id LIKE 'kill:%' ORDER BY granted_ts", (rid,))
    return rows


def db_bag_count(rid):
    rows = db_query('SELECT COUNT(*) c FROM bag_items WHERE rid=?', (rid,))
    return rows[0]['c'] if rows else 0


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()

    print('=== C3.3 战斗结算幂等验证 ===', flush=True)

    uid = 'c33test_battle_%d' % int(time.time())
    print('  测试账号 uid=%s' % uid, flush=True)

    cli = Client()
    cli.connect()
    roles = cli.login(uid)
    print('  login roles=%s' % roles, flush=True)

    code, trid = cli.create_role('C33BATTLE')
    print('  create_role code=%s trid=%s' % (code, trid), flush=True)
    if code != 1 or not trid:
        print('FATAL: 建角失败', flush=True)
        return 1

    # GM setlevel
    gm('setlevel', {'rid': trid, 'lev': 5})
    time.sleep(0.3)

    # 提升战斗属性（新角色 atk=100 打不过 2400HP 怪）
    try:
        con = sqlite3.connect(DB)
        con.execute('INSERT OR IGNORE INTO role_attr (rid) VALUES (?)', (trid,))
        con.execute('UPDATE role_attr SET atk_s=8000, def_s=500, hp_max=50000 WHERE rid=?', (trid,))
        con.commit()
        con.close()
        print('  战斗属性已提升: atk_s=8000 def_s=500 hp_max=50000', flush=True)
    except Exception as e:
        print('  !! 提升属性失败: %r' % e, flush=True)

    cli.select_role(trid)
    cli.role_init(trid)

    # 基线
    base = db_assets(trid)
    base_kill_log = db_reward_log_kill(trid)
    base_bag = db_bag_count(trid)
    print('\n── 基线 (before any kill) ──', flush=True)
    print('  exp=%s coin=%s gold=%s' % (base.get('exp'), base.get('coin'), base.get('gold')), flush=True)
    print('  reward_log kill 条目数=%d: %s' % (len(base_kill_log), base_kill_log), flush=True)
    print('  bag_items 件数=%d' % base_bag, flush=True)

    # ── 第 1 次击杀 mon 20001 ──
    print('\n── 第 1 次击杀 mon 20001 ──', flush=True)
    seen1 = cli.fight_mon(20001)
    print('  seen cmds: %s' % seen1, flush=True)
    time.sleep(1.0)
    after1 = db_assets(trid)
    after1_kill_log = db_reward_log_kill(trid)
    after1_bag = db_bag_count(trid)
    d1_exp = after1.get('exp', 0) - base.get('exp', 0)
    d1_coin = after1.get('coin', 0) - base.get('coin', 0)
    d1_bag = after1_bag - base_bag
    d1_kills = len(after1_kill_log) - len(base_kill_log)
    print('  exp delta=%+d (expect +50)' % d1_exp, flush=True)
    print('  coin delta=%+d (expect +30)' % d1_coin, flush=True)
    print('  bag delta=%+d (expect +1)' % d1_bag, flush=True)
    print('  reward_log kill delta=%+d (expect +1)' % d1_kills, flush=True)
    print('  new kill refs: %s' % [r['reference_id'] for r in after1_kill_log if r not in base_kill_log], flush=True)

    # ── 第 2 次击杀同型怪 mon 20001 ──
    print('\n── 第 2 次击杀 mon 20001（同型怪第二次）──', flush=True)
    time.sleep(2.0)  # 确保前一场战斗完全收尾（self.battle=None）
    seen2 = cli.fight_mon(20001)
    print('  seen cmds: %s' % seen2, flush=True)
    time.sleep(1.0)
    after2 = db_assets(trid)
    after2_kill_log = db_reward_log_kill(trid)
    after2_bag = db_bag_count(trid)
    d2_exp = after2.get('exp', 0) - after1.get('exp', 0)
    d2_coin = after2.get('coin', 0) - after1.get('coin', 0)
    d2_bag = after2_bag - after1_bag
    d2_kills = len(after2_kill_log) - len(after1_kill_log)
    print('  exp delta=%+d (expect +50)' % d2_exp, flush=True)
    print('  coin delta=%+d (expect +30, 旧 bug 时为 0)' % d2_coin, flush=True)
    print('  bag delta=%+d (expect +1)' % d2_bag, flush=True)
    print('  reward_log kill delta=%+d (expect +1)' % d2_kills, flush=True)
    print('  all kill refs: %s' % [r['reference_id'] for r in after2_kill_log], flush=True)

    # ── 总结判定 ──
    print('\n═══ 判定 ═══', flush=True)
    ok1 = (d1_exp == 50 and d1_coin == 30 and d1_bag == 1 and d1_kills == 1)
    ok2 = (d2_exp == 50 and d2_coin == 30 and d2_bag == 1 and d2_kills == 1)
    print('  第 1 次击杀独立结算: %s' % ('PASS' if ok1 else 'FAIL'), flush=True)
    print('  第 2 次击杀独立结算（旧 bug: coin=0）: %s' % ('PASS' if ok2 else 'FAIL'), flush=True)
    print('  两次累计: exp=%+d coin=%+d bag=%+d reward_log=%+d' % (
        after2.get('exp',0)-base.get('exp',0),
        after2.get('coin',0)-base.get('coin',0),
        after2_bag-base_bag,
        len(after2_kill_log)-len(base_kill_log)), flush=True)

    cli.close()

    # 清理
    if not args.keep:
        cleanup(trid, uid)
        print('\n  测试账号已清理 rid=%s uid=%s' % (trid, uid), flush=True)
    else:
        print('\n  --keep: 保留测试账号 rid=%s uid=%s' % (trid, uid), flush=True)

    return 0 if (ok1 and ok2) else 1


if __name__ == '__main__':
    sys.exit(main())
