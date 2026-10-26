# -*- coding: utf-8 -*-
"""R171 验收：`12xxx` 的 **`my_ord` 族（"榜上有我"）21 条**。

判据：
  1. 21 条**结构精确**（门禁权威解析器）
  2. ★ **走的是专用分支**（读 `tcp.log` —— 纪律第 22 条）
  3. ★ **"榜上有我"**：`my_ord == 1`、`rank_list` **恰好 1 条**，且 `rid == 本服角色`、`name` 与 DB 一致

★ `12918`（宗门榜，元素结构完全不同）本批**如实不做**（走兜底），下批单独攻克。

用法： python tools/verify_rank_family.py
"""
import io
import os
import socket
import sqlite3
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
RID = 1001
CMDS = (12904, 12913, 12914, 12915, 12916, 12917, 12919, 12920, 12921, 12923,
        12924, 12925, 12926, 12927, 12928, 12929, 12930, 12932, 12933, 12934, 12973,
        # ★ R172 第二批 10 条
        12977, 12978, 12979, 12986, 12988, 12995, 12996, 12997, 12998, 12999,
        # ★ R173：攻克 R172 如实留下的两条
        12918, 12994)


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


def q(sql, args=()):
    c = sqlite3.connect(DB)
    try:
        r = c.execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        r = []
    c.close()
    return r


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
        b = ask(c, bytes([1, 10, 0]))
        r = g.audit_body(sc[str(c)], b, c)
        if r['consumed'] != r['len'] or r['err']:
            bad += 1
            print('  ✗ %d len=%d 消耗=%d err=%s' % (c, r['len'], r['consumed'], r['err']))
    print('\n== 33 条结构精确性 ==  失败 %d 条 ⇒ %s' % (bad, '✓' if bad == 0 else '✗'))
    ok = ok and bad == 0

    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    ded = sum(1 for ln in new if '榜上有我' in ln)
    fb = sum(1 for ln in new if '兜底响应' in ln or '默认响应' in ln)
    print('  ★ 专用日志 %d 条 ｜ 兜底 %d 条 ⇒ %s'
          % (ded, fb, '✓' if (ded >= 21 and fb == 0) else '✗'))
    ok = ok and ded >= 33 and fb == 0

    # ★ "榜上有我"：my_ord=1 + rank_list 恰 1 条 + rid/name 一致
    row = q('SELECT name FROM roles WHERE rid=?', (RID,))
    wname = row[0][0] if row else ''
    good = 0
    for c in CMDS:
        b = ask(c, bytes([1, 10, 0]))
        # ★ `12994` 的 `my_ord` 是 **uint16**（读 1 字节只会拿到低字节 ⇒ 误判为 0）
        my_ord = (struct.unpack_from('>H', b, 0)[0] if c == 12994 else b[0])
        # ★ `12994` 的 **`my_ord` 是 uint16** ⇒ 起始偏移 2+4 = **6**（其余是 1+4 = 5）
        o = 6 if c == 12994 else 5
        # 跳过 my_* 附加字段：用解析器的 SC 定义找 rank_list 前还有哪些字段
        scf = sc[str(c)]
        idx = [i for i, f in enumerate(scf) if f.get('name') == 'rank_list'][0]
        for f in scf[2:idx]:                         # ★ `my_ord`(0) 与 `my_val`(1) **已在 o=5 里跳过**
            tp = f.get('type')
            if tp == 'string':
                n = struct.unpack_from('>H', b, o)[0]
                o += 2 + n
            elif tp == 'uint32':
                o += 4
            elif tp == 'uint16':
                o += 2
            elif tp == 'table':
                n = struct.unpack_from('>H', b, o)[0]
                o += 2 + n * 0                       # 空表
            else:
                o += 1
        cnt = struct.unpack_from('>H', b, o)[0]
        o += 2
        # 元素首字段 `ord:u8`；★ `12994` 的 `ord` 之后还有 `friend_val:u32` ⇒ 多跳 4
        o += 1 + (4 if c == 12994 else 0)
        rid = struct.unpack_from('>I', b, o)[0]
        o += 4
        sl = struct.unpack_from('>H', b, o)[0]
        o += 2 + sl
        nl = struct.unpack_from('>H', b, o)[0]
        nm = b[o + 2:o + 2 + nl].decode('utf-8', 'replace')
        if my_ord == 1 and cnt == 1 and rid == RID and nm == wname:
            good += 1
        else:
            print('  ✗ %d my_ord=%d cnt=%d rid=%d name=%r' % (c, my_ord, cnt, rid, nm))
    print('\n== ★ "榜上有我" ==  符合 %d / %d ⇒ %s'
          % (good, len(CMDS), '✓' if good == len(CMDS) else '✗'))
    ok = ok and good == len(CMDS)

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
