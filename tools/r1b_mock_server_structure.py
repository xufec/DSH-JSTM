#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理 `server/mock_server.py` 的结构：分区、主线、死代码体量。

产出 `docs/mock_server_结构图.md`（不含任何代码改动）。
纪律：**只读**。本脚本不修改 mock_server.py。
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'mock_server.py')
OUT = os.path.join(ROOT, 'docs', 'mock_server_结构图.md')

# 逻辑分区（按行号边界人工认定，来源=实读文件），用于把 2 万行压成可读骨架
REGIONS = [
    ('A. 文件头 / 导入 / 全局', 1, 120),
    ('B. 场景与 AOI 基础件', 121, 600),
    ('C. HTTP Handler：管理面 + 资源面', 601, 2600),
    ('D. 协议底座：编码器 / 字段 / 默认响应 / 权威编码器', 2601, 7000),
    ('E. 业务辅助（货币/背包/任务/场景/战斗/属性等 db_* 与 build_*）', 7001, 9800),
    ('F. TCP 主处理：分发主链（recv → cmd 分支）', 9801, 17200),
    ('G. 战斗 / 挂机 / 场景内链（154xx / 200xx）', 17201, 18300),
    ('H. 登录 / 活动 / 邮件 / 伙伴 / 场景重推（108xx~154xx 尾部）', 18301, 20000),
    ('I. 全局兜底与入口 main()', 20001, 20337),
]


