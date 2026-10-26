#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 `server/mock_server.py` 加**导航头**（纯注释，零功能风险）。

## 为什么只做这一步
实测尝试过「把 3,301 行已下沉模块的注释副本搬到归档文件」，但该文件里
**列0 的 migrated 注释与缩进 12 的活注释/活代码是交错的** —— 整块移除会让
后面的活代码失去缩进归属（实测直接触发 IndentationError）。
要安全地搬，必须逐块做语义核对（283 块），**收益（纯篇幅）不值这个风险**。

⇒ 本脚本只做**零风险**的部分：在文件顶部插入一个导航块（全为注释），
   让"主线在哪、分区在哪、改之前要注意什么"一目了然。
   结构全图另见 `docs/mock_server_结构图.md`。

幂等：已含 `MOCK_SERVER 导航` 则直接退出。
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'mock_server.py')
MARK = 'MOCK_SERVER 导航'


def main():
    raw = open(SRC, encoding='utf-8', newline='').read()
    if MARK in raw[:6000]:
        print('已存在导航头，跳过（幂等）')
        return 0
    lines = raw.split('\n')
    n = len(lines)

    TOC = []
    A = TOC.append
    A('# ' + '=' * 76)
    A('# ' + MARK + '（tools/r1b_add_nav_header.py 生成，人工可改）')
    A('# ' + '=' * 76)
    A('#')
    A('# 【这是什么】《绝世唐门》私服的游戏服务端。单进程 Python，**纯标准库零依赖**。')
    A('#   TCP 9000  = 游戏协议 [u32 BE len][u16 BE cmd][body]')
    A('#   HTTP 8080 = 资源面 + /DSH_ADMIN 管理面 + /GM 后台管理页面')
    A('#')
    A('# 【主线怎么读】')
    A('#   ① class Handler → handle()      TCP 主循环：收帧 → FrameParser → 分发')
    A('#   ② 主分发链      if cmd == N / if cmd in (...)    约 %d 个分支' % (
        sum(1 for l in lines if re.match(r'^\s+if cmd == \d', l)) +
        sum(1 for l in lines if re.match(r'^\s+if cmd in \(', l))))
    A('#   ③ 分支用到的东西 build_*() 组帧 ｜ db_*() 存取 ｜ mission_*/scene_*/battle_* 业务')
    A('#   ④ 兜底          global_default_sc  ★ 必须在所有专用分支**之后**（否则抢走全部）')
    A('#   ⑤ HTTP 侧       Handler.do_GET：/GM→gm.console ｜ /DSH_ADMIN/*→管理面 ｜ 其余→资源')
    A('#')
    A('# 【分区骨架（行号会漂移，以 banner 搜索为准）】')
    for name, a, b in (
            ('A 文件头 / 导入 / 全局变量', 1, 120),
            ('B 场景与 AOI 基础件（_scene_* / push_to_rid）', 121, 600),
            ('C HTTP Handler：管理面 + 资源面', 601, 2600),
            ('D 协议底座：编码器 / 字段 / 默认响应', 2601, 7000),
            ('E 业务辅助：db_* / build_* / mission_* / scene_*', 7001, 9800),
            ('F TCP 主处理：分发主链（最大的区）', 9801, 17200),
            ('G 战斗 / 挂机 / 场景内链（200xx / 154xx）', 17201, 18300),
            ('H 登录 / 活动 / 邮件 / 伙伴 / 场景重推', 18301, 20000),
            ('I 全局兜底 global_default_sc + main()', 20001, n)):
        A('#      %-50s L%d–L%d' % (name, a, b))
    A('#')
    A('# 【改之前必看】')
    A('#   · 新增专用分支后，确认它**不在** _GENERIC_DEFAULT_CMDS 或任何 cmd in (...) 元组里，')
    A('#     否则会被全局兜底抢先命中。门禁：python tools/lint_dispatch_shadow.py')
    A('#   · .get(k, default) 对「键存在但值为 None」返回 None —— 曾导致定时器异常刷屏。')
    A('#   · CS body 尾部有 4 字节缓冲区脏数据：**只读规格前 N 字节**。')
    A('#   · code == 1 才是成功；**唯一例外 10200 要 code == 0**。')
    A('#   · 服务端下发的 ID 必须校验存在性（曾因发不存在的 skill bid 1001 让客户端崩）。')
    A('#')
    # 真实统计（**不写死**：初版这里写死 0，是错的）
    _code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
    _com_lines = sum(1 for l in lines if l.strip().startswith('#'))
    _runs, _cur = [], 0
    for _l in lines:
        if _l.strip().startswith('#'):
            _cur += 1
        else:
            if _cur >= 5:
                _runs.append(_cur)
            _cur = 0
    if _cur >= 5:
        _runs.append(_cur)
    _dead = sum(_runs)
    A('# 【篇幅实况（供后续整理参考）】')
    A('#   本文件 %d 行：代码 %d ｜ 注释 %d ｜ 空行 %d'
      % (n, _code_lines, _com_lines, n - _code_lines - _com_lines))
    A('#   **连续注释块 ≥5 行者 %d 行（%d 块）** —— 主体是「已下沉到 server/<pkg>/'
      % (_dead, len(_runs)))
    A('#   后仍以注释留档」的副本（含 [P2X-migrated] 标记）。')
    A('#   实测：这些块与**活代码/活注释交错**，整块移除会破坏缩进归属 ⇒ 维持现状。')
    A('#   结构全图：docs/mock_server_结构图.md')
    A('# ' + '=' * 76)
    A('')

    # 插到第一条 import 之前（通常在文件头部注释之后）
    idx = None
    for i, l in enumerate(lines[:120]):
        if re.match(r'^(import|from)\s', l):
            idx = i
            break
    if idx is None:
        print('!! 找不到 import 行，放弃')
        return 1
    new_lines = lines[:idx] + TOC + lines[idx:]
    out = '\n'.join(new_lines)
    open(SRC, 'w', encoding='utf-8', newline='').write(out)
    print('已插入导航头：%d 行 → %d 行（+%d，纯注释）'
          % (n, len(new_lines), len(new_lines) - n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
