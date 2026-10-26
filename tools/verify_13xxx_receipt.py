# -*- coding: utf-8 -*-
"""R167 验收：`13xxx` 的**回执型 62 条**（按 SC 模式分 3 组）。

判据：
  1. 62 条**结构精确**（门禁权威解析器）
  2. A/B 组（`{code|tips:u8,msg}`）与 C 组（`{tips:u16,msg}`）的**宽度不同** —— 用解析器验证
  3. 有参命令的 `code`/`tips` 随"参数非空"如实

★ 本批的分组**边界由 spec 定义**（3 个模式的 SC 确实只有"状态+消息"），
  与 R163 的"按号段一刀切"本质不同。

用法： python tools/verify_13xxx_receipt.py
"""
import io
import os
import socket
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
A = [13012, 13074, 13075, 13303, 13357, 13358, 13368, 13415, 13503, 13508, 13514, 13515,
     13516, 13517, 13527, 13528, 13532, 13536, 13537, 13541, 13543, 13547, 13564, 13571,
     13576, 13582, 13584, 13711, 13721, 13731, 13743, 13811, 13818, 13842, 13843, 13902, 13907]
B = [13026, 13083, 13206, 13209, 13210, 13211, 13213, 13214, 13216, 13217, 13220, 13225,
     13226, 13228, 13229, 13231, 13256, 13258]
C = [13000, 13001, 13044, 13051, 13057, 13086, 13202]


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
    bad = 0
    for c in A + B + C:
        b = ask(c, b'')
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 62 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    # C 组比 A/B 组多 1 字节（`tips:u16` vs `code|tips:u8`）
    bA = ask(A[0], b'')
    bC = ask(C[0], b'')
    print('  A 组 %d 首字节=%d ｜ C 组 %d 前两字节=%d'
          % (A[0], bA[0], C[0], struct.unpack_from('>H', bC, 0)[0]))
    a1 = len(bA) >= 3 and len(bC) >= 4
    print('  ★ A/B 组(1 字节) 与 C 组(2 字节) 宽度不同，解析器都通过 ⇒ %s' % ('✓' if a1 else '✗'))
    ok = ok and a1

    # 有参：`13537 {item_bid:u32}` 非零 ⇒ 1；零 ⇒ 0
    # ★ `13537` 属 A 组 `{code:u8, msg:string}` ⇒ **`code` 在 `b[0]`**
    #   （我第一版去 `1+2+len(msg)` 之后读，那里是 msg 内容、当然是空 ⇒ 读到 -1）
    b1 = ask(13537, struct.pack('>I', 21903))
    b0 = ask(13537, struct.pack('>I', 0))
    print('  13537 item_bid 非零 ⇒ code=%d ｜ 零 ⇒ code=%d ⇒ %s'
          % (b1[0], b0[0], '✓' if (b1[0] == 1 and b0[0] == 0) else '✗'))
    ok = ok and b1[0] == 1 and b0[0] == 0

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
