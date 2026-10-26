# 日常活动清单（静态盘点）

> 日期：2026-10-02 | 方法：server/cfg 全表检索 | 数据源：1.4.11 配置（CONFIRMED）

---

## 一、已落地活动（服务端已覆盖）

| 活动名 | 配置表 | 条目数 | 奖励内容 | 服务端状态 |
|---|---|---:|---|---|
| **每日签到** | config_checkin.json → Checkin | 30 天 | Day1=coin 250,000；逐天递增+道具 | ✅ 已落地（activity/service.py） |

---

## 二、有完整配置但未落地

| 活动名 | 配置表 | 条目数 | 奖励内容摘要 | 落地可行性 |
|---|---|---:|---|---|
| **在线奖励** | config_party.json → OnlineReward | 2 组（新区 1 日 / 常驻 9999 日），各 19 档 | 1min=coin 10,000+道具 → 180min=coin 100,000+道具 | ✅ 配置完整，可接线 |
| **节日在线奖励** | config_fest_data.json → FestOnLine | 4 档 | 含 time/assets/item_list 完整字段 | ⚠️ 需确认活动时间窗口 |
| **公会福利** | config_guild.json → Guild_welfare | 7 级 | exp/guild_lev/contrib/coin | ⚠️ 依赖公会系统 |
| **奖励宝箱** | config_reward_box_data.json → RewardBoxList/Static | 完整 | 宝箱列表+静态定义 | ✅ 配置完整 |
| **奖励补发** | config_reward_back_data.json → RewardBack/Static | 完整 | 补发列表+静态定义 | ✅ 配置完整 |
| **节日转盘奖励** | config_holiday_dial_reward_data.json | 3 表（Constant/List/RewardData） | 转盘奖励池 | ✅ 配置完整 |

---

## 三、配置缺失/反构造失败

| 活动名 | 配置表 | 状态 | 说明 |
|---|---|---|---|
| **活动面板入口** | config_act.json → PlayOrderData | ⚠️ 空壳 | 197 条仅 [None, "fadeOut"] 动画数据，无实际活动名/时间/奖励 |
| **活动排序** | config_act.json → PlayOrder | ⚠️ 空壳 | 81 条仅空 dict 或 [None, x, y] 坐标 |
| **日常面板** | daily_panel.json → DailyPanel | ❌ None | 反构造失败；DailyType 有 3 类（RCHD=日常活动/XSHD=限时活动/JJKQ=精英开启） |

---

## 四、DailyType 分类（daily_panel.json）

| 类型代码 | 数值 | 含义 |
|---|---:|---|
| RCHD | 1 | 日常活动 |
| XSHD | 2 | 限时活动 |
| JJKQ | 3 | 精英开启 |

**DailyLimitType（开放限制类型）**：
- OPEN=0：直接开放
- LEV=1：等级限制
- TIME=2：时间限制

---

## 五、当前服务端活动覆盖状态

| 系统 | 状态 | 说明 |
|---|---|---|
| 签到 | ✅ 完整 | 30 天配置驱动，幂等 |
| 在线奖励 | ❌ 未接线 | 配置完整（OnlineReward 19 档），服务端无对应帧 |
| 限时活动面板 | ❌ 未实现 | PlayOrderData 反构造失败 |
| 福利大厅 | ❌ 未实现 | 无对应配置表入口 |
| 公会福利 | ❌ 依赖公会 | Guild_welfare 7 级配置存在 |

---

## 证据等级

| 项 | 等级 |
|---|---|
| 签到配置（30天） | CONFIRMED |
| 在线奖励配置（19档） | CONFIRMED |
| PlayOrderData 活动列表 | UNKNOWN（反构造失败） |
| DailyPanel 日常面板 | UNKNOWN（反构造失败） |

---

**server/ 目录未做任何修改。**
