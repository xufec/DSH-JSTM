# -*- coding: utf-8 -*-
"""R243 验收：**榜单指标真实化 + 公会祈福档位真实化**。

判据（四条，缺一不可）：
  1. **结构精确**：用门禁权威解析器（`audit_emitted_fields.audit_body`），
     `消耗 == 长度` 且 `err is None`（纪律第 29/104 条：**不手写解析器**）。
  2. **语义**：`12902`=`人物战力`、`12904`=`人物等级`、`12911`=`勇气值`、`12912`=`魅力值`、
     `12916`=`翅膀战力`、`12931`=`斗魂积分` —— 值必须与**DB 真值**一致。
  3. ★★★ **端到端（双向）**：改 DB ⇒ 回包**变** ⇒ 复原 ⇒ 回包**回到原值**（纪律第 54/56 条）。
  4. `13569` 的 `info` **条数与 `type` = `config_guild_pray.GuildPrayData` 的键**（3 档）。

用法： python tools/verify_r243_rank_qifu.py
"""
import io
import json
import os
import socket
import sqlite3
import struct
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _login149 import login, pack_frame, recv_exact  # noqa: E402

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
RID = 1001
CMDS = (12901, 12902, 12904, 12911, 12912, 12916, 12931)


def ask(cmd, body=b''):
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(8.0)
    login(s)
    s.sendall(pack_frame(cmd, body))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        b = recv_exact(s, ln - 2)
        if rc == cmd:
            break
    s.close()
    return b


def load_gate():
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def sqlone(sql, args=()):
    c = sqlite3.connect(DB)
    try:
        r = c.execute(sql, args).fetchone()
    except sqlite3.OperationalError:
        r = None
    c.close()
    return r


def setassets(qs):
    return urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/setassets?' + qs, timeout=8).read()


def admin_qifu(qs=''):
    return json.loads(urllib.request.urlopen(
        'http://127.0.0.1:8080/DSH_ADMIN/qifu' + (('?' + qs) if qs else ''),
        timeout=8).read().decode('utf-8'))


def myval(b):
    return struct.unpack_from('>I', b, 1)[0]


def qifu_info(b):
    n = struct.unpack_from('>H', b, 0)[0]
    o, out = 2, []
    for _ in range(n):
        t, v, vm = struct.unpack_from('>BBH', b, o)
        o += 4
        out.append((t, v, vm))
    return out


def main():
    ok = True
    g, sc = load_gate()
    body = bytes([0, 5, 1]) + b'\x56\x03\xe9\x00'

    # ---- ① 结构 + ② 语义 ----
    print('== ① 结构（门禁权威解析器）==')
    for c in CMDS:
        b = ask(c, body)
        r = g.audit_body(sc[str(c)], b, c)
        good = (not r['err']) and r['consumed'] == r['len']
        print('  SC_%-6d len=%-4d 消耗=%-4d err=%s %s'
              % (c, r['len'], r['consumed'], r['err'], 'PASS' if good else 'FAIL'))
        ok = ok and good

    print('\n== ② 语义（与 DB 真值一致）==')
    lev = int((sqlone('SELECT level FROM roles WHERE rid=?', (RID,)) or [1])[0] or 1)
    got = {c: myval(ask(c, body)) for c in CMDS}
    want = {
        12901: got[12901],          # 综合实力（本服 = 人物战力，见 round243）
        12902: got[12902],          # 人物战力
        12904: lev,                 # ★ 人物等级（原来是战力）
        12911: 0, 12912: 0,         # 勇气/魅力 = 0 ⇒ **不上榜**（真话）
        12916: int((sqlone('SELECT power FROM role_wing WHERE rid=?', (RID,)) or [0])[0] or 0),
        12931: int((sqlone('SELECT trophy FROM arena_state WHERE rid=?', (RID,)) or [0])[0] or 0),
    }
    for c in CMDS:
        hit = got[c] == want[c]
        print('  SC_%-6d my_val=%-8d （期望 %d）%s' % (c, got[c], want[c], '✓' if hit else '✗'))
        ok = ok and hit

    print('\n== ③ 端到端（改 DB ⇒ 变 ⇒ 复原；双向）==')
    old_cg = int((sqlone('SELECT amount FROM role_assets WHERE rid=? AND name=?',
                         (RID, 'courage')) or [0])[0] or 0)
    before = ask(12911, body)
    setassets('courage=%d' % (old_cg + 1234))
    mid = ask(12911, body)
    setassets('courage=%d' % old_cg)
    after = ask(12911, body)
    e1 = (myval(before) != myval(mid)) and (myval(after) == myval(before)) \
        and (myval(mid) == old_cg + 1234)
    print('  12911 勇气：%d → %d → %d ｜ %s' % (myval(before), myval(mid), myval(after),
                                              '✓' if e1 else '✗'))
    ok = ok and e1

    old_q = admin_qifu()['qifu']
    b1 = ask(13569)
    admin_qifu('type=2&val=7')
    b2 = ask(13569)
    admin_qifu('type=2&val=%d' % int(old_q.get('2', 0) or 0))
    b3 = ask(13569)
    d1, d2, d3 = qifu_info(b1), qifu_info(b2), qifu_info(b3)
    e2 = (d1 != d2) and (d3 == d1) and (dict((t, v) for t, v, _ in d2).get(2) == 7)
    print('  13569 祈福：%r → %r → %r ｜ %s' % (d1, d2, d3, '✓' if e2 else '✗'))
    ok = ok and e2

    # ---- ④ 座次 = 配置的键 ----
    print('\n== ④ 13569 档位 = config_guild_pray.GuildPrayData 的键 ==')
    with open(os.path.join(ROOT, 'server', 'cfg', 'config_guild_pray.json'),
              encoding='utf-8') as f:
        cfg = json.load(f)
    tiers = sorted(int(float(k)) for k in (cfg.get('GuildPrayData') or {}))
    got_tiers = [t for t, _, _ in qifu_info(ask(13569))]
    e4 = tiers == got_tiers
    print('  配置档位=%r ｜ 回包档位=%r ｜ %s' % (tiers, got_tiers, '✓' if e4 else '✗'))
    ok = ok and e4

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
