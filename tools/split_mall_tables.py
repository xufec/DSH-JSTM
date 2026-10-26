"""把 config_mall.luac 按"顶层表"拆开：MallXian / MallWeek / MallHuobanXishu / MallType ...

动机（本轮取证）：`tools/extract_mall.py` 是把 proto#0 里**所有**含 id/item_bid 的 TDUP
常量一股脑收集（按 id+item_bid+price 去重）→ 得到的 `server/mall_config.json` 其实是
**多张表的混合体**。要忠实实现 `SC_12836`（客户端 `on12836 → setZhenbaoGoodsList`），
必须知道 `Config.MallXian` **自己**的条目集合。

做法：顺序扫描 proto#0 的指令，遇到 `TNEW + GSET <name>` 就切换"当前表名"，
把其后（直到下一个 GSET）出现的 TDUP 条目归到该表。

用法：python tools/split_mall_tables.py [apk] [outdir]
"""
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, 'tools')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx    # noqa: E402

FIELDS = ['id', 'item_bid', 'pay_type', 'type', 'bind', 'price',
          'guild_lev', 'limit_week', 'limit_day_cli', 'cli_tag', 'order']


def kidx_d(pt, d):
    """GGET/GSET 的 D 字段索引 kgc（与 find_method_def 同一套反向约定）。"""
    pos = len(pt.kgc) - 1 - d
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    outdir = sys.argv[2] if len(sys.argv) > 2 else r'analysis\1.4.9\shop_luac'
    z = zipfile.ZipFile(apk)
    r = parse_bytes(z.read('assets/src/config/config_mall.luac'))
    pt = r.protos[0]

    tables = {}          # 序号 -> {'globals': [...], 'rows': [...]}
    cur = None
    order = []
    for w in pt.bc:
        op = OPS[w & 0xff]
        if op in ('GSET',):
            g = kidx_d(pt, (w >> 16) & 0xffff)
            name = g if isinstance(g, str) else None
            cur = {'global': name, 'rows': [], 'seen': set()}
            order.append(cur)
            continue
        if op == 'TDUP' and cur is not None:
            c = kidx(pt, (w >> 16) & 0xffff)
            h = dict(getattr(c, 'hash', []) or [])
            if 'item_bid' not in h or 'id' not in h:
                continue
            key = (h.get('id'), h.get('item_bid'))
            if key in cur['seen']:
                continue
            cur['seen'].add(key)
            cur['rows'].append({k: h.get(k) for k in FIELDS})

    os.makedirs(outdir, exist_ok=True)
    total = 0
    for i, t in enumerate(order, 1):
        rows = sorted(t['rows'], key=lambda x: (x.get('id') or 0))
        total += len(rows)
        print('[表%d] global=%-16s 条目=%d' % (i, t['global'], len(rows)))
        if rows:
            ids = [x['id'] for x in rows]
            print('        id 范围 %s .. %s ; 前 12 个: %s' % (ids[0], ids[-1], ids[:12]))
            types = sorted({x.get('type') for x in rows})
            print('        type 取值: %s ; limit_week 非 0 的条目数: %d'
                  % (types, sum(1 for x in rows if int(x.get('limit_week') or 0) != 0)))
            fn = os.path.join(outdir, 'mall_table_%d_%s.json' % (i, t['global'] or 'anon'))
            json.dump(rows, io.open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('        -> %s' % fn)
    print('合计条目 %d' % total)

    # 与 server/mall_config.json 对比
    mc = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'server', 'mall_config.json')
    if os.path.exists(mc):
        have = json.load(io.open(mc, encoding='utf-8'))
        have_ids = {int(g['id']) for g in have if g.get('id') is not None}
        print('\nserver/mall_config.json 条目=%d（唯一 id=%d）' % (len(have), len(have_ids)))
        for i, t in enumerate(order, 1):
            want = {int(x['id']) for x in t['rows'] if x.get('id') is not None}
            if not want:
                continue
            print('  [表%d %-16s] %d 条中，mall_config 里缺失 %d 条 %s'
                  % (i, t['global'], len(want), len(want - have_ids),
                     sorted(want - have_ids)[:12]))


if __name__ == '__main__':
    main()
