#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarise a uiautomator XML dump: text + clickable nodes + bounds."""
import re
import sys

path = sys.argv[1]
x = open(path, encoding='utf-8', errors='replace').read()
print('xml bytes:', len(x))
pat = re.compile(r'<node\b[^>]*>')
n = 0
for m in pat.finditer(x):
    s = m.group(0)
    t = re.search(r'text="([^"]*)"', s)
    c = re.search(r'clickable="(\w+)"', s)
    cl = re.search(r'class="([^"]*)"', s)
    b = re.search(r'bounds="([^"]*)"', s)
    res = re.search(r'resource-id="([^"]*)"', s)
    txt = t.group(1) if t else ''
    clickable = c.group(1) if c else '?'
    if not txt and clickable != 'true':
        continue
    n += 1
    print('%-34s click=%-5s %-22s %-26s %s' % (
        repr(txt)[:34], clickable,
        (cl.group(1).split('.')[-1] if cl else '?'),
        (res.group(1).split('/')[-1] if res else ''),
        b.group(1) if b else ''))
print('nodes of interest:', n)
