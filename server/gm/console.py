# -*- coding: utf-8 -*-
"""gm.console —— GM 后台管理系统（Web 控制台 + 新增管理端点）。

设计纪律（与 HANDOFF.md §二 一致）：
  1. **不新建服务**：复用 mock_server 既有的 HTTP 8080 端口与 `_send`。
  2. **不直改 DB 绕过业务**：写操作一律走 `gm.service` / 既有 `/DSH_ADMIN/*` 正式链路；
     本模块直读 DB 只用于"看"（角色卡/列表/审计），写只有 `setscene` 一处，
     且它写的是**场景坐标**这一没有 Service 覆盖的字段，并显式落 gm.log。
  3. **无循环 import**：本模块不 `import mock_server`。所有需要主机侧函数
     （push_to_rid / pack_frame / build_10201 / scene_* ）的调用，由 mock_server
     在 do_GET 里把**自身模块对象**作为 `host` 传进来。

接入方式（mock_server.py::Handler.do_GET 顶部一处）：
    from gm import console as _gm_console
    if _gm_console.handle(self, sys.modules[__name__]):
        return

新增端点：
    GET /GM                                  后台管理页面（单文件 SPA）
    GET /GM/api?act=overview                 总览
    GET /GM/api?act=roles                    角色列表
    GET /GM/api?act=rolecard&rid=1001        角色聚合卡（等级/资产/背包/装备/战力/任务）
    GET /GM/api?act=online                   在线连接
    GET /GM/api?act=gmlog&n=200              GM 审计尾
    GET /DSH_ADMIN/setscene?rid=&scene=&x=&y=&token=   传送到场景（写库 + 推 10200/10201）
    GET /DSH_ADMIN/rolemail?rid=             邮件列表（后台用）
    GET /DSH_ADMIN/gmsessions                在线连接（同 online，管理面命名）

鉴权：`DSH_GM_TOKEN` 环境变量，缺省 `dshgm`。仅**写操作**校验 token；
      只读端点保持历史无鉴权现状（S3-L8），页面内可填 token 记住在 localStorage。
"""

import json
import os
import sqlite3
import time

from core import runtime
from gm import service as gm_service

DB_PATH = os.path.join(runtime.HERE, 'state', 'roles.db')
PAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'console.html')
GM_LOG = os.path.join(runtime.HERE, 'logs', 'gm.log')

TOKEN_ENV = 'DSH_GM_TOKEN'
DEFAULT_TOKEN = 'dshgm'

# 只读聚合端点（/DSH_ADMIN/<act>）——由本模块接管，不进 mock_server 的老分支。
ADMIN_ACTS = {'roles', 'accounts', 'online', 'gmsessions', 'gmlog', 'rolecard',
              'setscene', 'rolemail'}


# ── 基础工具 ────────────────────────────────────────────────────────────────
def _token_of(q):
    return (q.get('token') or [''])[0]


def token_expected():
    return os.environ.get(TOKEN_ENV) or DEFAULT_TOKEN


def token_ok(q):
    return _token_of(q) == token_expected()


def _db():
    con = sqlite3.connect(DB_PATH, timeout=5.0)
    con.row_factory = sqlite3.Row
    return con


def _json(handler, obj, code=200):
    handler._send(code, json.dumps(obj, ensure_ascii=False, default=str))


def _table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (name,)).fetchone() is not None


# ── 只读聚合 ────────────────────────────────────────────────────────────────
def _roles(con):
    out = []
    for r in con.execute('SELECT rid,uid,name,level,career,sex,scene_id,x,y,'
                         'vip_level,status FROM roles ORDER BY rid').fetchall():
        d = dict(r)
        d['online'] = 0
        out.append(d)
    return out


