# -*- coding: utf-8 -*-
"""account.service —— 账号层 + 登录/建角命令（Phase 2 step 2）。

设计依据：phase2_design.md §二 account/。
迁移来源（mock_server.py 当前行号）：
  db_account_ensure / db_roles_of_uid / db_create_role   L4997–5051
  build_1110_roles                                       L1649–1689
  handle 1110 (登录)                                      L9676–9706
  handle 10101 (建角)                                     L15195–15220

注册命令：1110、10101。handler 签名 fn(h, cmd, body)，h=TcpHandler 实例。

★ 2026-10-17 三区 + 账号系统（本轮改动，全是"加约束"，不改协议形状）：
  1) **按区过滤角色**：CS_1110 的 `enter_srv_id` 从此真正被消费 ——
     以前 `db_roles_of_uid()` 恒返回该账号**所有**角色、且把 srv_id 写死 '1'，
     于是"一服建角、二三服都看得见"。
  2) **一区一角色**：建角时若该账号在该区已有角色 ⇒ 拒绝并给出原因
     （开关 config.json: one_role_per_zone，默认 true）。
  3) **服务端账号记录**：真实账号表 —— 密码哈希（首登绑定）、最近登录时间、
     最近区服、登录次数。密码来源：客户端 UserPanel 会把**密码写进 CS_1110 的
     `token` 字段**（user_panel.luac：`DengluPlatForm:getInstance().info.token =
     DEF_TOKEN or 密码`），所以服务端收得到，可以做真的账号鉴权。
     开关 config.json: account_auth（默认 true；关掉则退回"只记录不校验"）。
     ⚠ 老账号（无 pwd_hash）走**首登绑定**，不会被锁死。
"""

import hashlib
import struct
import sqlite3
import time

from core import runtime
from core.dispatch import register
from persistence.db import db_conn, db_release
from protocol.frame import w_u8, w_u16, w_u32, w_str, pack_frame

log = runtime.log
DEFAULT_UID = runtime.DEFAULT_UID
DEFAULT_SRV = '1'          # 未指定区服时的回退（与旧行为一致）


def _cfg_flag(name, default=True):
    """读运行配置开关（runtime.CFG 由 mock_server.main() 充填）。"""
    try:
        v = (runtime.CFG or {}).get(name, default)
    except Exception:
        return default
    if isinstance(v, str):
        return v.strip().lower() not in ('0', 'false', 'no', 'off', '')
    return bool(v)


def pwd_hash(pwd):
    """密码哈希。

    ⚠ 这是**本机私服**的账号口令，不是公网凭据：固定前缀 + SHA-256，
      够用且不需要额外依赖（不引 bcrypt/argon2）。不宣称抗离线爆破。
    """
    if not pwd:
        return ''
    return hashlib.sha256(('dsh-jstm:' + str(pwd)).encode('utf-8')).hexdigest()


def build_1110_roles(roles):
    """SCAccountLogin_1110 = code:uint8, msg:string, roles:table(...), least_career:uint8。
    code 必须 = 1（TRUE，否则弹空白提示框）。原 mock_server L1649。"""
    body = w_u8(1) + w_str('') + w_u16(len(roles))
    for r in roles:
        body += w_u32(r.get('rid', 0))
        body += w_str(r.get('srv_id', ''))
        body += w_str(r.get('name', ''))
        body += w_u16(r.get('lev', 1))
        body += w_u8(r.get('sex', 0))
        body += w_u16(r.get('career', 1))
        body += w_u8(r.get('is_online', 0))
    body += w_u8(0)          # least_career
    return body


def build_1110_fail(msg):
    """登录失败应答：code=0 + msg（客户端 on1110Rolelist: code ~= TRUE ⇒ message(msg)）。"""
    return w_u8(0) + w_str(msg or '登录失败') + w_u16(0) + w_u8(0)


def db_account_ensure(uid, name=''):
    """确保账号存在，返回归一化后的 uid（保留原语义，兼容既有调用方）。"""
    uid = (str(uid).strip() if uid else '') or DEFAULT_UID
    try:
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO accounts (uid,name,create_ts) VALUES (?,?,?)',
                    (uid, name or uid, int(time.time())))
        con.commit()
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_account_ensure failed: %r' % (e,))
    return uid


