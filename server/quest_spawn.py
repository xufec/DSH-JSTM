"""Phase F 服务端侧修复：把「任务链当前需要的目标」放进当前场景。

## 为什么需要它（有实测依据，不是猜）

`mission_util` proto#38 `moveToNpc(npcId)` 的**两条**目标解析路径：

    local e = Config.MapNpc[npcId]                  -- ① 客户端本地静态表
    if e then
        MissionUtil.gotoTarget(FindType.NPC, e[1], e[2], e[3], nil, npcId)
    else
        local vo = StoryCtrl:getInstance():getView():findSrvNpc(npcId)   -- ② 场景内"服务端 NPC"
        if vo then MissionUtil.gotoTarget(FindType.NPC, vo.scene_id, vo.x, vo.y, nil, npcId) end
    end

实测（`task_autopath_probe_result.md`）：

| 调用 | 结果 |
|---|---|
| `moveToNpc(10030)`（在 `Config.MapNpc`） | ✅ 命中 → `gotoTarget` → `scene:gotoTarget` → **角色真的走了** |
| `moveToNpc(20011)`（**不在** `Config.MapNpc`，场景里也没有） | ❌ `cfg_notInMapNpc` → **完全没有 `gotoTarget`** → 不动 |

⇒ **服务端唯一能做的、也是必须做的**：把任务链当前需要的 NPC / 怪物
放进当前场景的 `SC_10201.npcs` / `SC_10201.mons`。

## 数据来源（全部 1.4.9 APK，无编造）

| 用途 | 来源 |
|---|---|
| 哪些 NPC 客户端本地能解析 | `Config.MapNpc`（`map_npc.json`） |
| 场景边界 / 进入点 | `Config.Map[*].def_x/def_y/rows/cols`（`config_map.json`） |
| NPC 名字 | `Config.Npc[*].name`（`config_npc.json`） |
| 任务目标 / 提交 NPC | `Config.Mission`（`mission_config.json`） |
| `SC_10201.mons` 字段顺序 | `protocol/manual.md` 的 `SCMapGird_10201` |

## ⚠ 关于坐标（**必须如实标注**）

原版服务端「剧情 NPC / 关卡怪物摆在哪」的**布置表不在客户端 APK 里**，
本阶段**无法取证**（`Config.Map[*].mons` 实测全表为空、`20011` 等剧情 NPC
既不在 `Config.MapNpc` 也不在任何场景的 `npcs` 里）。

因此本模块下发的坐标是**可复现的「仿真摆位」**，不是原版坐标：

> 以该场景**声明的进入点** `Config.Map[scene].def_x/def_y`（这是真实配置值，
> 且是玩家进场的落点，必然是可行走区）为锚点，用**黄金角螺旋**把多个目标
> 错开，并夹到 `[1, cols-2] x [1, rows-2]` 范围内。

每一项都带 `source='emulated'`，**不得对外表述为原版坐标**。
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TASK_DIR = os.path.join(os.path.dirname(HERE), 'analysis', '1.4.9', 'task')

# 视为「怪物类」条件的名字（来自 mission_util proto#7 的条件分派字符串表）
MON_CONDITIONS = ('fight_mon', 'kill_mon', 'kill_scene_mon', 'kill_type_mon',
                  'seal_mon', 'award_scene_mon', 'kill_cross_boss')


def _load(name, default):
    p = os.path.join(TASK_DIR, name)
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


class QuestSpawn(object):
    """按「当前场景 + 任务链在途任务」计算该下发哪些剧情 NPC / 怪物。"""

    def __init__(self, missions, enabled=True):
        self.enabled = enabled
        self.missions = {int(k): v for k, v in (missions or {}).items()}
        self.map_npc = _load('map_npc.json', {})          # npc_id -> {scene_id,x,y}
        self.config_map = _load('config_map.json', {})    # scene -> {...}
        self.npc_cfg = _load('config_npc.json', {})       # npc_id -> {name,...}

    # ---------------- 基础查询 ----------------

    def _scene(self, scene_id):
        return self.config_map.get(str(scene_id)) or {}

    def static_npc_ids(self, scene_id):
        """该场景**静态**（客户端本地已知）的 NPC id 集合。"""
        return set((self._scene(scene_id).get('npcs') or {}).keys())

    def place(self, scene_id, idx, spread=3):
        """仿真摆位：以场景声明进入点为锚的黄金角螺旋（见模块头注）。"""
        s = self._scene(scene_id)
        dx = s.get('def_x') or 30
        dy = s.get('def_y') or 30
        cols = s.get('cols') or 69
        rows = s.get('rows') or 69
        ang = math.radians((idx * 137.5) % 360.0)
        r = spread + 2 * (idx // 6)
        x = int(round(dx + r * math.cos(ang)))
        y = int(round(dy + r * math.sin(ang)))
        return max(1, min(int(cols) - 2, x)), max(1, min(int(rows) - 2, y))

    def _npc_name(self, npc_id):
        return (self.npc_cfg.get(str(npc_id)) or {}).get('name') or ('npc%d' % npc_id)

    # ---------------- 主逻辑 ----------------

    def story_npcs(self, scene_id, active_bids):
        """任务链需要、但客户端本地解析不了、且当前场景没有的**剧情 NPC**。"""
        if not self.enabled:
            return []
        local = self.static_npc_ids(scene_id)
        out, seen = [], set()
        for bid in sorted(active_bids):
            m = self.missions.get(int(bid)) or {}
            if m.get('type') != 1:
                continue
            npc_id = int(m.get('commit_npc_id') or 0)
            if not npc_id or npc_id in seen:
                continue
            if str(npc_id) in self.map_npc:          # 客户端本地就能解析 ⇒ 不用下发
                continue
            if str(npc_id) in local:                 # 场景里已经有了
                continue
            seen.add(npc_id)
            x, y = self.place(scene_id, len(out))
            out.append({'id': npc_id, 'bid': npc_id, 'type': 0, 'x': x, 'y': y,
                        'name': self._npc_name(npc_id),
                        'source': 'emulated', 'why': 'mission %d commit_npc' % bid})
        return out

    def target_mons(self, scene_id, active_bids):
        """`fight_mon` 类任务的目标怪物（`Config.Map[*].mons` 全表为空 ⇒ 必须服务端下发）。"""
        if not self.enabled:
            return []
        out, seen = [], set()
        for bid in sorted(active_bids):
            m = self.missions.get(int(bid)) or {}
            if m.get('type') != 1:
                continue
            prog = m.get('progress') or []
            if not prog or not isinstance(prog[0], (list, tuple)) or len(prog[0]) < 3:
                continue
            cond, tgt = prog[0][0], prog[0][1]
            if cond not in MON_CONDITIONS:
                continue
            try:
                tgt = int(tgt)
            except Exception:
                continue
            if tgt in seen:
                continue
            seen.add(tgt)
            x, y = self.place(scene_id, len(out), spread=8)
            out.append({'id': tgt, 'bid': tgt, 'type': 0,
                        'name': self._npc_name(tgt), 'realm': 0, 'mspd': 100,
                        'x': x, 'y': y, 'dir': 0, 'res_id': '', 'status': 0,
                        'source': 'emulated', 'why': 'mission %d %s' % (bid, cond)})
        return out

    def extras(self, scene_id, active_bids):
        """返回 (story_npcs, mons)。"""
        return (self.story_npcs(scene_id, active_bids),
                self.target_mons(scene_id, active_bids))
