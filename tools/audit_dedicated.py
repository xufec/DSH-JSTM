#!/usr/bin/env python3
"""审计"专用 handler 且真机未发送"的**查询型**命令（补 R43 暴露的盲区）。

## 为什么需要

现有三道在线/回放审计都有盲区：

| 审计 | 覆盖 | 盲区 |
|---|---|---|
| `audit_sc_live.py` | 默认应答集合（76+25） | **专用 handler** 不在其中 |
| `replay_captures.py` | 真机发过的 233 条 | **真机没发过**的命令完全测不到 |
| `verify_*.py` | 若干点状功能 | 需人工列举 |

⇒ **"专用 handler + 真机从未发送"** 的命令无人校验。
R43 的 `SC_10306` 正是此类：真机 341 抓包 0 次、走专用分支，
结果它的 `attr` 条目结构与 `SC_10304` 不同却被复用切分 ⇒ **多写 8 字节**，
静态与回放两道审计都放过了它。

## 判据（只挑**安全可调**的）

1. 命中 `mock_server.py` 里的**专用分发**：`if cmd == N:` / `if cmd in (…)`；
2. `CS_<cmd>` 存在且**字段为空** —— 纯查询，不需要构造参数；
3. `SC_<cmd>` 存在且**不含 `code`/`result`/`tips`** —— 不是"操作结果"，
   避免把"回成功/失败"这类有副作用的命令当成查询去调。

三条同时满足才纳入；调用后按 `SC` 规格**精确解析**。

用法：
    python tools/audit_dedicated.py            # 全量
    python tools/audit_dedicated.py --list      # 只列清单，不发包
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOCK = os.path.join(ROOT, 'server', 'mock_server.py')
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')

from audit_sc_conformance import parse_full  # noqa: E402


def dedicated_cmds(src):
    """解析 mock_server.py 的专用分发命令号（含多行元组）。"""
    out = set()
    for m in re.finditer(r'if cmd == (\d{4,5}):', src):
        out.add(int(m.group(1)))
    for m in re.finditer(r'if cmd in \(([^)]*)\):', src, re.S):
        for x in re.findall(r'\d{4,5}', m.group(1)):
            out.add(int(x))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--timeout', type=float, default=2.0)
    args = ap.parse_args()

    with open(FIELDS, encoding='utf-8') as f:
        fields = json.load(f)
    cs, sc = {}, {}
    for k, v in fields.items():
        c = v.get('cmd')
        if not c:
            continue
        if v.get('dir') == 'cs':
            cs.setdefault(str(c), v.get('fields') or [])
        elif v.get('dir') == 'sc':
            sc.setdefault(str(c), v.get('fields') or [])

    src = open(MOCK, encoding='utf-8').read()
    ded = dedicated_cmds(src)
    print('# mock_server.py 专用分发命令数: %d' % len(ded))

    pick = []
    for c in sorted(ded):
        key = str(c)
        if key not in cs or key not in sc:
            continue
        if cs[key]:                       # 需要参数 ⇒ 不纳入（避免误触发）
            continue
        if any((f.get('name') or '') in ('code', 'result', 'tips') for f in sc[key]):
            continue                      # 带结果码 ⇒ 可能是操作型
        pick.append(c)

    print('# 其中「CS 为空 且 SC 无结果码」的查询型: %d' % len(pick))
    print('  ' + ', '.join(map(str, pick)))
    if args.list:
        return

    import socket
    import struct
    from audit_sc_live import pack_frame, recv_exact, login

    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    login(s)
    s.settimeout(args.timeout)

    ok = bad = noresp = 0
    problems = []
    for c in pick:
        key = str(c)
        try:
            s.sendall(pack_frame(c, b''))
            got = None
            while True:
                hdr = recv_exact(s, 6)
                (ln, rcmd) = struct.unpack('>IH', hdr)
                payload = recv_exact(s, ln - 2)
                if rcmd == c:
                    got = payload
                    break
        except Exception:
            got = None
            try:
                s.close()
            except Exception:
                pass
            s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
            login(s)
            s.settimeout(args.timeout)
        if got is None:
            noresp += 1
            problems.append((c, 'NO-RESPONSE', '有 SC 规格但无应答'))
            continue
        off, errs, unver = parse_full(got, sc[key])
        # ★★ R84：**多版本尾部字段豁免**（四个门禁同一条规则，理由见 audit_emitted_fields.py
        #   里的 `MULTI_VERSION_TAIL` 注释）：本服对 10301/10302 刻意多发尾部字段以兼容 1.4.11
        #   （1.4.11 比 1.4.9 多 `diamond`+`rainbow_diamond`）。判据：
        #   **名单内 + 无解析错误 + 包比规格长**（多出来的只可能在尾部）。
        #   ⚠ 少发（包更短）**不豁免**；⚠ 命令号在循环里是**字符串**，必须 `int(c)`。
        tail_ok = (int(c) in (10301, 10302) and not errs and off < len(got))
        if (errs or (not unver and off != len(got))) and not tail_ok:
            bad += 1
            problems.append((c, 'MISMATCH',
                             '; '.join(errs[:2]) or '消耗 %d != %d' % (off, len(got))))
        else:
            ok += 1
    s.close()

    print()
    print('=== 专用 handler 查询审计（%d 条）===' % len(pick))
    print('  符合规格 %d / 不符 %d / 无应答 %d' % (ok, bad, noresp))
    for c, kind, why in problems:
        print('  ★ %-9s %-6d %s' % (kind, c, why))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
