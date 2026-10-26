# -*- coding: utf-8 -*-
"""R192（新目标④）：**解构器工程 —— 自动选"主 proto"**。

## ★ 发现（`_diag_r192b.txt`）

| 配置 | 各 proto 的指令数 | **主 proto** | 用对后的结果 |
|---|---|---|---|
| `config_item` | 91 / **65483** | **proto1** | `Config`（120 字符）|
| `config_skill` | **69601** / 137 / 40 | **proto0** | `Config`（737 字符）|
| `config_mon_data` | **58359** / 71 / 33 | **proto0** | `Config`（311 字符）|
| `config_common` | **57** | proto0 | ★ **13 个顶层键**（1365 字符）✓ |

★★ **根因**：`batch_deconstruct.py` 用 `deconstruct(path, proto_index=0)`，
   **但"主 chunk"不一定是 proto0**（`config_item` 的是 **proto1**！）
   ⇒ **解构出 2 B**。

★ **本脚本的修**：**先 parse，选出"指令数最多的 proto"作主 chunk**，再用它解构 ✓
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import config_deconstruct as cd          # noqa: E402  ★ 它的 import 会关掉 stdout

ROOT0 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = open(os.path.join(ROOT0, 'analysis', '1.4.9', '_deconstruct_auto.txt'),
           'w', encoding='utf-8', newline='\n')


def print(*a):                            # ★ 覆盖内置 print ⇒ 只写日志文件（stdout 已不可用）
    LOG.write(' '.join(str(x) for x in a) + '\n')
    LOG.flush()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_tmp_cfg')
DST = os.path.join(ROOT, 'server', 'cfg')
os.makedirs(DST, exist_ok=True)

files = sorted(f for f in os.listdir(SRC) if f.endswith('.luac'))
print('  _tmp_cfg 里有 %d 个 .luac' % len(files))

ok, empty, better, skipped = 0, [], [], []
for fn in files:
    name = fn[:-5]
    p = os.path.join(SRC, fn)
    dst = os.path.join(DST, name + '.json')
    old_sz = os.path.getsize(dst) if os.path.exists(dst) else 0
    try:
        r = cd.parse_file(p)
    except Exception as e:
        print('  ✗ %-34s parse 失败 %r' % (name, e))
        continue
    # ★ 选"指令数最多"的 proto 作主 chunk
    best_pi, best_n = 0, -1
    for pi, pr in enumerate(r.protos):
        n = len(pr.bc)
        if n > best_n:
            best_pi, best_n = pi, n
    got = None
    for pi in [best_pi] + [i for i in range(len(r.protos)) if i != best_pi]:
        try:
            j = cd.to_jsonable(cd.deconstruct(p, proto_index=pi))
            s = json.dumps(j, ensure_ascii=False)
            if got is None or len(s) > len(got[1]):
                got = (j, s, pi)
            if len(s) > 200:
                break
        except Exception:
            continue
    if got is None:
        empty.append(name)
        continue
    j, s, pi = got
    new_sz = len(s)
    # ★★ 安全：**只在"新结果比旧的大"时覆盖** ——
    #   否则会把原来正确的解构结果（来自另一个 proto）覆盖成更差的版本
    #   （R192 第一版实测：`config_skill_xiulian` 156585 → 129129，就是被覆盖坏的）
    if new_sz < 40:
        empty.append(name)
        continue
    if new_sz <= old_sz:
        skipped.append((name, old_sz, new_sz, pi))
        continue
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(j, ensure_ascii=False, indent=1))
    ok += 1
    if new_sz > old_sz + 40:
        better.append((name, old_sz, new_sz, pi, len(r.protos)))
    if 'item' in name or 'skill' in name or 'common' in name or 'mon' in name:
        print('  %-34s proto%d/%d ⇒ %d 字符（原 %d）' % (name, pi, len(r.protos), new_sz, old_sz))

print('\n  ★ 成功解构（且不劣于原结果）%d 个；仍空 %d 个；跳过（新结果不大于旧的）%d 个'
      % (ok, len(empty), len(skipped)))
print('  ★ 明显改善（+40 字符以上）的 %d 个：' % len(better))
for n, o, w, pi, np_ in better[:24]:
    print('     %-36s %6d → %6d（proto%d/%d）' % (n, o, w, pi, np_))
if empty:
    print('  仍空: %s' % empty[:20])
