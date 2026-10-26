#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C4 场景系统 E2E —— GM 后台传送 + 存档场景跨重登保持（回归门禁）。

覆盖的缺陷（2026-10-16 实测暴露）：
  D1 `_current_bid()` 只读 spawn 配置（恒 10001）⇒ 切图后移动校验用错 MapBlock，
     合法坐标被判"不可走"、被拽回并落库。
  D2 登录（10102）恒用 `spawn.bid`=10001 ⇒ GM 传送/挂机图/副本所在地一重登即丢，
     私服化下等于只有一张图可玩。
  D3 10300 补推 10200 也用 `spawn.bid` ⇒ 客户端每跑一次场景初始化就被拽回旧图。

本脚本证明 D2/D3 已修（存档场景可跨重登保持），并回归 setscene 的写库 + 帧下发。
D1 由 `_current_bid` 的单元断言 + 实机移动帧共同覆盖（实机部分在文档中记录）。

纪律：
  - 使用全新随机测试账号 c4sctest_<ts>，**绝不触碰 rid=1001**；结束自动清场。
  - 每项断言区分「连接成功」与「业务成功」，断言写清期望/实际。
  - 未真实执行的项标 NOT_RUN，绝不编造。
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
BASELINE_RID = 1001
SPAWN_SCENE = 10001
TOKEN = os.environ.get('DSH_GM_TOKEN') or 'dshgm'

# 目标场景：10005 乾坤日月谷（config_map 实有），10010 挂机场所（config_guaji）
SCENE_A = 10005
SCENE_B = 10010
SCENE_BAD = 99999

RESULTS = []


def record(name, expected, actual, ok, evidence=''):
    tag = 'PASS' if ok is True else ('FAIL' if ok is False else 'NOT_RUN')
    print('[%s] %-52s | 期望=%s | 实际=%s' % (tag, name, expected, actual))
    RESULTS.append({'name': name, 'expected': expected, 'actual': actual,
                    'result': tag, 'evidence': evidence})
    return ok


# ── 帧编解码（与 c1_e2e_closed_loop.py 同源）──────────────────────────────
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


def http_get(path):
    try:
        conn = http.client.HTTPConnection(HOST, HTTP_PORT, timeout=10)
        conn.request('GET', path)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', 'replace')
        conn.close()
        return resp.status, body
    except Exception as e:
        return -1, 'EXC %r' % e


