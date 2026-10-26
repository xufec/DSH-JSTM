"""Phase E 自测：验证「加经验 → 达标 → 升级 → 属性成长 → 落库」。

不依赖客户端，直接对 `server/state/roles.db` 跑一遍。
**会自动备份/还原数据库**，不会破坏现场。

用法：
    python tools/test_levelup.py
    python tools/test_levelup.py --db server/state/roles.db --exp 5000
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.join(ROOT, 'server', 'state', 'roles.db'))
    # ★ R243：`200000` 是**等级表换版前的旧值** —— 现在 70→71 需要 **2600094**，
    #   加 20 万永远升不了级 ⇒ 两个断言必然失败（**测试参数过期**，不是服务端 bug）。
    ap.add_argument('--exp', type=int, default=3000000)
    ap.add_argument('--rid', type=int, default=1001)
    a = ap.parse_args()

    if not os.path.exists(a.db):
        print('!! 数据库不存在: %s' % a.db)
        return 1
    bak = a.db + '.leveltest.bak'
    shutil.copy2(a.db, bak)
    print('已备份 -> %s' % bak)

    import mock_server as M
    try:
        M.DB_PATH = a.db
        M.db_init()
        M.db_bag_init()

        st = M.role_state(M.DEFAULT_CFG)
        lev0, exp0 = int(st['lev']), int(st.get('exp') or 0)
        need0 = M.level_need(lev0)
        print('\n--- 战前 ---')
        print('  lev=%d exp=%d 本级需要=%s exp_max(下发)=%s exp_total_nextlev=%s'
              % (lev0, exp0, need0, st.get('exp_max'), st.get('exp_total_nextlev')))
        attr0 = M.db_get_attr(a.rid) or {}
        print('  atk_s=%s hp_max=%s' % (attr0.get('atk_s'), attr0.get('hp_max')))

        print('\n--- 加 %d 经验 ---' % a.exp)
        res = M.add_role_exp(M.DEFAULT_CFG, a.rid, a.exp)
        print('  结果: %s' % res)

        st2 = M.role_state(M.DEFAULT_CFG)
        attr1 = M.db_get_attr(a.rid) or {}
        print('\n--- 战后 ---')
        print('  lev=%d exp=%d exp_max(下发)=%s exp_total_nextlev=%s'
              % (int(st2['lev']), int(st2.get('exp') or 0),
                 st2.get('exp_max'), st2.get('exp_total_nextlev')))
        print('  atk_s=%s hp_max=%s' % (attr1.get('atk_s'), attr1.get('hp_max')))

        # 断言
        print('\n--- 断言 ---')
        ok = True
        if res['lev'] <= lev0:
            print('  !! 等级没有提升'); ok = False
        else:
            print('  OK 等级 %d -> %d（升 %d 级）' % (lev0, res['lev'], res['ups']))
        if res['exp'] >= (M.level_need(res['lev']) or 1 << 62):
            print('  !! 剩余经验仍 >= 下一级需求，升级循环有问题'); ok = False
        else:
            print('  OK 剩余经验 %d < 下一级需求 %s' % (res['exp'], M.level_need(res['lev'])))
        if int(st2.get('exp_max') or 0) != (M.level_need(res['lev']) or 0):
            print('  !! role_state 下发的 exp_max 与实际阈值不一致'); ok = False
        else:
            print('  OK 下发的 exp_max 与阈值一致 (%s)' % st2.get('exp_max'))
        if int(attr1.get('atk_s') or 0) <= int(attr0.get('atk_s') or 0):
            print('  !! 属性没有成长（应为 IMPLEMENTATION_FALLBACK 成长）'); ok = False
        else:
            print('  OK 属性成长 atk_s %s -> %s' % (attr0.get('atk_s'), attr1.get('atk_s')))

        # 重登保持：重新读一次（模拟重连/重启）
        st3 = M.role_state(M.DEFAULT_CFG)
        if int(st3['lev']) != int(st2['lev']):
            print('  !! 重新读取后等级不一致'); ok = False
        else:
            print('  OK 重新读取等级保持 %d' % int(st3['lev']))

        print('\n结论: %s' % ('全部通过 ✅' if ok else '存在失败项 ❌'))
        return 0 if ok else 2
    finally:
        shutil.copy2(bak, a.db)
        os.remove(bak)
        print('\n已还原数据库（备份已删除）')


if __name__ == '__main__':
    sys.exit(main() or 0)
