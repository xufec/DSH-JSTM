# -*- coding: utf-8 -*-
"""R243b：★★ **族命令 × 数据源 三向对照表**（为"逐族接真值"派活）。

对 `R232`/`R233` 那 90 条"有自己的分支但只走权威编码器（= 结构正确、内容空）"的命令：
  ① 取 **权威 SC 字段名**（顶层 + 子表元素，**递归**）
  ② 与 **245 个 `cfg_kconfig` 配置**的**键名**求交
  ③ 与 **本服 45 张 DB 表**的**列名**求交
  ④ 打印 `重合 ≥ N` 的候选（按重合数降序）

⚠ 输出只是**线索**（纪律第 42/46 条："字段名重合 ≠ 语义对应"），
   逐个接真值前仍必须**逐字段确凿**。

用法：python tools/scan_family_sources.py [--min 3] [--cmd 18736]
"""
import argparse
import importlib.util
import io
import json
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KCFG = os.path.join(ROOT, 'server', 'cfg_kconfig')
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')

FAM = {
    'R232 187xx(7)': [18700, 18701, 18702, 18703, 18708, 18732, 18733],
    'R233 110xx(13)': [11001, 11002, 11003, 11004, 11005, 11006, 11007, 11008,
                       11011, 11012, 11013, 11014, 11018],
    'R233 112xx(9)': [11204, 11212, 11213, 11214, 11218, 11222, 11237, 11239, 11241],
    'R233 124xx(8)': [12404, 12412, 12415, 12417, 12418, 12422, 12450, 12499],
    'R233 132xx(8)': [13204, 13205, 13219, 13223, 13234, 13235, 13237, 13238],
    'R233 133xx(13)': [13309, 13324, 13344, 13345, 13346, 13349, 13350, 13351,
                       13360, 13362, 13363, 13366, 13370],
    'R233 135xx(13)': [13510, 13522, 13523, 13525, 13534, 13535, 13540, 13553,
                       13562, 13566, 13567, 13568, 13581],
    'R233 138xx(7)': [13810, 13813, 13815, 13817, 13821, 13826, 13851],
    'R233 187xx(4)': [18736, 18751, 18752, 18756],
    'R233 188xx(8)': [18802, 18806, 18813, 18814, 18828, 18829, 18863, 18864],
}


def load_specs():
    sp = importlib.util.spec_from_file_location(
        'g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(g)
    return g.load_specs()


def names_of(fields, out=None, dep=0):
    """★ 递归收集 SC 的字段名（顶层 + 子表元素）。"""
    if out is None:
        out = set()
    if dep > 3:
        return out
    for f in (fields or []):
        if not isinstance(f, dict):
            continue
        n = f.get('name')
        if isinstance(n, str) and n:
            out.add(n)
        names_of(f.get('items') or [], out, dep + 1)
    return out


def cfg_key_names(obj, out=None, dep=0):
    if out is None:
        out = set()
    if dep > 3:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            cfg_key_names(v, out, dep + 1)
    elif isinstance(obj, list):
        for v in obj[:20]:
            cfg_key_names(v, out, dep + 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min', type=int, default=3)
    ap.add_argument('--cmd', type=int, default=0)
    a = ap.parse_args()
    cs, sc = load_specs()

    cfgs = {}
    for n in sorted(os.listdir(KCFG)):
        if not n.endswith('.json'):
            continue
        try:
            cfgs[n[:-5]] = cfg_key_names(json.load(open(os.path.join(KCFG, n),
                                                        encoding='utf-8')))
        except Exception:
            pass
    con = sqlite3.connect(DB)
    tabs = {}
    for (t,) in con.execute("select name from sqlite_master where type='table'"):
        tabs[t] = set(r[1] for r in con.execute('pragma table_info("%s")' % t))
    con.close()
    print('  ★ 数据源：%d 个配置 ｜ %d 张表' % (len(cfgs), len(tabs)))

    for fam, cmds in FAM.items():
        print('\n=== %s ===' % fam)
        for c in cmds:
            if a.cmd and c != a.cmd:
                continue
            flds = names_of(sc.get(str(c)) or [])
            hits = []
            for n, ks in cfgs.items():
                ov = flds & ks
                if len(ov) >= a.min:
                    hits.append((len(ov), 'cfg:' + n, sorted(ov)[:6]))
            for n, ks in tabs.items():
                ov = flds & ks
                if len(ov) >= a.min:
                    hits.append((len(ov), 'db:' + n, sorted(ov)[:6]))
            hits.sort(key=lambda x: -x[0])
            tag = ('★ %d 字段' % len(flds)) if flds else '⚠ 无字段'
            print('  cmd=%-6d %s' % (c, tag))
            for ov, src, ovl in hits[:3]:
                print('        %-34s 重合 %2d ｜ %s' % (src, ov, ovl))
            if not hits:
                print('        （无重合 ≥ %d 的数据源）' % a.min)


if __name__ == '__main__':
    main()
