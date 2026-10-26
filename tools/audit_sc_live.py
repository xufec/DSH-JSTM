#!/usr/bin/env python3
"""SC 在线一致性复核：向**运行中的服务端**逐个发 _GENERIC_DEFAULT_CMDS，
把真实回包按规格严格解析，确认线上字节与"成功但空"的默认响应完全一致。

与 `audit_sc_conformance.py` 的关系：
    前者是**静态**审计（直接调 `_build_default_sc` 并解析）；
    本工具是**动态**复核（走 TCP，验证真正上线的那条路径）。

用法：python tools/audit_sc_live.py [--host 127.0.0.1] [--port 9000] [--timeout 2]
"""
import argparse
import importlib.util
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
MOCK = os.path.join(ROOT, 'server', 'mock_server.py')

from audit_sc_conformance import parse_strict  # noqa: E402


def load_mock():
    spec = importlib.util.spec_from_file_location('mock_server_live', MOCK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['mock_server_live'] = mod
    spec.loader.exec_module(mod)
    return mod


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
    """登录 —— ★★ R85：**必须按真机 1.4.9 的形态发 args**。

    服务端按 `CS_1110` 的 args 判版本族（`ver_family_of`）：
        n = len(args); if n <= 2: return '1.3.0'; if body<210: '1.4.11'; else '1.4.9'
    真机 1.4.9 客户端发 **10 个键**；而这里原先发的是 `struct.pack('>III',1,1,1)`
    —— 根本不是 args 表 ⇒ 服务端解析出 `args={}` ⇒ **判成 1.3.0**
    ⇒ 服务端按 1.3.0 产出（例：`build_10303` 跳过 4 字节尾部）
    ⇒ 本门禁再用 **1.4.9 的 spec** 解析 ⇒ 报 `10303 vip_exp: 越界`。
    **那是"验证器与真机不同形态"，不是服务端 bug** ⇒ 修这里。
    """
    args = struct.pack('>H', 10)
    for k, v in (('account', 'dsh_local'), ('channelId', '1'),
                 ('device_id', 'dsh-probe'), ('enter_srv_id', '1'),
                 ('gettui_cid', ''), ('idfa', ''), ('platform', 'ewan'),
                 ('sign', ''), ('timestamp', '0'), ('token', '')):
        kb = k.encode()
        vb = v.encode()
        args += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    s.sendall(pack_frame(10001, struct.pack('>H', 1) + b'c' + b'\x00' * 4))
    s.sendall(pack_frame(1110, args))
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


def get_sc(hid, cmd):
    for k, v in hid.items():
        if v.get('dir') == 'sc' and str(v.get('cmd')) == str(cmd):
            return v.get('fields') or []
    return None


def has_cs(hid, cmd):
    return any(v.get('dir') == 'cs' and str(v.get('cmd')) == str(cmd) for v in hid.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    ap.add_argument('--timeout', type=float, default=2.0)
    ap.add_argument('--unsupported', action='store_true',
                    help='同时复核 _UNSUPPORTED_ACTION_CMDS（code=0 未开放应答）')
    args = ap.parse_args()

    with open(FIELDS, encoding='utf-8') as f:
        fields = json.load(f)
    mock = load_mock()
    cmds = set(mock._GENERIC_DEFAULT_CMDS)
    if args.unsupported:
        cmds |= set(getattr(mock, '_UNSUPPORTED_ACTION_CMDS', set()))
    cmds = sorted(cmds)

    s = socket.create_connection((args.host, args.port), timeout=10)
    login(s)
    s.settimeout(args.timeout)

    ok = bad = noresp = 0
    cs_only = []
    cs_count = 0
    problems = []
    for cmd in cmds:
        fs = get_sc(fields, cmd)
        if fs is None:
            # 无 SC 定义：若是 CS-only（有 CS 无 SC）则客户端不期待回包，
            # 服务端"不应答"才是正确行为 —— 不算问题。
            if has_cs(fields, cmd):
                cs_only.append(cmd)
                cs_count += 1
            else:
                noresp += 1
                problems.append((cmd, None, '既无 CS 也无 SC 定义'))
            continue
        try:
            s.sendall(pack_frame(cmd, b''))
            got = None
            while True:
                hdr = recv_exact(s, 6)
                (ln, rcmd) = struct.unpack('>IH', hdr)
                payload = recv_exact(s, ln - 2)
                if rcmd == cmd:
                    got = payload
                    break
        except (socket.timeout, EOFError) as e:
            noresp += 1
            problems.append((cmd, None, '无应答/超时 (%s)' % type(e).__name__))
            # 连接可能残留数据，重建
            try:
                s.close()
            except Exception:
                pass
            s = socket.create_connection((args.host, args.port), timeout=10)
            login(s)
            s.settimeout(args.timeout)
            continue

        off, errs = parse_strict(got, fs)
        # ★★ R84：**多版本尾部字段豁免**（与 audit_emitted_fields 同一理由）。
        #   本服对 10301/10302 刻意多发尾部字段以兼容 1.4.11
        #   （1.4.11 比 1.4.9 多 `diamond`+`rainbow_diamond`，见 tools/diff_role_specs.py）。
        #   判据：**名单内 + 无解析错误 + 包比规格长**（多出来的只可能在尾部）。
        #   ⚠ 少发（包更短）**不豁免** —— 那会让 1.4.11 解析越界、整条消息被丢弃。
        #   ⚠ `cmd` 在这里是**字符串**（与 audit_emitted_fields 里同一个坑）⇒ 必须 `int(cmd)`，
        #     否则 `cmd in (10301, 10302)` 恒为 False，豁免静默失效。
        tail_ok = (int(cmd) in (10301, 10302) and not errs and off < len(got))
        if (errs or off != len(got)) and not tail_ok:
            bad += 1
            problems.append((cmd, len(got), '; '.join(errs[:2]) or '消耗 %d != %d' % (off, len(got))))
        else:
            ok += 1

    s.close()
    print('=== SC 在线一致性复核（_GENERIC_DEFAULT_CMDS）===')
    print('  命令数 %d：一致 %d / 不一致 %d / 无应答(异常) %d / CS-only(不应答) %d'
          % (len(cmds), ok, bad, noresp, cs_count))
    if cs_only:
        print('  CS-only（协议无 SC，正确不回应）: %s' % cs_only)
    for cmd, ln, pb in problems:
        print('  · %-6d len=%-5s %s' % (cmd, ln if ln is not None else '-', pb))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
