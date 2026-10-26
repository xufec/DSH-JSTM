# -*- coding: utf-8 -*-
"""persistence.db —— SQLite 连接池 + db_init（Phase 2 step 1：从 mock_server.py 搬入）。

设计依据：analysis/phase2_design.md §二 persistence/、§5.2、§九 风险 3。

迁移来源（mock_server.py 当前行号）：
  DB_PATH            L4212
  _DB_LOCAL          L4232
  db_conn()          L4235–4242
  db_release(con)    L4245–4254
  db_init()          L4289–4337（★ 保留全部 6 张 CREATE TABLE，行为不变）
  STATE_DIR          L5343

★ db_init 只建 roles/accounts/role_attr/missions/role_assets/mall_bought 6 张主表；
  其余 49 张表仍由 main() 里各 db_*_init() 零散补建（本轮不改，防 schema 漂移 ——
  设计 §九 风险 3）。本模块**不**去集中那些 init，避免漏搬导致新库起不来。
"""

import os
import sqlite3
import threading

from core import runtime

# server/state/roles.db（原 mock_server.L4212，逐字同路径）。
DB_PATH = os.path.join(runtime.HERE, 'state', 'roles.db')
# server/state（角色态落盘目录，原 mock_server.L5343）。
STATE_DIR = os.path.join(runtime.HERE, 'state')

# SQLite 连接复用（线程本地）—— 原 L4220–4231 注释随代码搬走。
#   依据：cProfile 显示一次 SC_12400 请求里 sqlite3.connect 被调 6 次，占该请求耗时 37%。
#   服务端多线程 ⇒ 每线程一个连接。安全：
#     1. db_conn() 每次复位 row_factory，防 sqlite3.Row 泄漏；
#     2. db_release() 不关闭连接，仅回滚未提交事务，防脏事务残留。
_DB_LOCAL = threading.local()


def db_conn():
    """取本线程的共用 SQLite 连接（不存在则建）。"""
    con = getattr(_DB_LOCAL, 'con', None)
    if con is None:
        con = sqlite3.connect(DB_PATH, timeout=10)
        _DB_LOCAL.con = con
    con.row_factory = None          # ★ 每次交付复位，防设置泄漏
    return con


def db_release(con=None):
    """“释放”连接：回滚未提交事务，连接留在线程本地复用。"""
    c = con if con is not None else getattr(_DB_LOCAL, 'con', None)
    if c is None:
        return
    try:
        if c.in_transaction:
            c.rollback()
    except Exception:
        pass


def _ensure_column(con, table, column, decl, backfill=None):
    """幂等加列（老库迁移用）。

    为什么需要：`CREATE TABLE IF NOT EXISTS` 对**已存在**的表完全不生效，
    所以给旧库补列只能走 ALTER TABLE。用 PRAGMA 先查，避免重复 ALTER 报错。
    backfill: 可选 SQL 片段（在加列之后、仅当本次真的加了列时执行一次）。
    """
    try:
        cols = [r[1] for r in con.execute('PRAGMA table_info(%s)' % table)]
        if column in cols:
            return False
        con.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table, column, decl))
        if backfill:
            con.execute(backfill)
        return True
    except Exception as e:
        print('!! _ensure_column %s.%s failed: %r' % (table, column, e))
        return False


