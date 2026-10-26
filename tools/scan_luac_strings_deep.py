#!/usr/bin/env python3
"""在 1.4.9 APK 全部 .luac 中搜索字符串常量，**包含嵌套 TableConst 的键与值**。

为什么需要这个工具：`proto.strings`（= `luajit_bc.Proto.strings`）只返回
常表中的**顶层字符串**。像 `config_drop.luac` 这种把字段名放在
`TDUP` 表常量里的文件，其字段名（`mon_bid`、`first_p_sum`、…）
**不会**出现在 `proto.strings` 中，于是基于 `proto.strings` 的全局扫描
（如 `tools/find_luac_global.py`）会得出**假阴性**。

本工具递归遍历 `TableConst.array` 与 `TableConst.hash`，
把其中的字符串键与字符串值也纳入索引搜索空间。

【硬约束】只读 anzbao/jstm.apk（1.4.9）。绝不读取 jstm_142165.apk。

用法：
    python tools/scan_luac_strings_deep.py <字符串> [<字符串> ...]
    python tools/scan_luac_strings_deep.py --all-multi <名1> <名2> ...   # 同一 proto 同时含全部名
    python tools/scan_luac_strings_deep.py --stats                       # 统计
"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import ChildRef, TableConst, parse_bytes  # noqa: E402

APK = os.path.join(os.path.dirname(HERE), 'anzbao', 'jstm.apk')
BANNED = ('142165', 'dldlJl')


def deep_strings(tc, out, depth=0):
    """递归收集 TableConst 内的字符串（键与值）。"""
    if depth > 6:
        return
    for v in (tc.array or []):
        if isinstance(v, str):
            out.add(v)
        elif isinstance(v, TableConst):
            deep_strings(v, out, depth + 1)
    for k, v in (tc.hash or []):
        if isinstance(k, str):
            out.add(k)
        if isinstance(v, str):
            out.add(v)
        elif isinstance(v, TableConst):
            deep_strings(v, out, depth + 1)


def proto_strings_deep(pt):
    out = set(pt.strings)
    for t in pt.tables:
        deep_strings(t, out)
    return out


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0] == '--stats':
        z = zipfile.ZipFile(APK)
        n = 0
        tot = 0
        for name in z.namelist():
            if not name.endswith('.luac'):
                continue
            if any(b in name for b in BANNED):
                continue
            try:
                r = parse_bytes(z.read(name))
            except Exception:
                continue
            n += 1
            for pt in r.protos:
                tot += len(proto_strings_deep(pt))
        print('扫描 .luac 文件 %d 个，深字符串常量总计 %d' % (n, tot))
        return

    mode_all = args[0] == '--all-multi'
    if mode_all:
        args = args[1:]
    want = set(args)
    z = zipfile.ZipFile(APK)
    hits = {}
    for name in sorted(z.namelist()):
        if not name.endswith('.luac'):
            continue
        if any(b in name for b in BANNED):
            continue
        try:
            r = parse_bytes(z.read(name))
        except Exception:
            continue
        for i, pt in enumerate(r.protos):
            ss = proto_strings_deep(pt)
            if mode_all:
                if want <= ss:
                    hits.setdefault('ALL', []).append((name, i, sorted(want)))
            else:
                got = want & ss
                if got:
                    hits.setdefault(name, []).append((i, sorted(got)))
    if mode_all:
        print('=== 同时包含 %s 的 proto：%d 个 ===' % (sorted(want),
                                                  len(hits.get('ALL', []))))
        for name, i, got in hits.get('ALL', []):
            print('   %-58s proto#%-4d' % (name, i))
        return
    print('=== 命中文件 %d 个 ===' % len(hits))
    for name in sorted(hits):
        for i, got in hits[name]:
            print('   %-58s proto#%-4d %s' % (name, i, got))


if __name__ == '__main__':
    main()
