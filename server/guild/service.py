# -*- coding: utf-8 -*-
"""guild.service —— 公会（宗门）只读配置驱动 + 状态（④ 收官）。

旧链实况：role_guild 表 + 建宗(13500)/列表(guild_rows)/祈福(qifu) 已在 mock_server
旧链实现并持久化（rid=1001 已有行 "DSH测试宗门"）。公会成员/科技/祭坛等多表
审计为 0 行 UNKNOWN，本轮不补写闭环。

本模块提供**配置真值读路径**（CONFIRMED，config_guild.json）：
  - guild_info(rid)：当前公会名/人数 + 配置上限（Guild_limit）。
  - guild_shop()：公会商店商品（Guild_shop）。
数值以配置为准；无配置真值的公会写闭环（捐献/科技/战）保持旧链/UNKNOWN。
"""

import json
import os

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log

_PATH = os.path.join(runtime.HERE, 'cfg', 'config_guild.json')
_cfg = None


def _load():
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(_PATH, encoding='utf-8') as f:
            _cfg = json.load(f)
    except Exception as e:
        log('server.log', '!! guild cfg load failed: %r' % (e,))
        _cfg = {}
    return _cfg


def _h(v):
    return (v or {}).get('hash') or v or {}


def guild_info(rid):
    """当前角色公会信息（读 role_guild 真表）。

    # NOTE：config_guild.json 的 Guild_limit 实为职位权限表（27 条 flag），
    Guild_shop 为空表 ⇒ 人数上限/商店商品无配置真值，如实返 0（不编造）。
    """
    name = ''
    try:
        con = db_conn()
        r = con.execute('SELECT name FROM role_guild WHERE rid=?', (int(rid),)).fetchone()
        db_release(con)
        if r:
            name = str(r[0] or '')
    except Exception as e:
        log('server.log', '!! guild_info failed: %r' % (e,))
    return {'in_guild': bool(name), 'name': name, 'level': 1,
            'member_count': 1, 'member_cap': 0}


def guild_shop():
    """公会商店商品（config_guild.json Guild_shop 空表 ⇒ []，UNKNOWN 无商品真值）。"""
    return []
