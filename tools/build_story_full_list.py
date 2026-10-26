"""生成【1.4.9 完整剧情任务清单】。

输出：
  analysis/1.4.9/task/story_quest_full_list.md    完整 262 条主线（按等级=章节分组）+ 全表分类索引
  analysis/1.4.9/task/story_quest_full_list.csv   便于表格软件打开

数据来源（全部 1.4.9 APK）：
  Config.Mission  config_mission.luac  -> server/mission_config.json
  Config.MapNpc   config_map_npc.luac  -> map_npc.json
  Config.Map      config_map.luac      -> config_map.json
  Config.Npc      config_npc.luac      -> config_npc.json
  MissionType 枚举 mission_util.luac proto#68（已提取，见 MISSION_TYPE）
"""
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

T = r'analysis\1.4.9\task'
OUT_MD = os.path.join(T, 'story_quest_full_list.md')
OUT_CSV = os.path.join(T, 'story_quest_full_list.csv')

MISSION_TYPE = {
    1: ('MIS_ZHU', '主线'), 2: ('MIS_FUN', '功能'), 3: ('MIS_RICHANG', '日常'),
    4: ('MIS_CHENGJIU', '成就'), 5: ('MIS_ZHI', '支线'), 6: ('MIS_HUAN', '循环'),
    7: ('MIS_XUAN', '悬赏'), 8: ('MIS_BANG', '帮派'), 9: ('MIS_GUI', '归'),
    10: ('MIS_YIN', '隐'), 11: ('MIS_DAN', '丹'), 12: ('MIS_GUI_ALL', '归·全'),
    13: ('MIS_BAOTU', '宝图'), 14: ('MIS_GUILD', '宗门'), 15: ('MIS_YAO', '妖'),
    16: ('MIS_TRIAL', '试炼'), 17: ('MIS_HUSONG', '护送'), 18: ('MIS_MENPAI', '门派'),
    19: ('MIS_YUEKA', '月卡'), 20: ('MIS_NEWYEAR', '新年'), 21: ('MIS_FAVOUR', '情缘'),
    22: ('MIS_COUPLE', '夫妻'), 23: ('MIS_COLLECT', '采集'), 24: ('MIS_ZHIZUN', '至尊'),
    25: ('MIS_GUANGHUAN', '光环'), 26: ('MIS_HALO', '魂环'), 27: ('MIS_SECRET', '秘境'),
    29: ('MIS_JIEYI', '结义'),
}


def reward_str(r):
    if not r:
        return '—'
    parts = []
    for k in ('coin', 'exp', 'hero_exp', 'gold'):
        if r.get(k):
            parts.append('%s=%s' % (k, r[k]))
    for k, v in r.items():
        if k not in ('coin', 'exp', 'hero_exp', 'gold'):
            parts.append('%s=%s' % (k, v))
    return ' '.join(parts) if parts else '—'


