# -*- coding: utf-8 -*-
"""R221（新目标④）：★★★ **"常量池 → 配置表"转换器** —— 解锁"线性解构失败"的配置。

## ★ 为什么

R195 用 `dump_kconst.py` dump 出 **285/286 个配置的常量池**（`server/cfg_kconst/`），
但那是**原始形态**（`{proto0: {kgc: [...], knum: [], kstr: []}}`）—— **服务端读不了**。

★ 而**线性解构**（`server/cfg/`）对 **18 个配置失败**（`config_skill` 的"嵌套函数"等）
⇒ ★★ **本工具把"常量池"转成"配置表形态"**（`{顶层键: {行 id: {字段: 值}}}`）
   ⇒ **服务端现有的 `cfg()` 读取函数就能用** ✓

## 转换规则

① **找出"主表"**（`hash` 项最多的 dict）⇒ 它是 `{id: row}`
② **若"多 dict 各装一行"** ⇒ **合并成一个 `{序号: row}`**
③ **`list` 型 `kgc`** ⇒ **`{序号: 数组}`**
④ 输出 `server/cfg_kconfig/<name>.json`（**结构与 `server/cfg` 平行**）
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'cfg_kconst')
DST = os.path.join(ROOT, 'server', 'cfg_kconfig')
os.makedirs(DST, exist_ok=True)

files = sorted(f for f in os.listdir(SRC) if f.endswith('.json'))
print('  cfg_kconst: %d 个' % len(files))

ok = 0
big = []
for fn in files:
    name = fn[:-5]
    try:
        j = json.load(open(os.path.join(SRC, fn), encoding='utf-8'))
    except Exception:
        continue
    rows = {}
    lists = {}
    for pi, v in (j or {}).items():
        kgc = v.get('kgc') or []
        dicts = [x for x in kgc if isinstance(x, dict) and (x.get('hash') or x.get('array'))]
        # ① 多 dict ⇒ 每个一行
        if len(dicts) >= 3:
            for i, d in enumerate(dicts):
                h = d.get('hash') or {}
                a = d.get('array') or []
                if not h and not a:
                    continue
                key = str(int(h.get('id') or h.get('bid') or i + 1))
                rows[key] = dict(h) if h else {'array': a}
        elif dicts:
            # ② 一个 dict 装 N 行
            for d in dicts:
                for k, vv in (d.get('hash') or {}).items():
                    rows[str(k).split('.')[0]] = vv
        # ③ list 型
        ls = [x for x in kgc if isinstance(x, list)]
        if ls:
            lists[pi or 'main'] = ls
    if not rows and not lists:
        continue
    out = {}
    if rows:
        out['rows'] = rows
    if lists:
        out['lists'] = lists
    with open(os.path.join(DST, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(out, ensure_ascii=False))
    ok += 1
    big.append((name, len(rows), sum(len(v) for v in lists.values())))

big.sort(key=lambda x: -x[1])
print('  ★ 转换出 %d 个（`server/cfg_kconfig/`）' % ok)
print('  ★ 行数最多的 18 个:')
for n, r, l in big[:18]:
    print('     %-34s %6d 行 ｜ list %6d 条' % (n, r, l))
