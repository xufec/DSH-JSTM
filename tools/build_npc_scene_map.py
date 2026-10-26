"""生成 NPC/场景/坐标关系表 → analysis/1.4.9/task/npc_scene_position_map.md

数据来源（全部 1.4.9 APK）：
  Config.MapNpc        config_map_npc.luac  -> map_npc.json
  Config.MapSceneDoors config_map_npc.luac  -> map_scene_doors.json
  Config.Map           config_map.luac      -> config_map.json
  Config.Npc           config_npc.luac      -> config_npc.json
  Config.Mission       config_mission.luac  -> server/mission_config.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

T = r'analysis\1.4.9\task'
OUT = os.path.join(T, 'npc_scene_position_map.md')


def main():
    mn = json.load(open(os.path.join(T, 'map_npc.json'), encoding='utf-8'))
    doors = json.load(open(os.path.join(T, 'map_scene_doors.json'), encoding='utf-8'))
    cm = json.load(open(os.path.join(T, 'config_map.json'), encoding='utf-8'))
    npc = json.load(open(os.path.join(T, 'config_npc.json'), encoding='utf-8'))
    ms = json.load(open(r'server\mission_config.json', encoding='utf-8'))

    L = []
    A = L.append
    A('# NPC / 场景 / 坐标关系表（1.4.9 APK 提取）')
    A('')
    A('> 全部数据来自客户端配置，**无编造**。')
    A('> 提取脚本：`tools/extract_map_npc.py`、`tools/extract_config_map.py`、`tools/extract_config_npc.py`')
    A('')
    A('## 一、`Config.MapNpc`：NPC → 场景 → 坐标（54 个唯一 NPC）')
    A('')
    A('字段来自 `config_map_npc.luac`，与 `MissionUtil.moveToNpc`（`mission_util` proto#38）')
    A('读取的 `e[1]/e[2]/e[3]` 一一对应。')
    A('')
    A('| npc_id | npc_name | 场景ID | 场景名 | x | y |')
    A('|---|---|---|---|---|---|')
    rows = sorted(mn.items(), key=lambda kv: (int(kv[1]['scene_id'] or 0), int(kv[0])))
    for k, v in rows:
        nm = (npc.get(k) or {}).get('name') or '—'
        sid = str(v['scene_id'])
        A('| %s | %s | %s | %s | %s | %s |'
          % (k, nm, sid, cm.get(sid, {}).get('name', '?'), v['x'], v['y']))
    A('')
    A('## 二、`Config.MapSceneDoors`：场景传送图（18 条）')
    A('')
    A('| 场景 | → 可去场景 |')
    A('|---|---|')
    for d in sorted(doors, key=lambda x: str(x['key'])):
        arr = d['array']
        dests = [str(x) for x in arr[1:] if x is not None]
        A('| %s %s | %s |' % (d['key'], cm.get(str(d['key']), {}).get('name', '?'),
                              ', '.join(dests)))
    A('')
    A('## 三、`Config.Map`：全部场景（%d 个）与静态布置数量' % len(cm))
    A('')
    A('| 场景ID | 场景名 | rows | cols | def_x | def_y | npcs | mons | elems |')
    A('|---|---|---|---|---|---|---|---|---|')
    for sid in sorted(cm, key=lambda x: int(x)):
        s = cm[sid]
        A('| %s | %s | %s | %s | %s | %s | %d | %d | %d |'
          % (sid, s.get('name'), s.get('rows'), s.get('cols'), s.get('def_x'), s.get('def_y'),
             len(s.get('npcs') or {}), len(s.get('mons') or {}), len(s.get('elems') or {})))
    A('')
    A('## 四、★ 剧情主线需要的 NPC：哪些能寻路、哪些不能')
    A('')
    A('判定规则（来自 `mission_util` proto#38）：')
    A('')
    A('- **在 `Config.MapNpc` 里** ⇒ 客户端本地就能解析坐标 ⇒ 可寻路（`CONFIRMED`）')
    A('- **不在 `Config.MapNpc`** ⇒ 只能靠 `StoryCtrl:getInstance():getView():findSrvNpc(npcId)`')
    A('  ⇒ **必须由服务端把它放进当前场景的 `SC_10201.npcs`**（否则无坐标 ⇒ 不寻路）')
    A('')
    zhu = {int(k): v for k, v in ms.items() if v.get('type') == 1}
    inmap, notin = [], []
    for bid in sorted(zhu):
        snpc = zhu[bid].get('commit_npc_id') or 0
        if not snpc:
            continue
        (inmap if str(snpc) in mn else notin).append((bid, snpc))
    A('### 4.1 提交 NPC **在** `Config.MapNpc`：%d 条主线（可寻路）' % len(inmap))
    A('')
    A('| task_id | task_name | submit_npc | npc_name | 场景 | x | y |')
    A('|---|---|---|---|---|---|---|')
    for bid, snpc in inmap[:60]:
        v = mn[str(snpc)]
        A('| %d | %s | %d | %s | %s %s | %s | %s |'
          % (bid, zhu[bid].get('name'), snpc, (npc.get(str(snpc)) or {}).get('name', '—'),
             v['scene_id'], cm.get(str(v['scene_id']), {}).get('name', '?'), v['x'], v['y']))
    A('')
    A('### 4.2 提交 NPC **不在** `Config.MapNpc`：%d 条主线（**需服务端下发**）' % len(notin))
    A('')
    A('| task_id | task_name | submit_npc | npc_name | 结论 |')
    A('|---|---|---|---|---|')
    for bid, snpc in notin:
        A('| %d | %s | %d | %s | 服务端须放入当前场景 |'
          % (bid, zhu[bid].get('name'), snpc, (npc.get(str(snpc)) or {}).get('name', '【无定义】')))
    A('')
    open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
    print('写出', OUT)
    print('  MapNpc %d ｜ 场景 %d ｜ 传送 %d ｜ 主线提交NPC在表内 %d / 表外 %d'
          % (len(mn), len(cm), len(doors), len(inmap), len(notin)))


if __name__ == '__main__':
    main()
