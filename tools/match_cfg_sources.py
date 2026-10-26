# -*- coding: utf-8 -*-
"""R201：★★ **批量匹配"命令的 SC 子表 ↔ `cfg_kconst` 配置"** —— 找可升级的命令。

★ 思路：R189 的 229 条大多"空表"（因为当时没有配置源）。
  现在有 **`cfg_kconst`（285 个配置）** ⇒ **凡是"SC 的子表名能对上配置名"的**，
  ⇒ **可以用真实条目填充** ✓

★ 匹配规则（保守）：
   命令号 → 候选配置名（`config_<语义>`），从 `SC` 的**子表名**里取词。
   例：`SC{list:table<...>}` 且命令在 `13xxx`（限购商店）⇒ 试 `config_exchange`/`config_shop*`。
★ 本脚本只**输出候选**（不自动改），供人工确认。
"""
import importlib.util
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location('g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

KC = sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, 'server', 'cfg_kconst'))
            if f.endswith('.json'))
print('  cfg_kconst: %d 个配置' % len(KC))

# 待查命令 = 所有"有 SC"的
allc = sorted(int(k) for k in sc.keys() if str(k).isdigit())
print('  有 SC 的命令: %d 条' % len(allc))

# 关键词表：SC 的子表名 → 配置名片段
KW = {
    'list': ['exchange', 'shop', 'act', 'function', 'item', 'gift', 'charge'],
    'info': ['common', 'attr', 'function'],
    'role_list': ['partner', 'friend', 'team'],
    'reward_list': ['charge', 'checkin', 'mission', 'act'],
    'item_list': ['item', 'drop', 'gift', 'shop'],
    'goods_list': ['shop', 'market'],
    'rank_list': ['rank', 'arena', 'race'],
    'guild_list': ['guild'],
    'task_list': ['mission', 'task'],
    'skill_list': ['skill'],
    'hero_list': ['hero', 'mon_data'],
    'equip_list': ['item', 'eqm'],
    'record_list': ['exchange', 'market', 'auction'],
    'box_list': ['item', 'drop'],
    'mon_list': ['mon_data', 'mon'],
    'boss_list': ['boss'],
    'scene_list': ['dungeon', 'map'],
    'partner_list': ['partner'],
    'surface_list': ['fashion'],
    'flower_list': ['flower'],
    'mine_list': ['mine'],
    'holiday_list': ['function', 'fest'],
}

hits = []
for c in allc:
    fs = sc.get(str(c)) or []
    subs = [(f.get('name'), f.get('type')) for f in fs
            if isinstance(f, dict) and (f.get('items'))]
    if not subs:
        continue
    for nm, _tp in subs:
        for kw in KW.get(nm, []):
            for cfg in KC:
                if kw in cfg:
                    hits.append((c, nm, cfg))
                    break

# 去重并统计"哪个配置被最多命令引用"
from collections import Counter
cnt = Counter(h[2] for h in hits)
print('\n  ★ 匹配到 %d 组（命令, 子表名, 配置）' % len(hits))
print('  ★ 被最多命令引用的配置 top20：')
for cfg, n in cnt.most_common(20):
    cmds = sorted({h[0] for h in hits if h[2] == cfg})
    print('     %-34s %3d 条命令 ｜ 例: %s' % (cfg, n, cmds[:8]))
