"""检查本地私服的角色 / 任务 / 资产状态（只读）。

用法：python tools/inspect_db.py
"""
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  'server', 'state', 'roles.db')


def main():
    print('DB:', DB, '存在' if os.path.exists(DB) else '【缺失】')
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    print('\n=== 表 ===')
    tabs = [r['name'] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")]
    print('  ', tabs)

    for t in tabs:
        print('\n=== %s ===' % t)
        try:
            rows = con.execute('SELECT * FROM %s' % t).fetchall()
        except Exception as e:
            print('   ERR', e)
            continue
        if not rows:
            print('   (空)')
            continue
        if t == 'missions':
            for r in sorted(rows, key=lambda x: x['mission_bid']):
                d = dict(r)
                print('   bid=%-7s status=%-3s value=%-5s target=%-7s tval=%-5s '
                      'proc=%-3s code=%-3s commit=%-4s loop=%s/%s'
                      % (d.get('mission_bid'), d.get('mission_status'), d.get('value'),
                         d.get('target'), d.get('target_value'), d.get('process_status'),
                         d.get('code'), d.get('commit_num'), d.get('loop_count'),
                         d.get('loop_num')))
        else:
            for r in rows:
                d = dict(r)
                s = ' '.join('%s=%s' % (k, v) for k, v in d.items()
                             if k not in ('updated_at',))
                print('   ', s[:300])


if __name__ == '__main__':
    main()
