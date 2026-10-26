# Phase B —— 剧情任务路线图（1.4.9）

> 数据来源：**唯一** —— `anzbao/jstm.apk`（1.4.9）的 `config_mission.luac`，
> 由 `tools/extract_mission_config.py` 提取为 `server/mission_config.json`（846 条）。
> 本文档由 `tools/build_quest_route.py` 生成数据文件，**不含任何编造内容**。
> `confidence` 只用：**CONFIRMED / VERIFIED / INFERRED / UNKNOWN**

---

## 一、★ 关键结论（都基于真实数据）

| # | 结论 | 依据 | confidence |
|---|---|---|---|
| 1 | **主线共 262 条**（`type=1` = `MIS_ZHU`），bid 从 **10010** 到 **12430** | `mission_config.json` 统计 | **CONFIRMED** |
| 2 | **全部 262 条主线 `auto_accept = 1`** ⇒ **主线全部自动接取** | 逐条统计 | **CONFIRMED** |
| 3 | 因此 `accept_npc_id` **普遍为 0** ⇒ **主线不从 NPC 接取** | 逐条统计 | **CONFIRMED** |
| 4 | **NPC 的作用在"提交"**：**188 / 262** 条主线有 `commit_npc_id ≠ 0` | 逐条统计 | **CONFIRMED** |
| 5 | **48 条主线带完成条件**（`progress` 非空） | 逐条统计 | **CONFIRMED**（条件值 **VERIFIED**：Phase 5G 实测过 `fight_mon`） |
| 6 | **配置里没有 `next_task_id` 字段**（36 字段全部列出，无任何 `next`） | 字段统计 | **CONFIRMED** |
| 7 | 主线 **按 `lev` 自然分段**：lev1=1、lev2=2、lev3=7、lev4=4、lev5=4、lev6=3、lev7=1、lev8=2… | 分组统计 | **CONFIRMED** |

---

## 二、§十三「下一任务从哪来」的判定

| 候选 | 判定 | 依据 |
|---|---|---|
| **A. 配置里直接指定 `next_task_id`** | ❌ **否证** | `Config.Mission` **36 个字段里没有**任何 `next` 类字段 |
| **D. 客户端本地剧情表决定** | ❌ **否证** | 没有独立剧情表；`config_mission.luac` 就是全部任务定义 |
| **B. 服务端动态决定** | ⚠️ **可能**（无法直接证明） | 我们**没有原版服务端代码** |
| **C. 按等级/剧情阶段决定** | ⚠️ **最符合数据形态** | 262 条主线**按 `lev` 自然分段**，且 bid 递增（10010→10020→10030→10040→10051…） |

**⇒ 结论标 `INFERRED`**：**下一任务 = 主线序列中 bid 升序的下一条，且其 `lev ≤ 玩家等级`。**
**这不是"原版就是这样"，而是"数据形态支持的最简解释"。**

**⇒ 当前服务器实现（`mission_chain`）正是这一规则**（bid 升序 + `lev ≤ 等级` + 第一个未完成作解锁指针），
**与数据结构吻合**；Phase 5 实测也证明该规则能跑通（链随提交前移）。

---

## 三、主线路线（前 30 条，完整 262 条见 `story_quest_route.json`）

| # | task_id | name | lev | submit_npc | 条件 | next |
|---|---|---|---|---|---|---|
| 1 | 10010 | 斗罗魂师 | 1 | 10030 | — | 10020 |
| 2 | 10020 | 切磋魂技 | 2 | 0 | `fight_mon` | 10030 |
| 3 | 10030 | 武魂觉醒 | 2 | 20011 | — | 10040 |
| 4 | 10040 | 武魂觉醒 | 3 | 10030 | — | 10051 |
| 5 | 10051 | 武魂觉醒 | 3 | 0 | — | 10052 |
| 6 | 10052 | 武魂觉醒 | 3 | 0 | — | 10053 |
| 7 | 10053 | 武魂觉醒 | 3 | 0 | — | 10054 |
| 8 | 10054 | 武魂觉醒 | 3 | 0 | — | 10055 |
| 9 | 10055 | 武魂觉醒 | 3 | 0 | — | 10060 |
| 10 | 10060 | 斗罗魂师 | 3 | 10030 | — | 10070 |
| 11 | 10070 | 巫风挑战 | 4 | 0 | `fight_mon(20002)` | 10071 |
| 12 | 10071 | 巫风挑战 | 4 | 0 | `fight_mon(20022)` | 10072 |
| 13 | 10072 | 巫风挑战 | 4 | 0 | `fight_mon(20040)` | 10080 |
| 14 | 10080 | 巫风挑战 | 4 | 0 | — | 10090 |
| 15 | 10090 | 猎取魂环 | 5 | 0 | — | 10091 |
| 16 | 10091 | 猎取魂环 | 5 | 0 | — | 10092 |
| 17 | 10092 | 猎取魂环 | 5 | 0 | `collect_elem(20001)` | 10100 |
| 18 | 10100 | 猎取魂环 | 5 | 0 | `fight_mon(20003)` | 10110 |
| … | … | … | … | … | … | … |