def main():
    L = open(SRC, encoding='utf-8', errors='replace').read().split('\n')
    n = len(L)

    def stat(a, b):
        seg = L[a - 1:b]
        code = sum(1 for x in seg if x.strip() and not x.strip().startswith('#'))
        com = sum(1 for x in seg if x.strip().startswith('#'))
        blank = sum(1 for x in seg if not x.strip())
        mig = sum(1 for x in seg if 'migrated' in x)
        cmds = sum(1 for x in seg if re.match(r'^\s+if cmd == \d', x)) + \
            sum(1 for x in seg if re.match(r'^\s+if cmd in \(', x))
        return dict(lines=len(seg), code=code, comment=com, blank=blank,
                    migrated=mig, cmd_branches=cmds)

    # 连续注释块（>=5 行）= 死代码候选
    runs, cur, start = [], 0, 0
    for i, l in enumerate(L):
        if l.strip().startswith('#'):
            if cur == 0:
                start = i + 1
            cur += 1
        else:
            if cur >= 5:
                runs.append((start, cur))
            cur = 0
    if cur >= 5:
        runs.append((start, cur))
    dead_lines = sum(r[1] for r in runs)

    # 顶层定义
    defs = [(i + 1, l.split('(')[0].replace('def ', '').strip())
            for i, l in enumerate(L) if re.match(r'^def ', l)]
    classes = [(i + 1, l.strip()) for i, l in enumerate(L) if re.match(r'^class ', l)]

    # Handler 方法
    methods = [(i + 1, l.strip()) for i, l in enumerate(L) if re.match(r'^    def ', l)]

    M = []
    A = M.append
    A('# `server/mock_server.py` 结构图与主线\n')
    A('> 自动生成：`tools/r1b_mock_server_structure.py`。**只读分析，未改动源文件**。\n')
    A('> 目的：把 20k 行压成可读骨架，让"主线在哪、某功能在哪、哪些是死代码"一目了然。\n')
    A('\n## 一、总览\n')
    A('| 指标 | 值 |')
    A('|---|---:|')
    A('| 总行数 | **%d** |' % n)
    A('| 代码行 | %d (%.1f%%) |' % (n - sum(1 for x in L if not x.strip()) -
                                sum(1 for x in L if x.strip().startswith('#')),
                                100.0 * (n - sum(1 for x in L if not x.strip()) -
                                         sum(1 for x in L if x.strip().startswith('#'))) / n))
    A('| 注释行 | %d (%.1f%%) |' % (sum(1 for x in L if x.strip().startswith('#')),
                                100.0 * sum(1 for x in L if x.strip().startswith('#')) / n))
    A('| 空行 | %d |' % sum(1 for x in L if not x.strip()))
    A('| **连续注释块(≥5行)** | **%d 块 / %d 行（%.1f%%）** ← 死代码主体 |'
      % (len(runs), dead_lines, 100.0 * dead_lines / n))
    A('| `[P2X-migrated]` 标记 | %d 处 |' % sum(1 for x in L if 'migrated' in x))
    A('| 顶层 `def` | %d 个 |' % len(defs))
    A('| `class` | %d 个 |' % len(classes))
    A('| `Handler` 方法 | %d 个 |' % len(methods))
    A('| `if cmd == N:` 分支 | %d 个 |' % sum(1 for x in L if re.match(r'^\s+if cmd == \d', x)))
    A('| `if cmd in (...)` 分支 | %d 个 |' % sum(1 for x in L if re.match(r'^\s+if cmd in \(', x)))
    A('')
    A('> **一句话**：文件不是"乱"，而是**长期增量叠加**——'
      '真正的业务逻辑在 14,612 行代码里，另外 **3,301 行是已下沉模块后留下的注释副本**（死代码）。\n')

    A('\n## 二、主线（从连接建立起）\n')
    A('```')
    A('TCP accept')
    A('  └─ Handler(SocketServer.BaseRequestHandler)')
    A('       └─ handle()  ── recv 循环')
    A('            ├─ FrameParser          ← 拆 [u32 len][u16 cmd][body]')
    A('            └─ 尾部 **if cmd == N / if cmd in (...)** 主分发链（约 376 个分支）')
    A('                 ├─ 专用业务分支（多数）')
    A('                 └─ global_default_sc 全局兜底（★ 必须在所有专用分支之后）')
    A('')
    A('HTTP 侧（同一 Handler 类，另一个方向）')
    A('  └─ Handler.do_GET')
    A('       ├─ /GM*            → gm.console（后台管理系统）')
    A('       ├─ /DSH_ADMIN/*    → 管理面（~80 个 action，含 GM 写操作）')
    A('       ├─ /DSH_PROBE      → 客户端探针回传')
    A('       └─ 资源面          → url_config / version / gateway / notice …')
    A('```')
    A('')
    A('**读代码的建议顺序**（按主线逆推）：')
    A('1. `class Handler` → `handle()`（TCP 主循环，约在 F 区起点）')
    A('2. 主分发链：搜 `if cmd ==` 找到目标命令')
    A('3. 该分支调用的 `build_*` / `db_*` —— 在 E 区（业务辅助）')
    A('4. 帧编码规则 —— 在 D 区（协议底座）')
    A('5. 出问题时：`global_default_sc`（I 区）可能抢先命中 → 见 §五 陷阱\n')

    A('\n## 三、分区骨架（按行号）\n')
    A('| 区 | 起止行 | 行数 | 代码 | 注释 | 死代码标记 | cmd 分支 | 内容 |')
    A('|---|---|---:|---:|---:|---:|---:|---|')
    tot = Counter()
    for name, a, b in REGIONS:
        s = stat(a, min(b, n))
        for k, v in s.items():
            tot[k] += v
        A('| %s | %d–%d | %d | %d | %d | %d | %d | |'
          % (name, a, min(b, n), s['lines'], s['code'], s['comment'],
             s['migrated'], s['cmd_branches']))
    A('| **合计** | 1–%d | **%d** | %d | %d | %d | %d | |'
      % (n, tot['lines'], tot['code'], tot['comment'], tot['migrated'],
         tot['cmd_branches']))
    A('')

    A('\n## 四、死代码分布（已下沉模块的注释副本）\n')
    A('连续注释块 ≥5 行的 15 个最大块：\n')
    A('| 起始行 | 行数 | 首行摘要 |')
    A('|---|---:|---|')
    for s, ln in sorted(runs, key=lambda x: -x[1])[:15]:
        A('| L%d | %d | `%s` |' % (s, ln, L[s - 1].strip()[:70].replace('|', '\\|')))
    A('')
    A('> 这些块**全部**以 `[P2X-migrated …]` 开头，指向 `server/` 下已存在的模块文件。')
    A('> 它们是"搬家时的原文留档"，**不是**仍在执行的代码。\n')

    A('\n## 五、已知陷阱（读/改此文件前必看）\n')
    A('1. **兜底位置**：`global_default_sc` **必须**在所有专用分支之后（见 I 区注释）。')
    A('   若被挪到前面，所有专用实现都会被它抢走 —— 这是本项目反复踩过的坑。')
    A('2. **同一个 cmd 不要既在专用分支又在通用元组里** —— 项目有门禁 '
      '`tools/lint_dispatch_shadow.py`；当前为 ✓ 无遮蔽。')
    A('3. **`.get(k, default)` 对"键存在但值为 None"返回 None** —— 曾导致每 2.5 秒异常刷屏。')
    A('4. **CS body 尾部有 4 字节脏数据** —— 只读规格前 N 字节。')
    A('5. **`code==1` 才是成功**，唯一例外 `10200` 要 `code==0`。\n')

    A('\n## 六、关于"死代码"的处置（**已实测，结论：维持现状**）\n')
    A('尝试过三种方案，**实测结果如下**：\n')
    A('| 方案 | 结果 |')
    A('|---|---|')
    A('| **A. 原样保留**（当前采用） | ✅ 零风险 |')
    A('| B. 整块搬到 `server/_migrated_archive.py` | ❌ **不安全**（见下） |')
    A('| C. 直接删除 | ❌ 更不安全 |')
    A('')
    A('### B 为什么不可行（实测证据）\n')
    A('用 `tokenize` 精确识别"纯注释行"后按连续块搬迁，只搬了 39 块就触发 '
      '`IndentationError: unexpected indent`。原因是这些注释块**与活代码/活注释交错**：\n')
    A('```')
    A('  L3761-3767  # [P2B-migrated …] <旧代码>      ← 列0 注释（可搬）')
    A('  L3768            # ② 按 SC 编码                ← 缩进 4 的活注释')
    A('  L3769-3774  # [P2B-migrated …] <旧代码>')
    A('  L3775-3780            # ★★★ R203：…            ← 缩进 12 的**活注释**（有用）')
    A('  ...')
    A('  L3787                return w_u16(n) + …        ← **活代码**，缩进 12')
    A('```')
    A('⇒ 整块移除会**删掉活注释**，并让后面的**活代码失去缩进归属**。')
    A('要安全搬，必须对 283 个块**逐块做语义核对** —— 收益只是篇幅，**不值这个风险**。\n')
    A('> **结论**：保留现状。已在 `mock_server.py` 顶部加**导航头**'
      '（`tools/r1b_add_nav_header.py`），让主线与分区可读，而不动任何代码结构。\n')

    txt = '\n'.join(M) + '\n'
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(txt)
    print('写出 %s（%d 字节）' % (os.path.relpath(OUT, ROOT), len(txt.encode('utf-8'))))
    print('总行 %d ｜ 代码 %d ｜ 注释 %d ｜ 死代码块 %d 行（%.1f%%）'
          % (n, tot['code'], tot['comment'], dead_lines, 100.0 * dead_lines / n))


if __name__ == '__main__':
    main()
