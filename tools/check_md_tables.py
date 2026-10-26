#!/usr/bin/env python3
"""正确统计 Markdown 表格列数：忽略反引号代码跨度内的 '|'，并识别转义 '\\|'。

用法：python tools/check_md_tables.py analysis/1.4.9/item/*.md
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def split_row(line):
    """按未转义、且不在 `...` 内的 '|' 切分。"""
    cells = []
    cur = []
    in_code = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '\\' and i + 1 < len(line) and line[i + 1] == '|':
            cur.append('|')
            i += 2
            continue
        if ch == '`':
            in_code = not in_code
            cur.append(ch)
            i += 1
            continue
        if ch == '|' and not in_code:
            cells.append(''.join(cur))
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append(''.join(cur))
    # 去掉首尾空单元（行首/行尾的 '|'）
    if cells and cells[0].strip() == '':
        cells = cells[1:]
    if cells and cells[-1].strip() == '':
        cells = cells[:-1]
    return cells


def main():
    total_bad = 0
    for path in sys.argv[1:]:
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding='utf-8').read().split('\n')
        groups = []
        cur = []
        for i, l in enumerate(lines):
            if l.lstrip().startswith('|'):
                cur.append((i + 1, l))
            else:
                if cur:
                    groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
        bad = 0
        for g in groups:
            counts = [len(split_row(l)) for _, l in g]
            if len(set(counts)) > 1:
                bad += 1
                print('  !! %s 表(起始行 %d) 列数不一致: %s'
                      % (os.path.basename(path), g[0][0], counts))
        print('%-34s 表格 %d 个, 列数不一致 %d 个' %
              (os.path.basename(path), len(groups), bad))
        total_bad += bad
    print('\n合计异常表格: %d' % total_bad)
    return 1 if total_bad else 0


if __name__ == '__main__':
    sys.exit(main())