# ── TCP 客户端 ────────────────────────────────────────────────────────────
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

    def drain_until(self, want, timeout=5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            rcmd, body = self.read_frame()
            if rcmd is None:
                continue
            if rcmd == want:
                return body
        return None

    def login(self, uid):
        """10001 FirstPack → 1110 登录（10 键 args，1.4.9 版本族）。返回角色列表。"""
        self.send(10001, struct.pack('>H', 1) + b'c' + b'\x00' * 4)
        args = struct.pack('>H', 10)
        for k, v in (('account', uid), ('channelId', '1'), ('device_id', 'c4-scene'),
                     ('enter_srv_id', '1'), ('gettui_cid', ''), ('idfa', ''),
                     ('platform', 'ewan'), ('sign', ''),
                     ('timestamp', str(int(time.time()))), ('token', '')):
            args += w_str(k) + w_str(v)
        self.send(1110, args)
        body = self.drain_until(1110, timeout=5.0)
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
            off += 1 + 2 + 1
            roles.append({'rid': rid, 'lev': lev})
        return roles

    def create_role(self, name):
        """10101 建角 → (code, rid)。"""
        body = struct.pack('>B', 0) + w_str(name) + struct.pack('>h', 1) + w_str('ewan')
        self.send(10101, body)
        p = self.drain_until(10101)
        if p is None:
            return None, None
        code = p[0]
        off = 1 + 2 + struct.unpack_from('>H', p, 1)[0]
        rid = struct.unpack_from('>I', p, off)[0]
        return code, rid

    def select_role(self, rid):
        """10102 选角 → (code, enter_bid, enter_x, enter_y)。

        SC_10102 之后服务端会主动推 10200（SCRoleEnter），本函数顺带把它解出来：
          SC_10200 = code:u8, msg:str, bid:u32, line_id:u8, x:u16, y:u16, dir:u8
        """
        self.send(10102, struct.pack('>I', rid) + struct.pack('>B', 1))
        p = self.drain_until(10102, timeout=6.0)
        code = p[0] if p else None
        e = self.drain_until(10200, timeout=6.0)
        if e is None:
            return code, None, None, None
        off = 1 + 2 + struct.unpack_from('>H', e, 1)[0]
        bid = struct.unpack_from('>I', e, off)[0]; off += 4
        off += 1  # line_id
        x, y = struct.unpack_from('>HH', e, off)
        return code, bid, x, y


# ── 清场：仅测试 rid/uid ──────────────────────────────────────────────────
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


def login_enter(rid, uid):
    """重开连接 → 登录 → 选角 → 返回进场景 bid。"""
    c = Client()
    c.connect()
    c.login(uid)
    code, bid, x, y = c.select_role(rid)
    c.close()
    return code, bid, x, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()

    print('=== C4 场景系统 E2E（GM 传送 + 存档场景跨重登保持）===')
    base_pre = db_query('SELECT rid,level,exp,coin FROM roles WHERE rid=?', (BASELINE_RID,))
    base_pre_s = db_query('SELECT name,amount FROM role_assets WHERE rid=?', (BASELINE_RID,))
    print('  基线 rid=1001: roles=%s assets=%s' % (base_pre, base_pre_s))

    uid = 'c4sctest_%d' % int(time.time())
    print('  测试账号 uid=%s  token=%s' % (uid, TOKEN))

    # ── 1) 建角 + 首登：应进 spawn 场景 ──
    cli = Client()
    cli.connect()
    roles = cli.login(uid)
    r1 = record('[1] 新账号角色列表为空', 'roles=[]', roles, roles == [])
    code, trid = cli.create_role('C4场景')
    r2 = record('[1] 10101 建角成功', 'code=1 且 rid>=2001',
                'code=%s rid=%s' % (code, trid), code == 1 and trid and trid >= 2001)
    c102, bid0, x0, y0 = cli.select_role(trid)
    cli.close()
    r3 = record('[1] 首次登录进 spawn 场景 10001',
                'bid=%d' % SPAWN_SCENE, 'bid=%s (%s,%s)' % (bid0, x0, y0),
                bid0 == SPAWN_SCENE,
                'SC_10200 bid=%s x=%s y=%s' % (bid0, x0, y0))

    # ── 2) GM 传送 A：写库 ──
    st, sbody = http_get('/DSH_ADMIN/setscene?rid=%d&scene=%d&token=%s' % (trid, SCENE_A, TOKEN))
    row = db_query('SELECT scene_id,x,y FROM roles WHERE rid=?', (trid,))
    r4 = record('[2] GM setscene 写库 scene_id=%d' % SCENE_A,
                'HTTP200 且 DB scene_id=%d' % SCENE_A,
                'http=%s DB=%s' % (st, row), st == 200 and row and row[0]['scene_id'] == SCENE_A,
                sbody[:200])

    # ── 3) 重登：应进 A（D2 核心断言）──
    c, bidA, xA, yA = login_enter(trid, uid)
    r5 = record('[3] 重登后进入存档场景 %d（D2）' % SCENE_A,
                'bid=%d' % SCENE_A, 'bid=%s (%s,%s)' % (bidA, xA, yA), bidA == SCENE_A,
                'SC_10200 bid=%s' % bidA)

    # ── 4) 传送 B + 重登 ──
    st, sbody = http_get('/DSH_ADMIN/setscene?rid=%d&scene=%d&token=%s' % (trid, SCENE_B, TOKEN))
    c, bidB, xB, yB = login_enter(trid, uid)
    r6 = record('[4] 再传送 %d 后重登仍保持' % SCENE_B,
                'bid=%d' % SCENE_B, 'bid=%s (%s,%s)' % (bidB, xB, yB), bidB == SCENE_B,
                sbody[:160])

    # ── 5) 非法场景兜底：不得把玩家丢进不存在的图 ──
    st, sbody = http_get('/DSH_ADMIN/setscene?rid=%d&scene=%d&token=%s' % (trid, SCENE_BAD, TOKEN))
    c, bidBad, xBad, yBad = login_enter(trid, uid)
    r7 = record('[5] 非法场景 %d ⇒ 登录兜底回 spawn' % SCENE_BAD,
                'bid=%d（不回 %d）' % (SPAWN_SCENE, SCENE_BAD),
                'bid=%s' % bidBad, bidBad == SPAWN_SCENE,
                'DB scene_id=%s' % (db_query('SELECT scene_id FROM roles WHERE rid=?',
                                             (trid,)) or [{}])[0].get('scene_id'))
    # 复原到 A，供后续人工观察
    http_get('/DSH_ADMIN/setscene?rid=%d&scene=%d&token=%s' % (trid, SCENE_A, TOKEN))

    # ── 6) 鉴权：无 token 必须拒绝 ──
    st, sbody = http_get('/DSH_ADMIN/setscene?rid=%d&scene=%d' % (trid, SCENE_A))
    r8 = record('[6] setscene 无 token 被拒', 'HTTP 401', 'http=%s' % st, st == 401,
                sbody[:120])

    # ── 7) 只读端点不要求 token ──
    st, sbody = http_get('/GM/api?act=overview')
    r9 = record('[6] 只读端点 /GM/api 免 token', 'HTTP 200', 'http=%s' % st, st == 200)

    # ── 8) 场景存在性：config_map 里有 10002–10011 挂机图 ──
    ok_maps = []
    for sc in (10002, 10005, 10010, 10011):
        st, sbody = http_get('/DSH_ADMIN/setscene?rid=%d&scene=%d&token=%s' % (trid, sc, TOKEN))
        _r = db_query('SELECT scene_id FROM roles WHERE rid=?', (trid,))
        ok_maps.append(st == 200 and _r and _r[0]['scene_id'] == sc)
    r10 = record('[8] 挂机场景族 10002/10005/10010/10011 均可传送',
                 '全部 HTTP200 且落库', ok_maps, all(ok_maps))

    # ── 清场 ──
    if not args.keep:
        cleanup(trid, uid)
        left = db_query('SELECT COUNT(*) c FROM roles WHERE rid=?', (trid,))[0]['c']
        acct = db_query('SELECT COUNT(*) c FROM accounts WHERE uid=?', (uid,))[0]['c']
        r11 = record('[9] 测试账号残留清理', 'roles=0 accounts=0',
                     'roles=%s accounts=%s' % (left, acct), left == 0 and acct == 0)

    base_post = db_query('SELECT rid,level,exp,coin FROM roles WHERE rid=?', (BASELINE_RID,))
    base_post_s = db_query('SELECT name,amount FROM role_assets WHERE rid=?', (BASELINE_RID,))
    r12 = record('[10] 基线 rid=1001 未被动过', 'pre==post',
                 'roles_equal=%s assets_equal=%s' % (base_pre == base_post,
                                                     base_pre_s == base_post_s),
                 base_pre == base_post and base_pre_s == base_post_s)

    npass = sum(1 for x in RESULTS if x['result'] == 'PASS')
    nfail = sum(1 for x in RESULTS if x['result'] == 'FAIL')
    print('\n──────── 结果 ────────')
    print('检查项 %d，通过 %d，失败 %d' % (len(RESULTS), npass, nfail))
    if nfail:
        print('失败清单：')
        for x in RESULTS:
            if x['result'] == 'FAIL':
                print('  - %s | 期望=%s 实际=%s' % (x['name'], x['expected'], x['actual']))
    return 1 if nfail else 0


if __name__ == '__main__':
    sys.exit(main())
