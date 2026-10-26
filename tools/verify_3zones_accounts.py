# -*- coding: utf-8 -*-
"""三区 + 账号系统 自检（离线，不碰活库、不起服务）。

用法（仓库根目录）：
    python tools/verify_3zones_accounts.py

做什么：
  1. 把 server/state/roles.db **复制到临时目录**，把 persistence.db.DB_PATH 指过去，
     跑 db_init() 验证迁移（roles.srv_id / accounts.* 加列 + 历史角色回填 '1'）。
  2. 直接调 account.service 的库函数，断言：
       · 同账号不同区可各建一个角色；同区重复建角被拒（一区一角色）
       · db_roles_of_uid(uid, 区) 只返回该区角色（三区隔离的根）
       · 账号鉴权：首登绑定、密码正确通过、错误/空密码被拒、account_auth=false 放开
  3. 用**假连接**直接跑 @register(1110)/@register(10101) 的 handler，
     断言 SC_1110 的 code/角色数按区变化、10101 的应答 srv_id 落在正确区。
     （假连接只捕获 sendall 的字节，不做真实 socket。）
"""
import os
import shutil
import struct
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'server')
sys.path.insert(0, SERVER)

FAIL = []


def check(cond, msg):
    print(('  OK   ' if cond else '  FAIL ') + msg)
    if not cond:
        FAIL.append(msg)


# ── 1) 临时库 + 迁移 ────────────────────────────────────────────────
live_db = os.path.join(SERVER, 'state', 'roles.db')
tmpdir = tempfile.mkdtemp(prefix='dsh_3z_')
tmp_db = os.path.join(tmpdir, 'roles.db')
if os.path.isfile(live_db):
    shutil.copy2(live_db, tmp_db)
    print('copied live db -> %s' % tmp_db)
else:
    print('(no live db; starting from empty)')

from persistence import db as pdb            # noqa: E402
pdb.DB_PATH = tmp_db                         # ★ 全部读写都走临时副本
pdb.db_init()
print('db_init() done（迁移已跑）')

con = pdb.db_conn()
role_cols = [r[1] for r in con.execute('PRAGMA table_info(roles)')]
acct_cols = [r[1] for r in con.execute('PRAGMA table_info(accounts)')]
check('srv_id' in role_cols, 'roles.srv_id 列已加')
check('pwd_hash' in acct_cols and 'last_login_ts' in acct_cols
      and 'last_srv_id' in acct_cols and 'login_count' in acct_cols,
      'accounts 规范化列已加（pwd_hash/last_login_ts/last_srv_id/login_count）')
nulls = con.execute("SELECT COUNT(*) FROM roles WHERE srv_id IS NULL OR srv_id=''").fetchone()[0]
check(nulls == 0, '历史角色 srv_id 已回填（无空值，实际 %d 行空）' % nulls)
legacy = con.execute('SELECT rid,srv_id FROM roles ORDER BY rid').fetchall()
print('   历史角色:', [(int(r[0]), r[1]) for r in legacy])
pdb.db_release(con)

# ── 2) 库函数：一区一角色 + 按区过滤 + 鉴权 ─────────────────────────
import account.service as A                    # noqa: E402
from core import runtime                       # noqa: E402

UID = 'verify_user'
r1 = A.db_create_role(UID, '一区角色', 0, 1, '1')
r2 = A.db_create_role(UID, '二区角色', 0, 2, '2')
r3 = A.db_create_role(UID, '一区第二个', 0, 1, '1')
check(r1 and r2, '同账号在 1 区/2 区各建一个角色成功（rid=%s/%s）' % (r1, r2))
check(r3 is None, '同账号在同一区重复建角被拒（一区一角色）')

z1 = A.db_roles_of_uid(UID, '1')
z2 = A.db_roles_of_uid(UID, '2')
z3 = A.db_roles_of_uid(UID, '3')
check([r['rid'] for r in z1] == [r1], '1 区只返回 1 区角色')
check([r['rid'] for r in z2] == [r2], '2 区只返回 2 区角色')
check(z3 == [], '3 区（没建过）返回空 —— 不再"一服建角、三服可见"')
check(all(r['srv_id'] == '1' for r in z1) and all(r['srv_id'] == '2' for r in z2),
      '角色下发携带真实 srv_id')

# 鉴权
ok, msg = A.db_account_upsert('vfy_auth', pwd='pw123456', srv_id='1')
check(ok, '首登：绑定密码（无 pwd_hash 时）')
ok2, msg2 = A.db_account_upsert('vfy_auth', pwd='wrongpw', srv_id='1')
check((not ok2) and msg2, '密码错误被拒（msg=%r）' % msg2)
ok3, _ = A.db_account_upsert('vfy_auth', pwd='pw123456', srv_id='2')
check(ok3, '密码正确通过（并记录 last_srv_id）')

con = pdb.db_conn()
row = con.execute('SELECT pwd_hash,last_srv_id,login_count FROM accounts WHERE uid=?',
                  ('vfy_auth',)).fetchone()
