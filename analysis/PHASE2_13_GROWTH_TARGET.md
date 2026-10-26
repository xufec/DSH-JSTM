# PHASE 2.13 —— 开服成长计划（30500/30501/30502）真实实现

> 目标：把"配置齐全、客户端有入口、服务端无实现"的**开服成长计划**打通。
> 旧链：`30501/30502` 走 `{result,msg,items}` **空物品桩**（`w_u16(0)`），`30500` 无实现。

---

## 一、★ 关键取证：`30507=登录` 的推断被**命令名否决**

先前我从 `action_kaifu_growplan_item.luac` 的 `type` 分派（`type=3 → sender30507`）
**推断**"30507 = 登录奖励领取"。本轮查 `protocol/cmd_table.json` 发现**命令名是权威的**：

| cmd | cmd_table 名称 | 实际语义 |
|---|---|---|
| **30500** | 请求成长目标信息 | 面板整包 |
| **30501** | **领取登陆奖励** | `GrowthTarget[day].login_reward` |
| **30502** | **领取充值奖励** | `.charge_reward`（受 `charge_gold` 门槛）|
| 30503 | 半价抢购 | `HalfDiscountBuy` |
| 30506 | 领取目标奖励 | `TodayTarget[target_id]` |
| 30507 | 领取**组合**奖励 | 组合奖励（**非登录**）|

⇒ **字节码 type 分派推出的映射是错的，已按命令名纠正**（记此以免后人再踩）。
教训：**"命令名"优先于"字节码推断"**；两者冲突时必须回到 `cmd_table` 复核。

---

## 二、证据等级

| 项 | 等级 | 依据 |
|---|---|---|
| 命令语义 | **CONFIRMED** | `protocol/cmd_table.json` |
| 帧结构 | **CONFIRMED** | `protocol/fields.json`（`SC_30501/30502{result:u8,msg:s,items:table{item_bid:u32,num:u32}}`）|
| 奖励数值 | **CONFIRMED** | `server/cfg/config_growth_target_data.json`（day1: login 36500×5+36006×3；charge 25104×3+36010×1+25327×5；`charge_gold=80`）|
| 客户端入口 | **CONFIRMED** | 反汇编 `game/action/kaifu/action_kaifu_growplan{,_item}.luac`（读 `GrowthTarget[day].login_reward/.charge_reward`，文案「累计充值{0}元」）|
| `total_charge`（累计充值）存放 | **INFERENCE** | 原版在服务端；本实现落 `role_gt.total_charge`，由充值链路/GM 写 |

---

## 三、实现（新模块 `server/growth_target/`）

| 文件 | 内容 |
|---|---|
| `service.py` | `gt_cfg()` 读配置、`role_gt(rid,login_day,charge_day,total_charge)`、`claim(rid,day,kind)`、`state/set_total_charge` |
| `handler.py` | `@register(30500/30501/30502)` |
| `mock_server.py` | +1 行 import（在既有 P8 软降级 `try` 块内）|

- `30501` 领登录奖励：无门槛；已领 ⇒ `result=0「已领取」`
- `30502` 领充值奖励：`total_charge >= charge_gold` 才可领，否则 `result=0「累计充值不足」`
- `30500` 返回各天 `(login_reward_state, charge_reward_state, total_charge)` 真值
- **幂等**：发奖走 `reward.service.grant`，`reference_id = gt:{kind}:{rid}:{day}` ⇒
  重复点击 / 重连重发**不会重复发**；`role_gt` 另存认领态（面板要用）

---

## 四、验证（可复跑，ALL PASS 13 项）

```
python server/mock_server.py --http 8080 --game 9000
python tools/test_growth_target.py --port 9000
```
```
30501 day=1 → result=1，items={36500:5, 36006:3}，背包 36500 +5
30501 重复 → result=0「已领取」，背包未变
30502 total_charge=0 → result=0「累计充值不足」
30502 total_charge=80 → result=1，items={25104:3, 36010:1, 25327:5}，背包 25104 +3
30502 重复 → result=0
30500 → day1(登录已领=1, 充值已领=1, 累计充值=80)
==== ALL PASS ====
```

**门禁**：`miniloop 145/145` ✓ ｜ `lint_dispatch_shadow` ✓ 无分发遮蔽 ｜ `py_compile` OK ｜ `/DSH_ADMIN/status` lv70/scene=10001 ✓

**测试卫生**：测试跑在真实角色 1001 上，已内建 **`snapshot()`+`cleanup()` 自动还原背包 / `reward_log` / `role_gt`**；
复跑确认：背包回到 `{36500:1, 其余 0}`、`role_gt=0`、`reward_log(growth_target)=0`、`role_answer=0`。
（本轮还发现并清掉了我先前 `16100` 探针留下的一行 `role_answer`。）

**另修**：`tools/test_growth_target.py` 起初报 2 个 FAIL，根因是**测试自身的 Python 求值顺序 bug**
（`out[r.u32()]=r.u32()` 会先算右侧 ⇒ bid/num 反读），非服务端问题；已修正。

---

## 五、诚实边界

| 项 | 状态 |
|---|---|
| `30503 半价抢购`、`30506 领取目标奖励` | **未实现**（`TodayTarget`/`HalfDiscountBuy` 配置已存在，可续做）|
| `30500` 的 `remain_time` / `targets` 子表 | **未填**（0 / 空表）：`targets` 的 `finished_value/total_value` 数据源未取证 ⇒ 按纪律不编造 |
| `total_charge` 的**写入链路** | 未接：目前只暴露 `service.set_total_charge()`，尚未与充值命令打通 |
| `charge_gold` 单位 | **INFERENCE**：按"累计充值(钻石)"与配置直接比较 |

---

## 六、下一步

1. **刮刮乐**（补"盘面张数"客户端取证）→ **送花**（补 charm/courage 数值来源）。
2. `30503/30506` 续做（配置已在）。
3. 需 MuMu 联调的族（秘境/节日/夺宝）。

[PHASE 2.13 开服成长计划完成]