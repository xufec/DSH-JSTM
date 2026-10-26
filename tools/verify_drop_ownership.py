"""独立复核：APK 内的掉落物品到底是不是《绝世唐门》自己的内容。

子代理提出「Config.Drop / DropItem 是模板残留，物品全来自仙剑/轩辕剑/古剑」。
本脚本**不依赖子代理的结论**，直接从 1.4.9 APK 本体取三组独立证据：

  ① 掉落物品的名字与 id 号段（逐条列出）
  ② APK 里是否存在这些 item 的资源文件（图标等）—— 若没有，说明游戏根本没用到
  ③ 对照组：《绝世唐门》自己的角色资源（H30xxx/R01xxx/...）在 APK 里的资源情况

用法：python tools/verify_drop_ownership.py
"""
import json
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')

from luajit_bc import parse_bytes  # noqa: E402


def main():
    z = zipfile.ZipFile(APK)
    names = z.namelist()

    # ---------- ① 掉落物品清单 ----------
    di = json.load(open(os.path.join(ROOT, 'analysis', '1.4.9', 'item',
                                     '_config_drop_item.json'), encoding='utf-8'))
    items = []
    for gid, pool in (di.get('Config', {}).get('DropItem') or {}).items():
        for _, it in (pool.get('item_list') or {}).items():
            items.append((int(it.get('item_bid') or 0), it.get('item_name') or ''))
    items = sorted(set(items))
    print('=== ① 掉落池里的全部物品（%d 个，去重）===' % len(items))
    for bid, nm in items:
        print('   %-6d %s' % (bid, nm))
    seg = sorted({b // 1000 * 1000 for b, _ in items})
    print('   号段: %s' % seg)

    # ---------- ② 这些物品有没有资源文件 ----------
    print('\n=== ② 这些 item id 在 APK 里有没有对应资源 ===')
    hits = 0
    for bid, nm in items[:12]:
        h = [n for n in names if str(bid) in n]
        if h:
            hits += 1
            print('   %-6d %-16s -> %s' % (bid, nm, h[:3]))
    print('   （前 12 个里命中 %d 个）' % hits)
    # 泛化：资源目录里有没有 item / goods 图标区
    icondirs = sorted({os.path.dirname(n) for n in names
                       if re.search(r'(?i)/(item|goods|prop|icon)s?/', n)})
    print('   资源里的 item/goods 类目录（前 12）：')
    for d in icondirs[:12]:
        print('      ', d)

    # ---------- ③ 对照组：唐门自己的角色资源 ----------
    print('\n=== ③ 对照：《绝世唐门》自己的怪物 res_id 在 APK 里有没有资源 ===')
    mon = json.load(open(os.path.join(ROOT, 'analysis', '1.4.9', 'task',
                                      'config_mon.json'), encoding='utf-8'))
    resids = sorted({v.get('res_id') for v in mon.values() if v.get('res_id')})
    print('   Config.Mon 的 res_id 样本: %s' % resids[:8])
    ok = 0
    for r in resids[:8]:
        h = [n for n in names if r in n]
        print('   %-8s -> %d 个资源 %s' % (r, len(h), h[:2]))
        if h:
            ok += 1
    print('   （前 8 个 res_id 里 %d 个在 APK 里有资源）' % ok)

    # ---------- ④ 包内有没有"唐门系"的物品名 ----------
    print('\n=== ④ 全包字符串里搜《绝世唐门》角色名 vs 仙剑系角色名 ===')
    want_tm = ['霍雨浩', '唐舞桐', '王冬', '戴浩', '宁天', '贝贝', '叶夕水', '唐门']
    want_other = ['李逍遥', '赵灵儿', '林月如', '酒剑仙', '龙葵', '南宫煌', '聂小倩']
    cnt = {w: 0 for w in want_tm + want_other}
    for n in names:
        if not n.endswith('.luac'):
            continue
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        for pt in r.protos:
            for s in pt.strings:
                if s in cnt:
                    cnt[s] += 1
    for w in want_tm:
        print('   唐门系 %-6s -> %d 个 .luac 出现' % (w, cnt[w]))
    for w in want_other:
        print('   他作系 %-6s -> %d 个 .luac 出现' % (w, cnt[w]))


if __name__ == '__main__':
    main()
