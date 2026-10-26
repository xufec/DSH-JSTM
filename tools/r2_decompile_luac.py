#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 `luajit-decompiler-v2` 批量反编译 APK 内的 LuaJIT 字节码。

## 背景（**更正 R1.3 的一条结论**）
R1.3 步骤 ④ 曾判定"无可用的 LuaJIT 反编译器（unluac 只支持标准 Lua 5.1），
故以函数级调用图替代"。**该结论错误** —— 仓库 `tools/luajit-decompiler-v2-master.zip`
就是一个可用的 LuaJIT 反编译器（C++，Windows API），本脚本配套的构建已产出
`tools/luajit-decompiler-v2-build/LuajitDecompiler.exe`。
实测：`mission_ctrl.luac`(39.9 KB) → **52.8 KB 可读 Lua 源码，用时 0.042 秒**。
⇒ 本脚本把它用于**全量反编译**，产出可读源码供 Agent 检索。

## 用法
  python tools/r2_decompile_luac.py --version 1.4.11                # 全量 game/**/*.luac
  python tools/r2_decompile_luac.py --version 1.4.11 --filter mission
  python tools/r2_decompile_luac.py --version 1.4.11 --all-luac     # 含 config/ 等

## 产物
  analysis/luajit_src/<version>/<APK 内相对路径>.lua
  analysis/luajit_src/<version>/_decompile_report.json

纪律：**不修改 APK**；只把字节码读出到临时目录再反编译；原始字节码不落盘丢弃。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'tools', 'luajit-decompiler-v2-build', 'LuajitDecompiler.exe')
OUTROOT = os.path.join(ROOT, 'analysis', 'luajit_src')

APKS = {'1.3.0': r'anzbao\dldlJl.apk',
        '1.4.9': r'anzbao\jstm.apk',
        '1.4.11': r'anzbao\jstm_142165.apk'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', required=True, choices=list(APKS))
    ap.add_argument('--filter', default='assets/src/game/',
                    help='只处理路径含该子串的 luac（默认 game/）')
    ap.add_argument('--all-luac', action='store_true', help='处理 APK 内全部 .luac')
    ap.add_argument('--keep-bytecode', action='store_true',
                    help='保留反编译前的 .luac 到 _bytecode/（默认不保留）')
    args = ap.parse_args()

    if not os.path.exists(EXE):
        print('!! 缺 %s（先构建，见 tools/luajit-decompiler-v2-build/）' % EXE)
        return 1

    apk = os.path.join(ROOT, APKS[args.version])
    outdir = os.path.join(OUTROOT, args.version)
    os.makedirs(outdir, exist_ok=True)
    work = tempfile.mkdtemp(prefix='r2lj_')
    try:
        z = zipfile.ZipFile(apk)
        names = [n for n in z.namelist() if n.endswith('.luac')]
        if not args.all_luac:
            names = [n for n in names if args.filter in n]
        print('版本 %s ｜ APK %s ｜ 待反编译 %d 个 luac' % (args.version, APKS[args.version], len(names)))

        extracted = 0
        for n in names:
            rel = n.replace('/', os.sep)
            dst = os.path.join(work, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with z.open(n) as f, open(dst, 'wb') as o:
                shutil.copyfileobj(f, o)
            extracted += 1
        z.close()
        print('已提取 %d 个到临时目录' % extracted)

        t0 = time.time()
        r = subprocess.run([EXE, work + os.sep, '-o', outdir + os.sep],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=7200)
        dt = time.time() - t0
        print('反编译输出（前 15 行）:\n%s' % (r.stdout or '')[:1500])
        if r.stderr:
            print('stderr（前 5 行）: %s' % r.stderr[:500])

        produced, failed = [], []
        for n in names:
            # ★ 实测输出布局：**完整镜像 APK 内相对路径**（含 assets/src/），只把 .luac 换成 .lua。
            #   初版多剥了一层 `assets/src/` ⇒ 全部误判为"失败"（其实 14/14 都成功了）。
            cand = os.path.join(outdir, os.path.splitext(n)[0] + '.lua')
            hit = cand if os.path.exists(cand) else None
            (produced if hit else failed).append({'luac': n, 'lua': hit})

        rep = {
            'version': args.version, 'apk': APKS[args.version],
            'decompiler': 'tools/luajit-decompiler-v2-build/LuajitDecompiler.exe',
            'command': '%s <tmpdir> -o %s' % (os.path.basename(EXE), outdir),
            'elapsed_sec': round(dt, 2),
            'luac_selected': len(names), 'extracted': extracted,
            'decompiled_ok': len(produced), 'failed': len(failed),
            'success_rate': round(len(produced) / len(names), 4) if names else 0,
            'failed_list': failed[:200],
            'returncode': r.returncode,
            'stdout_tail': (r.stdout or '')[-3000:],
        }
        if args.keep_bytecode:
            bk = os.path.join(outdir, '_bytecode')
            if os.path.exists(bk):
                shutil.rmtree(bk)
            shutil.copytree(work, bk)
        with open(os.path.join(outdir, '_decompile_report.json'), 'w', encoding='utf-8') as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
        print('\n成功 %d / 失败 %d ｜ 用时 %.1fs ｜ 成功率 %.1f%%'
              % (len(produced), len(failed), dt,
                 100.0 * len(produced) / len(names) if names else 0))
        print('写出: analysis/luajit_src/%s/（%d 个 .lua）+ _decompile_report.json'
              % (args.version, len(produced)))
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
