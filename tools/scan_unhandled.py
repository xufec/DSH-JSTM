# -*- coding: utf-8 -*-
"""★ 找出"**既不在任何集合、也无专用实现**"的命令 —— 统计盲区自查。

## 为什么

`tools/gap_verdicts.py` 的"未实现" = `(_GENERIC_DEFAULT_CMDS | _UNSUPPORTED_ACTION_CMDS) - 已实现`。
但 R132 发现：**成长命令**（`11601`/`15703`/`18906`…）**既不在两个集合里、也没有专用实现**
⇒ 它们落到**最后的兜底路径** ⇒ **根本不进那个统计**！

⇒ 本脚本把这类命令列出来（这才是"真实缺口"的完整集合）。
判据：`fields.json` 里有 SC 或 CS 定义，但服务端**既不在两个集合、也没有 `if cmd == N` / `if cmd in (...)`**。

用法： python tools/scan_unhandled.py
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

# 所有有协议定义的命令
ALL = {}
for k, v in FIELDS.items():
    c = str(v.get('cmd') or '')
    if c.isdigit():
        ALL.setdefault(int(c), {'cs': False, 'sc': False, 'file': v.get('file')})
        if v.get('dir') in ('cs', 'sc'):
            ALL[int(c)][v.get('dir')] = True

unhandled = sorted(c for c in ALL if c not in GEN and c not in UNS and c not in EQ)
print('  协议命令总数: %d' % len(ALL))
print('  两个集合: %d ｜ 专用实现: %d' % (len(GEN | UNS), len(EQ)))
print('  ★ **既不在集合、也无专用实现**: %d 条\n' % len(unhandled))

# 按前缀（家族）聚合
fam = {}
for c in unhandled:
    fam.setdefault(str(c)[:3], []).append(c)
for pfx in sorted(fam, key=lambda p: -len(fam[p])):
    lst = fam[pfx]
    print('  %sxx  %2d 条: %s' % (pfx, len(lst), ','.join(map(str, lst[:14]))))
