# -*- coding: utf-8 -*-
"""friend.service —— 好友系统（13300 列表 / 13321 申请列表 / 13303 申请加友 / 13305 应答）。

★ 证据等级：
  · 帧结构：**CONFIRMED** —— `protocol/fields.json`；好友元素是**统一 15 字段**：
      {rid,srv_id,name,sex,lev,career,power,login_time,face_id,is_online,
       group_id,intimacy,grid,gsrv_id,guild_name}
    （`13300.friend_list` / `13321.request_list` / `13322.add_list` **同一结构**）
  · 命令语义：**CONFIRMED** —— `cmd_table`（13303「A 向服务端请求想加 B 为好友」、
    13305「B 告诉服务端，加或不加 A 为好友」）
  · **为何要做**：`13300`/`13321` 客户端真实调用 **58 / 57 次**，原实现走通用编码器 ⇒ **恒回空表**；
    HANDOFF"已闭环"清单里**没有社交/好友**。见 `analysis/extraction/dead_protocols_and_traffic.md` §5.4。
  · 表结构 `role_friend` / `role_friend_req`：**INFERENCE**（原版表不可取证）。
"""

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log


def db_friend_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_friend (
        rid INTEGER, friend_rid INTEGER, srv_id TEXT, ctime INTEGER,
        PRIMARY KEY (rid, friend_rid))""")
    con.execute("""CREATE TABLE IF NOT EXISTS role_friend_req (
        to_rid INTEGER, from_rid INTEGER, srv_id TEXT, ctime INTEGER,
        PRIMARY KEY (to_rid, from_rid))""")
    con.commit()
    db_release(con)


def profile(rid):
    """好友元素 15 字段（真值取自 `roles` + 战力）。取不到 ⇒ 空名 + 0（不编造）。"""
    try:
        from role.storage import db_get_role
        r = db_get_role(rid) or {}
    except Exception:
        r = {}
    try:
        from mock_server import role_power_of
        pw = int(role_power_of(rid) or 0)
    except Exception:
        pw = 0
    return {
        'rid': int(rid), 'srv_id': '1', 'name': str(r.get('name') or ''),
        'sex': int(r.get('sex') or 0) & 0xff, 'lev': int(r.get('level') or 1) & 0xffff,
        'career': int(r.get('career') or 1) & 0xffff, 'power': pw & 0xffffffff,
        'login_time': int(r.get('updated_at') or 0) & 0xffffffff,
        'face_id': 0, 'is_online': 1, 'group_id': 0, 'intimacy': 0, 'grid': 0,
        'gsrv_id': '1', 'guild_name': '',
    }


def friends(rid):
    db_friend_init()
    con = db_conn()
    rows = con.execute('SELECT friend_rid FROM role_friend WHERE rid=? ORDER BY ctime',
                       (int(rid),)).fetchall()
    db_release(con)
    return [profile(r[0]) for r in rows]


def requests(rid):
    db_friend_init()
    con = db_conn()
    rows = con.execute('SELECT from_rid FROM role_friend_req WHERE to_rid=? ORDER BY ctime',
                       (int(rid),)).fetchall()
    db_release(con)
    return [profile(r[0]) for r in rows]


def add_request(from_rid, to_rid, srv_id='1'):
    """A 申请加 B。返回 (ok, msg)。"""
    if int(from_rid) == int(to_rid):
        return False, '不能加自己'
    try:
        from role.storage import db_get_role
        if not db_get_role(to_rid):
            return False, '目标不存在'
    except Exception:
        pass
    db_friend_init()
    con = db_conn()
    if con.execute('SELECT 1 FROM role_friend WHERE rid=? AND friend_rid=?',
                   (int(from_rid), int(to_rid))).fetchone():
        db_release(con)
        return False, '已经是好友'
    con.execute('INSERT OR REPLACE INTO role_friend_req VALUES (?,?,?,?)',
                (int(to_rid), int(from_rid), str(srv_id or '1'), 0))
    con.commit()
    db_release(con)
    log('tcp.log', '  ** 好友申请 %d -> %d' % (from_rid, to_rid))
    return True, ''


def answer(to_rid, from_rid, agreed, srv_id='1'):
    """B 应答 A 的申请。agreed=1 建立双向好友；agreed=0 仅撤销申请。返回 (ok,msg)。"""
    db_friend_init()
    con = db_conn()
    row = con.execute('SELECT 1 FROM role_friend_req WHERE to_rid=? AND from_rid=?',
                      (int(to_rid), int(from_rid))).fetchone()
    con.execute('DELETE FROM role_friend_req WHERE to_rid=? AND from_rid=?',
                (int(to_rid), int(from_rid)))
    if agreed and row:
        con.execute('INSERT OR REPLACE INTO role_friend VALUES (?,?,?,0)',
                    (int(to_rid), int(from_rid), str(srv_id or '1')))
        con.execute('INSERT OR REPLACE INTO role_friend VALUES (?,?,?,0)',
                    (int(from_rid), int(to_rid), str(srv_id or '1')))
    con.commit()
    db_release(con)
    log('tcp.log', '  ** 好友应答 to=%d from=%d agreed=%s' % (to_rid, from_rid, agreed))
    return True, ''


def del_friend(rid, friend_rid):
    """主动删友（**双向**删除）。返回 (ok,msg)。"""
    db_friend_init()
    con = db_conn()
    con.execute('DELETE FROM role_friend WHERE rid=? AND friend_rid=?',
                (int(rid), int(friend_rid)))
    con.execute('DELETE FROM role_friend WHERE rid=? AND friend_rid=?',
                (int(friend_rid), int(rid)))
    con.commit()
    db_release(con)
    log('tcp.log', '  ** 好友删除 rid=%d <-> %d' % (rid, friend_rid))
    return True, ''


def clear_requests(rid):
    """一键清空好友申请。返回 (ok,msg)。"""
    db_friend_init()
    con = db_conn()
    con.execute('DELETE FROM role_friend_req WHERE to_rid=?', (int(rid),))
    con.commit()
    db_release(con)
    log('tcp.log', '  ** 好友申请清空 rid=%d' % rid)
    return True, ''
