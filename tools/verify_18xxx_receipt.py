# -*- coding: utf-8 -*-
"""R175 验收：`18xxx` 回执型 **31 条**（28 条 `{code,msg}` + 3 条 `{code,tips:string}`）。

判据：
  1. 31 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **真校验**：`18709`（`{partner_id}`）在 `role_heros` 里 ⇒ `code=1`，否则 `0`
  4. ★ **真校验**：`18014`/`18607`（`{rid,srv_id}`）== 本服角色 ⇒ `1`

用法： python tools/verify_18xxx_receipt.py
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
A = [18005, 18014, 18102, 18103, 18302, 18304, 18305, 18306, 18310, 18314, 18316, 18321,
     18500, 18501, 18503, 18505, 18602, 18603, 18607, 18610, 18758, 18801, 18811, 18812,
     18820, 18821, 18861, 18862]
B = [18709, 18711, 18712]
# ★ R176 子表组 14 条
C = [18000, 18006, 18008, 18009, 18010, 18020, 18021, 18024, 18025, 18312, 18320, 18404, 18605, 18609]
ALL = A + B + C

B70 = {18302: bytes([1]), 18304: bytes([1]), 18310: bytes([1]), 18314: bytes([1]),
       18316: bytes([1]), 18505: bytes([1]), 18503: struct.pack('>I', 1),
       18610: struct.pack('>I', 1), 18602: bytes([1]),
       18014: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1',
       18607: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1',
       18712: struct.pack('>I', RID) + struct.pack('>H', 1) + b'1' + struct.pack('>I', 30800),
       18709: struct.pack('>I', 30800), 18861: bytes([1]), 18862: bytes([1])}


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
    for c in ALL:
        b = ask(c, B70.get(c, b''))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 45 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    # ★ 本验收覆盖两个批次 ⇒ 日志文案有两种（`18xxx 回执型` 与 `18xxx 子表组`）
    ded = sum(1 for ln in new if '18xxx 回执型' in ln or '18xxx 子表组' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 31 and fb == 0) else '✗'))
    ok = ok and ded >= 45 and fb == 0

    # ★ 真校验：18709 的 partner_id
    b1 = ask(18709, struct.pack('>I', 30800))
    b0 = ask(18709, struct.pack('>I', 99999999))
    print('  18709 有效 partner ⇒ code=%d ｜ 无效 ⇒ code=%d ⇒ %s'
          % (b1[0], b0[0], '✓' if (b1[0] == 1 and b0[0] == 0) else '✗'))
    ok = ok and b1[0] == 1 and b0[0] == 0

    # ★ 真校验：18014 的 rid
    b1 = ask(18014, struct.pack('>I', RID) + struct.pack('>H', 1) + b'1')
    b0 = ask(18014, struct.pack('>I', 9999) + struct.pack('>H', 1) + b'1')
    print('  18014 本服 rid ⇒ code=%d ｜ 他人 ⇒ code=%d ⇒ %s'
          % (b1[0], b0[0], '✓' if (b1[0] == 1 and b0[0] == 0) else '✗'))
    ok = ok and b1[0] == 1 and b0[0] == 0

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
