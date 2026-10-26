# PHASE 2.12 —— 答题活动（16100~16103）真实实现

> 目标：把"客户端有入口、服务端是桩"的**答题玩法**打通为可玩闭环。
> 背景：旧链 `16102` 是**假成功** —— 它把**玩家提交的答案当作正确答案回显**（`w_u8(_a)`），
> 且 `16100/16101` 无实现、无判题、无发奖、无次数与时段约束。

---

## 一、证据等级（按级别引用，勿升级）

| 项 | 等级 | 依据 |
|---|---|---|
| 帧结构 16100/16101/16102/16103 | **CONFIRMED** | `protocol/fields.json`（源自 `cmd_resolve_161.luac`） |
| 题目/时段/门槛/题数/奖励 | **CONFIRMED** | `server/cfg/config_answer.json` |
| **正确答案键** | ★ **NOT CONFIRMED** | 见下 §二 |

`config_answer.json` 实测：
```
Question : {qid:{content, a,b,c,d}}        共 239 题
Other    : {interval:20, lev:20, question_num:20, series_num:15}
OpentTime: {1:{11:00-13:00}, 2:{17:00-19:00}}
AnswerAward.answer_reward: {1:[null,8,36500,3,1], 2:[null,16,25300,1,1]}
           ⇒ 答对>=8：物品 36500×3 ；答对>=16：物品 25300×1
```

---

## 二、★ 答案键的处理（本项目最需要标注的一处）

**原版 `config_answer.Question` 只有 `content + a/b/c/d`，没有任何"正确项"字段**
（已核对；灯谜表 `config_lantern_answer` 同样只有 `a1..a16 + answer_len`，那是拼字谜而非选择题）。

⇒ 若照抄"无答案键"就**无法实现判题**。经用户明确指示，采用**项目推导键**：

- 文件：`server/answer_key.json`（UTF-8）
- 头信息写死：
  `_meta.provenance = "AI-derived from question text - NOT original APK data"`
  `_meta.evidence_level = "NOT CONFIRMED (project-supplied / INFERENCE)"`
  `_meta.uncertain = [34 个 qid]`（多为游戏内私有事实/歧义谜语，其余为客观事实/算术/字谜）
- 校验：239 条齐全、取值全在 `{a,b,c,d}`、**没有一条指向空白选项**

> **纪律**：这份键**不得**在任何文档/结论里被当作原版真值（CONFIRMED）引用。
> 若日后拿到原版答案源，直接替换该文件即可，代码无需改动。

---

## 三、实现（新模块 `server/answer/`）

| 文件 | 内容 |
|---|---|
| `server/answer/service.py` | 配置/键加载、`role_answer` 状态表、`left_count/level_ok/open_now/start/submit/settle` |
| `server/answer/handler.py` | `@register(16100/16101/16102/16103)` 四个 handler |
| `server/mock_server.py` | +1 行 `import answer.handler`（在既有 P8 `try/except` 软降级块内） |

**协议行为**：
| cmd | 行为 |
|---|---|
| 16100 | `{count}` = 今日剩余场次（`series_num` − 已用） |
| 16101 | 开始/续答 → `{code,msg,left_time(=interval),index,correct_num,question_id}`；题序以 **`(rid,day)` 为种子**⇒ 同日同角色**可复现**（便于回归）|
| 16102 | **真判题** → `{index,correct_num,correct_answer,question_id}`；`correct_answer` 为**选项序号 0..3**（a=0..d=3）|
| 16103 | 超时结算 → 按 `AnswerAward` 阈值发奖（**`RewardService.grant` + `reward_log` 幂等**）→ `{correct_num}` |

约束：等级门槛 `lev=20`；**开放时段**（11-13 / 17-19）真实生效；跨天自动重置。
测试用开关：环境变量 **`DSH_ANSWER_OPEN=1`** 临时放开时段（**不写进 config.json**）。

---

## 四、验证（可复跑）

```
# 生产（默认）：时段外应被拒
python server/mock_server.py --http 8080 --game 9000
python tools/test_answer.py --port 9000        # 预期 16101 code=0「不在活动时间」

# 联调：临时放开时段
$env:DSH_ANSWER_OPEN='1'; python server/mock_server.py --http 8080 --game 9000
python tools/test_answer.py --port 9000        # → ALL PASS（14 项）
```

联调实测结果：
```
16100 count=15
16101 code=1 idx=1 qid=10168（有答案键）
16102 correct_answer=2（与键一致）累计对=1
再答 7 题 → 累计对=8
16103 结算 → 奖励 36500 ×3 已入包（1→4）
重复 16103 → 不再发（幂等）
==== ALL PASS ====
```

**门禁**：`miniloop 145/145` ✓ ｜ `lint_dispatch_shadow` ✓ 无分发遮蔽 ｜
`py_compile` OK ｜ `/DSH_ADMIN/status` lv70/scene=10001 ✓

**★ 测试卫生（本轮实际踩到并修好）**：首跑把奖励发进了**真实角色 1001** 的背包
（36500：1→4），且只清了 `role_answer` ⇒ **残留**。已手动还原，并把
`tools/test_answer.py` 改为 **`snapshot()` + `cleanup()` 自动还原背包与 `reward_log`**，
复跑确认：BEFORE=1 / AFTER=1、`role_answer=0`、`reward_log(answer)=0`。

---

## 五、诚实边界

| 项 | 状态 |
|---|---|
| 答案键的**正确率** | **未验证**：34/239 标为 uncertain；无原版答案源可对照（子代理当时 web_search 不可用）|
| `16110~16113`（灯谜答题，拼字谜 `a1..a16+answer_len`） | **未实现**（另一套玩法，需先定"多字提交"判定）|
| `AnswerAward` 第 4 个元素语义（`[null,阈值,bid,数量,?]` 的末位） | **INFERENCE**：按"数量"用了第 3 位，末位未使用 |
| 次数语义 `series_num=15` | **INFERENCE**：按"每日可参加场次"实现（未实机对照） |

---

## 六、下一步

1. **开服成长计划**（`config_growth_target_data`）—— 只差"`3050x` ↔ login/charge_reward"一步
   取证（`action_kaifu_growplan_item.luac` 的 `type` 赋值处）即可落地。
2. **刮刮乐**（补盘面张数取证）→ **送花**（补 charm/courage 数值来源）。
3. 需 MuMu 联调的族（秘境/节日/夺宝）。

[PHASE 2.12 答题活动完成]