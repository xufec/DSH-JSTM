# -*- coding: utf-8 -*-
"""role.storage —— 角色主表读写 + 四件套 build_*（Phase 2 step 2）。

设计依据：phase2_design.md §二 role/、§4.1。
迁移来源（mock_server.py 当前行号）：
  _DB_COLS                 L4227–4231
  db_get_role / db_save_role              L4961–4991
  _DB_TO_SC / _sc_to_db_updates / role_state   L5055–5122
  ROLE_DEFAULTS            L1698–1730
  build_10302 / build_10303 / build_10301      L5151–5314

build_* 读 runtime.CUR_VER 做多版本分流（与现状逐字节一致）。
"""

import os
import time
import sqlite3

from core import runtime
from persistence.db import db_conn, db_release, DB_PATH
from protocol.frame import w_u8, w_u16, w_u32, w_str
from currency.service import db_get_assets
from level.service import level_need, level_next_total, level_attr_point
from attribute.service import ATTR_DEFAULTS, ATTR_FIELDS, db_get_attr, db_save_attr

log = runtime.log

_DB_COLS = ['rid', 'uid', 'name', 'level', 'career', 'sex', 'exp',
            'hp', 'max_hp', 'mp', 'max_mp', 'gold', 'gold_acc', 'diamond', 'coin',
            'scene_id', 'x', 'y', 'dir', 'vip_level', 'title', 'status',
            'srv_id',            # ★ 2026-10-17：角色归属区服（三区隔离的落点）
            'updated_at']

ROLE_DEFAULTS = {
    # 身份
    # ★ PHASE 2.25（用户报障「头像空白」）：`face_id` 默认 0 ⇒ `SC_10301` 发 0
    #   ⇒ 客户端**没有头像可渲染** ⇒ 头像空白。
    #   真值来源：`server/cfg/config_role_face.json` 的 `RoleFace`（14 项，键 **100..113**，
    #   每项 `{animate: 62xxx}`）⇒ 取**首个有效头像 id 100** 作为默认。
    #   ⚠ 本服未实现"换头像"（`10327`），故用固定默认值；**替换点就在这一行**。
    #   （`head_bid` 头像框保持 0：头像框本属"未获得"状态，**不编造**。
    #     真值表见 `config_head_surface.json` 的 `HeadSurface`，键 10107..10114。）
    'rid': 1001, 'srv_id': '1', 'name': 'DSH', 'lev': 1, 'sex': 0,
    'career': 1, 'face_id': 100,
    # VIP
    'is_vip': 0, 'vip_lev': 0, 'vip_exp': 0,
    # 称号
    'cur_title': 0, 'ntm_title': 0,
    # 公会
    'gid': 0, 'gsrv_id': '', 'position': 0, 'gname': '',
    # 移动/容量
    'mspd': 100,
    'volume': 0, 'store_volume': 0, 'store_partner_volume': 0,
    'volume_open': 0, 'store_volume_open': 0, 'store_partner_volume_open': 0,
    # 经验 / 点数
    'exp': 0, 'exp_max': 100, 'exp_total_nextlev': 100,
    'attr_point': 0, 'profit_exp': 0,
    # 资产（SC_10302）
    'gold': 0, 'gold_acc': 0, 'diamond': 0,
    'coin': 0, 'sinew': 0, 'experience': 0, 'coupon': 0, 'vitality': 0,
    'guild_contrib': 0, 'practice_exp': 0, 'tower_cent': 0, 'arena_cent': 0,
    'power': 0,
    # 婚姻 / 结拜
    'marry_state': 0, 'spouse_name': '', 'spouse_rid': 0, 'spouse_srv_id': '',
    'insight_status': 0, 'jid': 0, 'j_srv_id': '', 'jlev': 0, 'j_title': '',
    # 外观
    'head_bid': 0, 'chat_bubble': 0,
    # 场景（持久化用）
    'scene_id': 10001, 'x': 30, 'y': 30, 'dir': 0,
}

# DB 列名 ↔ SC 字段名映射
_DB_TO_SC = {'level': 'lev', 'vip_level': 'vip_lev', 'x': 'x', 'y': 'y',
             'dir': 'dir', 'scene_id': 'scene_id', 'name': 'name',
             'career': 'career', 'sex': 'sex', 'exp': 'exp', 'gold': 'gold',
             'gold_acc': 'gold_acc', 'title': 'cur_title', 'status': 'status',
             'uid': 'uid', 'diamond': 'diamond', 'coin': 'coin', 'hp': 'hp', 'max_hp': 'max_hp',
             'mp': 'mp', 'max_mp': 'max_mp',
             # ★ 2026-10-17：让 DB 里的真实区服覆盖 ROLE_DEFAULTS 的 '1'
             #   ⇒ SC_10301/10302/10303 等下发出去的 srv_id 与实际所在区一致。
             'srv_id': 'srv_id'}


