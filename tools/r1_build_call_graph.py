#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1.3-④：**proto 级调用图**（替代"自研完整 LuaJIT 反编译器"）。

## 先说清能力边界（不夸大）
**自研一个可用的 LuaJIT 2.0 反编译器，本项目做不到**，理由：
  - LuaJIT 字节码是寄存器机 + 轨迹优化产物，**没有可靠的局部变量/表达式还原**；
  - 上游没有成熟的开源 LuaJIT 反编译器可用（`unluac` 只支持标准 Lua 5.1，不支持 LuaJIT）；
  - 强行做一个"能看个大概"的反编译器，产出的伪代码**无法作为证据**，反而违反
    "不把推断写成确认"的纪律。

**因此本步交付的是"函数级调用图"**——不还原函数体，但把
`每个 proto 调用了哪些名字（方法/全局）` 抽出来，配合"名字 → 定义处"索引，
足以回答 Agent 最常问的两个问题：
  1. **"这个函数被谁调用？"**（反向：名字 → 引用它的 luac#proto）
  2. **"这个函数调用了什么？"**（正向：proto → 名字集合）

## 字节码口径
LuaJIT 的方法调用形态固定为：
    TGETS/GGET/TGETV  <callee>   ← 取被调名
    (MOV/DUP 传 self 与参数)
    CALL             A=nargs
⇒ 对每个 `CALL`，**回看最多 10 条**最近一次 `TGETS/GGET/TGETV`，取其名字作为被调名。
标 `heuristic` —— 这是**静态近似**，不是精确的数据流分析。

用法：python tools/r1_build_call_graph.py [版本，默认 1.4.11]
产出：analysis/r1_client_index/R1_函数级调用图_<版本>.json
"""
import json
import os
import sys
import zipfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index')

APKS = {'1.3.0': r'anzbao\dldlJl.apk',
        '1.4.9': r'anzbao\jstm.apk',
        '1.4.11': r'anzbao\jstm_142165.apk'}

NAME_OPS = ('TGETS', 'GGET', 'TGETV')
LOOKBACK = 10


def proto_calls(pt):
    """返回该 proto 调用的名字集合（去重，保留出现顺序）。"""
    bc = getattr(pt, 'bc', None) or []
    ops = [(OPS[w & 0xff], (w >> 8) & 0xff, (w >> 16) & 0xffff) for w in bc]
    out = []
    for i, (op, a, d) in enumerate(ops):
        if op != 'CALL':
            continue
        for j in range(i - 1, max(-1, i - 1 - LOOKBACK), -1):
            o2, a2, d2 = ops[j]
            if o2 in NAME_OPS:
                nm = kidx(pt, d2)
                if isinstance(nm, str) and 1 < len(nm) < 60:
                    out.append(nm)
                break
    seen, res = set(), []
    for n in out:
        if n not in seen:
            seen.add(n)
            res.append(n)
    return res


def main():
    ver = sys.argv[1] if len(sys.argv) > 1 else '1.4.11'
    apk = os.path.join(ROOT, APKS[ver])
    print('版本 %s  APK %s' % (ver, APKS[ver]))
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.endswith('.luac')]
    graph = {}
    name_index = defaultdict(list)
    stat = Counter()
    fails = []
    for i, n in enumerate(names):
        try:
            r = parse_bytes(z.read(n))
        except Exception as e:
            fails.append({'path': n, 'error': repr(e)})
            continue
        protos = []
        for pi, pt in enumerate(r.protos):
            calls = proto_calls(pt)
            if calls:
                protos.append({'p': pi, 'calls': calls})
                for c in calls:
                    name_index[c].append('%s#%d' % (n, pi))
            stat['protos'] += 1
            if calls:
                stat['protos_with_calls'] += 1
        if protos:
            graph[n] = protos
            stat['luac_with_calls'] += 1
        if (i + 1) % 500 == 0:
            print('    %d/%d' % (i + 1, len(names)))
    z.close()

    # 反向索引瘦身：只保留**被多处引用**的名字（Agent 查"谁调用 X"最常用）
    hot = {k: v for k, v in name_index.items() if len(v) >= 2}
    out = {
        '_meta': {
            'phase': 'R1.3', 'step': '04_call_graph',
            'generated_by': 'tools/r1_build_call_graph.py',
            'version': ver,
            'capability_boundary': '**不交付 LuaJIT 反编译器**。理由：LuaJIT 字节码为寄存器机，'
                                   '无可用的开源反编译器（unluac 只支持标准 Lua 5.1）；'
                                   '强行产出伪代码无法作为证据，违反"不把推断写成确认"。'
                                   '本步交付**函数级调用图**，回答"谁调用谁"。',
            'method': '对每个 CALL，回看最多 %d 条最近一次 TGETS/GGET/TGETV 取其名字' % LOOKBACK,
            'evidence': 'heuristic（静态近似，非精确数据流分析）',
            'graph_shape': 'luac 路径 → [{p: proto索引, calls: [被调名…]}]',
            'reverse_index': 'callee 名 → [luac#proto]（仅保留被 ≥2 处引用的名字）',
        },
        'stats': {
            'luac_scanned': len(names),
            'luac_parse_failed': len(fails),
            'luac_with_calls': stat['luac_with_calls'],
            'protos': stat['protos'],
            'protos_with_calls': stat['protos_with_calls'],
            'distinct_callee_names': len(name_index),
            'callee_names_referenced_ge2': len(hot),
        },
        'parse_failures': fails,
        'reverse_index_hot': {k: v[:60] for k, v in sorted(hot.items(), key=lambda x: -len(x[1]))},
        'graph': graph,
    }
    p = os.path.join(OUT, 'R1_函数级调用图_%s.json' % ver)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    print('luac %d（失败 %d）｜ proto %d（有调用 %d）｜ 被调名 %d（≥2 处引用 %d）'
          % (len(names), len(fails), stat['protos'], stat['protos_with_calls'],
             len(name_index), len(hot)))
    print('写出: %s (%d B)' % (os.path.basename(p), os.path.getsize(p)))
    print('Top 被引用名: %s' % [k for k, _ in sorted(name_index.items(),
                                                   key=lambda x: -len(x[1]))[:12]])


if __name__ == '__main__':
    main()
