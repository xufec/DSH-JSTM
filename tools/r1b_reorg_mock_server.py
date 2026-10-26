#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理 `server/mock_server.py`：把**已下沉模块后留下的注释副本**搬到独立归档文件。

## 为什么这样做（安全第一）
`mock_server.py` 20,337 行里有 **3,301 行** 是「代码已迁到 `server/<pkg>/`、原文仍以注释
留在原地」的副本（`[P2X-migrated …]`）。它们不参与执行，但占了 16.2% 的篇幅，
让主线被淹没。

三种处置：
  A 原样保留 —— 零风险，但噪音大
  B **搬到 `server/_migrated_archive.py`**（纯注释文件，不被 import）← **本脚本采用**
  C 直接删除 —— 会丢唯一副本，**不采用**

**B 的好处**：主文件瘦身、历史 100% 保留、可随时 diff 比对、且不影响任何执行路径。

## 精确性
用 Python 标准库 `tokenize` 判定「某行是否只有注释」——
**不会**误伤字符串字面量里的 `#`，也**不会**误伤 docstring。

## 纪律
- 只搬「连续 ≥5 行、且首行含 `migrated`」的**整块注释**
- 每块在主文件原位留**一行指针**（同缩进），保证行内结构与缩进合法
- 改前已有备份 `server/mock_server.py.bak_r1b_20261017`
"""
import io
import os
import re
import sys
import tokenize

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'mock_server.py')
ARC = os.path.join(ROOT, 'server', '_migrated_archive.py')

MIN_BLOCK = 5
NEED_MARK = 'migrated'


def comment_only_lines(path):
    """返回 {行号: 纯注释行文本}（仅当该行**只有一个 COMMENT token 且无代码**）。"""
    out = {}
    by_line = {}
    with open(path, 'rb') as f:
        for tok in tokenize.tokenize(f.readline):
            if tok.type in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER):
                continue
            by_line.setdefault(tok.start[0], []).append(tok)
    for ln, toks in by_line.items():
        if len(toks) == 1 and toks[0].type == tokenize.COMMENT:
            out[ln] = toks[0].string
    return out


def main():
    raw = open(SRC, encoding='utf-8', newline='').read()
    lines = raw.split('\n')
    co = comment_only_lines(SRC)
    print('纯注释行: %d' % len(co))

    # 连续块
    runs = []
    cur = []
    for ln in range(1, len(lines) + 1):
        if ln in co:
            cur.append(ln)
        else:
            if len(cur) >= MIN_BLOCK:
                runs.append(cur)
            cur = []
    if len(cur) >= MIN_BLOCK:
        runs.append(cur)

    picked = [r for r in runs if NEED_MARK in lines[r[0] - 1]]
    moved_lines = sum(len(r) for r in picked)
    print('连续注释块≥%d: %d 块 ｜ 其中首行含 %r: %d 块 / %d 行'
          % (MIN_BLOCK, len(runs), NEED_MARK, len(picked), moved_lines))
    if not picked:
        print('没有可搬的块')
        return 0

    # 归档文件
    A = []
    A.append('# -*- coding: utf-8 -*-')
    A.append('"""`mock_server.py` 的**迁移留档**（纯注释，不被任何模块 import）。')
    A.append('')
    A.append('本文件由 `tools/r1b_reorg_mock_server.py` 生成。')
    A.append('内容 = 原 `mock_server.py` 中「代码已下沉到 `server/<pkg>/`、原文以注释保留」的整块副本。')
    A.append('搬出目的：让主文件主线清晰；**历史 100% 保留**，可随时与模块实现 diff 比对。')
    A.append('')
    A.append('⚠ 本文件**不参与执行**：全为注释，import 它没有任何效果。')
    A.append('"""')
    A.append('')

    # 逐块搬出（从后往前替换，避免行号漂移）
    out_lines = list(lines)
    ptr_of = {}
    for r in picked:
        s, e = r[0], r[-1]
        indent = re.match(r'^\s*', lines[s - 1]).group(0)
        block = lines[s - 1:e]
        A.append('# ' + '=' * 74)
        A.append('# 原 mock_server.py L%d–L%d（共 %d 行）' % (s, e, len(block)))
        A.append('# ' + '=' * 74)
        A.extend(block)
        A.append('')
        arc_line = len(A)  # 该块在归档中的结束行
        ptr_of[(s, e)] = arc_line
        out_lines[s - 1:e] = ['%s# [已迁出] 原 L%d–L%d（%d 行 migrated 留档）'
                               '→ server/_migrated_archive.py 同名块'
                               % (indent, s, e, len(block))]

    new_src = '\n'.join(out_lines)

    # 顶部导航（若尚未加过）
    TOC = build_toc(out_lines, moved_lines, len(picked))
    if 'MOCK_SERVER 导航' not in new_src[:4000]:
        # 插到第一个 import 之前（即文件头注释之后）
        idx = 0
        for i, l in enumerate(new_src.split('\n')[:80]):
            if re.match(r'^(import|from)\s', l):
                idx = i
                break
        nl = new_src.split('\n')
        nl[idx:idx] = TOC.split('\n')
        new_src = '\n'.join(nl)

    with open(ARC, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(A) + '\n')
    with open(SRC, 'w', encoding='utf-8', newline='') as f:
        f.write(new_src)

    print('搬出 %d 块 / %d 行 → %s' % (len(picked), moved_lines,
                                    os.path.relpath(ARC, ROOT)))
    print('主文件: %d 行 → %d 行（- %d）'
          % (len(lines), len(new_src.split('\n')),
             len(lines) - len(new_src.split('\n'))))
    return 0


