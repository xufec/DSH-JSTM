# PHASE 2.21 —— `16664` 限时充值返利：从**全 0** 改为**配置真值**

> 选靶依据：`16664 获取限时充值返利活动数据` 客户端**真实调用 52 次**（活动族最后一条高频未做项）。

---

## 一、原状与缺口

`16664` 原落在**通用编码器组**（`20504,13341,13354,17001,13321,16664,20028,30716`）⇒
回包全 0 / 空串 ⇒ **客户端视为"无返利活动"**。

---

## 二、★ 找到配置源（CONFIRMED）

`server/cfg/config_holiday_util.json` 的两个段：

**`LimitConstant.hash`**（活动参数）：

| 键 | 值 | 用途 |
|---|---|---|
| `charge_return_rule_switch` | **1** | → `status`（规则开关）|
| `charge_return_active_rate` | **500** | → `rate`（返利率）|
| `charge_return_day` / `charge_return_mins` / `charge_return_countdown` | 7 / 180 / 15 | （时长/倒计时参数，见§四）|
| `charge_return_max_gold` / `charge_return_gold` | 2000 / 1000 | 上限/门槛 |

**`TipsConstant.hash`**：`charge_return_timelimit_tips1` / `tips2` → `msg`（活动文案）
（★ 我第一版错读到 `LimitConstant` 里，发出空 `msg`；**已修正**为 `TipsConstant`。）

**`ChargeReturnGolds.hash`**：`normal/eyou/tw/en` 各一列返利档位（如 `normal=[null,10,30,120,450,880,1880,250,1280]`）。

---

## 三、实现（`mock_server.py`：既有组内新增 `elif cmd == 16664`）

```python
SC_16664 = { msg, bid, remain_sec, status, end_time, rate, client_reward }
  msg    ← TipsConstant.charge_return_timelimit_tips1      （CONFIRMED）
  status ← LimitConstant.charge_return_rule_switch         （CONFIRMED，名字即"规则开关"）
  rate   ← LimitConstant.charge_return_active_rate         （CONFIRMED）
  bid    ← config_function 中 module_flag=='charge_double' 的 id = 62
           （与 PHASE 2.20 同一印证法：module_flag ↔ 客户端活动注册表 name）
  remain_sec / end_time / client_reward ← **无配置来源 ⇒ 0 / 0 / ''**（不编造）
```

> ★ **实现方式的重要选择**：**没有**新加顶层 `if cmd == 16664:` ——
> 那会造成"同一命令两处分支"（我在 PHASE 2.19 对 `10925` 犯过这个错、被 `shadow_lint` 逮住）。
> 本次改为**组内 `elif`**，保持"一条命令一处分支"⇒ `shadow_lint` 仍 **✓ 无分发遮蔽**。

---

## 四、验证

**回包实测**：
```
16664 →
  msg = "活动期间，首笔充值可以获得<div fontcolor=#249015>大量钻石…"（真配置文案）✓
  bid = 62        status = 1        rate = 500      ✓
  remain_sec = 0  end_time = 0      client_reward = ''   （无来源，如实留空）
```

**门禁**：`miniloop 145/145` ✓ ｜ **`lint_dispatch_shadow` ✓ 无分发遮蔽** ｜ `py_compile` OK ｜
`/DSH_ADMIN/status` lv70/scene=10001 ✓

---

## 五、诚实边界

| 项 | 状态 |
|---|---|
| `remain_sec`（活动剩余秒） | **0**：配置里只有 `charge_return_mins=180`/`countdown=15` 这类**时长**参数，"活动剩余时间"需**运营配置的绝对起止时间**，本服无 ⇒ 不编造 |
| `end_time` | 同上 ⇒ 0 |
| `client_reward`（奖励展示串） | **空**：其格式未取证（`ChargeReturnGolds` 是档位数值，不是展示串）⇒ 不编造 |
| `bid` 取 62 | 依据 `module_flag=='charge_double'`；若原版另有 id，改一行即可（**单点替换**）|
| 返利**领取**链路 | **未实现**（`ChargeReturnGolds` 档位已定位，但领取命令未定性）|

[PHASE 2.21 完成]
