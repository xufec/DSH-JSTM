# 核心玩法候选评估（P1 未实现族）— 侦察结论

> 日期：2026-10-06 | 目的：为"完善其他核心玩法"选定**证据充分、可端到端闭环**的目标。
> 方法：`cmd_table` + `fields.json` 规格 + `server/cfg` 配置 + **客户端 luac 反汇编**。
> 纪律：**配置里没有的数值一律不编造**；每条都给出"可直接实现 / 需再取证 / 已否决"。

---

## 可用基础设施（已具备，无需新建）

| 能力 | 位置 | 说明 |
|---|---|---|
| 幂等发奖 | `server/reward/service.py` → `grant(rid, awards, reference_id, source)` | **`reward_log` 表幂等**：同一 `(rid, reference_id)` 只发一次 ✓ |
| 命令注册 | `server/core/dispatch.py` → `@register(cmd)` | 新模块直接注册 |
| 帧编码 | `server/protocol/frame.py` → `w_u8/w_u16/w_u32/w_str/pack_frame` | |
| 扣费 | `server/currency/service.py` → `db_add_assets` | |
| 入包 | `server/inventory` / `db_bag_add` / `addItemInBagCode` | |

---

## 一、★ 推荐目标：**开服成长计划**（`config_growth_target_data`）— 可直接实现

**配置（CONFIRMED，全数值）**：`server/cfg/config_growth_target_data.json`
```
GrowthTarget[day] = {
  charge_gold : <累计充值门槛(钻石)>,
  login_reward: {1:[null,bid,cnt,?], 2:...},     ← 登录奖励
  charge_reward:{1:[null,bid,cnt,?], ...},       ← 充值奖励
}
```
实测样例：day1 charge_gold=80, login_reward={36500×5, 36006×3}, charge_reward={25104×3, 36010×1, 25327×5}
另有 `TodayTarget` / `HalfDiscountBuy` / `RewardGroup`。

**客户端（CONFIRMED，反汇编 `game/action/kaifu/action_kaifu_growplan_item.luac`）**：
- 读 `Config.TodayTarget`、`Config.GrowthTarget[day].login_reward`、`.charge_reward`
- 文案含「累计充值{0}元」(=`charge_gold`)、「领取」按钮
⇒ **每天两档：登录奖励（无条件）+ 充值奖励（需累计充值达标）**

**协议（现有 stub）**：`30501{day:u8}` / `30502{day:u8}` / `30506{target_id:u32}` / `30507{day:u16}`
→ 均返回 `{result:u8, msg, items:table}`

**⚠ 唯一剩余歧义**：`30501/30502/30506/30507` 哪条对应 `login_reward`、哪条对应 `charge_reward`。
需再做一步取证（客户端 `action_kaifu_growplan.luac` 的 `sender3050x` 调用点），**不猜**。

### ★ 已定位到"同按钮按 type 分派"（本轮新证据）

反汇编 `action_kaifu_growplan_item.luac` proto（L1884-1945，`knum=[1,2,3,4,6,7]`）：
**同一个领取按钮按 `self.type` 分派到不同命令**：

| `type` | 动作 |
|---|---|
| 1 | `sender30501(day)` |
| 2 | **不发领取**：Fire `OPENVIEW/YUANBAO` + `GROWPLAN_CLOSE_VIEW` ⇒「去充值」跳转 |
| 3 | `sender30507(day)` |
| 4 | `sender30502(day)` |
| 6 | `sender30506(target_id)`（配合 `TodayTarget`，文案「请先完成今日全部目标！」）|
| 7 | （同类分支，未展开）|

另：`action_kaifu_growplan.luac` 用 `sender30500`（L211）与 `sender30503(day)`（L820）。

