#!/usr/bin/env python3
"""C 路：后台统计真机发来的任务类命令（12403 提交 / 12401 接取 …）。

目的：玩家自己在做挂机时，把 `12403` 的 **bid** 与时间记下来 ——
一旦抓到，就能确定"哪个 bid 属于哪条挂机线"，往 `_chengjiu_map.json` 加一行即可。

用法：
    python tools/watch_mission_bids.py                 # 前台，Ctrl-C 停
    python tools/watch_mission_bids.py --minutes 120   # 自动跑 120 分钟
输出：`analysis/1.4.9/mission_bid_watch.log`（追加写，含去重计数）
"""
import argparse
import os
import re
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TCP = os.path.join(ROOT, 'server', 'logs', 'tcp.log')
OUT = os.path.join(ROOT, 'analysis', '1.4.9', 'mission_bid_watch.log')
WATCH = (12401, 12402, 12403, 12407, 12408, 12409, 12421, 12430, 12431, 12432)
# `>> cmd=12403 ? body(4)=00 00 27 1a` / `>> cmd=12403 ? body(8)=...`
RE = re.compile(r'\[(\d\d:\d\d:\d\d)\]\s+>> cmd=(\d+) \? body\((\d+)\)=((?:[0-9a-f]{2} )+[0-9a-f]{2})')


def note(msg):
    line = '[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg)
    with open(OUT, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--minutes', type=float, default=0, help='>0 则到点自动退出')
    args = ap.parse_args()

    if not os.path.exists(TCP):
        print('找不到 %s' % TCP)
        sys.exit(1)
    f = open(TCP, 'r', encoding='utf-8', errors='replace')
    f.seek(0, os.SEEK_END)
    note('=== 开始监听任务类命令（%s）===' % ', '.join(map(str, WATCH)))
    seen = {}
    end = time.time() + args.minutes * 60 if args.minutes > 0 else None
    while True:
        if end is not None and time.time() > end:
            note('=== 到点退出；本次统计：%s ===' % seen)
            break
        line = f.readline()
        if not line:
            time.sleep(0.4)
            continue
        m = RE.search(line)
        if not m:
            continue
        t, cmd, _n, hexs = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        if cmd not in WATCH:
            continue
        body = bytes.fromhex(hexs.replace(' ', ''))
        bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else None
        seen[bid] = seen.get(bid, 0) + 1
        note('cmd=%d bid=%s 次数=%d  body=%s' % (cmd, bid, seen[bid], hexs))


if __name__ == '__main__':
    main()