def _accounts(con):
    """服务端账号记录（2026-10-17 扩充）。

    除 uid/name/create_ts 外，返回：
      · pwd_set      是否有密码（**不回显哈希**，只给布尔）
      · last_login_ts / last_srv_id / login_count   最近登录痕迹
      · roles        该账号**按区**的角色清单 [{rid,srv_id,name,level}, …]
                     —— 直接回答"哪个账号在哪个区有什么角色"，也便于核对三区隔离。
    """
    out = []
    cols = [r[1] for r in con.execute('PRAGMA table_info(accounts)')]
    has_new = 'pwd_hash' in cols
    sel = ('uid,name,create_ts,pwd_hash,last_login_ts,last_srv_id,login_count'
           if has_new else 'uid,name,create_ts')
    for r in con.execute('SELECT %s FROM accounts ORDER BY create_ts' % sel).fetchall():
        d = dict(r)
        d['pwd_set'] = bool(d.pop('pwd_hash', None))
        for k in ('last_login_ts', 'last_srv_id', 'login_count'):
            d.setdefault(k, None)
        d['roles'] = []
        out.append(d)
    try:
        by_uid = {}
        for r in con.execute('SELECT rid,uid,srv_id,name,level FROM roles '
                             'ORDER BY srv_id, rid').fetchall():
            by_uid.setdefault(str(r['uid'] or ''), []).append(
                {'rid': int(r['rid']), 'srv_id': str(r['srv_id'] or '1'),
                 'name': r['name'] or '', 'level': int(r['level'] or 1)})
        for d in out:
            d['roles'] = by_uid.get(str(d.get('uid') or ''), [])
    except Exception:
        pass
    return out


def _online(host):
    """在线连接快照（只取叶子字段，不 dump 活对象）。"""
    rows = []
    try:
        live = list(runtime.LIVE_CONNECTIONS)
    except Exception:
        live = []
    for h in live:
        try:
            rid = host._scene_rid(h)
        except Exception:
            rid = 0
        try:
            addr = '%s:%s' % (h.client_address[0], h.client_address[1])
        except Exception:
            addr = '?'
        rows.append({'rid': int(rid or 0), 'addr': addr})
    return rows


def _gmlog(n=200):
    if not os.path.exists(GM_LOG):
        return []
    with open(GM_LOG, encoding='utf-8', errors='replace') as f:
        return [ln.rstrip('\n') for ln in f.readlines()[-int(n):]]


def _rolecard(con, rid):
    r = con.execute('SELECT * FROM roles WHERE rid=?', (int(rid),)).fetchone()
    if r is None:
        return None
    card = {'role': dict(r)}
    card['assets'] = {x['name']: x['amount'] for x in con.execute(
        'SELECT name,amount FROM role_assets WHERE rid=?', (int(rid),)).fetchall()}
    for tbl, key in (('bag_items', 'bag'), ('store_items', 'store'),
                     ('equip_items', 'equip'), ('missions', 'missions')):
        if _table_exists(con, tbl):
            card[key] = [dict(x) for x in con.execute(
                'SELECT * FROM %s WHERE rid=?' % tbl, (int(rid),)).fetchall()]
        else:
            card[key] = []
    if _table_exists(con, 'role_mail'):
        card['mail_count'] = con.execute(
            'SELECT COUNT(*) FROM role_mail WHERE rid=?', (int(rid),)).fetchone()[0]
    if _table_exists(con, 'reward_log'):
        card['reward_log'] = [dict(x) for x in con.execute(
            'SELECT reference_id,source,granted_ts FROM reward_log WHERE rid=? '
            'ORDER BY granted_ts DESC LIMIT 50', (int(rid),)).fetchall()]
    return card


def _roles_with_online(con, host):
    roles = _roles(con)
    online = {r['rid'] for r in _online(host)}
    for d in roles:
        d['online'] = 1 if d['rid'] in online else 0
    return roles


