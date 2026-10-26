# 第十六轮：黑市真实商品 + 奖励界面五项协议

> 用户报障：① 黑市商贩点击有反应但**空列表**　② **奖励界面**：在线福利为空 / 招募奖励为空 /
> 签到奖励无法领取 / 幸运转盘、摇钱树无法使用

---

## 一、① 黑市空列表 —— ✅ **已修（填入原版真实商品）**

### 取证：`config_black_market.luac` 有 **21 条**真实商品

```
25934  {"gold":24, "name":"一袋金魂币",  "black_soul":30, "num":1}
25933  {"gold":24, "name":"一袋银魂币",  "black_soul":30, "num":1}
25327  {"gold":60, "name":"坐骑进阶丹",  "black_soul":75, "num":5}
25367  {"gold":60, "name":"魂灵进阶丹",  "black_soul":75, "num":5}
25520  {"gold":60, "name":"魂环进阶丹",  "black_soul":75, "num":5}
36500  {"gold":20, "name":"洗髓丹",      "black_soul":25, "num":5}
…共 21 条
```

**字段**：`bid / name / num / gold / black_soul`

### 实现

**填入 `config.black_market_items`（21 条，保留 `bid/name/num/gold/black_soul`，`id` 用索引、`status=0`）。**

### 验证（★ 我第一遍的测试读错了偏移）

```
30600 回包 49 字节
  原始: 00 | 00 00 00 00 | 00 15 | 01 00 02 00 ... 15 00
        refresh  next_time   count=21  21 条 (id,status)
  refresh_times=0  next_time=0  **items=21**
  长度校验: 1+4+2+21*2 = 49 ✓
```

**⚠ 第一遍我读成 `items=5377` —— 那是**我的测试脚本偏移算错**（count 在偏移 **5**，我读了 6）。
**⇒ 服务端正确，测试脚本错。**（第 9 处小自纠，测试侧。）**

---

## 二、② 奖励界面五项 —— ✅ **协议已补齐**

### 取证：客户端注册表

```
game/dailysign/dailysign_ctrl.luac : 14100 14101 14600 14601 10945 17600 17601 17602 16903 16904 19600~19604
game/dailysign/moneytree_ctrl.luac : **17800 17801**   ← 摇钱树
```

### 本轮实现（全部实测通过）

| 功能 | CMD | 定义 | 实测 |
|---|---|---|---|
| **签到信息** | `14100` | `(空) → SC{days,is_get,vip_lev}` | 3 字节 ✓ |
| **签到领取** | `14101` | `(空) → SC{tips,msg,days,assets:table,items:table}` | 5 字节 ✓ **含幂等** |
| **摇钱树** | `17800` | `(空) → SC{free_count,all_free_count,gold_count,get_coin}` | 7 字节 ✓ |
| **摇钱树领取** | `17801` | `(空) → SC{code,msg}` | 3 字节 ✓ |
| **在线福利** | `17600` | `(空) → SC{days,reward,get_day:table}` | 5 字节 ✓ |
| **在线福利领取** | `17601` | `{day:u8} → SC{tips,msg,days,num}` | 6 字节 ✓ |
| 在线福利(其它) | `17602` | `(空) → SC{...}` | 3 字节 ✓ |
| **在线时长** | `16903` | `(空) → SC{day,online_time,next_aim,status:table}` | 14 字节 ✓ |
| 在线时长(其它) | `16904` | `(空) → SC{...}` | 3 字节 ✓ |

**新增 `sign_got` 表**（签到幂等：同一天重复领只提示"今日已签到"，不重复发奖）。

---

## 三、⚠ 未实现（按纪律）与未取证项

### 3.1 **按纪律不实现**：`19600`（含未解子表）

```
19600 CS{type:u8} → SC{type, list:table(id, order, tot_time, day_time, status,
                                        **reward_list:D|Dsc19600reward_list|**,
                                        coin_type1, coin1)}
```
**⇒ 含 `D|Dsc19600reward_list|` 未解子表 ⇒ 按项目纪律**主动不实现**（不猜编码）。**

### 3.2 **未定位**：幸运转盘 / 招募奖励

| 功能 | 状态 |
|---|---|
| **幸运转盘** | 找到 `config_holiday_lucky_turntable_data.luac`（781 字节）/ `config_holiday_dial_reward_data.luac`（2682）；**但未定位到它的 CMD** ⇒ 需继续查客户端注册表 |
| **招募奖励** | **未定位**（可能属 `hero`/`partner` 或活动模块） |
| **`10945`** | `CS{card_id:string} → SC{code,msg,items:table}`；**未实现**（本轮未做） |

### 3.3 **奖励数值未取证**

**签到/在线福利/摇钱树的**具体奖励值**原版未逐项取证 ⇒
`config` 里放的是**可玩性占位**（`sign_rewards` / `online_rewards` / `moneytree_coin_per_use`），
**已在配置里明确标注"待拿原版数据后替换"，未编造成"原版值"。**

---

## 四、自查

```
mock_server.py OK ｜ lua-check OK（123864 字节）｜ 服务端 8080/9000（PID 30672）｜ stderr 0 字节
新增：30600~30603（黑市，真实 21 条）、14100/14101（签到+幂等）、17800/17801（摇钱树）、
      17600~17602（在线福利）、16903/16904（在线时长）、12430~12432（悬赏）
新增表：sign_got（签到幂等）
新增数据：config_black_market 的 21 条真实商品 → config.black_market_items
```

---

## 五、请实机确认

1. **黑市** —— 现在有 **21 件真实商品**（一袋金魂币/坐骑进阶丹/洗髓丹…）了吗？
2. **签到** —— 能领了吗？（领一次会 +500 银魂币，再领提示"今日已签到"）
3. **在线福利 / 摇钱树** —— 打开不再空白/可点了吗？

**若"幸运转盘/招募奖励"仍不行**，请告诉我它们的**入口在哪**（哪个界面/按钮），
我去查那两个模块的客户端注册表 —— 那是定位 CMD 最快的路径。
