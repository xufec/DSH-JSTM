#!/usr/bin/env python3
"""校验已改包 APK 里注入到 config.luac 的 Lua 片段。

tools/patch_apk.py 会往明文的 assets/src/config.luac 末尾追加代码。实测的
文件内部位置（务必按这个顺序解析，否则会被同名注释骗到）：

    [原 config.luac]
    [观测器段]  .............. "-- ---- DSH url observer"
    [注入块头]  .............. "-- ===== injected by DSH private server ====="
        local __dsh_srv_src = [====[
    [内置服务端源码]
        ]====]
    [兜底包装]  .............. "-- ================= DSH embedded local server (fallback)"

这段追加代码一旦语法有错，整个 config chunk 编译失败、游戏静默卡住，
所以打包后必须能独立验证。校验分三段：服务端源码 / 观测器 / 胶水（剥掉长括号内容）。

usage:
  python tools/verify_injected_lua.py patched/jstm_solo.apk
"""
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHECK_JS = os.path.join(HERE, 'lua-check', 'check.js')
OUT_DIR = os.path.join(HERE, 'lua-check')

# 锚点必须**纯 ASCII**：注入块里带中文/符号注释（如 ⚠、←），经过编码转换
# 会变，只有 ASCII 片段可靠。
SERVER_BEGIN = 'local __dsh_srv_src = [====['
SERVER_END = ']====]'
OBSERVER_MARK = '---- DSH url observer'
FALLBACK_MARK = 'DSH_FALLBACK_BEGIN'
HEAD_MARK = 'injected by DSH private server'

SERVER_REQUIRED = [
    'M.PORT = ', 'M.HOST_IP = ', 'M.GAME_PORT = ',
    'function M.start()', 'function M.start_game()', 'function M.tick()',
    'M.install(0.05)',
]
OBSERVER_REQUIRED = ['cc.XMLHttpRequest']


def lua_check(label, src):
    path = os.path.join(OUT_DIR, '_injected_%s.lua' % re.sub(r'\W+', '_', label))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    r = subprocess.run(['node', CHECK_JS, path], capture_output=True,
                       encoding='utf-8', errors='replace')
    return r.returncode == 0, (r.stdout or r.stderr or '').strip()


def report(label, src, required, bad):
    ok, msg = lua_check(label, src)
    print('%-22s %s  (%d bytes)' % (label, 'OK' if ok else 'FAIL', len(src)))
    n = bad
    if not ok:
        n += 1
        print('   ', msg[:300])
    for needle in required:
        if needle not in src:
            print('    !! missing structure: %s' % needle)
            n += 1
    return n


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'patched', 'jstm_solo.apk')
    z = zipfile.ZipFile(apk)
    raw = z.read('assets/src/config.luac')
    # 整个文件已被 patch_apk.py 统一转成 UTF-8（含中文注释），
    # 这里必须按 UTF-8 解码才能可靠匹配 ASCII 标记。
    text = raw.decode('utf-8', errors='replace')

    print('config.luac: %d bytes' % len(raw))
    bad = 0

    # ---- 定位锚点（实测字符位置，别再假设顺序）----
    #   head(注入块头)=1712 < observer=35458 < fallback=36582
    #   < srv_begin=36821 < srv_end(=EOF)=61836
    #  也就是说：注入块头在最前，观测器接在其后，最后才是包着服务端源码的兜底包装。
    i = text.rfind(SERVER_BEGIN)
    j = text.find(SERVER_END, i + len(SERVER_BEGIN)) if i >= 0 else -1
    k = text.find(OBSERVER_MARK)
    h = text.find(HEAD_MARK)
    fb = text.find(FALLBACK_MARK)
    if min(i, j, k, h, fb) < 0:
        # ★ 联调版（--no-embedded）布局：没有内置服务端源码、也没有兜底包装，
        #   只有「注入块头 + 观测器段」。这种布局**同样必须过语法闸门**
        #   （注入块一旦语法错，config chunk 编译失败 → 游戏静默卡死），
        #   所以这里走一条等价的窄验证，而不是直接判失败。
        if h >= 0 and k >= 0 and h < k:
            h_line = text.rfind('\n', 0, h) + 1
            _need = [] if 'obs-only' in text else ['UPDATE_SKIP = true', 'URL_PATH = {']
            bad = report('inject head', text[h_line:k], _need, 0)
            bad = report('url observer', text[k:], OBSERVER_REQUIRED, bad)
            if 'obs-only' not in text and 'UPDATE_SKIP = true' not in text:
                print('    !! missing UPDATE_SKIP = true (版本检查旁路)')
                bad += 1
            print('  (no-embedded layout: 无内置服务端段，跳过 srv/fallback 断言)')
            print('RESULT:', 'PASS' if bad == 0 else 'FAIL (%d)' % bad)
            return 1 if bad else 0
        print('!! injected markers NOT FOUND -- patch did not run?')
        return 1
    if not (h < k < fb < i < j):
        print('!! anchor order unexpected: head=%d observer=%d fallback=%d srv=[%d,%d]'
              % (h, k, fb, i, j))
        return 1

    # ---- 1) 内置服务端源码（长括号内部） ----
    bad = report('builtin server', text[i + len(SERVER_BEGIN):j], SERVER_REQUIRED, bad)

    # ---- 2) 观测器段（注入块头之后、兜底包装之前） ----
    bad = report('url observer', text[k:fb], OBSERVER_REQUIRED, bad)

    # ---- 3) 胶水 = 注入块头 .. 观测器 + 兜底包装开头 + 长括号之后的收尾 ----
    #  中间三块都已被单独校验，这里只把"外壳"拼起来，确认它们合起来是一个完整 chunk。
    #  注意锚点 HEAD_MARK 落在注释行中间，必须回退到该行行首，
    #  否则切片以 "by DSH ..." 开头，解析器当然报错（踩过）。
    h_line = text.rfind('\n', 0, h) + 1
    glue_src = text[h_line:k] + text[fb:i] + text[j + len(SERVER_END):]
    bad = report('injection glue', glue_src, ['UPDATE_SKIP = true', 'URL_PATH = {'], bad)

    # ---- 4) 关键配置断言 ----
    #  注意：**不再**断言 IS_PLATFORM_LOGIN = false。
    #  实测结论（见 单机版内置服务端.md 第 13/14 轮）：
    #    main() 的判定是 `if (not IS_PLATFORM_LOGIN) or _is_game_restart then
    #    ver_load_start() end` —— 保留 true 反而让游戏走正规启动流程；
    #    把它改成 false 对启动推进没有帮助（真正缺的是 ver_load_start 的调用时机）。
    #  所以这里只做提示，不算失败。
    if 'UPDATE_SKIP = true' not in text:
        print('    !! missing UPDATE_SKIP = true (版本检查旁路)')
        bad += 1
    if 'IS_PLATFORM_LOGIN = true' not in text and 'IS_PLATFORM_LOGIN = false' not in text:
        print('    !! missing IS_PLATFORM_LOGIN (config.luac 被改坏了?)')
        bad += 1

    print('RESULT:', 'PASS' if bad == 0 else 'FAIL (%d)' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

