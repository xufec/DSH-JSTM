#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C5-A 条件事件 E2E —— `kill_type_mon` + `use_item`/`consume_item` 接线回归。

## 本批接线的证据（CONFIRMED）
`kill_type_mon` 的 target 是**怪物类型码** = `Config.Mon.fields[4]`（不是 mon_bid）。
三重独立取证：
  ① 配置自证：fields[4]==8 的 15 只怪**全名「狂暴魂兽」**（bid 60154–60243）；
     fields[4]==12 的 21 只全属邪魂师族（邪魂祭祀/邪魂法师/圣灵统领/圣灵精英/圣灵守护兽）。
  ② 任务名自证：码 8 的 6 条任务全名「狂暴魂兽」（75001–75006）；码 12 的名为「灭邪魂师」。
  ③ 客户端自证：`analysis/1.4.9/task/_mission_util_root_full.txt` @2602–2647
     `kill_type_mon` 分支文案 = '邪魂师%s/%s只' / '击杀%s/%s只狂暴魂兽'。

`use_item`/`consume_item` 的 target 是**物品 bid**，触发点 = CS_10505（使用物品）。

## 用例
  1 kill_type_mon：75001（type 8 / need 5）—— 击杀 60154（狂暴魂兽）推进；
     **反例**：击杀 20001（类型码 0，非 8）**不得**推进（证明是按类型过滤而非"任意击杀"）。
  2 use_item    ：52000（use_item 25300 / need 10）—— 用 25300 ×10 后置 STATUS_2；
     **反例**：使用无关物品 **不得**推进。
  3 GM setmissions 现在会把 `target/target_value` 按配置 `progress[0]` 正确播种
     （此前写死 0/1 ⇒ 条件型任务无法推进）。

纪律：全新随机测试账号；绝不触碰 rid=1001；结束自动清场并比对基线。
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
HOST, TCP_PORT, HTTP_PORT = '127.0.0.1', 9000, 8080
BASELINE_RID = 1001

KILL_MISSION = 75001          # 狂暴魂兽：kill_type_mon 8 / need 5
KILL_MON_TYPE8 = 60154        # fields[4]==8 ⇒ 狂暴魂兽
KILL_MON_TYPE0 = 20001        # fields[4]==0 ⇒ 戴浩（反例：不属类型 8）
USE_MISSION = 52000           # 侦查密令：use_item 25300 / need 10
USE_ITEM_BID = 25300
USE_ITEM_OTHER = 25920        # 反例物品

TALK_MISSION = 40000          # 「杀怪」：accept_talk=52002 / accept_npc=10010 / 非 auto_accept
TALK_ACCEPT_BID = 52002
TALK_NPC = 10010

RESULTS = []


def record(name, expected, actual, ok, evidence=''):
    tag = 'PASS' if ok is True else ('FAIL' if ok is False else 'NOT_RUN')
    print('[%s] %-50s | 期望=%s | 实际=%s' % (tag, name, expected, actual))
    RESULTS.append({'name': name, 'result': tag, 'expected': expected,
                    'actual': actual, 'evidence': evidence})
    return ok


def pack_frame(cmd, body=b''):
    return struct.pack('>I', 2 + len(body)) + struct.pack('>H', cmd) + body


def recv_exact(s, n):
    buf = b''
    while len(buf) < n:
        c = s.recv(n - len(buf))
        if not c:
            raise EOFError('closed')
        buf += c
    return buf


def w_str(s):
    b = str(s).encode('utf-8')
    return struct.pack('>H', len(b)) + b


def db_query(sql, args=()):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    r = [dict(x) for x in con.execute(sql, args).fetchall()]
    con.close()
    return r


