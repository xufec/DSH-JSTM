# -*- coding: utf-8 -*-
"""R215b：★★★ **"日志 vs 回包"一致性批量检查** —— 抓出"日志硬编码 0 但回包非 0"的误导源。

★ 背景：`19400` 的日志写死 `mingge_list=0`，而**回包实际是 2 条** ⇒
   它让我在 R203 把 `19400` 误判为"空表" ❌
★ 本脚本对每个"日志里写死 `xxx=0`"的命令，**实际发包**，解析出**真实条数**，对比。
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

# ① 找"日志里写死 xxx=0"的命令 + 背后的表名
lines = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read().split('\n')
sus = []
for i, ln in enumerate(lines):
    m = re.search(r"log\('tcp\.log',\s*'\s*<<\s*%?d?\s*(\d{4,6})?\s*SC_?\d*\s*(.*?)'", ln)
    if not m:
        m2 = re.search(r"(\d{5})\s+SC_\1\s+(.*?)'", ln)
        if not m2:
            continue
        cmd, rest = int(m2.group(1)), m2.group(2)
    else:
        cmd = int(m.group(1)) if m.group(1) else None
        rest = m.group(2)
        if cmd is None:
            m3 = re.search(r'(\d{5})', ln)
            cmd = int(m3.group(1)) if m3 else None
    if cmd is None:
        continue
    for mm in re.finditer(r'([a-z_]+)=0\b', rest):
        sus.append((cmd, mm.group(1), i + 1))
print('  ★ 可疑（日志写死 `xxx=0`）: %d 处' % len(sus))


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


print()
print('  ★ 逐条实测（看"日志声称 0"的字段在回包里是否非 0）:')
seen = set()
for cmd, field, ln_no in sus:
    if (cmd, field) in seen:
        continue
    seen.add((cmd, field))
    # ★ 只查 SC 里真有该 field 的
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
    r = g.audit_body(sc.get(str(cmd)) or [], b, cmd)
    # ★ 找该 field 在字节流里的值（用门禁的解析结果的 offsets 不一定有 ⇒ 简化：看 hex 是否全 0）
    print('     L%-6d cmd=%-6d field=%-18s SC=%s ｜ 回包 %d 字节，全零=%s'
          % (ln_no, cmd, field, hit.get('type'), len(b), set(b) == {0}))
