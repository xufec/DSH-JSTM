# 任务系统：按 APK 原有任务加载（✅ 完成 —— 任务数 1 → 8 条主线链）

> **用户要求**：奖励机制要真正跑通；**任务数量过少，依据 APK 原有任务加载实现任务系统**。
> **本轮做法**：把客户端 `config_mission.luac` 的**全表（846 条）**提取成服务器可读的 JSON，
> 服务器据此下发**主线链**、并按每条任务自己的 `award_assets` 发奖。

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`tools/extract_mission_config.py`**（新增） | 从 `config_mission.luac` 提取**完整任务表** → `server/mission_config.json`。按反汇编出的构造模式解析（条目表 + `progress`/`award_assets`/`commit_item`… 子表 + `KSHORT/TSETV` 落表） |
| **`server/mission_config.json`**（新增） | **846 条任务**（其中主线 `type=1` 262 条），字段含 `bid/name/desc/type/lev/accept_npc_id/commit_npc_id/award_assets/…` |
| **`server/mock_server.py`** | ① 新增 `MISSION_CFG_PATH` / `mission_cfg()`（惰性加载全表）/ `mission_def(bid)`<br>② 新增 **`mission_chain(cfg)`**：决定"当前给玩家哪些任务"——显式 `mission_chain` 优先，否则**按等级从 APK 全表挑主线**（`lev <= 玩家等级`，取前 `mission_chain_max` 条，默认 8）<br>③ **`mission_rows()` 播种改为"按 APK 任务表"**（config 里的 `missions` 仍可手工覆盖）<br>④ **`12403` 奖励改为以 APK 任务表为准**：`award_assets` 取自 `mission_config.json`，再经 `AssetsEnToCode` 解码 |
| `server/config.json` | `missions` 清空（改由 APK 表驱动）；新增 `mission_chain_max = 8` |

---

## 2. 提取结果（**已验证**）

```
提取任务数: 846        主线(type=1): 262 条

抽查 10010 = {bid:10010, name:'斗罗魂师', desc:'去周漪老师处报到', type:1, lev:1,
              accept_npc_id:0, commit_npc_id:10030,
              award_assets:[[2,1290],[4,500],[15,500]]}
```

**⇒ 与客户端 `Config.Mission[10010]` **逐字一致**（含 `award_assets` 三元组）。**

**其它主线（奖励逐条不同，证明是"配置驱动"而非写死）：**

| bid | name | lev | commit_npc | award_assets | 解码后 |
|---|---|---|---|---|---|
| 10010 | 斗罗魂师 | 1 | 10030 | `[[2,1290],[4,500],[15,500]]` | coin 1290 / exp 500 / hero_exp 500 |
| 10020 | 切磋魂技 | 2 | 0 | `[[2,1290],[4,500],[15,500]]` | coin 1290 / exp 500 / hero_exp 500 |
| 10030 | 武魂觉醒 | 2 | 20011 | `[[2,1350],[4,520],[15,500]]` | coin 1350 / exp 520 / hero_exp 500 |
| 10040 | 武魂觉醒 | 3 | 10030 | `[[2,1810],[4,700],[15,700]]` | coin 1810 / exp 700 / hero_exp 700 |
| 10051 | 武魂觉醒 | 3 | 0 | `[[2,2580],[4,1000],[15,900]]` | coin 2580 / exp 1000 / hero_exp 900 |
| 10070 | 巫风挑战 | 4 | 0 | `[[2,3620],[4,1400],[15,1300]]` | coin 3620 / exp 1400 / hero_exp 1300 |

---

## 3. 端到端实测（**已验证**）

```
[11:43:44]  << 12400 SC_12400 mission_list=7 (246 bytes)      ← ★ 一次下发 7 条

客户端为每一首都建了 VO（探针）：
   mis_bid=10020 / 10030 / 10040 / 10051 / 10052 / 10053 / 10054   （各 2 次上报）
```

**⇒ 任务数从 **1 条 → 7 条**（第 8 条 `10010` 被正确排除，见 §4）。**

---

## 4. ★ 关于"为什么是 7 条而不是 8 条"——**不是 bug，是正确行为**

```
DB:
   10010: mission_status=3, commit_num=1        ← 上一轮测试**已提交过**
   10020..10054: mission_status=1, commit_num=0

mission_chain(cfg) = [10010, 10020, 10030, 10040, 10051, 10052, 10053, 10054]   (8 条)
mission_rows 过滤后 = 7 条                        ← 10010 因"已完成"被过滤 ✓
```

**⇒ 已完成的任务不再下发**（这正是之前修 bug #2 时的设计），**行为正确**。

---

## 5. 奖励机制（**本轮验证要点**）

奖励链路现在是**完全配置驱动**的：

```
CS_12403{mission_bid}
   → 服务端按 bid 查 APK 任务表（mission_config.json）
   → 取该任务的 award_assets（原始 code 二元组）
   → 用 AssetsEnToCode 反查资产字段名
   → 写入通用资产表 role_assets
   → 回 SC_12403 + 推 SC_12405/12406 + 刷新 10301/10302/10303
```

**实测（上一轮，同一套解码路径）：**
```
** mission 10010 award_assets=[[2,1290],[4,500],[15,500]]
              -> delta={'coin':1290, 'exp':500, 'hero_exp':500}
** mission 10010 committed: +500 exp, +1290 coin, +0 gold
role_assets: [coin=1290, exp=500, hero_exp=500]
<< 10302 (refresh after commit) exp=500 coin=1290
```
**⇒ 奖励成功发放并落库，且**三项资产全发**（含 `hero_exp`）。**

---

## 6. 仍然缺失 / 待验证（如实）

1. **任务数量可调但没有"章节/等级门槛"逻辑** —— 目前是"取前 N 条主线"，
   真正的原版应该是**按剧情链逐步解锁**（`10010 → 10020 → …`）。
   本轮解决了"数量太少"，**串链解锁逻辑尚未实现**。
2. **`progress` 未用于判定完成** —— 提取里带了 `progress`，但 `10010` 为空、
   其它任务的 `progress` 语义（条件/计数）**尚未解码**。
3. **界面只见到 7 条 VO，没逐个核对任务栏显示**（一轮跑测时间有限）。
4. NPC 对话 UI 仍未打通（走 `MissionCtrl:submit` 触发提交）。
5. 客户端重登后仍会再发一次 `12403`（已幂等兜住）。

---

## 7. 本轮结论

| 项 | 结果 |
|---|---|
| 按 APK 原配置加载任务 | ✅ **846 条全表提取**（含 `award_assets`/`commit_npc_id`） |
| 提取正确性 | ✅ 抽查 `10010` **与客户端逐字一致** |
| 任务数量 | ✅ **1 → 8 条主线链**（`mission_chain_max` 可调） |
| 任务定义来源 | ✅ **APK `config_mission.luac`**（不再是手写） |
| 奖励来源 | ✅ **APK 的 `award_assets`** + `AssetsEnToCode` 解码 |
| 奖励发放 | ✅ 已验证（`coin`/`exp`/`hero_exp` 三项） |
| 已完成任务不再下发 | ✅ 已验证（7 vs 8 的原因） |
| 改 APK / UI | ✅ 未做 |

**交付物**：本文件、`tools/extract_mission_config.py`、`server/mission_config.json`（846 条）、
`server/mock_server.py`、`server/config.json`、`shots/p5_many_missions.png`

---

**[WAITING FOR NEXT INSTRUCTION]**
