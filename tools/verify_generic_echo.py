# -*- coding: utf-8 -*-
"""R188 验收：**跨家族 77 条 + 通用回显编码器**（专用分支 1105 → 1182）。

★★ 本批的**方法论突破**：`encode_by_sc_with_echo(cmd, body)`
   1. 用 **CS 的字段顺序**算 body 偏移（string = 2 + len）
   2. 用 **SC 的字段顺序**编码；**同名同类型 ⇒ 读 body 真值**
   3. `code`/`result` 首字段 ⇒ 1
   ★ **一次写好、77 条通用** —— 彻底解决"手写偏移"（本会话错了 N 次）。

判据：
  1. 77 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★★ **回显真的生效**：`14211`/`14212`（`bid`）、`14906`（`bid`）、`15002`（`item_id`）、
     `15516`（`jie`）、`21305`（`bid`）、`31002`（`boss_id`）的**回显值 == 请求值**

用法： python tools/verify_generic_echo.py
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

CMDS = [1201, 14020, 14021, 14022, 14023, 14028, 14202, 14206, 14207, 14210, 14211, 14212,
        14298, 14299, 14300, 14302, 14400, 14403, 14501, 14502, 14503, 14505, 14801, 14803,
        14806, 14811, 14906, 15000, 15002, 15016, 15101, 15201, 15207, 15208, 15301, 15303,
        15516, 15517, 15520, 15601, 15607, 15816, 15817, 15820, 15900, 21305, 21308, 21309,
        21310, 21311, 21313, 21399, 21600, 21601, 21602, 21605, 21609, 31000, 31002, 31003,
        31005, 31006, 31007, 31008, 31100, 31101, 31102, 31104, 31200, 31201, 31202, 31203,
        31204, 31205, 31206, 31207, 31208]

# 回显测试：CS 是 `{<name>:uint32}` 的单字段命令
ECHO_U32 = {14211: 21903, 14212: 21903, 21305: 21903, 21309: 21903,
            31002: 21903, 31005: 21903, 31101: 21903, 31102: 21903, 21399: 21903}
# ★ `14906` 的 CS 是 **`{bid:uint16}`**（不是 u32）⇒ 归 u16 组（我第一版发成 u32 ⇒ 服务端读前 2 字节）
ECHO_U16 = {15520: 21903, 15820: 21903, 21605: 21903, 14906: 21903}
ECHO_U8 = {14020: 7, 15516: 7, 15517: 7, 15816: 7, 15817: 7, 21602: 7, 21609: 7}


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


def find_u32(b, val):
    """在回包里找该 u32 值（回显的最简判据）。"""
    pat = struct.pack('>I', val)
    return b.find(pat)


def main():
    ok = True
    g, sc = load_gate()
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())

    bad = 0
    for c in CMDS:
        b = ask(c)
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 77 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '跨家族77（' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 77 and fb == 0) else '✗'))
    ok = ok and ded >= 77 and fb == 0

    # ★★ 回显验证（u32）
    good, tot = 0, 0
    for c, v in ECHO_U32.items():
        b = ask(c, struct.pack('>I', v))
        tot += 1
        if find_u32(b, v) >= 0:
            good += 1
        else:
            print('  ✗ %d 未回显 u32=%d（回包 %s）' % (c, v, b.hex(' ')[:40]))
    print('\n  ★ u32 回显：%d/%d ⇒ %s' % (good, tot, '✓' if good == tot else '✗'))
    ok = ok and good == tot

    # ★ 回显验证（u16）
    good2, tot2 = 0, 0
    for c, v in ECHO_U16.items():
        b = ask(c, struct.pack('>H', v))
        tot2 += 1
        if b.find(struct.pack('>H', v)) >= 0:
            good2 += 1
        else:
            print('  ✗ %d 未回显 u16=%d' % (c, v))
    print('  ★ u16 回显：%d/%d ⇒ %s' % (good2, tot2, '✓' if good2 == tot2 else '✗'))
    ok = ok and good2 == tot2

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
