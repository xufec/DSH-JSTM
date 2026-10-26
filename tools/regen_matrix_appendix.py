"""重新生成能力矩阵的附录 A（覆盖率全量表）与 logs/_cmd_coverage.txt。

用法：python tools/regen_matrix_appendix.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX = os.path.join(ROOT, 'analysis', '1.4.9', 'server_capability_matrix.md')
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
COV = os.path.join(ROOT, 'logs', '_cmd_coverage.txt')
HEADER = '## 附录 A：客户端请求 vs 服务端应答（全量，自动生成）'
DESIGN_NO_REPLY = {'10001', '10300', '15801'}


def main():
    req, rep = {}, {}
    with io.open(LOG, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.search(r'>> cmd=(\d+)', line)
            if m:
                req[m.group(1)] = req.get(m.group(1), 0) + 1
                continue
            m = re.search(r'<< (\d{3,5})\b', line)
            if m:
                rep[m.group(1)] = rep.get(m.group(1), 0) + 1

    keys = sorted(set(req) | set(rep), key=lambda c: int(c))
    rows, n_ok, n_gap, n_by, n_push = [], 0, 0, 0, 0
    for c in keys:
        q, r = req.get(c, 0), rep.get(c, 0)
        if q == 0 and r > 0:
            st, n_push = '仅服务端推送', n_push + 1
        elif c in DESIGN_NO_REPLY:
            st, n_by = '设计不应答', n_by + 1
        elif r > 0:
            st, n_ok = '✅应答', n_ok + 1
        else:
            st, n_gap = '❌缺口', n_gap + 1
        rows.append('| %s | %d | %d | %s |' % (c, q, r, st))

    src = io.open(MATRIX, encoding='utf-8').read()
    idx = src.find(HEADER)
    if idx < 0:
        print('!! 找不到附录 A 标题'); sys.exit(2)
    app = [HEADER, '',
           '> 来源：`server/logs/tcp.log` 自动解析（工具：`tools/regen_matrix_appendix.py`）；',
           '> 同时落盘为 `logs/_cmd_coverage.txt`。',
           '> `状态` 取值：`✅应答` / `❌缺口` / `设计不应答` / `仅服务端推送`。',
           '>',
           '> 说明：`✅应答` 表示该命令至少被应答过一次；`仅服务端推送` 表示客户端不请求、由服务端主动推送',
           '> （`10200 10201 10500`）。请求/应答次数为日志累计值，噪声（重试）会导致次数不等。', '',
           '| CMD | 请求次数 | 应答次数 | 状态 |', '|---|---|---|---|'] + rows + [
           '',
           '合计：✅应答 **%d** 条 · ❌缺口 **%d** 条 · 设计不应答 **%d** 条 · 仅服务端推送 **%d** 条（共 %d 条命令）'
           % (n_ok, n_gap, n_by, n_push, len(keys)), '']
    io.open(MATRIX, 'w', encoding='utf-8', newline='').write(src[:idx] + '\n'.join(app))

    with io.open(COV, 'w', encoding='utf-8', newline='') as f:
        for c in keys:
            f.write('%s\treq=%-5d\trep=%-5d\n' % (c, req.get(c, 0), rep.get(c, 0)))

    print('附录已重建：共 %d 条（客户端请求 %d 条；应答 %d / 缺口 %d / 设计不应答 %d / 仅推送 %d）'
          % (len(keys), len(req), n_ok, n_gap, n_by, n_push))
    for c in ('10509', '10557', '12831', '12832', '12836'):
        print('   %s -> req=%d rep=%d' % (c, req.get(c, 0), rep.get(c, 0)))


if __name__ == '__main__':
    main()
