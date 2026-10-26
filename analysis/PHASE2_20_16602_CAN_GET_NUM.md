# PHASE 2.20 —— `16602.can_get_num`（活动红点）从**恒 0** 改为**真值**

> 选靶依据：`16602 所有活动未领取数量` 客户端**真实调用 70 次**（活动族第三高）。

---

## 一、发现的缺口（真实、用户可见）

`SC_16602.holiday_list = table{ bid:u32, can_get_num:u8 }` —— `can_get_num` = **未领取数量（红点）**。

而原实现**复用了 16601 的字段遍历**，对 `can_get_num` 走：

```python
else:
    _v = kconst_int(_row, 'can_get_num')      # ← config_function 里**没有**这个字段
```

⇒ **恒为 0** ⇒ **活动面板永远不会为任何活动显示"可领取"红点**。

---

## 二、★ 确证的 id ↔ 活动映射（**非猜测**，双重印证）

来源 `config_function.module_flag`，与客户端活动注册表
（`activity_ctrl.luac` proto#30 的 `name`，见 `client_activity_icon_registry.md`）**互相印证**：

| id | description | **module_flag** | 客户端注册表 name | 本会话实现 |
|---|---|---|---|---|
| **3** | 答题 | `answer` | `answer` ✅ | 16100~16103（结算自动发奖，**非"领取"**）|
| **51** | 刮刮乐 | `scratcher` | `scratcher`/`lucky_turntable` ✅ | 16651/16652（消耗道具即开奖，**非"领取"**）|
| **505** | 成长目标 | `target` | `target` ✅ | **30500~30502（按天领取 ⇒ 有"可领取"语义）** |

⇒ **只有 505（成长目标）需要且能够报 `can_get_num`**；其余两类是"即时结算/消耗即得"，本就无可领。

---

## 三、实现（`mock_server.py`，`16601/16602` 分支内两处小改）

```python
# 循环前（仅 16602 计算一次）
_cgn505 = len([d for d in growth_target.gt_cfg()['targets']
               if d > growth_target.state(rid)['login_day']])

# 字段循环内
elif _nm == 'can_get_num':
    _v = _cgn505 if kconst_int(_row,'id','bid') == 505 else 0
```

---

## 四、验证（构造 CS 直测）

| 场景 | id 505 的 `can_get_num` | 期望 | |
|---|---|---|---|
| 清空 `role_gt`（0 天已领） | **7** | 7 | ✓ |
| 标记已领第 1 天 | **6** | 6 | ✓ |
| 其余 90 条 | **全 0** | 全 0（无假红点）| ✓ |

**真机**：`>> cmd=16602 body(1)=00` → `<< 16602 SC_16602 活动列表=91 条` ✓

**门禁**：`miniloop 145/145` ✓ ｜ **`lint_dispatch_shadow` ✓ 无分发遮蔽** ｜ `py_compile` OK ｜
`/DSH_ADMIN/status` lv70/scene=10001 ✓ ｜ 全部测试表 0 行

---

## 五、诚实边界

| 项 | 状态 |
|---|---|
| `can_get_num` 只接了 **id 505** | 其余 90 条恒 0 —— 因本服**未实现**那些活动的领取语义（回 0 是真话，不是偷懒）|
| **"可领取数"的口径** | 取"未领取的天数"（`day > login_day`）。原版是否按"当天可领=1"计数**未取证** ⇒ 标 **INFERENCE**，替换点集中在 `_cgn505` 一处 |
| `charge_reward`（充值奖励） | **未计入** `can_get_num`（作者取舍：仅登录奖励计入待领数；如需计入，改 `_cgn505` 一处即可）|
| `16664`（52 次调用） | **未做**（限时充值返利，`{msg,bid,remain_sec,status,end_time,rate,client_reward}`）；本轮未深查 |

[PHASE 2.20 完成]