def db_get_role(rid):
    """读一行；不存在返回 None。"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT * FROM roles WHERE rid=?', (rid,)).fetchone()
        db_release(con)
        return dict(row) if row else None
    except Exception as e:
        log('tcp.log', '  !! db_get_role failed: %r' % (e,))
        return None


def db_save_role(rid, **kw):
    """按字段增量保存（INSERT OR IGNORE 建行 → UPDATE 指定字段）。"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO roles (rid) VALUES (?)', (rid,))
        kw['updated_at'] = int(time.time())
        cols = [c for c in kw if c in _DB_COLS]
        if cols:
            con.execute('UPDATE roles SET %s WHERE rid=?' %
                        ','.join('%s=?' % c for c in cols),
                        [kw[c] for c in cols] + [rid])
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_save_role failed: %r' % (e,))
        return False


def _sc_to_db_updates(st):
    """把角色状态里"应持久化"的字段整理成 DB 列 → 值。

    ★ S3-A 任务1（diamond/gold 双路收敛）：gold/diamond 权威已统一到
      role_assets 表（role_state 合并时 role_assets 覆盖 roles 同名列）。
      这里**停止写** roles.gold / roles.diamond（历史双写残留，曾漂移
      roles.gold=1800140 vs assets.gold=1800041、roles.diamond=0 vs
      assets.diamond=100000）。exp/coin 维持双写同步（与 add_role_exp 一致），
      gold_acc 无 role_assets 行、仅 roles 列，保留。
    """
    return {
        'name': st.get('name', ''),
        'level': st.get('lev', 1),
        'career': st.get('career', 1),
        'sex': st.get('sex', 0),
        'exp': st.get('exp', 0),
        'gold_acc': st.get('gold_acc', 0),
        'coin': st.get('coin', 0),
        'scene_id': st.get('scene_id', 10001),
        'x': st.get('x', 0),
        'y': st.get('y', 0),
        'dir': st.get('dir', 0),
        'vip_level': st.get('vip_lev', 0),
        'title': str(st.get('cur_title', 0)),
        'status': st.get('status', 0),
        # ★ 2026-10-17：role_state() 的"种子行"也必须带区服 —— 否则会写出
        #   srv_id 为 NULL 的角色行（既不属于任何区，也不被任何区列出来）。
        'srv_id': str(st.get('srv_id') or '1'),
    }


def role_state(cfg):
    """把 默认值 + 配置 + 数据库 合并成一份完整角色状态（原 mock_server L5085）。"""
    st = dict(ROLE_DEFAULTS)
    st.update(cfg.get('role', {}) or {})
    rid = st.get('rid', 1001)

    row = db_get_role(rid)
    if row is None:
        db_save_role(rid, **_sc_to_db_updates(st))
        row = db_get_role(rid)
        log('tcp.log', '  ** role %s seeded into DB from config' % rid)
    if row:
        for col, sc in _DB_TO_SC.items():
            v = row.get(col)
            if v is not None:
                st[sc] = v
    for name, amount in db_get_assets(rid).items():
        st[name] = amount
    try:
        _lev = int(st.get('lev') or 1)
        st['exp_max'] = level_need(_lev) or 0
        st['exp_total_nextlev'] = level_next_total(_lev)
        st['attr_point'] = level_attr_point(_lev)
    except Exception as e:
        log('tcp.log', '  !! role_state level fields failed: %r' % (e,))
    # ★ R100：修炼经验（SC_10302/10303/10304 的 practice_exp）—— 与 SC_10621 skill_list **同源**
    #   （bid=10822 抗控修炼的 exp）。DB 里没有 practice_exp 这份资产，role_attr 也无此列
    #   ⇒ 不在此覆盖就恒为 ROLE_DEFAULTS 的 0，UI「拥有」栏永远空白（缺口 #5 的根因）。
    #   [INFERENCE] practice_exp ↔ 拥有栏 的对应关系仍待实机渲染回证；数值来源是配置真值。
    for _sk in (cfg.get('skills') or []):
        if int(_sk.get('bid', 0)) == 10822:
            st['practice_exp'] = int(_sk.get('exp', 0))
            break
    return st


def build_10302(st):
    """SC_10302 角色资产/经验刷新（原 mock_server L5151）。"""
    b = w_u16(st.get('lev', 1))
    for k in ('exp', 'gold', 'gold_acc', 'coin', 'sinew', 'experience', 'coupon',
              'vitality', 'guild_contrib', 'practice_exp', 'tower_cent',
              'arena_cent', 'integral', 'cash_coupon', 'dan_point',
              'guild_active', 'marriage', 'course', 'vip_exp', 'lingshi',
              'peak_point', 'black_soul', 'lottery_point', 'boss_point',
              'partner_shenqi_point', 'jiebai_cent', 'rune_exp', 'rune_chip'):
        b += w_u32(int(st.get(k) or 0))
    if runtime.CUR_VER != '1.3.0':
        b += w_u32(int(st.get('diamond') or 0))
        b += w_u32(int(st.get('rainbow_diamond') or 0))
    return b


