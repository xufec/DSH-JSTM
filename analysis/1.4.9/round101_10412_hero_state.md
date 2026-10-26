# R101：找到最可能的根因 —— **`SC_10412`（伙伴状态推送）我们从来没发过**

> 实验 C 的结果是 **"仍空"**。这不是坏消息 —— 它**排除掉了一个数据源**，
> 并把我引到了真正的候选：**`SC_10412`（`SCHeroState`）**。
> 已实现并验证。**这一轮还顺手纠正了 R98 实验 C 的判据缺陷**。
> **时间**：2026-09-29 00:35 – 01:00。

---

## 一、实验 C 的结论（虽"失败"，但**信息量很大**）

把 `10401.hero_bag` 从 **18 → 1**，界面**毫无变化** ⇒ **界面不靠 `10401` 的条数**。

### ★ 但我也要承认实验设计有问题

界面**本来就空**。此时"把 18 减到 1"**区分不了**两种情况：
- 界面**不读** `10401`
- 界面**读** `10401`，但 18 条**都被过滤掉了**（1 条自然也被过滤）

⇒ **正确做法是"打空整张表"或"换源"**，而不是"减少条目"。
已补上 `hero15_limit=0`（把 `11215` 打空）作为修正后的对照实验。

---

## 二、★★★ 真正的候选：`SC_10412`

翻 `10405~10412` 的规格时，有三条**`SC`-only**（只有服务端→客户端，没有 CS）：

| cmd | 规格 | 含义 |
|---|---|---|
| **`10412`** | **`SCHeroState_10412{hero_bid:uint32, state:uint8}`** | ★ **伙伴状态推送** |
| `10408` | `SCHeroUpDataChipNum_10408{hero_chips:table(hero_bid:u8, chip:u32)}` | 碎片数推送 |
| `10407` | `CSHerosAll_10407{args:table(hero_bid,power)}` → `SCHerosAll_10407{hero_error:table(bid)}` | 是 CS+SC（客户端来问）|

### 三条独立的证据都指向 `state`

1. **协议**：`SC_10412{hero_bid, state}` **只有 SC、没有 CS** ⇒ 它是**服务端主动推**的，
   客户端**永远不会来问** ⇒ 我们不发，客户端就**永远不知道**任何一个伙伴的 `state`。
2. **客户端字节码**：`game/hero/hero_data.luac` 的 proto [12] 里只有 **`state`** →
   `getHeroByBid` / `getHeroList`；
   而 **`HeroVo` 的 28 个字段里根本没有 `state`**（R91 已确认）⇒ 它是 `HeroData` 的
   **独立字段**，由**独立通道**维护 —— 那条通道就是 `changeHeroSatus`/`10412`。
3. **消费方**：`form_data.luac` proto#8 的"可选英雄"走 `HeroCtrl:getHeroListData()`，
   而它遍历 `Config.PartnerBase` 并用 `is_show`/`career`/`sequence` 处理 ——
   结合实验 C 的否定结果（不靠 `10401` 条数），**`state` 是剩下最可能的过滤键**。

⇒ **我们从来不推 `10412`** ⇒ 每个伙伴的 `state` 在客户端**从未被设置**
⇒ `getHeroListData()` 可能因此筛不出人 ⇒ **伙伴列表空、阵型"可选英雄"空**。

---

## 三、修复

```python
# 10401 应答之后，为每个已拥有伙伴补推一条 SC_10412
_st = _hero_state(self.cfg)                 # 与 10401 用同一个值，两条通道不能自相矛盾
for h in heros:
    sendall(pack_frame(10412, w_u32(h['bid']) + w_u8(_st)))
```

★ 为什么紧跟在 `10401` 之后：`10401` 负责把伙伴**建进 `hero_list`**，
  `10412` 负责**给每条设置 `state`** —— 顺序自然、且客户端此时已有这些伙伴。

### 实测

```
收到 19 条: 10401(len=274), 10412(bid=30800,state=1), 10412(bid=31300,state=1),
          10412(bid=32100,state=1), 10412(bid=32200,state=1), 10412(bid=32300,state=1) ...
★ 10412 条数 = 18  ⇒ PASS
```

---

## 四、★ 请你复测（**这次必须重启客户端**）

`10412` 是**在拉 `10401` 时推的** ⇒ 客户端要**重新登录**才会收到那一批推送。
另外 18 个伙伴的 `state` 是 `1`（配置 `hero_state`，R91 起的值）。

> **步骤**：MuMu 里 force-stop 客户端 → 重开 → 进游戏 → 再开伙伴界面。

| 结果 | 结论 / 下一步 |
|---|---|
| **列表出现了** | ✅ 根因确认：缺口是 `SC_10412` 状态推送 |
| **仍空** | 那就用**修正后的对照组**：我开 `hero15_limit=0`（把 `11215` 打空）—— 若界面**照旧**，`11215` 也被排除；剩下的候选只有 `10407`（`CSHerosAll`）与客户端本地逻辑 |

★ 我随时可以切换到任一实验（全部**秒级生效、不必重登**，除了 `10412` 那批需要重新登录）：
```
?name=hero_bag_limit&val=1     # 10401 只回 1 个
?name=hero15_limit&val=0       # 11215 打空（修正后的对照）
?name=hero_state_override&val=2 # 覆盖 state
?name=form_pos_limit&val=2      # 14000 上阵位只回 2 个
```

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽** / CS 2463-0 / SC 静态 79+1空-0 / SC 在线 **79-79** / 专用 **70-70** / 门禁 E **PASS** |
| 回归（12 项） | `verify_formation` / `verify_partner_list` / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |
| 实验开关 | 已全部复位（`hero_bag_limit=0 / hero_state=0 / form_pos_limit=0 / hero15_limit=-1`）|

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `10401` 应答后**补推 `SC_10412`**（每个伙伴一条 state）；`11215` 接 `hero15_limit`；`/DSH_ADMIN/exp` 允许键 +1 |
| `tools/_fix_r101_hero_state_push.py` | 插入脚本 |
| `server/mock_server.py.bak_r101` | 改前备份 |
| `analysis/1.4.9/round101_10412_hero_state.md` | 本报告 |

---

## 七、一句话

> 实验 C 的"仍空"**排除了 `10401` 条数**这条路，并暴露出**我的实验判据有缺陷**（该打空/换源，不是减条数）。
> 顺着 `SC`-only 的命令一查就找到了真正的缺口：**`SC_10412{hero_bid, state}` 是服务端主动推的伙伴状态**，
> 而**我们从来没发过** ⇒ 客户端每个伙伴的 `state` 从未初始化。
> 三条独立证据（协议只有 SC、`HeroVo` 没有 `state`、`getHeroListData` 的消费路径）都指向它。
> 已在 `10401` 之后**逐条补推 18 条 `10412`**（实测 PASS）—— **重启客户端**再开伙伴界面看结果。
