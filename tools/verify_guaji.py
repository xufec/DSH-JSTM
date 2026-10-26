# -*- coding: utf-8 -*-
"""R53 验证：挂机链 `15402`（任务→地图/坐标）+ `15403`（杀怪上报）+ `15404`（轮次结束推送）。

核对五件事：
  1. `SC_15402` 按规格**精确解析**，且 `mission_bid` 回显、`map_bid` 取自 `config_guaji`；
  2. `15402` 会把 `mission_bid` 记进 `guaji_state`（供 15403/15404 用）；
  3. `15403` **只接受真实的挂机怪**（`config_guaji` 的 8 条）⇒ code=1；未知 mon ⇒ **code=0**；
  4. `15403` 合法时 `kill_count` **真的 +1 落库**；
  5. `/DSH_ADMIN/guaji_end` 能推 `15404{mission_bid}`（推送型，规格精确解析）。

★ 跑完**恢复** `guaji_state`（玩家行原样还原），不留副作用。
用法：python tools/verify_guaji.py
"""
import json
import os
import socket
import sqlite3
import struct
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_conformance import parse_full  # noqa: E402
from audit_sc_live import pack_frame, recv_exact  # noqa: E402

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
    FIELDS = json.load(f)
with open(os.path.join(ROOT, 'server', '_guaji.json'), encoding='utf-8') as f:
    GUAJI = json.load(f)['spots']

PLAYER_RID = 1001
TEST_MISSION = 10010          # ★ R48 已取证：客户端在登录进场景后主动发 CS_15402{mission_bid=10010}
BAD_MON = 999999


def sc_spec(cmd):
    for k, v in FIELDS.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def login(s):
    _args = struct.pack('>H', 10)
    for _k, _v in (('account', 'dsh_local'), ('channelId', '1'),
                   ('device_id', 'dsh-probe'), ('enter_srv_id', '1'),
                   ('gettui_cid', ''), ('idfa', ''), ('platform', 'ewan'),
                   ('sign', ''), ('timestamp', '0'), ('token', '')):
        _kb = _k.encode(); _vb = _v.encode()
        _args += struct.pack('>H', len(_kb)) + _kb + struct.pack('>H', len(_vb)) + _vb
    s.sendall(pack_frame(1110, _args))
    rid = None
    while True:
        hdr = recv_exact(s, 6)
        ln, rc = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]
            off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]
            off += 2
            rid = struct.unpack_from('>I', p, off)[0] if cnt else None
            break
    if rid:
        s.sendall(pack_frame(10102, struct.pack('>I', rid) + w_str('1')))
        s.settimeout(2.0)
        try:
            while True:
                hdr = recv_exact(s, 6)
                ln, rc = struct.unpack('>IH', hdr)
                recv_exact(s, ln - 2)
                if rc == 10102:
                    break
        except socket.timeout:
            pass
        s.settimeout(5.0)
    return rid


def q(s, cmd, body=b'', want=None):
    """发 CS 收对应 SC（顺带把途中收到的推送收集起来）。"""
    s.sendall(pack_frame(cmd, body))
    while True:
        hdr = recv_exact(s, 6)
        ln, rc = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == cmd:
            return p


def db_state(rid):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT * FROM guaji_state WHERE rid=?', (rid,)).fetchone()
    d = dict(r) if r else None
    con.close()
    return d


ok = True
orig = db_state(PLAYER_RID)
print('原 guaji_state =', orig)

s = socket.create_connection(('127.0.0.1', 9000), 5)
s.settimeout(5.0)
rid = login(s)
print('login rid =', rid)

# ---- 15405（轮次查询）+ 15400（启动挂机）----
# 这两条是链路的最前面两环；一起纳入，保证"客户端一旦点到 4019 按钮"下游全部已验证。
body = q(s, 15405)
used, errs, unv = parse_full(body, sc_spec(15405))
lc = struct.unpack_from('>H', body, 0)[0]
print('\n== 15405（轮次查询，客户端打开 NPC 对话框时由 requestHuan() 发出）==')
print('  len=%d 消耗=%d errs=%s loop_count=%d  PASS=%s'
      % (len(body), used, errs, lc, used == len(body) and not errs))
if used != len(body) or errs:
    ok = False

body = q(s, 15400)
used, errs, unv = parse_full(body, sc_spec(15400))
n = struct.unpack_from('>H', body, 1)[0]
msg = body[3:3 + n].decode('utf-8', 'replace')
print('\n== 15400（启动挂机 / 由 funBtnHandler 在 btn.id==4019 时触发）==')
print('  len=%d 消耗=%d errs=%s code=%d msg=%r  PASS=%s'
      % (len(body), used, errs, body[0], msg, used == len(body) and not errs))
if body[0] != 1 or used != len(body) or errs:
    ok = False

