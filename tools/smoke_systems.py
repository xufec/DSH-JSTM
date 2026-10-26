# -*- coding: utf-8 -*-
"""系统冒烟：把"协议里有 CS、服务端也处理了、但客户端从没发过"的命令**逐条打一遍**。

为什么（2026-10-17 深挖）：
  `tools/audit_system_coverage.py` 显示四个系统的协议命令**全部**有活代码处理，
  但客户端历史日志里只跑过其中少数（伙伴 3/26、背包 6/61、战斗 4/19、魂技 4/10）。
  剩下那些从没被触发过的分支就是**覆盖空白**——最可能藏着解析/空值/索引类崩溃。

判据（每条命令）：
  · **无回包**            → 记 FAIL（客户端会干等）
  · 服务端日志出现 `!! cmd=N 处理异常` → 记 FAIL（handler 抛异常，已被逐条兜住）
  · 有回包但首字节是 code=0 → 记 REJECT（合法拒绝，算通过，仅记录）
  · 有回包 code=1/无 code 字段 → 记 OK

安全：临时建号（`smoke_<ts>`）→ 打完 → **删号 + 删关联行**。所有副作用都落在这个临时角色上。

用法：
    python tools/smoke_systems.py                 # 全部未测命令
    python tools/smoke_systems.py 11200 10500 20000 10600   # 指定区间
    python tools/smoke_systems.py --limit 20      # 每系统最多打 N 条
"""
import argparse
import collections
import glob
import os
import re
import socket
import sqlite3
import struct
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'server'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
HOST, PORT = '127.0.0.1', 9000
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')

UID = 'smoke_%d' % int(time.time())
PWD = 'smoke123456'


def frame(cmd, body=b''):
    return struct.pack('>IH', len(body) + 2, cmd) + body


def tlv(**kv):
    b = struct.pack('>H', len(kv))
    for k, v in kv.items():
        v = str(v).encode()
        b += struct.pack('>H', len(k)) + k.encode() + struct.pack('>H', len(v)) + v
    return b


class Conn:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=8)
        self.s.settimeout(0.3)
        self.buf = b''

    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))

    def drain(self, seconds):
        out, end = [], time.time() + seconds
        while time.time() < end:
            try:
                d = self.s.recv(65536)
            except socket.timeout:
                continue
            except Exception:
                break
            if not d:
                break
            self.buf += d
            while len(self.buf) >= 6:
                ln = struct.unpack_from('>I', self.buf, 0)[0]
                if len(self.buf) < 4 + ln:
                    break
                c = struct.unpack_from('>H', self.buf, 4)[0]
                out.append((c, self.buf[6:4 + ln]))
                self.buf = self.buf[4 + ln:]
        return out


def log_err_counts():
    """tcp.log 里 `!! cmd=N 处理异常` 的计数（逐条兜住后的显形点）。"""
    c = collections.Counter()
    try:
        for line in open(LOG, encoding='utf-8', errors='replace'):
            m = re.search(r'!! cmd=(\d+) 处理异常', line)
            if m:
                c[int(m.group(1))] += 1
    except FileNotFoundError:
        pass
    return c


