# -*- coding: utf-8 -*-
"""R192b：**只对"原来就空"的配置应用自动解构**（保护所有已有数据）。

## ★ 为什么

R192 第一版**覆盖了 70 个文件**（"新结果 ≥ 旧结果"就写）⇒
把 `config_map_npc.json`（原 `{MapNpc: …}`）覆盖成了 `{Config: …}` ⇒
**`verify_107xx.py` 报 `KeyError: 'MapNpc'`**（真机回归抓到了）。

★★ **安全原则**：**只在"原文件是空/极小"时才覆盖** ——
   **已有数据的文件一律不动**（哪怕新结果更大，也可能丢了原来那些键）。

## 步骤
1. 用 `batch_deconstruct.py`（proto0）**重建全部** ⇒ 回到"原始解构"状态
2. 记住哪些是"空/极小"（<200B）
3. 只对**这些**跑"自动选主 proto"并覆盖
"""
import io
import json
import os
import subprocess
import sys

sys.stdout = sys.__stdout__
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'server', 'cfg')

print('  ① 用 batch_deconstruct.py 重建（proto0 原始逻辑）...')
r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'batch_deconstruct.py')],
                   capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
print('     %s' % (r.stdout or '').strip().split('\n')[-1][:90])

# ★ 现在 server/cfg 是"原始解构"状态；找出空/极小的
small = []
for f in sorted(os.listdir(DST)):
    if not f.endswith('.json'):
        continue
    if os.path.getsize(os.path.join(DST, f)) < 200:
        small.append(f[:-5])
print('  ② 原始解构后，空/极小 %d 个：%s' % (len(small), small[:14]))

# ★ 只对这 70 个跑自动解构
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import config_deconstruct as cd          # noqa: E402

SRC = os.path.join(ROOT, '_tmp_cfg')
saved = []
for name in small:
    p = os.path.join(SRC, name + '.luac')
    dst = os.path.join(DST, name + '.json')
    if not os.path.exists(p):
        continue
    try:
        rr = cd.parse_file(p)
    except Exception:
        continue
    best = None
    for pi, pr in enumerate(rr.protos):
        try:
            s = json.dumps(cd.to_jsonable(cd.deconstruct(p, proto_index=pi)), ensure_ascii=False)
        except Exception:
            continue
        if best is None or len(s) > len(best[1]):
            best = (pi, s)
    if best and len(best[1]) >= 200:
        with open(dst, 'w', encoding='utf-8', newline='\n') as f:
            f.write(best[1])
        saved.append((name, len(best[1]), best[0], len(rr.protos)))

print('\n  ③ ★ 救回 %d 个（原来空、现在有数据）：' % len(saved))
for n, sz, pi, np_ in saved:
    print('     %-38s %7d 字符（proto%d/%d）' % (n, sz, pi, np_))
print('\n  ④ 非空的文件**一律未动**（保护已有数据）✓')
