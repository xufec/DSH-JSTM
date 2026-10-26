# -*- coding: utf-8 -*-
"""**批量解构**：把 APK 里所有 `config_*.luac` 解构成 JSON，落到 `server/cfg/`。

为什么：`tools/config_deconstruct.py`（R106–R109 做出来的对齐解构器）能处理
"具名嵌套配置"，而老提取器对这类输出 0 条。配置一旦可用，
`tools/cmd_unknown.py --by-system` 清单里那些"缺数据源"的系统就解锁了。

用法：
    python tools/batch_deconstruct.py            # 全部
    python tools/batch_deconstruct.py --only wing,tree,build,mingge
    python tools/batch_deconstruct.py --list     # 只列出会解哪些
"""
import argparse
import io
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')
OUTDIR = os.path.join(ROOT, 'server', 'cfg')
TMP = os.path.join(ROOT, '_tmp_cfg')

# ⚠ 先 import 再做 stdout 包装 —— `config_deconstruct` → `luajit_dis` 里
#   会 `sys.stdout.reconfigure(...)`，若这里先包一层，那边会对"已关闭的包装器"
#   再 reconfigure ⇒ `ValueError: I/O operation on closed file`（第一版就这么炸的）。
import config_deconstruct as cd  # noqa: E402
# ⚠ 这里**不能**再包一层 stdout —— \config_deconstruct\ 模块级已经包过了，
#   再包一层会让前一层被 gc 关闭 ⇒ \ValueError: I/O operation on closed file\。


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='只处理名字里含这些关键词的（逗号分隔）')
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()

    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    z = zipfile.ZipFile(APK)
    names = [n for n in z.namelist()
             if '/config/config_' in n and n.endswith('.luac')]
    if args.only:
        kws = [k.strip().lower() for k in args.only.split(',') if k.strip()]
        names = [n for n in names if any(k in n.lower() for k in kws)]
    if args.list:
        for n in names:
            print('  %-52s %d B' % (n.split('/')[-1], z.getinfo(n).file_size))
        print('共 %d 个' % len(names))
        return

    ok, empty, fail = [], [], []
    for n in sorted(names):
        base = n.split('/')[-1].replace('.luac', '')
        lp = os.path.join(TMP, base + '.luac')
        try:
            data = z.read(n)
            with open(lp, 'wb') as f:
                f.write(data)
            res = cd.deconstruct(lp)
            j = {k: cd.to_jsonable(v) for k, v in res.items()}
            # 顶层若非 Config 且只有一个键，取它的内容（配置都是 `Config = {...}`）
            cfg = j.get('Config', j) if isinstance(j, dict) else j
            n_top = len(cfg) if isinstance(cfg, (dict, list)) else 0
            outp = os.path.join(OUTDIR, base + '.json')
            with open(outp, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(cfg, f, ensure_ascii=False)
            (ok if n_top else empty).append((base, n_top, os.path.getsize(outp)))
        except Exception as e:
            fail.append((base, repr(e)[:60]))

    print('=== 解构成功且有顶层键：%d 个 ===' % len(ok))
    for b, n, sz in sorted(ok, key=lambda x: -x[1])[:24]:
        print('  %-34s %4d 键  %7.1f KB' % (b, n, sz / 1024))
    if len(ok) > 24:
        print('  …（其余 %d 个）' % (len(ok) - 24))
    print('\n=== 解出但为空：%d 个 ===' % len(empty))
    print('   ', ', '.join(b for b, _n, _s in empty[:14]))
    if fail:
        print('\n=== 失败：%d 个 ===' % len(fail))
        for b, e in fail[:8]:
            print('  %-34s %s' % (b, e))
    print('\n输出目录：%s' % OUTDIR)


if __name__ == '__main__':
    main()
