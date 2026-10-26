#!/usr/bin/env python3
"""AutoConstruct 调用点审计：独立还原规格并与 protocol/fields.json 交叉比对。

## 为什么需要这个工具

`protocol/fields.json` 由 `tools/extract_fields.py` 生成，其映射路径是
「class/descriptor 名 -> 注册原型 FNEW -> builder proto -> spec 数组」。
这条路径可靠，但它**不会自检**：一旦某个 proto 的 spec 被错配，
fields.json 会静默出错。

本工具走**第二条独立路径**：直接扫描 `cmd_resolve_*.luac` 里
`AutoConstruct` 的调用点三元组

    KSTR  'cs' | 'sc'     方向
    KSHORT <cmd>          命令号
    TDUP  <spec 数组>     字段规格（'name__C' / 'args__T__a@I##b@s'）

再把两边按 (cmd, dir) 对齐逐字段比对。

## 判据说明（真实抓包只能当弱证据）

客户端发 CS 时，body 尾部固定多出 4 字节缓冲区残留
（16500 body=00660000、17200 body=010103e9、16400 body=type+00000003、
16603 body=bid+0001316f、16605 body=102*bid+2d2d2d2d）。
因此「包长」无法区分 `{bid}` 与 `{bid,num}` —— 两者对 8 字节 body 都"对得上"。
**规格必须以上面的 AutoConstruct spec 为准**，不能用包长反推。

用法：
    python tools/audit_specs_vs_fields.py            # 全量审计并打印汇总
    python tools/audit_specs_vs_fields.py --cmd 16603  # 只查单个命令
    python tools/audit_specs_vs_fields.py --json out.json
"""
import argparse
import collections
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader, TableConst  # noqa: E402
from luajit_dis import OPS  # noqa: E402
from extract_fields import SPEC, parse_spec, kidx  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')

OP_GGET = OPS.index('GGET')
OP_KSTR = OPS.index('KSTR')
OP_KSHORT = OPS.index('KSHORT')
OP_KNUM = OPS.index('KNUM')
OP_TDUP = OPS.index('TDUP')
OP_CALL = OPS.index('CALL')

# AutoConstruct/KSHORT 之间允许的指令跨度
WINDOW = 24


def op_of(w):
    return w & 0xff


def scan_callsite(proto):
    """在单个 proto 内定位消息定义 -> [(cmd, dir, spec_array)]。

    实现在于「spec 表常量」本身：AutoConstruct 的第三个参数是一张
    字符串数组（'name__C' / 'args__T__a@I##b@s'）。方向与命令号紧邻其前，
    因此对每个 spec 表向前开窗取最近的 KSTR('cs'|'sc') 与 KSHORT。
    （GGET 的全局名不走 kgc，无法用 kidx 解析，故不以它为锚点。）
    """
    bc = proto.bc
    out = []
    for sp, w in enumerate(bc):
        if op_of(w) != OP_TDUP:
            continue
        v = kidx(proto, (w >> 16) & 0xffff)
        if not (isinstance(v, TableConst) and v.array):
            continue
        arr = [x for x in v.array if isinstance(x, str) and SPEC.match(x)]
        if not arr:
            continue
        direction = cmd = None
        for j in range(max(0, sp - 12), sp):
            wj = bc[j]
            op = op_of(wj)
            d = (wj >> 16) & 0xffff
            if op == OP_KSTR:
                vv = kidx(proto, d)
                if vv in ('cs', 'sc'):
                    direction = vv
            elif op in (OP_KSHORT, OP_KNUM):
                vv = kidx(proto, d) if op == OP_KNUM else d
                if isinstance(vv, float) and vv == int(vv):
                    vv = int(vv)
                if isinstance(vv, int) and 0 < vv < 100000:
                    cmd = vv
        if direction and cmd:
            out.append((cmd, direction, arr))
    return out


def build_from_apk():
    """扫描全部 cmd_resolve_*.luac -> {(cmd, dir): {'file','specs':[...]}}"""
    z = zipfile.ZipFile(APK)
    members = sorted(n for n in z.namelist()
                     if n.startswith('assets/src/config/protocal/cmd_resolve_')
                     and n.endswith('.luac'))
    found = {}
    for m in members:
        try:
            r = Reader(z.read(m))
            r.parse()
        except Exception:
            continue
        for pt in r.protos:
            for cmd, direction, spec in scan_callsite(pt):
                key = ('%05d' % cmd, direction)
                found.setdefault(key, {'file': m.rsplit('/', 1)[-1], 'specs': spec})
    return found


def load_fields():
    with open(FIELDS, encoding='utf-8') as f:
        return json.load(f)


def norm_fields(fs):
    """把 fields.json 的字段结构归一成可比较的元组序列。"""
    out = []
    for f in fs or []:
        items = f.get('items')
        if items:
            out.append((f['name'], 'table', tuple((x.get('name'), x.get('type')) for x in items)))
        else:
            out.append((f['name'], f.get('type'), None))
    return tuple(out)


