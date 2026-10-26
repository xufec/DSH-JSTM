# -*- coding: utf-8 -*-
"""三区隔离 / 账号鉴权 —— **活服务器**端到端自检（真 TCP，127.0.0.1:9000）。

用法（仓库根目录，服务端需已在跑）：
    python tools/verify_3zones_live.py

覆盖：
  1. CS_1110 带 enter_srv_id → 只回该区角色（2 区新建的角色，1/3 区看不到）
  2. CS_10101 建角落在**登录时选中的区**（并且同区重复建角被拒）
  3. CS_10102 带**别的区**的 srv_id 登录 → 服务端拒绝（code=0）—— 跨区登录被拦
  4. CS_10102 带正确区的 srv_id → 通过（code=1）
  5. 账号鉴权：密码错误 → CS_1110 返回 code=0 + msg

⚠ 只使用自带前缀的**临时测试账号**（zonecheck_<ts>），跑完自动删除该账号及其角色与其
   rid 关联行；**绝不触碰**已有账号（避免替别人"首登绑定"密码）。
"""
import os
import sqlite3
import struct
import sys
import time
import socket

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')

HOST, PORT = '127.0.0.1', 9000
UID = 'zonecheck_%d' % int(time.time())
PWD = 'zonepw123456'

FAIL = []


def check(cond, msg):
    print(('  OK   ' if cond else '  FAIL ') + msg)
    if not cond:
        FAIL.append(msg)


def w_u8(v):
    return struct.pack('>B', int(v) & 0xFF)


def w_u16(v):
    return struct.pack('>H', int(v) & 0xFFFF)


def w_u32(v):
    return struct.pack('>I', int(v) & 0xFFFFFFFF)


def w_str(s):
    b = (s or '').encode('utf-8')
    return w_u16(len(b)) + b


def frame(cmd, body=b''):
    payload = w_u16(cmd) + body
    return w_u32(len(payload)) + payload


def args_body(pairs):
    body = w_u16(len(pairs))
    for k, v in pairs:
        body += w_str(k) + w_str(v)
    return body


def recv_frame(sock, timeout=6.0):
    sock.settimeout(timeout)
    buf = b''
    while len(buf) < 6:
        d = sock.recv(65536)
        if not d:
            raise IOError('connection closed')
        buf += d
    ln = struct.unpack_from('>I', buf, 0)[0]
    while len(buf) < 4 + ln:
        d = sock.recv(65536)
        if not d:
            raise IOError('connection closed mid-frame')
        buf += d
    return struct.unpack_from('>H', buf, 4)[0], buf[6:4 + ln]


def login(sock, account, srv, token=PWD):
    """发 CS_1110；返回 (code, msg, roles[(rid,srv_id,name)])。"""
    sock.sendall(frame(1110, args_body([
        ('account', account), ('enter_srv_id', srv), ('token', token),
        ('platform', 'ewan'), ('timestamp', str(int(time.time())))])))
    cmd, b = recv_frame(sock)
    if cmd != 1110:
        return (-1, 'unexpected cmd=%d' % cmd, [])
    code = b[0]
    ml = struct.unpack_from('>H', b, 1)[0]
    msg = b[3:3 + ml].decode('utf-8', 'replace')
    off = 3 + ml
    n = struct.unpack_from('>H', b, off)[0]
    off += 2
    roles = []
    for _ in range(n):
        rid = struct.unpack_from('>I', b, off)[0]; off += 4
        sl = struct.unpack_from('>H', b, off)[0]; off += 2
        srv_id = b[off:off + sl].decode('utf-8'); off += sl
        nl = struct.unpack_from('>H', b, off)[0]; off += 2
        name = b[off:off + nl].decode('utf-8'); off += nl
        off += 2 + 1 + 2 + 1        # lev, sex, career, is_online
        roles.append((rid, srv_id, name))
    return (code, msg, roles)


def create_role(sock, name, sex=0, career=1):
    body = w_u8(sex) + w_str(name) + struct.pack('>h', career)
    sock.sendall(frame(10101, body))
    cmd, b = recv_frame(sock)
    code = b[0]
    ml = struct.unpack_from('>H', b, 1)[0]
    msg = b[3:3 + ml].decode('utf-8', 'replace')
    off = 3 + ml
    rid = struct.unpack_from('>I', b, off)[0]
    sl = struct.unpack_from('>H', b, off + 4)[0]
    srv_id = b[off + 6:off + 6 + sl].decode('utf-8')
    return code, msg, rid, srv_id


def role_login(sock, rid, srv):
    """CS_10102：srv_id 用**真机实测的单字节**编码（1 区 = 0x01）。"""
    body = w_u32(rid) + w_u8(int(srv) & 0xFF)
    sock.sendall(frame(10102, body))
    cmd, b = recv_frame(sock)
    code = b[0]
    ml = struct.unpack_from('>H', b, 1)[0]
    msg = b[3:3 + ml].decode('utf-8', 'replace')
    return code, msg


