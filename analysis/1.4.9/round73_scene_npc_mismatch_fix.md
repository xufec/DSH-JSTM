# R73：修复「地图 NPC 不匹配」——场景 NPC/怪改为**按场景下发**

> 用户报障：**有戴浩可以点击战斗，但是没有圣灵教精英，地图 NPC 不匹配**。
> 根因是两处**写死的全局表**，与场景无关。本轮全部改成按场景取，并在真机验证通过。
> **时间**：2026-09-29 18:15 – 18:30。

---

## 一、根因：两张表**永远发 10001 的**

`scene_quest_extras(cfg, scene_id)` 里：

```python
npcs = list(cfg.get('npcs', []))        # ← config.json 写死的 25 个（= 史莱克城的）
mons = static_mons(cfg, scene_id)       # ← 名字带 scene_id，但函数体**根本没用它**
```

`static_mons()` 只读 `cfg['mons']` —— 那是 **Phase D 手工加的测试怪 `20001 戴浩`**
（本意给**出生场景**做战斗验证），却跟着玩家进了挂机图。
于是：**进乾坤日月谷后，屏幕上还是史莱克城的人 + 戴浩，独独不见挂机怪。**

对照真数据（`analysis/1.4.9/task/config_map.json`）：

| 场景 | `Config.Map[scene].npcs` | `.mons` |
|---|---|---|
| 10001 史莱克城 | **25** 个（10010…50001） | 0 |
| 10005 乾坤日月谷 | **3** 个（10310/10320/10330） | 0 |

---

## 二、修复：三个函数按场景取值

新增 / 改写（`server/mock_server.py`）：

```python
def scene_npcs(cfg, scene_id):
    """按场景取 NPC；场景不在 Config.Map 里才回退 cfg['npcs']（不制造空白场景）。"""
    tbl = (map_cfg() or {}).get(str(scene_id), {}).get('npcs') or {}
    if not tbl:
        return list(cfg.get('npcs', []))
    return [{'id': b, 'bid': b, 'type': 2, 'x': …, 'y': …, 'name': ''} for b, v in tbl.items()]

def scene_mons(cfg, scene_id):
    """按场景取怪；config.json 的测试怪**只在出生场景**补上（保住 10001 的戴浩）。"""
    out = [<Config.Map[scene].mons 里每只，name/res_id 由 mon_def 补齐>]
    if scene_id == cfg['spawn']['bid']:
        out += <static_mons 中未重复的>
    return out
```

`scene_quest_extras()` 的静态部分改为走这两个函数。

### ★ 另外一道闸：剧情目标怪**只在出生场景刷**

用户看到的戴浩**还有一个来源**——`quest_spawn.target_mons(scene_id, active)`：

```
mission 10020「切磋魂技」 progress = [["fight_mon", 20001, 1], …]
```

`mission_config` 里**没有任何场景字段**（只说"打 20001 戴浩"，不说"在哪儿打"），
而 `target_mons` 目前**并不按场景过滤** ⇒ **每张图**都会刷出这只剧情怪。

在拿到 per-mission 场景数据之前，采取**保守且可解释**的做法：

```python
if int(scene_id) != 出生场景 and extra_mons:
    log(... '非出生场景 ⇒ 不刷剧情目标怪 ...')
    extra_mons = []          # 原版这些剧情切磋都在史莱克城
```

---

## 三、★ 真机验证（通过）

```
[18:20:05] << 10200 SCRoleEnter bid=10001 (54,59)
[18:20:05] << 10201 SCMapGird roles=1 npcs=25 mons=1 elems=2 (657 bytes)   ← 史莱克城：自己的 25 NPC + 戴浩（保留）
[18:20:05] .. 切场景 10001 -> 10005：坐标改用目标图默认点 (10,58)
[18:20:05] << 10200 SCRoleEnter bid=10005 (10,58)
[18:20:05] << 10201 SCMapGird roles=1 **npcs=3 mons=0** elems=2 (161 bytes)  ← ★ 乾坤日月谷：自己的 3 个 NPC，**0 只怪**
[18:20:23] << 15402 补推 mission_bid=10010 map_bid=10005 (10,58)
```

探针：

```
t=ghcreate mon_bid_10105_cfg_table_cfg_map_10005_scene_10005_cfgMon_table_hasMon_true
t=ghcreate done_mon_id_10052        ← ★ 挂机怪「圣灵教精英」照旧生成（客户端本地建）
```

**⇒ 地图 NPC 现在与场景一致**：乾坤日月谷里**没有戴浩**、只有该图自己的 3 个 NPC；
挂机怪由 `SC_15402` 在客户端本地创建（`mon_id=10052`）。
对照本地直调：

```
场景 10001: npcs=26 [10010…20011] | mons=1 [(20001,'戴浩')]
场景 10005: npcs=4  [10310,10320,10330,20011] | mons=0 []
```

---

## 四、下一步（`fight()` 的触发）—— 需要"看到屏幕"才能推进

R72 已查明：`CS_15202` 由 **`SCENE_CLIENT_ELEM_CLICK`（玩家点击地图里的怪）** 触发。

本轮我试了 5 个屏幕点（含正中心，因为怪生成在**玩家同一格**）：

```
tap(1280,720) / (1240,700) / (1320,740) / (1280,660) / (1220,760) → 均无 15202
```

但**点击是生效的**：日志里出现 `>> cmd=10204` 且坐标在变（(16,58)→(17,58)→(16,57)）
⇒ 输入进到了游戏、角色在**走路**（说明点到了地面，没点到怪的精灵）。
**怪到底画在屏幕哪个像素**，我这边拿不到可信观测（本环境 `screencap` 抓不到游戏屏，见 R67）。

### 所以请你在屏幕上做这一步

> 进乾坤日月谷后，地图上（或就在你角色脚下/旁边）会有那只挂机怪
> —— **用鼠标点它一下**。服务端对 `CS_15202` 的应答（R69 已补）**早就备好了**。

点完告诉我，我会从日志确认 `>> cmd=15202` → `<< 15202 code=1` 并接着把后续（自动开打 / `15403` 杀怪上报 / 轮次结算）接上。

### 若想让我自己也能点到（下一轮可选）

给探针再加一条上报：**怪的屏幕坐标**（读 `vo` 的世界坐标 + 摄像机变换）。这样"点怪"就能脚本化，
不必依赖截图。属于 APK 重打包（约 5 分钟），和 R65 那次同一套路。

---

## 五、全量验证 / 环境

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 170 / 默认 64 / 未开放 22）、CS 2463-0、SC 静态 85+1空-0、SC 在线 **86-86**、专用 **63-63**、门禁 E **PASS** |
| 回归 | `verify_guaji` / `level_consistency` / `race` / `arena` / `dungeon` / `mission_hook` **全 PASS** |
| 环境 | `stderr` **0 字节**；9000 恰好 1 监听；玩家 lev=70 / gold 833166 / 背包 27 |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `scene_npcs()` / `scene_mons()`；`scene_quest_extras()` 改用它们；新增"剧情目标怪只在出生场景刷"的闸 |
| `analysis/1.4.9/round73_scene_npc_mismatch_fix.md` | 本报告 |

---

## 七、一句话

> **两张表（NPC、怪）以前永远发 10001 的**，所以进了乾坤日月谷还是史莱克城的人 + 戴浩。
> 现在按 `Config.Map[scene]` 下发：**10005 = 3 个自己的 NPC、0 只怪**（戴浩只留在出生场景），
> 挂机怪照旧由 `SC_15402` 生成。剩下只有"点那只怪"这一下 —— 服务端的 `15202` 应答已经就位。
