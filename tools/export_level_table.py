"""导出 1.4.9 角色等级表（`Config.RoleAttr`）为服务端可直接用的精简 JSON。

## 数据来源（1.4.9 APK，唯一）

    assets/src/config/config_role_attr.luac  ->  Config.RoleAttr

提取链路（全部可复现）：

    python tools/apk_extract_luac.py "assets/src/config/config_role_attr.luac" \
        "analysis/1.4.9/level/_config_role_attr.luac"
    python tools/dump_drop_config.py analysis/1.4.9/level/_config_role_attr.luac \
        --json analysis/1.4.9/level/_role_attr_raw.json
    python tools/export_level_table.py          # 本脚本

## 已确认的事实

- `Config.RoleAttr` 有 **200** 个键（1..200）⇒ **等级上限 200**
- 每个等级 5 个字段（全表统一）：
    exp_total   累计经验（升到该级所需的累计值）
    exp_max     本级经验需求
    attr_point  属性点（**全表为 0**）
    sinew_add   筋脉加成
    sinew_max   筋脉上限（**全表 120**）
- **不含** atk / hp / def 等战斗属性 ⇒ 逐级属性成长**不在客户端配置里**

## 客户端怎么用它（决定服务端必须怎么对齐）

`game/main/main_ui.luac` proto#16 bc#0-5：

    local cfg = Config.RoleAttr[self.role.lev + 1]      -- ★ 注意 +1
    ...  self.expPos = role.exp / cfg.exp_max * self.expFull

⇒ 处于 **L 级**时，经验条分母 = `RoleAttr[L+1].exp_max`
⇒ 服务端升级阈值必须用**同一个值**，否则经验条与服务端判定会不一致。

## 用法

    python tools/export_level_table.py
    python tools/export_level_table.py --check      # 只做一致性自检
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'analysis', '1.4.9', 'level', '_role_attr_raw.json')
OUT = os.path.join(ROOT, 'analysis', '1.4.9', 'level', 'level_table.json')


def main():
    if not os.path.exists(SRC):
        print('!! 缺少 %s，请先按脚本头注的链路提取' % SRC)
        return 1
    raw = json.load(open(SRC, encoding='utf-8'))['Config']['RoleAttr']
    rows = {}
    for k, v in raw.items():
        try:
            lv = int(k)
        except Exception:
            continue
        rows[lv] = {
            'exp_max': int(v.get('exp_max') or 0),
            'exp_total': int(v.get('exp_total') or 0),
            'attr_point': int(v.get('attr_point') or 0),
            'sinew_add': int(v.get('sinew_add') or 0),
            'sinew_max': int(v.get('sinew_max') or 0),
        }

    levels = sorted(rows)
    max_lev = max(levels)
    print('Config.RoleAttr: %d 个等级，范围 %d..%d' % (len(rows), min(levels), max_lev))

    # --- 自检 ---
    errs = []
    # ① 键必须连续 1..max
    if levels != list(range(1, max_lev + 1)):
        miss = [l for l in range(1, max_lev + 1) if l not in rows]
        errs.append('等级键不连续，缺: %s' % miss[:10])
    # ② 单调不减
    em = [rows[l]['exp_max'] for l in levels]
    et = [rows[l]['exp_total'] for l in levels]
    if any(em[i] > em[i + 1] for i in range(len(em) - 1)):
        errs.append('exp_max 非单调不减')
    if any(et[i] > et[i + 1] for i in range(len(et) - 1)):
        errs.append('exp_total 非单调不减')
    # ③ exp_total[L] == exp_total[L-1] + exp_max[L]
    bad = [L for L in levels if L > 1
           and rows[L]['exp_total'] != rows[L - 1]['exp_total'] + rows[L]['exp_max']]
    if bad:
        errs.append('exp_total 递推不成立的等级: %s' % bad)

    print('\n--- 自检 ---')
    print('  键连续          : %s' % ('OK' if levels == list(range(1, max_lev + 1)) else 'FAIL'))
    print('  exp_max 单调    : %s' % ('OK' if not any(em[i] > em[i+1] for i in range(len(em)-1)) else 'FAIL'))
    print('  exp_total 单调  : %s' % ('OK' if not any(et[i] > et[i+1] for i in range(len(et)-1)) else 'FAIL'))
    if bad:
        for L in bad:
            print('  ★ 异常 Lv%-4d exp_total=%-12d 应为 %d (= %d + %d)'
                  % (L, rows[L]['exp_total'],
                     rows[L - 1]['exp_total'] + rows[L]['exp_max'],
                     rows[L - 1]['exp_total'], rows[L]['exp_max']))
        print('    ⇒ 原版数据本身的不一致（**如实保留，不修正**）')
    else:
        print('  exp_total 递推  : OK')

    if '--check' in sys.argv:
        return 1 if errs and 'exp_total 递推不成立的等级' in errs[0] else 0

    data = {
        '_source': 'assets/src/config/config_role_attr.luac (1.4.9 Config.RoleAttr)',
        '_note': ('服务端升级阈值 = levels[lev+1].exp_max（与客户端 '
                  'main_ui.luac proto#16 的 Config.RoleAttr[lev+1].exp_max 对齐）；'
                  '本表**不含** atk/hp/def，逐级属性成长不在 APK 内'),
        'max_lev': max_lev,
        'levels': {str(l): rows[l] for l in levels},
    }
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n已写出 %s' % OUT)
    print('  前 5 级 exp_max : %s' % [rows[l]['exp_max'] for l in levels[:5]])
    print('  末 3 级 exp_max : %s' % [rows[l]['exp_max'] for l in levels[-3:]])
    return 0


if __name__ == '__main__':
    sys.exit(main())
