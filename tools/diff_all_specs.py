#!/usr/bin/env python3
"""系统性跨版本字段 diff：找出"新版本字段更多 ⇒ 服务端按旧版编码会少发"的消息。

背景（R49）：1.4.11 的 `sc/10301` / `sc/10302` 比 1.4.9 **尾部多 1~2 个字段**，
服务端按 1.4.9 规格少发 ⇒ 新客户端**读越界** ⇒ 整条消息被丢弃 ⇒
角色数据空 ⇒ 功能 UI 全隐藏（静默、不报错）。修法是**下发版本并集**（尾部补 0）。

本脚本把这类问题**一次找全**：对两版共有的 (cmd, dir) 逐字段比较，
按"差异类型"分类输出，重点关注 **B 版多出的尾部字段**。

用法：
    python tools/diff_all_specs.py                # 1.4.9 vs 1.4.11
    python tools/diff_all_specs.py --b dldlJl.apk # 1.4.9 vs 1.3.0
"""
import argparse
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

A_APK = 'anzbao/jstm.apk'
B_APK = 'anzbao/jstm_142165.apk'


def all_specs(apk):
    z = zipfile.ZipFile(os.path.join(ROOT, apk))
    out = {}
    for n in z.namelist():
        if 'cmd_resolve_' not in n or not n.endswith('.luac'):
            continue
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        for p in r.protos:
            for sp, w in enumerate(p.bc):
                if OPS[w & 0xff] != 'TDUP':
                    continue
                v = kidx(p, (w >> 16) & 0xffff)
                if not (isinstance(v, TableConst) and v.array):
                    continue
                arr = [x for x in v.array if isinstance(x, str)]
                if not arr:
                    continue
                kind = cmd = None
                for j in range(max(0, sp - 16), sp):
                    o = OPS[p.bc[j] & 0xff]
                    d = (p.bc[j] >> 16) & 0xffff
                    if o == 'KSTR':
                        vv = kidx(p, d)
                        if vv in ('cs', 'sc'):
                            kind = vv
                    elif o == 'KSHORT':
                        cmd = d
                if kind and cmd is not None:
                    # ★ 注意：AutoConstruct 的字段串**可能被拆成多个常量**，
                    #   只取 arr[0] 会漏字段（第一版就这么错了，导致"0 条高风险"的假结论）。
                    out[(cmd, kind)] = [x.strip() for x in ' '.join(arr).split('|')]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--b', default=B_APK, help='对比用的 B 版本 apk（相对仓库根）')
    args = ap.parse_args()

    A = all_specs(A_APK)
    B = all_specs(args.b)
    print('A(1.4.9) 规格 %d 条 ｜ B(%s) 规格 %d 条' % (len(A), args.b, len(B)))

    under, over, other, same = [], [], [], 0
    for k in sorted(set(A) & set(B)):
        fa, fb = A[k], B[k]
        if fa == fb:
            same += 1
            continue
        # B 比 A 多，且 A 是 B 的前缀 ⇒ 服务端(A 版编码)会**少发尾部**
        if len(fb) > len(fa) and fb[:len(fa)] == fa:
            under.append((k, fa, fb))
        elif len(fa) > len(fb) and fa[:len(fb)] == fb:
            over.append((k, fa, fb))
        else:
            other.append((k, fa, fb))

    print('完全一致: %d' % same)
    print()
    print('★ 高风险（B 更多 ⇐ 服务端会少发尾部字段）: %d 条' % len(under))
    for k, fa, fb in under:
        extra = fb[len(fa):]
        print('  %s/%-6d A=%d 字段  B=%d 字段  多出: %s'
              % (k[1], k[0], len(fa), len(fb), extra))
    if over:
        print()
        print('（B 更少 ⇐ 服务端会多发尾部，通常无害）: %d 条' % len(over))
        for k, fa, fb in over[:12]:
            print('  %s/%-6d A=%d  B=%d  多出: %s' % (k[1], k[0], len(fa), len(fb), fa[len(fb):]))
    if other:
        print()
        print('（结构性不同，需要人工看）: %d 条' % len(other))
        for k, fa, fb in other[:20]:
            i = next((i for i in range(min(len(fa), len(fb))) if fa[i] != fb[i]), -1)
            print('  %s/%-6d A=%d B=%d  首个不同 @%d: %s vs %s'
                  % (k[1], k[0], len(fa), len(fb), i,
                     fa[i] if 0 <= i < len(fa) else '-', fb[i] if 0 <= i < len(fb) else '-'))


if __name__ == '__main__':
    main()
