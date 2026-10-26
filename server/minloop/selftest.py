#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小回环自检 —— 不依赖模拟器/客户端，直接用**真实协议规格**驱动整条回环。

它做的事：
  1. 起一个最小回环服务器（独立临时 DB、独立端口，绝不碰参考服的 8080/9000 与 roles.db）
  2. 用一个合成客户端把 **登录 → 角色 → 进场景 → 接任务 → 打怪 → 结算 → 掉落 → 提交 → 奖励 → 背包**
     整条链走完
  3. 每一帧都按 `protocol/fields.json` 的权威 SC 规格**严格解析**：
     少字节 / 多字节 / 结构不符 ⇒ 直接 FAIL（这是本项目"SC 被截断"踩过 4 次的那类 bug）
  4. 断言回环的**业务结果**：任务状态、怪物掉进包、奖励加到了货币上、背包能查到

用法：python server/minloop/selftest.py
"""
from __future__ import annotations

import json
import os
import socket
import struct
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import min_loop_server as M  # noqa: E402

FAILS = []
CHECKS = []


def check(cond, label, detail=''):
    CHECKS.append((bool(cond), label, detail))
    if not cond:
        FAILS.append('%s %s' % (label, detail))
    print('%s %s%s' % ('PASS' if cond else 'FAIL', label, ('  — ' + detail) if detail else ''))


# ── 权威规格的严格解码（镜像编码器；多/少字节都会被抓出来）──────────────────

def decode(fields, body):
    o = 0

    def rd(fs, buf, off):
        out = {}
        for f in fs or []:
            if not isinstance(f, dict):
                continue
            name = f.get('name') or ''
            items = f.get('items') or []
            if items:
                n = struct.unpack_from('>H', buf, off)[0]
                off += 2
                rows = []
                for _ in range(n):
                    r, off = rd(items, buf, off)
                    rows.append(r)
                out[name] = rows
                continue
            w = M.field_width(f.get('type'))
            if w == -1:
                n = struct.unpack_from('>H', buf, off)[0]
                out[name] = buf[off + 2:off + 2 + n].decode('utf-8', 'replace')
                off += 2 + n
            else:
                signed = (f.get('type') or '').lower().startswith('int')
                out[name] = int.from_bytes(buf[off:off + w], 'big', signed=signed)
                off += w
        return out, off

    vals, o = rd(fields, body, 0)
    return vals, o


# ── 合成客户端 ──────────────────────────────────────────────────────────────

class Client(object):
    def __init__(self, spec, host, port):
        self.spec = spec
        self.sock = socket.create_connection((host, port), timeout=5)
        self.sock.settimeout(2.0)
        self.buf = b''
        self.trace = []

    def send(self, cmd, values=None, raw=None):
        body = raw if raw is not None else (self.spec._enc_fields(
            self.spec.cs.get(cmd) or [], values or {}))
        self.sock.sendall(M.pack_frame(cmd, body))
        self.trace.append(('>>', cmd, len(body)))

    def recv_all(self, wait=0.35, idle=0.15):
        """收齐当前所有帧：[(cmd, body_dict, strict_ok, detail)]

        ⚠ 不能"收到一帧且缓冲为空就返回"——服务端应答后面常常**紧跟主动推送**
        （10102 后面就是 10200/10201），那样会把推送全漏掉。
        正确口径：**一直收到空闲超时**为止。
        """
        end = time.time() + wait
        out = []
        self.sock.settimeout(idle)
        while time.time() < end:
            try:
                d = self.sock.recv(65536)
            except socket.timeout:
                if out:
                    break                     # 已有数据且空闲 ⇒ 这一批收完了
                continue                      # 还没有数据 ⇒ 继续等到 wait
            if not d:
                break
            self.buf += d
            self.buf = self._drain(out, time.time())
        self.buf = self._drain(out, time.time())
        return out

    def _drain(self, out, end):
        while len(self.buf) >= 6:
            ln = struct.unpack_from('>I', self.buf, 0)[0]
            cmd = struct.unpack_from('>H', self.buf, 4)[0]
            if len(self.buf) < 4 + ln:
                break
            body = self.buf[6:4 + ln]
            self.buf = self.buf[4 + ln:]
            fields = self.spec.sc.get(cmd)
            if fields is None:
                out.append((cmd, None, False, 'SC 无定义却回了包'))
                continue
            try:
                vals, used = decode(fields, body)
                strict = (used == len(body))
                out.append((cmd, vals, strict,
                            '' if strict else '规格 %d 字节 / 实际 %d 字节' % (used, len(body))))
            except Exception as e:            # noqa: BLE001
                out.append((cmd, None, False, '解析异常 %r' % (e,)))
        return self.buf

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main():
    port = free_port()
    hp = free_port()
    tmp = tempfile.mkdtemp(prefix='minloop_selftest_')
    db = os.path.join(tmp, 'test.db')
    srv = M.Server(hp, port, db, bind='127.0.0.1')
    t = threading.Thread(target=srv.run, daemon=True)
    t.start()
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)

    spec = srv.spec
    c = Client(spec, '127.0.0.1', port)

    def strict_ok(frames, label):
        bad = [f for f in frames if not f[2]]
        check(not bad, '%s：SC 严格符合规格' % label,
              '; '.join('cmd=%s %s' % (b[0], b[3]) for b in bad))

    # ① 连接首包（CS-only ⇒ 不应答）
    c.send(10001, {'key': 'game_client'}, raw=M.w_u16(11) + b'game_client' + b'\x00' * 4)
    f = c.recv_all(0.4)
    check(len(f) == 0, '10001 CS-only 不回包', '回了 %s' % [x[0] for x in f])

    # ② 心跳
    c.send(1199, {}, raw=b'')
    f = c.recv_all()
    check(any(x[0] == 1199 and x[1] and x[1]['time'] > 0 for x in f), '1199 心跳有应答')
    strict_ok(f, '1199')

    # ③ 帐号登录 → 角色列表（code 必须 = 1）
    c.send(1110, {}, raw=M.w_str('account') + M.w_str('dsh_test')
           + M.w_str('platform') + M.w_str('ewan') + b'\x00\x00')
    f = c.recv_all()
    r1110 = next((x for x in f if x[0] == 1110), None)
    check(r1110 is not None, '1110 有应答')
    check(r1110 and r1110[1]['code'] == 1, '1110 code==1（TRUE）',
          'code=%s' % (r1110[1]['code'] if r1110 and r1110[1] else '?'))
    # ★ 已改：1110不再自动捧默认角色 ⇒ 列表**可以为空**（交给客户端走“创建角色”）
    check(r1110 and r1110[1]['roles'] is not None,
          '1110 带 roles 字段（可为空 ⇒ 客户端走创建角色）')
    strict_ok(f, '1110')
    # ★ 1110 不再自动捏角色、10102 也不再兜底 ⇒ 自检必须**先自己建一个角色**（正好覆盖 10101）
    if r1110 and r1110[1]['roles']:
        rid = r1110[1]['roles'][0]['rid']
    else:
        c.send(10101, {'sex': 0, 'name': '自检角色', 'career': 5, 'playform': 'android'})
        f_c0 = c.recv_all(0.6)
        r_c0 = next((x for x in f_c0 if x[0] == 10101), None)
        check(r_c0 is not None and r_c0[1]['code'] == 0 and int(r_c0[1]['rid']) > 0,
              '★ 空列表时先建角（code=0）再登录', 
              'code=%s rid=%s' % (r_c0[1]['code'] if r_c0 and r_c0[1] else '?',
                                  r_c0[1]['rid'] if r_c0 and r_c0[1] else '?'))
        rid = int(r_c0[1]['rid']) if r_c0 and r_c0[1] else 1001
        strict_ok(f_c0, '10101(自检建角)')

    # ④ 登录指定角色 → 10102 + 推 10200 / 10201
    c.send(10102, {'rid': rid, 'srv_id': '1'})
    f = c.recv_all(0.6)
    cmds = [x[0] for x in f]
    check(10102 in cmds, '10102 有应答')
    check(10200 in cmds, '10200 进场景推送')
    e10200 = next((x for x in f if x[0] == 10200), None)
    check(e10200 and e10200[1]['bid'] > 0, '10200 带真实场景 bid',
          'bid=%s' % (e10200[1]['bid'] if e10200 and e10200[1] else '?'))
    # ★ 10200 是 `code==1 才是成功` 的**例外**：scene_controller.luac proto[16]
    #   写的是 `if resp.code ~= 0 then message2(resp.msg) end` ⇒ **必须发 0**。
    #   这条断言防止再被"通则"改回 1（本项目实测发 1 会导致客户端不真正进场景）。
    check(e10200 and e10200[1]['code'] == 0, '10200 的 code 必须是 0（该命令的例外约定）',
          'code=%s' % (e10200[1]['code'] if e10200 and e10200[1] else '?'))
    # ★ 配套回归（依据 analysis/protocol_flow.md 的 2026-10-01 更正 + 参考服实机注释）：
    #   `10102`/`10103` 的成功码与 `1110` 同族 = **1（TRUE）**，**只有 `10200` 是 `code==0` 的例外**。
    #   该断言防止"把 10200 的例外推广到 1010x"这类反向错误。
    c.send(10103, {'rid': rid, 'srv_id': '1'})
    f10103 = c.recv_all(0.5)
    r10103 = next((x for x in f10103 if x[0] == 10103), None)
    check(r10103 is not None and r10103[1]['code'] == 1,
          '10103 的 code 必须是 1（与 10200 的 0 相反）',
          'code=%s' % (r10103[1]['code'] if r10103 and r10103[1] else '?'))
    strict_ok(f10103, '10103')
    check(10201 in cmds, '10201 场景格子推送')
    e10201 = next((x for x in f if x[0] == 10201), None)
    check(e10201 and len(e10201[1]['roles']) == 1, '10201 roles=1')
    check(e10201 and len(e10201[1]['mons']) >= 1, '10201 至少 1 只怪（否则打不了怪）')
    strict_ok(f, '10102/10200/10201')
    mon_id = e10201[1]['mons'][0]['id'] if e10201 and e10201[1]['mons'] else 20001

    # ⑤ 客户端初始化完毕 → 角色四件套
    c.send(10300, {}, raw=b'')
    f = c.recv_all(0.6)
    cmds = [x[0] for x in f]
    for cmd in (10301, 10302, 10303, 10304):
        check(cmd in cmds, '%d 角色信息推送' % cmd)
    strict_ok(f, '10301-10304')

    # ⑥ 任务列表（链头）
    c.send(12400, {}, raw=b'')
    f = c.recv_all()
    r12400 = next((x for x in f if x[0] == 12400), None)
    check(r12400 is not None, '12400 有应答')
    mlist = r12400[1]['mission_list'] if r12400 and r12400[1] else []
    check(len(mlist) >= 1, '12400 至少下发 1 条任务（链头）')
    strict_ok(f, '12400')
    head = mlist[0]['mission_bid'] if mlist else None

    # ⑦ 接任务
    c.send(12402, {'mission_bid': head})
    f = c.recv_all(0.5)
    r12402 = next((x for x in f if x[0] == 12402), None)
    check(r12402 is not None and r12402[1]['code'] == 1, '12402 接取成功（code==1）',
          'code=%s' % (r12402[1]['code'] if r12402 and r12402[1] else '?'))
    strict_ok(f, '12402')

    # ⑧ 打怪 → 整条战斗链 + 击杀奖励（★ 改为 **APK 配置驱动**后的期望值）
    #    依据：`analysis/1.4.9/item/_config_drop.json` 里怪物 20001 =
    #      {"coin":"{1000}", "wood":"{500}", first/core/normal 全空}
    #    且 `drop_table.md:102` 明确把 20001 列为"三个掉落节全空（只有 coin/wood）"。
    #    ⇒ 期望：**coin +1000**、**不发任何物品**（此前发的占位物与 +30/+50 属编造数据，已移除）。
    before_bag = len(srv.store.bag(rid))
    role_before_kill = srv.store.role(rid)
    c.send(20002, {'mon_id': mon_id})
    f = c.recv_all(1.0)
    cmds = [x[0] for x in f]
    check(20002 in cmds, '20002 有应答')
    check(20010 in cmds, '20010 战斗初始化')
    e20010 = next((x for x in f if x[0] == 20010), None)
    check(e20010 and len(e20010[1]['fighter_info_list']) == 2, '20010 两名战斗单位')
    rounds = [x for x in f if x[0] == 20012]
    check(len(rounds) >= 1, '20012 至少 1 个回合')
    check(any(x[0] == 20013 for x in f), '20013 伤害帧')
    e20020 = next((x for x in f if x[0] == 20020), None)
    check(e20020 is not None and e20020[1]['result'] == 1, '20020 战斗结果=胜')
    check(any(x[0] == 20023 for x in f), '20023 结算帧')
    # ★ 按 APK 配置断言（不再断言"一定有掉落物"——20001 的真实配置就是无物品）
    role_after_kill = srv.store.role(rid)
    check(role_after_kill['coin'] - role_before_kill['coin'] == 1000,
          '★ 击杀 20001 的 coin 奖励 = APK 配置的 1000',
          'coin %s→%s' % (role_before_kill['coin'], role_after_kill['coin']))
    drops = [x for x in f if x[0] == 10500]
    after_bag = srv.store.bag(rid)
    check(len(after_bag) == before_bag,
          '★ 怪物 20001 按 APK 配置**无物品掉落** ⇒ 背包不新增',
          'before=%d after=%d' % (before_bag, len(after_bag)))
    check(not drops, '★ 无物品掉落时**不发** 10500 掉落推送（不编造）', '10500 帧数=%d' % len(drops))
    strict_ok(f, '20002/20010/20012/20013/20020/20023')

    # ⑨ 提交任务 → 奖励落库
    before = srv.store.role(rid)
    c.send(12403, {'mission_bid': head})
    f = c.recv_all(0.6)
    r12403 = next((x for x in f if x[0] == 12403), None)
    # ⑭ ★★ 与**参考服真机帧的字节长度奇偶校验**（goal 50 轮 · round 17）
    #   真机依据 `logs/1.4.9/task_chain_tcp.log:136-137`：
    #       << 12405 SC_12405 update_mission_list=7 (246 bytes)
    #       << 12406 SC_12406 del_mission_list=[10010] (12 bytes)
    #   本服编码若与之一致 ⇒ 结构（字段宽度/顺序/表项数编码）**逐字节级吻合**。
    _e6 = spec.encode_sc(12406, {'del_mission_list': [{'mission_bid': 10010}]})
    check(len(_e6) + 6 == 12, '★★ 12406（1 项）帧长 = 12 字节，与参考服真机帧**完全一致**',
          'mine=%d ref=12' % (len(_e6) + 6))
    _item = {'mission_bid': 10010, 'mission_status': 2, 'commit_num': 0, 'loop_count': 0,
             'loop_num': 1, 'code': 1, 'process_status': 0, 'target': 0, 'target_value': 0,
             'value': 0, 'show_lave_time': 0, 'lave_time': 0, 'accept_time': 0}
    _e5 = spec.encode_sc(12405, {'update_mission_list': [_item] * 7})
    check(len(_e5) + 6 == 246, '★★ 12405（7 项）帧长 = 246 字节，与参考服真机帧**完全一致**',
          'mine=%d ref=246' % (len(_e5) + 6))
    # 提交后应刷新角色/货币（参考服 :138-139 推 10302 + 10301/10303）
    for _cmd in (10301, 10303):
        check(any(x[0] == _cmd for x in f), '★ 提交后刷新 %d（参考服 :138-139 行为）' % _cmd,
              'cmds=%s' % [x[0] for x in f][:10])
    # ★ round 16：提交成功后必须**推** 12405（任务列表更新）+ 12406（任务移除）
    #   —— 依据参考服两次真机抓包（`logs/1.4.9/task_chain_tcp.log:136-137`、
    #   `battle_chain_tcp.log:633/663/709/866`），此前本服漏了，导致"已提交任务不消失"。
    check(any(x[0] == 12405 for x in f), '★ 提交成功后推 12405（update_mission_list）',
          'cmds=%s' % [x[0] for x in f][:8])
    e12406 = next((x for x in f if x[0] == 12406), None)
    check(e12406 is not None, '★ 提交成功后推 12406（del_mission_list）')
    if e12406:
        del_bids = [int(i['mission_bid']) for i in (e12406[1].get('del_mission_list') or [])]
        check(head in del_bids, '★ 12406 的 del_mission_list 含刚提交的任务 bid',
              'del=%s head=%s' % (del_bids, head))
    check(r12403 and r12403[1]['code'] == 1, '12403 提交成功（code==1）',
          'msg=%s' % (r12403[1]['msg'] if r12403 and r12403[1] else '?'))
    after = srv.store.role(rid)
    gained = {k: after[k] - before[k] for k in ('coin', 'gold', 'coupon', 'exp', 'hero_exp')}
    check(any(v > 0 for v in gained.values()), '任务奖励真的落到货币上', json.dumps(gained))
    check(any(x[0] == 10302 for x in f), '奖励后 10302 货币同步')
    strict_ok(f, '12403/10302')

    # ⑩ 背包查询能查到掉落（★ bag_code 语义已按 analysis/1.4.9/bag_code_mapping.md 修正：1=主背包）
    c.send(10502, {'bag_code': 1})
    f = c.recv_all(0.6)
    r10502 = next((x for x in f if x[0] == 10502), None)
    check(r10502 is not None, '10502 有应答')
    items = r10502[1]['items'] if r10502 and r10502[1] else []
    # ★ 修正（goal 50 轮 · round 7）：怪物 20001 按 APK 配置**无物品掉落** ⇒ 主背包**可以**是空的。
    #   改为断言"应答内容与本服 DB 真实一致"，而**不是**硬要求非空
    #   —— 不允许为了满足断言而制造假掉落。
    dbitems = srv.store.bag(rid)
    check(len(items) == len(dbitems), '10502 返回的物品数与本服 DB 真实一致',
          'resp=%d db=%d' % (len(items), len(dbitems)))
    check(not any(i['bid'] == M.DROP_ITEM_BID for i in items),
          '★ 背包里**不应**再出现已移除的占位掉落物 bid=%d' % M.DROP_ITEM_BID)
    strict_ok(f, '10502')

    # ⑩b ★ 回归断言（本轮新增，依据 analysis/1.4.9/bag_code_mapping.md）：
    #     客户端请求 bag_code=2（角色装备栏）时，**绝不能拿到主背包的物品**
    #     —— 那是本项目文档里明确记录过的 bug（"装备栏看不到装备"）。
    c.send(10502, {'bag_code': 2})
    f = c.recv_all(0.6)
    r2 = next((x for x in f if x[0] == 10502), None)
    check(r2 is not None and r2[1]['bag_code'] == 2, '10502 bag_code=2 回显正确')
    items2 = r2[1]['items'] if r2 and r2[1] else []
    check(not any(i['bid'] == M.DROP_ITEM_BID for i in items2),
          'bag_code=2（装备栏）不得返回主背包物品', 'items=%d' % len(items2))
    check(len(items2) == 0, 'bag_code=2 本服未实现内容 ⇒ 诚实回空', 'items=%d' % len(items2))
    strict_ok(f, '10502(bag_code=2)')

    # ⑩c ★ 回归断言（goal round 24）：任务 10020 的条件是 `fight_mon(20001)×1`
    #       —— 旧实现只认 dict 行 ⇒ 把它当"无条件"，一提交就成功（破坏回环语义）。
    #       现在必须：(a) 解析出 target=20001/need=1；(b) 未击杀前提交必须**被拒**。
    m10020 = srv.data.mission(10020)
    check(m10020 is not None, '配置里有任务 10020（真机客户端实际提交的那一条）')
    tgt20, need20 = M.Session.mission_target(m10020)
    check(tgt20 == 20001 and need20 == 1, '10020 的条件解析为 fight_mon(20001)×1',
          'target=%s need=%s' % (tgt20, need20))
    c.send(12402, {'mission_bid': 10020})
    c.recv_all(0.4)
    c.send(12403, {'mission_bid': 10020})
    f20 = c.recv_all(0.5)
    r20 = next((x for x in f20 if x[0] == 12403), None)
    check(r20 is not None and r20[1]['code'] == 0,
          '未击杀 20001 之前提交 10020 ⇒ 必须被拒（code=0）',
          'code=%s msg=%s' % (r20[1]['code'] if r20 and r20[1] else '?',
                              r20[1]['msg'] if r20 and r20[1] else '?'))

    # ⑩d ★★ 回环核心行为测试（goal round 25）：
    #   按**文档确证的条件**跑完整环：接取 10020 → 击杀怪物 20001 → 进度+1 → 提交 ⇒ 成功 + 奖励落库。
    #   奖励金额按 APK 配置断言（10020: award_assets=[[2,1290],[4,500],[15,500]]）
    #   —— 这是"最小回环可操作"的最强一条证据（不是结构断言，是行为断言）。
    c.send(12402, {'mission_bid': 10020})
    c.recv_all(0.4)
    c.send(20002, {'mon_id': 20001})
    fb = c.recv_all(1.0)
    check(any(x[0] == 20020 and x[1] and x[1]['result'] == 1 for x in fb),
          '打了条件怪 20001 ⇒ 战斗胜利（20020 result=1）')
    # ★ 测量窗口必须**只覆盖提交那一步**：击杀本身会给一份 `[TEST_ONLY]` 占位击杀奖励
    #   （`KILL_REWARD`，非 APK 配置），若把窗口开在击杀之前，就会把它算进任务奖励里
    #   —— 本轮首跑正是如此（实测 coin+1320/exp+550，多出的 +30/+50 就是占位击杀奖励）。
    before20 = srv.store.role(rid)
    c.send(12403, {'mission_bid': 10020})
    f20b = c.recv_all(0.6)
    r20b = next((x for x in f20b if x[0] == 12403), None)
    check(r20b is not None and r20b[1]['code'] == 1,
          '★ 击杀后提交 10020 ⇒ 成功（code=1，回环闭合）',
          'code=%s' % (r20b[1]['code'] if r20b and r20b[1] else '?'))
    after20 = srv.store.role(rid)
    got20 = {k: after20[k] - before20[k] for k in ('coin', 'exp', 'gold', 'coupon', 'hero_exp')}
    check(got20['coin'] == 1290 and got20['exp'] == 500 and got20['hero_exp'] == 500,
          '★ 10020 奖励与 APK 配置逐项相等（coin+1290 / exp+500 / hero_exp+500）',
          json.dumps(got20))
    strict_ok(f20b, '12403(10020 击杀后提交)')

    # ⑫ ★ 数据完整性：真实物品来源表 `server/item_gift.json`（goal 50 轮 · round 13）
    #   来源 = APK `assets/src/config/config_item_gift.luac`（由 `tools/extract_item_gift.py` 还原）；
    #   它给出"礼包 → [物品bid, 数量]"的真值，用于**不给占位物**也能验证 10500 进包环。
    #   本断言只做"表能用"的体检：非空 + 内容 bid 高比例命中本作物品表（少量小数字是货币/经验码）。
    _gift_path = os.path.join(os.path.dirname(os.path.abspath(M.__file__)), '..', '..', 'server', 'item_gift.json')
    _gift_path = os.path.normpath(_gift_path)
    if os.path.exists(_gift_path):
        with open(_gift_path, encoding='utf-8') as fh:
            gifts = json.load(fh)
        tot = sum(len(v) for v in gifts.values())
        items = srv.data.items if hasattr(srv.data, 'items') else None
        if items is None:
            with open(os.path.join(os.path.dirname(os.path.abspath(M.__file__)), '..', 'item_config.json'),
                      encoding='utf-8') as fh:
                items = json.load(fh)
        hit = sum(1 for v in gifts.values() for p in v if p and str(p[0]) in items)
        check(len(gifts) >= 400, '★ item_gift.json 条目数足够（真实物品来源表）', 'gifts=%d' % len(gifts))
        check(tot > 0 and hit / max(tot, 1) >= 0.90,
              '★ item_gift 内容 bid 高比例命中本作物品表（≥90%）',
              'hit=%d/%d=%.1f%%' % (hit, tot, 100.0 * hit / max(tot, 1)))
    else:
        check(False, '★ item_gift.json 存在（真实物品来源表）', _gift_path)

    # ⑬ ★★ 真值进包环（goal 50 轮 · round 14）：使用**真实礼包** `100`
    #   其内容来自 `server/item_gift.json`（`config_item_gift.luac` 还原），例如
    #   礼包 100 → [[21200,1],[21201,1],[21202,1],…] 全是真物品 bid。
    #   期望：10505 code=1；10500 推送的物品 **逐条等于**该礼包的真实内容；背包真的多出这些物品。
    gift100 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(M.__file__)),
                                          '..', 'item_gift.json'), encoding='utf-8'))['100']
    # ★ round 16：服务端已照参考服加过滤（`is_valid_item`）⇒ 期望值 = **内容里确实存在于物品表**的那些 bid
    real_bids = [int(p[0]) for p in gift100
                 if int(p[0]) not in M.ASSET_CODE and srv.data.item_ok(int(p[0]))]
    bag_before = len(srv.store.bag(rid))
    c.send(10505, {'code': 0, 'item_id': 100, 'use_num': 1, 'type': 0, 'bid': 100})
    # ★ 2026-10-16 修 flaky：原为 `recv_all(0.8)`（idle 取默认 0.15s）。
    #   `recv_all` 的口径是"收到过数据后，一出现 idle 空档就返回"；而开 229 件礼包
    #   要逐件落库 + 逐连接推 10500，帧间空档在机器有负载时**会超过 0.15s**
    #   ⇒ 10505 到了、10500 还没到就返回 ⇒ 后面 4 条断言连锁误报
    #   （实测同一份代码跑出 143/145、139/145 不等，改动前的老版本同样复现）。
    #   这里给重活路径一个足够宽的总窗口 + 空档，断言才可复现。
    fg = c.recv_all(3.0, 0.6)
    r10505 = next((x for x in fg if x[0] == 10505), None)
    check(r10505 is not None and r10505[1]['code'] == 1, '★ 使用真实礼包 100 ⇒ 10505 code=1',
          'code=%s msg=%s' % (r10505[1]['code'] if r10505 and r10505[1] else '?',
                              r10505[1]['msg'] if r10505 and r10505[1] else '?'))
    e10500 = [x for x in fg if x[0] == 10500]
    check(len(e10500) == 1, '★ 开礼包 ⇒ 恰好一次 10500 进包推送', '10500 帧数=%d' % len(e10500))
    pushed_bids = [int(i['bid']) for i in (e10500[0][1]['items'] if e10500 else [])]
    check(pushed_bids == real_bids,
          '★★ 10500 推送的物品 bid **逐条等于**礼包 100 的真实内容（不编造）',
          'pushed=%s real=%s' % (pushed_bids[:6], real_bids[:6]))
    check(len(srv.store.bag(rid)) == bag_before + len(set(real_bids)),
          '★ 背包真的多出礼包内容的物品（按**去重**后的 bid 数；重复 bid 会合并成一行）',
          'before=%d after=%d 期望+%d（内容 %d 条 / 去重 %d）'
          % (bag_before, len(srv.store.bag(rid)), len(set(real_bids)), len(real_bids), len(set(real_bids))))
    strict_ok(fg, '10505/10500/10302')
    # 反向：**礼包表里没有**的 bid ⇒ 必须诚实拒绝（不得编造产出）。
    # 注：不要拿小数字当反例——`item_gift.json` 里连 `bid=1` 都是真礼包（[[25218,1],…]），
    #     这正是本项目"资产码/物品 bid 撞号"陷阱的又一实例。
    c.send(10505, {'code': 0, 'item_id': 999999, 'use_num': 1, 'type': 0, 'bid': 999999})
    fn = c.recv_all(2.0, 0.5)     # ★ 同上：放宽空档，避免把上一条的迟到帧算进来
    rn = next((x for x in fn if x[0] == 10505), None)
    check(rn is not None and rn[1]['code'] == 0, '★ 无确证内容的 bid ⇒ 10505 诚实拒绝（code=0）',
          'code=%s' % (rn[1]['code'] if rn and rn[1] else '?'))

    # ⑬b ★ 含"货币/经验码"的礼包分支（goal 50 轮 · round 15）：
    #   `item_gift.json` 里 **352 / 496** 个礼包的内容含货币/经验码
    #   （按 `ASSET_CODE`：1=gold 2=coin 3=coupon 4=exp 15=hero_exp）。
    #   实证样例：`21900 → [[4,1]]`（经验）、`21901 → [[2,1]]`（银魂币/coin）。
    #   期望：对应货币/经验**真的增加**，且**绝不建物品行**（不能把货币码当物品塞进背包）。
    b_exp = srv.store.role(rid)
    bag_cur = len(srv.store.bag(rid))
    c.send(10505, {'code': 0, 'item_id': 21900, 'use_num': 1, 'type': 0, 'bid': 21900})
    fc = c.recv_all(2.0, 0.5)     # ★ 同上：重活路径放宽空档
    a_exp = srv.store.role(rid)
    check(a_exp['exp'] > b_exp['exp'], '★ 含货币码的礼包 21900（[[4,1]]=exp）⇒ 经验增加',
          'exp %s→%s' % (b_exp['exp'], a_exp['exp']))
    check(len(srv.store.bag(rid)) == bag_cur,
          '★ 货币码**不进背包**（不得把资产码当物品建行）',
          'bag %d→%d' % (bag_cur, len(srv.store.bag(rid))))
    c.send(10505, {'code': 0, 'item_id': 21901, 'use_num': 1, 'type': 0, 'bid': 21901})
    c.recv_all(2.0, 0.5)          # ★ 同上：重活路径放宽空档
    a_coin = srv.store.role(rid)
    check(a_coin['coin'] > a_exp['coin'], '★ 礼包 21901（[[2,1]]=coin）⇒ 银魂币增加',
          'coin %s→%s' % (a_exp['coin'], a_coin['coin']))
    strict_ok(fc, '10505(货币礼包 21900)')

    # ★★ round 16：**真正检验过滤器** —— 礼包 `100` 的 229 个物品码**全部合法**，
    #    所以上面那条断言其实**测不到**过滤。这里换一个内容里**确含非法 bid** 的礼包
    #    （`25920` 的内容含 `8`/`12`，不在本作物品表）⇒ 那些 bid **必须被跳过**、绝不进包。
    g25920 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(M.__file__)),
                                         '..', 'item_gift.json'), encoding='utf-8'))['25920']
    bad_bids = [int(p[0]) for p in g25920
                if int(p[0]) not in M.ASSET_CODE and not srv.data.item_ok(int(p[0]))]
    if bad_bids:
        c.send(10505, {'code': 0, 'item_id': 25920, 'use_num': 1, 'type': 0, 'bid': 25920})
        f25920 = c.recv_all(0.6)
        rr = next((x for x in f25920 if x[0] == 10505), None)
        check(rr is not None and rr[1]['code'] == 1, '★ 使用礼包 25920 ⇒ code=1',
              'code=%s' % (rr[1]['code'] if rr and rr[1] else '?'))
        pushed_bad = [int(i['bid']) for x in f25920 if x[0] == 10500
                      for i in x[1]['items'] if int(i['bid']) in bad_bids]
        check(not pushed_bad,
              '★★ 不在本作物品表的 bid **绝不进包、绝不推送**（照参考服 is_valid_item 过滤）',
              '非法 bid=%s 却出现在推送里=%s' % (bad_bids[:4], pushed_bad[:4]))
        strict_ok(f25920, '10505(含非法 bid 的礼包 25920)')

    # ⑮ ★ 10303 的 `attr` 表只发**参考服实测的两项**（goal 50 轮 · round 19）
    #   真机依据：`logs/1.4.9/battle_chain_tcp.log:63`
    #     `<< 10303 SC_10303 attr (hp_max=4321 atk_s=777) (192 bytes)`
    #   ⇒ 参考服只发 2 项；本服此前发 **24 项全占位**（帧 2233 字节）＝把 24 个编造数值当角色属性。
    c.send(10303, {})
    f3 = c.recv_all(0.5)
    e3 = next((x for x in f3 if x[0] == 10303), None)
    check(e3 is not None, '10303 有应答')
    if e3:
        _at = e3[1].get('attr')
        _n = len(_at) if hasattr(_at, '__len__') else 0
        # ★ 纠正（round 20）：`SC_10303.attr` 是**结构体表**，每个 item 含约 24 个字段（约 176 字节）
        #   ⇒ 正确形态是**只有一个结构体**（参考服摘要也只打印一个属性块 `attr (hp_max=… atk_s=…)`）。
        #   实测：0 项=109 字节 / 1 项=**197** / 2 项=285 / 24 项=2233 ⇒ 与之对应的参考服是 **192**。
        check(_n == 1, '★ 10303 的 attr 恰为 **1 个属性结构体**（实测帧 197 字节 ≈ 参考服 192）',
              'attr项数=%s' % _n)
    strict_ok(f3, '10303')

    # ⑯ ★ 移动覆盖（goal 50 轮 · round 23）：
    #   参考服日志里 `10204` 出现 **472 次**（最高频），说明客户端**大量**发移动；
    #   而本服虽已实现 `on_10204`，**selftest 此前从未覆盖它** ⇒ 属于"实现了但没测"的盲点。
    #   这里补上：坐标上行 + 落库 + 回发（ack 回显坐标）。
    _b4 = srv.store.role(rid)
    c.send(10204, {'rid': rid, 'srv_id': '1', 'x': 77, 'y': 88})
    f4 = c.recv_all(0.5)
    r204 = next((x for x in f4 if x[0] == 10204), None)
    check(r204 is not None, '★ 10204（移动）有应答（此前 selftest 完全没覆盖）')
    if r204:
        check(int(r204[1]['x']) == 77 and int(r204[1]['y']) == 88,
              '★ 10204 的应答回显了上报坐标（x=77,y=88）',
              'x=%s y=%s' % (r204[1].get('x'), r204[1].get('y')))
    _a4 = srv.store.role(rid)
    check(int(_a4['x']) == 77 and int(_a4['y']) == 88,
          '★ 移动坐标真的落库（DB 里 x=77,y=88）',
          'db x=%s y=%s' % (_a4['x'], _a4['y']))
    strict_ok(f4, '10204')

    # ⑰ ★ 高频命令**批量**覆盖（goal 50 轮 · round 24）
    #   来源：round 23 用参考服频度排序产出的"覆盖缺口表"（前 14 条）。
    #   规则（与本服设计一致）：**有 SC 定义 ⇒ 必须应答且严格合规格；无 SC（CS-only）⇒ 必须不应答**
    #   ——后者是项目红线（给 CS-only 回包会把客户端推进未知分支）。
    HIGH_FREQ = (10924, 16500, 11200, 11215, 10922, 10921, 17200, 13771,
                 15700, 11600, 15501, 16706, 10932, 18900)
    for _cmd in HIGH_FREQ:
        c.send(_cmd, {}, raw=b'')
        _fh = c.recv_all(0.3)
        _rh = next((x for x in _fh if x[0] == _cmd), None)
        if spec.has_sc(_cmd):
            check(_rh is not None, '★ 高频命令 %d 有应答（SC 已定义）' % _cmd)
            if _rh is not None:
                strict_ok(_fh, '高频 cmd=%d' % _cmd)
        else:
            check(_rh is None, '★ 高频命令 %d 为 CS-only ⇒ **必须不应答**（项目红线）' % _cmd,
                  '却收到了应答')

    # ⑱ ★ `10922`（活动列表）**故意保持"空但合法"**（goal 50 轮 · round 25）
    #   依据（两侧都指向"空表是可接受的"）：
    #     · `analysis/1.4.9/protocol_flow.md:108`：参考服对活动等子系统回"**空但合法**"的包；
    #     · `analysis/1.4.9/blank_dialog.md:227`：参考服 `10922` **只回 0 条活动**，
    #       客户端据此显示"该功能暂未开放" ⇒ **客户端接受空表**（已验证行为）。
    #   ★ 而本服**确实握有真实活动数据**：`server/_richang.json['tasks']`（**43 条**，
    #     含 id/name/max_num/desc_cond/…），`SC_10922.act_list` 的 item 形状是
    #     `{id:uint16, status:uint8, int_args:table}` —— **id 能对上**，
    #     但 **`status` 的语义 UNKNOWN**（0 是"未开放"还是"进行中"无据）。
    #   ⇒ 按纪律**不填**：填错了会把客户端推进未验证的状态（例如显示可点但实际没实现的活动）。
    c.send(10922, {}, raw=b'')
    f22 = c.recv_all(0.4)
    e22 = next((x for x in f22 if x[0] == 10922), None)
    check(e22 is not None, '10922 有应答')
    if e22 is not None:
        check((e22[1].get('act_list') or []) == [],
              '★ 10922 保持"空但合法"：status 语义 UNKNOWN ⇒ 不填真实活动（宁缺勿造）',
              'act_list=%s' % (e22[1].get('act_list'),))
    strict_ok(f22, '10922(空但合法)')

    # ⑲ ★ `12404`（放弃任务 giveUpHandler）—— 本服把它做成**真功能**（参考服当时是 no-op）
    #   依据：`analysis/1.4.9/mission_protocol_verify.md:20,91`（"当前不回包 = no-op"）、
    #        `mission_status.md:77`（12404 = 放弃任务）；字段形状取自 `protocol/fields.json`。
    c.send(12402, {'mission_bid': 10020})
    c.recv_all(0.4)
    _rows_before = len(srv.store.missions(rid))
    c.send(12404, {'mission_bid': 10020})
    f4b = c.recv_all(0.6)
    r404 = next((x for x in f4b if x[0] == 12404), None)
    check(r404 is not None and r404[1]['code'] == 1 and int(r404[1]['mission_bid']) == 10020,
          '★ 12404 放弃任务 ⇒ code=1 且回显 mission_bid（参考服是 no-op，本服做成真功能）',
          'code=%s bid=%s' % (r404[1]['code'] if r404 and r404[1] else '?',
                              r404[1]['mission_bid'] if r404 and r404[1] else '?'))
    check(len(srv.store.missions(rid)) == _rows_before - 1,
          '★ 放弃后任务行真的被删除', 'before=%d after=%d' % (_rows_before, len(srv.store.missions(rid))))
    _e12406 = next((x for x in f4b if x[0] == 12406), None)
    check(_e12406 is not None and
          any(int(i['mission_bid']) == 10020 for i in (_e12406[1].get('del_mission_list') or [])),
          '★ 放弃后推 12406（del_mission_list 含该 bid）')
    strict_ok(f4b, '12404/12406(放弃任务)')

    # ⑳ ★ `12414`（NPC 交任务）—— 与 `12403` 同义的那一步（goal 50 轮 · round 29）
    #   形状依据 `analysis/jstm_1.4.9/task_protocol.md:24` + `protocol/fields.json`；
    #   语义细节未确证 ⇒ 只做"已达条件 ⇒ 完成 + 发奖"，其余诚实拒绝。
    c.send(12402, {'mission_bid': 10020})          # 重新接取（前面已放弃）
    c.recv_all(0.4)
    c.send(20002, {'mon_id': 20001})               # 满足条件：击杀 20001
    c.recv_all(1.0)
    _r_before14 = srv.store.role(rid)
    c.send(12414, {'talk_bid': 0, 'mission_bid': 10020, 'npc_bid': 10030})
    f14 = c.recv_all(0.8)
    r1414 = next((x for x in f14 if x[0] == 12414), None)
    check(r1414 is not None and r1414[1]['code'] == 1 and int(r1414[1]['mission_bid']) == 10020,
          '★ 12414（NPC 交任务）达条件 ⇒ code=1 且回显 mission_bid',
          'code=%s' % (r1414[1]['code'] if r1414 and r1414[1] else '?'))
    _r_after14 = srv.store.role(rid)
    check(_r_after14['coin'] - _r_before14['coin'] == 1290,
          '★ 12414 完成后奖励按 APK 配置落库（coin+1290）',
          'coin %s→%s' % (_r_before14['coin'], _r_after14['coin']))
    # 反向：未接取的任务走 12414 ⇒ 必须诚实拒绝
    c.send(12414, {'talk_bid': 0, 'mission_bid': 10040, 'npc_bid': 10030})
    f14b = c.recv_all(0.4)
    r14b = next((x for x in f14b if x[0] == 12414), None)
    check(r14b is not None and r14b[1]['code'] == 0,
          '★ 12414 对"未接取"的任务诚实拒绝（code=0）',
          'code=%s' % (r14b[1]['code'] if r14b and r14b[1] else '?'))
    strict_ok(f14 + f14b, '12414')

    # ㉑ ★ `12415`（交物品完成任务）—— goal 50 轮 · round 30
    #   形状依据 `analysis/jstm_1.4.9/task_protocol.md:25` + `protocol/fields.json`。
    #   纪律：**物品不足 ⇒ 必须诚实拒绝**（不凭空完成、不部分扣减）。
    #   用**真物品**：先走已验证的礼包路径拿到真实物品，再用它去交。
    c.send(10505, {'code': 0, 'item_id': 100, 'use_num': 1, 'type': 0, 'bid': 100})
    c.recv_all(0.8)
    _bag100 = srv.store.bag(rid)
    _real = next((b for b in _bag100 if int(b['bid']) == 21200), None)
    check(_real is not None, '★ 先经礼包路径取得真物品 21200（用于交物品测试）')
    if _real:
        c.send(12402, {'mission_bid': 10020})
        c.recv_all(0.4)
        _q_before = int(_real['quantity'])
        c.send(12415, {'mission_bid': 10020, 'item_bid': 21200, 'item_num': 1})
        f15 = c.recv_all(0.8)
        r1515 = next((x for x in f15 if x[0] == 12415), None)
        check(r1515 is not None and r1515[1]['code'] == 1,
              '★ 12415 交物品（背包确有该物品）⇒ code=1',
              'code=%s msg=%s' % (r1515[1]['code'] if r1515 and r1515[1] else '?',
                                  r1515[1]['msg'] if r1515 and r1515[1] else '?'))
        _now = next((b for b in srv.store.bag(rid) if int(b['bid']) == 21200), None)
        _q_after = int(_now['quantity']) if _now else 0
        check(_q_after == _q_before - 1, '★ 交物品后**背包真的扣减** 1 个（不编造库存）',
              'qty %d→%d' % (_q_before, _q_after))
        strict_ok(f15, '12415')
    # 反向：物品不足 ⇒ 诚实拒绝
    c.send(12402, {'mission_bid': 10020})
    c.recv_all(0.4)
    c.send(12415, {'mission_bid': 10020, 'item_bid': 999999, 'item_num': 5})
    f15b = c.recv_all(0.5)
    r15b = next((x for x in f15b if x[0] == 12415), None)
    check(r15b is not None and r15b[1]['code'] == 0,
          '★ 12415 物品不足 ⇒ 诚实拒绝（code=0，不凭空完成）',
          'code=%s' % (r15b[1]['code'] if r15b and r15b[1] else '?'))
    strict_ok(f15b, '12415(拒绝)')

    # ㉒ ★★ 修复"无法进图"：`10103`（角色重连）必须与 `10102` 一样**推场景数据**（goal round 33）
    #   依据：参考服实机注释——`10102`/`10103` SC 同构、都走 `code==TRUE` 成功分支并 fire `LOGIN_SUCCESS`，
    #   而 `scene_controller` 把 `LOGIN_SUCCESS` 绑到**进场景**。
    #   此前 `10103` 不在 LOOP ⇒ 只回通用应答、**不推 10200/10201** ⇒ 客户端重连时"进了场景却无场景数据"。
    c.send(10103, {'rid': rid, 'srv_id': '1'})
    f103 = c.recv_all(0.8)
    r103 = next((x for x in f103 if x[0] == 10103), None)
    check(r103 is not None and r103[1]['code'] == 1, '★ 10103 有应答且 code=1',
          'code=%s' % (r103[1]['code'] if r103 and r103[1] else '?'))
    check(any(x[0] == 10200 for x in f103), '★★ 10103 后必须推 10200（进场景）—— 此前漏推 ⇒ 无法进图',
          'cmds=%s' % [x[0] for x in f103][:6])
    _e21 = next((x for x in f103 if x[0] == 10201), None)
    check(_e21 is not None and len(_e21[1]['roles']) == 1 and len(_e21[1]['npcs']) >= 1,
          '★★ 10103 后必须推 10201（场景格子，含角色与 NPC）—— 此前漏推 ⇒ 无法进图',
          'npcs=%s' % (len(_e21[1]['npcs']) if _e21 else '?'))
    strict_ok(f103, '10103/10200/10201')

    # ㉓ ★ 创建角色（10101）—— goal round 78
    #   规格：CS sex,name,career,playform ／ SC code,msg,rid,srv_id；1110 的 least_career 是"剩余可选职业"位掩码
    _name = "自建角色A"
    c.send(10101, {'sex': 0, 'name': _name, 'career': 3, 'playform': 'android'})
    f_c = c.recv_all(0.6)
    r_c = next((x for x in f_c if x[0] == 10101), None)
    check(r_c is not None and r_c[1]["code"] == 0 and int(r_c[1]["rid"]) > 1000,
          "★ 10101 创建角色成功（**code=0** —— 反汇编确证该命令的例外约定）",
          "code=%s rid=%s" % (r_c[1]["code"] if r_c and r_c[1] else "?",
                              r_c[1]["rid"] if r_c and r_c[1] else "?"))
    _newrid = int(r_c[1]["rid"]) if r_c and r_c[1] else 0
    _e1110 = next((x for x in f_c if x[0] == 1110), None)
    check(_e1110 is not None and any(int(i["rid"]) == _newrid for i in _e1110[1]["roles"]),
          "★ 建角后立刻重推 1110，且列表里能看到新角色")
    check(_e1110 is not None and (_e1110[1]["least_career"] & (1 << 2)) == 0,
          "★ least_career 清掉了已被占用的职业位（career=3 ⇒ bit2=0）",
          "least_career=0x%02x" % (_e1110[1]["least_career"] if _e1110 else -1))
    # 新角色可以直接登录
    c.send(10102, {"rid": _newrid, "srv_id": "1"})
    f_l = c.recv_all(0.8)
    check(any(x[0] == 10200 for x in f_l), "★ 新建的角色可以直接登录进场景（10102 → 10200）")
    # 反向：重名 / 非法职业 ⇒ 诚实拒绝
    c.send(10101, {"sex": 0, "name": _name, "career": 4, "playform": "android"})
    f_d = c.recv_all(0.4)
    r_d = next((x for x in f_d if x[0] == 10101), None)
    check(r_d is not None and r_d[1]["code"] != 0, "★ 重名建角 ⇒ 诚实拒绝（code≠0 并带 msg）",
          "code=%s" % (r_d[1]["code"] if r_d and r_d[1] else "?"))
    c.send(10101, {"sex": 0, "name": "自建角色B", "career": 99, "playform": "android"})
    f_e = c.recv_all(0.4)
    r_e = next((x for x in f_e if x[0] == 10101), None)
    check(r_e is not None and r_e[1]["code"] != 0, "★ 非法职业建角 ⇒ 诚实拒绝（code≠0）")
    strict_ok(f_c, "10101/1110(建角)")

    # ⑪ 回环外命令：有 SC ⇒ 结构正确的通用应答；无 SC ⇒ 不回包
    generic = next((cmd for cmd in spec.sc
                    if cmd not in M.Session.LOOP and 10000 <= cmd <= 14000), None)
    c.send(generic, {}, raw=b'')
    f = c.recv_all(0.4)
    g = next((x for x in f if x[0] == generic), None)
    check(g is not None and g[2], '回环外命令走通用应答且严格合规格 cmd=%d' % generic)
    c.close()

    print('\n──────── 结果 ────────')
    print('检查项 %d，通过 %d，失败 %d' % (len(CHECKS), len(CHECKS) - len(FAILS), len(FAILS)))
    if FAILS:
        print('失败清单：')
        for x in FAILS:
            print('  - ' + x)
    print('DB 落盘：%s（保留供查看）' % db)
    sys.stdout.flush()
    # 服务端线程是 daemon 的；解释器退出时可能撞上 stdout 锁。
    # 直接 os._exit 收尾，避免那次无害但难看的 shutdown 竞态。
    os._exit(1 if FAILS else 0)


if __name__ == '__main__':
    sys.exit(main())
