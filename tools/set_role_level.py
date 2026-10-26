"""调整本地私服角色等级（并可选改经验）。

角色的**权威来源是数据库**（`server/state/roles.db` 的 `roles.level`）——
`mock_server.py` 的 `role_state()` 优先级为：
    ROLE_DEFAULTS < config.json.role < **数据库 roles 行**
所以只改 config.json 是**不生效**的（除非数据库里还没有该角色行）。
本工具两处一起改，避免以后重建库时又变回旧等级。

用法：
    python tools/set_role_level.py 70
    python tools/set_role_level.py 70 --exp 0
    python tools/set_role_level.py 70 --rid 1001

改完后需要**让客户端重新登录**（重启 App）才会拉到新等级：
客户端等级来自服务端 `SC_10303`（角色信息），登录时才下发。
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
CFG = os.path.join(ROOT, 'server', 'config.json')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('level', type=int)
    ap.add_argument('--rid', type=int, default=1001)
    ap.add_argument('--exp', type=int, default=None,
                    help='不给就保持原值')
    ap.add_argument('--no-backup', action='store_true')
    args = ap.parse_args()

    if not (1 <= args.level <= 200):
        print('!! 等级超出合理范围 1..200')
        return 2

    # ---- 备份 ----
    if not args.no_backup:
        stamp = time.strftime('%Y%m%d_%H%M%S')
        bdir = os.path.join(ROOT, 'backup', 'level_change_%s' % stamp)
        os.makedirs(bdir, exist_ok=True)
        shutil.copy2(DB, os.path.join(bdir, 'roles.db'))
        shutil.copy2(CFG, os.path.join(bdir, 'config.json'))
        print('已备份 -> %s' % bdir)

    # ---- 数据库（权威）----
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    row = con.execute('SELECT * FROM roles WHERE rid=?', (args.rid,)).fetchone()
    if row is None:
        print('!! 数据库里没有 rid=%s 的角色' % args.rid)
        con.close()
        return 3
    before = dict(row)
    con.execute('UPDATE roles SET level=?, updated_at=? WHERE rid=?',
                (args.level, int(time.time()), args.rid))
    if args.exp is not None:
        con.execute('UPDATE roles SET exp=? WHERE rid=?', (args.exp, args.rid))
    con.commit()
    after = dict(con.execute('SELECT * FROM roles WHERE rid=?', (args.rid,)).fetchone())
    con.close()
    print('DB   roles: level %s -> %s%s'
          % (before.get('level'), after.get('level'),
             '' if args.exp is None else '   exp %s -> %s' % (before.get('exp'), after.get('exp'))))

    # ---- config.json（只在"库还没这行"时才起作用，但保持一致性）----
    cfg = json.load(open(CFG, encoding='utf-8'))
    ch = []
    if isinstance(cfg.get('role'), dict) and cfg['role'].get('lev') != args.level:
        ch.append('role.lev %s -> %s' % (cfg['role'].get('lev'), args.level))
        cfg['role']['lev'] = args.level
        if args.exp is not None:
            cfg['role']['exp'] = args.exp
    if isinstance(cfg.get('roles'), list):
        for r in cfg['roles']:
            if r.get('rid') == args.rid and r.get('lev') != args.level:
                ch.append('roles[rid=%s].lev %s -> %s' % (args.rid, r.get('lev'), args.level))
                r['lev'] = args.level
    if ch:
        json.dump(cfg, open(CFG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('CFG  ', '; '.join(ch))
    else:
        print('CFG   config.json 已是目标等级（未改）')

    print()
    print('⇒ 请**重启客户端 App**（重新登录）以拉取新等级')
    print('   （等级随 SC_10303 在登录时下发；服务端每次读库，无需重启服务端）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
