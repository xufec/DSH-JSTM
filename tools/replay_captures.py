#!/usr/bin/env python3
"""真机流量回放审计：把 341 个抓包里的**每一条真实 CS 帧**回放给服务端，
逐条校验应答是否与协议规格一致 —— 直接度量"协议定义 → 已实现应答"的收敛度。

## 与其它审计的分工

| 工具 | 覆盖 | 判据 |
|---|---|---|
| `audit_specs_vs_fields.py` | 全部消息定义 | CS 规格挖掘对不对 |
| `audit_sc_conformance.py` | 全部 SC 规格 | 默认响应构建对不对（静态） |
| `audit_sc_live.py` | 47 条 generic | 默认响应上线后对不对（动态） |
| **本工具** | **233 条真机实际发过的命令** | **真实流量下应答对不对（动态、全量）** |

## 判据

- 有 SC 规格 ⇒ 应答必须能按规格**精确解析**（消耗字节数 == 实际长度）；
- 无 SC 规格（CS-only）⇒ **不应答**才算对；
- 超时无应答但**有** SC 规格 ⇒ 记为 **GAP**（客户端会表现为面板空/卡住）。

## ⚠ 副作用

回放会真实触发动作类命令（购买/领取/移动…）。运行前后请自行备份
`server/state/roles.db`；本工具只做只读统计，不负责回滚。

用法：
    python tools/replay_captures.py [--timeout 1.0] [--json out.json]
"""
import argparse
import collections
import glob
import json
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')
CAPS = os.path.join(ROOT, 'server', 'logs', 'tcp_*.bin')

from audit_sc_conformance import parse_full  # noqa: E402

LOGIN_CMDS = {10001, 1110, 10102}


def collect(per_cmd=1):
    """-> ({cmd: [(body, count), ...] 按频次降序，最多 per_cmd 个}, 文件数)

    只回放每命令的**众数 body** 会漏掉参数分支（错误路径、不同 bag_code…）。
    round37 发现的 10554/12832 等编码 bug 正是靠"不同参数走不同分支"才暴露，
    因此这里支持每命令取样多个高频变体。
    """
    per = collections.defaultdict(collections.Counter)
    files = sorted(glob.glob(CAPS))
    for p in files:
        b = open(p, 'rb').read()
        off = 0
        while off + 6 <= len(b):
            ln = struct.unpack_from('>I', b, off)[0]
            if ln < 2 or off + 4 + ln > len(b):
                break
            c = struct.unpack_from('>H', b, off + 4)[0]
            per[c][b[off + 6:off + 4 + ln]] += 1
            off += 4 + ln
    out = {c: cnt.most_common(per_cmd) for c, cnt in per.items()}
    return out, len(files)


def pack_frame(cmd, body=b''):
    return struct.pack('>I', 2 + len(body)) + struct.pack('>H', cmd) + body


def recv_exact(s, n):
    buf = b''
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise EOFError('closed')
        buf += chunk
    return buf


