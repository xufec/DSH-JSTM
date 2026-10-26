"""提取 1.4.9 里**真正的物品表** `Config.Item`（`config_item.luac` proto#1）。

## 背景（为什么值得单独做一个工具）

`tools/extract_config_mon.py` 能提 `Config.Mon`，是因为 `config_mon_data.luac` 的
proto#0 就是「巨型 if 链 + 表常量」。`config_item.luac` 的结构**不同**：

    proto#0  bc=91      -> 只是 32 个字段名（物品 schema）
    proto#1  bc=65483   -> kgc=10537（其中 10455 个表常量）、knum=1117  -> ★ 数据在这

所以只要取 proto#1 的 `knum`（物品 bid）与配套的表常量，即可还原物品表。

## 关键用途

验证 `Config.Drop` / `Config.DropItem` 里那批 `51000`–`51066` 的物品
**是否存在于本作真实物品表** —— 
- 若**不存在** ⇒ 掉落表确实是**模板残留/死数据**，不能当原版掉落用；
- 若存在 ⇒ 需要重新评估。

用法：
    python tools/extract_config_item.py                 # 摘要 + 号段分布
    python tools/extract_config_item.py --json out.json # 全量导出
    python tools/extract_config_item.py --has 51037 51038 35021
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import TableConst, parse_bytes  # noqa: E402
from luajit_dis import kidx  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')


def main():
    argv = sys.argv[1:]
    want_json = None
    if '--json' in argv:
        k = argv.index('--json')
        want_json = argv[k + 1]
        argv = argv[:k] + argv[k + 2:]
    probe = []
    if '--has' in argv:
        k = argv.index('--has')
        probe = argv[k + 1:]
        argv = argv[:k]

    import zipfile
    z = zipfile.ZipFile(APK)
    r = parse_bytes(z.read('assets/src/config/config_item.luac'))
    pt = r.protos[1]

    n = len(pt.knum)
    items = {}
    for d in range(n):
        bid = pt.knum[n - 1 - d]
        try:
            bid = int(bid)
        except Exception:
            continue
        t = kidx(pt, d)
        arr = None
        if isinstance(t, TableConst):
            arr = list(t.array or [])
        items[bid] = arr

    print('Config.Item 条目: %d 条（proto#1, knum=%d）' % (len(items), n))
    if items:
        ks = sorted(items)
        print('  bid 范围: %d .. %d' % (ks[0], ks[-1]))
        # 号段分布（按 1000 分桶）
        from collections import Counter
        buckets = Counter(b // 1000 * 1000 for b in ks)
        print('  号段分布（前 20）：')
        for b in sorted(buckets)[:20]:
            print('     %6d–%6d : %d' % (b, b + 999, buckets[b]))
        # 有内容的条目
        witharr = sum(1 for v in items.values() if v)
        print('  带表内容的条目: %d / %d' % (witharr, len(items)))
        # 样例
        print('  样例（有内容的前 3 条）：')
        shown = 0
        for b in ks:
            if items[b] and shown < 3:
                print('     %d -> %r' % (b, items[b][:12]))
                shown += 1

    if probe:
        print('\n--has 查询：')
        for p in probe:
            try:
                p = int(p)
            except Exception:
                continue
            print('   %-6d %s' % (p, '在表内 ✅' if p in items else '**不在表内** ❌'))

    if want_json:
        json.dump({str(k): v for k, v in items.items()},
                  open(want_json, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('\n已写出 %s（%d 条）' % (want_json, len(items)))


if __name__ == '__main__':
    main()
