"""按等级缩放角色战斗属性（`role_attr` 表）。

## 证据说明（**必须先读**）

- **等级曲线**在客户端里有：`config_role_attr.luac` 的 `Config.RoleAttr[lev]`
  含 `{exp_total, exp_max, attr_point, sinew_add, sinew_max}`。
- **战斗属性（atk_s/def_s/hp_max/hit/dodge/crit/...）的"等级→数值"公式不在客户端 APK 里** ——
  已逐表查证：`config_role_career.luac` 只有模型/武器资源（name/res/res_2/weapon_res/height），
  `config_attr.luac` 只有属性元数据（key↔id↔中文名、战力权重、是否显示），
  **都没有基础属性成长表**。原版里这些值是**服务端算出来**再通过 `SC_10303` 下发的。

⇒ 因此本工具做的是**可复现的缩放（emulation）**，**不是**还原原版数值：

    新值 = 旧值 × (目标等级 / 起始等级)

起始等级默认 7（改等级之前的值），可用 `--from-level` 覆盖。
每次运行都会写 `source='emulated'` 的备注到同目录的 `attr_scale.log`，便于追溯。

用法：
    python tools/scale_role_attr.py --to-level 70 --from-level 7
    python tools/scale_role_attr.py --to-level 70 --from-level 7 --set hp_max=60000
    python tools/scale_role_attr.py --show
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
LOG = os.path.join(ROOT, 'analysis', '1.4.9', 'task', 'attr_scale.log')

# 参与缩放的列（**只动数值列**，不碰 rid / updated_at）
NUM_COLS = ['strength', 'intellect', 'armor', 'constiution',
            'atk_s', 'atk_p', 'def_s', 'def_p', 'hp_max', 'atk_speed',
            'hit', 'dodge', 'crit', 'tenacity',
            'red_def_s', 'red_def_p', 'atk_abs', 'def_abs',
            'reduce', 'hurt', 'hit_rate_show', 'dodge_rate_show',
            'crit_rate_show', 'tenacity_rate_show']


def cols(con):
    return [r[1] for r in con.execute('PRAGMA table_info(role_attr)')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rid', type=int, default=1001)
    ap.add_argument('--to-level', type=int, default=None)
    ap.add_argument('--from-level', type=int, default=7)
    ap.add_argument('--set', action='append', default=[],
                    help='显式覆盖，如 --set hp_max=60000（可多次）')
    ap.add_argument('--show', action='store_true')
    ap.add_argument('--no-backup', action='store_true')
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    have = cols(con)
    row = con.execute('SELECT * FROM role_attr WHERE rid=?', (args.rid,)).fetchone()
    if row is None:
        print('!! role_attr 里没有 rid=%s 的行' % args.rid)
        return 3
    before = {k: v for k, v in dict(row).items() if v is not None}

    if args.show or args.to_level is None and not args.set:
        print('当前 role_attr（rid=%s）：' % args.rid)
        for k, v in before.items():
            print('   %-22s %s' % (k, v))
        print('\n（加 --to-level 70 执行缩放）')
        return 0

    # 备份
    if not args.no_backup:
        stamp = time.strftime('%Y%m%d_%H%M%S')
        bdir = os.path.join(ROOT, 'backup', 'attr_scale_%s' % stamp)
        os.makedirs(bdir, exist_ok=True)
        shutil.copy2(DB, os.path.join(bdir, 'roles.db'))
        print('已备份 -> %s' % bdir)

    ratio = 1.0
    if args.to_level:
        if args.from_level <= 0:
            print('!! --from-level 必须 > 0')
            return 2
        ratio = float(args.to_level) / float(args.from_level)

    updates, changes = {}, []
    for c in NUM_COLS:
        if c not in have:
            continue
        old = before.get(c)
        if old is None:
            continue
        new = int(round(int(old) * ratio))
        if new != old:
            updates[c] = new
            changes.append((c, old, new))

    for kv in args.set:
        if '=' not in kv:
            continue
        k, _, v = kv.partition('=')
        k = k.strip()
        if k not in have:
            print('!! 未知列 %r（已忽略）' % k)
            continue
        try:
            nv = int(v)
        except ValueError:
            print('!! %r 不是整数（已忽略）' % v)
            continue
        old = before.get(k)
        updates[k] = nv
        changes = [(a, b, c2) for a, b, c2 in changes if a != k]
        changes.append((k, old, nv))

    if not updates:
        print('没有需要改动的列。')
        return 0

    con.execute('UPDATE role_attr SET %s WHERE rid=?'
                % ','.join('%s=?' % k for k in updates),
                list(updates.values()) + [args.rid])
    con.commit()
    after = {k: v for k, v in dict(
        con.execute('SELECT * FROM role_attr WHERE rid=?', (args.rid,)).fetchone()).items()
        if v is not None}
    con.close()

    print('缩放比例 x%.3f（%s 级 → %s 级）' % (ratio, args.from_level, args.to_level))
    for k, o, n in changes:
        print('   %-22s %-10s -> %s' % (k, o, n))

    # 追溯日志
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('%s  rid=%s  %s级->%s级  ratio=%.3f  source=emulated\n'
                % (time.strftime('%Y-%m-%d %H:%M:%S'), args.rid,
                   args.from_level, args.to_level, ratio))
        for k, o, n in changes:
            f.write('      %-22s %s -> %s\n' % (k, o, n))
    print('\n追溯已写入 %s' % LOG)
    print('⇒ 请**重启客户端 App**，等级/属性随 SC_10303 在登录时下发')
    return 0


if __name__ == '__main__':
    sys.exit(main())
