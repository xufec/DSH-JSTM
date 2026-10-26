# -*- coding: utf-8 -*-
"""★★★ **全量回归跑手** —— 一条命令跑完"回归项"，并**自动快照/复原**本服状态。

为什么需要它：
  · 项目纪律要求"**每批都要跑回归且全 PASS**"，但回归项散在 `tools/verify_*.py`
    与 `tools/test_*.py` 里，**没有统一的跑手**（此前是人工一条条跑）。
  · 多数验证脚本**会改 DB/配置**（发道具、改等级、写资产）⇒ 必须**先快照、跑完复原**，
    否则回归本身会污染现场（R166 就踩过：名字被改成单字 '测'）。

判据（每条）：
  · **退出码 0**（`sys.exit` 非 0 = FAIL）
  · 且 stdout/stderr **不含** `FAIL` / `✗` / `Traceback`
  · 且**不超时**（默认 120s）

用法：
  python tools/regress_all.py                # 跑全部（排除名单见 EXCLUDE）
  python tools/regress_all.py --only rank    # 只跑文件名含 rank 的
  python tools/regress_all.py --list         # 只列清单
  python tools/regress_all.py --keep         # 跑完**不**复原（调试用，慎用）
"""
import argparse
import io
import os
import shutil
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

# ★ 需要**真机 / APK 重打包 / 交互**的脚本：本机无法跑（与"命令实现"无关）⇒ 排除并说明理由
EXCLUDE = {
    # 需要连真机 / 重打包 APK
    'verify_patched_apks.py': '需要真机 + 重打包产物',
    'verify_injected_lua.py': '需要真机注入',
    'verify_mission_hook.py': '需要真机 hook',
    # 需要真机 1234 端口
    'test_11215_10800.py': '需要真机流量回放',
    # 会长时间占用的稳定性脚本（另有 run_stability_5.ps1）
    'verify_guaji.py': '需要先跑挂机链（有副作用，单独跑）',
}

# ★ R243：这两个要求**第二个服务实例**（9099）——`--second` 时自动拉起并跑它们
SECOND_PORT = 9099
SECOND_HTTP = 8099
NEEDS_SECOND = {
    'test_aoi_wire.py': ['%d' % SECOND_PORT],
    'test_map_collision.py': ['%d' % SECOND_PORT, '10001'],
}


def snapshot():
    """★ 快照 DB 与配置（回归会改它们）。"""
    out = {}
    for rel in ('server/state/roles.db', 'server/config.json'):
        p = os.path.join(ROOT, rel.replace('/', os.sep))
        if os.path.exists(p):
            b = p + '.regress_bak'
            shutil.copy2(p, b)
            out[p] = b
    return out


def restore(snap):
    for p, b in snap.items():
        if os.path.exists(b):
            shutil.copy2(b, p)
            os.remove(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--keep', action='store_true')
    ap.add_argument('--timeout', type=int, default=120)
    ap.add_argument('--second', action='store_true',
                    help='额外拉起 9099/8099 实例，连 aoi/碰撞 两条也跑')
    a = ap.parse_args()

    names = []
    for pre in ('verify_', 'test_'):
        for n in sorted(os.listdir(HERE)):
            if n.startswith(pre) and n.endswith('.py'):
                names.append(n)
    if a.only:
        names = [n for n in names if a.only.lower() in n.lower()]
    todo = [n for n in names if n not in EXCLUDE]
    skipped = [n for n in names if n in EXCLUDE]
    if a.second:
        todo = [n for n in names if n not in EXCLUDE or n in NEEDS_SECOND]

    print('  ★ 回归项 %d ｜ 跳过 %d（需真机/有副作用）' % (len(todo), len(skipped)))
    for n in skipped:
        print('      - %-28s %s' % (n, EXCLUDE[n]))
    if a.list:
        return 0

    snap = snapshot()
    srv2 = None
    if a.second:
        print('  ★ 拉起第二实例：--http %d --game %d' % (SECOND_HTTP, SECOND_PORT))
        srv2 = subprocess.Popen([PY, os.path.join(ROOT, 'server', 'mock_server.py'),
                                 '--http', str(SECOND_HTTP), '--game', str(SECOND_PORT)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                cwd=ROOT)
        time.sleep(5)
    ok, bad = [], []
    t0 = time.time()
    try:
        for i, n in enumerate(todo, 1):
            t = time.time()
            args = [PY, os.path.join(HERE, n)] + NEEDS_SECOND.get(n, [])
            try:
                r = subprocess.run(args, capture_output=True,
                                   text=True, encoding='utf-8', errors='replace',
                                   timeout=a.timeout, cwd=ROOT)
                out = (r.stdout or '') + (r.stderr or '')
                rc = r.returncode
            except subprocess.TimeoutExpired:
                out, rc = '(超时)', -9
            dt = time.time() - t
            marks = [m for m in ('FAIL', '✗', 'Traceback') if m in out]
            good = (rc == 0) and not marks
            (ok if good else bad).append(n)
            print('  [%2d/%2d] %-6s %-30s %5.1fs rc=%-3d %s'
                  % (i, len(todo), 'PASS' if good else 'FAIL', n, dt, rc,
                     '' if good else ('标记=%r ' % marks) +
                     [x for x in out.split('\n') if x.strip()][-1:][0][:90]
                     if out.strip() else ''))
    finally:
        if srv2 is not None:
            srv2.terminate()
            try:
                srv2.wait(timeout=10)
            except Exception:
                srv2.kill()
        if not a.keep:
            restore(snap)
    print('\n  ★ 回归：PASS %d ｜ FAIL %d ｜ 耗时 %.1fs'
          % (len(ok), len(bad), time.time() - t0))
    if bad:
        print('  ✗ 失败清单：%s' % ', '.join(bad))
    print('  === 结果: %s ===' % ('PASS' if not bad else 'FAIL'))
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
