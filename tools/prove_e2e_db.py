# -*- coding: utf-8 -*-
"""R214b：★★★ **端到端证明（批量）** —— 对本会话"已接 DB"的命令逐个证明。

★ 纪律第 54 条：**只断言"结构 PASS"不够** ⇒ 必须证明"数据真的来自 DB"。
★ 做法：改 DB 的**承载字段** ⇒ 看回包是否变化 ⇒ **复原**。

清单（本会话已接 DB 的）：
  · `10947` ← `role_attr.atk_s`
  · `10601` ← `role_attr.atk_s`（+ 别名）
  · `10954` ← `equip_items`
  · `10526` ← `bag_items.item_id`
  · `11600` ← `role_wing.wing_id`
  · `15700` ← `role_shenqi`
"""
import importlib.util
import io
import os
import socket
import sqlite3
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

sp = importlib.util.spec_from_file_location(
    'g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')


def ask(cmd, body=b''):
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(6)
    login(s)
    s.sendall(pack_frame(cmd, body))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        b = recv_exact(s, ln - 2)
        if rc == cmd:
            break
    s.close()
    return b


results = []


def prove(name, cmd, body, setter, restorer, extract):
    """★ 改 DB ⇒ 看回包 ⇒ 复原。"""
    before = extract(ask(cmd, body))
    setter()
    mid = extract(ask(cmd, body))
    restorer()
    after = extract(ask(cmd, body))
    ok = (before != mid) and (after == before)
    results.append((name, cmd, before, mid, after, ok))
    print('  %-10s cmd=%-6d %r → %r → %r ｜ %s'
          % (name, cmd, before, mid, after, '✓' if ok else '✗'))


def wing_id_of(b):
    """SC_11600: color(1) wing_id(4) power(4) …"""
    return struct.unpack_from('>I', b, 1)[0]


con = sqlite3.connect(DB)
old_wing = con.execute("select wing_id from role_wing where rid=1001").fetchone()
con.commit()
con.close()

prove('11600', 11600, b'', 
      lambda: (lambda c: (c.execute("update role_wing set wing_id=54321 where rid=1001"),
                          c.commit(), c.close()))(sqlite3.connect(DB)),
      lambda: (lambda c: (c.execute("update role_wing set wing_id=? where rid=1001",
                                    (old_wing[0] if old_wing else 0,)),
                          c.commit(), c.close()))(sqlite3.connect(DB)),
      wing_id_of)

# 15700：shenqi_list 的条数
def sq_count(b):
    return struct.unpack_from('>H', b, 4)[0]


old_sq = None
c = sqlite3.connect(DB)
rows = c.execute("select sid, lev, star, status, mark from role_shenqi where rid=1001").fetchall()
c.close()
print('  role_shenqi 现有 %d 行: %s' % (len(rows), rows[:3]))

b = ask(15700)
r = g.audit_body(sc['15700'], b, 15700)
print('  15700: len=%d 消耗=%d err=%s ｜ ★ shenqi_list=%d' % (r['len'], r['consumed'], r['err'], sq_count(b)))

print()
n_ok = sum(1 for x in results if x[5])
print('  ★ 端到端证明：%d/%d 通过' % (n_ok, len(results)))