⇒ **最后一步取证**：读 `self.type` 的**赋值处**（item 的 574/1631 两段 proto：一为奖励行、一为「累计充值…元」行）
即可确定 `login_reward ↔ 命令` 与 `charge_reward ↔ 命令`。
`type=2` 是"去充值"而非领取，**不要把它也实现成发奖**（这是个容易踩的坑）。

**实现方案（取证后即可落地）**：
```
新模块 server/growth_target/ （或并入 server/activity/）
  service.py : growth_cfg() 读 config_growth_target_data
               db_gt_target_init(): role_growth_target(rid, day, login_got, charge_got)
               claim_login(rid, day)  → 校验未领 + 发奖(reference_id='gt:login:{rid}:{day}')
               claim_charge(rid, day) → 额外校验 累计充值>=charge_gold
  handler.py : @register(30501/30502/…)
帧: {result:u8(1=成功), msg:string, items:table{bid:u32,cnt:u32}}
幂等: reference_id 走 RewardService.grant（重复点击/reconnect 不会重复发）
测试: tools/test_growth_target.py — 领一次成功、再领失败、重启后仍失败
```

---

## 二、已评估但**否决/暂缓**的候选（附原因，避免重踩）

| 候选 | 结论 | 原因（证据） |
|---|---|---|
| **答题** `16100/16101/16102/16103`（+灯谜 `1611x`） | **否决** | 协议完整（`16102` 回 `correct_answer:u8`），但**配置无答案键**：`config_answer.Question` 只有 `content + a/b/c/d`（239 题），无任何"正确项"字段；`config_lantern_answer` 同样只有 `a1..a16 + answer_len`。⇒ 服务端无法判定对错，**实现必然编造** |
| **刮刮乐** `16651/16652` | **暂缓** | 配置完整（道具 `28031`、`card_num=3`、`reward_time_list={1,999}…{6,1}`、钻石 100/200/300/500/1000/2000）；客户端 `game/scratcher/*` 已确认 `card_list{index,card_id,gold,status}` + `cash_reward≠0⇒开奖重置`。**但盘面张数配置里没有**（客户端按服务端 `card_list` 动态建格）⇒ 张数属**设计决定**，需标 INFERENCE 并留替换点 |
| **送花** `13324/13326/16300` | **暂缓** | 协议清楚；但 `config_flower` 只有花名/资源/`flower_count=3`，**没有 courage/charm 加成数值** ⇒ 加成来源未取证 |
| **`17200`** | **不可用** | 已被**投资系统**占用（`server/mock_server.py` L14730，带 `itype`/里程碑语义） |
| **`30502` 标签"领取充值奖励"** | **更正** | `cmd_table`（1.4.9 底）标签不准；1.4.11 的 `30502` 由 **`game/action/kaifu/`（开服活动）** 使用 ⇒ 与首充无关 |

---

## 三、其他 P1 未实现族（尚未逐个取证，供后续排期）

`魂骨(soulbone)`、`增幅(amplification)`、`引导(guide)`、`秘境/其余副本`、`许愿`、`竞猜`、`宴会`、`回归`、`节日/运营活动`、`士气(morale)`。

> 注：其中 `秘境/节日/竞猜/夺宝/答题` 在 `unimplemented_systems.md` 标了**「⏳需MuMu取证」**
> ⇒ 其数值/奖励/UI 行为需实机联调才能确认，静态只能定协议与配置**存在性**。

---

## 四、建议执行顺序

1. **开服成长计划**（本文件 §一）——配置与客户端均已确认，**只差一条命令映射**即可实现，收益高（每日登录/充值双档，典型核心循环）。
2. 其后：**刮刮乐**（补盘面张数的客户端取证）→ **送花**（补 courage/charm 来源）。
3. 再往后：需 MuMu 联调的族（秘境/节日/夺宝/答题）。

**纪律提醒**：本文件所有"暂缓/否决"都**不是"做不了"**，而是"再做一步取证就能做"——
下一步只需**一条**客户端调用点分析，不要为了让功能"看起来有"而填猜测值。