def build_toc(out_lines, moved, nblocks):
    """生成主文件顶部的导航块（纯注释）。"""
    L = []
    L.append('# ' + '=' * 76)
    L.append('# MOCK_SERVER 导航（自动生成，人工可改）')
    L.append('# ' + '=' * 76)
    L.append('# 【这是什么】《绝世唐门》私服的游戏服务端：单进程 Python，纯标准库零依赖。')
    L.append('#   TCP 9000 = 游戏协议；HTTP 8080 = 资源面 + /DSH_ADMIN 管理面 + /GM 后台。')
    L.append('#')
    L.append('# 【主线怎么读】')
    L.append('#   1) class Handler  → handle()         TCP 主循环：收帧 → FrameParser → 分发')
    L.append('#   2) 主分发链       → if cmd == N / if cmd in (...)   约 376 个分支')
    L.append('#   3) 分支用到的东西 → build_*() 组帧 ; db_*() 存取 ; mission_*/scene_*/battle_*')
    L.append('#   4) 兜底           → global_default_sc（★ 必须在所有专用分支之后）')
    L.append('#   5) HTTP 侧        → class Handler do_GET：/GM → gm.console；/DSH_ADMIN/* → 管理面')
    L.append('#')
    L.append('# 【分区（按行号，实测）】')
    for name, a, b in (
            ('A 文件头 / 导入 / 全局变量', 1, 120),
            ('B 场景与 AOI 基础件', 121, 600),
            ('C HTTP Handler：管理面 + 资源面', 601, 2600),
            ('D 协议底座：编码器 / 字段 / 默认响应 / 权威编码器', 2601, 7000),
            ('E 业务辅助：db_* / build_* / mission_* / scene_*', 7001, 9800),
            ('F TCP 主处理：分发主链', 9801, 17200),
            ('G 战斗 / 挂机 / 场景内链（154xx / 200xx）', 17201, 18300),
            ('H 登录 / 活动 / 邮件 / 伙伴 / 场景重推', 18301, 20000),
            ('I 全局兜底 + main()', 20001, 99999)):
        L.append('#      %-52s L%d–L%d' % (name, a, b))
    L.append('#   ※ 行号会随编辑漂移；以 banner 搜索为准（搜「====」或「★★★」）。')
    L.append('#')
    L.append('# 【改之前必看】')
    L.append('#   · 新增专用分支后，务必确认它**不在** _GENERIC_DEFAULT_CMDS / 旧元组里，')
    L.append('#     否则会被全局兜底抢先命中（门禁：tools/lint_dispatch_shadow.py）。')
    L.append('#   · .get(k, default) 对「键存在但值为 None」返回 None —— 曾导致定时异常刷屏。')
    L.append('#   · CS body 尾部有 4 字节脏数据：只读规格前 N 字节。')
    L.append('#   · code==1 才是成功；唯一例外 10200 要 code==0。')
    L.append('#')
    L.append('# 【本文件已瘦身】')
    L.append('#   原有 %d 块 / %d 行「已下沉模块的注释副本」占篇幅却不可执行，' % (nblocks, moved))
    L.append('#   已搬到 server/_migrated_archive.py（纯注释，不被 import），原位留一行指针。')
    L.append('#   结构全图见 docs/mock_server_结构图.md。')
    L.append('# ' + '=' * 76)
    L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    sys.exit(main())
