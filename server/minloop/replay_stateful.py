#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**状态感知**的真机帧回放（`replay_real_frames.py` 的升级版）。

为什么要它：旧版只回答"应答能不能按权威 SC 严格解析 + code 对不对"——**从不看数据库**。
于是"服务端回了 code=1、但其实什么都没落库"这种假成功，旧版抓不到。

本文件做的事：
  每条源日志各起一个**全新**最小回环服务器（独立端口 + 临时 DB，与 selftest.py 同款进程内
  模式），把该日志里客户端**真实发出的帧按原顺序**灌进去；在每个**回环关键帧**
  （`Session.LOOP`，11 条）前后对 `Store` 做快照 ⇒ 用**库里的行**断言副作用：
      · 任务：12402/12403/20002 有没有创建 / 推进 `missions` 行
      · 背包：20002/10500 有没有让 `bag` 真的多一件
      · 货币：提交/击杀有没有让 `roles` 的 coin/gold/coupon/exp/hero_exp 变化
  并把每个关键帧的**服务端应答**逐帧记下来（含 SC 严格性与 code/msg）。

诚实纪律（硬，与 TASK 一致）：
  ① 只断言"**真实帧** + `server/mission_config.json`"能推出的东西；
  ② 抓包不含完整会话时（例：没有 10102 角色登录、没有 12402 接取、
     战斗怪 id 不在 `server/config.json`），一律记 **replay context disconnected**，
     **不**当服务端 bug；
  ③ 无法验证的一律打印 **UNKNOWN**，绝不编造期望值。

与 `replay_real_frames.py` 的差异（有意）：
  · 本文件把**抽出来的每一帧都发**（含 `protocol/fields.json` 里无 CS/SC 定义的命令），
    因为"状态感知"要求顺序完整；旧版会跳过无规格的命令。
  · 本文件**不**把服务端逐帧日志打到 stdout（会淹掉表格），但全部收进内存，
    结束时把其中的异常行（` !! `）打出来当证据。`REPLAY_VERBOSE=1` 可恢复原样。

