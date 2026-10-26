"""从 `config_promote.luac`（`Config.Promote`）抽取服务端可用的提升项目录表。

产物：`server/_promote.json`
  {"items": [{"key":.., "mulu":.., "mulu_name":.., "display_lev":.., "open_lev":..,
              "priority":.., "recommend":.., "button_name":.., "link_id":..,
              "icon_res":.., "is_finish":.., "content":.., ...}, ...]}

数据来源：APK `assets/src/config/config_promote.luac`（**唯一真源**，不编造）。
"""
import os
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from luajit_bc import Reader  # noqa: E402

SRC = os.path.join('_tmp_cfg', 'config_promote.luac')
OUT = os.path.join('server', '_promote.json')

data = open(SRC, 'rb').read()
r = Reader(data)
r.parse()

rows = []
for pi, pt in enumerate(r.protos):
    for t in (pt.tables or []):
        h = getattr(t, 'hash', None)
        if not h:
            continue
        d = {}
        for kv in h:
            try:
                k, v = kv
            except Exception:
                continue
            if isinstance(k, (str, int, float, bool)) or k is None:
                if isinstance(v, (str, int, float, bool)) or v is None:
                    d[k] = v
        if d:
            d['_proto'] = pi
            rows.append(d)

print('原始 TableConst 条数 =', len(rows))
# 只保留"像 Promote 条目"的：含 mulu 或 display_lev 或 priority
items = [x for x in rows if ('mulu' in x or 'display_lev' in x or 'priority' in x)]
print('Promote 条目 =', len(items))
if items:
    print('首条示例：', json.dumps(items[0], ensure_ascii=False)[:400])
    ids = sorted(set(int(x.get('mulu')) for x in items if isinstance(x.get('mulu'), (int, float))))
    print('mulu 取值集合 =', ids[:40], '…共', len(ids))
    dl = sorted(set(int(x.get('display_lev')) for x in items if isinstance(x.get('display_lev'), (int, float))))
    print('display_lev 取值 =', dl[:25])

# ★ 决定性的一层：`SC_20100.promote` 的 `code` 指向客户端 `Config.Promote` 的**第一个子表**
#   （字段 way / recommend / display_lev / button_id / icon / link / is_hide）。
#   依据：advance_new_panel.luac proto#17 读 `Config.Promote[one.code].display_lev`，
#         且该 proto 只用这些字段；构造器里这一子表的键是 TSETB D=257,258,259,…
#         连续序列 ⇒ 键 = 1,2,3,…（顺序即字节码中出现顺序）。
#   ★ 注意：`pt.tables` 的遍历顺序与字节码中的 TDUP 顺序**相反**（实测：反向排列后
#     与 dump 中 TDUP 的先后完全一致）⇒ 这里 reverse 一次再编号。
tips = list(reversed([x for x in items if 'way' in x and 'recommend' in x and 'display_lev' in x]))
print('第一子表（提升方式/推荐）条数 =', len(tips))
for i, x in enumerate(tips[:6], 1):
    print('   code=%-3d display_lev=%-4s way=%-10s recommend=%s'
          % (i, x.get('display_lev'), x.get('way'), str(x.get('recommend'))[:36]))
for i, x in enumerate(tips, 1):
    x['code'] = i

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'items': items, 'tips': tips,
               'source': 'assets/src/config/config_promote.luac'},
              f, ensure_ascii=False, indent=1)
print('写出 ->', OUT, os.path.getsize(OUT), 'bytes')