def build_10303(role, skills=None, attr=None):
    """SC_10303 角色属性（原 mock_server L5190）。"""
    a = dict(ATTR_DEFAULTS)
    a.update(attr or {})
    rid = role.get('rid', 1001)
    db_a = db_get_attr(rid)
    if not db_a:
        db_save_attr(rid, a)
        db_a = db_get_attr(rid)
    if db_a:
        a.update(db_a)

    b = b''
    b += w_u32(role.get('rid', 1001))
    b += w_str(role.get('srv_id', '1'))
    b += w_str(role.get('name', 'DSH'))
    b += w_u16(role.get('lev', 1))
    b += w_u8(role.get('is_vip', 0))
    b += w_u8(role.get('vip_lev', 0))
    b += w_u8(role.get('sex', 0))
    b += w_u16(role.get('career', 1))
    b += w_u8(role.get('volume', 0))
    b += w_u8(role.get('store_volume', 0))
    b += w_u8(role.get('store_partner_volume', 0))
    b += w_u8(role.get('volume_open', 0))
    b += w_u8(role.get('store_volume_open', 0))
    b += w_u8(role.get('store_partner_volume_open', 0))
    b += w_u16(role.get('attr_point', 0))
    sk = skills or []
    b += w_u16(len(sk))
    for s in sk:
        b += w_u32(s.get('bid', 0) if isinstance(s, dict) else int(s))
    # [P45-A D1] 战力回包接线：用真实战力覆盖 config.json 硬编码 power:0。
    # 与 10304/10306 同一算法（role_power），从本函数已合并的本地 attr 字典 a 算，
    # 保证同帧 power 与 attr 表自洽。# INFERENCE: 九维分项未接，总战力=calc_power(a)。
    from attribute.service import role_power as _role_power
    try:
        role = dict(role, power=int(_role_power({'role': {'rid': rid}, 'role_attrs': a}) or 0))
    except Exception:
        pass
    for k in ('power', 'exp', 'gold', 'coin', 'gold_acc', 'sinew', 'experience',
              'coupon', 'vitality', 'guild_contrib', 'practice_exp',
              'tower_cent', 'arena_cent'):
        b += w_u32(role.get(k, 0))
    b += w_u16(1)
    for name, t in ATTR_FIELDS:
        v = a.get(name, 0)
        b += w_u16(v) if t == 'u16' else w_u32(v)
    b += w_u16(role.get('mspd', 100))
    b += w_u16(0)
    if runtime.CUR_VER != '1.3.0':
        b += w_u32(role.get('vip_exp', 0))
        b += w_str(role.get('jiebai_title', ''))
        b += w_u8(role.get('jiebai_lev', 0))
    return b


def build_10301(role, skills=None):
    """SC_10301 角色基础信息（原 mock_server L5254）。"""
    b = b''
    b += w_u32(role.get('rid', 1001))
    b += w_str(role.get('srv_id', '1'))
    b += w_str(role.get('name', 'DSH'))
    b += w_u16(role.get('lev', 1))
    b += w_u8(role.get('is_vip', 0))
    b += w_u8(role.get('vip_lev', 0))
    b += w_u8(role.get('sex', 0))
    b += w_u16(role.get('career', 1))
    b += w_u16(role.get('face_id', 0))
    b += w_u16(role.get('cur_title', 0))
    b += w_u32(role.get('ntm_title', 0))
    b += w_u32(role.get('gid', 0))
    b += w_str(role.get('gsrv_id', ''))
    b += w_u8(role.get('position', 0))
    b += w_str(role.get('gname', ''))
    b += w_u16(role.get('mspd', 100))
    b += w_u8(role.get('volume', 0))
    b += w_u8(role.get('store_volume', 0))
    b += w_u8(role.get('store_partner_volume', 0))
    b += w_u8(role.get('volume_open', 0))
    b += w_u8(role.get('store_volume_open', 0))
    b += w_u8(role.get('store_partner_volume_open', 0))
    b += w_u32(role.get('exp_max', 100))
    b += w_u32(role.get('exp_total_nextlev', 100))
    b += w_u16(role.get('attr_point', 0))
    b += w_u32(role.get('profit_exp', 0))
    b += w_u8(role.get('marry_state', 0))
    b += w_str(role.get('spouse_name', ''))
    if runtime.CUR_VER != '1.3.0':
        b += w_u32(role.get('head_bid', 0))
        b += w_u32(role.get('chat_bubble', 0))
    sk = skills or []
    b += w_u16(len(sk))
    for s in sk:
        b += w_u32(s.get('bid', 0) if isinstance(s, dict) else int(s))
    b += w_u16(0)
    b += w_u16(0)
    b += w_u16(0)
    b += w_u16(0)
    b += w_u16(0)
    b += w_u16(0)
    b += w_u32(role.get('spouse_rid', 0))
    b += w_str(role.get('spouse_srv_id', ''))
    b += w_u8(role.get('insight_status', 0))
    b += w_u32(role.get('jid', 0))
    b += w_str(role.get('j_srv_id', ''))
    b += w_u8(role.get('jlev', 0))
    b += w_str(role.get('j_title', ''))
    b += w_u8(role.get('vip_diamond', 0))
    return b