def db_account_upsert(uid, name='', pwd='', srv_id=DEFAULT_SRV):
    """账号记录 + 鉴权。返回 (ok: bool, msg: str)。

    规则：
      · account_auth=false           → 只记录，不校验（退回旧行为）。
      · 新账号 / 老账号无 pwd_hash    → **首登绑定**本次密码（老账号不会被锁死）。
      · 已有 pwd_hash 且本次不匹配    → 拒绝，msg 由客户端弹出。
      · 每次成功登录都刷新 last_login_ts / last_srv_id / login_count。
    """
    uid = (str(uid).strip() if uid else '') or DEFAULT_UID
    srv = str(srv_id or DEFAULT_SRV) or DEFAULT_SRV
    now = int(time.time())
    enforce = _cfg_flag('account_auth', True)
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT uid,pwd_hash,login_count FROM accounts WHERE uid=?',
                          (uid,)).fetchone()
        if row is None:
            con.execute('INSERT INTO accounts '
                        '(uid,name,create_ts,pwd_hash,last_login_ts,last_srv_id,login_count) '
                        'VALUES (?,?,?,?,?,?,?)',
                        (uid, name or uid, now, (pwd_hash(pwd) or None), now, srv, 1))
            log('tcp.log', '  ** 账号新建 uid=%s（首登绑定密码=%s）'
                % (uid, 'yes' if pwd else 'no'))
        else:
            stored = row['pwd_hash']
            if enforce and stored:
                if not pwd:
                    db_release(con)
                    return False, '该账号已设置密码，请输入密码'
                if pwd_hash(pwd) != stored:
                    db_release(con)
                    log('tcp.log', '  !! 账号鉴权失败 uid=%s（密码不匹配）' % uid)
                    return False, '账号或密码不正确'
            con.execute('UPDATE accounts SET name=?, pwd_hash=?, last_login_ts=?, '
                        'last_srv_id=?, login_count=COALESCE(login_count,0)+1 WHERE uid=?',
                        (name or uid, stored or (pwd_hash(pwd) or None), now, srv, uid))
        con.commit()
        db_release(con)
        return True, ''
    except Exception as e:
        # 兜底：账号表出错**不阻断登录**（与旧行为一致；宁可少记一笔，不可让人进不去）
        log('tcp.log', '  !! db_account_upsert failed: %r' % (e,))
        return True, ''


def db_roles_of_uid(uid, srv_id=None):
    """该账号**在该区**的角色列表 —— 供 SC_1110 的 roles 表。

    ★ srv_id 为 None/'' 表示"不过滤"（仅调试用）；正常登录一律带区服。
    """
    out = []
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        sql = 'SELECT rid,name,level,career,sex,status,srv_id FROM roles WHERE uid=?'
        params = [uid]
        if srv_id is not None and str(srv_id) != '':
            sql += ' AND srv_id=?'
            params.append(str(srv_id))
        sql += ' ORDER BY rid'
        for r in con.execute(sql, tuple(params)):
            out.append({'rid': int(r['rid']), 'srv_id': str(r['srv_id'] or DEFAULT_SRV),
                        'name': r['name'] or '', 'lev': int(r['level'] or 1),
                        'sex': int(r['sex'] or 0), 'career': int(r['career'] or 1),
                        'is_online': int(r['status'] or 0)})
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_roles_of_uid failed: %r' % (e,))
    return out