def main():
    ms = json.load(open(r'server\mission_config.json', encoding='utf-8'))
    route = json.load(open(os.path.join(T, 'story_quest_route.json'), encoding='utf-8'))
    rows = route['route']
    by_bid = {r['task_id']: r for r in rows}

    L = []
    A = L.append
    A('# 绝世唐门 1.4.9 —— 完整剧情任务清单')
    A('')
    A('> **数据来源**：`anzbao/jstm.apk`（1.4.9）的 `config_mission.luac` / `config_map_npc.luac` /')
    A('> `config_map.luac` / `config_npc.luac`，以及 `mission_util.luac` proto#68 的 `MissionType` 枚举。')
    A('> 全部为客户端配置直读，**无编造**。')
    A('>')
    A('> **任务总数 846**，其中 `MIS_ZHU`（主线，type=1）**262 条** —— 本文件主体即这 262 条。')
    A('')
    A('## 一、任务类型分布（`MissionType` 枚举取自 `mission_util.luac` proto#68）')
    A('')
    A('| type | 常量 | 含义 | 条数 | bid 范围 |')
    A('|---|---|---|---|---|')
    import collections
    cnt = collections.Counter(v.get('type') for v in ms.values())
    for t in sorted(cnt, key=lambda x: (x is None, x)):
        bids = [int(k) for k, v in ms.items() if v.get('type') == t]
        nm, zh = MISSION_TYPE.get(t, ('?', '?'))
        A('| %s | `%s` | %s | %d | %d ~ %d |'
          % (t, nm, zh, cnt[t], min(bids), max(bids)))
    A('')
    A('⇒ **主线（type=1 `MIS_ZHU`）共 262 条**，其余 584 条为日常/支线/秘境/宗门/活动等，')
    A('**不属于剧情主线**，不与主线混列。')
    A('')

    # ---- 主体：262 条主线，按 lev 分组 ----
    A('## 二、剧情主线全表（262 条，按等级分组 = 剧情章节）')
    A('')
    A('字段说明：')
    A('')
    A('- **条件**：`progress` 的完成条件（`fight_mon` 打怪 / `collect_elem` 采集 / 空=对话或自动）')
    A('- **提交NPC**：`commit_npc_id` → `Config.Npc` 的名字；括号内 `场景id 场景名 (x,y)` 来自 `Config.MapNpc`')
    A('- **寻路**：`✅` = 目标在 `Config.MapNpc` 里，客户端可自动寻路；`❌` = 剧情 NPC，坐标不在 APK')
    A('- **奖励**：`award_assets` 解码（coin 金魂币 / exp 经验 / hero_exp 魂师经验）')
    A('')

    levs = sorted({r['accept_level'] for r in rows})
    for lev in levs:
        grp = [r for r in rows if r['accept_level'] == lev]
        A('### 章节 lev=%s（%d 条）' % (lev, len(grp)))
        A('')
        A('| # | task_id | 任务名 | 追踪文案 | 描述 | 条件 | 提交NPC | 场景/坐标 | 寻路 | 奖励 |')
        A('|---|---|---|---|---|---|---|---|---|---|')
        for r in grp:
            bid = r['task_id']
            d = ms[str(bid)]
            cond = r['condition'] or '—'
            if cond != '—':
                tgt = r.get('target_monster_id') or r.get('target_elem_id')
                cond = '%s(%s)x%s' % (cond, tgt, r.get('target_count'))
            npc = r.get('submit_npc_id')
            if npc:
                nm = r.get('submit_npc_name') or '【无定义】'
                if r.get('submit_scene_id'):
                    loc = '%s %s (%s,%s)' % (r['submit_scene_id'],
                                             r['submit_scene_name'] or '?',
                                             r['submit_x'], r['submit_y'])
                    path = '✅'
                else:
                    loc = '【UNKNOWN】剧情场景'
                    path = '❌'
                npcs = '%s %s' % (npc, nm)
            else:
                npcs, loc, path = '—（无提交NPC）', '—', '—'
            track = (d.get('progress_edit_2') or d.get('progress_edit') or '').replace('|', '/')
            desc = (d.get('desc') or '').replace('|', '/')
            A('| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s |'
              % (grp.index(r) + 1, bid, d.get('name'), track, desc, cond, npcs, loc,
                 path, reward_str(r.get('reward'))))
        A('')

    # ---- 附录 ----
    A('## 三、附录：任务总数与"可自动寻路"覆盖')
    A('')
    st = route.get('stats', {})
    A('| 项 | 值 |')
    A('|---|---|')
    A('| 主线总数 | 262 |')
    A('| 提交 NPC 在 `Config.MapNpc`（**可自动寻路**） | %s |' % st.get('submit_resolved'))
    A('| 提交 NPC 为剧情 NPC（坐标不在 APK） | %s |' % st.get('submit_unknown'))
    A('| `fight_mon` 类目标（怪物无摆位数据） | %s |' % st.get('target_mon_unknown'))
    A('')
    A('## 四、复现')
    A('')
    A('```powershell')
    A('python tools\\build_quest_route2.py        # 生成 story_quest_route.json')
    A('python tools\\build_story_full_list.py     # 生成本文件与 CSV')
    A('```')
    A('')

    open(OUT_MD, 'w', encoding='utf-8').write('\n'.join(L))
    print('写出', OUT_MD, '(%d 行)' % len(L))

    # ---- CSV ----
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['task_id', 'name', 'desc', 'progress_edit_2', 'lev', 'type',
                    'condition', 'target_id', 'target_count',
                    'submit_npc_id', 'submit_npc_name',
                    'submit_scene_id', 'submit_scene_name', 'submit_x', 'submit_y',
                    'can_autopath', 'reward_coin', 'reward_exp', 'reward_hero_exp',
                    'prev_task_id', 'next_task_id'])
        for r in rows:
            d = ms[str(r['task_id'])]
            npc = r.get('submit_npc_id')
            w.writerow([
                r['task_id'], d.get('name'), d.get('desc'),
                d.get('progress_edit_2') or d.get('progress_edit'),
                r['accept_level'], r['task_type'],
                r['condition'] or '',
                r.get('target_monster_id') or r.get('target_elem_id') or '',
                r.get('target_count') or '',
                npc or '', r.get('submit_npc_name') or '',
                r.get('submit_scene_id') or '', r.get('submit_scene_name') or '',
                r.get('submit_x') if r.get('submit_x') is not None else '',
                r.get('submit_y') if r.get('submit_y') is not None else '',
                'Y' if r.get('submit_scene_id') else 'N',
                (r.get('reward') or {}).get('coin', ''),
                (r.get('reward') or {}).get('exp', ''),
                (r.get('reward') or {}).get('hero_exp', ''),
                r.get('previous_task_id') or '', r.get('next_task_id') or '',
            ])
    print('写出', OUT_CSV, '(262 行主线)')

    # ---- 控制台摘要：前 20 条 ----
    print('\n前 20 条主线：')
    for r in rows[:20]:
        d = ms[str(r['task_id'])]
        print('  %-7s %-8s lev=%-3s %-14s %-16s %s'
              % (r['task_id'], d.get('name'), r['accept_level'],
                 (d.get('progress_edit_2') or d.get('desc') or '')[:14],
                 r.get('submit_npc_name') or '—',
                 ('%s(%s,%s)' % (r['submit_scene_id'], r['submit_x'], r['submit_y']))
                 if r.get('submit_scene_id') else '【剧情场景UNKNOWN】'))


if __name__ == '__main__':
    main()
