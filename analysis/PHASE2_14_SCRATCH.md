# PHASE 2.14 —— 刮刮乐（16651/16652）真实实现

> 旧链：`16652` 是**纯回显桩**（`w_u32(index) + w_u8(0)`），`16651` 落通用子表组 ⇒
> **不消耗道具、不建盘面、不开奖**。

---

## 一、证据等级（逐项标注）

| 项 | 等级 | 依据 |
|---|---|---|
| 帧结构 16651/16652 | **CONFIRMED** | `protocol/fields.json` |
| 规则与常量 | **CONFIRMED** | `server/cfg/config_scratch_card.json` |
| 客户端行为 | **CONFIRMED** | 反汇编 `game/scratcher/scratcher_view.luac` proto#17 |
| **各档钻石数值** | ★ **STRONG_INFERENCE** | 见 §二 |
| **盘面张数** | **INFERENCE** | 见 §二 |

**配置实测**（`ScratchCardConst`）：
```
item_bid      = 28031          （刮卡道具）
item          = "{28031,1}"    （每刮一次消耗 1 个）
card_num      = 3              （3 张相同卡开奖）
max_reward_id = 6              （1..6 档）
reward_time_list = {1,999},{2,999},{3,999},{4,999},{5,2},{6,1}   ← 各档"可获得次数上限"
notice_reward_ids = "6,5,4"    （需公告的档位）
ScratchCardRes = [null, card1..card6]
holiday_rule  = "…刮到3张相同的卡片时即可获得钻石奖励 / 每消耗一个道具必定会刮出3张相同的卡 /
                 刮卡可随机获得 100、200、300、500、1000、2000 钻石…"
```

**客户端确认**（`scratcher_view.luac` proto#17 `setData(card_list, cash_reward)`）：
`cash_reward~=0` ⇒ **清空全部格子（开奖并重置）**；否则按 `card.index` 摆格，`card.status~=0` ⇒ 该格已刮开可见。
（`scratcher_ctrl.luac`：`send16651` 拉盘面、`send16652(index)` 刮某格。）

---

## 二、★ 两处必须标注的不确定（均做成单点可替换）

1. **各档钻石数值（100/200/300/500/1000/2000）只存在于 `holiday_rule` 的「文本」里**
   —— 已**全量搜索 `server/cfg/*.json`**，`ScratchCard` 仅出现在 `config_scratch_card.json`，**无对应数值表**。
   它不是编造（是 APK 内官方文案），但属文本而非表 ⇒ 标 **STRONG_INFERENCE**，
   收敛为 `scratch/service.py` 的 **`TIER_GOLD = {1:100,…,6:2000}`** 一行，拿到表即替换。

2. **盘面张数**：客户端按服务端 `card_list` 动态建格 ⇒ 张数由**服务端决定**；
   取 `card_num=3`（与"每消耗一个道具必定会刮出 3 张相同的卡"自洽）⇒ **INFERENCE**，
   由配置 `card_num` 驱动，无需改代码即可调整。

抽档规则：按 `reward_time_list` 上限过滤（第 5 档只能出 2 次、第 6 档 1 次），
其余在可出档位中**均匀随机**（规则文本未给概率）⇒ 概率属 **INFERENCE**。

---

## 三、实现（新模块 `server/scratch/`）

| 文件 | 内容 |
|---|---|
| `service.py` | `scratch_cfg()`、`role_scratch(rid,board_id,cards,ts)`、`role_scratch_tier(rid,tier,cnt)`、`_bag_count/_bag_consume`（自持，避免依赖未搬迁 helper）、`new_board/scratch/take_reward` |
| `handler.py` | `@register(16651/16652)` |
| `mock_server.py` | +1 行 import（既有 P8 软降级 `try` 块内）|

行为：
- **16652{index}**：无盘面 ⇒ **消耗 1×28031**、按上限抽档、生成 `card_num=3` 张**同 card_id/gold** 的盘面；
  置该格 `status=1`；**全部刮开时开奖** —— 走 `RewardService.grant`（`code='gold'`，钻石），
  `reference_id = scratch:{rid}:{board_id}` ⇒ **幂等**。
- **16651**：若盘面已全开 ⇒ 返回 `cash_reward=档位钻石` 并**清盘**（客户端据此开奖+重置）；否则回当前盘面。
- 道具不足 ⇒ `code=0「刮刮乐道具不足」`，**不建盘、不发奖**。

---

## 四、验证（可复跑，ALL PASS 16 项）

```
python server/mock_server.py --http 8080 --game 9000
python tools/test_scratch.py --port 9000
```
```
16651 初始：cards=0 / cash_reward=0
16652 index=0 → code=1 status=1，道具 3→2（真消耗）
16651 → cards=3，**3 张 card_id 全相同**（{1}），gold 合法（{100}），已刮 1 格
16652 index=1,2 → 均 code=1
16651 → cash_reward=100，**钻石 1800140→1800240（真入账 +100）**，盘面清空
道具=0 时 16652 → code=0「刮刮乐道具不足」
==== ALL PASS ====
```

**门禁**：`miniloop 145/145` ✓ ｜ `lint_dispatch_shadow` ✓ 无分发遮蔽 ｜ `py_compile` OK ｜
`/DSH_ADMIN/status` lv70/scene=10001/gold=1800140 ✓

**测试卫生**：跑在真实角色 1001 上 ⇒ 内建 **`snapshot()`+`cleanup()`** 还原
背包(28031) / 钻石(gold) / `role_scratch*` / `reward_log(scratch)`。
复跑确认：`bag 28031=0`、`gold=1800140`（回到基线）、四张新表与三类 reward_log 均 **0**。

**本轮也修了测试自身的两个 bug**（非服务端）：
① `parse_items` 求值顺序反读（同上一轮）；② 开奖在"最后一格刮开"瞬间发生，
   而我把"开奖前钻石"采样放在了其后 ⇒ 改为在刮最后一格**之前**采样。

---

## 五、诚实边界

| 项 | 状态 |
|---|---|
| 各档**概率权重** | **INFERENCE**：规则文本未给 ⇒ 均匀随机；拿到权重表即替换 `_pick_tier` |
| 各档**钻石数值** | **STRONG_INFERENCE（文本来源）** ⇒ `TIER_GOLD` 单点替换 |
| `item_list` / `item_effect_list` / `client_reward` | 回**空**（配置无来源 ⇒ 不编造）|
| `notice_reward_ids`（6/5/4 档发公告） | **未接**（公告链路待接）|
| `remain_sec`（活动剩余秒） | 回 **0**（无配置来源 ⇒ 不编造）|
| 每档次数上限**跨天是否重置** | **未做**（`role_scratch_tier` 目前累计，不按天重置）|

---

## 六、下一步

按你先前"2、3、4、5 继续"的清单：**送花**（补 charm/courage 数值来源）→
`30503/30506` 续做 → 需 MuMu 联调的族（秘境/节日/夺宝）。

[PHASE 2.14 刮刮乐完成]