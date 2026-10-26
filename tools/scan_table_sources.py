# -*- coding: utf-8 -*-
"""**系统性扫描**：剩余"未实现"命令里，哪些能**从配置表产出真实列表**。

思路（R129 验证有效）：一条 `SC` 若含 `table(...)`，且它的**元素字段名**能在某个
`server/cfg/config_*.json` 的条目里找到，就说明**有配置源** ⇒ 值得实现（比默认响应强）。

用法： python tools/scan_table_sources.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

CFG = os.path.join(ROOT, 'server', 'cfg')
FIELDS = json.load(open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8'))


def load_sets():
    src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
    s2 = re.sub(r'#[^\n]*', '', src)

    def grab(name):
        m = re.search(name + r'\s*=\s*frozenset\(\[(.*?)\]\)', s2, re.S)
        return set(int(x) for x in re.findall(r'\b\d{4,5}\b', m.group(1))) if m else set()

    eq = set(int(x) for x in re.findall(r'if cmd == (\d{4,5}):', s2))
    for mm in re.finditer(r'if cmd in \(([^)]*)\):', s2):
        for x in re.findall(r'\d{4,5}', mm.group(1)):
            eq.add(int(x))
    return grab('_GENERIC_DEFAULT_CMDS'), grab('_UNSUPPORTED_ACTION_CMDS'), eq


def cfg_field_index():
    """`{字段名: 出现在哪些配置表}` —— 扫每张配置的前 3 条条目的键名。"""
    idx = {}
    for fn in sorted(os.listdir(CFG)):
        if not fn.endswith('.json'):
            continue
        name = fn[:-5]
        try:
            d = json.load(open(os.path.join(CFG, fn), encoding='utf-8'))
        except Exception:
            continue
        keys = set()

        def walk(node, depth=0):
            if depth > 2 or not isinstance(node, dict):
                return
            if 'hash' in node and isinstance(node['hash'], dict):
                keys.update(node['hash'].keys())
                return
            for k, v in list(node.items())[:3]:
                keys.add(k)
                walk(v, depth + 1)

        walk(d)
        for k in keys:
            idx.setdefault(str(k), set()).add(name)
    return idx


def main():
    gen, uns, eq = load_sets()
    idx = cfg_field_index()
    print('  配置字段索引：%d 个字段名（来自 %d 张配置）'
          % (len(idx), len([f for f in os.listdir(CFG) if f.endswith('.json')])))

    # 真机发过的（从 gap_worklist 的输出无法直接读，这里用"未实现"全集）
    todo = sorted((gen | uns) - eq)
    print('  未实现命令：%d 条\n' % len(todo))

    rows = []
    for c in todo:
        v = None
        for x in FIELDS.values():
            if str(x.get('cmd')) == str(c) and x.get('dir') == 'sc':
                v = x
                break
        if not v:
            continue
        tabs = [f for f in (v.get('fields') or []) if (f.get('items') or [])]
        if not tabs:
            continue
        for t in tabs:
            names = [i.get('name') for i in (t.get('items') or [])]
            hits = {}
            for n in names:
                if n in idx:
                    hits[n] = sorted(idx[n])[:3]
            if len(hits) >= max(2, len(names) // 2):
                rows.append((c, t.get('name'), names, hits))

    rows.sort(key=lambda r: -len(r[3]))
    print('  ★ 找到 %d 个"元素字段能在配置表里对上"的表：\n' % len(rows))
    for c, tn, names, hits in rows[:14]:
        print('  cmd=%-6d %s' % (c, tn))
        print('     元素字段: %s' % ', '.join(names)[:100])
        for n, cfgs in list(hits.items())[:5]:
            print('       %-14s ← %s' % (n, ', '.join(cfgs[:2])))


if __name__ == '__main__':
    main()