**⇒ 叙事线索清晰可见**：`斗罗魂师`（报到）→ `切磋魂技` → `武魂觉醒` → `巫风挑战` → `猎取魂环` …
**⇒ 这是一条**连续的主线剧情**，与"史莱克学院"开局吻合。**

---

## 四、每条任务的字段与证据强度（`story_quest_route.json` 逐条给出）

| 字段 | 来源 | confidence |
|---|---|---|
| `task_id` / `task_name` / `task_desc` / `task_type` / `accept_level` | 配置直读 | **CONFIRMED** |
| `accept_npc_id` / `submit_npc_id` / `accept_talk` / `submit_talk` | 配置直读 | **CONFIRMED** |
| `auto_accept` / `auto_commit` / `is_drama` / `abandon_flag` | 配置直读 | **CONFIRMED** |
| `condition` / `target_monster_id` / `target_count` | 配置 `progress[0]` 解码 | **VERIFIED**（Phase 5G/5I 实测） |
| `reward_assets_raw` | 配置直读 | **CONFIRMED** |
| `previous_task_id` / `next_task_id` / `chapter` | **按 bid 升序 + lev 分段推断** | **INFERRED** |
| `accept_npc_name` / `submit_npc_name` | **未查 `config_npc`** | **UNKNOWN** |
| `accept_scene_id` / `submit_scene_id` / `target_scene_id` | 配置里**无此字段** | **UNKNOWN** |
| `target_x` / `target_y` | 配置里**无此字段**（`missionGoto` 用条件+目标 id 现场寻路） | **UNKNOWN** |
| `target_npc_id` | 配置里**无此字段** | **UNKNOWN** |
| `reward_exp` / `reward_gold` / `reward_item` | 需经 `AssetsEnToCode` 解码 `award_assets` | **VERIFIED**（解码逻辑已实测） |
| `auto_path_data` | `missionGoto` 内部逻辑，未反汇编完 | **UNKNOWN** |

**⇒ "目标坐标 / 目标地图"在配置里**不存在**（无该字段）——
说明**寻路不是靠配置坐标，而是靠"条件 + 目标 id"现场解析**（`missionGoto`）。
这与 Phase 5 的发现一致：`missionGoto` 拿 `fight_mon`/`collect_elem` 当"要去的地方"。**

---

## 五、本阶段仍缺（指向 Phase F / 后续）

| 缺口 | 说明 |
|---|---|
| **目标场景/坐标** | 配置里没有 ⇒ 必须**看懂 `missionGoto`**（68KB 的 `mission_util proto[7]`）才知道它如何定位目标 |
| **`config_npc` 里的 NPC 名字** | `submit_npc_id`（如 10030=周漪）已能对上，但需**批量导出** NPC id→名字 表 |
| **`accept_scene_id` / `submit_scene_id`** | 无此字段 ⇒ 可能由 NPC 决定（NPC 属于某地图） |
| **`progress` 第 2 行** | 仍是 UNKNOWN |
| **74 条 `commit_npc_id=0` 的主线** | 完成方式未知（可能自动提交，`auto_commit` 需逐条看） |

---

## 六、交付物

| 文件 | 内容 |
|---|---|
| **`story_quest_route.json`** | **262 条主线**逐条记录（含 `confidence`），`next_task_source` 标为 `INFERRED` |
| **`story_quest_route.md`** | 本文件（结论 + 前 30 条路线表 + 证据强度表） |
| `tools/build_quest_route.py` | 生成脚本（可重跑核对） |
| `tools/extract_mission_config.py` | 上一步的全表提取脚本 |

