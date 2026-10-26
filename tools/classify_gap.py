# -*- coding: utf-8 -*-
"""★ 把 R136 的 **1144 条潜在缺口**分类，找出"能指到配置/DB"的那批。

## 为什么要做

R136 查明：协议里 **与 1144 条（CS+SC）既不在任何集合、也无专用实现**
⇒ 目前只走 R151 启用的**全局兜底**（回**空表**）。
本工具要找出：**哪些能升级为真实数据**（用已解构的 204 个配置 + 已建的 12 张状态表）。

## 分类维度

1. **家族**（按命令号段聚类 —— 同家族往往同源，比逐条看更有效）
2. **SC 顶层字段能否对上某个配置的字段**
3. **是否已在 `server/cfg/*.json` 里出现过**（配置覆盖）

用法：
    python tools/classify_gap.py                 # 总览 + 家族聚类
    python tools/classify_gap.py --family 15     # 看某个家族
    python tools/classify_gap.py --md out.md     # 写出报告
"""
import io
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, 'server', 'cfg')
SPEC = os.path.join(ROOT, 'protocol', 'fields.json')
GAP = os.path.join(ROOT, 'analysis', '1.4.9', '_unhandled_cs_sc.txt')


def load_gaps():
    out = []
    for ln in open(GAP, encoding='utf-8'):
        ln = ln.strip()
        if ln.isdigit():
            out.append(int(ln))
    return out


def load_spec():
    """返回 {cmd: {'sc': [字段名], 'cs_count': n}}

    ★ `fields.json` 的键是 `CSFirstPack_10001` 这种，`cmd` 是**字符串数字**；
    个别条目的 `cmd` 不是数字（如 `buff_bids`）⇒ 必须容错跳过。
    """
    d = json.load(open(SPEC, encoding='utf-8'))
    out = {}
    for v in d.values():
        if not isinstance(v, dict):
            continue
        try:
            c = int(v.get('cmd'))
        except (TypeError, ValueError):
            continue
        e = out.setdefault(c, {'sc': [], 'cs': 0})
        if v.get('dir') == 'sc':
            e['sc'] = [f.get('name') for f in (v.get('fields') or [])]
        elif v.get('dir') == 'cs':
            e['cs'] = len(v.get('fields') or [])
    return out


def cfg_index():
    """配置字段名 → [配置名, …]（只看 hash 里的顶层字段名）。"""
    idx = defaultdict(set)
    for fn in sorted(os.listdir(CFG)):
        if not fn.endswith('.json'):
            continue
        name = fn[:-5]
        try:
            d = json.load(open(os.path.join(CFG, fn), encoding='utf-8'))
        except Exception:
            continue
        for k, v in d.items():
            h = None
            if isinstance(v, dict):
                h = v.get('hash') if 'hash' in v else None
                if h is None and v and all(isinstance(x, dict) for x in list(v.values())[:1]):
                    h = v.get('hash')
            if isinstance(h, dict):
                for f in h.keys():
                    idx[f].add(name)
        idx['__keys__' + name] = set(d.keys())
    return idx


def main():
    args = sys.argv[1:]
    fam_filter = None
    md = None
    if '--family' in args:
        fam_filter = args[args.index('--family') + 1]
    if '--md' in args:
        md = args[args.index('--md') + 1]

    gaps = load_gaps()
    spec = load_spec()
    idx = cfg_index()

    # 家族聚类（命令号前 2 位）
    fam = defaultdict(list)
    for c in gaps:
        fam[str(c)[:2]].append(c)

    lines = []
    lines.append('# 潜在缺口（1144 条）的分类总览\n')
    lines.append('命令总数：**%d**\n' % len(gaps))
    lines.append('| 家族 | 条数 | 代表命令 |')
    lines.append('|---|---|---|')
    for k in sorted(fam, key=lambda x: -len(fam[x])):
        cs = sorted(fam[k])[:8]
        lines.append('| `%sxxx` | %d | %s |' % (k, len(fam[k]), ', '.join(str(x) for x in cs)))
    txt = '\n'.join(lines)
    print(txt)

    # 逐条找配置线索
    hit = []
    for c in gaps:
        sc = spec.get(c, {}).get('sc') or []
        if not sc:
            continue
        matched = {}
        for f in sc:
            if f in idx:
                matched[f] = sorted(idx[f])[:3]
        if matched:
            hit.append((c, sc, matched))
    print('\n★ 有配置字段线索的：**%d / %d** 条\n' % (len(hit), len(gaps)))
    for c, sc, m in hit[:30]:
        print('  %-7d SC[%s]' % (c, ','.join(sc)[:52]))
        for f, cfgs in list(m.items())[:3]:
            print('          %-16s ← %s' % (f, ', '.join(cfgs)[:80]))

    if md:
        with open(md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
            f.write('\n\n## 有配置字段线索的 %d 条\n\n' % len(hit))
            for c, sc, m in hit:
                f.write('- `%d` SC[%s]\n' % (c, ','.join(sc)))
                for k2, cfgs in m.items():
                    f.write('  - `%s` ← %s\n' % (k2, ', '.join(cfgs)))
        print('\n已写出 %s' % md)


if __name__ == '__main__':
    main()
