"""C5-A1：为 `kill_type_mon` 找「怪物类型字段」证据。

思路（不猜、只用可验证的对应关系）：
  1. 从 mission_config.json 抽出**全部** `kill_type_mon` 条件，得到实际使用的类型码集合。
  2. 对 config_mon.json 的 `fields` 做**逐下标值域统计**。
  3. 找哪些下标的值域**能容纳全部类型码**（候选判别字段），并看它们的分布是否像"类型"。
  4. 交叉核对：`fight_mon` / `kill_scene_mon` 用的是**具体怪 bid**，可作对照锚点。

输出：候选下标 + 每个候选在"已知任务怪"上的取值，供人工判定。
"""
import json
import os
import sys
import io
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MON = os.path.join(ROOT, 'analysis', '1.4.9', 'task', 'config_mon.json')
MIS = os.path.join(ROOT, 'server', 'mission_config.json')


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def progress_of(m):
    p = m.get('progress')
    return p if isinstance(p, list) else []


def main():
    mons = load(MON)
    mis = load(MIS)
    if isinstance(mis, dict):
        rows = list(mis.values())
    else:
        rows = mis
    print('mon 条数=%d  mission 条数=%d' % (len(mons), len(rows)))

    # ── 1) 收集各类条件的参数 ──
    kinds = defaultdict(list)
    for m in rows:
        for el in progress_of(m):
            if isinstance(el, (list, tuple)) and len(el) >= 2:
                kinds[str(el[0])].append(tuple(el))

    print('\n=== 条件 kind 计数（前 20）===')
    for k, v in sorted(kinds.items(), key=lambda kv: -len(kv[1]))[:20]:
        print('  %-22s %d' % (k, len(v)))

    ktm = kinds.get('kill_type_mon') or []
    print('\n=== kill_type_mon 全部 %d 条 ===' % len(ktm))
    codes = Counter()
    for e in ktm:
        print('   ', e)
        codes[e[1]] += 1
    print('  用到的类型码:', dict(codes))

    # ── 2) fields 逐下标值域 ──
    nfield = max(len(v.get('fields') or []) for v in mons.values())
    print('\n=== fields 逐下标值域（下标: 不同值数 | 样例值）===')
    doms = {}
    for i in range(nfield):
        vals = Counter()
        for v in mons.values():
            f = v.get('fields') or []
            if i < len(f):
                vals[repr(f[i])] += 1
        doms[i] = vals
        sample = ', '.join('%s×%d' % (k, c) for k, c in vals.most_common(6))
        print('  [%2d] %4d 种 | %s' % (i, len(vals), sample[:130]))

    # ── 3) 哪些下标能容纳全部 kill_type_mon 类型码 ──
    print('\n=== 候选：值域包含全部 kill_type_mon 类型码的 fields 下标 ===')
    want = set(codes)
    for i in range(nfield):
        numeric = set()
        for k in doms[i]:
            try:
                numeric.add(int(k))
            except Exception:
                pass
        if want and want <= numeric:
            used = {int(k): c for k, c in doms[i].items() if _int(k) is not None}
            print('  ★ 下标 [%d] 容纳全部类型码 %s；该下标共 %d 种取值'
                  % (i, sorted(want), len(numeric)))
            for code in sorted(want):
                same = [v['bid'] for v in mons.values()
                        if (v.get('fields') or [None] * nfield)[i] == code]
                print('      类型码 %-4s ⇒ %d 只怪，样例 %s'
                      % (code, len(same), same[:8]))

    # ── 4) 对照：fight_mon 用的是具体 bid，看那些怪在各下标的取值 ──
    fm = kinds.get('fight_mon') or []
    fm_bids = sorted({e[1] for e in fm})
    print('\n=== 对照：fight_mon 目标怪 bid=%s ===' % fm_bids)
    for b in fm_bids:
        v = mons.get(str(b))
        if v:
            print('  %-7s fields=%s' % (b, v.get('fields')))

    ksm = kinds.get('kill_scene_mon') or []
    ksm_bids = sorted({e[1] for e in ksm})
    print('\n=== 对照：kill_scene_mon 目标怪 bid=%s ===' % ksm_bids[:10])
    for b in ksm_bids[:10]:
        v = mons.get(str(b))
        if v:
            print('  %-7s fields=%s' % (b, v.get('fields')))

    # ── 5) 用任务的 lun/区别，看候选下标能否把 fight_mon 与 kill_type_mon 分开 ──
    print('\n=== 候选下标在全部 2645 条怪上的分布（找出像"类型"的）===')
    for i in range(nfield):
        ints = [int(k) for k in doms[i] if _int(k) is not None]
        if not ints:
            continue
        if min(ints) >= 0 and max(ints) <= 30 and len(ints) <= 25:
            print('  下标 [%2d]: 取值 %s' % (i, sorted(ints)))


def _int(x):
    try:
        return int(x)
    except Exception:
        return None


if __name__ == '__main__':
    main()
