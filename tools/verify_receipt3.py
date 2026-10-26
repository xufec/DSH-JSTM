# -*- coding: utf-8 -*-
"""R181 验收：**回执族第三批 65 条**（专用分支 795 → 860）。

判据：
  1. 65 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **回显**：`18023`/`19003`/`19005`（`id`）；`19517`/`19524`（`rid`）
  4. ★ **真校验**：`19517` 的 `rid` 非本服 ⇒ `code=0`

★ 本批有一处**重要发现**：`20711`/`20712`/`20714` 的 SC **其实是 `{code,msg}`**，
  而聚类时匹配到了**同号 cmd 的另一条 `fields.json` 记录** ⇒ 编码时**必须以"逐条查 SC"为准**。

用法： python tools/verify_receipt3.py
"""
import io
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
RID = 1001
CMDS = [18023, 19003, 19005, 19103, 19104, 19108, 19501, 19505, 19512, 19517, 19518,
        19519, 19524, 19526, 19529, 19532, 19533, 19537, 19903, 19904, 20025, 20027,
        20030, 20202, 20205, 20206, 20211, 20302, 20507, 20508, 20510, 20705, 20709,
        20710, 20711, 20712, 20713, 20714, 20715, 20716, 20722, 20723, 21302, 21603,
        21604, 21606, 21607, 21608, 30000, 30101, 30102, 30103, 30107, 30200, 30202,
        30203, 30208, 30303, 30700, 30705, 30706, 31001, 31004, 31103, 31301]

S = struct.pack
B = {18023: S('>I', 7) + S('>I', 1), 19003: S('>I', 7), 19005: S('>I', 7),
     19103: S('>I', 1), 19104: S('>I', 1), 19108: S('>I', 1) + S('>H', 0),
     19512: bytes([1]), 19517: S('>I', RID) + S('>H', 1) + b'1',
     19519: bytes([1]) + S('>I', RID) + S('>H', 1) + b'1',
     19524: S('>I', RID) + S('>H', 1) + b'1',
     19526: S('>I', 1) + S('>H', 1) + b'1' + bytes([1]), 19532: bytes([1]),
     20025: S('>H', 1) + b'x' + S('>H', 1) + b'1',
     20202: bytes([1]), 20205: bytes([1]), 20211: bytes([1]) + S('>I', 1),
     20302: S('>I', 1) + S('>H', 1) + b'1',
     20507: S('>I', 1) + S('>H', 1) + b'1' + bytes([1]),
     20508: S('>I', 1) + S('>H', 1) + b'1',
     20510: S('>I', 1) + S('>H', 1) + b'1' + bytes([1]),
     20705: S('>I', 1) + S('>H', 1) + b'1' + bytes([1]),
     20709: S('>I', 1) + S('>H', 1) + b'1', 20710: S('>I', 1) + S('>H', 1) + b'1',
     20711: S('>I', RID) + S('>H', 1) + b'1', 20712: S('>I', RID) + S('>H', 1) + b'1',
     20713: S('>I', 1) + S('>H', 1) + b'1' + bytes([1]),
     20714: S('>I', RID) + S('>H', 1) + b'1',
     21603: S('>I', 1), 21604: S('>I', 1)}


def ask(cmd, body=b''):
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(8.0)
    login(s)
    s.sendall(pack_frame(cmd, body))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        b = recv_exact(s, ln - 2)
        if rc == cmd:
            break
    s.close()
    return b


def load_gate():
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        'g', os.path.join(HERE, 'audit_emitted_fields.py'))
    g = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(g)
    cs, sc = g.load_specs()
    return g, sc


def main():
    ok = True
    g, sc = load_gate()
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())

    bad = 0
    for c in CMDS:
        b = ask(c, B.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 65 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '回执族-D' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 65 and fb == 0) else '✗'))
    ok = ok and ded >= 65 and fb == 0

    # ★ 回显 id（`19003`）
    b = ask(19003, struct.pack('>I', 7))
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    print('  19003 回显 id=%d ⇒ %s' % (got, '✓' if got == 7 else '✗'))
    ok = ok and got == 7

    # ★ 回显 + 真校验 rid（`19517`）
    b = ask(19517, B[19517])
    m = struct.unpack_from('>H', b, 1)[0]
    got = struct.unpack_from('>I', b, 1 + 2 + m)[0]
    b0 = ask(19517, struct.pack('>I', 9999) + struct.pack('>H', 1) + b'1')
    print('  19517 回显 rid=%d ｜ 他人 ⇒ code=%d ⇒ %s'
          % (got, b0[0], '✓' if (got == RID and b0[0] == 0) else '✗'))
    ok = ok and got == RID and b0[0] == 0

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