def untested(bounds):
    """复用覆盖矩阵的逻辑：协议 CS ∩ 活代码处理 − 客户端发过。"""
    from audit_system_coverage import live_handlers, sent_counts
    import json
    raw = json.load(open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8'))
    cs = set()
    for k, v in raw.items():
        try:
            c = int(v.get('cmd'))
        except Exception:
            continue
        if (v.get('dir') or '') == 'cs':
            cs.add(c)
    live, _ = live_handlers()
    sent = sent_counts()
    out = {}
    for name, (lo, hi) in bounds.items():
        out[name] = sorted(c for c in cs if lo <= c <= hi and c in live and not sent.get(c))
    return out


def guess_body(cmd):
    """给一条"监听型"最小 body：全 0（字段多为数值）+ 少量 1（计数类）。

    这不是"编造协议"，只是**喂一个有长度的帧**让解析路径跑起来；
    真正的语义校验由 verify_systems.py 负责。
    """
    return b'\x00' * 8


def has_sc(cmd):
    """协议里有没有 SC 定义 —— 决定"沉默"算不算问题。"""
    try:
        from protocol.fields import has_sc_definition
        return bool(has_sc_definition(cmd))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmds', nargs='*', type=int)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--wait', type=float, default=0.8)
    a = ap.parse_args()

    if a.cmds:
        bounds = {('%d-' % c): (c, c + 99) for c in a.cmds}
    else:
        bounds = {'伙伴 112xx': (11200, 11299), '背包 105xx': (10500, 10599),
                  '战斗 200xx': (20000, 20099), '魂技 106xx': (10600, 10699)}
    plan = untested(bounds)
    total = sum(len(v) for v in plan.values())
    print('== 未测命令（协议有 CS + 活代码处理 + 客户端从没发过）: %d 条 ==' % total)

    c = Conn()
    c.send(1110, tlv(account=UID, token=PWD, enter_srv_id='1'))
    c.drain(1.5)
    con = sqlite3.connect(DB, timeout=10)
    row = con.execute('SELECT rid FROM roles WHERE uid=?', (UID,)).fetchone()
    con.close()
    if not row:
        nm = UID[-8:]
        c.send(10101, struct.pack('>B', 1) + struct.pack('>B', len(nm)) + nm.encode()
               + struct.pack('>B', 1) + struct.pack('>H', 1001))
        c.drain(1.5)
        con = sqlite3.connect(DB, timeout=10)
        row = con.execute('SELECT rid FROM roles WHERE uid=?', (UID,)).fetchone()
        con.close()
    if not row:
        print('!! 建号失败，退出'); return 2
    rid = int(row[0])
    c.send(10102, struct.pack('>I', rid) + struct.pack('>B', 1))
    c.drain(2.0)
    print('== 临时号 %s ｜ rid=%d ==' % (UID, rid))

    errs_before = log_err_counts()
    results = {}
    for name, cmds in plan.items():
        if a.limit:
            cmds = cmds[:a.limit]
        print('\n-- %s（%d 条）--' % (name, len(cmds)))
        for cmd in cmds:
            c.send(cmd, guess_body(cmd))
            got = c.drain(a.wait)
            mine = [b for cc, b in got if cc == cmd]
            if mine:
                b0 = mine[0]
                head = 'code=%d' % b0[0] if b0 and b0[0] in (0, 1) else '首字节=%s' % (b0[:4].hex(' ') or '空')
                kind = 'REJECT' if (b0 and b0[0] == 0) else 'OK'
                results[cmd] = kind
                print('  %-6d 回包 ✔ %-6s %4d 字节  %s' % (cmd, kind, len(b0), head))
            else:
                # ★ 2026-10-17：沉默要分两种 —— 协议里**没有 SC 定义**的消息本来就是
                #   "上报型/通知型"（如 20011 客户端加载完成、20014 动画播完），
                #   服务端不回包是**正确**行为；只有**有 SC 定义却沉默**才是缺陷。
                sc = has_sc(cmd)
                if sc is False:
                    results[cmd] = 'SILENT_OK'
                    print('  %-6d 无回包（协议无 SC ⇒ 通知型，沉默正确）' % cmd)
                else:
                    results[cmd] = 'SILENT'
                    print('  %-6d **无回包**（协议有 SC 定义 ⇒ 客户端会干等！期间其它帧: %s）'
                          % (cmd, sorted(set(cc for cc, _ in got)) or '无'))
    errs_after = log_err_counts()
    raised = {k: errs_after[k] - errs_before.get(k, 0) for k in errs_after
              if errs_after[k] - errs_before.get(k, 0) > 0}
    if raised:
        print('\n== handler 抛异常（已逐条兜住，但要修）==')
        for k, v in sorted(raised.items()):
            print('  cmd=%-6d ×%d' % (k, v))
            results[k] = 'EXCEPTION'

    # 清理
    try:
        con = sqlite3.connect(DB, timeout=10)
        rids = [int(r[0]) for r in con.execute('SELECT rid FROM roles WHERE uid=?', (UID,))]
        for t in ('roles', 'role_attr', 'role_assets', 'missions', 'bag_items', 'equip_items',
                  'store_items', 'role_heros', 'role_buffs', 'role_skills', 'dungeon_progress',
                  'chengjiu_progress'):
            for r in rids:
                try:
                    con.execute('DELETE FROM %s WHERE rid=?' % t, (r,))
                except Exception:
                    pass
        con.execute('DELETE FROM accounts WHERE uid=?', (UID,))
        con.commit(); con.close()
        print('\n== 清理完成（%d 个角色行）==' % len(rids))
    except Exception as e:
        print('!! 清理失败: %r' % (e,))

    cnt = collections.Counter(results.values())
    print('\n===== 冒烟汇总 =====')
    print('  %s ｜ 共 %d 条' % (dict(cnt), len(results)))
    for k in ('SILENT', 'EXCEPTION'):
        bad = [c for c, v in results.items() if v == k]
        if bad:
            print('  ⚠ %s: %s' % (k, bad))
    return 1 if cnt['SILENT'] or cnt['EXCEPTION'] else 0


if __name__ == '__main__':
    sys.exit(main())
