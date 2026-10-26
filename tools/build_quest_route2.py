"""Phase B（增强版）：剧情任务路线图 —— 把任务表与**真实场景/坐标**关联。

数据来源（全部来自 1.4.9 APK，无编造）：
  server/mission_config.json        <- assets/src/config/config_mission.luac
  analysis/1.4.9/task/map_npc.json  <- assets/src/config/config_map_npc.luac  (Config.MapNpc)
  analysis/1.4.9/task/config_map.json <- assets/src/config/config_map.luac    (Config.Map)

关联规则（每条都能说出证据）：
  submit_npc_id  -> Config.MapNpc[npc] = {scene_id,x,y}   => submit_scene_id/x/y  【CONFIRMED】
  target(elem)   -> 在 Config.Map[*].elems 里反查 id       => target_scene_id/x/y  【CONFIRMED】
  target(mon)    -> 在 Config.Map[*].mons 里反查 id        => 实测 mons 全表为空 => 【UNKNOWN】
  submit_npc !=0 但不在 Config.MapNpc            => 需服务端 SC_10201 现场下发 => 【UNKNOWN】

confidence 只用 CONFIRMED / VERIFIED / INFERRED / UNKNOWN。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

MISSION = r'server\mission_config.json'
MAP_NPC = r'analysis\1.4.9\task\map_npc.json'
CONFIG_MAP = r'analysis\1.4.9\task\config_map.json'
CONFIG_NPC = r'analysis\1.4.9\task\config_npc.json'
OUT_JSON = r'analysis\1.4.9\task\story_quest_route.json'
OUT_MD = r'analysis\1.4.9\task\story_quest_route.md'

# award_assets 的资产 code 映射（服务端 mock_server 已实测使用；来源 config_game_data.luac）
ASSET_CODE = {2: 'coin', 4: 'exp', 15: 'hero_exp', 1: 'gold'}

# MissionType 枚举（**权威来源**：mission_util.luac proto#68 的常量表，已提取）
MISSION_TYPE = {
    1: 'MIS_ZHU(主线)', 2: 'MIS_FUN(功能)', 3: 'MIS_RICHANG(日常)',
    4: 'MIS_CHENGJIU(成就)', 5: 'MIS_ZHI(支线)', 6: 'MIS_HUAN(循环)',
    7: 'MIS_XUAN(悬赏)', 8: 'MIS_BANG(帮派)', 9: 'MIS_GUI(归)',
    10: 'MIS_YIN(隐)', 11: 'MIS_DAN(丹)', 12: 'MIS_GUI_ALL(归·全)',
    13: 'MIS_BAOTU(宝图)', 14: 'MIS_GUILD(宗门)', 15: 'MIS_YAO(妖)',
    16: 'MIS_TRIAL(试炼)', 17: 'MIS_HUSONG(护送)', 18: 'MIS_MENPAI(门派)',
    19: 'MIS_YUEKA(月卡)', 20: 'MIS_NEWYEAR(新年)', 21: 'MIS_FAVOUR(情缘)',
    22: 'MIS_COUPLE(夫妻)', 23: 'MIS_COLLECT(采集)', 24: 'MIS_ZHIZUN(至尊)',
    25: 'MIS_GUANGHUAN(光环)', 26: 'MIS_HALO(魂环)', 27: 'MIS_SECRET(秘境)',
    29: 'MIS_JIEYI(结义)',
}


def load():
    ms = json.load(open(MISSION, encoding='utf-8'))
    mn = json.load(open(MAP_NPC, encoding='utf-8'))
    cm = json.load(open(CONFIG_MAP, encoding='utf-8'))
    try:
        nc = json.load(open(CONFIG_NPC, encoding='utf-8'))
    except Exception:
        nc = {}
    return ms, mn, cm, nc


def invert(placements):
    """把 {scene: {id: {x,y}}} 反查成 {id: (scene, x, y)}"""
    out = {}
    for sid, sub in placements.items():
        for k, v in sub.items():
            out.setdefault(k, []).append((sid, v.get('x'), v.get('y')))
    return out


def main():
    ms, mn, cm, nc = load()
    npc2 = {int(k): v for k, v in mn.items()}
    scene_name = {k: v.get('name') for k, v in cm.items()}

    def npc_name(i):
        return (nc.get(str(i)) or {}).get('name')

    elems_inv, mons_inv, npcs_inv = {}, {}, {}
    for sid, s in cm.items():
        for k, v in (s.get('elems') or {}).items():
            elems_inv.setdefault(k, []).append((sid, v.get('x'), v.get('y')))
        for k, v in (s.get('mons') or {}).items():
            mons_inv.setdefault(k, []).append((sid, v.get('x'), v.get('y')))
        for k, v in (s.get('npcs') or {}).items():
            npcs_inv.setdefault(k, []).append((sid, v.get('x'), v.get('y')))

    zhu = sorted(int(k) for k, v in ms.items() if v.get('type') == 1)
    route = []
    stat = {'submit_resolved': 0, 'submit_unknown': 0,
            'target_elem_ok': 0, 'target_mon_unknown': 0,
            'target_npc_ok': 0, 'target_npc_unknown': 0}

    for i, bid in enumerate(zhu):
        d = ms[str(bid)]
        prog = d.get('progress') or []
        cond = None
        if prog and isinstance(prog[0], (list, tuple)) and len(prog[0]) >= 3:
            cond = {'name': prog[0][0], 'target': prog[0][1], 'need': prog[0][2]}

        # ---- 提交 NPC -> 场景/坐标 ----
        snpc = d.get('commit_npc_id') or 0
        sscene = sx = sy = sname = None
        sconf = 'UNKNOWN'
        if snpc and snpc in npc2:
            e = npc2[snpc]
            sscene, sx, sy = e.get('scene_id'), e.get('x'), e.get('y')
            sname = scene_name.get(str(sscene))
            sconf = 'CONFIRMED'
            stat['submit_resolved'] += 1
        elif snpc:
            stat['submit_unknown'] += 1

        # ---- 接取 NPC ----
        anpc = d.get('accept_npc_id') or 0
        ascene = ay = ax = None
        if anpc and anpc in npc2:
            e = npc2[anpc]
            ascene, ax, ay = e.get('scene_id'), e.get('x'), e.get('y')

        # ---- 目标解析 ----
        tgt_scene = tgt_x = tgt_y = None
        tgt_npc = None
        tconf = 'UNKNOWN'
        cname = cond['name'] if cond else None
        ctarget = cond['target'] if cond else None
        if cname in ('collect_elem', 'use_item_scene', 'npc_talk'):
            key = str(ctarget)
            if key in elems_inv:
                tgt_scene, tgt_x, tgt_y = elems_inv[key][0]
                tconf = 'CONFIRMED'
                stat['target_elem_ok'] += 1
            elif key in npcs_inv:
                tgt_scene, tgt_x, tgt_y = npcs_inv[key][0]
                tconf = 'CONFIRMED'
                stat['target_npc_ok'] += 1
            elif key in npc2:
                e = npc2[int(ctarget)]
                tgt_scene, tgt_x, tgt_y = e.get('scene_id'), e.get('x'), e.get('y')
                tconf = 'CONFIRMED'
                stat['target_npc_ok'] += 1
            else:
                stat['target_npc_unknown'] += 1
        elif cname in ('fight_mon', 'kill_mon', 'kill_scene_mon', 'kill_type_mon'):
            key = str(ctarget)
            if key in mons_inv:
                tgt_scene, tgt_x, tgt_y = mons_inv[key][0]
                tconf = 'CONFIRMED'
            else:
                stat['target_mon_unknown'] += 1
        elif cname in ('gotoScene', 'findRodeCommitMission'):
            tgt_scene = ctarget
            tconf = 'INFERRED'

        # ---- 奖励解码 ----
        rewards = {}
        for pair in (d.get('award_assets') or []):
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                rewards[ASSET_CODE.get(pair[0], 'code_%s' % pair[0])] = pair[1]

        route.append({
            'task_id': bid,
            'task_name': d.get('name'),
            'task_desc': d.get('desc'),
            'task_type': d.get('type'),
            'accept_level': d.get('lev'),
            'chapter': 'lev-%s' % d.get('lev'),
            'previous_task_id': (zhu[i - 1] if i > 0 else None),
            'next_task_id': (zhu[i + 1] if i + 1 < len(zhu) else None),
            'accept_npc_id': anpc or None,
            'accept_npc_name': npc_name(anpc) if anpc else None,
            'accept_scene_id': ascene,
            'accept_x': ax, 'accept_y': ay,
            'submit_npc_id': snpc or None,
            'submit_npc_name': npc_name(snpc) if snpc else None,
            'submit_scene_id': sscene,
            'submit_scene_name': sname,
            'submit_x': sx, 'submit_y': sy,
            'submit_pos_confidence': sconf,
            'accept_talk': d.get('accept_talk'),
            'submit_talk': d.get('commit_talk'),
            'auto_accept': d.get('auto_accept'),
            'auto_commit': d.get('auto_commit'),
            'is_drama': d.get('is_drama'),
            'abandon_flag': d.get('abandon_flag'),
            'condition': cname,
            'target_monster_id': (ctarget if cname and cname.startswith(('fight_mon', 'kill_')) else None),
            'target_elem_id': (ctarget if cname in ('collect_elem', 'use_item_scene') else None),
            'target_npc_id': tgt_npc,
            'target_count': (cond['need'] if cond else None),
            'target_scene_id': tgt_scene,
            'target_x': tgt_x, 'target_y': tgt_y,
            'target_confidence': tconf,
            'progress_raw': prog,
            'reward_assets_raw': d.get('award_assets'),
            'reward': rewards,
            'reward_exp': rewards.get('exp'),
            'reward_gold': rewards.get('gold'),
            'reward_coin': rewards.get('coin'),
            'unlock_condition': {'type': 'auto_accept' if d.get('auto_accept') else 'npc',
                                 'npc_id': anpc or None},
            'auto_path_data': None,
            'evidence': ('config_mission.luac:Config.Mission[%d]'
                         + ('; config_map_npc.luac:Config.MapNpc[%d]' % snpc if sscene else '')) % bid,
            'confidence': 'CONFIRMED',
        })

    out = {
        'source': 'anzbao/jstm.apk (1.4.9)',
        'tables_used': {
            'mission': 'assets/src/config/config_mission.luac -> Config.Mission',
            'map_npc': 'assets/src/config/config_map_npc.luac -> Config.MapNpc',
            'map': 'assets/src/config/config_map.luac -> Config.Map',
        },
        'total_missions': len(ms),
        'main_line_count': len(zhu),
        'next_task_source': 'INFERRED: 配置无 next 字段（已否证），按 bid 升序推断',
        'stats': stat,
        'route': route,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(out, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('写出', OUT_JSON, '主线', len(zhu), '条')
    print('统计:', json.dumps(stat, ensure_ascii=False))
    print()
    print('前 16 条主线（含真实坐标）：')
    print('  %-7s %-10s %-4s %-9s %-8s %-10s %-15s %-12s %s'
          % ('task', 'name', 'lev', 'sub_npc', 'scene', 'pos', 'cond',
             'target', 'tgt_scene,pos'))
    for r in route[:16]:
        pos = ('(%s,%s)' % (r['submit_x'], r['submit_y'])) if r['submit_x'] is not None else '-'
        tp = ('(%s,%s)' % (r['target_x'], r['target_y'])) if r['target_x'] is not None else '-'
        print('  %-7s %-10s %-3s %-7s %-7s %-10s %-15s %s->%s %s'
              % (r['task_id'], str(r['task_name'])[:10], r['accept_level'],
                 r['submit_npc_id'], r['submit_scene_id'], pos,
                 r['condition'] or '-', r['target_monster_id'] or r['target_elem_id'] or '',
                 r['target_scene_id'] or '-', tp))


if __name__ == '__main__':
    main()