check(row[0] and row[0] != 'pw123456', '密码以哈希落库（不是明文）')
check(row[1] == '2' and int(row[2] or 0) >= 2, 'last_srv_id/login_count 已刷新（%s/%s）'
      % (row[1], row[2]))
pdb.db_release(con)

runtime.CFG['account_auth'] = False
ok4, _ = A.db_account_upsert('vfy_auth', pwd='whatever', srv_id='1')
check(ok4, 'account_auth=false 时不校验（开关有效）')
runtime.CFG['account_auth'] = True


# ── 3) handler 级：假连接跑 1110 / 10101 ────────────────────────────
class FakeConn(object):
    def __init__(self):
        self.sent = []

    def sendall(self, b):
        self.sent.append(b)


class FakeH(object):
    def __init__(self):
        self.request = FakeConn()
        self.cfg = {}


def cs1110(account, srv, token='pw123456'):
    items = [('account', account), ('enter_srv_id', srv), ('token', token),
             ('platform', 'ewan'), ('timestamp', '1')]
    body = struct.pack('>H', len(items))
    for k, v in items:
        kb = k.encode('utf-8')
        vb = v.encode('utf-8')
        body += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return body


def parse_1110(pkt):
    """解 [u32 len][u16 cmd][code u8][msg str][n u16][roles…][least u8]。"""
    ln = struct.unpack_from('>I', pkt, 0)[0]
    cmd = struct.unpack_from('>H', pkt, 4)[0]
    b = pkt[6:4 + ln]
    code = b[0]
    ml = struct.unpack_from('>H', b, 1)[0]
    off = 3 + ml
    n = struct.unpack_from('>H', b, off)[0]
    off += 2
    roles = []
    for _ in range(n):
        rid = struct.unpack_from('>I', b, off)[0]; off += 4
        sl = struct.unpack_from('>H', b, off)[0]; off += 2
        srv = b[off:off + sl].decode('utf-8'); off += sl
        nl = struct.unpack_from('>H', b, off)[0]; off += 2
        name = b[off:off + nl].decode('utf-8'); off += nl
        off += 2 + 1 + 2 + 1
        roles.append((rid, srv, name))
    return cmd, code, roles


print('\n== handler 级 ==')
h = FakeH()
A.handle_1110(h, 1110, cs1110(UID, '1'))
cmd, code, roles = parse_1110(h.request.sent[-1])
check(cmd == 1110 and code == 1, '1110 在 1 区返回 code=1')
check([r[0] for r in roles] == [r1], '1110 在 1 区只回 1 区的角色')
h2 = FakeH()
A.handle_1110(h2, 1110, cs1110(UID, '2'))
_, code2, roles2 = parse_1110(h2.request.sent[-1])
check([r[0] for r in roles2] == [r2], '1110 在 2 区只回 2 区的角色')
h3 = FakeH()
A.handle_1110(h3, 1110, cs1110(UID, '3'))
_, _, roles3 = parse_1110(h3.request.sent[-1])
check(roles3 == [], '1110 在 3 区回空（隔离）')

# 错误密码 → code=0 + msg
h4 = FakeH()
A.handle_1110(h4, 1110, cs1110('vfy_auth', '1', token='bad'))
_, code4, _ = parse_1110(h4.request.sent[-1])
check(code4 == 0, '密码错误时 1110 返回 code=0（客户端会弹 msg）')

# 10101：在 3 区建角 → 落在 3 区；再建 → 被拒
h5 = FakeH()
A.handle_1110(h5, 1110, cs1110(UID, '3'))          # 先登录拿 _srv_id
name = '三区新角色'.encode('utf-8')
body10101 = bytes([0]) + struct.pack('>H', len(name)) + name + struct.pack('>h', 1)
A.handle_10101(h5, 10101, body10101)
# SC_10101 = code:u8 + msg:string(u16 len + bytes) + rid:u32 + srv_id:string
pkt = h5.request.sent[-1]
code5 = pkt[6]
_ml = struct.unpack_from('>H', pkt, 7)[0]
_off = 9 + _ml
rid5 = struct.unpack_from('>I', pkt, _off)[0]
_sl5 = struct.unpack_from('>H', pkt, _off + 4)[0]
srv5 = pkt[_off + 6:_off + 6 + _sl5].decode('utf-8')
check(code5 == 1 and srv5 == '3', '10101 建角落在登录时选中的区（srv_id=%r）' % srv5)
check([r['rid'] for r in A.db_roles_of_uid(UID, '3')] == [rid5], '新角色确实落在 3 区')
A.handle_10101(h5, 10101, body10101)
code6 = h5.request.sent[-1][6]
check(code6 == 0, '同区第二次建角被拒（code=0）')

shutil.rmtree(tmpdir, ignore_errors=True)
print('\nRESULT:', 'PASS' if not FAIL else 'FAIL(%d): %s' % (len(FAIL), FAIL))
sys.exit(1 if FAIL else 0)
