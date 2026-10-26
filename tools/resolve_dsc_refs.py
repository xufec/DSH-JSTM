#!/usr/bin/env python3
"""展开 `D|Dsc*|` 引用：把 fields.json 里的子结构引用还原成**真正的嵌套 items**。

## 问题（round37 发现）

`protocol/fields.json` 里

1. 472 个 `Dsc*` 条目**字段顺序被反转**（`dsc_spec.py` 头注早已警告），
   于是**类型随之错位**（反转后每个字段拿到下一个字段的类型）；
2. 顶层规格里约 180 处 `D|DscXXXXfield|` **保持未展开**，成为字符串类型。

后果：自动校验无法得知这些字段的字节长度（`Dsc10924int_args` 被当成 1 字节），
审计产生 5 条假阳性（10401 / 10502 / 10800 / 10924 / 11215）。

## 关联方法（可验证）

reader 原型（`ReadFMT(...)` + 逐个 `TSETS` 建表）才是**运行时真正用来解码的**，
其 TSETS 顺序 = 线序（**不反转**）。因此：

    用「字段名集合」把 fields.json 的 Dsc* 与 reader 配对：
      Dsc19400attr_ext (fields.json) = {attr_str, attr_ext_id}
      某 reader                      = {attr_ext_id, attr_str}     ⇒ 同名集合 ⇒ 配对成功

配对成功后，一律以 **reader 的顺序与类型为准** 覆盖 fields.json 的对应条目；
同名集合但类型不同者单独列出（说明类声明与 reader 不一致，值得记录）。

## 用法

    python tools/resolve_dsc_refs.py --dry-run     # 只报告（默认）
    python tools/resolve_dsc_refs.py --apply       # 写回 protocol/fields.json
    python tools/resolve_dsc_refs.py --apply --out protocol/fields.resolved.json
"""
import argparse
import collections
import json
import os
import re
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402
from dsc_spec import tokenize  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')

TYPENAME = {'C': 'uint8', 'c': 'int8', 'H': 'uint16', 'h': 'int16',
            'I': 'uint32', 'i': 'int32', 's': 'string', 'f': 'float',
            'd': 'double', 'b': 'bool', 'T': 'table', 'L': 'list'}
FMT_RE = re.compile(r'([CHIchis]|D\|[A-Za-z0-9_]+\|)+$')


def readers_in(data):
    """-> [(toks, names, proto_idx)]；names 顺序 = TSETS 顺序 = 线序（不反转）。"""
    r = parse_bytes(data)
    out = []
    for i, pt in enumerate(r.protos):
        strs = [s for s in pt.strings if isinstance(s, str)]
        fmts = [s for s in strs if FMT_RE.fullmatch(s or '')]
        if not fmts:
            continue
        fmt = max(fmts, key=lambda s: len(tokenize(s)))
        toks = tokenize(fmt)
        names = []
        for w in pt.bc:
            if (w & 0xff) == OPS.index('TSETS'):
                v = kidx(pt, (w >> 16) & 0xff)
                if isinstance(v, str) and v not in ('cs', 'sc'):
                    names.append(v)
        if not names or len(names) != len(toks):
            continue
        out.append((toks, names, i))
    return out


def build_reader_index():
    """{文件名: [(toks, names, proto_idx)]}

    ⚠ 不能只按「字段名集合」全局配对：`{val}` 这类名字在 uint8/uint16/uint32
    三种结构里都出现，全局配对会把它们塌缩成同一种并造成大量**错配**。
    正确做法是先用 Dsc 名字里的**号段**定位到对应 `cmd_resolve_<seg>.luac`，
    再在该文件内按名字集合匹配。
    """
    z = zipfile.ZipFile(APK)
    members = sorted(n for n in z.namelist()
                     if n.startswith('assets/src/config/protocal/cmd_resolve_')
                     and n.endswith('.luac'))
    idx = {}
    for name in members:
        short = name.rsplit('/', 1)[-1]
        try:
            rs = readers_in(z.read(name))
        except Exception:
            continue
        if rs:
            idx[short] = rs
    return idx


def candidate_files(idx, dsc_name):
    """Dsc10924int_args -> cmd_resolve_109.luac（号段逐级缩短直到文件存在）。"""
    m = re.match(r'Dsc(\d+)(.*)$', dsc_name)
    if not m:
        return []
    digits = m.group(1)
    for cut in range(len(digits), 2, -1):
        f = 'cmd_resolve_%s.luac' % digits[:cut]
        if f in idx:
            return [(f, idx[f])]
    # 退化：全库搜索
    return list(idx.items())


def match_reader(idx, dsc_name, names):
    """在候选文件里按名字（多重集）匹配；结构不一致则判为歧义。"""
    want = sorted(names)
    hits = []
    for fname, structs in candidate_files(idx, dsc_name):
        for toks, rnames, pi in structs:
            if sorted(rnames) == want:
                hits.append((tuple(toks), tuple(rnames), fname, pi))
    if not hits:
        return None, '未找到'
    uniq = set((t, n) for t, n, _, _ in hits)
    if len(uniq) > 1:
        return None, '歧义(%d 种结构)' % len(uniq)
    t, n, fname, pi = hits[0]
    return (list(t), list(n), fname, pi), None


