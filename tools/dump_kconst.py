# -*- coding: utf-8 -*-
"""R195（新目标④）：★★ **直接 dump 常量池**（绕过控制流）。

## ★ 为什么

R193/R194 用"线性模拟"能拿到 **chunk 顶层建表**的数据（`config_item` 的 3013 条），
但拿不到 **"嵌套函数返回"** 的数据 —— 例如：
   `config_skill` 的 **`proto0`（69601 条）**，`KGC=17727`、`KNum=8700`
   ⇒ ★ **数据全在"常量池"里**（每个 `TableConst` 就是一条技能表）✓

★ **⇒ 直接 dump `kgc` / `knum` / `kstr` 就能拿到**（**完全不依赖控制流模拟**）。

## 输出

`server/cfg_kconst/<name>.json`：
```json
{"proto0": {"kgc": [...], "knum": [...], "kstr": [...]}, "proto1": {...}}
```
★ 只写"非空"的 proto。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import config_deconstruct as cd          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = open(os.path.join(ROOT, 'analysis', '1.4.9', '_dump_kconst.txt'),
           'w', encoding='utf-8', newline='\n')


def print(*a):
    LOG.write(' '.join(str(x) for x in a) + '\n')
    LOG.flush()


SRC = os.path.join(ROOT, '_tmp_cfg')
DST = os.path.join(ROOT, 'server', 'cfg_kconst')
os.makedirs(DST, exist_ok=True)

files = sorted(f for f in os.listdir(SRC) if f.endswith('.luac'))
print('  _tmp_cfg: %d 个 .luac' % len(files))

ok = 0
big = []
for fn in files:
    name = fn[:-5]
    p = os.path.join(SRC, fn)
    try:
        r = cd.parse_file(p)
    except Exception:
        continue
    out = {}
    for pi, pr in enumerate(r.protos):
        kgc = cd.to_jsonable(getattr(pr, 'kgc', None) or [])
        knum = cd.to_jsonable(getattr(pr, 'knum', None) or [])
        kstr = cd.to_jsonable(getattr(pr, 'kstr', None) or [])
        if not (kgc or knum or kstr):
            continue
        out['proto%d' % pi] = {'kgc': kgc, 'knum': knum, 'kstr': kstr}
    if not out:
        continue
    s = json.dumps(out, ensure_ascii=False)
    with open(os.path.join(DST, name + '.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    ok += 1
    n_items = sum(len(v['kgc']) for v in out.values())
    big.append((name, len(s), n_items, len(out)))

big.sort(key=lambda x: -x[1])
print('  ★ dump 出 %d 个常量池文件' % ok)
print('  ★ 最大的 18 个：')
for n, sz, ni, np_ in big[:18]:
    print('     %-38s %8d 字符 ｜ KGC %6d 条 ｜ %d protos' % (n, sz, ni, np_))
