#!/usr/bin/env python3
"""Show head/tail of an extracted Lua fragment (encoding-safe)."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r'tools/lua-check/_injected_glue.lua'
n = int(sys.argv[2]) if len(sys.argv) > 2 else 14
src = open(path, encoding='utf-8', errors='replace').read()
lines = src.split('\n')
print('total lines:', len(lines), 'bytes:', len(src))
print('--- first %d ---' % n)
for i in range(min(n, len(lines))):
    print('%4d | %s' % (i + 1, lines[i][:120]))
print('--- last %d ---' % n)
for i in range(max(0, len(lines) - n), len(lines)):
    print('%4d | %s' % (i + 1, lines[i][:120]))