def db_role_in_srv(uid, srv_id):
    """该账号在该区已有的角色 rid（无则 0）。"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT rid FROM roles WHERE uid=? AND srv_id=? ORDER BY rid LIMIT 1',
                          (uid, str(srv_id or DEFAULT_SRV))).fetchone()
        db_release(con)
        return int(row['rid']) if row else 0
    except Exception as e:
        log('tcp.log', '  !! db_role_in_srv failed: %r' % (e,))
        return 0


def db_create_role(uid, name, sex, career, srv_id=DEFAULT_SRV):
    """真建角色（CS_10101）→ 返回新 rid；失败/该区已有角色返回 None。

    ★ 一区一角色：开关 one_role_per_zone（默认 true）。关掉即可在同区多建。
    """
    from role.storage import db_save_role, ROLE_DEFAULTS
    uid = (str(uid).strip() if uid else '') or DEFAULT_UID
    srv = str(srv_id or DEFAULT_SRV) or DEFAULT_SRV
    if _cfg_flag('one_role_per_zone', True):
        _ex = db_role_in_srv(uid, srv)
        if _ex:
            log('tcp.log', '  !! 10101 拒绝：uid=%s 在区 %s 已有角色 rid=%d'
                % (uid, srv, _ex))
            return None
    try:
        con = db_conn()
        row = con.execute('SELECT MAX(rid) FROM roles').fetchone()
        db_release(con)
        rid = max(int(row[0] or 1000) + 1, 2001)
    except Exception as e:
        log('tcp.log', '  !! db_create_role rid 分配失败: %r' % (e,))
        return None
    ok = db_save_role(rid,
                      uid=(str(uid).strip() if uid else '') or DEFAULT_UID,
                      name=(name or ('角色%d' % rid)),
                      level=int(ROLE_DEFAULTS.get('lev', 1)),
                      career=int(career or 1) & 0xffff,
                      sex=int(sex or 0) & 0xff,
                      srv_id=srv,
                      status=0)
    return rid if ok else None


@register(1110)
def handle_1110(h, cmd, body):
    """CS_1110 登录：按 (账号, 区服) 返回角色列表 + 记录/校验账号。"""
    args = {}
    try:
        _n = struct.unpack_from('>H', body, 0)[0]
        _off = 2
        for _ in range(_n):
            _kl = struct.unpack_from('>H', body, _off)[0]; _off += 2
            _k = body[_off:_off + _kl].decode('utf-8', 'replace'); _off += _kl
            _vl = struct.unpack_from('>H', body, _off)[0]; _off += 2
            _v = body[_off:_off + _vl].decode('utf-8', 'replace'); _off += _vl
            args[_k] = _v
    except Exception:
        args = {}
    uid = (str(args.get('account') or '').strip()) or DEFAULT_UID
    # ★ 区服：客户端 CS_1110 的 enter_srv_id = 玩家在登录页选中的那个区
    srv = (str(args.get('enter_srv_id') or '').strip()) or DEFAULT_SRV
    # ★ 密码：UserPanel 把密码写进 token 字段（见模块 docstring）
    pwd = str(args.get('token') or '')
    h._uid = uid
    h._srv_id = srv                # ★ 10101 建角时据此落区（CS_10101 本身不带 srv_id）
    h._ver_family = runtime.ver_family_of(len(body), args)

    ok, msg = db_account_upsert(uid, name=uid, pwd=pwd, srv_id=srv)
    if not ok:
        h.request.sendall(pack_frame(1110, build_1110_fail(msg)))
        log('tcp.log', '  << 1110 拒绝登录 account=%s srv=%s msg=%s' % (uid, srv, msg))
        return

    db_account_ensure(uid, name=uid)      # 兜底：确保账号行存在
    roles = db_roles_of_uid(uid, srv)
    pkt = pack_frame(1110, build_1110_roles(roles))
    h.request.sendall(pkt)
    log('tcp.log', '  << 1110 SCAccountLogin account=%s srv=%s roles=%d keys=%s ver=%s (%d bytes)'
        % (uid, srv, len(roles), sorted(args) or '(空args)',
           getattr(h, '_ver_family', '?'), len(pkt)))


@register(10101)
def handle_10101(h, cmd, body):
    """CS_10101 建角：落在**本次登录选中的区**，并按 one_role_per_zone 约束。"""
    try:
        _sex = body[0] if len(body) >= 1 else 0
        _nl = struct.unpack_from('>H', body, 1)[0]
        _name = body[3:3 + _nl].decode('utf-8', 'replace')
        _co = 3 + _nl
        _career = (struct.unpack_from('>h', body, _co)[0]
                   if len(body) >= _co + 2 else 1)
    except Exception:
        _sex, _name, _career = 0, '', 1
    _uid = getattr(h, '_uid', None) or DEFAULT_UID
    _srv = str(getattr(h, '_srv_id', None) or DEFAULT_SRV)
    if _cfg_flag('one_role_per_zone', True) and db_role_in_srv(_uid, _srv):
        out = w_u8(0) + w_str('本区已有角色，请直接进入游戏') + w_u32(0) + w_str(_srv)
        h.request.sendall(pack_frame(10101, out))
        log('tcp.log', '  !! 10101 本区已有角色 uid=%s srv=%s name=%s'
            % (_uid, _srv, _name))
        return
    _rid = db_create_role(_uid, _name, _sex, _career, _srv)
    if _rid:
        out = w_u8(1) + w_str('') + w_u32(_rid) + w_str(_srv)
        log('tcp.log', '  ** 10101 建角成功 uid=%s srv=%s rid=%d name=%s sex=%d career=%d'
            % (_uid, _srv, _rid, _name, _sex, _career))
    else:
        out = w_u8(0) + w_str('建角失败') + w_u32(0) + w_str(_srv)
        log('tcp.log', '  !! 10101 建角失败 uid=%s srv=%s name=%s' % (_uid, _srv, _name))
    h.request.sendall(pack_frame(10101, out))
