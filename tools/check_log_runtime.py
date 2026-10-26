# -*- coding: utf-8 -*-
"""R216b：★★★ **"运行时日志 vs 回包"一致性检查**（修正 R216 的判据）。

★ R216 的错：**静态扫源码里的日志行** ⇒ 抓到"**失败/实验分支**"的日志
  （如 `code=0 (钻石不足)`）⇒ **误报 3 处** ❌
★ 正确做法：**运行时抓 `tcp.log` 的新行** ⇒ 那是**实际执行分支**的日志 ✓
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
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')

W = {'uint8': 1, 'int8': 1, 'bool': 1, 'uint16': 2, 'int16': 2,
     'uint32': 4, 'int32': 4, 'uint64': 8, 'float': 4}


def parse_fields(fields, b, o):
    out = {}
    for f in (fields or []):
        if not isinstance(f, dict):
            continue
        nm = f.get('name') or ''
        tp = (f.get('type') or '').lower()
        its = f.get('items') or []
        if its:
            n = struct.unpack_from('>H', b, o)[0] if len(b) >= o + 2 else 0
            out[nm] = n
            o += 2
            for _ in range(n):
                _, o = parse_fields(its, b, o)
            continue
        if tp.startswith('string'):
            n = struct.unpack_from('>H', b, o)[0] if len(b) >= o + 2 else 0
            out[nm] = b[o + 2:o + 2 + n].decode('utf-8', 'replace')
            o += 2 + n
            continue
        w = W.get(tp, 1)
        out[nm] = int.from_bytes(b[o:o + w], 'big') if len(b) >= o + w else 0
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


# ★ 待查命令 = 所有"日志里出现过 `xxx=0`"的命令（静态收集命令号，运行时核对）
src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
cmds = set()
for m in re.finditer(r"log\('tcp\.log',\s*'[^']*?(\d{5})\s+SC_\1[^']*?([a-z_]+)=0", src):
    cmds.add(int(m.group(1)))
print('  ★ 静态命中"日志含 `xxx=0`"的命令: %d 个' % len(cmds))

bad = []
for c in sorted(cmds):
    base = len(open(LOG, encoding='utf-8', errors='replace').readlines())
    b = ask(c)
    if b is None:
        continue
    new = open(LOG, encoding='utf-8', errors='replace').readlines()[base:]
    # ★ 抓"实际执行"的那条日志
    line = None
    for l in new:
        if ('<< %d ' % c) in l or ('<< %d\t' % c) in l:
            line = l.strip()
    if line is None:
        continue
    vals, _ = parse_fields(sc.get(str(c)) or [], b, 0)
    # ★ 日志里的 `xxx=0`
    for mm in re.finditer(r'([a-z_]+)=0\b', line):
        fld = mm.group(1)
        v = vals.get(fld)
        if isinstance(v, int) and v != 0:
            bad.append((c, fld, v, line[:80]))

print('\n  ★★ **运行时日志写 0 但回包真实值非 0**: %d 组' % len(bad))
for c, f, v, line in bad:
    print('     cmd=%-6d %-16s 真实值=%-8s ｜ %s' % (c, f, v, line))
if not bad:
    print('     （无）✓ —— 所有日志与回包一致')
