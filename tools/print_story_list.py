"""打印 1.4.9 剧情主线（262 条）的紧凑清单，按等级=章节分组。

用法：python tools/print_story_list.py [起始lev] [结束lev]
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    ms = json.load(open(r'server\mission_config.json', encoding='utf-8'))
    route = json.load(open(r'analysis\1.4.9\task\story_quest_route.json',
                           encoding='utf-8'))['route']

    cur = None
    n = 0
    for x in route:
        lev = x['accept_level']
        if lev < lo or lev > hi:
            continue
        if lev != cur:
            cur = lev
            print('\n===== 章节 lev=%s =====' % lev)
        n += 1
        d = ms[str(x['task_id'])]
        track = (d.get('progress_edit_2') or d.get('progress_edit') or d.get('desc') or '')
        cond = x['condition'] or ''
        if cond:
            t = x.get('target_monster_id') or x.get('target_elem_id')
            cond = ' [%s(%s)x%s]' % (cond, t, x.get('target_count'))
        npc = x.get('submit_npc_name')
        if x.get('submit_scene_id'):
            loc = '%s@%s(%s,%s)' % (npc or x['submit_npc_id'],
                                    x['submit_scene_name'], x['submit_x'], x['submit_y'])
        elif x.get('submit_npc_id'):
            loc = '%s@【剧情场景未知】' % (npc or x['submit_npc_id'])
        else:
            loc = '无提交NPC'
        rw = x.get('reward') or {}
        rws = '/'.join('%s%s' % (k, v) for k, v in rw.items()) or '—'
        print('%-6s %-7s %-20s%-16s 提交:%-24s 奖励:%s'
              % (x['task_id'], d.get('name'), track[:20], cond, loc, rws))
    print('\n合计 %d 条' % n)


if __name__ == '__main__':
    main()