def gm(act, params):
    qs = '&'.join('%s=%s' % (k, v) for k, v in params.items())
    try:
        c = http.client.HTTPConnection(HOST, HTTP_PORT, timeout=15)
        c.request('GET', '/DSH_ADMIN/%s?%s' % (act, qs))
        r = c.getresponse()
        b = r.read().decode('utf-8', 'replace')
        c.close()
        return r.status, b
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
        ln, rcmd = struct.unpack('>IH', hdr)
        try:
            return rcmd, recv_exact(self.s, ln - 2)
        except (EOFError, OSError):
            return rcmd, None

    def drain_until(self, want, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            rcmd, body = self.read_frame()
            if rcmd == want:
                return body
        return None

    def drain_rest(self, secs):
        end = time.time() + secs
        while time.time() < end:
            self.read_frame()

    def login(self, uid):
        self.send(10001, struct.pack('>H', 1) + b'c' + b'\x00' * 4)
        args = struct.pack('>H', 10)
        for k, v in (('account', uid), ('channelId', '1'), ('device_id', 'c5-cond'),
                     ('enter_srv_id', '1'), ('gettui_cid', ''), ('idfa', ''),
                     ('platform', 'ewan'), ('sign', ''),
                     ('timestamp', str(int(time.time()))), ('token', '')):
            args += w_str(k) + w_str(v)
        self.send(1110, args)
        body = self.drain_until(1110, timeout=5.0)
        if body is None:
            return None
        off = 1 + 2 + struct.unpack_from('>H', body, 1)[0]
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
        body = struct.pack('>B', 0) + w_str(name) + struct.pack('>h', 1) + w_str('ewan')
        self.send(10101, body)
        p = self.drain_until(10101)
        if p is None:
            return None, None
        off = 1 + 2 + struct.unpack_from('>H', p, 1)[0]
        return p[0], struct.unpack_from('>I', p, off)[0]

    def select_role(self, rid):
        self.send(10102, struct.pack('>I', rid) + struct.pack('>B', 1))
        p = self.drain_until(10102, timeout=6.0)
        self.drain_until(10200, timeout=6.0)
        return p[0] if p else None

    def role_init(self, rid):
        self.send(10300, struct.pack('>I', rid))
        self.drain_rest(2.0)

    def afk_start(self):
        """CS_15400（空）→ SC_15400{code,msg}：允许启动挂机。"""
        self.send(15400, b'')
        return self.drain_until(15400, timeout=5.0)

    def afk_mission(self, mission_bid):
        """CS_15402{mission_bid:u32} → SC{mission_bid,map_bid,x,y}：建立挂机会话。"""
        self.send(15402, struct.pack('>I', mission_bid))
        return self.drain_until(15402, timeout=5.0)

    def afk_kill(self, mon_bid):
        """CS_15403{mon_bid:u32} → SC{code,msg}：挂机杀怪上报（真实击杀事件）。"""
        self.send(15403, struct.pack('>I', mon_bid))
        return self.drain_until(15403, timeout=5.0)

    def talk(self, talk_bid, mission_bid, npc_bid):
        """CS_12414{talk_bid:u32, mission_bid:u32, npc_bid:u32} → SC{mission_bid,npc_bid,code,msg}"""
        self.send(12414, struct.pack('>I', talk_bid) + struct.pack('>I', mission_bid) +
                  struct.pack('>I', npc_bid))
        p = self.drain_until(12414, timeout=5.0)
        if p is None:
            return None, None
        off = 8  # mission_bid(4) + npc_bid(4)
        code = p[off]
        return code, None

    def fight_mon(self, mon_bid, drain_secs=60.0):
        """CS_20002 发起战斗（服务端自驱回合）→ 等 20020 后再等 8s 让结算跑完。"""
        self.send(20002, struct.pack('>i', mon_bid))
        t0 = time.time()
        while time.time() - t0 < drain_secs:
            rcmd, _ = self.read_frame()
            if rcmd == 20020:
                self.drain_rest(8.0)
                return True
        return False

    def use_item(self, item_id, bid, n=1):
        """CS_10505{code:u8, item_id:u32, use_num:u16, type:u32, bid:u32}"""
        body = (struct.pack('>B', 0) + struct.pack('>I', item_id) +
                struct.pack('>H', n) + struct.pack('>I', 0) + struct.pack('>I', bid))
        self.send(10505, body)
        return self.drain_until(10505, timeout=5.0)


def mission_row(rid, bid):
    r = db_query('SELECT mission_bid,mission_status,target,target_value,value '
                 'FROM missions WHERE rid=? AND mission_bid=?', (rid, bid))
    return r[0] if r else None


def cleanup(trid, uid):
    con = sqlite3.connect(DB)
    for t in [x[0] for x in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
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

    print('=== C5-A 条件事件 E2E（kill_type_mon / use_item）===')
    pre = db_query('SELECT rid,level,exp FROM roles WHERE rid=?', (BASELINE_RID,))
    print('  基线 rid=1001: %s' % pre)

    uid = 'c5cond_%d' % int(time.time())
    print('  测试账号 uid=%s' % uid)

    cli = Client()
    cli.connect()
    cli.login(uid)
    code, trid = cli.create_role('C5条件')
    print('  建角 code=%s rid=%s' % (code, trid))
    cli.select_role(trid)
    cli.role_init(trid)

    # ══ 场景 1：kill_type_mon（走**挂机杀怪上报** 15403 —— 这类任务的原版通道）══
    # 依据：75001–75006「狂暴魂兽」的第二个 progress 元素正是挂机图 [10002..10005]。
    gm('setlevel', {'rid': trid, 'lev': 30})      # 30 级 ⇒ 挂机点 1（25–34，map 10002）
    time.sleep(0.4)
    st, sb = gm('setmissions', {'rid': trid, 'bid': KILL_MISSION})
    row = mission_row(trid, KILL_MISSION)
    r1 = record('[1] GM setmissions 按配置播种条件(cond/target/need)',
                'cond=kill_type_mon target=8 need=5',
                'http=%s DB=%s' % (st, row),
                bool(row) and row['target'] == 8 and row['target_value'] == 5,
                sb[:220])

    cli.afk_start()
    cli.afk_mission(KILL_MISSION)
    time.sleep(0.3)

    # 反例先行：击杀类型码 0 的怪（20001 戴浩）不得推进类型 8 的条件
    cli.afk_kill(KILL_MON_TYPE0)
    time.sleep(1.3)
    row = mission_row(trid, KILL_MISSION)
    r2 = record('[1] 反例：击杀类型码 0 的怪不推进类型 8 条件',
                'value=0（按类型过滤，非"任意击杀"）',
                'value=%s' % (row and row['value']),
                bool(row) and int(row['value'] or 0) == 0)

    cli.afk_kill(KILL_MON_TYPE8)
    time.sleep(1.3)
    row = mission_row(trid, KILL_MISSION)
    r3 = record('[2] 击杀 60154（狂暴魂兽,类型码 8）⇒ value=1',
                'value=1 status=1',
                'value=%s status=%s' % (row and row['value'], row and row['mission_status']),
                bool(row) and int(row['value'] or 0) == 1)

    for _ in range(4):
        cli.afk_kill(KILL_MON_TYPE8)
        time.sleep(1.3)                            # 15403 频率门 1.0s
    row = mission_row(trid, KILL_MISSION)
    r4 = record('[2] 累计 5 杀 ⇒ 条件达成置 STATUS_2（可提交）',
                'value=5 status=2',
                'value=%s status=%s' % (row and row['value'], row and row['mission_status']),
                bool(row) and int(row['value'] or 0) == 5
                and int(row['mission_status'] or 0) == 2)

    # ══ 场景 2：use_item / consume_item ═════════════════════════════════
    st, sb = gm('setmissions', {'rid': trid, 'bid': USE_MISSION})
    row = mission_row(trid, USE_MISSION)
    r5 = record('[3] setmissions 播种 use_item 条件',
                'target=%d need=10' % USE_ITEM_BID,
                'http=%s DB=%s' % (st, row),
                bool(row) and row['target'] == USE_ITEM_BID and row['target_value'] == 10,
                sb[:200])

    gm('addbag', {'rid': trid, 'bid': USE_ITEM_BID, 'n': 12, 'code': 1})
    gm('addbag', {'rid': trid, 'bid': USE_ITEM_OTHER, 'n': 3, 'code': 1})
    time.sleep(0.5)
    iid = {r['bid']: r['item_id'] for r in db_query(
        'SELECT item_id,bid FROM bag_items WHERE rid=?', (trid,))}
    if USE_ITEM_BID not in iid:
        record('[3] 物品入包（前置）', 'bid=%d 在包内' % USE_ITEM_BID,
               'bag ids=%s' % list(iid), False)
    else:
        # 反例：使用无关物品
        cli.use_item(iid[USE_ITEM_OTHER], USE_ITEM_OTHER, 1)
        row = mission_row(trid, USE_MISSION)
        r6 = record('[3] 反例：使用无关物品不推进 use_item 条件',
                    'value=0', 'value=%s' % (row and row['value']),
                    bool(row) and int(row['value'] or 0) == 0)

        # 正向：用 10 个
        for _ in range(10):
            cli.use_item(iid[USE_ITEM_BID], USE_ITEM_BID, 1)
        row = mission_row(trid, USE_MISSION)
        r7 = record('[4] 使用 %d ×10 ⇒ 条件达成置 STATUS_2' % USE_ITEM_BID,
                    'value=10 status=2',
                    'value=%s status=%s' % (row and row['value'], row and row['mission_status']),
                    bool(row) and int(row['value'] or 0) == 10
                    and int(row['mission_status'] or 0) == 2)

    cli.close()

    # ══ 场景 3：12414 对话推进（accept_talk 真正接取任务）════════════════
    # 40000「杀怪」：accept_talk=52002 / accept_npc_id=10010 / progress=[[kill_scene_mon,16000,1],…]
    # 且其 auto_accept **未置位** ⇒ 该任务的接取入口就是这段对话（统计自证）。
    cli2 = Client()
    cli2.connect()
    cli2.login(uid)
    cli2.select_role(trid)
    cli2.role_init(trid)
    gm('setmissions', {'rid': trid, 'bid': 10010})   # 清空并把链头设为 10010（40000 不在库里）
    time.sleep(0.5)
    before = db_query('SELECT COUNT(*) c FROM missions WHERE rid=? AND mission_bid=?',
                      (trid, TALK_MISSION))[0]['c']
    code14, _ = cli2.talk(TALK_ACCEPT_BID, TALK_MISSION, TALK_NPC)
    row = mission_row(trid, TALK_MISSION)
    r8 = record('[7] 12414 accept_talk ⇒ 真正接取任务（此前只回显）',
                'code=1 且 DB 出现 mission_bid=%d status=1 target=16000' % TALK_MISSION,
                'code=%s before=%s DB=%s' % (code14, before, row),
                code14 == 1 and before == 0 and bool(row)
                and int(row['mission_status'] or 0) == 1 and row['target'] == 16000)

    # 幂等：同一条对话再发一次不得重复建行 / 不得报错
    code14b, _ = cli2.talk(TALK_ACCEPT_BID, TALK_MISSION, TALK_NPC)
    cnt = db_query('SELECT COUNT(*) c FROM missions WHERE rid=? AND mission_bid=?',
                   (trid, TALK_MISSION))[0]['c']
    r9 = record('[7] 12414 重复对话幂等（不重复建行）',
                'code=1 且行数=1', 'code=%s rows=%s' % (code14b, cnt),
                code14b == 1 and cnt == 1)

    # process_talk：只确认、不改状态（配置中不存在 talk 类 progress 条件，已全表核过）
    st_before = mission_row(trid, TALK_MISSION)['mission_status']
    code14c, _ = cli2.talk(50070, 10070, 0)
    st_after = mission_row(trid, TALK_MISSION)['mission_status']
    r10 = record('[7] 12414 process_talk ⇒ 确认但不伪造进度',
                 'code=1 且原有任务状态不变',
                 'code=%s status %s→%s' % (code14c, st_before, st_after),
                 code14c == 1 and st_before == st_after)

    # 负例：不存在的任务必须诚实拒绝
    code14d, _ = cli2.talk(12345, 999999, 0)
    r11 = record('[7] 12414 非法 mission_bid ⇒ 诚实拒绝 code=0',
                 'code=0', 'code=%s' % code14d, code14d == 0)
    cli2.close()

    # ══ 场景 4：离线挂机收益结算（C5-C）══════════════════════════════════
    # 10933 是客户端"离线挂机开"；收益速率客户端侧无表（已取证），故速率是
    # # INFERENCE 占位且**可由 config.json 覆盖**。这里验证"机制"（时长×速率、幂等结算），
    # 不验证"速率真值"（那是 BLOCKED，需真服抓包）。
    import json as _json
    cli3 = Client()
    cli3.connect()
    cli3.login(uid)
    cli3.select_role(trid)
    cli3.role_init(trid)
    cli3.send(10933, b'')
    cli3.drain_until(10933, timeout=5.0)
    # 时间旅行夹具：把 off_started_at 拨回 10 分钟（否则要真等 600s 才够 1 分钟粒度）
    _con3 = sqlite3.connect(DB)
    _con3.execute('UPDATE guaji_state SET off_started_at=? WHERE rid=?',
                  (int(time.time()) - 600, trid))
    _con3.commit()
    _con3.close()

    st, sb = gm('afk_status', {'rid': trid})
    off = (_json.loads(sb).get('result') or {}).get('offline') or {}
    r12 = record('[8] afk_status 回出离线会话累计（此前只落状态不结算）',
                 'on=1 且 minutes>=9',
                 'http=%s offline=%s' % (st, off),
                 st == 200 and int(off.get('on') or 0) == 1
                 and int(off.get('minutes') or 0) >= 9)

    g0 = db_query("SELECT amount FROM role_assets WHERE rid=? AND name='gold'",
                  (trid,))[0]['amount']
    st2, sb2 = gm('afk_offline_claim', {'rid': trid})
    j2 = _json.loads(sb2)
    g1 = db_query("SELECT amount FROM role_assets WHERE rid=? AND name='gold'",
                  (trid,))[0]['amount']
    r13 = record('[9] afk_offline_claim 真发奖（gold 增加）',
                 'ok=True 且 gold 增加',
                 'http=%s gold %s→%s result=%s' % (st2, g0, g1, j2.get('result')),
                 st2 == 200 and j2.get('ok') is True and g1 > g0)

    st3, sb3 = gm('afk_offline_claim', {'rid': trid})
    j3 = _json.loads(sb3)
    g2 = db_query("SELECT amount FROM role_assets WHERE rid=? AND name='gold'",
                  (trid,))[0]['amount']
    r14 = record('[9] 重复结算幂等（reward_log 挡住，不二次发奖）',
                 'already=True 且 gold 不再增加',
                 'gold %s→%s result=%s' % (g1, g2, (j3.get('result') or {}).get('already')),
                 g2 == g1 and bool((j3.get('result') or {}).get('already')))
    cli3.close()

    if not args.keep:
        cleanup(trid, uid)
        left = db_query('SELECT COUNT(*) c FROM roles WHERE rid=?', (trid,))[0]['c']
        acc = db_query('SELECT COUNT(*) c FROM accounts WHERE uid=?', (uid,))[0]['c']
        record('[5] 测试账号清理无残留', 'roles=0 accounts=0',
               'roles=%s accounts=%s' % (left, acc), left == 0 and acc == 0)

    post = db_query('SELECT rid,level,exp FROM roles WHERE rid=?', (BASELINE_RID,))
    record('[6] 基线 rid=1001 未被动过', 'pre==post',
           'equal=%s' % (pre == post), pre == post)

    npass = sum(1 for x in RESULTS if x['result'] == 'PASS')
    nfail = sum(1 for x in RESULTS if x['result'] == 'FAIL')
    print('\n──────── 结果 ────────')
    print('检查项 %d，通过 %d，失败 %d' % (len(RESULTS), npass, nfail))
    for x in RESULTS:
        if x['result'] == 'FAIL':
            print('  - %s | 期望=%s 实际=%s' % (x['name'], x['expected'], x['actual']))
    return 1 if nfail else 0


if __name__ == '__main__':
    sys.exit(main())
