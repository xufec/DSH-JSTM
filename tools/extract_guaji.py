#!/usr/bin/env python3
"""抽取 `config_guaji`（挂机刷怪点）→ `server/_guaji.json`。

## 为什么有用（R48 / A 路取证）

挂机（AFK）是我们**尚未实现**的玩法，而它是「学院任务 / 监察任务」这两条
成就线（`trigger_fun: hongchen / zhuoyao`，实为客户端 `GhostMon` 实例名）
**真正的进度来源**。

`config_guaji` 给出了挂机点：

```
{mon_bid: 10101, disc: '星斗大森林', lev_l: 25, map_bid: 10002, lev_r: 34}
{mon_bid: 10102, disc: '明月森林',   lev_l: 35, map_bid: 10007, lev_r: 44}
…
```

| 字段 | 含义 |
|---|---|
| `mon_bid` | 该挂机点刷的**怪**（对应 `config_mon`） |
| `map_bid` | 挂机**地图/场景** id |
| `disc`   | 地名 |
| `lev_l` / `lev_r` | 适用等级段 |

★ 结论：这张表是 **挂机地图↔怪**，**不含** mission/daily 归属
⇒ 「挂机线 ↔ 任务」的映射**仍未被任何配置表达**。

用法：python tools/extract_guaji.py [--print]
"""
import argparse
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import TableConst, parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')
INSIDE = 'assets/src/config/config_guaji.luac'
OUT = os.path.join(ROOT, 'server', '_guaji.json')
FIELDS = ('mon_bid', 'map_bid', 'disc', 'lev_l', 'lev_r')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', dest='do_print', action='store_true')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()

    r = parse_bytes(zipfile.ZipFile(APK).read(INSIDE))
    spots = []
    for p in r.protos:
        for w in p.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            v = kidx(p, (w >> 16) & 0xffff)
            if not isinstance(v, TableConst) or not v.hash:
                continue
            h = {str(k): vv for k, vv in v.hash}
            if 'mon_bid' not in h or 'map_bid' not in h:
                continue
            spots.append({f: (h.get(f) if isinstance(h.get(f), str)
                              else int(h.get(f) or 0)) for f in FIELDS})
    spots.sort(key=lambda x: int(x['lev_l'] or 0))
    print('挂机点 %d 个' % len(spots))
    if args.do_print:
        print('%-10s %-10s %-6s %-6s %s' % ('mon_bid', 'map_bid', 'lev_l', 'lev_r', 'disc'))
        for s in spots:
            print('%-10s %-10s %-6s %-6s %s'
                  % (s['mon_bid'], s['map_bid'], s['lev_l'], s['lev_r'], s['disc']))
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({'spots': spots}, f, ensure_ascii=False, indent=1)
    print('已写出 %s' % args.out)


if __name__ == '__main__':
    main()
