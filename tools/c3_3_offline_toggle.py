#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3.3-D 离线挂机开关闭环验证：隔离账号测 10933/10934/10932 + 15403 收紧。

用例：
  A. 新隔离号 lev=70：
     1) 10932 查询 → off_state=0（off_on 默认 0，真话）
     2) 15403 裸发（无挂机会话）→ code=0（会话拦截 a）
     3) DB 直写 mission_bid 模拟 15402 已启动挂机链
     4) 15403 合法 mon_bid → code=1 kill_count+1；立即再发 → code=0（频率拦截 b）
     5) 等 1.5s 后 15403 → code=1（间隔过窗放行）
     6) 10933 开启 → code=1；DB off_on=1/off_started_at>0
     7) 10932 查询 → off_state=1（与 DB 一致）
     8) 10934 关闭 → code=1；DB off_on=0
     9) 10932 查询 → off_state=0
  B. 第二个隔离号 lev=1（不 setlevel）：
     10) 10933 → code=0（30 级门禁，config_function id=504 open_lev=30）

用法：python tools/c3_3_offline_toggle.py [--keep]
"""
import argparse
import os
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


def db_exec(sql, args=()):
    con = sqlite3.connect(DB)
    con.execute(sql, args)
    con.commit()
    con.close()


def gm(act, params):
    import http.client
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
        for k, v in (('account', uid), ('channelId', '1'), ('device_id', 'c33d-e2e'),
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

    def query_10932(self):
        self.send(10932, b'')
        p = self.drain_until(10932, timeout=4.0)
        if p is None or len(p) < 8:
            return None
        d, ds, dst, off = struct.unpack_from('>HHHH', p, 0)
        return {'double': d, 'double_sum': ds, 'double_state': dst, 'off_state': off}

    def cmd_code_msg(self, cmd):
        self.send(cmd, b'')
        p = self.drain_until(cmd, timeout=4.0)
        if p is None:
            return None, None
        code = p[0]
        ml = struct.unpack_from('>H', p, 1)[0]
        msg = p[3:3 + ml].decode('utf-8', 'replace') if ml else ''
        return code, msg

    def send_15403(self, mon_bid):
        self.send(15403, struct.pack('>I', mon_bid))
        p = self.drain_until(15403, timeout=4.0)
        if p is None:
            return None, None
        code = p[0]
        ml = struct.unpack_from('>H', p, 1)[0]
        msg = p[3:3 + ml].decode('utf-8', 'replace') if ml else ''
        return code, msg


def guaji_row(rid):
    rows = db_query('SELECT * FROM guaji_state WHERE rid=?', (rid,))
    return rows[0] if rows else None


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


results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond)))
    print('  [%s] %s %s' % ('PASS' if cond else 'FAIL', name, detail), flush=True)


import socket  # noqa: E402


def run_account(uid, lev):
    cli = Client()
    cli.connect()
    roles = cli.login(uid)
    print('  login roles=%s' % roles, flush=True)
    code, trid = cli.create_role('C33DOFF')
    print('  create_role code=%s trid=%s' % (code, trid), flush=True)
    if code != 1 or not trid:
        print('FATAL: 建角失败', flush=True)
        cli.close()
        return None
    gm('setlevel', {'rid': trid, 'lev': lev})
    time.sleep(0.3)
    cli.select_role(trid)
    cli.role_init(trid)
    return cli, trid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()

    print('=== C3.3-D 离线挂机开关闭环验证 ===', flush=True)

    # ── 账号 A：lev=70 ──
    uid_a = 'c33test_off_%d' % int(time.time())
    print('\n── 账号 A uid=%s lev=70 ──' % uid_a, flush=True)
    out = run_account(uid_a, 70)
    cli_a, rid_a = out

    # 1) 初始 10932 → off_state=0
    q = cli_a.query_10932()
    print('  10932 初始: %s' % q, flush=True)
    check('A1 初始 off_state=0', q and q['off_state'] == 0, str(q))

    # 2) 裸发 15403 → code=0（会话拦截）
    c, m = cli_a.send_15403(10105)
    print('  15403 裸发: code=%s msg=%r' % (c, m), flush=True)
    check('A2 无会话 15403 被拒(code=0)', c == 0, 'msg=%r' % m)

    # 3) DB 直写 mission_bid 模拟 15402 启动挂机链
    # ★ 2026-10-16 修 flaky：`updated_at` **必须写成一个"过去"的时间戳**。
    #   15403 的频率门是 `now - updated_at < guaji_kill_min_sec(1.0)` ⇒ 拒。
    #   原实现写 `int(time.time())`（= 此刻），而下一行**立刻**发 15403 ⇒
    #   dt≈0 ⇒ 必然命中频率拦截、A3 期望 code=1 却拿到 code=0「操作过快」
    #   —— 只有在"写库与发包之间恰好跨过整秒"时才侥幸通过（实测 7/10，随机）。
    #   本用例要测的是"**有会话** ⇒ 放行"，与限流无关 ⇒ 把锚点拨回 5 秒前。
    db_exec('INSERT OR REPLACE INTO guaji_state (rid,loop_count,mission_bid,kill_count,updated_at) '
            'VALUES (?,0,10010,0,?)', (rid_a, int(time.time()) - 5))
    row = guaji_row(rid_a)
    print('  DB 写入 mission_bid=10010: %s' % row, flush=True)

    # 4) 合法 15403 → code=1；立即再发 → code=0（频率拦截）
    c, m = cli_a.send_15403(10105)
    row = guaji_row(rid_a)
    print('  15403 合法: code=%s msg=%r kill_count=%s' % (c, m, row and row['kill_count']), flush=True)
    check('A3 有会话 15403 放行(code=1,kill+1)', c == 1 and row and row['kill_count'] == 1,
          'kill_count=%s' % (row and row['kill_count']))
    c2, m2 = cli_a.send_15403(10105)
    row = guaji_row(rid_a)
    print('  15403 连发: code=%s msg=%r kill_count=%s' % (c2, m2, row and row['kill_count']), flush=True)
    check('A4 连发被频率拦截(code=0)', c2 == 0 and row and row['kill_count'] == 1,
          'msg=%r' % m2)

    # 5) 等 1.5s → 再发放行
    time.sleep(1.5)
    c3, m3 = cli_a.send_15403(10105)
    row = guaji_row(rid_a)
    print('  15403 隔窗: code=%s msg=%r kill_count=%s' % (c3, m3, row and row['kill_count']), flush=True)
    check('A5 隔 1.5s 后放行(code=1,kill+1)', c3 == 1 and row and row['kill_count'] == 2,
          'kill_count=%s' % (row and row['kill_count']))

    # 6) 10933 开启 → code=1
    c, m = cli_a.cmd_code_msg(10933)
    row = guaji_row(rid_a)
    print('  10933 开启: code=%s msg=%r DB=%s' % (c, m, row), flush=True)
    check('A6 10933 code=1 且 off_on=1', c == 1 and row and row['off_on'] == 1,
          'off_started_at=%s' % (row and row['off_started_at']))

    # 7) 10932 → off_state=1
    q = cli_a.query_10932()
    print('  10932 开启后: %s' % q, flush=True)
    check('A7 开启后 off_state=1', q and q['off_state'] == 1, str(q))

    # 8) 10934 关闭 → code=1
    c, m = cli_a.cmd_code_msg(10934)
    row = guaji_row(rid_a)
    print('  10934 关闭: code=%s msg=%r DB off_on=%s' % (c, m, row and row['off_on']), flush=True)
    check('A8 10934 code=1 且 off_on=0', c == 1 and row and row['off_on'] == 0, '')

    # 9) 10932 → off_state=0
    q = cli_a.query_10932()
    print('  10932 关闭后: %s' % q, flush=True)
    check('A9 关闭后 off_state=0', q and q['off_state'] == 0, str(q))

    cli_a.close()

    # ── 账号 B：lev=1 门禁 ──
    uid_b = 'c33test_offB_%d' % int(time.time())
    print('\n── 账号 B uid=%s lev=1（门禁）──' % uid_b, flush=True)
    outb = run_account(uid_b, 1)
    cli_b, rid_b = outb
    c, m = cli_b.cmd_code_msg(10933)
    print('  10933 lev=1: code=%s msg=%r' % (c, m), flush=True)
    row = guaji_row(rid_b)
    check('B1 lev=1 开离线被拒(code=0,off_on=0)',
          c == 0 and (not row or row['off_on'] in (0, None)), 'msg=%r' % m)
    cli_b.close()

    # ── 清理 ──
    if not args.keep:
        cleanup(rid_a, uid_a)
        cleanup(rid_b, uid_b)
        print('\n  测试账号已清理 rid=%s/%s' % (rid_a, rid_b), flush=True)

    print('\n═══ 汇总 ═══', flush=True)
    nfail = 0
    for name, ok in results:
        if not ok:
            nfail += 1
    print('  %d/%d PASS' % (len(results) - nfail, len(results)), flush=True)
    return 1 if nfail else 0


if __name__ == '__main__':
    sys.exit(main())
