# R89：**阵法书全部发放到背包** + 新增 `/DSH_ADMIN/addbag` 管理接口

> 用户要求：「直接给我背包里加上全部阵法图纸」。
> 已从 `config_formation.luac` 取出**全部阵法书物品 id**，核对名字/等级后一次性发放，
> 并新增一个**可复用**的发放接口（以后要重发、补给、给别的角色发都用它）。
> **时间**：2026-09-29 21:55 – 22:05。

---

## 一、阵法书 = `config_formation.luac` 里每个阵法挂的物品 id

`config_formation.luac` 的每个阵法记录附近都有一条
`TableConst(array=[None, 36xxx, 1])` —— 那就是该阵法的**阵法书物品 id**。
逐个与 `server/item_config.json`（3535 条真实物品表）对照：

| 阵法书 bid | 名字 | item `lev` | 对应阵法 | 阵法 `need_lev` |
|---|---|---|---|---|
| **36053** | 天攻阵法书 | 20 | 天攻阵 (f_type=2) | 20 |
| **36056** | 疾风阵法书 | 32 | 疾风阵 (f_type=4) | 32 |
| **36052** | 地御阵法书 | 36 | 地御阵 (f_type=3) | 36 |
| **36055** | 破雷阵法书 | 42 | 破雷阵 (f_type=5) | 42 |
| **36054** | 飘雨阵法书 | 46 | 飘雨阵 (f_type=6) | 46 |
| **36057** | 锋矢阵法书 | 50 | 锋矢阵 (f_type=7) | 50 |

★ **book.lev == formation.need_lev，六条全对上** ⇒ 映射可确证。
★ 「**流云阵**」(f_type=1, need_lev=1) **没有对应的书** —— 它是**初始阵**，
  配置里就没给它挂物品（逻辑自洽，不是遗漏）。

---

## 二、已发放（背包实测）

```
$ GET /DSH_ADMIN/addbag?formation_books=1
  added = 36053,36056,36052,36055,36054,36057
  背包共 33 条；其中阵法书：
     bid=36053  x1     bid=36056  x1     bid=36052  x1
     bid=36055  x1     bid=36054  x1     bid=36057  x1
```

**6/6 全部入包** ✓

---

## 三、新增管理接口 `/DSH_ADMIN/addbag`（可复用）

| 用法 | 说明 |
|---|---|
| `GET /DSH_ADMIN/addbag?formation_books=1` | ★ **一键发放全部 6 张阵法书** |
| `GET /DSH_ADMIN/addbag?bid=36057&n=1` | 发单个物品（`n` 个数） |
| `GET /DSH_ADMIN/addbag?bids=36052,36053&n=1` | 一次发多个 |
| `GET /DSH_ADMIN/addbag?bid=NNN&code=4` | 指定背包（`bag_code`，默认 1=普通背包） |

**行为**：写入 DB（`db_bag_add`）→ **推送给在线连接**（`bag_push_frames`）→
返回发放清单与当前背包内容。所以**不必重登**就该看到。

> ⚠ 实现时踩到一个坑并已修：`LIVE_CONNECTIONS` 的元素是 **`(handler, lock)` 元组**
> （见其定义处），不是 handler 本身 —— 直接把它传给 `bag_push_frames` 会打错。
> 现在做了两种形态的兼容。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽** / CS 2463-0 / SC 静态 81+1空-0 / SC 在线 81-81 / 专用 66-66 / 门禁 E **PASS** |
| 回归（12 项） | `verify_formation` / `verify_partner_list` / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `FORMATION_BOOKS` 常量；新增 `/DSH_ADMIN/addbag` 路由 |
| `analysis/1.4.9/round89_formation_books.md` | 本报告 |

---

## 六、请你复测（**先重启客户端**）

> ① MuMu 里 force-stop 客户端 → 重开 → 进游戏；
> ② 打开背包，应能看到 **6 张阵法书**（天攻 / 疾风 / 地御 / 破雷 / 飘雨 / 锋矢）；
> ③ 再进「伙伴 → 阵型」页看是否出现阵法列表。

> 如果 ③ 仍是空 —— 那就是 **`14099`（阵型属性汇总，真机发了 55 次、我们回默认空响应）**
> 或**阵型的另一条命令**的问题了。下一步我会按 `form_type_list.luac` /
> `form_ctrl.luac` 的 `handle_1400x` 逐个读它到底要哪些字段，
> 并把 `14099` 实现掉（**它的 `attr_list` 语义我还需要从客户端消费点取证，不猜数值**）。

---

## 七、一句话

> **6 张阵法书按 `config_formation` 里挂的物品 id 全部发放完毕**（book.lev 与阵法 need_lev 六条全对上，
> 「流云阵」是初始阵所以没有书）。顺带留了个可复用的 `/DSH_ADMIN/addbag` 接口。
> **复测前记得重启客户端**；若阵型页仍空，下一枪打 `14099`（阵型属性汇总）——它现在是默认空响应。
