# -*- coding: utf-8 -*-
"""core.dispatch —— 命令分发表兼容层（Phase 2 step 0）。

设计依据：analysis/phase2_design.md §3.3（兼容层设计）、§七 步骤 1。

用途：在不改动旧 8,854 行 if 链的前提下，给后续批次一个"新 handler 优先、
旧 if 链兜底"的切换开关。step 0 阶段表为空 ⇒ 所有命令 100% 走旧路径，
行为与拆分前字节级一致。

语义（handle 返回值）：
  - cmd 未注册            -> 返回 None（调用方继续走旧 if 链）
  - cmd 已注册且 handler 成功 -> 返回 True（调用方 return，处理完毕）
  - cmd 已注册但 handler 抛异常 -> 记录日志后返回 None（调用方落到旧 if 链兜底，
                                  保证永远有应答——见设计 §3.3 硬规则）

调用点（mock_server.py _reply 最开头）：
    handled = dispatch.handle(cmd, self, body)
    if handled is not None:
        return
"""

import os
import re
import sys

# cmd(int) -> handler(h, cmd, body) -> None
DISPATCH_TABLE = {}

# 可被 mock_server 注入的日志函数 log(name, text)；默认写 stderr。
_log_fn = None


def set_logger(fn):
    """由 mock_server.py 注入它自己的 log(name, text)，便于统一落盘。"""
    global _log_fn
    _log_fn = fn


def _log(text):
    try:
        if _log_fn is not None:
            _log_fn('dispatch.log', text)
            return
    except Exception:
        pass
    sys.stderr.write('[dispatch] %s\n' % text)


def register(*cmds):
    """装饰器：把 handler 注册到 DISPATCH_TABLE。

    用法（后续新模块内）：
        from core.dispatch import register
        @register(1110, 10102)
        def handle_login(h, cmd, body): ...
    """
    def deco(fn):
        for c in cmds:
            DISPATCH_TABLE[c] = fn
        return fn
    return deco


def register_one(cmd, fn):
    """非装饰器形式注册（便于动态注册）。"""
    DISPATCH_TABLE[cmd] = fn


def is_registered(cmd):
    return cmd in DISPATCH_TABLE


def registered_cmds():
    return sorted(DISPATCH_TABLE.keys())


def handle(cmd, h, body):
    """查表分发。见模块 docstring 的返回值语义。

    返回：
      True  -> 已由新 handler 处理完毕，调用方应 return。
      None  -> 未注册，或新 handler 失败需兜底；调用方继续走旧 if 链。
    """
    fn = DISPATCH_TABLE.get(cmd)
    if fn is None:
        return None
    try:
        fn(h, cmd, body)
        return True
    except Exception as e:
        # 硬规则：已注册但 handler 抛异常 ⇒ 不 return，落旧 if 链兜底。
        _log('!! DISPATCH handler cmd=%d failed: %r -- fallback to old if-chain'
             % (cmd, e))
        return None


# ── shadow_lint：if 链遮蔽检测 ──────────────────────────────────────────
# 设计 §九 风险 2：历史上出现过"前面 if cmd==N 遮蔽后面真正写库的 N"。
# 本函数扫描 mock_server.py 源码，对每个**已注册**命令检查旧 if 链里
# 是否出现多次匹配（>1 处即潜在遮蔽）。step 0 表为空 ⇒ 无命令可查。

_REPLY_RE = re.compile(r'def _reply\(self, cmd, body\)')
_IFCMD_RE = re.compile(r'if\s+cmd\s*==\s*(\d+)|elif\s+cmd\s*==\s*(\d+)|'
                       r'if\s+cmd\s+in\s*\(([^)]*)\)')


def _mock_server_path():
    # core/dispatch.py -> server/core/dispatch.py -> ../mock_server.py
    return os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'mock_server.py'))


def shadow_lint():
    """对已注册命令检查旧 if 链遮蔽。

    返回 dict: {
        'checked': [已注册命令列表],
        'shadow':  [(cmd, 旧链匹配次数, 行号列表)],   # 次数>1 即潜在遮蔽
        'unregistered': 'n/a'
    }
    step 0（表为空）=> checked=[], shadow=[]。
    """
    cmds = registered_cmds()
    report = {'checked': cmds, 'shadow': []}
    if not cmds:
        report['note'] = 'DISPATCH_TABLE 为空，无命令可 lint（step 0 基线）'
        return report

    path = _mock_server_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        report['error'] = '读取 mock_server.py 失败: %r' % e
        return report

    # 定位 _reply 函数体行范围（粗：从 def _reply 到下一个顶层 def/class）。
    start = None
    for i, ln in enumerate(lines):
        if _REPLY_RE.search(ln):
            start = i
            break
    if start is None:
        report['error'] = '未找到 _reply 定义'
        return report

    # 统计每个已注册 cmd 在 _reply 区域内的匹配行号。
    cmd_hits = {c: [] for c in cmds}
    for i in range(start, len(lines)):
        ln = lines[i]
        # 遇到下一个顶层（列首）class/def 则停止（_reply 结束）
        if i > start and re.match(r'^(class |def )', ln):
            break
        m = _IFCMD_RE.search(ln)
        if not m:
            continue
        if m.group(1):      # if cmd == N
            c = int(m.group(1))
            if c in cmd_hits:
                cmd_hits[c].append(i + 1)
        elif m.group(2):    # elif cmd == N
            c = int(m.group(2))
            if c in cmd_hits:
                cmd_hits[c].append(i + 1)
        elif m.group(3):    # if cmd in (a, b, c)
            for tok in m.group(3).split(','):
                tok = tok.strip()
                if tok.isdigit() and int(tok) in cmd_hits:
                    cmd_hits[int(tok)].append(i + 1)

    for c in cmds:
        hits = cmd_hits[c]
        if len(hits) > 1:
            report['shadow'].append((c, len(hits), hits))
    return report


if __name__ == '__main__':
    rpt = shadow_lint()
    print('DISPATCH_TABLE size =', len(DISPATCH_TABLE))
    print('registered cmds     =', rpt['checked'])
    print('shadow report       =', rpt['shadow'])
    if rpt.get('note'):
        print('note:', rpt['note'])