# ── 写操作：GM 传送 ─────────────────────────────────────────────────────────
def _setscene(host, rid, scene, x, y):
    """GM 传送：写 roles.scene_id/x/y，并向该 rid 在线连接推 10200 + 10201。

    为什么直接写 DB：场景坐标没有 Service 覆盖（`_send_10200` 用的是每连接
    `_last_enter` + `role_with_saved_pos`）。这里写的是持久化坐标，重登即生效，
    与客户端 10204 上报流程不冲突（客户端上报会覆盖回自己的位置）。
    """
    rid, scene = int(rid), int(scene)
    x = int(x) if x is not None else None
    y = int(y) if y is not None else None
    con = _db()
    try:
        row = con.execute('SELECT x,y,dir,level,name,career,sex FROM roles WHERE rid=?',
                          (rid,)).fetchone()
        if row is None:
            return {'ok': False, 'msg': 'no such rid'}
        if x is None or y is None:
            mx, my = host.map_def_xy(scene)
            x = int(mx) if x is None and mx else (x if x is not None else 0)
            y = int(my) if y is None and my else (y if y is not None else 0)
        con.execute('UPDATE roles SET scene_id=?, x=?, y=? WHERE rid=?',
                    (scene, x, y, rid))
        con.commit()
        role = {'rid': rid, 'srv_id': '1', 'name': row['name'],
                'lev': int(row['level'] or 1), 'career': int(row['career'] or 1),
                'sex': int(row['sex'] or 0), 'x': x, 'y': y,
                'dir': int(row['dir'] or 0)}
    finally:
        con.close()

    pushed, note = 0, ''
    try:
        sp = runtime.CFG.get('spawn', {})
        out = (host.w_u8(0) + host.w_str('') + host.w_u32(scene) +
               host.w_u8(sp.get('line_id', 1)) + host.w_u16(x) + host.w_u16(y) +
               host.w_u8(int(role.get('dir') or 0)))
        pkt = host.pack_frame(10200, out)
        # ★ 必须**同时**同步每连接的场景上下文 `_last_enter`：
        #   `push_to_rid` 只发字节，不改 handler 状态；而 `_current_bid()` 以
        #   `_last_enter` 为准做移动校验/10300 补推。不同步 ⇒ 传送后校验仍按旧图，
        #   客户端上报的移动被判"不可走"、坐标被拽回并落库（实测就是这个现象）。
        with runtime.LIVE_LOCK:
            conns = list(runtime.LIVE_CONNECTIONS)
        for ent in conns:
            h = ent[0] if isinstance(ent, (tuple, list)) else ent
            try:
                if int(host._scene_rid(h) or 0) != rid:
                    continue
                h._last_enter = (scene, x, y)
                h.request.sendall(pkt)
                pushed += 1
            except Exception as e:
                note = 'push failed: %r' % (e,)
        npcs, mons = host.scene_quest_extras(runtime.CFG, scene)
        elems = host.scene_elems(scene) if runtime.CFG.get('send_map_elems', True) else []
        pkt2 = host.pack_frame(10201, host.build_10201([role], npcs, mons, elems))
        pushed += host.push_to_rid(rid, pkt2)
        note = ('npcs=%d mons=%d elems=%d %s' % (len(npcs), len(mons), len(elems), note)).strip()
    except Exception as e:
        note = 'push failed: %r' % (e,)

    gm_service.log_gm('setscene', rid, 'scene=%d x=%d y=%d pushed=%d %s ref=gm:setscene:%d:%d'
                      % (scene, x, y, pushed, note, rid, int(time.time())))
    return {'ok': True, 'rid': rid, 'scene': scene, 'x': x, 'y': y,
            'pushed': pushed, 'note': note}


def _rolemail(con, rid, n=100):
    if not _table_exists(con, 'role_mail'):
        return []
    return [dict(x) for x in con.execute(
        'SELECT id,from_name,subject,assets,items,send_time,read_time FROM role_mail '
        'WHERE rid=? ORDER BY id DESC LIMIT ?', (int(rid), int(n))).fetchall()]


