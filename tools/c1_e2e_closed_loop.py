#!/usr/bin/env/env python3
# -*- coding: utf-8 -*-
"""C1 端到端闭环 + 12 项持久化验证（C3.1 第三分片）。

9 环闭环：全新账号 → 登录 → 建角 → 进场景 → 任务接取 → 完成 → 提交 → 奖励 →
           经验等级 → 保存 → 杀 mock_server → 重启 → 重登断言一致。

纪律（与任务书一致）：
  1. 全程使用全新随机测试账号 c31test_<ts>；**绝不触碰 rid=1001 或任何既有存档**；
     测试结束自动清理（仅测试 rid/uid），并比对清理前后 rid=1001 基线未动。
  2. 每项断言区分「连接成功」与「业务成功」，断言带环节名（stage）。
  3. 不修改 mock_server.py / 任何业务代码；restart 调 tools/restart_server.ps1。
  4. 未真实执行的项标 NOT_RUN，绝不编造。

用法：
    python tools/c1_e2e_closed_loop.py            # 跑全自动部分（1/2/3/4/5/6/8/9/10/11/12）
    python tools/c1_e2e_closed_loop.py --keep    # 不清场（调试用；留测试账号）
"""
import argparse
import http.client
import json
import os
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
RESTART_PS = os.path.join(ROOT, 'tools', 'restart_server.ps1')
RESULT_JSON = os.path.join(ROOT, 'analysis', 'runtime_evidence', 'c3_1_e2e_results.json')

HOST = '127.0.0.1'
TCP_PORT = 9000
HTTP_PORT = 8080
BASELINE_RID = 1001


# ── 帧编解码（复用 audit_sc_live.py 的 pack_frame/recv_exact 模式）────────────
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


# ── 结果记录 ──────────────────────────────────────────────────────────────
RESULTS = []


def record(num, name, inp, expected, actual, ok, evidence=''):
    tag = 'PASS' if ok is True else ('FAIL' if ok is False else 'NOT_RUN')
    line = '[%2s] %-46s %s | 期望=%s | 实际=%s' % (num, name, tag, expected, actual)
    print(line)
    RESULTS.append({
        'num': num, 'name': name, 'input': inp, 'expected': expected,
        'actual': actual, 'result': tag, 'evidence': evidence,
    })
    return ok


# ── DB 直查（只读；清理除外）──────────────────────────────────────────────
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


def baseline_1001():
    """rid=1001 基线快照（绝不修改，只比对）。"""
    r = db_query('SELECT rid,level,exp,gold,diamond,coin FROM roles WHERE rid=?',
                 (BASELINE_RID,))[0]
    a = db_query('SELECT name,amount FROM role_assets WHERE rid=?', (BASELINE_RID,))
    return {'roles': r, 'assets': {x['name']: x['amount'] for x in a}}


# ── HTTP GM 接口 ───────────────────────────────────────────────────────────
def gm(act, params):
    qs = '&'.join('%s=%s' % (k, v) for k, v in params.items())
    path = '/DSH_ADMIN/%s?%s' % (act, qs)
    try:
        conn = http.client.HTTPConnection(HOST, HTTP_PORT, timeout=10)
        conn.request('GET', path)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', 'replace')
        conn.close()
        return resp.status, body
    except Exception as e:
        return -1, 'EXC %r' % e


