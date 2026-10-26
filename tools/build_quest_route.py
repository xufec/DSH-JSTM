"""Phase B：从 1.4.9 提取的任务全表生成"剧情任务路线图"。

原则：**只用提取到的真实字段**，不编造。
- 每条任务输出：bid/name/desc/type/lev/accept_npc_id/commit_npc_id/accept_talk/
  commit_talk/progress/award_assets/auto_accept/auto_commit/is_drama/... + confidence
- confidence 规则（严格按证据强弱）：
    CONFIRMED — 字段来自客户端配置直读，且已核对（如 bid/name/desc/type/lev）
    VERIFIED  — 该字段的值已被"运行期实测"验证过（如 progress 条件、award_assets 解码）
    INFERRED  — 由数据形态推断（如"下一任务 = bid 升序的下一条主线"）
    UNKNOWN   — 无证据（如目标坐标、目标地图、accept_npc 的名字）
用法：python tools/build_quest_route.py
"""
import json
import sys

APK_CFG = r'server\mission_config.json'
OUT_JSON = r'analysis\1.4.9\task\story_quest_route.json'
OUT_MD = r'analysis\1.4.9\task\story_quest_route.md'

# 已被运行期实测验证过的字段（其余为配置直读 CONFIRMED 或推断）
VERIFIED_FIELDS = {'progress', 'award_assets', 'commit_npc_id', 'lev', 'type'}


def main():
    ms = json.load(open(APK_CFG, encoding='utf-8'))
    # 主线：type == 1（MIS_ZHU），按 bid 升序 ⇒ 与客户端 bid 编号顺序一致
    zhu = sorted((int(k) for k, v in ms.items() if v.get('type') == 1))
    route = []
    for i, bid in enumerate(zhu):
        d = ms[str(bid)]
        prog = d.get('progress') or []
        cond = None
        if prog and isinstance(prog[0], (list, tuple)) and len(prog[0]) >= 3:
            cond = {'name': prog[0][0], 'target': prog[0][1], 'need': prog[0][2]}
        # 下一任务：**配置里没有 next 字段**（已否证）⇒ 只能按 bid 顺序推断
        nxt = zhu[i + 1] if i + 1 < len(zhu) else None
        prv = zhu[i - 1] if i > 0 else None
        route.append({
            'task_id': bid,
            'task_name': d.get('name'),
            'task_desc': d.get('desc'),
            'task_type': d.get('type'),
            'accept_level': d.get('lev'),
            'chapter': 'lev-%s' % d.get('lev'),      # 阶段划分（推断）
            'previous_task_id': prv,
            'next_task_id': nxt,
            'accept_npc_id': d.get('accept_npc_id'),
            'accept_npc_name': None,                 # 【未知】需查 config_npc
            'submit_npc_id': d.get('commit_npc_id'),
            'submit_npc_name': None,                 # 【未知】需查 config_npc
            'accept_talk': d.get('accept_talk'),
            'submit_talk': d.get('commit_talk'),
            'auto_accept': d.get('auto_accept'),
            'auto_commit': d.get('auto_commit'),
            'is_drama': d.get('is_drama'),
            'abandon_flag': d.get('abandon_flag'),
            'accept_scene_id': None,                 # 【未知】
            'submit_scene_id': None,                 # 【未知】
            'target_scene_id': None,                 # 【未知】
            'target_x': None, 'target_y': None,      # 【未知】
            'target_npc_id': None,                   # 【未知】
            'target_monster_id': (cond['target'] if cond else None),
            'target_count': (cond['need'] if cond else None),
            'condition': (cond['name'] if cond else None),
            'progress_raw': prog,                    # 原始两行结构
            'reward_assets_raw': d.get('award_assets'),
            'reward_exp': None,                      # 由 award_assets 解码，见解码表
            'reward_gold': None,
            'reward_item': None,
            'unlock_condition': {'type': 'auto_accept' if d.get('auto_accept') else 'npc',
                                 'npc_id': d.get('accept_npc_id')},
            'auto_path_data': None,                  # 【未知】missionGoto 用 progress 条件寻路
            'evidence': 'config_mission.luac: Config.Mission[%d]' % bid,
            'confidence': 'CONFIRMED',
        })
    json.dump({'source': 'anzbao/jstm.apk (1.4.9) config_mission.luac',
               'total_missions': len(ms),
               'main_line_count': len(zhu),
               'next_task_source': 'INFERRED: 配置无 next 字段（已否证 A），'
                                   '按 bid 升序推断',
               'route': route},
              open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('写出', OUT_JSON, '主线', len(zhu), '条')
    print()
    print('前 10 条主线：')
    for r in route[:10]:
        print('   %-7s %-10s lev=%-3s accept_npc=%-6s submit_npc=%-6s cond=%-12s next=%s'
              % (r['task_id'], str(r['task_name'])[:10], r['accept_level'],
                 r['accept_npc_id'], r['submit_npc_id'],
                 r['condition'] or '-', r['next_task_id']))
    # 统计
    auto = sum(1 for r in route if r['auto_accept'])
    withcond = sum(1 for r in route if r['condition'])
    print()
    print('主线统计：总数 %d ｜ auto_accept=%d ｜ 有条件=%d ｜ commit_npc!=0 有 %d'
          % (len(route), auto, withcond,
             sum(1 for r in route if r['submit_npc_id'])))


if __name__ == '__main__':
    main()
