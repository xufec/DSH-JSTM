# -*- coding: utf-8 -*-
"""R216：★★★ **精确核对"日志声称 0"的字段** —— 按 SC 解析出**该字段的真实值**。

★ 与 R215 的 `check_log_vs_reply.py` 的区别：
   R215 只看"回包是否全零"（**粗略**，会误判"别的字段非零"）；
   ★ 本脚本**按权威 SC 逐字段解析** ⇒ **直接拿到"日志里那个字段"的值** ✓
"""
import importlib.util
import io
import os
import re
import socket
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from _login149 import login, pack_frame, recv_exact  # noqa: E402

sp = importlib.util.spec_from_file_location(
    'g', os.path.join(ROOT, 'tools', 'audit_emitted_fields.py'))
g = importlib.util.module_from_spec(sp)
sp.loader.exec_module(g)
cs, sc = g.load_specs()

W = {'uint8': 1, 'int8': 1, 'bool': 1, 'uint16': 2, 'int16': 2,
     'uint32': 4, 'int32': 4, 'uint64': 8, 'float': 4}


def parse_fields(fields, b, o):
    """★ 按权威 SC 解析 ⇒ `{字段名: 值}`（子表只记条数）。"""
    out = {}
    for f in (fields or []):
        if not isinstance(f, dict):
            continue
        nm = f.get('name') or ''
        tp = (f.get('type') or '').lower()
        its = f.get('items') or []
        if its:
            if len(b) < o + 2:
                out[nm] = 0
                continue
            n = struct.unpack_from('>H', b, o)[0]
            out[nm] = n
            o += 2
            for _ in range(n):
                sub, o = parse_fields(its, b, o)
            continue
        if tp.startswith('string'):
            if len(b) < o + 2:
                out[nm] = ''
                continue
            n = struct.unpack_from('>H', b, o)[0]
            out[nm] = b[o + 2:o + 2 + n].decode('utf-8', 'replace')
            o += 2 + n
            continue
        w = W.get(tp, 1)
        if len(b) < o + w:
            out[nm] = 0
            continue
        out[nm] = int.from_bytes(b[o:o + w], 'big')
        o += w
    return out, o


def ask(cmd, body=b''):
    try:
        s = socket.create_connection(('127.0.0.1', 9000), 5)
        s.settimeout(5.0)
        login(s)
        s.sendall(pack_frame(cmd, body))
        while True:
            ln, rc = struct.unpack('>IH', recv_exact(s, 6))
            b = recv_exact(s, ln - 2)
            if rc == cmd:
                break
        s.close()
        return b
    except Exception:
        return None


# ★ 从日志里抽"写死 0"的（命令号, 字段名）
lines = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read().split('\n')
sus = []
for i, ln in enumerate(lines):
    if "log('tcp.log'" not in ln:
        continue
    m = re.search(r'(\d{5})\s+SC_\1\s+(.*)', ln)
    if not m:
        continue
    cmd = int(m.group(1))
    for mm in re.finditer(r'([a-z_]+)=0\b', m.group(2)):
        sus.append((cmd, mm.group(1), i + 1))
uniq = sorted(set((c, f) for c, f, _ in sus))
print('  ★ 可疑（命令, 字段）: %d 组' % len(uniq))

real = []
for cmd, field, in [(c, f) for c, f in uniq]:
    hit = None
    for f in (sc.get(str(cmd)) or []):
        if isinstance(f, dict) and f.get('name') == field:
            hit = f
            break
    if hit is None:
        continue
    b = ask(cmd)
    if b is None:
        continue
    vals, _ = parse_fields(sc.get(str(cmd)) or [], b, 0)
    v = vals.get(field)
    real.append((cmd, field, v, hit.get('type')))

bad = [x for x in real if isinstance(x[2], int) and x[2] != 0]
print('\n  ★★ **日志写 0 但真实值非 0** 的: %d 组' % len(bad))
for cmd, field, v, tp in sorted(bad, key=lambda x: -abs(x[2]) if isinstance(x[2], int) else 0):
    print('     cmd=%-6d %-18s 真实值=%-8s（SC %s）' % (cmd, field, v, tp))
print('\n  ★ 日志正确的: %d 组' % (len(real) - len(bad)))
