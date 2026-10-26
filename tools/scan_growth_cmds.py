# -*- coding: utf-8 -*-
"""扫"已建系统"（座椅/翅膀/神器/命格/法宝/魂兽/坐骑/元神）的命令家族，
列出**尚未实现**的写操作（升级/升星/培养）—— 作为"成长动作"的候选。

用法： python tools/scan_growth_cmds.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = json.load(open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8'))

# 已建状态表的系统 → 命令前缀
FAMILIES = {
    '座椅 chair': ('208', ['role_chair']),
    '翅膀 wing': ('116', ['role_wing']),
    '神器 shenqi': ('157', ['role_shenqi']),
    '命格 mingge': ('194', ['role_mingge', 'role_yuanshen']),
    '法宝 fabao': ('189', ['role_fabao']),
    '魂兽 lingshou': ('158', ['role_lingshou']),
    '坐骑 ride': ('155', ['role_ride']),
    '装备 equip': ('214', ['equip_items']),
}

src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
s2 = re.sub(r'#[^\n]*', '', src)


def implemented():
    eq = set(int(x) for x in re.findall(r'if cmd == (\d{4,5}):', s2))
    for mm in re.finditer(r'if cmd in \(([^)]*)\):', s2):
        for x in re.findall(r'\d{4,5}', mm.group(1)):
            eq.add(int(x))
    return eq


def in_set(name):
    m = re.search(name + r'\s*=\s*frozenset\(\[(.*?)\]\)', s2, re.S)
    return set(int(x) for x in re.findall(r'\b\d{4,5}\b', m.group(1))) if m else set()


EQ = implemented()
GEN = in_set('_GENERIC_DEFAULT_CMDS')
UNS = in_set('_UNSUPPORTED_ACTION_CMDS')

for label, (pfx, tables) in FAMILIES.items():
    print('=== %s（表：%s）===' % (label, ', '.join(tables)))
    found = []
    for k, v in FIELDS.items():
        c = str(v.get('cmd') or '')
        if not c.startswith(pfx) or len(c) != 5:
            continue
        if v.get('dir') != 'cs':
            continue
        n = int(c)
        if n in EQ:
            continue
        fs = [f.get('name') for f in (v.get('fields') or [])]
        # 找同命令的 SC
        sc = None
        for k2, v2 in FIELDS.items():
            if str(v2.get('cmd')) == c and v2.get('dir') == 'sc':
                sc = [f.get('name') for f in (v2.get('fields') or [])]
                break
        found.append((n, fs, sc or []))
    for n, cs, sc in sorted(found):
        tag = '默认' if n in GEN else ('未开放' if n in UNS else '无')
        print('  %-6d CS[%s]' % (n, ','.join(cs)[:44]))
        print('         → SC[%s]   [%s]' % (','.join(sc)[:70], tag))
    if not found:
        print('  （该家族已全部实现）')
    print()
