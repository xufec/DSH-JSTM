#!/usr/bin/env python3
"""Lint：检测**分发顺序遮蔽**（同一命令既走专用分支、又在通用集合里）。

## 为什么需要

`mock_server.py` 的分发是"靠前的分支先 return"。
`_GENERIC_DEFAULT_CMDS` / `_UNSUPPORTED_ACTION_CMDS` 两个集合的分支
**位置靠前**，会给出一份"规格正确但全零/未开放"的应答并 return
⇒ 若某命令**同时**又写了专用实现（分支在文件里更靠后），
**专用实现永远不会执行** —— 也就是**死代码**。

本项目已因此踩坑 **四次**：

| 轮次 | 命令 | 后果 |
|---|---|---|
| round40 | `12901/12902/12911/12912/12931` | 5 个排行榜全返回全零 |
| round42 前后 | `13401/13403` | 商城真实商品列表被空表遮蔽 |
| R46 | `13042` | 爬塔面板永远没进度（真机发 183 次） |
| R47 | `11300/11308` | 竞技场面板全零（真机发 259/23 次） |

每次都靠**人工记得"移出集合"**，而每次都可能漏。
本 lint 把这条纪律变成**机械检查**。

用法：
    python tools/lint_dispatch_shadow.py            # 0=通过，1=有遮蔽
    python tools/lint_dispatch_shadow.py --quiet
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOCK = os.path.join(ROOT, 'server', 'mock_server.py')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def _strip_comments(text):
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith('#'):
            continue
        out.append(ln.split('#')[0])
    return '\n'.join(out)


def _set_members(src, name):
    """取出 `name = frozenset([...])` 里的整数（先剥注释，避免注释里的数字被误收）。"""
    m = re.search(r'^%s\s*=\s*frozenset\(\[(.*?)\]\)' % re.escape(name),
                  src, re.S | re.M)
    if not m:
        return set()
    body = _strip_comments(m.group(1))
    return set(int(x) for x in re.findall(r'\d{4,5}', body))


def dedicated_cmds(src):
    """专用分发命令号（含多行元组 + ★ **变量集合**）。

    ★ R172：`if cmd in _VAR:`（数据驱动写法，R171 引入）也要认 ——
      本函数原先**只认字面量**，导致**专用分支计数少算 31 条**
      （与 `scan_unhandled_by_dir` / `audit_dedicated_really` 的盲区同一个）。
    """
    out = set()
    for m in re.finditer(r'if cmd == (\d{4,5}):', src):
        out.add(int(m.group(1)))
    for m in re.finditer(r'if cmd in \(([^)]*)\):', src, re.S):
        for x in re.findall(r'\d{4,5}', m.group(1)):
            out.add(int(x))
    # ★ 变量集合：`if cmd in _VAR:` ⇒ 去 `_VAR = { N: … }` 的键里找
    for m in re.finditer(r'if cmd in (_[A-Za-z0-9_]+):', src):
        _var = m.group(1)
        _m2 = re.search(re.escape(_var) + r'\s*=\s*\{(.*?)\n\}', src, re.S)
        if _m2:
            for x in re.findall(r'\b(\d{4,6})\s*:', _m2.group(1)):
                out.add(int(x))
    return out


def duplicate_dedicated(src):
    """★ R83：**同一命令出现多个专用分支** ⇒ 前面的会遮蔽后面的（后者永不执行）。

    为什么加这条：`15403` 曾有两份 `if cmd == 15403:`（旧版无条件回成功、新版校验+
    累加击杀），旧版先命中 ⇒ 新版成了死代码，表现为"未知怪也回成功、击杀计数不动"。
    本门禁原先只查"专用 vs 通用集合"，**对"专用 vs 专用"是盲区**。

    ⚠ 必须先剥注释 —— 这个文件里大量注释**引用**了 `if cmd == N:` 片段，
      直接扫原文会产生几十条误报（第一版就是这么错的）。

    返回 {cmd: 出现次数}（只统计 >1 的）。
    """
    src = _strip_comments(src)
    # ⚠⚠ 判据用 **(缩进层级, 命令号)** 计数：
    #   · **同层**出现两次 ⇒ 真遮蔽（同一个 `if cmd` 分发链里两条入口，后者是死代码）
    #   · **不同层** ⇒ 嵌套子条件（例：`if cmd in (20001..20017)` 内层再
    #     `if cmd in (20004,20016)`）—— 那是**合法控制流**，必须排除。
    #   v1（只扫原文）误报 38 条；v2（剥注释后把两种形式混在一起、不看缩进）
    #   仍误报 20004/20016。v3 只查 `==` 形式，却**漏掉了真正的跨形式遮蔽**：
    #   `11216` 曾被前置的 `if cmd in (11206, 11216):` 遮住后面写库的
    #   `if cmd == 11216:`（R86 的"神物兑换进不了背包"就是这个）。
    #   ⇒ 现在按缩进分层统计，两种误报同时消除。
    cnt = {}
    for m in re.finditer(r'^([ \t]*)if cmd == (\d{4,5}):', src, re.M):
        k = (len(m.group(1)), int(m.group(2)))
        cnt[k] = cnt.get(k, 0) + 1
    for m in re.finditer(r'^([ \t]*)if cmd in \(([^)]*)\):', src, re.M):
        ind = len(m.group(1))
        for x in re.findall(r'\d{4,5}', m.group(2)):
            k = (ind, int(x))
            cnt[k] = cnt.get(k, 0) + 1
    out = {}
    for (ind, cmd), v in cnt.items():
        if v > 1:
            out[cmd] = out.get(cmd, 0) + v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    src = open(MOCK, encoding='utf-8').read()
    gen = _set_members(src, '_GENERIC_DEFAULT_CMDS')
    uns = _set_members(src, '_UNSUPPORTED_ACTION_CMDS')
    ded = dedicated_cmds(src)

    if not args.quiet:
        print('专用分支 %d 条 ｜ 默认集合 %d 条 ｜ 未开放集合 %d 条'
              % (len(ded), len(gen), len(uns)))

    shadow_gen = sorted(ded & gen)
    shadow_uns = sorted(ded & uns)

    bad = False
    if shadow_gen:
        bad = True
        print('\n★ 被 _GENERIC_DEFAULT_CMDS 遮蔽的专用实现（%d 条）：' % len(shadow_gen))
        print('  ' + ', '.join(map(str, shadow_gen)))
        print('  ⇒ 这些命令的专用分支**永远不会执行**，请从集合中移出。')
    if shadow_uns:
        bad = True
        print('\n★ 被 _UNSUPPORTED_ACTION_CMDS 遮蔽的专用实现（%d 条）：' % len(shadow_uns))
        print('  ' + ', '.join(map(str, shadow_uns)))
        print('  ⇒ 同上，请从集合中移出。')

    # ★ R83：专用 vs 专用 的遮蔽（同一命令多个分支 ⇒ 后者是死代码）
    dups = duplicate_dedicated(src)
    if dups:
        bad = True
        print('\n★ 同一命令存在多个专用分支（%d 条）—— **后者永远不会执行**：' % len(dups))
        for k in sorted(dups):
            print('  %d 出现 %d 次' % (k, dups[k]))
        print('  ⇒ 请合并/删除旧分支（历史上 15403 就是这样被遮蔽的）。')

    if not bad:
        print('\n✓ 无分发遮蔽：所有专用实现都能真正执行。')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
