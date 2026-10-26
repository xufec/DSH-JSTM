#!/usr/bin/env python3
"""抽取 `config_richang`（日常/活跃度）→ `server/_richang.json`。

## 背景（R48）

真机点开「日常」面板会发 `13781`（活跃度）+ `13786`（周常/日常状态）。
MuMu 截图显示面板有 **6 个任务**（学院任务 / 监察任务 / 斗魂场 / 封神之路 /
宝图任务 / 极地寻宝）以及"拥有活力 0/1420"，但服务端当时回的是全零。

**关键发现**：服务端回 `huoli_list=0` 时客户端**仍显示完整任务列表**
⇒ 任务定义在客户端本地配置里 ⇒ 定位到 **`config_richang.luac`**。

该表里其实有**两类记录**（同名不同用途）：

| 类 | 代表字段 | 说明 |
|---|---|---|
| **口径类** | `{id, name, max_num, limit_lev, ord}` | 任务口径（id 即 `huoli_id`） |
| **面板类** | `{id:208, name, huoli_id:1, type_name:'日常任务', max_num:10, ord:1, ico, desc*}` | 面板显示条目，`max_num` 与截图上的「0/10、0/50」**完全吻合** |

`SC_13781.huoli_list` 的条目是 `{id:H, num:H, val:H}`
⇒ `id` 取 **`huoli_id`**（与面板类的 `huoli_id`、口径类的 `id` 三方一致）。

用法：
    python tools/extract_richang.py                # 写 server/_richang.json
    python tools/extract_richang.py --print        # 同时打印
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
INSIDE = 'assets/src/config/config_richang.luac'
OUT = os.path.join(ROOT, 'server', '_richang.json')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', dest='do_print', action='store_true')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()

    z = zipfile.ZipFile(APK)
    r = parse_bytes(z.read(INSIDE))

    kezhi, panel = {}, {}
    for p in r.protos:
        for w in p.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            v = kidx(p, (w >> 16) & 0xffff)
            if not isinstance(v, TableConst) or not v.hash:
                continue
            h = {str(k): vv for k, vv in v.hash}
            if 'name' not in h:
                continue
            if 'huoli_id' in h:                      # 面板类
                panel[int(h.get('id') or 0)] = {
                    'id': int(h.get('id') or 0),
                    'huoli_id': int(h.get('huoli_id') or 0),
                    'name': h.get('name') or '',
                    'type_name': h.get('type_name') or '',
                    'type': int(h.get('type') or 0),
                    'max_num': int(h.get('max_num') or 0),
                    'ord': int(h.get('ord') or 0),
                    'ico': int(h.get('ico') or 0),
                    'desc_cond': h.get('desc_cond') or '',
                    'desc_time': h.get('desc_time') or '',
                    'desc_more': h.get('desc_more') or '',
                    'cli_assets': h.get('cli_assets') or '',
                }
            elif 'limit_lev' in h:                   # 口径类
                kezhi[int(h.get('id') or 0)] = {
                    'huoli_id': int(h.get('id') or 0),
                    'name': h.get('name') or '',
                    'max_num': int(h.get('max_num') or 0),
                    'limit_lev': int(h.get('limit_lev') or 0),
                    'ord': int(h.get('ord') or 0),
                }

    tasks = sorted(panel.values(), key=lambda t: (t['ord'], t['id']))
    print('面板条目 %d 条 ｜ 口径条目 %d 条' % (len(tasks), len(kezhi)))
    if args.do_print:
        print('\n%-6s %-8s %-12s %-16s %-6s %s'
              % ('id', 'huoli_id', 'name', 'type_name', 'max', 'ord'))
        for t in tasks:
            print('%-6d %-8d %-12s %-16s %-6d %d'
                  % (t['id'], t['huoli_id'], t['name'], t['type_name'],
                     t['max_num'], t['ord']))

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({'tasks': tasks, 'kezhi': list(kezhi.values())},
                  f, ensure_ascii=False, indent=1)
    print('\n已写出 %s' % args.out)


if __name__ == '__main__':
    main()