def login(s):
    s.sendall(pack_frame(10001, struct.pack('>H', 1) + b'c' + b'\x00' * 4))
    s.sendall(pack_frame(1110, struct.pack('>III', 1, 1, 1)))
    recv_exact(s, 6)
    s.sendall(pack_frame(10102, struct.pack('>I', 1001)))
    s.settimeout(1.0)
    try:
        while True:
            hdr = recv_exact(s, 6)
            (ln, rcmd) = struct.unpack('>IH', hdr)
            recv_exact(s, ln - 2)
            if rcmd == 10200:
                break
    except (EOFError, socket.timeout):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    ap.add_argument('--timeout', type=float, default=1.0)
    ap.add_argument('--json')
    ap.add_argument('--per-cmd', type=int, default=1,
                    help='每命令回放的高频变体数（默认 1=只回放众数 body）')
    args = ap.parse_args()

    with open(FIELDS, encoding='utf-8') as f:
        fields = json.load(f)
    sc = {}
    cs = set()
    for k, v in fields.items():
        c = v.get('cmd')
        if not c:
            continue
        if v.get('dir') == 'sc':
            sc.setdefault(str(c), v.get('fields') or [])
        elif v.get('dir') == 'cs':
            cs.add(str(c))

    samples, nfiles = collect(args.per_cmd)
    todo = sorted(c for c in samples if c not in LOGIN_CMDS)
    nvariants = sum(len(v) for c, v in samples.items() if c not in LOGIN_CMDS)
    print('# 抓包文件 %d 个，去重命令 %d 条（跳过登录序列 %s）'
          % (nfiles, len(samples), sorted(LOGIN_CMDS)))
    print('# 本轮计划回放变体 %d 个（每命令最多 %d 个高频变体）'
          % (nvariants, args.per_cmd))

    s = socket.create_connection((args.host, args.port), timeout=10)
    login(s)
    s.settimeout(args.timeout)

    ok = gap = mismatch = cs_only_ok = cs_only_bad = unver = skipped = 0
    rows = []
    noresp_cmds = set()
    for cmd in todo:
        key = str(cmd)
        has_sc = key in sc
        if cmd in noresp_cmds:
            skipped += len(samples[cmd])
            continue
        for body, nsample in samples[cmd]:
            try:
                s.sendall(pack_frame(cmd, body))
                got = None
                while True:
                    hdr = recv_exact(s, 6)
                    (ln, rcmd) = struct.unpack('>IH', hdr)
                    payload = recv_exact(s, ln - 2)
                    if rcmd == cmd:
                        got = payload
                        break
            except (socket.timeout, EOFError):
                got = None
                try:
                    s.close()
                except Exception:
                    pass
                s = socket.create_connection((args.host, args.port), timeout=10)
                login(s)
                s.settimeout(args.timeout)

            if got is None:
                if has_sc:
                    gap += 1
                    rows.append((cmd, 'GAP', nsample, '有 SC 规格但无应答'))
                    noresp_cmds.add(cmd)      # 该命令无应答 ⇒ 其余变体不必再试
                else:
                    cs_only_ok += 1
                    rows.append((cmd, 'CS-ONLY', nsample, '无 SC 定义，不应答=正确'))
                break
            if not has_sc:
                cs_only_bad += 1
                rows.append((cmd, 'EXTRA', nsample, '无 SC 定义却回了 %d 字节' % len(got)))
                continue
            off, errs, unverified = parse_full(got, sc[key])
            if errs or (not unverified and off != len(got)):
                mismatch += 1
                rows.append((cmd, 'MISMATCH', nsample,
                             '; '.join(errs[:2]) or '消耗 %d != %d' % (off, len(got))))
            elif unverified:
                unver += 1
                rows.append((cmd, 'UNVERIFIED', nsample, '含未解子表，长度不可校验'))
            else:
                ok += 1

    s.close()
    print()
    print('=== 真机流量回放审计（%d 条命令 / %d 个变体）===' % (len(todo), nvariants))
    print('  应答符合规格 : %d' % ok)
    print('  CS-only 正确 : %d' % cs_only_ok)
    print('  含未解子表（不可校验）: %d' % unver)
    print('  ★ GAP（有 SC 却无应答）: %d' % gap)
    print('  ★ 规格不符   : %d' % mismatch)
    print('  ★ 多余应答   : %d' % cs_only_bad)
    print('  跳过（同命令已确认无应答）: %d' % skipped)
    print()
    for cmd, kind, ns, why in rows:
        if kind in ('OK',):
            continue
        print('  %-9s %-6d (样本%4d) %s' % (kind, cmd, ns, why))

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({'n_cmds': len(todo), 'ok': ok, 'gap': gap, 'mismatch': mismatch,
                       'cs_only_ok': cs_only_ok, 'cs_only_bad': cs_only_bad,
                       'rows': [{'cmd': c, 'kind': k, 'samples': n, 'why': w} for c, k, n, w in rows]},
                      f, ensure_ascii=False, indent=1)
        print('\n已写出 %s' % args.json)

    sys.exit(1 if (mismatch or cs_only_bad) else 0)


if __name__ == '__main__':
    main()
