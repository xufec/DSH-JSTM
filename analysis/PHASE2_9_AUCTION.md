# PHASE 2.9 —— 拍卖行（18020/18021/18022）真实商品与一口价购买

> 此前：`18020` 回**三张空表**、`18021` 回空表 ⇒ **拍卖行永远是空的**；`18022` 走 R180 回执族（假成功）。

## 一、发现的一个坑（值得记录）

`config_auction_data` 的 52 行里**混着两类行**：

| 类型 | 数量 | 例 |
|---|---|---|
| **商品行**（有 `item_bid`） | **50** | `1050: {item_bid:21904, init_price:500, buy_price:3000, assets:"guild_contrib", rate:60}` |
| 配置行（无 `item_bid`） | 2 | `51:{guild_contrib:1000, coupon:50000}`、`52:{open_lev:35,...}` |

⇒ 若不过滤，会把 2 条配置当成商品发出去。**已按 `item_bid` 过滤**。

## 二、实现（server/mock_server.py）

| cmd | 语义 | 行为 |
|---|---|---|
| 18020 | 打开拍卖行 | `{code,msg,buy_list(空),notice_list(空),item_list}`，`item_list` = **50 件真实商品** |
| 18021 | 拍卖物品列表 | `{type,item_list}`（同一份真实商品） |
| 18022 | **一口价购买** `CS{id}` | 校验商品存在 → 校验资产充足 → **真扣费**（`db_add_assets` 负数）+ **真入包**（`db_bag_add`）；不足/不存在 ⇒ `code=0` |

关键映射：
- `price_assets`（SC 是 `u8` **资产 code**）← 配置里的 `assets`（**资产名**）经
  `asset_label_map()`（= `config_game_data.CodeToAssets` 反查）转换 ⇒ 与扣费用**同一套资产体系**。
- `last_price` ← `init_price`（起拍价）；`buy_price` ← `buy_price`（一口价）。

新增 `auction_cfg()` / `auction_price_assets_code()`；从 18xxx 子表块与 R180 族**移出** `18020/18021/18022`，
并删除因此变成死代码的旧分支。

## 三、验证（可复跑）

```
python server/mock_server.py --http 8191 --game 9191
python tools/test_auction.py --port 9191      →  ALL PASS（11 项）
```

★ 测试用**新建的一次性账号/角色**驱动，**不动 1001 的资产与背包**：
```
18020 → items=50，首件 id=1050 item_bid=21904 price_assets=8(guild_contrib) init=500 buy=3000
18021 → items=50
18022 id=1050 余额 0 → code=0「货币不足」
18022 补足 5000 → code=1，**资产 5000→2000（真扣 3000）**，**bag 出现 bid=21904（真入包）**
18022 id=999999 → code=0「商品不存在」
```

**回归全绿（9 套）**：team / jiebai / jiebai_multi / marry / marry_propose / multi_session / fashion / halo / auction。
**门禁**：`lint_dispatch_shadow` → `✓ 无分发遮蔽`（1430/0/0）。`py_compile` OK。
**清理**：一次性账号/角色已删；`bag_items(1001)` 仍 6、`role_assets(1001)` 仍 9（**未受影响**）。

## 四、诚实边界

| 项 | 状态 |
|---|---|
| 竞拍（出价/加价） | 未实现：只做**一口价**；`last_price` 直接取 `init_price` |
| 18025 交易记录 | 未实现（返回空表） |
| 18026 关注/提醒 | 未实现 |
| `item_number` | 配置无此字段 ⇒ 取 **1**（代码注释标 INFERENCE） |
| 拍卖税收/手续费 `rate` | 未实现 |

## 五、下一步

**统一属性/战力汇总** —— 时装（2.7）、光环（2.8）目前只落库、**不影响属性/战力**。
应把 `role_fashion` / `role_halo`（以及后续翅膀/命格等）汇入 `role_attr` 与 `role_power_of`，
让客户端战力面板能反映成长。这是本项目架构目标里最关键的一环。

[PHASE 2.9 拍卖行完成]