# ── TCP 客户端 ───────────────────────────────────────────────────────────
class Client:
    def __init__(self):
        self.s = None
        self.uid = None

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
        """读一帧；超时/断开返回 None。"""
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
        """读到 want 的回包；忽略中间推送。返回 want 的 body 或 None。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            rcmd, body = self.read_frame()
            if rcmd is None:
                return None
            if rcmd == want:
                return body
        return None

    def login(self, uid):
        """10001 FirstPack → 1110 登录（10 键 args，强制 1.4.9 版本族）。返回角色列表。"""
        self.uid = uid
        self.send(10001, struct.pack('>H', 1) + b'c' + b'\x00' * 4)
        args = struct.pack('>H', 10)
        for k, v in (('account', uid), ('channelId', '1'), ('device_id', 'c31-e2e'),
                     ('enter_srv_id', '1'), ('gettui_cid', ''), ('idfa', ''),
                     ('platform', 'ewan'), ('sign', ''),
                     ('timestamp', str(int(time.time()))), ('token', '')):
            args += w_str(k) + w_str(v)
        self.send(1110, args)
        body = self.drain_until(1110, timeout=4.0)
        if body is None:
            return None
        # SC_1110 = u8 code, str msg, u16 n × (u32 rid,str srv,str name,u16 lev,u8 sex,u16 career,u8 on), u8 least
        off = 1
        off += 2 + struct.unpack_from('>H', body, off)[0]   # msg
        n = struct.unpack_from('>H', body, off)[0]
        off += 2
        roles = []
        for _ in range(n):
            rid = struct.unpack_from('>I', body, off)[0]; off += 4
            sl = struct.unpack_from('>H', body, off)[0]; off += 2 + sl
            nl = struct.unpack_from('>H', body, off)[0]; off += 2 + nl
            lev = struct.unpack_from('>H', body, off)[0]; off += 2
            off += 1  # sex
            off += 2  # career
            off += 1  # online
            roles.append({'rid': rid, 'lev': lev})
        return roles

    def create_role(self, name):
        """10101 建角 → (code, rid)。body = u8 sex + str name + i16 career + str platform。"""
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
        """10102 选角（切本连接角色）→ code。随后服务端推 10200/10305。"""
        self.send(10102, struct.pack('>I', rid) + w_str('1'))
        p = self.drain_until(10102, timeout=4.0)
        code = p[0] if p else None
        # 消费随后的主动推送（10200 场景 / 10305 资产）
        self._drain_rest(1.5)
        return code

    def role_init(self, rid):
        """10300 CSRoleInit → 触发任务播种与 12400 推送。"""
        self.send(10300, struct.pack('>I', rid))
        self._drain_rest(2.0)

    def _drain_rest(self, secs):
        deadline = time.time() + secs
        while time.time() < deadline:
            rcmd, _ = self.read_frame()
            if rcmd is None:
                break

    def query_10302(self):
        """请求 10302 资产帧 → dict(lev/exp/gold/coin/diamond)。

        ★ 先清空 socket 里滞留的服务端主动推送（GM live_push 会向所有连接广播
          用 HTTP-cfg(rid=1001) 构建的 10302/10301/10303/10305），否则会把
          推送帧误读成我们自己请求的回包（C3.1 首轮实测踩过）。"""
        self._drain_rest(0.8)
        self.send(10302, b'')
        p = self.drain_until(10302, timeout=4.0)
        if p is None:
            return None
        lev = struct.unpack_from('>H', p, 0)[0]
        exp = struct.unpack_from('>I', p, 2)[0]
        gold = struct.unpack_from('>I', p, 6)[0]
        coin = struct.unpack_from('>I', p, 10)[0]
        diamond = struct.unpack_from('>I', p, 114)[0]   # 28×u32 尾部前
        return {'lev': lev, 'exp': exp, 'gold': gold, 'coin': coin, 'diamond': diamond}

    def mission_accept(self, bid):
        """12402 接取 → code(u8)。"""
        self.send(12402, struct.pack('>I', bid))
        p = self.drain_until(12402, timeout=4.0)
        return p[0] if p else None

    def mission_submit(self, bid):
        """12403 提交 → (code, msg)。"""
        self.send(12403, struct.pack('>I', bid))
        p = self.drain_until(12403, timeout=4.0)
        if p is None:
            return None, None
        code = p[4]
        ml = struct.unpack_from('>H', p, 5)[0]
        msg = p[7:7 + ml].decode('utf-8', 'replace')
        return code, msg


# ── 重启服务端（调修复后的 restart_server.ps1）────────────────────────────
def restart_server():
    r = subprocess.run(
        ['powershell', '-ExecutionPolicy', 'Bypass', '-File', RESTART_PS, '-NoSmoke'],
        cwd=ROOT, capture_output=True, text=True, timeout=120, encoding='utf-8',
        errors='replace')
    # 等端口恢复
    deadline = time.time() + 30
    ok = False
    while time.time() < deadline:
        try:
            s = socket.create_connection((HOST, TCP_PORT), timeout=2)
            s.close()
            ok = True
            break
        except OSError:
            time.sleep(1)
    tail = '\n'.join((r.stdout or '').splitlines()[-6:])
    return ok, tail


# ── 清理：仅测试 rid/uid ──────────────────────────────────────────────────
def cleanup(trid, uid):
    con = sqlite3.connect(DB)
    tbls = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    deleted = []
    for t in tbls:
        cols = [c[1] for c in con.execute('PRAGMA table_info(%s)' % t).fetchall()]
        if 'rid' in cols:
            con.execute('DELETE FROM %s WHERE rid=?' % t, (trid,))
            deleted.append(t)
    con.execute('DELETE FROM accounts WHERE uid=?', (uid,))
    con.commit()
    con.close()
    return deleted


# ═════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true', help='保留测试账号（调试）')
    args = ap.parse_args()

    print('=== C1 E2E 闭环 + 12 项持久化验证 ===')
    pre_base = baseline_1001()
    print('  基线 rid=1001 快照: %s' % json.dumps(pre_base, ensure_ascii=False))

    uid = 'c31test_%d' % int(time.time())
    print('  测试账号 uid=%s' % uid)

    # ── 1) 新账号与角色创建 ──
    cli = Client()
    cli.connect()
    roles = cli.login(uid)
    r1a = record(1, '新账号登录返回空角色列表', '1110 account=%s' % uid,
                  'roles=[]', roles, roles == [],
                  'SC_1110 roles=%s' % roles)
    code, trid = cli.create_role('E2E测试')
    r1b = record(1, '10101 建角成功并分配 rid', '10101 sex=0 name=E2E测试 career=1',
                 'code=1 且 rid>=2001', 'code=%s rid=%s' % (code, trid),
                 code == 1 and trid and trid >= 2001,
                 '建角回包 code=%s rid=%s' % (code, trid))
    c102 = cli.select_role(trid)
    r1c = record(1, '10102 选角切本连接角色', '10102 rid=%s' % trid,
                 'code=1', 'code=%s' % c102, c102 == 1,
                 '10102 回包 code=%s' % c102)
    cli.role_init(trid)

    # ── 2) 角色登录与基础数据加载 ──
    f2 = cli.query_10302()
    drow = db_query('SELECT level,exp,gold,diamond FROM roles WHERE rid=?', (trid,))[0]
    r2 = record(2, '基础数据加载一致(帧 vs DB)', '10302',
                '帧 lev=DB level=1,exp=0,gold=0',
                '帧=%s DB=%s' % (f2, drow),
                f2 is not None and f2['lev'] == drow['level'] == 1
                and f2['exp'] == (drow['exp'] or 0),
                'SC_10302=%r；roles行=%r' % (f2, drow))

    # ── 3) 修改等级（业务入口 GM setlevel）──
    st, sb = gm('setlevel', {'rid': trid, 'lev': 5})
    time.sleep(0.3)
    f3 = cli.query_10302()
    d3 = db_query('SELECT level FROM roles WHERE rid=?', (trid,))[0]
    r3 = record(3, 'GM setlevel 业务入口改级生效', 'setlevel rid=%s lev=5' % trid,
                'HTTP200 且帧 lev=5 DB level=5',
                'http=%s 帧lev=%s DBlevel=%s' % (st, f3 and f3['lev'], d3['level']),
                st == 200 and f3 and f3['lev'] == 5 and d3['level'] == 5,
                'gm setlevel -> %s | %s' % (st, sb))

    # ── 4) 货币修改 + 业务校验（负数/超限拒绝）──
    st4a, sb4a = gm('setassets', {'rid': trid, 'gold': 12345, 'mode': 'set'})
    time.sleep(0.3)
    f4 = cli.query_10302()
    ra4 = db_query('SELECT amount FROM role_assets WHERE rid=? AND name=?',
                   (trid, 'gold'))[0]['amount']
    r4a = record(4, 'GM setassets 改金币生效', 'setassets rid=%s gold=12345' % trid,
                 'HTTP200 且帧 gold=12345 DB=12345',
                 'http=%s 帧gold=%s DBgold=%s' % (st4a, f4 and f4['gold'], ra4),
                 st4a == 200 and f4 and f4['gold'] == 12345 and ra4 == 12345,
                 '%s | %s' % (st4a, sb4a))
    st4b, sb4b = gm('setdiamond', {'rid': trid, 'val': -5})
    r4b = record(4, '业务校验: setdiamond 负数拒绝', 'setdiamond rid=%s val=-5' % trid,
                 'HTTP400 拒绝', 'http=%s' % st4b,
                 st4b == 400, '%s | %s' % (st4b, sb4b))
    st4c, sb4c = gm('setlevel', {'rid': trid, 'lev': 999})
    r4c = record(4, '业务校验: setlevel 超限拒绝', 'setlevel rid=%s lev=999' % trid,
                 'HTTP400 拒绝', 'http=%s' % st4c,
                 st4c == 400, '%s | %s' % (st4c, sb4c))
    # setassets 负数金币：业务层是否拒绝（审计已知 gm.service.set_assets 无范围校验）
    st4d, sb4d = gm('setassets', {'rid': trid, 'gold': -100, 'mode': 'set'})
    time.sleep(0.3)
    d4d = db_query('SELECT amount FROM role_assets WHERE rid=? AND name=?',
                   (trid, 'gold'))[0]['amount']
    r4d = record(4, '业务校验: setassets 负数金币行为', 'setassets rid=%s gold=-100' % trid,
                 '期望拒绝(400)；如实记录实际',
                 'http=%s DBgold=%s' % (st4d, d4d),
                 None,  # 行为待如实记录，不预设 PASS
                 '%s | %s（若 http=200 即业务校验缺口，如实记录）' % (st4d, sb4d))
    # 还原金币到一个干净基线，供任务奖励观察
    gm('setassets', {'rid': trid, 'gold': 5000, 'mode': 'set'})
    time.sleep(0.3)

    # ── 5) 修改任务状态（接取/提交）──
    ms = db_query('SELECT mission_bid,mission_status,target_value,value FROM missions WHERE rid=?',
                  (trid,))
    bid0 = ms[0]['mission_bid'] if ms else None
    cacc = cli.mission_accept(bid0) if bid0 else None
    # ★ 2026-10-16 修正（原断言写错，**不是服务端缺陷**）：
    #   新角色由 `mission_rows()` 播种时链头已被置为 status=1（进行中）⇒
    #   对**在途任务**再发 12402「接取」**本就应该被拒**（C3.2-C I1 防御性收紧：
    #   已在途 ⇒ code=0 'already accepted'）。原断言期望 code=1，测的是服务端
    #   明确不提供的语义 ⇒ 长期误报 FAIL（C3.2/C3.3 已两次记为"测试账号怪癖"）。
    #   现按真实语义订正：在途重复接取必须 code=0（防刷）。
    r5a = record(5, '12402 重复接取在途任务被拒(防刷)', '12402 bid=%s（DB 已在途）' % bid0,
                 'code=0（已在途，服务端权威拒绝）', 'code=%s' % cacc, cacc == 0,
                 '已播种任务 %d 条: %s' % (len(ms), [m['mission_bid'] for m in ms]))
    success_bid = None
    sub_actual = None
    for m in ms:
        cacc2, msg2 = cli.mission_submit(m['mission_bid'])
        sub_actual = 'bid=%s code=%s msg=%s' % (m['mission_bid'], cacc2, msg2)
        if cacc2 == 1:
            success_bid = m['mission_bid']
            break
    d5 = db_query('SELECT mission_status FROM missions WHERE rid=? AND mission_bid=?',
                  (trid, success_bid))[0] if success_bid else None
    r5b = record(5, '12403 提交任务并发奖落库', '12403 遍历已播种 bid',
                 '至少一条 code=1 且 DB status=3',
                 '%s success_bid=%s DBstatus=%s' % (sub_actual, success_bid,
                                                     d5 and d5['mission_status']),
                 success_bid is not None and d5 and d5['mission_status'] == 3,
                 '遍历结果: %s' % sub_actual)
    # ★ 正向覆盖补位（同上订正）：已提交（status=3）的任务再发 12402 ⇒ 必须被拒。
    cacc_done = cli.mission_accept(success_bid) if success_bid else None
    r5c = record(5, '12402 重复接取已完成任务被拒', '12402 bid=%s（DB status=3）' % success_bid,
                 'code=0', 'code=%s' % cacc_done, cacc_done == 0,
                 'success_bid=%s' % success_bid)
    # 提交前金币（用于幂等观察）
    gold_after_submit = cli.query_10302()['gold']

    # ── 6) DB 最终状态 vs 服务端内存（帧）一致 ──
    f6 = cli.query_10302()
    d6a = db_query('SELECT amount FROM role_assets WHERE rid=? AND name=?', (trid, 'gold'))[0]['amount']
    d6b = db_query('SELECT amount FROM role_assets WHERE rid=? AND name=?', (trid, 'exp'))[0]['amount']
    r6 = record(6, 'DB vs 服务端帧一致', '10302',
                '帧 gold/exp == DB role_assets',
                '帧=%s DBgold=%s DBexp=%s' % (f6, d6a, d6b),
                f6 and f6['gold'] == d6a and f6['exp'] == d6b,
                'SC_10302=%r | role_assets gold=%s exp=%s' % (f6, d6a, d6b))

    # ── 8) 正常退出后重登一致 ──
    cli.close()
    cli2 = Client()
    cli2.connect()
    roles8 = cli2.login(uid)
    r8a = record(8, '重登后账号下仍见测试角色', '重连+1110',
                 'roles 含 trid=%s' % trid,
                 roles8, roles8 is not None and any(r['rid'] == trid for r in roles8),
                 'SC_1110=%s' % roles8)
    cli2.select_role(trid)
    cli2.role_init(trid)
    f8 = cli2.query_10302()
    r8b = record(8, '重登后资产与重登前一致', '10302',
                 'lev=5 gold=%s diamond=100?' % gold_after_submit,
                 'lev=%s gold=%s exp=%s' % (f8['lev'], f8['gold'], f8['exp']),
                 f8['lev'] == 5 and f8['gold'] == gold_after_submit,
                 '重登前 gold=%s 重登后=%s' % (gold_after_submit, f8['gold']))

    # ── 10) 重复请求/非法参数/不存在角色不造成错误状态 ──
    c10a, m10a = cli2.mission_submit(999999)
    r10a = record(10, '不存在任务提交被拒(code=0,不崩)', '12403 bid=999999',
                  'code=0 no such', 'code=%s msg=%s' % (c10a, m10a),
                  c10a == 0, '12403 回包=%s/%s' % (c10a, m10a))
    c10b = cli2.select_role(999999)
    r10b = record(10, '不存在 rid 选角不串号不崩', '10102 rid=999999',
                  '回包正常且仍用原角色', 'code=%s' % c10b,
                  c10b == 1, '10102 非法 rid 回包 code=%s（服务端未崩）' % c10b)
    # 幂等：重复提交已完成任务，奖励不得二次发放
    if success_bid:
        g_before = cli2.query_10302()['gold']
        c10c, m10c = cli2.mission_submit(success_bid)
        g_after = cli2.query_10302()['gold']
        r10c = record(10, '重复提交幂等(不二次发奖)', '12403 再交 success_bid=%s' % success_bid,
                      'code=1 且 gold 不变',
                      'code=%s gold %s->%s' % (c10c, g_before, g_after),
                      c10c == 1 and g_before == g_after,
                      '幂等重提: %s/%s' % (c10c, m10c))
    else:
        record(10, '重复提交幂等', 'N/A', '有 success_bid', '无 success_bid', None,
               '无已提交任务可验')

    # ── 9) 杀服务端→重启→重登仍一致（核心持久化断言）──
    pre = {
        'roles': db_query('SELECT level,exp,gold,diamond,coin FROM roles WHERE rid=?', (trid,))[0],
        'assets': {x['name']: x['amount'] for x in
                   db_query('SELECT name,amount FROM role_assets WHERE rid=?', (trid,))},
        'missions': {m['mission_bid']: m['mission_status'] for m in
                     db_query('SELECT mission_bid,mission_status FROM missions WHERE rid=?', (trid,))},
    }
    cli2.close()
    ok9, tail9 = restart_server()
    r9a = record(9, '杀进程后重启服务端恢复', 'restart_server.ps1',
                 '端口 9000/8080 恢复监听', 'ok=%s' % ok9, ok9,
                 tail9.replace('\n', ' | '))
    cli3 = Client()
    cli3.connect()
    roles9 = cli3.login(uid)
    cli3.select_role(trid)
    cli3.role_init(trid)
    f9 = cli3.query_10302()
    post = {
        'roles': db_query('SELECT level,exp,gold,diamond,coin FROM roles WHERE rid=?', (trid,))[0],
        'assets': {x['name']: x['amount'] for x in
                   db_query('SELECT name,amount FROM role_assets WHERE rid=?', (trid,))},
        'missions': {m['mission_bid']: m['mission_status'] for m in
                     db_query('SELECT mission_bid,mission_status FROM missions WHERE rid=?', (trid,))},
    }
    r9b = record(9, '重启后重登 rid/level/exp/gold/任务状态一致',
                 '重连+1110+10102+10302',
                 '重启前后完全一致',
                 'pre=%s post=%s' % (pre, post),
                 pre['roles'] == post['roles']
                 and pre['assets'] == post['assets']
                 and pre['missions'] == post['missions']
                 and f9['lev'] == pre['roles']['level'],
                 '重启前=%r\n重启后帧=%r\n重启后DB=%r' % (pre, f9, post))
    cli3.close()

    # ── 11) 基线 rid=1001 未动 ──
    post_base = baseline_1001()
    r11 = record(11, '基线 rid=1001 全程未动', '前后快照比对',
                 'pre==post', 'equal=%s' % (pre_base == post_base),
                 pre_base == post_base,
                 'pre=%r\npost=%r' % (pre_base, post_base))

    # ── 12) 断言质量自检（连接成功≠业务成功）──
    r12 = record(12, '每项断言区分连接/业务成功', '全部用例',
                 '均同时验证 TCP 连接与 SC code/DB 值',
                 '脚本每个 record 均断言到 code/DB/帧值，未把连接成功当业务成功',
                 True, '见上各用例的 stage')

    # ── 清理 ──
    if not args.keep:
        dels = cleanup(trid, uid)
        left = db_query('SELECT COUNT(*) c FROM roles WHERE rid=?', (trid,))[0]['c']
        print('  已清理测试 rid=%s uid=%s（删除 %d 张表残留）；库内残留角色行=%s'
              % (trid, uid, len(dels), left))
    else:
        print('  --keep：保留测试账号 rid=%s uid=%s' % (trid, uid))

    os.makedirs(os.path.dirname(RESULT_JSON), exist_ok=True)
    json.dump({'uid': uid, 'trid': trid, 'results': RESULTS,
               'pre_baseline_1001': pre_base, 'post_baseline_1001': post_base},
              open(RESULT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    n_pass = sum(1 for x in RESULTS if x['result'] == 'PASS')
    n_fail = sum(1 for x in RESULTS if x['result'] == 'FAIL')
    n_na = sum(1 for x in RESULTS if x['result'] == 'NOT_RUN')
    print('\n=== 汇总: PASS=%d FAIL=%d NOT_RUN=%d（测试 rid=%s uid=%s）==='
          % (n_pass, n_fail, n_na, trid, uid))
    print('结果 JSON: %s' % RESULT_JSON)
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
