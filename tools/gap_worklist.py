# -*- coding: utf-8 -*-
"""**下一阶段工作清单生成器**：找出"真机在发、我们只回默认空响应"的命令，按真机热度排序。

为什么需要它：`_GENERIC_DEFAULT_CMDS` 的"通用默认响应"能保证**结构正确、不卡死**，
但对**带返回数值的动作/查询类命令**，它会让客户端把 0 当真值（R81 饱食度就是这么坏的）。
所以需要一份**按真机热度排序**的清单来决定先修哪条 —— 而不是凭感觉挑。

数据来源（全部可复核）：
  · `server/logs/tcp.log` —— 真机真实流量（`>> cmd=N` 与 `<< N <描述>` 配对）
  · `protocol/fields.json` —— SC 字段规格（给出该命令"本该发什么"）

用法：
    python tools/gap_worklist.py                 # 前 30 条
    python tools/gap_worklist.py --top 90        # 全部 90 条
    python tools/gap_worklist.py --cmd 16602     # 只看某条
    python tools/gap_worklist.py --md out.md     # 输出 markdown 表
"""
import argparse
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')


def scan(path, tail=0):
    """返回 (发送次数, 默认响应次数) 两个 dict。`tail>0` 时只看最后 N 行。

    ⚠ 必须能只看**最近**日志：否则会把"已经修好的命令"（如 `16605`，R86 已实现）
      的历史默认响应也统计进来，清单就不再反映**当前**缺口。
    """
    sent, dflt = {}, {}
    req = None
    if tail:
        with open(path, encoding='utf-8', errors='replace') as f:
            buf = f.readlines()[-tail:]
    else:
        with open(path, encoding='utf-8', errors='replace') as f:
            buf = f.readlines()
    for ln in buf:
        m = re.search(r'>> cmd=(\d+)', ln)
        if m:
            req = int(m.group(1))
            sent[req] = sent.get(req, 0) + 1
            continue
        m2 = re.search(r'<< (\d+) ', ln)
        if m2 and req is not None and int(m2.group(1)) == req:
            if '默认响应' in ln:
                dflt[req] = dflt.get(req, 0) + 1
            req = None
    return sent, dflt


def sc_field_names(fields, cmd):
    for k, v in fields.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return [f.get('name') for f in (v.get('fields') or []) if f.get('name')]
    return []


def cfg_candidates(names):
    """按 SC 字段名去本地**已提取的配置表**里找可能的支撑（只做名字匹配，供人工复核）。

    这一步**只给线索，不下结论** —— 最终"能不能做真实数据"必须靠人看配置内容
    （方案 §P0-3 的统一验收：每条命令要能指到"数据来自哪张原版配置表 / 哪张 DB 表"）。
    """
    import glob
    cfgs = []
    for pat in (os.path.join(ROOT, 'server', '*.json'),
                os.path.join(ROOT, 'analysis', '1.4.9', 'task', '*.json'),
                os.path.join(ROOT, '_tmp_cfg', '*.json')):
        cfgs += glob.glob(pat)
    keys = set()
    for n in names:
        for part in re.split(r'[_\d]+', n or ''):
            if len(part) >= 4:
                keys.add(part.lower())
    hits = []
    for p in cfgs:
        b = os.path.basename(p).lower()
        for k in keys:
            stem = k[:5]
            if stem and stem in b:
                hits.append(os.path.basename(p))
                break
    return sorted(set(hits))[:3]


def sc_fields(fields, cmd):
    """取 SC 的字段摘要字符串。"""
    for k, v in fields.items():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            fs = v.get('fields') or []
            return ', '.join('%s:%s' % (f.get('name'), f.get('type'))
                             for f in fs)[:150] or '（无字段）'
    return '（fields.json 无 SC 定义）'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--tail', type=int, default=20000,
                    help='只看日志最后 N 行（0=全部）；默认 2 万行 ≈ 一个服务端周期')
    ap.add_argument('--triage', action='store_true',
                    help='输出分诊表（SC 顶层字段 + 可能的配置支撑 + 处置建议）')
    ap.add_argument('--cmd', type=int)
    ap.add_argument('--md')
    args = ap.parse_args()

    fields = json.load(open(FIELDS, encoding='utf-8'))
    sent, dflt = scan(LOG, args.tail)
    rows = sorted(dflt.items(), key=lambda kv: -kv[1])
    if args.cmd:
        rows = [(args.cmd, dflt.get(args.cmd, 0))]
    rows = rows[:args.top]

    lines = ['| # | 命令 | 默认响应 | 真机总发 | SC 结构（本该发什么） |',
             '|---|---|---|---|---|']
    for i, (cmd, n) in enumerate(rows, 1):
        lines.append('| %d | `%d` | %d | %d | %s |'
                     % (i, cmd, n, sent.get(cmd, 0), sc_fields(fields, cmd)))

    if args.triage:
        lines = ['| # | 命令 | 默认响应 | SC 顶层字段 | 可能的配置支撑 | 处置 |',
                 '|---|---|---|---|---|---|']
        for i, (cmd, n) in enumerate(rows, 1):
            names = sc_field_names(fields, cmd)
            cand = cfg_candidates(names)
            todo = '**看配置可否做真实数据**' if cand else '结构正确空表 + 诚实说明'
            lines.append('| %d | `%d` | %d | %s | %s | %s |'
                         % (i, cmd, n, ', '.join(names)[:60],
                            ', '.join('`%s`' % c for c in cand) or '（未找到候选）', todo))

    out = '\n'.join(lines)
    if args.md:
        open(args.md, 'w', encoding='utf-8', newline='\n').write(out + '\n')
        print('已写出 %s（%d 行）' % (args.md, len(rows)))
    else:
        print(out)
    print('\n真机发过 %d 种命令；其中**只回默认响应**的 %d 种（统计范围：最后 %d 行）'
          % (len(sent), len(dflt), args.tail))


if __name__ == '__main__':
    main()