# ── 分发：/GM 页面 与 /GM/api ───────────────────────────────────────────────
def handle(handler, host):
    """处理 /GM* 请求。返回 True 表示已应答，调用方直接 return。"""
    path = handler.path.split('?')[0]
    if path not in ('/GM', '/GM/', '/gm', '/gm/'):
        return False
    if not os.path.exists(PAGE_PATH):
        handler._send(500, json.dumps({'ok': False, 'msg': 'console.html missing'},
                                      ensure_ascii=False))
        return True
    with open(PAGE_PATH, encoding='utf-8') as f:
        handler._send(200, f.read(), 'text/html; charset=utf-8')
    return True


def handle_api(handler, host, q):
    """处理 /GM/api?act=...。返回 True 表示已应答。"""
    act = (q.get('act') or ['overview'])[0]
    try:
        if act == 'roles':
            con = _db()
            try:
                _json(handler, {'ok': True, 'roles': _roles_with_online(con, host),
                                'accounts': _accounts(con)})
            finally:
                con.close()
            return True
        if act == 'rolecard':
            rid = (q.get('rid') or ['1001'])[0]
            con = _db()
            try:
                card = _rolecard(con, rid)
            finally:
                con.close()
            _json(handler, {'ok': card is not None, 'card': card},
                  200 if card else 404)
            return True
        if act in ('online', 'gmsessions'):
            _json(handler, {'ok': True, 'online': _online(host)})
            return True
        if act == 'gmlog':
            _json(handler, {'ok': True, 'lines': _gmlog((q.get('n') or [200])[0])})
            return True
        if act == 'token':
            _json(handler, {'ok': token_ok(q), 'token_required': bool(token_expected())})
            return True
        if act == 'overview':
            con = _db()
            try:
                n_roles = con.execute('SELECT COUNT(*) FROM roles').fetchone()[0]
                n_acct = con.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]
                tables = con.execute("SELECT COUNT(*) FROM sqlite_master "
                                     "WHERE type='table'").fetchone()[0]
            finally:
                con.close()
            _json(handler, {'ok': True, 'roles': n_roles, 'accounts': n_acct,
                            'db_tables': tables, 'online': _online(host),
                            'server_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'gm_token_required': bool(token_expected())})
            return True
    except Exception as e:
        _json(handler, {'ok': False, 'msg': '%r' % (e,)}, 500)
        return True
    return False


# ── 分发：/DSH_ADMIN/<act> 新增动作 ─────────────────────────────────────────
def admin(handler, host, act, q, rid):
    """接管本模块新增的 /DSH_ADMIN/<act>。返回 True 表示已应答。"""
    if act not in ADMIN_ACTS:
        return False
    try:
        if act in ('online', 'gmsessions'):
            _json(handler, {'ok': True, 'online': _online(host)})
            return True
        con = _db()
        try:
            if act == 'roles':
                _json(handler, {'ok': True, 'roles': _roles_with_online(con, host),
                                'accounts': _accounts(con), 'n': 0})
                return True
            if act == 'accounts':
                _json(handler, {'ok': True, 'accounts': _accounts(con)})
                return True
            if act == 'gmlog':
                _json(handler, {'ok': True, 'lines': _gmlog((q.get('n') or [200])[0])})
                return True
            if act == 'rolecard':
                card = _rolecard(con, rid)
                _json(handler, {'ok': card is not None, 'card': card},
                      200 if card else 404)
                return True
            if act == 'rolemail':
                _json(handler, {'ok': True, 'rid': rid,
                                'mails': _rolemail(con, rid, (q.get('n') or [100])[0])})
                return True
        finally:
            con.close()
        if act == 'setscene':
            if not token_ok(q):
                _json(handler, {'ok': False, 'msg': 'gm token required'}, 401)
                return True
            res = _setscene(host, rid,
                            (q.get('scene') or q.get('bid') or [10001])[0],
                            (q.get('x') or [None])[0], (q.get('y') or [None])[0])
            _json(handler, res, 200 if res.get('ok') else 404)
            return True
    except Exception as e:
        _json(handler, {'ok': False, 'msg': '%r' % (e,)}, 500)
        return True
    return False
