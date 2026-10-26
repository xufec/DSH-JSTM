# -*- coding: utf-8 -*-
"""item.service —— 物品配置与有效性校验（Phase 2c）。

迁移来源（mock_server.py）：
  ITEM_CFG_PATH / _ITEM_IDS   L1816–1818
  item_ids                    L1821–1839
  item_cfg / _ITEM_CFG        L5624 / L5650–5662
  item_exists / item_name     L5665–5679
  is_valid_item               L1894–1917

只依赖 core.runtime(log) + json。无循环 import。
"""

import os
import json

from core import runtime

log = runtime.log

ITEM_CFG_PATH = os.path.join(runtime.HERE, 'item_config.json')
_ITEM_CFG = None
_ITEM_IDS = None


def item_ids():
    """真实物品表的 bid 集合（背包空白根因防护，见原注释）。"""
    global _ITEM_IDS
    if _ITEM_IDS is None:
        try:
            with open(ITEM_CFG_PATH, encoding='utf-8') as f:
                _ITEM_IDS = set(json.load(f).keys())
            log('server.log', 'item table loaded: %d 条' % len(_ITEM_IDS))
        except Exception as e:
            _ITEM_IDS = set()
            log('server.log', '!! item table load failed: %r（将不过滤）' % (e,))
    return _ITEM_IDS


def item_cfg():
    """返回物品表 dict（真实物品表）。"""
    global _ITEM_CFG
    if _ITEM_CFG is None:
        try:
            with open(ITEM_CFG_PATH, encoding='utf-8') as f:
                _ITEM_CFG = json.load(f)
            log('server.log', 'item config loaded: %d 条 <- %s'
                % (len(_ITEM_CFG), ITEM_CFG_PATH))
        except Exception as e:
            log('server.log', '!! item config load failed: %r（将拒绝一切掉落）' % (e,))
            _ITEM_CFG = {}
    return _ITEM_CFG


def item_exists(bid):
    return str(int(bid)) in item_cfg()


def item_name(bid):
    a = item_cfg().get(str(int(bid)))
    if isinstance(a, dict):
        n = a.get('name')
        return n if isinstance(n, str) else ''
    if isinstance(a, list) and len(a) > 2 and isinstance(a[2], str):
        return a[2]
    return ''


def is_valid_item(bid):
    """bid 是否真实可用（必须存在且带真实 type，空记录不算）。表加载失败时不过滤。"""
    ids = item_ids()
    if not ids:
        return True
    key = str(int(bid))
    if key not in ids:
        return False
    v = item_cfg().get(key)
    if isinstance(v, dict):
        return v.get('type') is not None
    if isinstance(v, list):
        return len(v) > 3 and v[3] is not None
    return False