print('live target: %s:%d   test account: %s' % (HOST, PORT, UID))
try:
    s = socket.create_connection((HOST, PORT), timeout=6)
except Exception as e:
    print('!! 连不上服务端 %s:%d (%r) —— 先启动 server/mock_server.py' % (HOST, PORT, e))
    sys.exit(2)

# 1) 2 区登录（新账号 → 首登绑定）→ 建角落在 2 区
code, msg, roles = login(s, UID, '2')
check(code == 1, '新账号在 2 区登录成功（code=1, msg=%r）' % msg)
check(roles == [], '新账号在 2 区还没有角色')
code, msg, rid2, srv2 = create_role(s, '二区角色A')
check(code == 1 and srv2 == '2', 'CS_10101 建角落在 2 区（rid=%s srv=%r）' % (rid2, srv2))
code, msg, rid_dup, _ = create_role(s, '二区角色B')
check(code == 0, '同区重复建角被拒（code=0, msg=%r）' % msg)

# 2) 区隔离：同一个账号换区看角色列表
code, _, z2 = login(s, UID, '2')
check([r[0] for r in z2] == [rid2], '2 区列表 = 刚建的角色')
code, _, z1 = login(s, UID, '1')
check(z1 == [], '1 区看不到 2 区的角色（隔离生效）')
code, _, z3 = login(s, UID, '3')
check(z3 == [], '3 区看不到 2 区的角色（隔离生效）')
check(all(r[1] == '2' for r in z2), '角色条目携带真实 srv_id=2')

# 3) 跨区 10102：用 1 区的 srv_id 登录 2 区的角色 → 必须被拒
code, msg = role_login(s, rid2, 1)
check(code == 0, '跨区登录 CS_10102(rid=%s, srv=1) 被拒（code=0, msg=%r）' % (rid2, msg))
# 4) 本区 10102 → 通过
code, msg = role_login(s, rid2, 2)
check(code == 1, '本区登录 CS_10102(rid=%s, srv=2) 通过（code=1）' % rid2)

# 5) 密码错误 → 1110 拒绝
s2 = socket.create_connection((HOST, PORT), timeout=6)
code, msg, _ = login(s2, UID, '2', token='definitely-wrong')
check(code == 0 and msg, '密码错误被拒（code=0, msg=%r）' % msg)
s2.close()


# 6) 角色数据三连（10301/10302/10303）—— 收敛后由 role/handler.py 走**模块实现**
#    2026-10-17 把 mock_server 里那份"本地新实现"删掉后，这里就是唯一路径；本段确保
#    它真能出包（不是空帧、不是异常被兜住后静默）。
def recv_cmd(sock, want, timeout=6.0):
    """读到指定 cmd 为止（中间会有 10200/10201/10305 等服务端推送）。"""
    sock.settimeout(timeout)
    buf = b''
    deadline = time.time() + timeout
    while time.time() < deadline:
        while True:
            if len(buf) >= 6:
                ln = struct.unpack_from('>I', buf, 0)[0]
                if len(buf) >= 4 + ln:
                    cmd = struct.unpack_from('>H', buf, 4)[0]
                    body = buf[6:4 + ln]
                    buf = buf[4 + ln:]
                    if cmd == want:
                        return cmd, body
                    continue
            break
        d = sock.recv(65536)
        if not d:
            raise IOError('connection closed')
        buf += d
    return None, b''


s3 = socket.create_connection((HOST, PORT), timeout=6)
code, _, roles3 = login(s3, UID, '2')
check(code == 1 and [r[0] for r in roles3] == [rid2], '10301~3 前置：重新登录并进入 2 区角色')
for _cmd, _min in ((10301, 40), (10302, 20), (10303, 40)):
    s3.sendall(frame(_cmd))
    got, body = recv_cmd(s3, _cmd)
    check(got == _cmd and len(body) >= _min,
          'SC_%d 应答正常（%d 字节 ≥ %d）' % (_cmd, len(body), _min))
s3.close()

# ── 清理：只删本次测试账号及其角色与 rid 关联行 ─────────────────────
try:
    con = sqlite3.connect(DB, timeout=10)
    rids = [int(r[0]) for r in con.execute('SELECT rid FROM roles WHERE uid=?', (UID,))]
    for t in ('roles', 'role_attr', 'role_assets', 'missions', 'bag_items',
              'equip_items', 'store_items', 'role_heros', 'role_buffs'):
        try:
            for rid in rids:
                con.execute('DELETE FROM %s WHERE rid=?' % t, (rid,))
        except Exception:
            pass
    con.execute('DELETE FROM accounts WHERE uid=?', (UID,))
    con.commit()
    con.close()
    print('cleaned test rows: account=%s rids=%s' % (UID, rids))
except Exception as e:
    print('!! cleanup failed: %r' % (e,))

print('\nRESULT:', 'PASS' if not FAIL else 'FAIL(%d): %s' % (len(FAIL), FAIL))
sys.exit(1 if FAIL else 0)
