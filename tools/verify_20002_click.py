# -*- coding: utf-8 -*-
"""R77 验证：模拟客户端点击怪发出的 `CS_20002{mon_id}`，确认服务端**不再回**
`no such monster 10105`。

为什么能这样验：R77 把"玩家当前场景"**落库**了（`roles.scene_id`），
而 `20002` 的校验改为读**当前场景**的怪表 ⇒ 任何新连接（本脚本）都能拿到
与真机一致的结果，**不必等玩家手点**。

用法：
    python tools/verify_20002_click.py                 # 用角色当前场景
    python tools/verify_20002_click.py 10005 10105     # 指定场景/怪
"""
import io
import socket
import struct
import sys
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from audit_sc_live import pack_frame, recv_exact  # noqa: E402


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
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        p = recv_exact(s, ln - 2)
        if rc == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]
            off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]
            off += 2
            if cnt:
                rid = struct.unpack_from('>I', p, off)[0]
            break
    if rid:
        s.sendall(pack_frame(10102, struct.pack('>I', rid) + w_str('1')))
        s.settimeout(2.0)
        try:
            while True:
                ln, rc = struct.unpack('>IH', recv_exact(s, 6))
                recv_exact(s, ln - 2)
                if rc == 10102:
                    break
        except socket.timeout:
            pass
        s.settimeout(6.0)
    return rid


def ask(s, cmd, body):
    s.sendall(pack_frame(cmd, body))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        p = recv_exact(s, ln - 2)
        if rc == cmd:
            return p


def main():
    import sqlite3
    con = sqlite3.connect(r'server\state\roles.db')
    row = con.execute('SELECT scene_id,x,y FROM roles WHERE rid=1001').fetchone()
    con.close()
    scene = int(row[0]) if row else 10001
    # ★ 2026-10-01 修正**过时写法**：`10105` 是旧/参考配置里的怪（既不是任务 bid，
    #   也不在任何任务的 `fight_mon` 条件里）。最小回环服的场景怪取自它自己的
    #   `server/config.json`：当前是 **bid 20001** —— 而它**正好是客户端实际提交的任务 `10020`
    #   要求打的怪**（`mission_config.json`: `progress=[["fight_mon",20001,1],…]`）。
    #   ⇒ 按配置取怪，才能得到有意义的"点击→20002"验证结果。
    import json as _json
    import os as _os
    mon = 10105
    try:
        with open(_os.path.join('server', 'config.json'), encoding='utf-8') as _f:
            _cfg = _json.load(_f)
        _m = (_cfg.get('mons') or [{}])[0]
        mon = int(_m.get('id') or _m.get('bid') or mon)
    except Exception:
        pass
    if len(sys.argv) >= 3:
        scene, mon = int(sys.argv[1]), int(sys.argv[2])
    print('DB 里角色当前场景 =', scene, ' 待点怪 =', mon)

    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(6.0)
    print('login rid =', login(s))

    p = ask(s, 20002, struct.pack('>i', mon))
    code = p[0]
    n = struct.unpack_from('>H', p, 1)[0]
    msg = p[3:3 + n].decode('utf-8', 'replace')
    print('CS_20002{mon_id=%d} → code=%d msg=%r  (%d bytes)' % (mon, code, msg, len(p)))
    ok = (code == 1)
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    s.close()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