# ---- 15402 ----
body = q(s, 15402, struct.pack('>I', TEST_MISSION))
used, errs, unv = parse_full(body, sc_spec(15402))
mb, mbid, x, y = struct.unpack_from('>IIII', body, 0)
print('\n== 15402 ==')
print('  len=%d 消耗=%d errs=%s  PASS=%s' % (len(body), used, errs,
      used == len(body) and not errs))
print('  mission_bid=%d map_bid=%d (%d,%d)' % (mb, mbid, x, y))

# ★ 期望值不能写死：挂机点由**角色等级段**决定；等级落在所有段之外时，
#   服务端应老实回 map_bid=0（而不是硬塞一个点）。这里按同一规则算期望。
lev_now = json.loads(urllib.request.urlopen(
    'http://127.0.0.1:8080/DSH_ADMIN/status').read())['role']['level']
exp_spot = next((g for g in GUAJI
                 if int(g['lev_l']) <= int(lev_now) <= int(g['lev_r'])), None)
print('  角色等级=%s ⇒ 期望挂机点=%s' % (lev_now, exp_spot or '无（等级段之外）'))
if exp_spot is None:
    print('  等级段之外 ⇒ 期望 map_bid=0: %s' % ('是' if mbid == 0 else '否 ← 不应硬塞'))
    if mbid != 0:
        ok = False
else:
    print('  map_bid 命中 config_guaji: %s' % ('是' if int(exp_spot['map_bid']) == mbid else '否'))
    if int(exp_spot['map_bid']) != mbid:
        ok = False
if mb != TEST_MISSION or used != len(body) or errs:
    ok = False
st = db_state(PLAYER_RID)
print('  mission_bid 是否落库: %s (%s)' % (st and st.get('mission_bid'), st))
if not st or int(st.get('mission_bid') or 0) != TEST_MISSION:
    ok = False

# ---- 15403 合法怪 ----
good_mon = int(GUAJI[0]['mon_bid'])
before = int(db_state(PLAYER_RID).get('kill_count') or 0)
body = q(s, 15403, struct.pack('>I', good_mon))
used, errs, unv = parse_full(body, sc_spec(15403))
print('\n== 15403 合法怪 mon_bid=%d（config_guaji 第 1 条）==' % good_mon)
print('  len=%d 消耗=%d errs=%s code=%d' % (len(body), used, errs, body[0]))
after = int(db_state(PLAYER_RID).get('kill_count') or 0)
print('  kill_count: %d → %d' % (before, after))
if body[0] != 1 or after != before + 1 or used != len(body) or errs:
    ok = False

# ---- 15403 未知怪 ----
body = q(s, 15403, struct.pack('>I', BAD_MON))
print('\n== 15403 未知怪 mon_bid=%d ==' % BAD_MON)
n = struct.unpack_from('>H', body, 1)[0]
msg = body[3:3 + n].decode('utf-8', 'replace')
after2 = int(db_state(PLAYER_RID).get('kill_count') or 0)
print('  code=%d msg=%r  kill_count 未变: %s' % (body[0], msg, after2 == after))
if body[0] != 0 or after2 != after:
    ok = False

# ---- 15404 推送（管理接口触发）----
s.settimeout(3.0)
try:
    with urllib.request.urlopen('http://127.0.0.1:8080/DSH_ADMIN/guaji_end?rid=%d' % PLAYER_RID,
                                timeout=5) as f:
        admin = json.loads(f.read().decode('utf-8'))
except Exception as e:
    admin = {'ok': False, 'err': repr(e)}
print('\n== 15404 推送（/DSH_ADMIN/guaji_end）==')
print('  admin resp =', json.dumps(admin, ensure_ascii=False)[:160])
got = None
try:
    while True:
        hdr = recv_exact(s, 6)
        ln, rc = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == 15404:
            got = p
            break
except socket.timeout:
    pass
if got is None:
    print('  ★ 未收到 15404 推送')
    ok = False
else:
    used, errs, unv = parse_full(got, sc_spec(15404))
    print('  15404 len=%d 消耗=%d errs=%s mission_bid=%d  PASS=%s'
          % (len(got), used, errs, struct.unpack_from('>I', got, 0)[0],
             used == len(got) and not errs))
    if used != len(got) or errs:
        ok = False
s.close()

# ---- 恢复 ----
print('\n== 恢复 guaji_state ==')
con = sqlite3.connect(DB)
if orig is None:
    con.execute('DELETE FROM guaji_state WHERE rid=?', (PLAYER_RID,))
else:
    cols = [k for k in orig if k != 'rid']
    con.execute('INSERT OR REPLACE INTO guaji_state (rid,%s) VALUES (%s)'
                % (','.join(cols), ','.join(['?'] * (len(cols) + 1))),
                [PLAYER_RID] + [orig[c] for c in cols])
con.commit()
con.close()
print('  恢复后 =', db_state(PLAYER_RID))

print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
