#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SC 帧长奇偶校验：把**参考服真机抓包**里每条 SC 的字节长度，
与本服日志里同命令的帧长对照 ⇒ 自动筛出"结构可能不一致"的候选。

为什么要这样比：**帧长一致同时锁住字段宽度、顺序与表计数编码**
（round 17 用 `12405=246 / 12406=12` 验证过这个方法有效）。

诚实纪律（务必照看）：
  · 帧长**依赖载荷内容**（例如任务列表 7 项 vs 1 项）⇒ 长度不同**不一定是 bug**；
  · 本工具只产出 **CANDIDATE（待人工复核）**，**不自动判错、不改代码**；
  · 只有在"**同命令的最小/典型形态**都无交集"时，才值得怀疑结构。

用法：
  python tools/cmp_sc_lengths.py [参考日志...] --mine [本服日志...]
  默认：参考 = logs/1.4.9/*.log；本服 = logs/minloop/live*.log + stateful_replay_out.txt
"""
from __future__ import annotations

import collections
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 兼容两种日志形态：
#   参考服：`<< 12406 SC_12406 del_mission_list=[10010] (12 bytes)`   ← 带括号
#   本服  ：`<< 1110 SCAccountLogin … 39 bytes`                       ← 不带括号
TOL = 32          # 邻近容差（字节）：覆盖角色名/NPC 名等变长字符串造成的长度差
SC_RE = re.compile(r'<<\s+(\d{4,5})\b.*?(\d+)\s*bytes\)?')

try:                                    # Windows 控制台可能是 GBK ⇒ 强制 UTF-8（本项目通用做法）
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


def collect(paths):
    """{cmd: Counter(长度)}，只统计日志里 `<< <cmd> … (<N> bytes)` 形态的行。"""
    out = collections.defaultdict(collections.Counter)
    files = 0
    for p in paths:
        if not os.path.exists(p):
            continue
        files += 1
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                for line in f:
                    m = SC_RE.search(line)
                    if m:
                        out[int(m.group(1))][int(m.group(2))] += 1
        except OSError:
            pass
    return out, files


def main(argv):
    mine_flag = argv.index('--mine') if '--mine' in argv else -1
    if mine_flag > 0:
        ref_args = argv[1:mine_flag]
        mine_args = argv[mine_flag + 1:]
    else:
        ref_args, mine_args = [], argv[1:]

    ref_paths = ref_args or sorted(glob.glob(os.path.join(ROOT, 'logs', '1.4.9', '*.log')))
    mine_paths = mine_args or (
        sorted(glob.glob(os.path.join(ROOT, 'logs', 'minloop', 'live*.log')))
        + [os.path.join(ROOT, 'stateful_replay_out.txt')])

    ref, nref = collect(ref_paths)
    mine, nmine = collect(mine_paths)
    print('参考日志 %d 个 / 本服日志 %d 个' % (nref, nmine))
    print('%-8s %-28s %-28s %s' % ('命令', '参考服帧长(次数)', '本服帧长(次数)', '判定'))
    print('-' * 96)
    same = overlap = near = cand = only = 0
    for cmd in sorted(set(ref) | set(mine)):
        r = ref.get(cmd)
        m = mine.get(cmd)
        if r and not m:
            only += 1
            continue
        if m and not r:
            continue
        rl = ' '.join('%d×%d' % (L, n) for L, n in sorted(r.items())[:3])
        ml = ' '.join('%d×%d' % (L, n) for L, n in sorted(m.items())[:3])
        if set(r) & set(m):
            # 有交集：至少存在一次长度完全一致 ⇒ 结构大概率一致
            overlap += 1
            verdict = 'OK(有交集)'
        elif any(abs(a - b) <= TOL for a in r for b in m):
            # ★ round 22：**邻近容差** —— 帧长里有**变长字符串**（角色名/NPC 名/公会名等），
            #   名字长度不同就会造成几字节到几十字节的差（实测 `10303`：本服 209 vs 参考 192，
            #   差 17 字节 = 角色名长度差）。这类差异**不是结构错误**，不该长期误报。
            near += 1
            verdict = 'OK(邻近±%dB)' % TOL
        else:
            cand += 1
            verdict = '★ CANDIDATE'
        if verdict not in ('OK(有交集)',) and not verdict.startswith('OK(邻近'):
            print('%-8d %-28s %-28s %s' % (cmd, rl, ml, verdict))
    print('-' * 96)
    print('有交集 %d ｜ 邻近容差(%dB)内 %d ｜ ★待复核候选 %d ｜ 仅参考服有 %d' % (overlap, TOL, near, cand, only))
    print('说明：帧长依赖载荷(如任务列表项数)，**长度不同不等于 bug**；本工具只筛候选，不判错。')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

