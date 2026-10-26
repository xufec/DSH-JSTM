# -*- coding: utf-8 -*-
"""★ 修正统计口径：把"未处理"的命令按 **CS/SC 方向** 分类，找出**真正需要应答**的。

## 为什么必须分类

`tools/scan_unhandled.py` 找到 **1360 条**"既不在集合、也无专用实现"的命令。
但其中：

  · **CS-only**（只有 `CS_`、没有 `SC_`）⇒ 客户端**上报**（日志/统计）⇒ 服务端**不该答** ✓
  · **SC-only**（只有 `SC_`、没有 `CS_`）⇒ 服务端**该主动推**（另论）
  · **CS+SC** ⇒ ★ **客户端会问、服务端必须答** ⇒ **这才是真正的缺口**

用法： python tools/scan_unhandled.py --by-dir
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = json.load(open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8'))

src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
s2 = re.sub(r'#[^\n]*', '', src)


def grab(name):
    m = re.search(name + r'\s*=\s*frozenset\(\[(.*?)\]\)', s2, re.S)
    return set(int(x) for x in re.findall(r'\b\d{4,5}\b', m.group(1))) if m else set()


GEN = grab('_GENERIC_DEFAULT_CMDS')
UNS = grab('_UNSUPPORTED_ACTION_CMDS')
EQ = set(int(x) for x in re.findall(r'if cmd == (\d{4,5}):', s2))
for mm in re.finditer(r'if cmd in \(([^)]*)\):', s2):
    for x in re.findall(r'\d{4,5}', mm.group(1)):
        EQ.add(int(x))
# ★★★ R172：**`if cmd in _VAR:`（变量集合）也要认** ——
#   R171 引入数据驱动写法（`_R171 = {...}` + `if cmd in _R171:`），
#   而本脚本**只认字面量元组** ⇒ 把已实现的 21 条**误算成"未实现"**（清单里一直有它们）。
#   ★ 这与门禁 G 原来的盲区是**同一个** ⇒ 凡"扫源码判已实现"的工具都要支持变量集合。
for mm in re.finditer(r'if cmd in (_[A-Za-z0-9_]+):', s2):
    _var = mm.group(1)
    _m2 = re.search(re.escape(_var) + r'\s*=\s*\{(.*?)\n\}', s2, re.S)
    if _m2:
        for x in re.findall(r'\b(\d{4,6})\s*:', _m2.group(1)):
            EQ.add(int(x))

ALL = {}
for k, v in FIELDS.items():
    c = str(v.get('cmd') or '')
    if c.isdigit() and len(c) >= 4:
        d = ALL.setdefault(int(c), {'cs': False, 'sc': False})
        if v.get('dir') in ('cs', 'sc'):
            d[v.get('dir')] = True

unhandled = [c for c in ALL if c not in GEN and c not in UNS and c not in EQ]
cs_only = [c for c in unhandled if ALL[c]['cs'] and not ALL[c]['sc']]
sc_only = [c for c in unhandled if ALL[c]['sc'] and not ALL[c]['cs']]
both = [c for c in unhandled if ALL[c]['cs'] and ALL[c]['sc']]

print('  未处理（既不在集合、无专用实现）: %d 条' % len(unhandled))
print('    · **CS-only**（客户端上报，不该答）: %d 条' % len(cs_only))
print('    · **SC-only**（服务端该推）        : %d 条' % len(sc_only))
print('    · **CS+SC**（★ 客户端会问、必须答）: %d 条\n' % len(both))

fam = {}
for c in sorted(both):
    fam.setdefault(str(c)[:3], []).append(c)
print('  ★ CS+SC 未处理，按家族（前 20）：')
for pfx in sorted(fam, key=lambda p: -len(fam[p]))[:20]:
    print('    %sxx  %2d 条: %s' % (pfx, len(fam[pfx]), ','.join(map(str, fam[pfx][:12]))))

# 落盘，供后续批次用
out = os.path.join(ROOT, 'analysis', '1.4.9', '_unhandled_cs_sc.txt')
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(map(str, sorted(both))) + '\n')
print('\n  CS+SC 全清单已写入 %s（%d 条）' % (out, len(both)))
