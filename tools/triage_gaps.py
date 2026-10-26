#!/usr/bin/env python3
"""GAP 分类（triage）：把「有 SC 规格却无应答」的命令，按**客户端是否真的消费应答**分档。

## 判据

客户端注册应答处理器的命名约定（本仓库全线可用）：

    on<cmd>  /  handle<cmd>  /  hander<cmd>  /  Handle<cmd>  /  on_<cmd>

于是：

| 分类 | 含义 | 该不该补 |
|---|---|---|
| **无处理器** | 客户端发了却不处理回包（上报/广播型，如 10300、10999） | ⇒ 无应答**无害**，可不做 |
| **有处理器** | 客户端在等数据（面板/状态） | ⇒ **真实缺口**，按价值排期 |

进一步，对"有处理器"的命令再标注处理器所在模块，便于判断属于哪个玩法。

## 用法

    python tools/triage_gaps.py --json analysis/1.4.9/replay_r39.json
    python tools/triage_gaps.py --json ... --out analysis/1.4.9/gap_triage.json
"""
import argparse
import collections
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')

PATTERNS = ['on%d', 'handle%d', 'hander%d', 'Handle%d', 'on_%d', 'handle_%d']


def scan_handlers(cmds):
    """-> {cmd: [文件, ...]}；只做字节级精确匹配，快且稳。"""
    z = zipfile.ZipFile(APK)
    members = [n for n in z.namelist() if n.endswith('.luac')]
    pats = {c: [p % c for p in PATTERNS] for c in cmds}
    hits = collections.defaultdict(set)
    for n in members:
        try:
            d = z.read(n)
        except Exception:
            continue
        if not d:
            continue
        short = n.split('/')[-1]
        for c, ps in pats.items():
            if c in hits and len(hits[c]) >= 6:
                continue
            for p in ps:
                if p.encode() in d:
                    hits[c].add(short)
                    break
    return {c: sorted(v) for c, v in hits.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', required=True, help='回放审计 JSON（取其中的 GAP 行）')
    ap.add_argument('--out')
    ap.add_argument('--limit', type=int, default=40)
    args = ap.parse_args()

    with open(args.json, encoding='utf-8') as f:
        rep = json.load(f)
    gaps = sorted({r['cmd'] for r in rep['rows'] if r['kind'] == 'GAP'})
    print('# 回放报告 %s：GAP %d 条' % (os.path.basename(args.json), len(gaps)))

    hits = scan_handlers(gaps)
    withh = [c for c in gaps if c in hits]
    noh = [c for c in gaps if c not in hits]

    print()
    print('=== 分类 ===')
    print('  ★ 有客户端处理器（真实缺口，客户端在等数据）: %d' % len(withh))
    print('  · 无客户端处理器（无应答无害，可不做）      : %d' % len(noh))
    print()
    print('--- ★ 真实缺口（按处理器模块）---')
    for c in withh:
        print('  %-6d %s' % (c, ', '.join(hits[c][:4])))
    print()
    print('--- · 无害缺口（客户端无处理器）---')
    print('  ' + ', '.join(str(c) for c in noh))

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump({'gap_total': len(gaps),
                       'real_gaps': {str(c): hits[c] for c in withh},
                       'harmless': noh},
                      f, ensure_ascii=False, indent=1)
        print('\n已写出 %s' % args.out)


if __name__ == '__main__':
    main()
