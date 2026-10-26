# -*- coding: utf-8 -*-
"""R237（新目标④）：★★★ **给 `kconst_to_cfg.py` 加"散片合并"规则** ——
   解锁"多 dict 各装一行"型的配置（如 `config_demon`）。

## ★ 诊断（R236/R237 的核心发现）

`cfg_kconst/config_demon.json` 的 `kgc` 有 **118 项**，其中：
```
[ 0] dict  hash={"action_power_kill":10, "balance_ratio":1}      ← ★ 全局参数（无关键键）
[ 1] 'DemonKeyValue'                                             ← ★ 分组标识（字符串）
[ 2] list  [null,3,5,7,9,11]                                     ← ★ 数组型（阶段序列）
…
[ 9] dict  hash={"lev_up_chip":130, "lev":5, "cost":400, "chip_sum":310}
```
**键频次**：`bid` **只有 9 次** ⇒ ★★ **只有 9 个恶魔**（**不是 60**）；
`action_power` **45 次**（**数组型**）。

★ **⇒ 旧规则把每个 dict 当"一行"** ⇒ **得到 60 个"残缺行"** ❌
★ **⇒ 正确规则**：**按"关键键"（`bid`/`id`/`uid`）分组** ——
   ① 若某 dict **含关键键** ⇒ **它是"一个实体的开头"**
   ② **后续不含关键键的 dict** ⇒ **合并进"当前实体"**
   ③ 数组型（list）⇒ **归入 `lists`**（**不硬配**）
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'cfg_kconst')
DST = os.path.join(ROOT, 'server', 'cfg_kconfig2')      # ★ 新目录（不动 R221 的产物）
os.makedirs(DST, exist_ok=True)

KEYCAND = ('bid', 'id', 'uid', 'index', 'type')


def merge_rows(kgc):
    """★ 把"散片 dict"按关键键分组合并 ⇒ `{key: row}`。"""
    rows = {}
    cur = None
    for x in kgc:
        if isinstance(x, str):
            continue
        if not isinstance(x, dict):
            continue
        h = x.get('hash') or {}
        a = x.get('array') or []
        if not h and not a:
            continue
        keys = set(h.keys())
        kk = next((k for k in KEYCAND if k in keys), None)
        if kk is not None:
            k = str(h.get(kk))
            cur = rows.setdefault(k, {})
            cur.update(h)
        elif cur is not None:
            # ★ 不含关键键 ⇒ 合并进"当前实体"
            cur.update(h)
            if a:
                cur.setdefault('_arrays', []).append(a)
        else:
            rows.setdefault('_global', {}).update(h)
    return rows


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
    rows, lists = {}, {}
    for pi, v in (j or {}).items():
        kgc = v.get('kgc') or []
        r = merge_rows(kgc)
        if r:
            rows.update(r)
        for x in kgc:
            if isinstance(x, list) and x:
                lists.setdefault(pi or 'main', []).append(x)
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
print('  ★ 合并后输出 %d 个（`server/cfg_kconfig2/`）' % ok)
print('  ★ 行数最多的 20 个（**对比 R221 的 `cfg_kconfig`**）:')
for n, r, l in big[:20]:
    print('     %-34s %6d 行 ｜ list %6d 条' % (n, r, l))