---

# 补编（2026-09-17）：场景 / 坐标 / NPC 名字**已补全**

> 上一版把 `accept_scene_id / submit_scene_id / target_scene_id / target_x / target_y /
> accept_npc_name / submit_npc_name` **全部标为 UNKNOWN**。
> 本轮从 1.4.9 APK 又提取到三张表，**其中 128/188 条主线的提交位置已可给出真实坐标**。

## 七、新增数据源（**CONFIRMED**，均为 1.4.9 APK 直读）

| 表 | 文件 | 内容 | 提取脚本 | 提取结果 |
|---|---|---|---|---|
| `Config.MapNpc` | `config_map_npc.luac` | `npc_id -> {scene_id, x, y}`（54 个唯一 NPC） | `tools/extract_map_npc.py` | `map_npc.json` |
| `Config.MapSceneDoors` | `config_map_npc.luac` | 场景传送图（18 条） | 同上 | `map_scene_doors.json` |
| `Config.Map` | `config_map.luac` | **124 个场景**：`name/rows/cols/def_x/def_y` + `npcs/mons/elems` | `tools/extract_config_map.py` | `config_map.json` |
| `Config.Npc` | `config_npc.luac` | **456 个 NPC**：`name/face/res_id/talk/talk2/button` | `tools/extract_config_npc.py` | `config_npc.json` |
| `Config.Mon` | `config_mon_data.luac` | 怪物定义（**无坐标**） | `tools/extract_config_mon.py` | `config_mon.json` |

**`Config.MapNpc` 与 `Config.Npc` 的对应关系已被代码侧证实**：
`mission_util` proto#38 `moveToNpc` 读的正是 `Config.MapNpc[id][1..3]`（`TGETB 1/2/3`），
与提取出的 `{scene_id, x, y}` 三元组一一吻合。

## 八、字段置信度**更新表**

| 字段 | 上一版 | 本版 | 依据 |
|---|---|---|---|
| `submit_scene_id` / `submit_x` / `submit_y` | UNKNOWN | **CONFIRMED（128 条）** | `Config.MapNpc` 直读 |
| `submit_npc_name` | UNKNOWN | **CONFIRMED** | `Config.Npc[name]` |
| `target_scene_id` / `target_x` / `target_y`（`collect_elem` 类） | UNKNOWN | **仍 UNKNOWN** | 条件目标 id 不与 `Config.Map[*].elems` 同域，未对上 |
| `target_scene_id` / `target_x` / `target_y`（`fight_mon` 类，38 条） | UNKNOWN | **仍 UNKNOWN** | `Config.Map[*].mons` 实测**全表为空** |
| `reward_exp` / `reward_gold` / `reward_coin` | VERIFIED | **VERIFIED** | `award_assets` 解码 + 实测发放 |
| 剧情 NPC（`commit_npc_id` 为 20xxx 的 60 条） | UNKNOWN | **仍 UNKNOWN** | 见 `task_story_scene_finding.md`：它们属于**剧情场景**，客户端 APK 里没有该场景的编排表 |

## 九、统计（`tools/build_quest_route2.py` 输出）

```
主线 262 条
  submit_resolved     = 128   ← 提交 NPC 在 Config.MapNpc 里，坐标 CONFIRMED
  submit_unknown      =  60   ← 20xxx 剧情 NPC，需剧情场景（UNKNOWN）
  target_mon_unknown  =  38   ← fight_mon 目标，mons 全表为空
  target_npc_unknown  =   4
```

**⇒ 直接结论：光靠客户端配置，128 条主线（约 49%）的提交目标坐标是现成的；
剩下 60 条卡在"剧情场景编排表"，38 条卡在"怪物摆位表"——**
**这两张表都不在 APK 里，属原版服务端数据，本阶段无法取证。**

## 十、生成脚本（可重跑）

| 脚本 | 作用 |
|---|---|
| `tools/build_quest_route2.py` | 生成带**真实坐标**的 `story_quest_route.json`（本轮实际使用） |
| `tools/build_npc_scene_map.py` | 生成 `npc_scene_position_map.md`（NPC/场景/坐标全表 + 可寻路性判定） |

