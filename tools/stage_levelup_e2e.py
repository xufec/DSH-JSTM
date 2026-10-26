"""Phase E 真机 E2E 的现场准备：把角色放到「只差一点点经验就升级」。

用法：
    python tools/stage_levelup_e2e.py            # 默认差 100 经验
    python tools/stage_levelup_e2e.py --gap 5000 # 差 5000
    python tools/stage_levelup_e2e.py --restore  # 还原到战斗回归起点

做法（**不伪造完成，只设置测试起点**）：
    从 `analysis/_db_before_battle.db` 还原，然后把 `role_assets.exp`
    设为「本级需求 - gap」，使角色处于即将升级的状态。
    经验本身仍必须由**真实战斗/任务奖励**产生。
"""
import argparse
import io
import os
import shutil
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'server'))

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
SNAP = os.path.join(ROOT, 'analysis', '_db_before_battle.db')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gap', type=int, default=100)
    ap.add_argument('--rid', type=int, default=1001)
    ap.add_argument('--restore', action='store_true')
    a = ap.parse_args()

    if not os.path.exists(SNAP):
        print('!! 缺少快照 %s' % SNAP)
        return 1
    shutil.copy2(SNAP, DB)
    for f in (os.path.join(ROOT, 'server', 'state', 'role_%d.json' % a.rid),):
        if os.path.exists(f):
            os.remove(f)
    print('已从快照还原 -> %s' % DB)

    import mock_server as M
    M.DB_PATH = DB
    M.db_init()
    M.db_bag_init()
    if a.restore:
        st = M.role_state(M.DEFAULT_CFG)
        print('lev=%s exp=%s' % (st['lev'], st.get('exp')))
        return 0

    st = M.role_state(M.DEFAULT_CFG)
    lev = int(st['lev'])
    need = M.level_need(lev)
    if not need:
        print('!! 已是等级上限 %s' % lev)
        return 1
    target = max(0, need - int(a.gap))
    con = sqlite3.connect(DB)
    con.execute('INSERT OR IGNORE INTO role_assets (rid,name,amount) VALUES (?,?,0)',
                (a.rid, 'exp'))
    con.execute('UPDATE role_assets SET amount=? WHERE rid=? AND name=?',
                (target, a.rid, 'exp'))
    con.commit()
    con.close()
    st = M.role_state(M.DEFAULT_CFG)
    print('已布置：lev=%s exp=%s  本级需求=%s  → 再得 %s 经验即升级'
          % (st['lev'], st.get('exp'), need, need - target))
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