def to_fields(toks, names):
    out = []
    for nm, ch in zip(names, toks):
        if ch.startswith('D|'):
            out.append({'name': nm, 'type': 'table', 'items': [],
                        '_ref': ch[2:-1]})
        else:
            out.append({'name': nm, 'type': TYPENAME.get(ch, ch)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--out', default=None)
    ap.add_argument('--limit-report', type=int, default=12)
    args = ap.parse_args()

    with open(FIELDS, encoding='utf-8') as f:
        data = json.load(f)

    idx = build_reader_index()
    nstruct = sum(len(v) for v in idx.values())
    print('# reader 原型: %d 个，分布于 %d 个号段文件' % (nstruct, len(idx)))

    # ---- 1) 修正 Dsc* 条目：以 reader 的顺序/类型为准 ----
    dsc_keys = [k for k in data if k.startswith('Dsc')]
    fixed = same = unmatched = 0
    type_conflicts = []
    unmatched_keys = []
    for k in dsc_keys:
        fs = data[k].get('fields') or []
        if not fs:
            continue
        r, why = match_reader(idx, k, [f['name'] for f in fs])
        if not r:
            unmatched += 1
            unmatched_keys.append((k, why))
            continue
        toks, names, fname, pi = r
        old = [(f['name'], f['type']) for f in fs]
        new = to_fields(toks, names)
        if [f for f in new if '_ref' in f]:
            continue                     # 含更深引用，交给第 2 步递归
        if old == [(f['name'], f['type']) for f in new]:
            same += 1
        else:
            fixed += 1
            # 同名集合但类型不同 ⇒ 类声明与 reader 不一致，值得记录
            if sorted(t for _, t in old) != sorted(f['type'] for f in new):
                type_conflicts.append((k, old, new))
            data[k]['fields'] = new
            data[k]['source'] = 'reader'
            data[k]['note'] = 'round38: 顺序/类型以 reader 原型为准（原 fields.json 为反转）'

    print('# Dsc* 条目 %d：修正 %d / 已一致 %d / 未配对 %d'
          % (len(dsc_keys), fixed, same, unmatched))
    print('#   其中「同名集合但类型不同」（类声明 vs reader 冲突）: %d'
          % len(type_conflicts))
    for k, old, new in type_conflicts[:args.limit_report]:
        print('    · %-28s old=%s' % (k, old))
        print('    %-30s new=%s' % ('', [(f['name'], f['type']) for f in new]))
    for k, why in unmatched_keys[:args.limit_report]:
        print('    ? 未配对 %-26s %s' % (k, why))

    # ---- 2) 展开顶层/嵌套的 D|X| 引用 ----
    def resolve(name, depth=0, seen=()):
        if name in seen or depth > 8:
            return []
        v = data.get(name)
        if not v:
            return None
        fs = v.get('fields') or []
        out = []
        for f in fs:
            if f.get('_ref'):
                sub = resolve(f['_ref'], depth + 1, seen + (name,))
                if sub is None:
                    return None
                out.append({'name': f['name'], 'type': 'table', 'items': sub})
            elif f.get('items'):
                out.append({'name': f['name'], 'type': 'table',
                            'items': [dict(x) for x in f['items']]})
            else:
                out.append({'name': f['name'], 'type': f['type']})
        return out

    expanded = 0
    failed = []

    def walk(fs, owner, path=''):
        nonlocal expanded
        out = []
        for f in fs:
            t = str(f.get('type') or '')
            if t.startswith('D|'):
                ref = t[2:-1]
                sub = resolve(ref)
                if sub is None:
                    failed.append((owner, path + f['name'], ref))
                    out.append({'name': f['name'], 'type': 'table'})
                    continue
                out.append({'name': f['name'], 'type': 'table', 'items': sub})
                expanded += 1
            elif f.get('items'):
                out.append({'name': f['name'], 'type': 'table',
                            'items': walk(f['items'], owner, path + f['name'] + '.')})
            else:
                out.append(f)
        return out

    for k, v in data.items():
        if v.get('dir') not in ('cs', 'sc'):
            continue
        v['fields'] = walk(v.get('fields') or [], k)

    print('# 展开 D|X| 引用: %d 处（失败 %d）' % (expanded, len(failed)))
    for owner, path, ref in failed[:args.limit_report]:
        print('    ! %-22s %-24s -> %s' % (owner, path, ref))

    # 清掉临时字段
    for k, v in data.items():
        for f in (v.get('fields') or []):
            walk2 = [f]
            while walk2:
                x = walk2.pop()
                x.pop('_ref', None)
                for y in (x.get('items') or []):
                    walk2.append(y)

    out = args.out or (FIELDS if args.apply else None)
    if out:
        if args.apply and not args.out:
            shutil.copyfile(FIELDS, FIELDS + '.bak_round38')
            print('# 原文件已备份 -> %s.bak_round38' % FIELDS)
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('# 已写出 %s' % out)
    else:
        print('# （dry-run，未写文件；加 --apply 生效）')


if __name__ == '__main__':
    main()
