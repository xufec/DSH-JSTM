#!/usr/bin/env python3
"""由 analysis/1.4.9/item/_drop_detail.csv 生成 drop_table.md 的 Markdown 表格行。

【硬约束】输入 CSV 由 tools/analyze_drop.py 从 1.4.9 APK (anzbao/jstm.apk)
还原的 _config_drop.json / _config_drop_item.json 派生；不含 1.4.11 数据。
"""
import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DROP = os.path.join(ROOT, 'analysis', '1.4.9', 'item', '_config_drop.json')
DROPITEM = os.path.join(ROOT, 'analysis', '1.4.9', 'item', '_config_drop_item.json')
CSV = os.path.join(ROOT, 'analysis', '1.4.9', 'item', '_drop_detail.csv')

d = json.load(open(DROP, encoding='utf-8'))['Config']['Drop']
di = json.load(open(DROPITEM, encoding='utf-8'))['Config']['DropItem']

# 每个 DropItem 组，被哪些 mon_bid / 以什么角色引用
refs = {}
for k, e in d.items():
    if e['first']:
        refs.setdefault(str(e['first']), []).append('%s:first' % k)
    if e['core']:
        refs.setdefault(str(e['core']), []).append('%s:core' % k)
    for ib in (e['normal'] or {}):
        refs.setdefault(ib, []).append('%s:normal' % k)


def pool_table():
    out = []
    hdr = ('| DropItem组 | p_sum | 序号 | 物品bid | 物品名 | item_num | roll区间 | 概率(pp/p_sum) | 被谁引用 |')
    out.append(hdr)
    out.append('|---|---|---|---|---|---|---|---|---|')
    for g in sorted(di, key=int):
        grp = di[g]
        items = sorted(grp['item_list'].items(), key=lambda kv: int(kv[0]))
        used = '、'.join(sorted(set(refs.get(g, [])))) or '**无引用**'
        first = True
        for idx, it in items:
            f = it['pp'] / grp['p_sum'] * 100
            out.append('| %s | %s | %s | %s | %s | %s | %s–%s | %d/%d = %.2f%% | %s |'
                       % (g if first else '↳', grp['p_sum'] if first else '',
                          idx, it['item_bid'], it['item_name'], it['item_num'],
                          it['min'], it['max'], it['pp'], grp['p_sum'], f,
                          used if first else ''))
            first = False
    return '\n'.join(out)


def detail_table():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))
    out = []
    out.append('| 怪物bid | 怪物名 | 节 | DropItem组 | 档位(pp/区间) | 物品bid | 物品名 | 数量 | 组内区间 | 组内概率 | 数据来源/证据 |')
    out.append('|---|---|---|---|---|---|---|---|---|---|---|')
    for r in rows:
        sec = r['section']
        if sec.startswith('first'):
            s, field = '首次', 'first'
        elif sec.startswith('core'):
            s, field = '核心', 'core'
        else:
            s, field = '普通', 'normal'
        dn = r['dropitem_bid']
        grp = di.get(dn, {})
        psum = grp.get('p_sum')
        tpp = r['t_pp']
        prob = ('%s/%s = %.2f%%' % (tpp, psum, int(tpp) / psum * 100)) if (tpp and psum) else '—'
        if s == '普通':
            src = ('`Drop[%s].normal[%s][%s]` pp=%s 区间[%s,%s] → `DropItem[%s].item_list[%s]`'
                   % (r['mon_bid'], dn, r['inner_idx'], r['mid_pp'], r['mid_min'],
                      r['mid_max'], dn, r['term_idx']))
            slot = 'pp=%s 区间[%s,%s] / 组 Σpp=1000' % (r['mid_pp'], r['mid_min'], r['mid_max'])
        else:
            src = ('`Drop[%s].%s=%s` → `DropItem[%s].item_list[%s]`'
                   % (r['mon_bid'], field, dn, dn, r['term_idx']))
            slot = '—（%s 直接指向该组）' % field
        out.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s–%s | %s | %s |'
                   % (r['mon_bid'], mon_name(r['mon_bid']), s, dn, slot,
                      r['item_bid'], r['item_name'], r['item_num'],
                      r['t_min'], r['t_max'], prob, src))
    return '\n'.join(out)


MON = os.path.join(ROOT, 'analysis', '1.4.9', 'task', 'config_mon.json')
_mon = json.load(open(MON, encoding='utf-8')) if os.path.exists(MON) else {}


def mon_name(b):
    e = _mon.get(b)
    return e['name'] if e else '**不在 Config.Mon**'


print('##### POOL')
print(pool_table())
print()
print('##### DETAIL')
print(detail_table())
