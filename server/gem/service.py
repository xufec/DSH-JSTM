# -*- coding: utf-8 -*-
"""gem.service —— 宝石镶嵌/合成服务（Phase 7；①c G3）。

①c G3 CONFIRMED：config_item_fuse.json ItemRoleFuse（192 条）= 合成消耗。
  合成 bid -> {coin:2000~4000, rate:100(=100%), fuse:{1:[null,out_bid,num]}}。
镶嵌属性加成：config_item.json 无 atk/def 字段、ItemJewel 17 条 null ⇒ UNKNOWN 占位。
"""

import json
import os

from core import runtime

log = runtime.log

_FUSE = os.path.join(runtime.HERE, 'cfg', 'config_item_fuse.json')
_fuse = {}
_JATTR = os.path.join(runtime.HERE, 'cfg', 'config_item_misc_attr.json')
_jewel_by_slots = {}


def _load_jewel_attr():
    """G3 CONFIRMED：config_item_misc_attr.ItemMiscAttrJewel 总属性表（按槽位数）。
    返回 {slot_n: {attr_name: value}}，slot_n=12/18/24。整套满槽总属性（非单颗）。"""
    global _jewel_by_slots
    if _jewel_by_slots:
        return _jewel_by_slots
    try:
        with open(_JATTR, encoding='utf-8') as f:
            rows = json.load(f).get('ItemMiscAttrJewel') or {}
        items = rows if isinstance(rows, list) else list(rows.values())
        for it in items:
            if not isinstance(it, dict):
                continue
            # it 形如 {"12": {"array":[], "hash":{"attr":{...}}}}
            for slot_k, wrap in it.items():
                if str(slot_k) not in ('12', '18', '24'):
                    continue
                h = (wrap or {}).get('hash') or {}
                attr = h.get('attr') or {}
                out = {}
                for _k, spec in attr.items():
                    if isinstance(spec, list) and len(spec) >= 3:
                        out[spec[1]] = int(spec[2])
                # 同档多类宝石取累加（atk/hp 类叠加）
                prev = _jewel_by_slots.get(int(slot_k), {})
                for k2, v2 in out.items():
                    prev[k2] = prev.get(k2, 0) + v2
                _jewel_by_slots[int(slot_k)] = prev
                break
    except Exception as e:
        log('server.log', '!! jewel attr load failed: %r' % (e,))
        _jewel_by_slots = {}
    return _jewel_by_slots


def jewel_attr_by_slots(slots):
    """按已镶嵌槽位数取总属性加成（CONFIRMED 总表）。"""
    t = _load_jewel_attr()
    if not t:
        return {}
    # 取不超过 slots 的最高档
    avail = sorted(k for k in t if k <= int(slots))
    if not avail:
        return {}
    return t[avail[-1]]


def _load():
    global _fuse
    if _fuse:
        return _fuse
    try:
        with open(_FUSE, encoding='utf-8') as f:
            d = (json.load(f).get('ItemRoleFuse') or {})
        for src_bid, levels in d.items():
            lv1 = ((levels or {}).get('1') or {}).get('hash') or {}
            fuse_out = lv1.get('fuse') or {}
            out = None
            for _k, spec in fuse_out.items():
                if isinstance(spec, list) and len(spec) >= 3:
                    out = (int(spec[1]), int(spec[2]))
                    break
            _fuse[int(src_bid)] = {'coin': int(lv1.get('coin') or 0),
                                   'rate': int(lv1.get('rate') or 100),
                                   'out': out}
    except Exception as e:
        log('server.log', '!! item_fuse load failed: %r' % (e,))
        _fuse = {}
    return _fuse


def fuse_cost(src_bid):
    """合成消耗（CONFIRMED）：返回 {coin, rate, out:(bid,num)}；不可合成 ⇒ None。"""
    return _load().get(int(src_bid))


def gem_attrs(gem_bid):
    """取宝石属性加成（# UNKNOWN：镶嵌加成无配置表，占位空）。"""
    return {}