def norm_spec(specs):
    """规格 -> 可比较元组。子结构引用 `D|DscX|` 归一为 ('REF')。

    注意：round38 起 fields.json 里的 `D|DscX|` 已被**展开成真正的嵌套 items**
    （见 tools/resolve_dsc_refs.py），而 AutoConstruct 原始 spec 里仍是字面引用。
    因此规格侧把引用标记为 'REF'，比较时只要求"对侧也是表"，不再逐字段比。
    """
    def item_type(t):
        return 'REF' if str(t).startswith('D|') else t

    out = []
    for f in (parse_spec(s) for s in specs):
        items = f.get('items')
        if items:
            out.append((f['name'], 'table',
                        tuple((x['name'], item_type(x['type'])) for x in items)))
        else:
            out.append((f['name'], item_type(f['type']), None))
    return tuple(out)


def fields_equal(got, want):
    """比较 fields.json 归一结果与规格归一结果；规格侧 'REF' 处放宽为"必须是表"。"""
    if len(got) != len(want):
        return False
    for g, w in zip(got, want):
        if g[0] != w[0]:
            return False
        if w[1] == 'table':
            if g[1] != 'table':
                return False
            if w[2] is None:
                continue                     # 规格里是 table 但无内联子字段 ⇒ 不深比
            if any(x[1] == 'REF' for x in w[2]):
                continue                     # 含子结构引用 ⇒ 只要求对侧也是表
            if not fields_equal(g[2] or (), w[2]):
                return False
        else:
            if g[1] != w[1]:
                return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cmd', help='只审计某个命令号')
    ap.add_argument('--json', help='把审计结果写到 JSON')
    ap.add_argument('--show-ok', action='store_true', help='同时打印一致的条目')
    args = ap.parse_args()

    callsites = build_from_apk()
    fields = load_fields()

    # fields.json: 按 (cmd, dir) 归组（可能一个 cmd 有多个类名）
    by_key = collections.defaultdict(list)
    for key, v in fields.items():
        cmd = str(v.get('cmd') or '')
        direction = v.get('dir')
        m = re.match(r'^(CS|SC)', key)
        if not cmd or direction not in ('cs', 'sc') or not m:
            continue
        by_key[(cmd.zfill(5), direction)].append((key, v))

    if args.cmd:
        c = str(args.cmd).zfill(5)
        keys = [k for k in set(list(callsites) + list(by_key)) if k[0] == c]
    else:
        keys = sorted(set(list(callsites) + list(by_key)))

    stats = {'ok': 0, 'diff': 0, 'only_spec': 0, 'only_fields': 0, 'empty': 0,
             'empty_msg': 0}
    diffs = []
    for k in keys:
        cs = callsites.get(k)
        fl = by_key.get(k) or []
        if not fl:
            stats['only_spec'] += 1
            diffs.append({'key': k, 'kind': 'only-spec', 'spec': cs['specs'] if cs else None})
            continue
        if not cs:
            # fields.json 有、调用点扫描没有：区分「空消息（本就无 spec）」
            # 与「有字段却找不到 spec」（真正的可疑项）。
            nonempty = [k for k, v in fl if v.get('fields')]
            if nonempty:
                stats['only_fields'] += 1
                diffs.append({'key': k, 'kind': 'only-fields',
                              'fields': [x[0] for x in fl]})
            else:
                stats['empty_msg'] += 1
            continue
        want = norm_spec(cs['specs'])
        for key, v in fl:
            got = norm_fields(v.get('fields'))
            if not got:
                stats['empty'] += 1
                diffs.append({'key': k, 'kind': 'fields-empty', 'class': key, 'spec': cs['specs']})
                continue
            if fields_equal(got, want):
                stats['ok'] += 1
                if args.show_ok:
                    print('OK   %-14s %s' % (key, cs['file']))
            else:
                stats['diff'] += 1
                diffs.append({'key': k, 'kind': 'diff', 'class': key, 'file': cs['file'],
                              'spec': cs['specs'], 'fields': got, 'want': want})

    print('=== AutoConstruct 调用点 vs fields.json ===')
    print('  调用点(独立还原)条目: %d' % len(callsites))
    print('  fields.json 命令对 : %d' % len(by_key))
    print('  一致 %d / 不一致 %d / 仅规格 %d / 仅fields(有字段) %d / fields空 %d'
          % (stats['ok'], stats['diff'], stats['only_spec'], stats['only_fields'], stats['empty']))
    print('  空消息(无 spec，一致视为正常) %d' % stats['empty_msg'])
    print()
    for d in diffs:
        if d['kind'] == 'diff':
            print('✗ DIFF %s (%s)  %s' % (d['class'], d['key'][1], d.get('file', '')))
            print('    spec  : %s' % (d['spec'],))
            print('    fields: %s' % (d['fields'],))
            print('    want  : %s' % (d['want'],))
        elif d['kind'] in ('only-spec', 'fields-empty'):
            print('· %s %s' % (d['kind'], d['key']))
            print('    spec  : %s' % (d['spec'],))
        else:
            print('· only-fields %s -> %s' % (d['key'], d['fields']))

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({'stats': stats, 'diffs': diffs}, f, ensure_ascii=False, indent=1)
        print('\n已写出 %s' % args.json)


if __name__ == '__main__':
    main()
