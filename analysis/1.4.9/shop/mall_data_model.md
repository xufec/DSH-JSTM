# 1.4.9 商城数据模型（`Config.Mall*` 五张表）

> **目标 APK**：`anzbao/jstm.apk` / `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 1.4.11 未参与任何判定。
> 数据来源：`assets/src/config/config_mall.luac`（22539 B）
> 提取：`python tools/dump_drop_config.py analysis/1.4.9/shop_luac/config_mall.luac`

---

## 一、★ 关键发现：`config_mall.luac` 里是**五张表**，此前只提了一张

反汇编 `config_mall.luac` proto#0（`bc=1398`, `kgc=234`, `knum=0`）：

```
全局安装点 1 个： bc#4  Config  dict(5 keys)
### Config : 5 键
   字符串键(5): ['MallGoods', 'MallHuobanXishu', 'MallType', 'MallWeek', 'MallXian']
```

| 表 | 条数 | 内容 | 是否含 `item_bid`/`price` |
|---|---|---|---|
| **`Config.MallGoods`** | **110** | 「常用」页签货物 | ✅ 含 |
| **`Config.MallWeek`** | **24** | 「热卖/周商店」页签 | ✅ 含（`type=20`、`limit_week`） |
| **`Config.MallXian`** | **45** | 「**珍宝**/限时」页签 | ❌ **只有 `{id, cli_tag}`** |
| `Config.MallType` | 4 | 等级区间 → 商城 type 映射 | — |
| `Config.MallHuobanXishu` | 14 | 伙伴系数 | — |

> ⚠ **本阶段之前只提取了 `MallGoods` + `MallWeek`**（`server/mall_config.json` 的 **134 = 110 + 24**，
> id 集合与 `MallGoods ∪ MallWeek` **完全相等**，已用 `tools/build_shop_goods.py` 核对通过）。
> **`MallXian` 从未被提取** —— 这是「珍宝页签为空」在数据侧的成因之一。

---

## 二、各页签的数据来源（客户端 `shop_view` / `shop_model` 实测）

客户端页签常量（`shop_view.luac` proto#6 `updateTabBar` 常量池）：

```
NORMAL(常用) ZHENBAO(珍宝) EXCHANGE(试炼) GUILD(宗门) NPC
YINBI(金魂币) HONOR(声望) JIFEN(积分) EXCOLLECT(兑换) WEEKDAY(热卖)
```

`shop_normal_view.luac` proto#24 决定每个页签**从哪儿取货**：

| 页签 | 取数方法 | 数据来源 |
|---|---|---|
| 常用 NORMAL | `getGoodsList()` | **客户端配置** `Config.MallGoods`（经 `initConfigGoodsByType` 按等级/职业过滤） |
| 热卖 WEEKDAY | `getWeekdayGoodsList()` | **客户端配置** `Config.MallWeek` |
| **珍宝 ZHENBAO** | **`getZhenbaoGoodsList()`** | **服务端 `SC_12836`** ← `requestZhenbaoData()` → `ctrl:request12836()` |
| 副本 SECRET/SECRET2 | `getCopyMallGoodsList()` | 服务端 `12838` / `12842` |
| NPC | `getNPCGoodsList()` | 服务端 |
| 宗门 GUILD | `getGuildList()` | 服务端 |

**⇒ 珍宝页签的货物只可能来自服务端的 `SC_12836`；本地配置只提供 id 列表。**
服务端此前**完全没有实现 12836** ⇒ **页签必然为空**。

---

## 三、★ 珍宝（`Config.MallXian`）的字段——**原版只给了 id**

`MallXian` 45 条，**字段集合唯一**：

```
字段集合: {('cli_tag', 'id'): 45}
key 范围: 21001 .. 21045
21001 {"id": 21001, "cli_tag": ""}
21002 {"id": 21002, "cli_tag": ""}
...
```

- 与 `MallGoods` 交集 **0**，与 `MallWeek` 交集 **0**
- **没有 `item_bid` / `price` / `pay_type` / `bind` / `limit_num`**

⇒ **原版珍宝到底卖什么、卖多少钱，不在客户端 APK 里**（属原版服务端数据）。
这与本项目此前遇到的「怪物 HP」「逐级属性成长」是**同一类缺口**。

### 3.1 本阶段的处理（严格标注）

| 字段 | 来源 | 标记 |
|---|---|---|
| `id`（21001..21045） | **原版** `Config.MallXian` | **原版** ✅ |
| `cli_tag` | **原版** `Config.MallXian` | **原版** ✅ |
| `item_bid` / `price` / `pay_type` / `bind` / `limit_num` | 从**真实物品表** `Config.Item` 里按确定性规则挑可用消耗品 | **`IMPLEMENTATION_FALLBACK`** ❌ **不是原版数值** |

生成工具：`tools/build_shop_goods.py` → `server/mall_zhenbao.json`（45 条）。

> **id 用原版**的意义：客户端 `setZhenbaoGoodsList` 会按 id 去 `MallXian` 取 `cli_tag`，
> 所以 id 必须与客户端配置对齐；而**内容**是我方补的，必须在文档与日志里标明。

---

## 四、`Config.MallType`（等级 → 商城 type）

```
MallType[1..4] = { min_lev, max_lev, type }
MallType[1] = {min_lev:1, max_lev:9, type:4}
```

「常用」页签按玩家等级落在哪个区间、再按 `MallGoods[*].type` 过滤。
`MallGoods` 的 `type` 分布：`{2:51, 3:15, 4:11, 5:10, 6:10, 20:24, 100:5, 101:4, 102:4}`。

---

## 五、真实物品表（`Config.Item`）——货物的唯一合法来源

1101+ 条真实物品（`analysis/1.4.9/item/config_item.json`，1117 条，bid 33000–99999）。
按 `idx3`（type）分布：`{7:2, 31:110, 32:20, 33:81, 35:27, 40:1}`。

可作商城货物的**消耗品类型**：**31 / 32 / 33 / 35**（共 **238** 件）。

⇒ 服务端所有商城货物都经 `is_valid_item()` 过滤：
**只卖真实物品表里存在的物品**，否则买回去的背包会变成空白。

---

## 六、未知项（不猜）

| 项 | 状态 |
|---|---|
| 原版珍宝（限时商店）卖什么 / 价格 / 币种 | **`UNKNOWN`** —— `MallXian` 只有 id |
| 原版兑换商店（12840）配方 | **`UNKNOWN`** —— 同上，`IMPLEMENTATION_FALLBACK` |
| 原版副本商店（12838/12842）货物 | **`UNKNOWN`** —— 本阶段复用珍宝表并标注 |
| `cli_tag` 各取值的展示语义（"八折"/"五折"/"HOT"） | 部分（有取值，语义 `INFERRED`） |
| `MallHuobanXishu` 的用途 | 未追（伙伴系数，非商城主流程） |
