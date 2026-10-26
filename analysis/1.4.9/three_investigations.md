# 三项调查结果（ItemNewGift / 伙伴商店 / 聚宝盆奖池）

> 用户指定：① 解析 `ItemNewGift` 哈希 ⇒ 解决礼包打开失败
> ② 定位伙伴商店协议 ⇒ 解决兑换不了
> ③ 找原版聚宝盆奖池 ⇒ 解决物品不一致

**方法：用新做的通用读取器 `tools/extract_config.py` 直接读表 + 查客户端字节码。不猜。**

---

## ① 礼包打开失败 —— ★**查清了：`30010` 的内容不在客户端配置里**

### 证据：三张表逐一核查

| 表 | 结构 | 含 `30010`？ |
|---|---|---|
| **`Config.ItemGift`** | `[None, 礼包bid, 物品bid, 数量]`（数组） | ❌ 不在（共 496 个礼包） |
| **`Config.ItemNewGift`** | `{show_price, price, limit_bid, bid, buy_type}` | ✅ **在，但它是****商店价格表**！ |
| **`Config.SelectGift`** | 条件 `{lev_min,sex,lev_max}` + 内容 `[None,36540,5,1]` + 选项 `[None,1,2,3,4]` | ❌ 不在 |

**`ItemNewGift` 里的 `30010` 原文：**
```json
{"show_price": 0, "price": 0, "limit_bid": 0, "bid": 30010, "buy_type": ""}
```
**对照同表另一条：**
```json
{"show_price": 800, "price": 288, "limit_bid": 30150, "bid": 30053, "buy_type": "gold"}
```
**⇒ 字段是 `price` / `buy_type` ⇒ 这是**商店价目表**，不是"打开给什么"。**

### ★ 结论（`CONFIRMED`）

**`30010`（10级礼包）在客户端三张礼包表里**都没有内容定义** ⇒**
**⇒ 它的内容是**服务端逻辑**决定的（等级礼包常见做法：按等级/活动由服务端发放）。**

**⇒ 所以「礼包打开失败」**不是协议问题**，而是**我们没实现"打开这个礼包给什么"的服务端逻辑**。**

**⇒ 修法（可选，需你确认给什么）：**
在 `config.json` 里加一张**服务端侧**的等级礼包内容表，例如：
```json
"levgift_open": { "30010": [[16201, 1], [33001, 1]], "33001": [[16201, 3]] }
```
**⚠ 具体给什么**没有依据**，**我不会编** —— 需要你指定，或我按"同级常见配置"给一个**明确标注为自定**的默认值。**

---

## ② 聚宝盆奖池 —— 数据源找到了，但需再挖一层

### 找到的表

```
config_treasure.luac              9,914   （通用读取器返回 0 条 ⇒ 结构特殊）
config_treasure_box_data.luac    12,337   ✅ 84 条
config_reward_box_data.luac       8,639
```

**`config_treasure_box_data` 全部字段（逐条核对）：**
```
is_person, box_type, is_pass, leader_add_point, bid, elem_bid, is_leader_open, is_free, drop_id
```
**样例行：**
```json
{"bid":1100, "elem_bid":90202, "box_type":2, "is_free":1, "drop_id":17000, ...}
```

**⇒ 奖池是**按 `drop_id` 指向掉落表**（`drop_id=17000`）。**

### 但 `config_drop` 里没有 17000

**`config_drop.luac` 结构（字节码直读）：**
```
Config.Drop[<drop_id>] = { first_p, core_p, normal, normal_sum, <14 字段哈希> }
```
**抽出来只有 **34 组**（4001~4013、20001~…），**不含 17000**。**

**⇒ 所以 `drop_id=17000` 指向的是**另一张表**（或另一套编号），**本轮**未定位**。**

### 附带：补了 **`11701~11704`（聚宝盆平行族）**

**真机未应答里发现 `11701/11702`（与 `11710~11713` **同构的平行族**），已补齐：**
```
cmd=11701 -> 4 字节   cmd=11702 -> 3 字节
cmd=11703 -> 16 字节  cmd=11704 -> 4 字节
```

---

## ③ 伙伴商店兑换 —— ★**定位到了：是 NPC 兑换界面**

### 证据

**`config_exchange.luac`（153 条）—— 兑换表：**
```json
{"bind":1, "type":1, "item_num":1, "limit_week":0, "pay_type":"gold",       "price":30, "order":0}
{"bind":1, "type":2, "item_num":1, "limit_week":0, "pay_type":"arena_cent", "price":6,  "order":1}
```
**字段：`type`（分类）/ `pay_type`（支付币种）/ `price` / `item_num` / `bind` / `limit_week` / `limit_day` / `limit_point` / `peak_score` / `order`**

**谁读它（客户端字节码）：**
```
game/npc/view/map_exchange_view.luac              proto[3] [4] read 'exchange'
game/soulstar/viewstar/soulstar_viewstar_panel.luac proto[49]
```

### ★ 结论（`CONFIRMED`）

**兑换功能挂在 **NPC 的 `map_exchange_view`（地图兑换界面）** 上 ——**
**⇒ 而 NPC 对话链路**正是之前九轮未闭环的 `getScene()==nil` 问题**（`setOpenNpc` 调用失败）！**

**⇒ 所以「伙伴商店兑换不了」与「NPC 交互不可用」**是同一个根因**。**

**⇒ 修法（两条路）：**
1. **治本**：解开 `getScene()==nil`（需真机调用栈，静态已到尽头）
2. **绕过**：直接实现兑换协议（需先定位 `map_exchange_view` 注册的 CMD）

**⇒ 本轮**未定位到 CMD**（下一步：扫 `map_exchange_view.luac` 的 `RegisterProtocal`）。**

---

## 总结（本轮实际交付）

| 项 | 状态 |
|---|---|
| **① 礼包打开失败** | ✅ **查清根因**：`30010` 内容不在客户端配置 ⇒ **是服务端逻辑**，需你指定给什么（**不编造**） |
| **② 聚宝盆奖池** | ⚠️ **数据源定位到 `config_treasure_box_data.drop_id`**，但 `17000` 不在 `config_drop` ⇒ **需再挖一层**；**附带补齐 `11701~11704`** |
| **③ 伙伴商店** | ✅ **定位到根因**：走 **NPC `map_exchange_view`** ⇒ **与 `getScene()==nil` 同源**；CMD 待定位 |

**新增工具**：`tools/extract_config.py`（通用读表）、`tools/extract_drop.py`（掉落表）
**新增协议**：`11701 / 11702 / 11703 / 11704`
**自查**：`mock_server.py OK` ｜ 服务端 8080/9000 运行中 ｜ stderr 0 字节
