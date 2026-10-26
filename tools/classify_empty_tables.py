# -*- coding: utf-8 -*-
"""R204：★ **把 435 条空表按"数据来源"分类** —— 找出真正可动的对象。

分类：
  · **DB 可填** —— 子表名对应**玩家状态**（`role_*`/`*_state` 表），且本服有该玩家的数据
  · **配置可填** —— 子表名对应某配置的**主表字段**（且值非 0）
  · **事实为空** —— 社交域（本服 1 个角色）或"玩家未获得"
  · **未知** —— 需人工看

★ 本脚本只**分类**（不改代码），输出 `analysis/1.4.9/_empty_class.txt`。
"""
import importlib.util
import io
import json
import os
import sqlite3
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = importlib.util.spec_from_file_location('g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

# ① DB 表清单
db = os.path.join(ROOT, 'server', 'state', 'roles.db')
con = sqlite3.connect(db)
tabs = {}
for (t,) in con.execute("select name from sqlite_master where type='table'"):
    try:
        n = con.execute('select count(*) from "%s"' % t).fetchone()[0]
        cols = [r[1] for r in con.execute('pragma table_info("%s")' % t)]
    except Exception:
        n, cols = -1, []
    tabs[t] = (n, cols)
con.close()
print('  DB 表: %d 张；有数据的: %d 张' % (len(tabs), sum(1 for v in tabs.values() if v[0] > 0)))

# ② 配置的"主表字段名"+"值非零率"
D = os.path.join(ROOT, 'server', 'cfg_kconst')
CFG = {}
for fn in sorted(os.listdir(D)):
    if not fn.endswith('.json'):
        continue
    try:
        j = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    except Exception:
        continue
    best = {}
    for v in j.values():
        for x in (v.get('kgc') or []):
            if isinstance(x, dict):
                h = x.get('hash') or {}
                if len(h) > len(best):
                    best = h
    if best:
        nz = sum(1 for v in best.values() if isinstance(v, (int, float)) and v)
        CFG[fn[:-5]] = (set(k for k in best if isinstance(k, str)), nz, len(best))

# ③ 社交域/事实为空的族名
FACT = ('friend', 'team', 'circle', 'wedding', 'market', 'guild_race', 'battlevideo',
        'qifu', 'chongzhi', 'mail', 'chat', 'rank_of_other')
print('  配置: %d 个' % len(CFG))

AL = json.load(open(os.path.join(ROOT, 'tools', '_emitted_empty_allow.json'), encoding='utf-8'))
allow = AL.get('allow') or {}
by = {}
for k in allow:
    c, f = k.split(':', 1)
    by.setdefault(c, []).append(f)
print('  空表: %d 条 / %d 个命令' % (len(allow), len(by)))

cls = Counter()
rows = []
for cmd, fields in sorted(by.items()):
    fs = sc.get(cmd) or []
    for fname in fields:
        elem = None
        for f in fs:
            if isinstance(f, dict) and f.get('name') == fname:
                elem = [i.get('name') for i in (f.get('items') or [])]
                break
        elem = elem or []
        # 分类
        dbhit = None
        for t, (n, cols) in tabs.items():
            if n <= 0:
                continue
            # ★ 子表元素字段名与 DB 列名重合 ≥ 3，或表名暗示
            ov = len(set(elem) & set(cols))
            if ov >= 3:
                dbhit = (t, n, ov)
                break
        cfghit = None
        for cfg, (keys, nz, tot) in CFG.items():
            ov = len(set(elem) & keys)
            if ov >= 8 and nz * 2 >= tot and tot:
                cfghit = (cfg, ov, nz, tot)
                break
        if dbhit:
            k = 'DB可填'
        elif cfghit:
            k = '配置可填'
        elif not elem:
            k = '无元素'
        else:
            k = '未知'
        cls[k] += 1
        rows.append((cmd, fname, k, dbhit, cfghit, elem))

print('\n  ★ 分类统计:')
for k, n in cls.most_common():
    print('     %-10s %3d 条' % (k, n))
print('\n  ★ "DB可填"的样例:')
for cmd, fname, k, dbh, cfh, elem in rows:
    if k == 'DB可填':
        print('     %-6s %-18s ← DB %s（%d 行，重合 %d）' % (cmd, fname, dbh[0], dbh[1], dbh[2]))
print('\n  ★ "配置可填"的样例:')
n = 0
for cmd, fname, k, dbh, cfh, elem in rows:
    if k == '配置可填':
        print('     %-6s %-18s ← %s（重合 %d，非零 %d/%d）' % (cmd, fname, cfh[0], cfh[1], cfh[2], cfh[3]))
        n += 1
        if n >= 10:
            break

out = os.path.join(ROOT, 'analysis', '1.4.9', '_empty_class.txt')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    for cmd, fname, k, dbh, cfh, elem in rows:
        f.write('%s\t%s\t%s\t%s\t%s\n' % (
            cmd, fname, k,
            ('%s:%d:%d' % (dbh[0], dbh[1], dbh[2])) if dbh else
            ('%s:%d:%d/%d' % (cfh[0], cfh[1], cfh[2], cfh[3])) if cfh else '',
            ','.join(elem)[:80]))
print('\n  ⇒ 已写 %s' % out)
