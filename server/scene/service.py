# -*- coding: utf-8 -*-
"""scene.service —— 场景函数群（P3deep 整群下沉破环）。
下沉自 mock_server.py：static_mons/quest_spawn/map_cfg/scene_elems/scene_npcs/scene_mons/
map_def_xy/guaji_spots/guaji_spot_for_lev。打破 scene_mons ↔ guaji_spot_for_lev 环依赖。
"""
import os
import json

from core import runtime
from task.service import mission_def as mon_def, mission_cfg
from role.storage import role_state

log = runtime.log

HERE = os.path.dirname(os.path.abspath(__file__))

# QuestSpawn 惰性
try:
    from quest_spawn import QuestSpawn
except Exception:
    QuestSpawn = None
_QUEST_SPAWN = None

_GUAJI = None
_MAP_DEF = None
_MAP_CFG = None
_MAP_CFG_PATH = os.path.join(HERE, '..', '..', 'analysis', '1.4.9', 'task', 'config_map.json')


def static_mons(cfg, scene_id):
    """配置里写死的场景怪物（测试摆位）。[P3deep-migrated]"""
    out = []
    for i, m in enumerate(cfg.get('mons') or []):
        bid = int(m.get('bid') or m.get('id') or 0)
        if not bid:
            continue
        d = mon_def(bid)
        out.append({
            'id': int(m.get('id') or bid),
            'bid': bid,
            'type': int(m.get('type', 0)),
            'name': m.get('name') or d.get('name') or ('mon%d' % bid),
            'realm': int(m.get('realm', 0)),
            'mspd': int(m.get('mspd', 100)),
            'x': int(m.get('x', 30) if m.get('x') is not None else 30),
            'y': int(m.get('y', 30) if m.get('y') is not None else 30),
            'dir': int(m.get('dir', 0)),
            'res_id': m.get('res_id') or d.get('res_id') or '',
            'status': int(m.get('status', 0)),
            'source': m.get('source') or 'emulated',
            'why': m.get('why') or 'config.mons[%d]' % i,
        })
    return out


def quest_spawn():
    """惰性构造 QuestSpawn（只读 APK 提取物）。[P3deep-migrated]"""
    global _QUEST_SPAWN
    if _QUEST_SPAWN is None:
        _QUEST_SPAWN = QuestSpawn(mission_cfg()) if QuestSpawn else False
    return _QUEST_SPAWN or None


def map_cfg():
    """Config.Map 全量表（只读快照）。[P3deep-migrated]"""
    global _MAP_CFG
    if _MAP_CFG is None:
        try:
            with open(_MAP_CFG_PATH, encoding='utf-8') as f:
                _MAP_CFG = json.load(f)
        except Exception as e:
            log('tcp.log', '  !! 读取 config_map.json 失败: %r' % (e,))
            _MAP_CFG = {}
    return _MAP_CFG


def scene_elems(scene_id):
    """SCMapGird_10201.elems 场景元素。[P3deep-migrated]"""
    scene = (map_cfg() or {}).get(str(scene_id)) or {}
    out = []
    for eid, e in (scene.get('elems') or {}).items():
        out.append({'id': int(eid), 'bid': int(eid), 'type': 0, 'sub_type': 0,
                    'name': '', 'x': int(e.get('x') or 0), 'y': int(e.get('y') or 0),
                    'res_id': ''})
    return out


def scene_npcs(cfg, scene_id):
    """按场景取 NPC 表。[P3deep-migrated]"""
    scene = (map_cfg() or {}).get(str(scene_id)) or {}
    tbl = scene.get('npcs') or {}
    if not tbl:
        return list(cfg.get('npcs', []))
    return [{'id': int(b), 'bid': int(b), 'type': 2,
             'x': int(v.get('x') or 0), 'y': int(v.get('y') or 0), 'name': ''}
            for b, v in tbl.items()]


def scene_mons(cfg, scene_id):
    """按场景取怪表（含挂机怪补齐）。[P3deep-migrated]"""
    scene = (map_cfg() or {}).get(str(scene_id)) or {}
    out = []
    for mid, m in (scene.get('mons') or {}).items():
        bid = int(mid)
        d = mon_def(bid)
        out.append({'id': bid, 'bid': bid, 'type': 0,
                    'name': d.get('name') or '', 'realm': 0, 'mspd': 100,
                    'x': int(m.get('x') or 0), 'y': int(m.get('y') or 0), 'dir': 0,
                    'res_id': d.get('res_id') or '', 'status': 0,
                    'source': 'config_map', 'why': 'Config.Map[%s].mons' % scene_id})
    _spawn_bid = int((cfg.get('spawn') or {}).get('bid') or 10001)
    if int(scene_id) == _spawn_bid:
        have = {m['id'] for m in out}
        for m in static_mons(cfg, scene_id):
            if m['id'] not in have:
                out.append(m)
    elif not scene:
        out = static_mons(cfg, scene_id)
    try:
        _lev9 = int((role_state(cfg) or {}).get('lev')
                    or (cfg.get('role') or {}).get('lev') or 1)
        _spot9 = guaji_spot_for_lev(_lev9) or {}
        if int(_spot9.get('map_bid') or 0) == int(scene_id) and _spot9.get('mon_bid'):
            _mb9 = int(_spot9['mon_bid'])
            if not any(int(m.get('bid') or 0) == _mb9 for m in out):
                _x9, _y9 = map_def_xy(int(scene_id))
                _d9 = mon_def(_mb9)
                out.append({
                    'id': _mb9, 'bid': _mb9, 'type': 0,
                    'name': _d9.get('name') or '', 'realm': 0, 'mspd': 100,
                    'x': int(_x9 or 0), 'y': int(_y9 or 0), 'dir': 0,
                    'res_id': _d9.get('res_id') or '', 'status': 0,
                    'source': 'guaji', 'why': 'R77 挂机图等级段的怪（与 20002 共用）'})
    except Exception:
        pass
    return out


def guaji_spots():
    """挂机点表。[P3deep-migrated]"""
    global _GUAJI
    if _GUAJI is None:
        try:
            with open(os.path.join(HERE, '..', '_guaji.json'), encoding='utf-8') as f:
                _GUAJI = json.load(f).get('spots') or []
        except Exception as e:
            log('tcp.log', '  !! 读取 _guaji.json 失败: %r' % (e,))
            _GUAJI = []
    return _GUAJI


def map_def_xy(map_bid):
    """地图默认出生点。[P3deep-migrated]"""
    global _MAP_DEF
    if _MAP_DEF is None:
        _MAP_DEF = {}
        try:
            p = os.path.join(HERE, '..', '..', 'analysis', '1.4.9', 'task',
                             'config_map.json')
            with open(p, encoding='utf-8') as f:
                for k, v in (json.load(f) or {}).items():
                    if isinstance(v, dict):
                        _MAP_DEF[str(k)] = (int(v.get('def_x') or 0),
                                            int(v.get('def_y') or 0))
        except Exception as e:
            log('tcp.log', '  !! 读取 config_map 失败: %r' % (e,))
    return _MAP_DEF.get(str(map_bid), (0, 0))


def guaji_spot_for_lev(lev):
    """按等级段挑挂机点。[P3deep-migrated]"""
    for s in sorted(guaji_spots(), key=lambda x: int(x.get('lev_l') or 0)):
        if int(s.get('lev_l') or 0) <= int(lev) <= int(s.get('lev_r') or 0):
            return s
    return None
