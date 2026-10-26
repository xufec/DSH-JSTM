# -*- coding: utf-8 -*-
"""**未知命令普查**：把"我们没实现/没分析过"的命令，逐条定位到**客户端的归属文件**。

为什么需要：`tools/gap_worklist.py` 只告诉我们"哪些命令只得到默认响应"，
但**不知道那些命令属于哪个系统** —— 于是每次都要人工翻 APK。
本工具**一次遍历**所有 `.luac`，建出 `命令号 → [文件]` 的全量映射，
再叠加四列信息，输出一张可直接派活的表：

    cmd ｜ 归属（哪个系统的 ctrl/view/panel）｜ 我们的状态 ｜ 真机频次 ｜ SC 字段摘要

用法：
    python tools/cmd_unknown.py                    # 只看"未知且真机发过"的
    python tools/cmd_unknown.py --all              # 全部未实现的
    python tools/cmd_unknown.py --cmd 10407        # 单查
    python tools/cmd_unknown.py --md out.md

★ KSHORT 扫描口径：LuaJIT 的 `KSHORT` 指令 4 字节 = `[op][A][D_lo][D_hi]`，
  操作数 `D` 就是那个 16 位常量 ⇒ `d[i] == OP_KSHORT and u16(d[i+2]) == cmd`。
  这是本项目一直用来"扫命令号"的办法（`tools/_cmp_versions.py` 同款），**不做反汇编**。
"""
import argparse
import io
import json
import os
import re
import struct
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')          # 1.4.9（真机在跑的那版）
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')
SERVER = os.path.join(ROOT, 'server', 'mock_server.py')
LOG = os.path.join(ROOT, 'server', 'logs', 'tcp.log')

try:
    from luajit_dis import OPS
    OP_KSHORT = OPS.index('KSHORT')
except Exception:
    OP_KSHORT = 0x28


def build_owner_map(path):
    """一次遍历 → `{cmd: [文件…]}`。只保留 ctrl/view/panel/model 这类有语义的文件。"""
    z = zipfile.ZipFile(path)
    owners = {}
    for n in z.namelist():
        if not n.endswith('.luac'):
            continue
        d = z.read(n)
        if len(d) < 4:
            continue
        short = n.replace('assets/src/', '')
        for i in range(len(d) - 3):
            if d[i] == OP_KSHORT:
                v = struct.unpack_from('<H', d, i + 2)[0]
                if 10000 <= v < 40000:
                    owners.setdefault(v, []).append(short)
    return owners


def nice_owner(files, limit=3):
    """把文件列表压成"系统名"：优先 ctrl，其次 view/panel/model。"""
    def score(f):
        s = 0
        if 'ctrl' in f:
            s -= 30
        if '/view/' in f or f.endswith('_view.luac') or 'panel' in f:
            s -= 10
        if 'const' in f or 'config/' in f:
            s += 20
        return s
    fs = sorted(set(files), key=lambda f: (score(f), len(f)))
    out = []
    for f in fs:
        name = os.path.basename(f).replace('.luac', '')
        if name not in out:
            out.append(name)
        if len(out) >= limit:
            break
    return ', '.join(out) if out else '（未找到）'


def server_status(src):
    """返回 (专用==/专用in, 通用默认, 未开放)。"""
    s2 = re.sub(r'#[^\n]*', '', src)
    m = re.search(r'_GENERIC_DEFAULT_CMDS\s*=\s*frozenset\(\[(.*?)\]\)', s2, re.S)
    gen = set(int(x) for x in re.findall(r'\b\d{4,5}\b', m.group(1))) if m else set()
    m2 = re.search(r'_UNSUPPORTED_ACTION_CMDS\s*=\s*frozenset\(\[(.*?)\]\)', s2, re.S)
    uns = set(int(x) for x in re.findall(r'\b\d{4,5}\b', m2.group(1))) if m2 else set()
    eq = set(int(x) for x in re.findall(r'if cmd == (\d{4,5}):', s2))
    for mm in re.finditer(r'if cmd in \(([^)]*)\):', s2):
        for x in re.findall(r'\d{4,5}', mm.group(1)):
            eq.add(int(x))
    return eq, gen, uns


def scan_log(path, tail=40000):
    sent, dflt = {}, {}
    req = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for ln in f.readlines()[-tail:]:
            m = re.search(r'>> cmd=(\d+)', ln)
            if m:
                req = int(m.group(1))
                sent[req] = sent.get(req, 0) + 1
                continue
            m2 = re.search(r'<< (\d+) ', ln)
            if m2 and req is not None and int(m2.group(1)) == req:
                if '默认响应' in ln:
                    dflt[req] = dflt.get(req, 0) + 1
                req = None
    return sent, dflt