用法：python server/minloop/replay_stateful.py [日志文件...]
"""
from __future__ import annotations

import os
import socket
import sys
import tempfile
import threading
import time
import hashlib
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import min_loop_server as M  # noqa: E402
from replay_real_frames import frames_from_log  # noqa: E402
from selftest import Client, free_port  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(HERE)

# 抓包日志在**项目根**的 logs/1.4.9/（不是 server/logs/），按任务给定默认值解析。
ROOT = os.path.dirname(SERVER_DIR)
DEFAULT_LOGS = [os.path.join(ROOT, 'logs', '1.4.9', 'battle_chain_tcp.log'),
                os.path.join(ROOT, 'logs', '1.4.9', 'task_chain_tcp.log')]

ASSET_KEYS = ('coin', 'gold', 'coupon', 'exp', 'hero_exp')
LOOP_CRITICAL = sorted(M.Session.LOOP)

# ── 服务端日志捕获（只收不发，异常行留作证据）──────────────────────────────────
SRV_LOG = []
_ORIG_LOG = M.log


def _cap(msg):
    SRV_LOG.append(str(msg))
    if os.environ.get('REPLAY_VERBOSE'):
        _ORIG_LOG(msg)


M.log = _cap


# ── Store 快照 / 差分 ───────────────────────────────────────────────────────

def snapshot(store):
    return {
        'missions': {(r['rid'], r['mission_bid']): (r['status'], r['progress'])
                     for r in store.all('SELECT * FROM missions')},
        'bag': {r['item_id']: (r['rid'], r['bid'], r['quantity'])
                for r in store.all('SELECT * FROM bag')},
        'assets': {r['rid']: tuple(int(r[k] or 0) for k in ASSET_KEYS)
                   for r in store.all('SELECT * FROM roles')},
    }


def diff(before, after):
    eff = {'mission_new': [], 'mission_chg': [], 'bag_new': [], 'bag_chg': [], 'assets': []}
    for k, v in after['missions'].items():
        if k not in before['missions']:
            eff['mission_new'].append((k[0], k[1], v[0], v[1]))
        elif before['missions'][k] != v:
            eff['mission_chg'].append((k[0], k[1], before['missions'][k], v))
    for iid, v in after['bag'].items():
        if iid not in before['bag']:
            eff['bag_new'].append((v[0], v[1], v[2]))
        elif before['bag'][iid] != v:
            eff['bag_chg'].append((v[0], v[1], v[2] - before['bag'][iid][2]))
    for rid, v in after['assets'].items():
        b = before['assets'].get(rid)
        d = {k: v[i] - (b[i] if b else 0) for i, k in enumerate(ASSET_KEYS)
             if v[i] - (b[i] if b else 0)}
        if d:
            eff['assets'].append((rid, d))
    return eff


def eff_empty(eff):
    return not any(eff.values())


def eff_str(eff):
    parts = []
    if eff['mission_new']:
        parts.append('任务新建 ' + ','.join('rid=%s bid=%s st=%s pr=%s' % x
                                           for x in eff['mission_new']))
    if eff['mission_chg']:
        parts.append('任务推进 ' + ','.join('rid=%s bid=%s %s→%s' % (x[0], x[1], x[2], x[3])
                                           for x in eff['mission_chg']))
    if eff['bag_new']:
        parts.append('进包 ' + ','.join('rid=%s bid=%s x%s' % x for x in eff['bag_new']))
    if eff['bag_chg']:
        parts.append('进包(叠) ' + ','.join('rid=%s bid=%s +%s' % x for x in eff['bag_chg']))
    if eff['assets']:
        parts.append('货币 ' + ','.join('rid=%s %s' % (x[0], x[1]) for x in eff['assets']))
    return '; '.join(parts)


# ── 单条日志的回放 ──────────────────────────────────────────────────────────

def classify_negative(msg):
    """「诚实拒绝」与「回放上下文不连贯」分开 —— 后者不是服务端 bug。"""
    if '怪物不在场' in msg:
        return 'disconnected:mon_not_in_config'
    if '任务不存在' in msg:
        return 'disconnected:mission_not_in_config'
    if '条件未满足' in msg:
        return 'honest_reject:condition_not_met'
    return 'honest_reject:other'


def start_server(prefix):
    port, hp = free_port(), free_port()
    tmp = tempfile.mkdtemp(prefix=prefix)
    db = os.path.join(tmp, 'replay.db')
    srv = M.Server(hp, port, db, bind='127.0.0.1')
    threading.Thread(target=srv.run, daemon=True).start()
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
            return srv, port, db
        except OSError:
            time.sleep(0.05)
    raise RuntimeError('最小回环服务器没起来（端口 %d）' % port)


def srv_rev():
    """被回放的那份 `min_loop_server.py` 的修订指纹（本仓库是多人并发的 ⇒ 必须记）。"""
    p = os.path.join(HERE, 'min_loop_server.py')
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def replay(path):
    """一条日志 = 一个全新服务器 + 临时 DB；回放其真实帧并记录每帧的应答与 DB 副作用。"""
    frames = frames_from_log(path)
    srv, port, db = start_server('minloop_stateful_')
    spec = srv.spec
    c = Client(spec, '127.0.0.1', port)

    res = OrderedDict(name=os.path.basename(path), path=path, db=db,
                      frames=len(frames), sent=0, no_cs=0,
                      cmds=Counter(cmd for cmd, _b in frames),
                      strict_bad=[], code_bad=[], honest=Counter(), negatives=[],
                      no_reply=[], critical=[], reply_cmds=Counter(),
                      mission_new=Counter(), mission_chg=Counter(),
                      bag_new=Counter(), assets={}, unparsed_conditions=[],
                      srv_exc=[], malformed=[])

    for idx, (cmd, body) in enumerate(frames):
        if not spec.has_sc(cmd) and not spec.cs.get(cmd):
            res['no_cs'] += 1
        critical = cmd in M.Session.LOOP
        if not critical:
            c.recv_all(0.05, 0.03)                 # 先清干净，免得上帧残留混进来
        before = snapshot(srv.store) if critical else None
        c.send(cmd, raw=body)
        res['sent'] += 1

        replies = c.recv_all(0.8 if critical else 0.12, 0.25 if critical else 0.05)
        got = []
        for rcmd, vals, ok, detail in replies:
            res['reply_cmds'][rcmd] += 1
            if not ok:
                res['strict_bad'].append((idx, rcmd, detail))
            code = vals.get('code') if isinstance(vals, dict) else None
            msg = vals.get('msg') if isinstance(vals, dict) else None
            got.append((rcmd, ok, code, msg))
            if rcmd in M.Session.LOOP and code not in (None, 1):
                if code == 0 and msg:
                    key = classify_negative(msg)
                    res['honest'][key] += 1
                    res['negatives'].append((idx, rcmd, key, msg))
                else:
                    res['code_bad'].append((idx, rcmd, code, msg))
        if critical:
            after = snapshot(srv.store)
            eff = diff(before, after)
            try:
                cs = spec.read_cs(cmd, body) if spec.cs.get(cmd) else None
            except Exception as e:                 # noqa: BLE001
                cs = None
                res['malformed'].append((idx, cmd, repr(e), body[:16].hex(' ')))
            res['critical'].append((idx, cmd, cs, got, eff))
            if not replies:
                res['no_reply'].append((idx, cmd))
            for rid, bid, st, pr in eff['mission_new']:
                res['mission_new'][(rid, bid)] += 1
            for rid, bid, _old, _new in eff['mission_chg']:
                res['mission_chg'][(rid, bid)] += 1
            for rid, bid, q in eff['bag_new']:
                res['bag_new'][(rid, bid)] += q
            for rid, bid, dq in eff['bag_chg']:
                res['bag_new'][(rid, bid)] += dq
            for rid, d in eff['assets']:
                cur = res['assets'].setdefault(rid, {})
                for k, v in d.items():
                    cur[k] = cur.get(k, 0) + v
            # 配置里有、但本服 mission_target 解析不出来的条件形态（只记录当证据，不修）
            if cmd == 12403 and cs:
                m = srv.data.mission(int(cs.get('mission_bid') or 0))
                if m is not None:
                    tgt, need = M.Session.mission_target(m)
                    p = m.get('progress') or []
                    if p and need == 0:
                        res['unparsed_conditions'].append((m['bid'], repr(p), tgt, need))
    c.recv_all(0.4, 0.1)
    c.close()

    res['spec'] = spec
    res['srv_exc'] = [l for l in SRV_LOG if ' !! ' in l]
    res['mission_rows'] = [(r['rid'], r['mission_bid'], r['status'], r['progress'])
                           for r in srv.store.all('SELECT * FROM missions')]
    res['bag_rows'] = [(r['rid'], r['bid'], r['quantity'])
                       for r in srv.store.all('SELECT * FROM bag')]
    res['final_assets'] = {r['rid']: {k: r[k] for k in ASSET_KEYS}
                           for r in srv.store.all('SELECT * FROM roles')}
    return res


# ── UNKNOWN：抓包里没有的东西，绝不用"期望值"填空 ─────────────────────────────

UNKNOWN_NOTES = {
    10102: '角色登录：抓包无此帧 ⇒ 会话从未绑定角色（服务器只在 10300/10301 时兜底取默认角色）'
           '⇒ "登录指定角色后落库"这条路径无法用真实帧断言',
    12400: '任务列表：抓包无此帧 ⇒ 无法用真实帧断言列表下发内容',
    12402: '任务接取：抓包无此帧 ⇒ "接取后 missions 落行"这条路径**无法用真实帧断言**',
    12403: '任务提交：抓包无此帧 ⇒ 提交/发奖路径无法用真实帧断言',
    20002: '战斗发起：抓包无此帧 ⇒ 战斗/掉落/击杀奖励路径无法用真实帧断言',
    10502: '背包查询：抓包无此帧 ⇒ 10502 回包与库里数据的一致性无法用真实帧断言',
}


def unknown_for(res, mons):
    out = []
    for cmd, note in sorted(UNKNOWN_NOTES.items()):
        if res['cmds'].get(cmd, 0) == 0:
            out.append(note)
    seen = set()
    for _idx, cmd, cs, _got, _eff in res['critical']:
        if cmd == 20002 and cs:
            seen.add(int(cs.get('mon_id') or 0))
    for mid in sorted(seen - mons):
        out.append('战斗怪 id=%d 不在 server/config.json（在场怪 %s）⇒ 该帧判为 '
                   'replay context disconnected' % (mid, sorted(mons)))
    for idx, cmd in res['no_reply']:
        if res['spec'].has_sc(cmd):                # 有 SC 却不回包 = 可疑（不明说成 bug）
            out.append('#%d cmd=%d 有 SC 定义却**没有应答** ⇒ 该关键帧的落库效果无法归因'
                       '（UNKNOWN，不作服务端 bug 结论）' % (idx, cmd))
    return out


def expected_no_reply(res):
    """协议里没有 SC 定义 ⇒ 本服**规定不回包**（10001 等）：预期行为，不是问题。"""
    return sorted({cmd for _idx, cmd in res['no_reply'] if not res['spec'].has_sc(cmd)})


# ── 主流程 ──────────────────────────────────────────────────────────────────

def _selftest():
    """diff() 的唯一自检：新建 / 推进 / 叠包 / 货币 四类副作用都必须被抓到。"""
    b = {'missions': {(1001, 10010): (1, 0)}, 'bag': {1: (1001, 33001, 1)},
         'assets': {1001: (0, 0, 0, 0, 0)}}
    a = {'missions': {(1001, 10010): (1, 1), (1001, 10020): (2, 0)},
         'bag': {1: (1001, 33001, 3)},
         'assets': {1001: (1290, 0, 0, 500, 500)}}
    e = diff(b, a)
    assert e['mission_new'] == [(1001, 10020, 2, 0)], e
    assert e['mission_chg'] == [(1001, 10010, (1, 0), (1, 1))], e
    assert e['bag_chg'] == [(1001, 33001, 2)] and not e['bag_new'], e
    assert e['assets'] == [(1001, {'coin': 1290, 'exp': 500, 'hero_exp': 500})], e
    assert eff_empty(diff(b, b)), e
    assert classify_negative('怪物不在场') == 'disconnected:mon_not_in_config'
    assert classify_negative('条件未满足（0/1）') == 'honest_reject:condition_not_met'
    print('replay_stateful 自检通过（diff 四类副作用 + 拒绝分类）')
    return 0


def main(argv):
    if '--selftest' in argv:
        return _selftest()
    logs = [p for p in (argv[1:] or DEFAULT_LOGS) if os.path.exists(p)]
    if not logs:
        print('找不到抓包日志：%s' % (argv[1:] or DEFAULT_LOGS))
        return 2
    mons = {int(m['id']) for m in M.Data().mons}

    rev0 = srv_rev()
    print('被回放的服务器源码 min_loop_server.py rev=%s（本仓库多人并发，数字只对这份修订有效）'
          % rev0)
    results = []
    for p in logs:
        print('… 回放 %s' % p)
        sys.stdout.flush()
        results.append(replay(p))
    rev1 = srv_rev()
    if rev1 != rev0:
        print('★ 警告：运行期间 min_loop_server.py 被并发改动（rev %s → %s）⇒ 上面的数字可能'
              '对应改前那份，重跑一次。' % (rev0, rev1))

    # ── 逐日志明细（含"每个关键帧的服务端应答"）─────────────────────────────
    for res in results:
        print('\n' + '═' * 78)
        print('源日志：%s' % res['path'])
        print('帧 %d（其中 %d 条在 protocol/fields.json 里无 CS/SC 定义，仍按原顺序发出）'
              % (res['frames'], res['no_cs']))
        print('DB：%s' % res['db'])
        print('回环关键帧（Session.LOOP %s）共 %d 个：' % (LOOP_CRITICAL, len(res['critical'])))
        print('─' * 78)
        for idx, cmd, cs, got, eff in res['critical']:
            rep = ', '.join('re%d%s%s' % (c, '' if ok else '!规格不符',
                                          (' code=%s msg=%r' % (code, msg))
                                          if (code is not None or msg) else '')
                            for c, ok, code, msg in got) or '（无应答）'
            print('#%-4d cmd=%-5d cs=%-32s ← %s' % (idx, cmd, str(cs)[:32], rep))
            if not eff_empty(eff):
                print('        DB ⇒ %s' % eff_str(eff))
        if res['no_reply']:
            exp = expected_no_reply(res)
            print('关键帧无应答 %d 个；其中协议无 SC ⇒ 规定不回包（预期）：%s'
                  % (len(res['no_reply']), exp or '无'))
        if res['unparsed_conditions']:
            print('★ 配置条件形态解析不了（mission_target 只认 list[dict]）—— 见报告"发现"：')
            for bid, p, tgt, need in res['unparsed_conditions']:
                print('   bid=%s progress=%s ⇒ target=%s need=%s' % (bid, p, tgt, need))
        print('库里最终 missions：%s' % (res['mission_rows'] or '（空）'))
        print('库里最终 bag：%s' % (res['bag_rows'] or '（空）'))
        print('库里最终 assets：%s' % res['final_assets'])
        if res['malformed']:
            print('CS 解析异常帧：%s' % res['malformed'])
        if res['srv_exc']:
            print('服务端异常行 %d 条；完整输出前 2 条（证据）：' % len(res['srv_exc']))
            for l in res['srv_exc'][:2]:
                print('   ' + l.replace('\n', '\n   '))
        if res['negatives']:
            print('诚实拒绝 / 上下文不连贯 %d 次：' % len(res['negatives']))
            for idx, cmd, key, msg in res['negatives'][:8]:
                print('   #%-4d cmd=%-5d %-38s %s' % (idx, cmd, key, msg))

    # ── 汇总表 ─────────────────────────────────────────────────────────────
    print('\n' + '═' * 78)
    print('汇总（每条日志 = 一个全新服务器 + 临时 DB）')
    hdr = ('%-24s %6s %6s %6s %8s %6s %6s %6s %8s %8s'
           % ('源日志', '帧', '命令', '回放', '严格不符', '任务写', '背包件', '货币',
              '诚实拒绝', 'UNKNOWN'))
    print(hdr)
    print('-' * len(hdr))
    for res in results:
        unk = unknown_for(res, mons)
        nmiss = sum(res['mission_new'].values()) + sum(res['mission_chg'].values())
        nbag = sum(res['bag_new'].values())
        ncur = sum(len(v) for v in res['assets'].values())
        print('%-24s %6d %6d %6d %8d %6d %6d %6d %8d %8d'
              % (res['name'], res['frames'], len(res['cmds']), res['sent'],
                 len(res['strict_bad']), nmiss, nbag, ncur,
                 sum(res['honest'].values()), len(unk)))

    # ── 观察到的 DB 副作用（数字）───────────────────────────────────────────
    print('\n观察到的 DB 副作用（判据是库里的行，不是应答里的 code）：')
    any_eff = False
    for res in results:
        if res['mission_new'] or res['mission_chg'] or res['bag_new'] or res['assets']:
            any_eff = True
        print('  %s' % res['name'])
        print('    任务新建：%s' % (dict(res['mission_new']) or '无'))
        print('    任务推进：%s' % (dict(res['mission_chg']) or '无'))
        print('    背包进物：%s' % (dict(res['bag_new']) or '无'))
        print('    货币变化：%s' % (res['assets'] or '无'))
    if not any_eff:
        print('    两条源日志都没有观察到任何 DB 副作用。')

    # ── 无法断言 / UNKNOWN ─────────────────────────────────────────────────
    print('\n无法断言 / UNKNOWN：')
    u = 0
    for res in results:
        for n in unknown_for(res, mons):
            print('  [%s] %s' % (res['name'], n))
            u += 1
        exp = expected_no_reply(res)
        if exp:
            print('  [%s] 预期不回包（protocol 无 SC，本服规定不应答，非问题）：%s'
                  % (res['name'], exp))
    if not u:
        print('  无（除上列预期不回包外）。')

    strict = sum(len(r['strict_bad']) for r in results)
    danger = sum(len(r['code_bad']) for r in results)
    exc = sum(len(r['srv_exc']) for r in results)
    honest = sum(sum(r['honest'].values()) for r in results)
    print('\n总计：严格不符 %d；危险应答（code=0 且 msg 空 / 非法 code）%d；'
          '服务端异常行 %d；诚实拒绝/上下文不连贯 %d'
          % (strict, danger, exc, honest))
    ok = (strict == 0 and danger == 0)
    print('结论：%s' % ('真实帧状态化回放：无规格不符、无危险应答'
                      if ok else '存在失败项，见上'))
    sys.stdout.flush()
    os._exit(0 if ok else 1)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
