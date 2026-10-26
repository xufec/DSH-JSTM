#!/usr/bin/env python3
"""生成 64 项属性元数据 + 与 `role_attr` 表列的差异清单（R43 交付物之一）。

## 为什么需要

`config_attr.luac` 定义 **AttrLen = 64** 项属性，而 `role_attr` 表只落了 **25 列**。
缺口此前只在文档里口头提过，没有清单，导致：**哪些属性缺失、哪些缺失项还"有战力权重"**
（即真的会让战力算少）无人能一眼看清。

## `src` 判据（严格不猜）

只标记**有证据**的：

| src | 判据 | 例 |
|---|---|---|
| `derived` | 该键是**展示副本**，同表内存在对应的"真值"键 | `hit_rate_show`(201) ← `hit_rate`(125)；同理 dodge/crit/tenacity |
| `runtime` | 运行时状态而非角色输入属性 | `hp`(110 当前血量) |
| `unknown` | 无充分证据 ⇒ **不猜** | 其余 |

`stored` 表示是否已落在 `role_attr` 表；`power_weight != 0` 且 `stored = False`
的项**会直接算少战力**，单独高亮。

用法：
    python tools/gen_attr_meta.py                 # 打印清单 + 写 server/_attr_meta.json
    python tools/gen_attr_meta.py --out x.json
"""
import argparse
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ATTR_DATA = os.path.join(ROOT, 'server', '_attr_data.json')
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
OUT = os.path.join(ROOT, 'server', '_attr_meta.json')

# ★ 展示副本 → 真值键（同表内成对存在，证据充分）
SHOW_PAIRS = {
    'hit_rate_show': 'hit_rate',
    'dodge_rate_show': 'dodge_rate',
    'crit_rate_show': 'crit_rate',
    'tenacity_rate_show': 'tenacity_rate',
}
RUNTIME = {'hp'}          # 当前血量：运行时状态


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--print', dest='do_print', action='store_true', default=True)
    args = ap.parse_args()

    d = json.load(open(ATTR_DATA, encoding='utf-8'))
    id2k = d['AttrId2Key']
    k2s = d.get('AttrKey2Str') or {}
    pw = d.get('AttrPower') or {}
    show = set(d.get('AttrKeyIsShow') or {})

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("select name from pragma_table_info('role_attr')")
    cols = set(r[0] for r in cur.fetchall())
    con.close()

    rows = []
    for i, k in id2k.items():
        key = k
        if key in SHOW_PAIRS:
            src = 'derived'
        elif key in RUNTIME:
            src = 'runtime'
        else:
            src = 'unknown'
        rows.append({
            'id': int(float(i)),
            'key': key,
            'name': k2s.get(key, ''),
            'power_weight': pw.get(key, 0),
            'is_show': key in show,
            'stored': key in cols,
            'src': src,
        })
    rows.sort(key=lambda r: r['id'])

    missing = [r for r in rows if not r['stored']]
    missing_power = [r for r in missing if r['power_weight']]
    derived = [r for r in rows if r['src'] == 'derived']

    print('AttrLen=%d ｜ role_attr 列 %d ｜ 缺列 %d（其中**带战力权重**的 %d）'
          % (len(rows), len(cols), len(missing), len(missing_power)))
    print()
    print('★ 缺失且**带战力权重**（会让战力算少）:')
    for r in missing_power:
        print('   id=%-4d %-18s %-8s 权重=%-5s' % (r['id'], r['key'], r['name'], r['power_weight']))
    print()
    print('★ 可取证为"派生"的展示副本（src=derived）: %s'
          % ', '.join(r['key'] for r in derived))
    print()
    print('全部缺失项(%d): %s' % (len(missing), [r['key'] for r in missing]))
    print()
    print('已落表(%d): %s' % (len(rows) - len(missing), [r['key'] for r in rows if r['stored']]))

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({'attr_len': len(rows), 'items': rows}, f, ensure_ascii=False, indent=1)
    print('\n已写出 %s' % args.out)


if __name__ == '__main__':
    main()