def sc_summary(fields, cmd):
    for v in fields.values():
        if str(v.get('cmd')) == str(cmd) and v.get('dir') == 'sc':
            return ', '.join('%s:%s' % (f.get('name'), f.get('type'))
                             for f in (v.get('fields') or []))[:90] or '（无字段）'
    return '（无 SC 定义）'


def system_of(files):
    """从归属文件里抽出**系统名**（优先 `xxx_ctrl`）。"""
    ctrls = sorted({os.path.basename(f).replace('.luac', '')
                    for f in files if f.endswith('_ctrl.luac')})
    if ctrls:
        return ctrls[0].replace('_ctrl', '')
    views = sorted({os.path.basename(f).replace('.luac', '')
                    for f in files if 'view' in f or 'panel' in f or 'model' in f})
    return views[0].replace('_view', '').replace('_panel', '').replace('_model', '') if views else '?'


def by_system(rows, owners, sent, dflt):
    """按系统聚合：该系统下**真机发过**的命令里，有多少我们**没实现**、多少只回默认。"""
    agg = {}
    for c, _ow, st, d, s, _sc in rows:
        sysname = system_of(owners.get(c, []))
        a = agg.setdefault(sysname, {'cmds': [], 'dflt': 0, 'sent': 0, 'none': 0})
        a['cmds'].append(c)
        a['dflt'] += d
        a['sent'] += s
        if '专用' not in st:
            a['none'] += 1
    out = sorted(agg.items(), key=lambda kv: (-kv[1]['sent'], -kv[1]['none']))
    lines = ['| 系统（客户端 ctrl） | 未实现命令数 | 默认响应次数 | 真机总发 | 命令号 |',
             '|---|---|---|---|---|']
    for name, a in out:
        lines.append('| **%s** | %d | %d | %d | %s |'
                     % (name, a['none'], a['dflt'], a['sent'],
                        ', '.join('`%d`' % c for c in sorted(a['cmds'])[:8])))
    return '\n'.join(lines), len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cmd', type=int)
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--by-system', action='store_true',
                    help='按系统（客户端 ctrl）聚合')
    ap.add_argument('--top', type=int, default=40)
    ap.add_argument('--md')
    args = ap.parse_args()

    fields = json.load(open(FIELDS, encoding='utf-8'))
    src = open(SERVER, encoding='utf-8').read()
    eq, gen, uns = server_status(src)
    sent, dflt = scan_log(LOG)

    print('正在扫 APK 建"命令→归属"映射…（一次遍历，约十几秒）', file=sys.stderr)
    owners = build_owner_map(APK)
    print('  命中 %d 个命令号有归属文件' % len(owners), file=sys.stderr)

    # 全部协议命令
    allcmds = sorted({int(v['cmd']) for v in fields.values() if str(v.get('cmd', '')).isdigit()})

    def status(c):
        s = []
        if c in eq:
            s.append('专用')
        if c in gen:
            s.append('默认')
        if c in uns:
            s.append('未开放')
        return '+'.join(s) or '**无**'

    rows = []
    for c in (([args.cmd] if args.cmd else allcmds)):
        st = status(c)
        if not args.cmd:
            if not args.all:
                # 默认只看"未实现 + 真机发过"
                if '专用' in st or sent.get(c, 0) == 0:
                    continue
            else:
                if '专用' in st:
                    continue
        rows.append((c, nice_owner(owners.get(c, [])), st,
                     dflt.get(c, 0), sent.get(c, 0), sc_summary(fields, c)))
    rows.sort(key=lambda r: (-r[3], -r[4]))

    if args.by_system:
        out, n_sys = by_system(rows, owners, sent, dflt)
        if args.md:
            open(args.md, 'w', encoding='utf-8', newline='\n') \
                .write('# 未实现命令 · 按系统聚合\n\n' + out + '\n')
            print('已写出 %s（%d 个系统）' % (args.md, n_sys))
        else:
            print(out)
        print('\n共 %d 个系统；命令 %d 条' % (n_sys, len(rows)))
        return

    lines = ['| cmd | 归属（客户端） | 我们的状态 | 默认响应 | 真机总发 | SC 字段 |',
             '|---|---|---|---|---|---|']
    for c, ow, st, d, s, sc in rows[:args.top]:
        lines.append('| `%d` | %s | %s | %d | %d | %s |' % (c, ow, st, d, s, sc))
    out = '\n'.join(lines)
    if args.md:
        open(args.md, 'w', encoding='utf-8', newline='\n').write(out + '\n')
        print('已写出 %s（%d 行）' % (args.md, len(rows[:args.top])))
    else:
        print(out)
    print('\n共 %d 条；协议命令总数 %d；有归属映射的 %d'
          % (len(rows), len(allcmds), len(owners)))


if __name__ == '__main__':
    main()