def db_init():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS roles (
        rid INTEGER PRIMARY KEY,
        uid TEXT, name TEXT, level INTEGER, career INTEGER, sex INTEGER,
        exp INTEGER, hp INTEGER, max_hp INTEGER, mp INTEGER, max_mp INTEGER,
        gold INTEGER, gold_acc INTEGER, diamond INTEGER, coin INTEGER,
        scene_id INTEGER, x INTEGER, y INTEGER, dir INTEGER,
        vip_level INTEGER, title TEXT, status INTEGER, updated_at INTEGER)""")
    # ★★ R44：账号表（最小）。
    #   uid 取自 CS_1110.args 里的 account —— 真机实测该表 10 对键值。
    #   ⚠ 协议里没有密码字段（原版走 token + 设备标识）⇒ 不做 password 列（YAGNI）。
    con.execute("""CREATE TABLE IF NOT EXISTS accounts (
        uid TEXT PRIMARY KEY, name TEXT, create_ts INTEGER)""")
    # ★★ 2026-10-17「三区 + 账号系统」迁移（全部**加列**，不动既有数据）：
    #   ① roles.srv_id —— 角色归属区服。之前是隐式的：代码里到处写死 '1'，
    #      于是"一服建角、二三服都看得见"。旧库的历史角色一律回填 '1'（当时确实
    #      只有 1 个区，等价）。
    #   ② accounts 规范化 —— 服务端账号记录：密码哈希（首登绑定）、最近登录时间、
    #      最近区服、登录次数。原版协议没有密码字段，但客户端 UserPanel 会把
    #      **密码写进 CS_1110 的 token 字段**（见 user_panel proto：info.token =
    #      DEF_TOKEN or 密码），所以服务端收得到，可以做真正的账号鉴权。
    _ensure_column(con, 'roles', 'srv_id', 'TEXT')
    _ensure_column(con, 'accounts', 'pwd_hash', 'TEXT')
    _ensure_column(con, 'accounts', 'last_login_ts', 'INTEGER')
    _ensure_column(con, 'accounts', 'last_srv_id', 'TEXT')
    _ensure_column(con, 'accounts', 'login_count', 'INTEGER')
    # 老库补登：把无主角色挂到默认账号，避免既有玩家角色变孤儿（幂等）
    con.execute("UPDATE roles SET uid=? WHERE uid IS NULL OR uid=''", (runtime.DEFAULT_UID,))
    # ★ 同款补登（**每次启动都跑**，不只加列那一次）：srv_id 为空的行既不属于任何区、
    #   也不会被任何区的角色列表列出来（"隐形角色"）。历史行 + role_state 种的行都归 1 区。
    con.execute("UPDATE roles SET srv_id='1' WHERE srv_id IS NULL OR srv_id=''")
    # Phase 4E 续：属性表（列名就用协议里的字段名，避免二次映射出错）
    con.execute("""CREATE TABLE IF NOT EXISTS role_attr (
        rid INTEGER PRIMARY KEY,
        strength INTEGER, intellect INTEGER, armor INTEGER, constiution INTEGER,
        atk_s INTEGER, atk_p INTEGER, def_s INTEGER, def_p INTEGER,
        hp_max INTEGER, atk_speed INTEGER, hit INTEGER, dodge INTEGER,
        crit INTEGER, tenacity INTEGER, red_def_s INTEGER, red_def_p INTEGER,
        atk_abs INTEGER, def_abs INTEGER, reduce INTEGER, hurt INTEGER,
        hit_rate_show INTEGER, dodge_rate_show INTEGER,
        crit_rate_show INTEGER, tenacity_rate_show INTEGER,
        updated_at INTEGER)""")
    # Phase 5J：任务状态表（每角色每任务一行）
    con.execute("""CREATE TABLE IF NOT EXISTS missions (
        rid INTEGER, mission_bid INTEGER,
        mission_status INTEGER, process_status INTEGER,
        target INTEGER, target_value INTEGER, value INTEGER,
        commit_num INTEGER, loop_count INTEGER, loop_num INTEGER,
        code INTEGER, accept_time INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, mission_bid))""")
    # 通用资产表：任何 AssetsEnToCode 里的资产都能存（"奖励配置驱动"的前提）
    con.execute("""CREATE TABLE IF NOT EXISTS role_assets (
        rid INTEGER, name TEXT, amount INTEGER,
        PRIMARY KEY (rid, name))""")
    # 商城购买记录：每角色每商品一行（供 SC_12831 的 has_buy_num）
    con.execute("""CREATE TABLE IF NOT EXISTS mall_bought (
        rid INTEGER, goods_id INTEGER, num INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, goods_id))""")
    # Phase 2c：发奖幂等日志（reward.grant 统一入口）
    con.execute("""CREATE TABLE IF NOT EXISTS reward_log (
        rid INTEGER, reference_id TEXT, source TEXT, granted_ts INTEGER,
        PRIMARY KEY (rid, reference_id))""")
    con.commit()
    db_release(con)
