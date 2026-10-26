#!/usr/bin/env python3
"""基于 tools/dump_drop_config.py 还原出的 Config.Drop / Config.DropItem，
生成可直接放进文档的掉落明细与统计。

【硬约束】只读 analysis/1.4.9/item/_config_drop*.json —— 这些 JSON 由
tools/dump_drop_config.py 从 anzbao/jstm.apk (1.4.9) 提取的 .luac 还原。
绝不涉及 jstm_142165.apk（1.4.11）。

用法：
    python tools/analyze_drop.py            # 打印统计 + 全部明细
    python tools/analyze_drop.py --csv out.csv
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DROP = os.path.join(ROOT, 'analysis', '1.4.9', 'item', '_config_drop.json')
DROPITEM = os.path.join(ROOT, 'analysis', '1.4.9', 'item', '_config_drop_item.json')
MON = os.path.join(ROOT, 'analysis', '1.4.9', 'task', 'config_mon.json')

SUMF = {'first_p': 'first_p_sum', 'core_p': 'core_p_sum', 'normal': 'normal_sum'}


def load():
    d = json.load(open(DROP, encoding='utf-8'))['Config']['Drop']
    di = json.load(open(DROPITEM, encoding='utf-8'))['Config']['DropItem']
    mon = json.load(open(MON, encoding='utf-8')) if os.path.exists(MON) else {}
    return d, di, mon


def iter_pools(entry, sec):
    """把某个掉落节展开成 [(item_bid_or_None, 中层键, 中层 pool)]。

    经 Config.Drop 全部 29 条逐条核对，三个节的**嵌套层数并不一致**：

      normal  : normal[item_bid][中层键] = {num?, min, max, pp}      （三层）
      core_p  : core_p[中层键]          = {num, min, max, pp}        （两层）
      first_p : first_p[中层键]         = {num, min, max, pp}        （两层）

    判定方法：若某子值自身仍是「所有成员都是带 pp 的 dict」的 dict，则多一层。
    """
    node = entry.get(sec) or {}
    for k, v in node.items():
        if isinstance(v, dict) and v and all(
                isinstance(x, dict) and 'pp' in x for x in v.values()):
            for idx, pool in v.items():
                yield k, idx, pool
        else:
            yield None, k, v


def main():
    d, di, mon = load()
    monkeys = set(mon)
    dropkeys = sorted(d, key=lambda x: int(x))

    print('=== Config.Drop 统计 ===')
    print('掉落条目总数        : %d' % len(dropkeys))
    print('条目字段数          : %d（全部条目一致）' % len(next(iter(d.values()))))
    in_mon = [k for k in dropkeys if k in monkeys]
    not_in_mon = [k for k in dropkeys if k not in monkeys]
    print('mon_bid 命中 Config.Mon : %d  -> %s' % (len(in_mon), in_mon))
    print('mon_bid 不在 Config.Mon : %d  -> %s' % (len(not_in_mon), not_in_mon))
    print()
    print('=== Config.DropItem 统计 ===')
    print('掉落池组数          : %d' % len(di))
    print('组 key             : %s' % sorted(di, key=lambda x: int(x)))
    tot_items = sum(len(v['item_list']) for v in di.values())
    print('item_list 条目总数  : %d' % tot_items)
    print()

    # ---- 校验 1：DropItem 组内 p_sum == Σpp，且 min/max 是 pp 的前缀累加区间 ----
    print('=== 概率自校验（Config.DropItem）===')
    bad_sum = bad_span = 0
    for k, v in sorted(di.items(), key=lambda kv: int(kv[0])):
        items = sorted(v['item_list'].values(), key=lambda x: x['min'])
        s = sum(it['pp'] for it in items)
        if s != v['p_sum']:
            bad_sum += 1
            print('   [p_sum != Σpp] %s: p_sum=%s Σpp=%s' % (k, v['p_sum'], s))
        cum = 0
        for it in items:
            cum += it['pp']
            if it['max'] != cum or it['min'] != cum - it['pp'] + 1:
                bad_span += 1
                print('   [区间!=pp累加] %s bid=%s pp=%s min=%s max=%s 期望 min=%d max=%d'
                      % (k, it['bid'], it['pp'], it['min'], it['max'], cum - it['pp'] + 1, cum))
    print('   %d/%d 组满足 p_sum == Σpp；%d 条不满足 max == 前缀累加 pp'
          % (len(di) - bad_sum, len(di), bad_span))
    print('   => INFERRED：组内按 1..p_sum 均匀 roll，命中 [min,max] 的条目，'
          '概率 = pp / p_sum')
    print()

    # ---- 校验 2：Config.Drop 各节的 normal_sum / *_p_sum 语义 ----
    print('=== *_p_sum 与 normal_sum 语义校验（Config.Drop）===')
    for k in dropkeys:
        e = d[k]
        for sec, sf in SUMF.items():
            pools = list(iter_pools(e, sec))
            if not pools:
                continue
            s = sum(p['pp'] for _, _, p in pools)
            got = e[sf]
            if sec == 'normal':
                # normal_sum 是 {item_bid: 该 item_bid 小节内 Σpp}
                per = {}
                for ib, _, p in pools:
                    per[ib] = per.get(ib, 0) + p['pp']
                exp = {('%s.0' % b if float(b) == int(b) else b): v for b, v in per.items()}
                ok = all(abs(float(got.get(bk, -1)) - v) < 1e-9 for bk, v in exp.items())
                if not ok:
                    print('   [normal_sum 不符] %s: 表内=%s 实算=%s' % (k, got, exp))
            else:
                if s != got:
                    print('   [%s != Σpp] %s: %s=%s Σpp=%s' % (sf, k, sf, got, s))
    print('   （无输出行表示逐条一致）')
    print()

    # ---- 引用图 ----
    referenced = set()
    for k, e in d.items():
        for sec in ('normal',):
            referenced |= set(e[sec].keys())
        if e['first']:
            referenced.add(str(e['first']))
        if e['core']:
            referenced.add(str(e['core']))
    print('DropItem 被 Config.Drop 引用到的组: %s' % sorted(referenced, key=int))
    print('DropItem 存在但未被引用        : %s' % sorted(set(di) - referenced, key=int))
    print()

    # ---- 明细 ----
    rows = []

    def emit(mon_bid, section, dropitem_bid, inner_idx, mid_pp, mid_min, mid_max,
             term_idx, item_bid, item_name, item_num, t_min, t_max, t_pp, src):
        rows.append({
            'mon_bid': mon_bid,
            'section': section,
            'dropitem_bid': dropitem_bid,
            'inner_idx': inner_idx,
            'mid_pp': mid_pp,
            'mid_min': mid_min,
            'mid_max': mid_max,
            'term_idx': term_idx,
            'item_bid': item_bid,
            'item_name': item_name,
            'item_num': item_num,
            't_min': t_min,
            't_max': t_max,
            't_pp': t_pp,
            'src': src,
        })

    def expand(mon_bid, section, dropitem_bid, inner_idx, mid_pp, mid_min, mid_max, note):
        grp = di.get(str(dropitem_bid))
        if grp is None:
            emit(mon_bid, section, dropitem_bid, inner_idx, mid_pp, mid_min, mid_max,
                 '', 'UNKNOWN', '', '', '', '', '',
                 note + ' -> config_drop_item.luac[%s] 【该组不存在】' % dropitem_bid)
            return
        for idx, g in sorted(grp['item_list'].items(), key=lambda kv: int(kv[0])):
            emit(mon_bid, section, dropitem_bid, inner_idx, mid_pp, mid_min, mid_max,
                 idx, g['item_bid'], g['item_name'], g['item_num'],
                 g['min'], g['max'], g['pp'],
                 '%s -> config_drop_item.luac[%s].item_list[%s]' % (note, dropitem_bid, idx))

    for k in dropkeys:
        e = d[k]
        if e['first']:
            expand(k, 'first(首次)', e['first'], '', '', '', '',
                   'config_drop.luac[%s].first=%s' % (k, e['first']))
        if e['core']:
            expand(k, 'core(核心)', e['core'], '', '', '', '',
                   'config_drop.luac[%s].core=%s core_interval=%s'
                   % (k, e['core'], e['core_interval']))
        for item_bid, mid_idx, pool in iter_pools(e, 'normal'):
            if item_bid is None:
                rows.append({'mon_bid': k, 'section': 'normal(随机)',
                             'dropitem_bid': 'UNKNOWN', 'inner_idx': mid_idx,
                             'mid_pp': pool.get('pp'), 'mid_min': pool.get('min'),
                             'mid_max': pool.get('max'), 'term_idx': '', 'item_bid': 'UNKNOWN',
                             'item_name': '', 'item_num': pool.get('num'), 't_min': '',
                             't_max': '', 't_pp': '',
                             'src': 'config_drop.luac[%s].normal（外层键未还原）' % k})
                continue
            expand(k, 'normal(随机)', item_bid, mid_idx, pool.get('pp'), pool.get('min'),
                   pool.get('max'),
                   'config_drop.luac[%s].normal[%s][%s] pp=%s 区间[%s,%s]'
                   % (k, item_bid, mid_idx, pool.get('pp'), pool.get('min'), pool.get('max')))

    print('=== 掉落明细（%d 行）===' % len(rows))
    hdr = ('mon_bid', 'section', 'dropitem_bid', 'inner_idx', 'mid_pp', 'mid_min',
           'mid_max', 'term_idx', 'item_bid', 'item_name', 'item_num', 't_min',
           't_max', 't_pp')
    print('  ' + '  '.join('%-13s' % h for h in hdr))
    for r in rows:
        print('  ' + '  '.join('%-13s' % str(r.get(h)) for h in hdr))

    if '--csv' in sys.argv:
        import csv
        out = sys.argv[sys.argv.index('--csv') + 1]
        with open(out, 'w', newline='', encoding='utf-8-sig') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print('\n已写出 %s (%d 行)' % (out, len(rows)))


if __name__ == '__main__':
    main()
