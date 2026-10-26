# -*- coding: utf-8 -*-
"""命令覆盖审计：客户端**请求了**但服务端**没回包**的命令。

为什么需要（2026-10-17）：
  `protocol/fields.json` 里定义了 SC 的消息，客户端**会在等应答**；服务端沉默 ⇒ 客户端
  超时/面板干等/判定掉线。这类"沉默"在日志里只表现为"有 `>> cmd=N`、没有 `<< N`"，
  很容易被忽略。本工具跨全部轮转日志做统计，并把结果分成：
    · 无 SC 定义（CS-only 上报型）        -> 沉默是**正确**行为
    · 明示不实现（_UNSUPPORTED_ACTION_CMDS）-> 应回失败码，不回也是问题
    · EMPTY_REPLIES / _GENERIC_DEFAULT_CMDS -> 应回空/默认帧
    · 其余（有 SC 定义、也不在名单里）      -> **★ 可疑：真沉默**
  另统计 `!! cmd=N 处理异常`（handler 抛异常被兜住）——这些同样会让客户端等不到包。

用法（仓库根目录）：
    python tools/audit_cmd_coverage.py                 # 全部 tcp*.log
    python tools/audit_cmd_coverage.py --min-req 3     # 只看请求≥3次的
"""
import argparse
import collections
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'server'))
LOGDIR = os.path.join(ROOT, 'server', 'logs')

RE_REQ = re.compile(r'>> cmd=(\d+)')
RE_REP = re.compile(r'<< (\d+)\b')
RE_ERR = re.compile(r'!! cmd=(\d+) 处理异常')


def whitelists():
    """从 mock_server 取现成名单 + 从 protocol 取 SC 定义。"""
    out = {'no_sc': set(), 'unsupported': set(), 'empty': set(), 'generic': set()}
    try:
        import mock_server as m
        out['unsupported'] = set(m._UNSUPPORTED_ACTION_CMDS)
        out['empty'] = set(m.EMPTY_REPLIES)
        out['generic'] = set(m._GENERIC_DEFAULT_CMDS)
        try:
            from protocol.fields import has_sc_definition
            for c in range(1, 40000):
                pass
        except Exception:
            pass
    except Exception as e:
        print('!! 载入 mock_server 失败（名单将为空）: %r' % (e,))
    return out


def has_sc(cmd):
    from protocol.fields import has_sc_definition
    try:
        return has_sc_definition(cmd)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-req', type=int, default=1)
    ap.add_argument('--files', default='tcp*.log')
    a = ap.parse_args()

    wl = whitelists()
    req = collections.Counter()
    rep = collections.Counter()
    err = collections.Counter()
    files = sorted(glob.glob(os.path.join(LOGDIR, a.files)))
    for p in files:
        for line in open(p, encoding='utf-8', errors='replace'):
            m = RE_REQ.search(line)
            if m:
                req[int(m.group(1))] += 1
                continue
            m = RE_REP.search(line)
            if m:
                rep[int(m.group(1))] += 1
                continue
            m = RE_ERR.search(line)
            if m:
                err[int(m.group(1))] += 1

    print('日志文件: %d 个 ｜ 请求命令: %d 个 ｜ 有回包: %d 个 ｜ 异常命令: %d 个'
          % (len(files), len(req), len(rep), len(err)))
    if err:
        print('\n== handler 抛过异常的命令（已兜住，但要修）==')
        for c, n in err.most_common():
            print('   %6d  x%d' % (c, n))

    silent = []
    for c, n in req.items():
        if rep[c] or n < a.min_req:
            continue
        if c in wl['unsupported'] or c in wl['empty'] or c in wl['generic']:
            kind = '名单内（应回空/失败帧）'
        else:
            sc = has_sc(c)
            kind = '无 SC 定义（CS-only ⇒ 沉默正确）' if sc is False else '★ 有 SC 定义却没回'
        silent.append((c, n, kind))

    star = [x for x in silent if x[2].startswith('★')]
    print('\n== 请求了但没回包: %d 个（其中 ★可疑 %d 个）==' % (len(silent), len(star)))
    for c, n, kind in sorted(star) + sorted(x for x in silent if not x[2].startswith('★')):
        print('   %6d  请求%-4d  %s' % (c, n, kind))

    print('\n结论:', 'PASS（无"有 SC 定义却不回包"的命令）' if not star else
          'FAIL（%d 个命令有 SC 定义却沉默，需逐个查 handler）' % len(star))
    if star:
        print('\n⚠ 注意：本工具读的是**历史日志**，日志写下的那一刻的代码可能与现在不同')
        print('  （2026-10-17 实测过一次误判：日志里 36 条"沉默"，用 tools/probe_silent_cmds.py')
        print('   现发现收一测 —— 17/17 全部有回包，那些 handler 是后来才补的）。')
        print('  ⇒ 每条结论都要用 tools/probe_silent_cmds.py <cmd...> 现场复核，别直接当 bug 修。')
    return 1 if star else 0


if __name__ == '__main__':
    sys.exit(main())
