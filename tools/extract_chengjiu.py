#!/usr/bin/env python3
"""抽取 `config_chengjiu`（成就）→ `server/_chengjiu.json`。

## 背景（R48）

真机 `16400`（成就面板）发了 **450 次**，服务端原落在通用集合回**全零**。
成就与日常同属"能自然产生进度"的一类，且**配置齐全**：

```
{bid, name, desc, val(目标值), cent, group, type, type2,
 pre, post, title, show, open_lev, guider_id,
 trigger_mod, trigger_fun}      ← ★ 后两者是"进度由什么触发"的链接
```

例：`{bid:10101, name:'学院能手', desc:'完成20轮学院任务', val:20, group:10100,
      trigger_mod:'mission', trigger_fun:'hongchen'}`

用法：
    python tools/extract_chengjiu.py [--print]
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
INSIDE = 'assets/src/config/config_chengjiu.luac'
OUT = os.path.join(ROOT, 'server', '_chengjiu.json')

FIELDS = ('bid', 'name', 'desc', 'val', 'cent', 'group', 'type', 'type2',
          'pre', 'post', 'title', 'show', 'open_lev', 'guider_id',
          'trigger_mod', 'trigger_fun')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', dest='do_print', action='store_true')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()

    z = zipfile.ZipFile(APK)
    r = parse_bytes(z.read(INSIDE))

    items = {}
    for p in r.protos:
        for w in p.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            v = kidx(p, (w >> 16) & 0xffff)
            if not isinstance(v, TableConst) or not v.hash:
                continue
            h = {str(k): vv for k, vv in v.hash}
            if 'name' not in h or 'bid' not in h:
                continue
            bid = int(h.get('bid') or 0)
            rec = {}
            for f in FIELDS:
                if f in h:
                    vv = h[f]
                    rec[f] = int(vv) if isinstance(vv, (int, float)) else (vv or '')
            items[bid] = rec

    groups = {}
    for rec in items.values():
        groups.setdefault(int(rec.get('group') or 0), 0)
        groups[int(rec.get('group') or 0)] += 1

    print('成就条目 %d 条 ｜ 分组 %d 个' % (len(items), len(groups)))
    if args.do_print:
        print('\n%-8s %-10s %-6s %-6s %-12s %-10s %s'
              % ('bid', 'name', 'val', 'cent', 'trigger_mod', 'trigger_fun', 'desc'))
        for bid in sorted(items)[:20]:
            r2 = items[bid]
            print('%-8d %-10s %-6s %-6s %-12s %-10s %s'
                  % (bid, r2.get('name', ''), r2.get('val', ''), r2.get('cent', ''),
                     r2.get('trigger_mod', ''), r2.get('trigger_fun', ''),
                     (r2.get('desc') or '')[:24]))

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({'items': items}, f, ensure_ascii=False, indent=1)
    print('\n已写出 %s' % args.out)


if __name__ == '__main__':
    main()
